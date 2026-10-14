| # | Middleware | 用途 | 来源 | import 路径 | 证据 |
|----|------------|------|------|------------|------|
| 1  | ToolErrorMiddleware | 捕获工具执行时抛出的异常，将其转成 `ToolMessage(status="error")` 反馈给模型，让模型能够自我修正参数并重试，而不是直接中断 agent 运行。可与 `ToolRetryMiddleware` 配合：在内部重试失败时再接管异常。 | LangChain 专有 | `from langchain.agents.middleware import ToolErrorMiddleware` | `built-in.md:57` |
| 2  | ToolRetryMiddleware | 工具调用失败时按指数退避自动重试，应对外部 API 的瞬时网络故障。可配最大重试次数、初始/最大延迟、抖动以及失败后行为（继续/抛错/自定义）。 | LangChain 专有 | `from langchain.agents.middleware import ToolRetryMiddleware` | `built-in.md:145` |
| 3  | ModelRetryMiddleware | 模型调用失败时按指数退避自动重试，处理模型 API 的瞬时错误（429/503 等）。可配退避参数和失败处理（返回错误消息或重新抛异常）。 | LangChain 专有 | `from langchain.agents.middleware import ModelRetryMiddleware` | `built-in.md:253` |
| 4  | ModelFallbackMiddleware | 主模型调用失败时按顺序回退到备用模型，构建跨供应商的容灾能力，常用于成本优化（主模型失败降级）和服务兜底。 | LangChain 专有 | `from langchain.agents.middleware import ModelFallbackMiddleware` | `built-in.md:390` |
| 5  | SummarizationMiddleware | 当消息历史接近 token 限制时，自动用 LLM 把旧消息压缩成摘要，保留最近 N 条（或 M tokens / F 上下文比例），从而在长会话中维持上下文窗口。仅压缩文本，多模态块按原样保留在未截断消息里。 | 两个框架都有 | `from langchain.agents.middleware import SummarizationMiddleware`（canonical）<br/>或 `from deepagents.middleware import SummarizationMiddleware`（re-export） | LangChain：`built-in.md:434`、`short-term-memory.md:544`、`context-engineering.md:1144`<br/>DeepAgents：`agents.md:1107+`、`deep-agent-from-scratch.md:348+`<br/>Reference URL：`reference.langchain.com/python/langchain/agents/middleware/summarization/...` |
| 6  | HumanInTheLoopMiddleware | 在执行高风险工具（写库、转账、发邮件等）前中断 agent，等待人类 approve / edit / reject 后再恢复。必须配置 `checkpointer` 维持中断状态。 | LangChain 专有 | `from langchain.agents.middleware import HumanInTheLoopMiddleware` | `built-in.md:634`、`sql-agent.md:270`、`agents.md:1901+` |
| 7  | ModelCallLimitMiddleware | 限制单次 run 或整条 thread 内的模型调用次数，防止 agent 失控循环、烧光 API 配额或成本失控。 | LangChain 专有 | `from langchain.agents.middleware import ModelCallLimitMiddleware` | `built-in.md:683` |
| 8  | ToolCallLimitMiddleware | 限制工具调用次数（全局或按工具名），可分别配置 thread 级和 run 级上限。用于防止特定工具被刷爆、agent 死循环或外部 API 被限流。 | LangChain 专有 | `from langchain.agents.middleware import ToolCallLimitMiddleware` | `built-in.md:731` |
| 9  | PIIMiddleware | 检测并处理 PII：内置支持 email/credit_card/ip/mac_address/url 等类型，可配置 redact（替换）/mask（局部遮蔽）/hash（哈希）/block（抛错）策略，可应用到输入、输出、流式输出或工具结果。 | LangChain 专有 | `from langchain.agents.middleware import PIIMiddleware` | `built-in.md:823`、`agents.md:1760+` |
| 10 | TodoListMiddleware | 为 agent 注入 `write_todos` 工具与配套系统提示，使其能够规划多步计划并跟踪进度，适合需要协调多工具、多步骤的复杂任务。 | LangChain 专有 | `from langchain.agents.middleware import TodoListMiddleware` | `built-in.md:986`；`changelog-py.md:71-78` 明确写"not `deepagents`"，deepagents v0.7 不再 re-export |
| 11 | LLMToolSelectorMiddleware | 在调用主模型前先用一个小模型（或主模型）对工具列表做筛选，仅把与当前查询最相关的 K 个工具喂给主模型，减少 token 消耗并提高选择准确性，适合工具数 10+ 的场景。 | LangChain 专有 | `from langchain.agents.middleware import LLMToolSelectorMiddleware` | `built-in.md:1023` |
| 12 | ProviderToolSearchMiddleware | 把部分工具藏在模型供应商的服务端 tool search 后按需调出，避免一次性把所有工具 schema 塞进 prompt。仅 Anthropic Sonnet 4+/Opus 4+/Haiku 4.5+、OpenAI gpt-5.5+ 等支持服务端工具搜索的模型可用。 | LangChain 专有 | `from langchain.agents.middleware import ProviderToolSearchMiddleware` | `built-in.md:1073` |
| 13 | ShellToolMiddleware | 向 agent 暴露一个持久 shell 会话，使其可以跑命令、执行脚本、操作文件系统。可通过 `HostExecutionPolicy`（默认）/`DockerExecutionPolicy`/`CodexSandboxExecutionPolicy` 调整安全边界。注意：持久会话与 `HumanInTheLoopMiddleware` 不兼容。 | LangChain 专有 | `from langchain.agents.middleware import ShellToolMiddleware, HostExecutionPolicy` | `built-in.md:1137` |
| 14 | FilesystemMiddleware | 为 agent 注入 `ls`/`read_file`/`write_file`/`edit_file` 四个文件系统工具。backend 抽象（默认 `StateBackend` 存在图状态；可用 `CompositeBackend` 把 `/memories/` 路由到持久 `StoreBackend`）实现跨线程长期记忆。 | DeepAgents 专有 | `from deepagents.middleware.filesystem import FilesystemMiddleware`<br/>或 `from deepagents.middleware import FilesystemMiddleware` | `built-in.md:1271`、`built-in.md:1297`、`agents.md:1002-1074` |
| 15 | SubAgentMiddleware | 向主 agent 暴露 `task` 工具，使其可以派生子 agent 处理子任务。子 agent 拥有独立上下文，结果以简短摘要返回，避免主 agent 上下文被中间工具调用污染。还支持包装自定义 LangGraph 图作为子 agent。 | DeepAgents 专有 | `from deepagents.middleware.subagents import SubAgentMiddleware` | `built-in.md:1332`、`built-in.md:1367` |
| 16 | RubricMiddleware (Beta) | 允许声明『完成标准』rubric，由 LLM-as-judge 评估 agent 输出，未达标则驱动 agent 自评迭代直到通过或达到上限。Beta，API 可能变动；需 `deepagents>=0.6.5`。 | DeepAgents 专有 | `from deepagents import RubricMiddleware, create_deep_agent` | `built-in.md:1403` 要求 `deepagents>=0.6.5`；`built-in.md:1412-1508` 全部从 deepagents import；Reference URL：`reference.langchain.com/python/deepagents/middleware/rubric/...` |
| 17 | FilesystemFileSearchMiddleware | 为 agent 提供 `glob_search`（按 glob 模式匹配文件名）和 `grep_search`（基于 ripgrep 的内容正则检索），常用于代码库探索、定位文件或搜索代码内容。 | LangChain 专有 | `from langchain.agents.middleware import FilesystemFileSearchMiddleware` | `built-in.md:1539`、`built-in.md:1583` |
| 18 | ContextEditingMiddleware + ClearToolUsesEdit | 当 token 接近阈值时清理旧的工具调用输出（替换为 `[cleared]` 占位），仅保留最近 K 条工具结果，控制长会话中的上下文膨胀和成本，可选是否同时清掉工具调用参数。 | LangChain 专有 | `from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit` | `built-in.md:1622`、`built-in.md:1688`；harness 中无任何 deepagents 端 import证据 |
| 19 | LLMToolEmulator | 用 LLM 模拟工具返回值，跳过真实工具执行。常用于测试、外部工具未就绪/成本过高或原型设计阶段快速验证 agent 行为。 | LangChain 专有 | `from langchain.agents.middleware import LLMToolEmulator` | `built-in.md:1723`、`built-in.md:1749` |

