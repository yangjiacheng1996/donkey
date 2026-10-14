我先把目录约定记下：

> donkey 仓库根布局：`/home/ctyun/workspace/github/donkey/`（含 `donkey/`, `harness/`, `.specify/` 等）
> Python 包名：`donkey/` （即 `import donkey`）
> profile 目录：`donkey/example/` —— 模板文件随包 `pip install` 分发，用户通过 `donkey init` / `donkey-cli new` 复制到 `agents/<name>/` 或外部路径

下面回答你 deepagents vs LangChain 的取舍问题，并据此给出 `<donkey_project_root>/donkey/example/` 目录的模板文件清单。

---

## 一、deepagents 与 LangChain `create_agent` 的本质区别

先看清楚两者在做什么：

| 层级 | LangChain `create_agent` | deepagents `create_deep_agent` |
|---|---|---|
| 是什么 | 一个工厂函数，返回一个 LangGraph 图 | 一个**预装配的 agent harness**，内部调 `create_agent` 但预先塞了 5 个中间件 + 1 个 backend 抽象 |
| 输入 | `model / tools / system_prompt / middleware / checkpointer / store` | 上面 6 个 **+** `backend / skills / subagents / permissions` |
| 默认行为 | 完全空白 —— 你不传 middleware 就只有裸 ReAct 循环 | 自动装配 `FilesystemMiddleware + SummarizationMiddleware + MemoryMiddleware + SkillsMiddleware + SubAgentMiddleware` |
| 暴露的 LangGraph 节点 | `START → model → tools → model → END`（干净 3 节点） | 在 model/tools 之间插了一堆中间件节点，节点图复杂（13+ 节点） |
| 后端抽象 | 没有 —— tool 自己管状态 | 引入 `Backend Protocol`：StateBackend（state 临时）/ StoreBackend（store 持久）/ FilesystemBackend（磁盘）/ CompositeBackend（混合） |

**关键事实**：`create_deep_agent` 是用 `create_agent` 实现的。你用 `create_deep_agent` 的每一项能力，理论上都能用 `create_agent` + 几个 `from deepagents.middleware import ...` 拼出来——只是 deepagents 帮你写好了默认配置。

---

## 二、用 deepagents 你**具体**牺牲什么

我按你的硬约束逐条对照：

### 牺牲 1：失去对内置 profile tool 的控制权

deepagents 默认装配的中间件会向模型注入**固定名字**的工具：

| deepagents 中间件 | 注入的工具名 | 你的 profile tool |
|---|---|---|
| `FilesystemMiddleware` | `ls / read_file / write_file / edit_file` | `filesystem.py`（读写复制本地文件） |
| `ShellToolMiddleware`（若启用） | `shell` + `execute` | `commandline.py`（执行系统命令） |
| `SkillsMiddleware` | `read_skill`（按需） | 你 SKILL.md 用 `load_skill` 工具加载 |

**冲突**：模型看到两个 `read_file` 不知道选哪个；GUI 客户端渲染工具调用卡片也得处理两套同名 UI。

**取舍**：
- 用 deepagents → 删掉 `filesystem.py` / `commandline.py` profile tool，让 deepagents 接管
- 用 `create_agent` → 保留你的内置 3 个 profile tool，干净可控

### 牺牲 2：虚拟文件系统 vs 真实文件系统的语义分裂

deepagents 的 `FilesystemMiddleware` 默认把 `read_file` / `write_file` 路由到 **`StateBackend`**——也就是 LangGraph state（短期，会话结束就没了）或 `StoreBackend`（长期，跨 session）。

用户用 `filesystem.py` profile tool 直接读磁盘是另一个语义：

```
用户问："打开 notes.txt"
  路线 A（deepagents StateBackend）：读取临时 state 里的文件，会话结束消失
  路线 B（filesystem.py 直接 IO）：读取磁盘文件，下次还在
```

**取舍**：如果你想 profile tool 直接操作磁盘（你的设计里 "donkey init 后 workspace 自动有 filesystem.py" 就是这个意思），deepagents 的虚拟 FS 反而是干扰项。

### 牺牲 3：图结构变得不可调试

`create_deep_agent` 返回的图，节点包含：
- `__start__`
- `before_agent` × N（多个 hook 串起来）
- `FilesystemMiddleware.before_model`
- `SummarizationMiddleware.before_model`
- `SkillsMiddleware.wrap_model_call`（最外层 wrap）
- `model`
- `SkillsMiddleware.wrap_model_call`（最内层 wrap）
- `SummarizationMiddleware.after_model`
- `FilesystemMiddleware.after_model`
- `after_agent` × N
- `tools`（含 `ls/read_file/write_file/edit_file` + 用户的工具）
- `__end__`

→ `agent.get_graph().draw_mermaid()` 输出十几行。HITL 中断排障时很难一眼看清"在哪个中间件里停了"。

`create_agent` 的图就是教科书式的：

```
__start__ → before_model → model → tools → model → ... → __end__
```

