# LangChain 文档目录

本目录是 [LangChain Python 官方文档](https://docs.langchain.com/oss/python/langchain) 的离线 Markdown 镜像，结构与官方完全一致，共 76 个文件。每篇简介都基于文档实际内容提取。

## 顶层文档（32 篇）

### 入门与安装

| 文件 | 简介 |
|---|---|
| [install.md](./install.md) | LangChain 安装说明：`pip install -U langchain` / `uv add langchain`，需 Python 3.10+ |
| [quickstart.md](./quickstart.md) | 快速上手：几分钟内构建第一个 `create_agent`，含 Prompt 指南式步骤 |
| [overview.md](./overview.md) | LangChain 概览：`create_agent` 提供极简可配置 Harness，由模型+工具+中间件组成 |
| [philosophy.md](./philosophy.md) | LangChain 设计哲学：易上手 + 灵活 + 生产就绪 |
| [component-architecture.md](./component-architecture.md) | 组件架构图：模型/工具/Agent/内存/检索模块协作关系 |
| [get-help.md](./get-help.md) | 获取帮助渠道：社区论坛、Slack、Academy、GitHub issue |
| [academy.md](./academy.md) | LangChain Academy 课程主页（指向官网 academy.langchain.com） |

### 核心概念

| 文件 | 简介 |
|---|---|
| [agents.md](./agents.md) | Agent 核心：模型在循环中调用工具直到任务完成，附 `create_agent` 用法 |
| [models.md](./models.md) | 模型抽象层：支持多 provider 切换，涵盖工具调用、结构化输出、多模态、推理 |
| [messages.md](./messages.md) | 消息类型：HumanMessage/AIMessage/ToolMessage/SystemMessage 等基本单位 |
| [tools.md](./tools.md) | 工具：让 Agent 访问实时数据、执行代码、查询数据库 |
| [structured-output.md](./structured-output.md) | 结构化输出：让 Agent 返回 JSON / Pydantic / dataclass 等结构化数据 |
| [streaming.md](./streaming.md) | 流式输出：实时流式返回 Agent 的运行更新 |
| [event-streaming.md](./event-streaming.md) | 事件流：`stream_events` 订阅模型/工具/Agent 生命周期事件 |
| [short-term-memory.md](./short-term-memory.md) | 短期记忆：跨多次交互保留信息，支持 checkpointer 与摘要压缩 |
| [long-term-memory.md](./long-term-memory.md) | 长期记忆：跨会话持久化到 LangGraph Store，含命名空间与向量检索 |
| [runtime.md](./runtime.md) | Runtime：LangGraph 暴露的 context/store/stream writer/execution_info/server_info |
| [retrieval.md](./retrieval.md) | 检索增强生成（RAG）：document loaders/splitters/vector stores 流水线 |
| [mcp.md](./mcp.md) | Model Context Protocol：通过 `MCPAdapter`（基于 FastMCP）接入 MCP 服务器 |
| [context-engineering.md](./context-engineering.md) | 上下文工程：给模型在正确时间提供正确上下文（prompt/messages/tools/model/format） |
| [guardrails.md](./guardrails.md) | 安全护栏：PII 检测、人在回路、模型评估等内置与自定义实现 |
| [human-in-the-loop.md](./human-in-the-loop.md) | 人在回路：用 HITLMiddleware 在敏感工具调用前暂停等待人工审批 |

### 构建指南

| 文件 | 简介 |
|---|---|
| [deep-agent-from-scratch.md](./deep-agent-from-scratch.md) | 从零搭建数据分析 Agent：sandbox + 摘要 + skills + subagent 逐步搭建 |
| [sql-agent.md](./sql-agent.md) | 构建 SQL Agent：表查询/schema/查询自检/HITL 审批全流程教程 |
| [voice-agent.md](./voice-agent.md) | 语音 Agent：STT → Agent → TTS 三段流水线，亚 700ms 延迟 |
| [knowledge-base.md](./knowledge-base.md) | 语义搜索：基于 PDF 嵌入、向量库、检索器构建知识库与迷你 RAG |
| [studio.md](./studio.md) | LangSmith Studio：本地可视化调试 LangChain Agent 的免费界面 |
| [deploy.md](./deploy.md) | 部署：把 Agent 一键部署到 LangSmith Cloud（含 GitHub 集成） |
| [ui.md](./ui.md) | Agent Chat UI：Next.js 应用，连接本地或部署的 LangChain Agent |
| [observability.md](./observability.md) | LangSmith 可观测性：tracing 追踪工具调用、提示生成、决策过程 |

### 杂项

| 文件 | 简介 |
|---|---|
| [changelog-py.md](./changelog-py.md) | Python 包 changelog（langchain、@langchain/openai、anthropic 等） |
| [changelog-js.md](./changelog-js.md) | JavaScript/TypeScript 包 changelog |

## errors/（7 篇错误排查）

| 文件 | 简介 |
|---|---|
| [INVALID_PROMPT_INPUT.md](./errors/INVALID_PROMPT_INPUT.md) | Prompt 模板缺少或非法输入变量，附 f-string 转义说明 |
| [INVALID_TOOL_RESULTS.md](./errors/INVALID_TOOL_RESULTS.md) | AIMessage 的 tool_calls 与 ToolMessage 不匹配（缺/多/孤儿），目前仅 langchainjs |
| [MESSAGE_COERCION_FAILURE.md](./errors/MESSAGE_COERCION_FAILURE.md) | 消息对象不符合 MessageLikeRepresentation 格式 |
| [MODEL_AUTHENTICATION.md](./errors/MODEL_AUTHENTICATION.md) | Provider 鉴权失败，检查 API key、env 变量或代理配置（langchainjs） |
| [MODEL_NOT_FOUND.md](./errors/MODEL_NOT_FOUND.md) | 模型名拼写错误或被代理限制（langchainjs） |
| [MODEL_RATE_LIMIT.md](./errors/MODEL_RATE_LIMIT.md) | 触发 provider 速率限制，附限流/缓存/多 provider 策略（langchainjs） |
| [OUTPUT_PARSING_FAILURE.md](./errors/OUTPUT_PARSING_FAILURE.md) | 输出解析器无法解析模型响应，建议改用结构化输出 |

## frontend/（15 篇前端集成模式）

| 文件 | 简介 |
|---|---|
| [overview.md](./frontend/overview.md) | 前端总览：`useStream` 流式构建生成 UI，类型化消息与工具调用 |
| [controlled-generative-ui.md](./frontend/controlled-generative-ui.md) | 受控生成 UI：自预制组件做工具渲染/状态渲染/推理显示 |
| [declarative-generative-ui.md](./frontend/declarative-generative-ui.md) | 声明式生成 UI：用 json-render/A2UI 在组件目录约束内组合 UI |
| [open-ended-generative-ui.md](./frontend/open-ended-generative-ui.md) | 开放生成 UI：在沙箱中渲染第三方 MCP App，最具表达力但需隔离 |
| [generative-ui-overview.md](./frontend/generative-ui-overview.md) | 生成 UI 三种范式总览：controlled/declarative/open-ended 对比 |
| [tool-calling.md](./frontend/tool-calling.md) | 工具调用卡片：把 Agent 工具调用渲染为带状态的 UI 卡片 |
| [reasoning-tokens.md](./frontend/reasoning-tokens.md) | 推理 token 渲染：折叠块显示模型思考过程与最终答案 |
| [structured-output.md](./frontend/structured-output.md) | 结构化输出渲染：把类型化数据映射为自定义卡片/图表/表格 |
| [markdown-messages.md](./frontend/markdown-messages.md) | Markdown 消息渲染：实时解析流式 Markdown（标题/列表/代码/表格） |
| [headless-tools.md](./frontend/headless-tools.md) | 无头工具：客户端实现工具（如 IndexedDB/地理位置），数据不出设备 |
| [human-in-the-loop.md](./frontend/human-in-the-loop.md) | 前端 HITL：中断触发审批卡片，支持 approve/edit/reject/respond |
| [branching-chat.md](./frontend/branching-chat.md) | 分支对话：编辑消息或重新生成回复时基于 checkpoint 分叉 |
| [join-rejoin.md](./frontend/join-rejoin.md) | 断线重连：客户端断开后重新挂载到正在运行的 Agent 流 |
| [message-queues.md](./frontend/message-queues.md) | 消息队列：允许用户快速连发多条消息顺序处理 |
| [time-travel.md](./frontend/time-travel.md) | 时间旅行：检查点历史查看、回放与从任意点恢复执行 |

## frontend/integrations/（5 篇 UI 库集成）

| 文件 | 简介 |
|---|---|
| [overview.md](./frontend/integrations/overview.md) | 集成总览：CopilotKit/AI Elements/assistant-ui/OpenUI 范式与场景对比 |
| [ai-elements.md](./frontend/integrations/ai-elements.md) | AI Elements：shadcn/ui 风格组件 + useStream 完整集成示例 |
| [assistant-ui.md](./frontend/integrations/assistant-ui.md) | assistant-ui：用 `useExternalStoreRuntime` 把 useStream 接到 AssistantRuntimeProvider |
| [copilotkit.md](./frontend/integrations/copilotkit.md) | CopilotKit：AG-UI 中间件、自定义 endpoint、结构化生成 UI、Slack 频道 |
| [openui.md](./frontend/integrations/openui.md) | OpenUI：用 openui-lang DSL 描述完整仪表盘/报告，渐进式渲染 |

## middleware/（3 篇中间件）

| 文件 | 简介 |
|---|---|
| [overview.md](./middleware/overview.md) | 中间件总览：在 Agent 执行的各阶段插入自定义逻辑 |
| [built-in.md](./middleware/built-in.md) | 内置中间件：预构建常用场景（PII/摘要/HITL/限流/重试等） |
| [custom.md](./middleware/custom.md) | 自定义中间件：在 Agent 生命周期特定点实现 hook |

## multi-agent/（10 篇多 Agent 模式）

| 文件 | 简介 |
|---|---|
| [index.md](./multi-agent/index.md) | 多 Agent 总览：subagents/handoffs/skills/router 四种范式对比与性能分析 |
| [subagents.md](./multi-agent/subagents.md) | Subagents：主 Agent 把子 Agent 当工具调用，sync/async 详解 |
| [handoffs.md](./multi-agent/handoffs.md) | Handoffs：工具调用更新状态变量切换 Agent 配置或路由到其他子图 |
| [skills.md](./multi-agent/skills.md) | Skills：按需加载专用 prompt/知识，单 Agent 渐进式披露能力 |
| [router.md](./multi-agent/router.md) | Router：分类节点把请求分发给多个专业 Agent 并合成结果 |
| [custom-workflow.md](./multi-agent/custom-workflow.md) | Custom workflow：用 LangGraph StateGraph 混合确定性与 Agent 行为 |
| [subagents-personal-assistant.md](./multi-agent/subagents-personal-assistant.md) | 教程：日历+邮件个人助手，subagent 编排 + HITL 审批 |
| [handoffs-customer-support.md](./multi-agent/handoffs-customer-support.md) | 教程：客服 handoffs 状态机（保修验证→问题分类→解决） |
| [router-knowledge-base.md](./multi-agent/router-knowledge-base.md) | 教程：GitHub/Notion/Slack 多源知识库路由器 |
| [skills-sql-assistant.md](./multi-agent/skills-sql-assistant.md) | 教程：SQL 助手用 progressive disclosure 按需加载 skills |

## test/（4 篇测试）

| 文件 | 简介 |
|---|---|
| [index.md](./test/index.md) | 测试总览：单元/集成/Evals 三种策略对比 |
| [unit-testing.md](./test/unit-testing.md) | 单元测试：用 `GenericFakeChatModel` + `InMemorySaver` 测逻辑，无 API 调用 |
| [integration-testing.md](./test/integration-testing.md) | 集成测试：真实 LLM API，pytest 标记分离、API key 管理、VCR 回放 |
| [evals.md](./test/evals.md) | Agent Evals：用 AgentEvals 做 trajectory match 与 LLM-as-judge 评估 |

## 目录结构总览

```
LangChain_doc/
├── (32 个顶层 .md)
├── errors/          (7 篇错误排查)
├── frontend/         (15 篇前端模式)
│   └── integrations/ (5 篇 UI 库集成)
├── middleware/       (3 篇中间件)
├── multi-agent/      (10 篇多 Agent)
└── test/            (4 篇测试)
```

## 使用建议

1. **首次了解 LangChain**：按 `install → quickstart → agents → tools` 顺序阅读
2. **构建生产 Agent**：补全 `context-engineering → middleware → guardrails → human-in-the-loop → observability`
3. **多 Agent 系统**：从 `multi-agent/index.md` 入手，根据场景选 subagents/handoffs/router/skills
4. **前端集成**：先看 `frontend/overview.md`，再按 UI 库选 `frontend/integrations/` 下对应文档
5. **测试上线**：参考 `test/integration-testing.md` + `test/evals.md` 搭建 CI

> 注：所有页面底部均带有 "Edit this page on GitHub" 链接，指向官方 `langchain-ai/docs` 仓库，可直接访问官方源站校对最新内容。