# 计数汇总

| 分类 | 数量 | 编号 |
|------|------|------|
| LangChain 专有 | 15 | 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 19 |
| DeepAgents 专有 | 3  | 14, 15, 16 |
| 两个框架都有 | 1  | 5 |
| **合计** | **19** | — |

# 表外补充（不在 19 个内置表里，但属于 deepagents）

| Middleware | 用途 | 来源 | import 路径 | 证据 |
|-----------|------|------|------------|------|
| SkillsMiddleware | 从指定目录加载 skill markdown 文件作为按需调用的领域知识（prompt 驱动的技能，类比 Agent Skills / llms.txt 模式），让团队可以独立开发、渐进式披露能力。 | DeepAgents 专有 | `from deepagents.middleware import SkillsMiddleware` | `agents.md:1107-1233`、`deep-agent-from-scratch.md:507-587`；Reference URL 指向 `reference.langchain.com/python/deepagents/middleware/skills/...` |
| MemoryMiddleware | 把 `AGENTS.md` 等长期记忆文件内容注入到 system prompt，使 agent 跨线程持久遵守这些指令、流程与约定。 | DeepAgents 专有 | `from deepagents.middleware import MemoryMiddleware` | `agents.md:1107-1233`；Reference URL：`reference.langchain.com/python/deepagents/middleware/memory/MemoryMiddleware`（`agents.md:1239`） |

