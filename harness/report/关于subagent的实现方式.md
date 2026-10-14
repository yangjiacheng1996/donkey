# 关于 subagent 的实现方式

> 本报告针对 donkey 项目中 subagent 的两种实现路线做对比分析：
> 路线 A：把 subagent 实现成 `@tool`，主 agent 通过工具调用触发 subagent；
> 路线 B：把 subagent 实现成 LangGraph `StateGraph` 子图，主图用 `add_node` 装配。
> 报告内容 100% 基于 `harness/LangChain_doc/`、`harness/LangGraph_doc/` 离线文档 + 项目既有 `harness/report/` 调研。

---

## 一、问题的本质：并发模型差异

你已经精准识别了核心矛盾：

| 路线 | subagent 启动方式 | 是否支持并发调用 subagent | 排他性工具是否需要加锁 |
|---|---|---|---|
| **A：@tool 形式** | 主 agent 调 `tool_call("subagent", ...)` | ✅ 支持（LangChain 原生） | ⚠️ 需要（排他性工具要排队） |
| **B：LangGraph 子图** | 主图 `add_node("subagent", compiled_subgraph)` | ❌ 默认不支持（需 Send fan-out） | ✅ 不需要（单线程语义） |

但这个表有一个**关键修正**：路线 B 是否支持并发，**取决于子图的 checkpointer 模式**，而不仅仅是"子图本身"。我先把官方文档的相关事实摆出来，再下结论。

---

## 二、关键官方文档事实

### 2.1 @tool 形式的并发：LangChain/LangGraph **原生支持**

**证据**：`harness/LangChain_doc/tools.md:1195`

> **Multiple parallel tool calls:** When the model calls several tools in one step, all of them execute first. After all tools finish, the agent routes to `END` only if **every** tool in that batch has `return_direct=True`.

→ 主 agent 一次模型响应里发出多个 `tool_call`，LangGraph 默认会**并发执行**这些 tool call（实际是 `asyncio.gather`），每个 tool call 拿到自己的 `ToolMessage` 后再回到 model。

这条事实对路线 A 是**关键利好**：
- 主 agent 决定"并行调研 3 个 subagent" → 一次模型响应里发 3 个 `task(subagent=researcher, ...)` `task(subagent=writer, ...)` `task(subagent=reviewer, ...)` → 3 个 subagent **真的并行跑**。
- 这正是你用过的 OpenCode 行为。

### 2.2 LangGraph 子图的并发：**节点层面默认串行**

**证据**：`harness/LangGraph_doc/use-subgraphs.md:316-326` 表格