### 牺牲 4：依赖锁死在 deepagents 的发布节奏

看 `LangChain_doc/changelog-py.md` 的记录：
- `create_deep_agent` 在 v0.4.x 把 `TodoListMiddleware` 从默认装配移除
- `backend=` 参数签名从 `backend=callable` 改成 `backend=StoreBackend(namespace=callable)`
- v0.6.x `permissions=` API 引入，旧用法废弃

**这意味着**：deepagents 包的 minor 版本升级可能 break 你的 profile。一旦你把它选成默认入口，donkey 项目的依赖升级测试工作量翻倍。

### 牺牲 5：`shell` 工具与持久 session 的冲突（已知官方限制）

`LangChain_doc/middleware/built-in.md §Shell tool` 的 Note 明确：
> "Persistent shell sessions do not currently work with interrupts (human-in-the-loop)."

deepagents 的 `ShellToolMiddleware` 默认是**持久 shell session**（多次 invoke 共享同一个 shell 进程）。

如果你要 `HumanInTheLoopMiddleware`（你规定必须开启），且 `shell` 工具触发 HITL，**官方目前不支持**——会卡死。

**解决**：必须用 `ShellToolMiddleware(workspace_root=None)`（临时 session，每次新建），但这不是 deepagents 的默认行为。

### 牺牲 6：与"小白极简"哲学的内在冲突

deepagents 自动注入 5 个中间件 = 默认 8+ 工具（4 个 FS 工具 + shell + 可能的 subagent tools + 用户 tools）。一个 hello agent profile 一启动，模型面对的就是 8 个工具描述，system prompt 被塞满中间件提示。

你的"设计哲学"原文：
> "避免「默认配置太重」侵蚀用户"

deepagents 的"开箱即用"恰恰是**默认配置很重**——它假设你要做长任务、虚拟 FS、子智能体、todo 规划。Hello agent 用户全都不需要。

### 牺牲 7：失去"我能 100% 解释这个 agent 怎么跑"的能力

`create_agent` 的每一段行为都是用户写的（用户显式 import 每个中间件、显式写 `middleware=[...]`）。

`create_deep_agent` 隐式装配——出错时报错栈来自 deepagents 内部，**用户的代码里看不到**。HITL 卡住、上下文压缩丢失信息、skill 加载失败…… 都得去翻 deepagents 源码。

---

## 三、用 deepagents 你**得到**什么（具体到你的设计）

| 能力 | 价值 | 是否必须 |
|---|---|---|
| **Skills 一行启用**（`skills=["./skills/"]`） | 不用手写 30 行 `SkillMiddleware` | **否**——`harness/LangChain_doc/multi-agent/skills-sql-assistant.md` 给出了完整 `SkillMiddleware` 实现 |
| **Subagent 字典语法**（`subagents=[{name, description, system_prompt, tools}]`） | 不用 `@tool` 包一层 `subagent.invoke` | **否**——`harness/LangChain_doc/multi-agent/subagents.md` §Tool per agent 给出 `@tool` 包装写法 |
| **虚拟文件系统**（4 个工具 + state/store 后端路由） | 用户不用自己写 `filesystem.py` | **是**——但你的硬约束要求 profile 内置 `filesystem.py`，所以这是**冲突**而非补充 |
| **SummarizationMiddleware 默认带** | 省一行配置 | **否**——`from langchain.agents.middleware import SummarizationMiddleware` 也就一行 |
| **TodoListMiddleware 默认带** | 多步任务自动规划 | **否**——同上，且 deepagents 新版本默认已移除 |

**结论**：deepagents 真正不可替代的便利只有 "Skills + Subagent 一行配置"，其他都能用 `create_agent` 拼出来。

---

## 四、我的最终建议

考虑到你的硬约束 + 设计哲学，我建议**采用双轨制**：

```
agents/
├── default/              # 极简 hello agent，用 create_agent（小白开箱即用）
└── deep_research/        # 高级模板，用 create_deep_agent（专业用户复制）
```

- **默认 profile（`agents/default/`）用 `create_agent`**：
  - 保留 `filesystem.py / commandline.py / webfetch.py` 三个内置 profile tool
  - 用户需 Skills → 自己写 30 行 `SkillMiddleware`（参考 `skills-sql-assistant.md`）
  - 用户需 Subagent → `@tool` 包一层（参考 `subagents.md`）
  - 符合"小白极简 / 工作区即 agent / 不重复造轮子"

- **`agents/deep_research/` 用 `create_deep_agent`**：
  - 不带 `filesystem.py / commandline.py` profile tool（deepagents 接管）
  - 一行 `skills=["./skills/"]` 启用 Skills
  - 一行 `subagents=[{...}]` 启用 Subagent
  - 标注 "高级模板，删除 `filesystem.py / commandline.py` profile tool"

这样：

| 用户类型 | 复制路径 | 入口 |
|---|---|---|
| 小白（90%） | `donkey-cli new my-agent` （= 复制 `default/`） | `create_agent` |
| 高级（10%） | `donkey-cli new my-research --from deep_research` | `create_deep_agent` |