# 节点数量统计表（LangChain 1.x 实测，2026-10-13）

> **作用**：每个中间件挂载后对 LangGraph 主图的**实际影响**（新增节点数 / 注入工具数 / 状态 schema 扩展）。
>
> **数据来源**：
> - 环境：`.venv/` 本地 venv，`langchain==1.4.5`、`langgraph==1.2.14`、`langgraph-prebuilt==1.1.0`、`langchain-core==1.6.10`
> - 源码验证：`inspect.getsource(<Middleware>)` 读 `def before_agent / before_model / after_model / after_agent / wrap_model_call / wrap_tool_call` 在 `cls.__dict__` 中的存在性
> - 编译验证：`create_agent(model=fake, tools=[], middleware=[<single>]).get_graph().nodes.keys()` 实际编译图节点列表
> - 框架机制：`langchain.agents.factory.create_agent` 源码 `factory.py:1642-1688` —— 仅当子类重写了 hook 方法才挂图节点，**不**检查方法体是否早返回
>
> **列含义**：
> - **sync hook(s)**：类 `__dict__` 中存在的同步 hook 方法名
> - **async hook(s)**：类 `__dict__` 中存在的异步 hook 方法名（去掉 `a` 前缀）
> - **加节点数**：挂载该中间件**单独**编译后，`graph.nodes.keys()` 中**新增**的非基线节点数（基线 = `__start__` / `model` / `tools` / `__end__`，其中 `tools` 仅在有 tools 时出现）
> - **注入工具数**：该中间件通过 `cls.tools` / `machines.clear_tools` 注册的工具函数数量（含 `BaseTool` 实例与 `tool(...)` 装饰器）
> - **基线总节点**：4（无 tools 时为 3）
> - **donkey v1 状态**：是否在 donkey v1 录用名单（§1.5.4 立项书）