> | Mode                                      | `checkpointer=`  | Behavior                                                                                                                                                                                                 |
> | ----------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | [Per-invocation](#per-invocation-default) | `None` (default) | Each call starts fresh and inherits the parent's checkpointer to support [interrupts](/oss/python/langgraph/interrupts) and [durable execution](/oss/python/langgraph/persistence) within a single call. |
> | [Per-thread](#per-thread)                 | `True`           | State accumulates across calls on the same thread. Each call picks up where the last one left off.                                                                                                       |
> | [Stateless](#stateless)                   | `False`          | No checkpointing at all—runs like a plain function call. No interrupts or durable execution.                                                                                                             |

**per-invocation 模式**（默认）：每次调用 fresh state，可以并发调用不同子图，**互不干扰**。
**per-thread 模式**：状态累积，**不支持并行调用同一子图**（`use-subgraphs.md:494` 原文警告）。
**stateless 模式**：没有 checkpoint，没有 HITL/durable execution，不适合生产。

### 2.3 路线 B 真正的并发瓶颈：**节点层面串行**

即使 per-invocation 模式"语义上"支持并发，**子图作为 `add_node` 的节点，在 LangGraph 的节点调度里是按拓扑序串行执行的**——除非你显式用 `Send` fan-out。

**证据**：`harness/LangChain_doc/multi-agent/router.md:45-67`

```python
from langgraph.types import Send

def classify_query(state: State) -> list[ClassificationResult]: ...

def route_query(state: State):
    classifications = classify_query(state["query"])
    return [
        Send(c["agent"], {"query": c["query"]})
        for c in classifications
    ]
```

要让子图节点并发，必须：
1. 写一个 fan-out 函数返回 `list[Send]`（而不是 `goto="..."`）；
2. 每个 `Send` 是 LangGraph 的并行任务；
3. 然后还需要一个 reduce/synthesize 节点收集并行结果。

也就是说：**路线 B 想实现并发 ≠ 不要锁**，而是"既要写 Send fan-out，又要写 reduce 节点，还要给排他性工具加锁"——比路线 A 复杂。

### 2.4 路线 B 的另一个隐性坑：嵌套节点 vs 工具函数的可观测性

**证据**：`harness/LangGraph_doc/use-subgraphs.md:693` Note

> Viewing subgraph state requires that LangGraph can **statically discover** the subgraph—i.e., it is [added as a node](#add-a-subgraph-as-a-node) or [called inside a node](#call-a-subgraph-inside-a-node). It does not work when a subgraph is called inside a [tool](/oss/python/langchain/tools) function or other indirection (e.g., the [subagents](/oss/python/langchain/multi-agent/subagents) pattern). Interrupts still propagate to the top-level graph regardless of nesting.

→ 路线 A（subagent 在 @tool 里被 `subagent.invoke()`）**不享受静态发现**，调试时看不到子图节点结构。
→ 路线 B（`add_node("subagent", compiled_subgraph)`）**可以静态发现**，`agent.get_graph().draw_mermaid()` 能看到完整图。

但反过来，路线 A 的 `@tool` 是 LangGraph 原生 tool_call，**v3 event streaming 会原样流出**（见 `harness/LangChain_doc/event-streaming.md`），前端可以直接渲染 subagent 调用卡片；路线 B 的 `add_node` 子图事件需要通过 `stream.subgraphs` 投影（`use-subgraphs.md:772`）才能拿到，前端要额外接 projection。

---

## 三、两条路线的工程化对比

### 3.1 实施复杂度对比

| 维度 | 路线 A：@tool 形式 | 路线 B：LangGraph 子图 |
|---|---|---|
| **官方参考** | `harness/LangChain_doc/multi-agent/subagents.md` 全章 | `harness/LangGraph_doc/use-subgraphs.md` + `harness/LangChain_doc/multi-agent/router.md`（Send fan-out） |
| **subagent 定义** | `subagent = create_agent(...)` 一个独立图 | 独立 `StateGraph` + 显式 `add_node` / `add_edge`，要么共享父 state schema，要么写 wrapper function |
| **装配到主图** | `tools=[call_researcher, call_writer]`（直接当工具） | `parent.add_node("researcher", researcher_subgraph)` 或 `parent.add_node(call_researcher_node)`（用 wrapper function 调 subgraph） |
| **并发支持** | ✅ 主 agent 多 tool_call 自动并发（`tools.md:1195`） | ⚠️ 默认串行；并发需写 Send fan-out + reduce 节点（`router.md:45-67`） |
| **HITL 透传** | ✅ Interrupts 自然冒泡（`use-subgraphs.md:693` 末句） | ✅ 自然（interrupt 在子图节点上） |
| **Checkpointer** | per-invocation（默认 `None`，每次 fresh state，**支持并发**） | per-invocation（默认）支持并发；per-thread 不支持 |
| **Store** | 继承父 store（`create_agent(store=...)`） | 需手动传或继承 |
| **Middleware** | 每个 subagent 独立 `middleware=[...]` | 父图 middleware 在子图外层；子图内部需自己装 |
| **上下文隔离** | ✅ 默认 isolated（只接收 query 字符串；可改 forked） | ⚠️ 共享 state schema 时会污染父 state；要写 wrapper function 隔离 |
| **图可观测性** | ⚠️ 子图被 @tool 包了一层，**不在 `get_graph()` 里** | ✅ 完整在 `get_graph()` 里，能 `draw_mermaid` |
| **事件流** | 主 agent 发出 `tool_call` event → 直接渲染 | 需 `stream.subgraphs` 投影，前端多一层 |
| **状态检查** | ❌ `get_state(subgraphs=True)` 看不到被 @tool 包住的子图 | ✅ 完整可见 |

### 3.2 排他性工具的处理复杂度对比

你说"排他性工具有两种实现方式"——**工具侧排队** vs **Agent 侧排队**。我分别评估每条路线下两种实现的成本。

#### 场景举例：4 个 profile tool 中哪些是排他性的？

回顾 `harness/report/内置工具应该自己实现还是调用中间件.md` + `harness/prompt/我的一些设计-最终敲定.md` 的内置工具清单：

| 工具 | 行为 | 排他性？ |
|---|---|---|
| `filesystem.py`（读/写/复制/移动/删除） | 单次 IO 操作几十 ms | ⚠️ **写操作排他**（防止两个 subagent 同时写同一个文件）；读操作可并发 |
| `filesearch.py`（glob/grep） | 只读，ripgrep 子进程 | ✅ 无排他性（只读，且 ripgrep 自己处理并发文件访问） |
| `commandline.py`（`subprocess.run`） | 单次执行几十 ms ~ 几分钟 | ⚠️ **强烈排他**（移动鼠标 = 单点设备 IO、长时间 shell、数据库 long-write 都在这一类） |
| `webfetch.py`（httpx） | 单次 HTTP 请求 | ✅ 无排他性（HTTP 服务端自己处理并发） |

→ 真正需要加锁的只有 `filesystem.py` 的**写操作** + `commandline.py` 的**所有操作**两类。颗粒度小，不是"所有工具都要加锁"。

#### 路线 A 下的加锁方案（推荐：工具侧非阻塞 + 立即报错）

> ⚠️ **早期方案曾考虑 FIFO 队列，但在"状态敏感型工具"（鼠标 / 文件写入 / 长时间 shell）上反语义**：晚到的 agent 基于过期状态做出的指令会被盲目执行，相互抵消。详见 §6.2.0 的鼠标反例。**最终方案是非阻塞 + 立即报错**。

锁放在**工具函数内部**，对工具作者透明：

```python
# tools/commandline.py
import asyncio

# 单例：整个进程一把非阻塞锁
_lock = asyncio.Lock()

BUSY_MESSAGE = (
    "此工具正在被其他智能体调用，此工具不允许同时被两个及以上智能体调用，"
    "具有排他性，请稍后再试。"
)

@tool
async def run_shell(command: str, timeout: int = 60) -> str:
    """Execute a shell command.

    Mutually exclusive: returns BUSY_MESSAGE immediately if another agent
    is currently using this tool. Do NOT block — caller should re-observe
    relevant state (running processes, file system, etc.) before retrying.
    """
    if _lock.locked():
        return BUSY_MESSAGE
    async with _lock:
        proc = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"Timeout after {timeout}s: command='{command}'"
        return stdout.decode()
```

**关键点**：
- 工具作者写 `if _lock.locked(): return BUSY_MESSAGE` + `async with _lock:`，无需知道 subagent 概念；
- 多个 subagent 并发调用 `run_shell` 时，**后到的 agent 立即拿到 BUSY_MESSAGE 返回**，不阻塞、不排队；
- agent 拿到 BUSY_MESSAGE 后被引导重新观察状态（鼠标位置 / 文件内容 / 进程列表），基于最新状态重新决策——这是 §6.2.0 论证的正确反馈环；
- 与 LangGraph 集成方式：零侵入——LangGraph 拿到 ToolMessage 后自然把决策权交给模型；
- 代码量：~20 行（含错误处理）。

#### 路线 B 下的"不加锁"方案

路线 B 默认串行执行子图节点，所有 subagent 工具天然不会并发，**理论上确实不用加锁**。

但有一个细节需要确认：**subagent 内部的 tool_call 也是串行的吗？**

**证据**：`harness/LangChain_doc/tools.md:1195` 仍然适用——不管 subagent 是怎么被启动的，它内部 `create_agent(...)` 的 ReAct 循环在一次模型响应里的多 tool_call **默认还是并发**。

也就是说：
- 路线 A：subagent 启动是并发的 + subagent 内部多 tool_call 是并发的 → 排他性工具需要锁
- 路线 B：subagent 启动是串行的 + subagent 内部多 tool_call 仍然是并发的 → **排他性工具还是要锁**（只要 subagent 内部可能并发调工具）

**结论**：即使走路线 B（默认串行 subagent 启动），只要某个 subagent 自己内部会并发调 `commandline.py`，还是得加锁——只不过触发概率比路线 A 低。

**真正能完全不加锁的场景**：subagent 内部工具全是无状态只读工具（glob、grep、http GET、webfetch）。但这要求**禁止 subagent 用 commandline.py 和写操作**——这等于阉割 subagent 的能力，不现实。

---

## 四、第三条路线：subgraph 包在 @tool 里（混合方案）

你问题里只提了两条，但社区还有第三条常见写法——既保留 OpenCode 的并发语义，又用 LangGraph 子图：

```python
# subagent 定义成 StateGraph 子图
researcher_subgraph = StateGraph(...).compile()

# 然后用 @tool 包一层
@tool
def ask_researcher(question: str) -> str:
    """Research using a specialist subagent."""
    result = researcher_subgraph.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content

# 主 agent 当工具调用
main_agent = create_agent(tools=[ask_researcher, ...])
```

→ 这条路线**实质上等价于路线 A**（并发 + 需要锁），**还多一层 @tool 包装**。优势是 subagent 的图结构在 `researcher_subgraph.get_graph()` 里能看到，但主图的 `get_graph()` 看不到。

**结论**：第三条路线没有显著优势，**不推荐**——直接走路线 A，用 `create_agent(...)` 当 subagent 更简单（官方 `subagents-personal-assistant.md` 示范代码就是这个写法）。

---

## 五、对你现有设计的硬约束适配性

回顾 `harness/prompt/我的一些设计-最终敲定.md` 第 62 行：

> 我使用过OpenCode，这个软件可以同时拉起多个sub agent。所以sub agent应该走@tool形式。但是LangChain没有subagent中间件，需要自己实现。

这条已经把路线定下来了。本报告只是验证这个选择 + 给出锁的实施方案。让我把硬约束逐条对照：

| 约束 | 路线 A 适配 | 路线 B 适配 |
|---|---|---|
| 不允许 `import deep_agents` 或 `managed_deep_agents` | ✅ 纯 LangChain | ✅ 纯 LangGraph |
| "100% 基于 LangChain 实现" | ✅ 全部来自 `langchain.tools` / `create_agent` | ✅ 全部来自 `langgraph.graph` |
| 仿照 OpenCode | ✅ OpenCode 是 subagent 并发模型 | ❌ 路线 B 失去并发性，违背 OpenCode 行为 |
| "工作区即 agent" | ✅ subagent 文件放在 `workspace/subagents/`（参考 `donkey/example/` 模板） | ✅ 同上 |
| 单 agent 多 session 模式 | ✅ 单 agent 内 subagent 并发跑多 session 不冲突 | ✅ 同上 |
| "小白极简"哲学 | ✅ `agent.py` 多写 30 行 `@tool` 包装 | ⚠️ 子图定义 + Send fan-out 比 @tool 包一层更复杂 |
| 可定制（用户加新 subagent） | ✅ 用户在 `subagents/` 加一个文件，`agent.py` 加载 | ⚠️ 用户要懂 LangGraph 图 API |
| 排他性工具加锁 | ⚠️ 需要 ~30 行 `commandline.py` 加锁代码 | ⚠️ subagent 内部并发场景下也需要锁 |

---

## 六、推荐结论

**路线 A（@tool 形式）是 donkey 的正确选择**。理由汇总：

### 6.1 直接理由

1. **路线 A 是 LangChain 官方推荐的 subagent 写法**（`subagents.md §Tool per agent` 全章示范 + `subagents-personal-assistant.md` 完整 demo），不是冷门方案。
2. **路线 A 原生支持并发**，与 OpenCode 行为一致；路线 B 要并发得额外写 Send fan-out，比路线 A 复杂。
3. **路线 A 的"锁"工作量可控**：4 个 profile tool 里只有 `commandline.py` 和 `filesystem.py` 写操作需要锁，~20 行非阻塞立即报错代码，**与项目其余部分的复杂度量级一致**（参见 `LangChain复刻agent.py的可行性分析.md` 里 `skills_loader.py` 也是 ~50 行）。**关键的是不能用 FIFO 队列**——详见 §6.2.0 的鼠标反例。
4. **路线 B 以为"不需要锁"是错觉**——subagent 内部多 tool_call 仍然并发（`tools.md:1195`），只要 subagent 用到 `commandline.py` 就还是要锁。所以路线 B 并不省事，只是把锁的触发面缩小了。
5. **`我的一些设计-最终敲定.md` 第 62 行已经选定了路线 A**，本报告只是把这个选择的合理性 + 锁实施方案补完整。

### 6.2 锁的实施方案（最终推荐）：工具侧非阻塞 + 立即报错

#### 6.2.0 关键设计判断：为什么不能是 FIFO 队列

排他性工具（如鼠标移动、长时间 shell、数据库 long-write）有一个共性——**它们的操作基于"执行前的世界状态"做出决策，但执行期间世界状态会被前一个调用方改变**。这意味着晚到的调用方如果排队等待后执行，它基于的"执行前状态"已经过期，指令叠加会产生语义错误。

**反例**（用 OpenCode 的鼠标场景）：

> 假设两个 subagent A、B 都观察到了鼠标当前位置 `(100, 100)`。
> - A 决策：左移 30 像素（意图：到 `(70, 100)`）
> - B 决策：右移 50 像素（意图：到 `(150, 100)`）
> 
> **方案 1：FIFO 队列**
> - A 先执行：从 `(100, 100)` → `(70, 100)`
> - B 排队后执行：从 `(70, 100)` → `(120, 100)`
> - B 以为自己的指令是"右移 50"，结果实际只右移了 20（因为鼠标已经先被 A 移到 70）
> - **两个指令相互抵消，B 的最终效果是右移 20 像素**
> - B 拿到结果 `(120, 100)`，以为"右移 50"的目标没达成（差异 30），做出错误的下游决策
> 
> **方案 2：立即报错**
> - A 先执行：从 `(100, 100)` → `(70, 100)`
> - B 调用时收到 `"工具正被占用"` 的 ToolMessage
> - **B 知道状态可能变了，重新调"获取鼠标位置"工具**，看到真实位置 `(70, 100)`
> - B 基于最新状态重新决策（要么继续右移 50 到 `(120, 100)`，要么改主意不移动）

**结论**：FIFO 队列在"基于状态决策"的工具上是**反语义**的——它会盲目执行已经过时的指令。**立即报错把决策权交还给 agent，让 agent 基于最新状态重新规划**——这才是正确的反馈环。

文件系统写入同理：

> 两个 subagent 都观察到 `output.txt` 是空的，都决定追加内容。
> - FIFO 队列：两个 append 串行执行，最终文件内容是两段拼起来（**可能正确也可能错误**，取决于是否真有冲突，但 agent 无法察觉）
> - 立即报错：第二个 subagent 收到"工具被占用"，重新读 `output.txt` 看到已有内容，**决定是覆盖还是改写到新文件**

命令行执行也是：

> A 跑 `rm -rf build/ && make`，耗时 10 秒；B 在第 5 秒也想跑 `rm -rf build/ && make`。
> - FIFO：B 排队等 A 跑完，再跑一次 `rm -rf build/ && make`——冗余执行
> - 立即报错：B 看到 `make` 已经在跑（或 build/ 目录不存在），决定等会儿再跑或不跑

**因此 FIFO 队列在本项目里被排除。**

#### 6.2.1 三种方案对比

| 方案 | 锁位置 | 行为 | 推荐度 |
|---|---|---|---|
| **A1：工具侧非阻塞 + 立即报错** | 工具函数内部 | 已锁定 → 立即返回 BUSY_MESSAGE 给 ToolMessage | ✅ **推荐** |
| A2：锁住整个 subagent 生命周期 | `@tool` 包装最外层 | subagent 启动取锁，返回结果释放 | ❌ 粒度太粗 |
| A3：工具侧 FIFO 队列 | 工具函数内部 | 已锁定 → 排队等待 | ❌ **反语义**（见 6.2.0） |

#### 6.2.2 方案 A1（推荐）的具体设计

- **锁对象**：`commandline.py`（必须）+ `filesystem.py` 的**写操作**（必须）；只读工具（`filesearch.py`、`webfetch.py`、filesystem 读操作）**不需要**加锁。
- **锁位置**：工具函数内部，`asyncio.Lock.locked()` 探测 + `async with _lock:` 获取。
- **锁语义**：非阻塞。已锁定 → 立即返回错误字符串 → agent 重新观察状态 → 重新决策。
- **错误消息**（固定文案）：
  > "此工具正在被其他智能体调用，此工具不允许同时被两个及以上智能体调用，具有排他性，请稍后再试。"
- **代码量**：~20 行/工具（含错误处理）。
- **与 LangGraph 集成方式**：零侵入——工具作者写 `async with _lock:`，LangGraph 拿到 ToolMessage 后自然把决策权交给模型。
- **agent 侧提示词要求**：在 `instructions.md` 里加一行——"调用排他性工具（commandline、写文件）时若收到'工具正被占用'错误，请先重新观察相关状态（鼠标位置、文件内容、运行进程），再决定是否重试或改用其他方案"。

#### 6.2.3 方案 A2 的具体设计（不推荐）

- **锁位置**：subagent 的 `@tool` 包装函数最外层。
- **锁语义**：subagent 启动时取锁，返回结果时释放。
- **缺点**：粒度太粗——一个 subagent 跑 5 轮，其中只有 1 轮调 `commandline.py`，其他 4 轮白白阻塞；并发性严重退化。
- **额外缺点**：subagent 内部多 tool_call 仍然并发（A1 也覆盖了这种情况，但 A2 反而不覆盖），所以 A2 既粗又不全。

#### 6.2.4 方案 A3 的具体设计（不推荐）

- **锁位置**：工具函数内部，`asyncio.Lock` + `deque[Future]`。
- **锁语义**：已锁定 → 入队等待 → 前一个释放后唤醒下一个。
- **致命问题**：见 §6.2.0 的鼠标反例——基于过期状态的指令被盲目执行，**状态敏感型工具上完全反语义**。
- **退化情形**：哪怕工具不是状态敏感的（纯计算型），FIFO 排队会让 agent loop 在 tool_call 阶段长时间挂起，模型无法继续思考，对长任务也不友好。

### 6.3 实施 checklist（路线 A 落地步骤）

按从简到难的顺序：

1. **定义 subagent 目录结构**（`harness/prompt/我的一些设计-最终敲定.md` 已经在 `donkey/example/default/subagents/` 留了占位目录）：
   ```
   workspace/subagents/
     __init__.py
     researcher.py          # subagent = create_agent(...)，导出 researcher
     writer.py
   ```
   每个文件暴露 `subagent_name = create_agent(model, tools, system_prompt)`。

2. **`@tool` 包装函数**（放在 `workspace/agent.py` 或 `workspace/subagents/__init__.py`）：
   ```python
   from langchain.tools import tool
   from subagents.researcher import researcher
   from subagents.writer import writer

   @tool
   def call_researcher(query: str) -> str:
       """Research a topic and synthesize findings."""
       result = researcher.invoke({"messages": [{"role": "user", "content": query}]})
       return result["messages"][-1].content

   @tool
   def call_writer(query: str) -> str:
       """Write content based on a brief."""
       result = writer.invoke({"messages": [{"role": "user", "content": query}]})
       return result["messages"][-1].content

   main_agent = create_agent(
       model=llm,
       tools=[..., call_researcher, call_writer],  # subagent 与普通 tool 平级
       system_prompt=...,
       middleware=[...],
   )
   ```

3. **排他性工具加锁**（`workspace/tools/commandline.py`，方案 A1：非阻塞立即报错）：
   ```python
   import asyncio

   _lock = asyncio.Lock()  # 进程单例

   BUSY_MESSAGE = (
       "此工具正在被其他智能体调用，此工具不允许同时被两个及以上智能体调用，"
       "具有排他性，请稍后再试。"
   )

   @tool
   async def run_shell(command: str, timeout: int = 60) -> str:
       """Execute a shell command.

       Mutually exclusive: returns BUSY_MESSAGE immediately if another agent
       is currently using this tool. Do NOT block — caller should re-observe
       relevant state (running processes, file system, etc.) before retrying.
       """
       if _lock.locked():
           return BUSY_MESSAGE
       async with _lock:
           proc = await asyncio.create_subprocess_shell(
               command,
               stdout=asyncio.subprocess.PIPE,
               stderr=asyncio.subprocess.PIPE,
           )
           try:
               stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
           except asyncio.TimeoutError:
               proc.kill()
               return f"Timeout after {timeout}s: command='{command}'"
           return stdout.decode()
   ```

   `filesystem.py` 的写操作（`write_file` / `delete_file` / `move_file`）加同样的锁，读操作不加。`filesearch.py` 和 `webfetch.py` 不加锁（只读 + 无状态）。

4. **README 文档**（`workspace/subagents/README.md`）：教用户怎么加新 subagent，参考 `harness/LangChain_doc/multi-agent/subagents.md`。

5. **HITL 配置**：`HumanInTheLoopMiddleware(interrupt_on={..., "call_researcher": True, "call_writer": True})`——subagent 本身已经被隔离，子图内部如果还调 `run_shell`/`write_file`，HITL 在**主图层**冒泡（`use-subgraphs.md:693` 末句），不需要在子图内部重复配。

### 6.4 一个反直觉的额外收益

路线 A 的 `@tool` 包装其实给前端**提供了一个清晰的 subagent 调用卡片渲染点**：

```python
@tool
def call_researcher(query: str) -> str:
    """..."""
```

`@tool` 装饰器自动生成 tool schema，前端拿到 `tool_call.name == "call_researcher"` 就能识别"这是一个 subagent 调度"，渲染成"🚀 启动研究员 subagent"的卡片，而普通工具 `read_file` 渲染成"📄 读取文件"卡片。

如果走路线 B（add_node），前端要靠 namespace 路径区分是 subagent 节点还是普通节点，渲染逻辑更复杂。

---

## 七、FAQ

### Q1: 路线 B 是不是也能并发？

是的，但需要写 Send fan-out + reduce 节点，比路线 A 复杂，且事件流要 `stream.subgraphs` 投影。**结论**：路线 B 想要并发等于做两遍路线 A 的事（既写 @tool 又写 Send），不如直接走 A。

### Q2: 路线 B 是不是完全没用？

不是。如果**确定不需要并发**（比如某个 profile 只有 1 个 subagent，且只在小任务里跑），路线 B 有可观测性优势——subagent 图节点在 `agent.get_graph().draw_mermaid()` 里能看到。但 donkey 是通用型 agent 引擎，不能假设用户只用 1 个 subagent。

### Q3: 锁加在哪里最干净？

工具侧。理由：
- 工具作者知道自己的工具是否排他（filesystem 写操作是，glob 不是），写在工具内部最自然；
- Agent 侧加锁意味着每个使用排他工具的 subagent 都要写 `@tool` 包装逻辑，**违反"用户加新 subagent 无需关心锁"的简洁原则**；
- 工具侧加锁对 subagent 和普通 agent 调用**都生效**——一个工具不管被谁调，排他性都一样。

### Q4: 如果用户用线程而不是 asyncio 怎么办？

`asyncio.Lock` 是为 LangGraph 默认的 async tool execution 设计的。LangChain 的 `@tool` 默认在 async 上下文跑（`create_agent` 内部用 `astream`）。**单线程同步调用不存在"并发"问题**——一个 Python 进程一个 GIL，sync tool_call 不会真的并发执行；只有 async + 并发 tool_call 才会触发锁探测（`lock.locked()`）。

### Q5: 命令行执行时间过长时怎么办？

`run_shell(timeout=60)` 已有 `asyncio.wait_for` 掐断。**锁是非阻塞的**，A 在跑 60 秒的 `make` 时，B 调用 `run_shell` 立即拿到 BUSY_MESSAGE 返回，**不会**让 B 的 agent loop 挂起——B 立刻知道"工具有人在用"，可以决定是观察相关进程状态、改用其他工具，还是等会儿再试。

这种"立即失败 + 让 agent 重新规划"的反馈环比 FIFO 排队（让 B 傻等 60 秒再盲目执行已过时的命令）更符合 LLM 决策的需求。

### Q6: 多个 subagent 同时收到 BUSY_MESSAGE，会不会陷入死循环？

理论上可能——A、B 都看到 BUSY_MESSAGE，都重试，都再次收到 BUSY_MESSAGE，循环下去。

**应对**：
1. **在 BUSY_MESSAGE 里建议退避**：把消息改成"请稍候片刻（建议等 1-5 秒）后重试"，让模型自行 sleep。
2. **在 instructions.md 加反退化提示**："如果连续收到 BUSY_MESSAGE 且任务不紧急，请改用其他非排他性工具（glob / grep / webfetch）或等待更长时间"。
3. **工具侧暴露一个简单统计**：`run_shell` 返回值如果是 BUSY_MESSAGE，可以附带当前锁持有者的预计剩余时间（如果可预估的话），让模型做更明智的退避。

对于 donkey 这个 hello agent 级别的项目，第 1、2 条已经足够；第 3 条作为可选增强。

---

## 八、总结

| 评估维度 | 路线 A：@tool | 路线 B：子图 |
|---|---|---|
| **并发支持** | ✅ 原生（`tools.md:1195`） | ⚠️ 需 Send fan-out |
| **HITL 透传** | ✅ 自然 | ✅ 自然 |
| **图可观测性** | ⚠️ 子图被 @tool 包装，父图看不到 | ✅ `get_graph()` 完整可见 |
| **前端事件流** | ✅ tool_call event 直接渲染 | ⚠️ 需 `stream.subgraphs` 投影 |
| **锁的工作量** | ~20 行（仅 `commandline.py` + `filesystem.py` 写，非阻塞立即报错） | ~20 行（subagent 内部并发场景下同样需要） |
| **实施复杂度** | 低（`@tool` 包一层 + 锁） | 高（StateGraph + Send fan-out + reduce） |
| **用户学习曲线** | 平（写 `create_agent` + `@tool`） | 陡（要懂 LangGraph 图 API） |
| **与 OpenCode 行为一致** | ✅ | ❌ |
| **与项目既有设计一致** | ✅（`我的一些设计-最终敲定.md:62` 已选 A） | ❌ |
| **推荐** | **✅** | ❌ |

**最终推荐**：**路线 A（@tool 形式）+ 工具侧非阻塞立即报错锁**。

- subagent 当 `@tool`，主 agent 通过 tool_call 并发调度（LangGraph 原生支持，`tools.md:1195`）；
- 排他性工具（`commandline.py` + `filesystem.py` 写）在工具内部用 `asyncio.Lock.locked()` 探测 + `async with _lock:` 获取；已锁定时立即返回固定 BUSY_MESSAGE；
- agent 收到 BUSY_MESSAGE 后，**重新观察相关状态**（鼠标位置 / 文件内容 / 进程列表），再决定下一步——这正是 LLM 应该做的，而不是傻等 FIFO；
- 用户加新 subagent 只需在 `workspace/subagents/` 写一个 `create_agent(...)` + `@tool` 包装，**无需关心锁**。

**为什么不用 FIFO 队列**：见 §6.2.0 的鼠标反例——FIFO 会让基于过期状态做出的指令被盲目执行，**相互抵消**产生语义错误；立即报错把决策权交还给 agent，让 agent 基于最新状态重新规划，才是正确的反馈环。

这个方案已经在 `harness/prompt/我的一些设计-最终敲定.md:62` 有了原则性表述，本报告把它落地为具体的锁实现 + 装配步骤 + FAQ。