**文档里说清**："两个模板不能混用——`deep_research/` 模板里没有 `filesystem.py` profile tool，因为 deepagents 的虚拟文件系统已覆盖；如果你复制 default 后想用 deepagents 能力，需要自己删掉 3 个 profile tool 并改 `agent.py` 入口。"

---

## 五、`donkey/example/` 目录的具体模板文件清单

按你的 pip 分发要求，`donkey/example/` 是**模板源**，实际部署到 `agents/<name>/` 后才是可运行的 profile。文件清单：

```
donkey/example/
├── README.md                                    # 模板目录说明（不复制）
├── default/                                     # 默认 profile（极简 create_agent）
│   ├── README.md                                # 模板说明（不复制到 agents/<name>/）
│   ├── instructions.md                          # "You are my helpful assistant."
│   ├── agent.py                                 # create_agent(...) 示例
│   ├── tools/
│   │   ├── get_time.py                          # 示例 @tool
│   │   └── echo.py
│   ├── middleware/
│   │   └── __init__.py                          # 保留空，提示用户在此加自定义
│   ├── skills/
│   │   └── hello/
│   │       └── SKILL.md                         # 示例 skill
│   ├── subagents/
│   │   └── __init__.py                          # 空目录占位
│   └── tests/
│       └── test_smoke.py
├── deep_research/                               # 高级模板（create_deep_agent）
│   ├── README.md                                # 模板说明 + "需要 deepagents 包"
│   ├── instructions.md
│   ├── agent.py                                 # create_deep_agent(...) 示例
│   ├── tools/
│   │   └── web_search.py
│   ├── middleware/
│   │   └── __init__.py
│   ├── skills/
│   │   ├── research/
│   │   │   └── SKILL.md
│   │   └── report_writer/
│   │       └── SKILL.md
│   ├── subagents/
│   │   └── researcher.py                        # 字典形式 subagent 定义
│   └── tests/
│       └── test_smoke.py
└── pyproject.toml.tmpl                          # 可选：profile 独立依赖时的模板（v0.4 已删除）
```

**关键文件 `agents/default/agent.py` 内容（建议）**：

```python
"""Default hello agent. Edit this file to customize."""
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    SummarizationMiddleware,
)
from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path

from tools.get_time import get_time
from tools.echo import echo

PROFILE_NAME = "default"
SESSION_DIR = Path(__file__).resolve().parent / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# 单个 checkpointer 配 InMemorySaver 作为占位；
# 真正每个 thread_id 一个独立 .sqlite 文件由 donkey runtime 注入
checkpointer = SqliteSaver.from_conn_string(
    str(SESSION_DIR / "_base.sqlite"), serde=...  # serde 由 runtime 注入
)

agent = create_agent(
    model="openai:gpt-5.5",          # 实际由 donkey runtime 注入 init_chat_model
    tools=[get_time, echo],
    system_prompt="You are my helpful assistant.",
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-5.4-mini",  # 用便宜模型摘要
            trigger=("tokens", 6000),
            keep=("messages", 20),
        ),
        HumanInTheLoopMiddleware(
            interrupt_on={
                # 用户在此配置需要审批的工具
            },
        ),
    ],
    checkpointer=checkpointer,
)
```

**注意**：`agent.py` 里的 `model=` 和 `checkpointer=` 都是**占位**，donkey runtime 在 graph_compose 阶段会：
1. 解析 `agent.py` AST 拿到 `agent = create_agent(...)` 的关键字参数
2. 注入 `model=init_chat_model(...)`（从 `.env` / 启动参数）
3. 注入真实的 `checkpointer=...`（运行时 SqliteSaver，按 thread_id 选文件）
4. 再调用 `create_agent` 生成实际图

如果 runtime 不做 AST 改写，就需要用户在 `agent.py` 里写：

```python
import os
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model=os.environ.get("LLM_MODEL", "openai:gpt-5.5"),
    model_provider="openai",
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)
```

这两条路径你倾向哪个？

---

## 六、需要你确认的决策点

1. **入口策略**：A. 默认 `create_agent` + 高级模板 `create_deep_agent` 双轨（我推荐） / B. 只用 `create_agent`（最简，但用户写 Skills/Subagent 要自己写中间件） / C. 只用 `create_deep_agent`（便利多但要删 `filesystem.py/commandline.py` profile tool）
2. **`agent.py` 的 model / checkpointer 注入方式**：A. 用户在 `agent.py` 里 `os.environ[...]` 显式读（透明、无黑魔法） / B. donkey runtime 做 AST 改写（用户 `agent.py` 干净但 runtime 复杂） / C. 用 `create_agent(model="placeholder:xxx")` 占位 + runtime monkey patch（脆弱，不推荐）
3. **`donkey/example/` 目录**：双模板（`default/` + `deep_research/`）还是单模板（只用 `default/`）？