| Middleware | sync hook(s) | async hook(s) | 加节点数 | 节点名 | 注入工具数 | 工具名 | 基线总节点 | donkey v1 |
|---|---|---|---|---|---|---|---|---|
| ToolErrorMiddleware | `wrap_tool_call` | `awrap_tool_call` | **0** | — | 0 | — | 4 | ✅ 录用 |
| ToolRetryMiddleware | `wrap_tool_call` | `awrap_tool_call` | **0** | — | 0 | — | 4 | ✅ 录用 |
| ModelRetryMiddleware | `wrap_model_call` | `awrap_model_call` | **0** | — | 0 | — | 3（无 tools 时） | ✅ 录用 |
| ModelFallbackMiddleware | `wrap_model_call` | `awrap_model_call` | **0** | — | 0 | — | 3（无 tools 时） | ❌ 排除（§1.5.5 上下文长度不一致） |
| ModelCallLimitMiddleware | `before_model` + `after_model` | `abefore_model` + `aafter_model` | **+2** | `ModelCallLimitMiddleware.before_model` + `ModelCallLimitMiddleware.after_model` | 0 | — | 5（带 tools 时） | ✅ 录用 |
| ToolCallLimitMiddleware | `after_model` | `aafter_model` | **+1** | `ToolCallLimitMiddleware.after_model` | 0 | — | 4（无 tools 时 3） | ❌ 排除（§1.5.5 与 ModelCallLimitMiddleware 功能重叠） |
| SummarizationMiddleware | `before_model` | `abefore_model` | **+1** | `SummarizationMiddleware.before_model` | 0 | — | 4 | ✅ 录用 |
| HumanInTheLoopMiddleware | `after_model` + `wrap_tool_call` | `aafter_model` + `awrap_tool_call` | **+1** | `HumanInTheLoopMiddleware.after_model`（HITL 中断机制走 `wrap_tool_call`，不增节点） | 0 | — | 5（带 tools 时） | ❌ 排除（§1.5.5 v2 引入） |
| PIIMiddleware | `before_model` + `after_model` | `abefore_model` + `aafter_model` | **+2**（**始终 2 节点，与 `apply_to_*` 配置无关**） | `PIIMiddleware[<pii_type>].before_model` + `PIIMiddleware[<pii_type>].after_model` | 0 | — | 5（带 tools 时） | ✅ 录用 |
| TodoListMiddleware | `after_model` + `wrap_model_call` | `aafter_model` + `awrap_model_call` | **+1** | `TodoListMiddleware.after_model`（`wrap_model_call` 不增节点） | **+1** | `write_todos` | 5（带 tools 时） | ✅ 录用 |
| LLMToolSelectorMiddleware | `wrap_model_call` | `awrap_model_call` | **0** | — | 0 | — | 3（无 tools 时） | ✅ 录用 |
| ProviderToolSearchMiddleware | `wrap_model_call` | `awrap_model_call` | **0** | — | 0 | — | 3（无 tools 时） | ❌ 排除（§1.5.5 极少供应商支持） |
| ShellToolMiddleware | `before_agent` + `after_agent` | `abefore_agent` + `aafter_agent` | **+2** | `ShellToolMiddleware.before_agent` + `ShellToolMiddleware.after_agent` | **+1** | `shell`（持久 shell session） | 6（带 tools 时） | ❌ 排除（§1.5.5 持久 shell + HITL 冲突 + HostExecutionPolicy 无 timeout） |
| FilesystemFileSearchMiddleware | （无） | （无） | **0** | — | **+2** | `glob_search` + `grep_search` | 4（带 tools 时） | ✅ 录用 |
| ContextEditingMiddleware | `wrap_model_call` | `awrap_model_call` | **0** | — | 0 | — | 3（无 tools 时） | ✅ 录用（与 `ClearToolUsesEdit` 配合使用） |
| LLMToolEmulator | `wrap_tool_call` | `awrap_tool_call` | **0** | — | 0 | — | 4 | ❌ 排除（§1.5.5 测试专用） |

> **关键实证结论**（2026-10-13，`.venv` 内 `langchain==1.4.5` 源码 + 编译图双向验证）：
>
> 1. **LangGraph 工厂挂图节点的判定逻辑**（`langchain/agents/factory.py:1642-1688`）：**仅当子类重写了 hook 方法**（`cls.__dict__` 中存在），才把对应 hook 注册为图节点。**不**检查方法体的早返回分支。
> 2. **PIIMiddleware 始终 +2 节点**（即使 `apply_to_output=False` 让 body 立即 `return None`）——这是 donkey v1 选用 PII 时的关键成本，必须计入节点预算。
> 3. **ModelCallLimitMiddleware 是 node-style 而非 wrap-style**：立项书初稿 §1.5.4 曾误标为 "wrap-style `wrap_model_call`"（实证 `pii.py`/`model_call_limit.py` 源码 + 编译图均显示为 `before_model` + `after_model` 两个节点）。**已修订**（评审 2 轮，2026-10-13）。
> 4. **ContextEditingMiddleware 是 wrap-style 而非 node-style**：立项书初稿曾误标为 "node-style `before_model`"（实证 `context_editing.py` 仅 `wrap_model_call`，无 `before_model`）。**已修订**。
> 5. **TodoListMiddleware 同时挂节点 + 工具**：`after_model` 节点 + `wrap_model_call` 包装 + `write_todos` 工具（+1 节点 + 1 工具）。
> 6. **ShellToolMiddleware 加 +2 节点（不是 1）**：因为它同时重写 `before_agent` + `after_agent`，且会注册 `shell` 工具（持久 shell session，与 HITL 冲突——这是立项书 §1.5.5 排除它的核心理由）。
> 7. **FilesystemFileSearchMiddleware 不加任何节点 / 是 "工具注入型"**：仅通过 `cls.tools = [glob_search, grep_search]` 注册 2 个工具。

## donkey v1 录用 10 项中间件的节点影响汇总

| 中间件 | 加节点数 | 注入工具数 | 备注 |
|---|---|---|---|
| ToolErrorMiddleware | 0 | 0 | wrap_tool_call 嵌入 `tools` 节点内部 |
| ToolRetryMiddleware | 0 | 0 | 同上 |
| ModelRetryMiddleware | 0 | 0 | wrap_model_call 嵌入 `model` 节点内部 |
| SummarizationMiddleware | +1 | 0 | SummarizationMiddleware.before_model |
| ModelCallLimitMiddleware | +2 | 0 | before_model + after_model |
| PIIMiddleware | +2 | 0 | before_model + after_model（始终 2 节点，与配置无关） |
| TodoListMiddleware | +1 | +1 | TodoListMiddleware.after_model + write_todos 工具 |
| LLMToolSelectorMiddleware | 0 | 0 | wrap_model_call 嵌入 `model` 节点内部 |
| FilesystemFileSearchMiddleware | 0 | +2 | glob_search + grep_search（无任何 hook） |
| ContextEditingMiddleware | 0 | 0 | wrap_model_call 嵌入 `model` 节点内部 |
| **合计** | **+6 节点** | **+3 工具** | 基线 4 + 6 = **10 总节点**（与立项书 §4.4.2 实测一致） |

## donkey v1 不录用（已排除）中间件的节点影响

| 中间件 | 加节点数 | 注入工具数 | 排除理由 |
|---|---|---|---|
| ModelFallbackMiddleware | 0 | 0 | 降级模型上下文长度可能与主模型不一致；§1.5.5 |
| ToolCallLimitMiddleware | +1 | 0 | 与 ModelCallLimitMiddleware 功能重叠；§1.5.5 |
| ProviderToolSearchMiddleware | 0 | 0 | 极少供应商支持；§1.5.5 |
| HumanInTheLoopMiddleware | +1 | 0 | v1 最小化智能体不需要；§1.5.5 / v2 引入 |
| LLMToolEmulator | 0 | 0 | 测试专用中间件；§1.5.5 |
| ShellToolMiddleware | +2 | +1 | 持久 shell + HITL 冲突 + HostExecutionPolicy 无 timeout；§1.5.5 |

# donkey agent.py 推荐写法（全部 LangChain 路径，零 deepagents 依赖）

```python
from langchain.agents.middleware import (
    ToolErrorMiddleware,
    ToolRetryMiddleware,
    ModelRetryMiddleware,
    ModelFallbackMiddleware,
    SummarizationMiddleware,            # 两个框架都有，用 LangChain 端
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
    LLMToolSelectorMiddleware,
    ProviderToolSearchMiddleware,
    ShellToolMiddleware,                # 注意：持久 shell + HITL 冲突
    FilesystemFileSearchMiddleware,     # glob_search + grep_search
    ContextEditingMiddleware,
    ClearToolUsesEdit,
    LLMToolEmulator,
)

# 不要 import 的 5 个（全部 deepagents 专有）：
# FilesystemMiddleware
# SubAgentMiddleware
# SkillsMiddleware
# MemoryMiddleware
# RubricMiddleware
