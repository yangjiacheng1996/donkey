# donkey 项目开发目录（features / phases 总索引）

> 本文件是 `harness/features/` 下所有 `feature*.md` / `feature*_phase*.md` 提示词文件的**总目录**。
>
> - **权威源**：所有 F 编号定义以 `harness/features/立项书.md` 为准；不可妥协原则、Phase 切分规则、段位表以 `.specify/memory/constitution.md` 为准。
> - **维护人**：Maintainer（yangjiacheng）；本文档由 Speckit 起稿、人工复核修订。
> - **本版本**：v0.5 草稿（2026-10-15）—— **采用"报错驱动开发"作为 Phase 划分主哲学**；用奥卡姆剃刀约束退出码分配；F001 改为真幂等（4 场景 + 模板清单 + 用户内容保护）；退出码实际使用连号、预留码放末尾。

---

## §0 阅读顺序与权威引用

| 优先级 | 文档 | 作用 |
|---|---|---|
| ★★★ | `.specify/memory/constitution.md` | 不可妥协原则（N-01~N-12）、Phase 切分规则、段位总表 |
| ★★★ | `harness/features/立项书.md` | F 编号唯一权威、Feature 范围、Phase 总览（§3.2.1、§5.2.1、§5.5） |
| ★★ | `harness/report/LangChain内置中间件速查表.md` | v1 录用 / 禁用中间件清单 |
| ★★ | `harness/report/内置工具应该自己实现还是调用中间件.md` | 三大内置 `@tool` 设计决策依据 |
| ★★ | `harness/report/Saver和Store.md` | 长期记忆选型 + SqliteStore 实施蓝本（v3 路线） |
| ★★ | `harness/report/LangGraph的节点到底是什么东西.md` | 中间件 hook 风格 → 节点数映射 |
| ★ | `harness/LangChain_doc/`、`harness/LangGraph_doc/`、`harness/Managed_deep_agents/` | 官方文档镜像 |
| ★ | `harness/prompt/speckit.md` | Speckit 工作流提示词 |

---

## §1 编号与切分规则速查

### §1.1 F 编号唯一定义（来自立项书 §3.2.1 + 宪法 §4.2）

| 编号 | 一级命令 / 客户端 | 核心库 API |
|---|---|---|
| **F001** | `donkey init` | `init_workspace(path, name, force)` |
| **F002** | `donkey load` | `load_workspace(path) -> LoadResult` |
| **F003** | `donkey session` | `list_sessions / new_session / remove_session / import_session` |
| **F004** | `donkey run` | `run_session(path, session_id)` |
| **F005** | `donkey web` | （前端，复用 F001–F004 库 API） |
| **F006** | `donkey gui` | （前端，复用 F001–F004 库 API） |

### §1.2 Phase 编号格式

```
featurexxx_phasexxx_<phase name>.md
```

- `xxx` 三位数字，左侧补 0；
- `<phase name>` 用英文短横线连字符（kebab-case），见 §3 各 Feature 章节；
- 例：`feature001_phase001_cli_validation.md`、`feature003_phase002_new.md`；
- **Phase 编号串行**：同 Feature 内 Phase 编号严格递增；Phase 编号不跨 Feature 复用。

### §1.3 Phase 切分规则（来自宪法 §4.3 + 立项书 §5.2.1）

| 规则 | 适用 Feature | 切分单位 |
|---|---|---|
| **规则 A：按二级命令切** | 含二级命令的 Feature（如 F003） | 每个二级命令 = 一个 Phase |
| **规则 B：按退出码段位切** | 无二级命令的 Feature（如 F001/F002/F004/F005/F006） | 每 N 个连续退出码 = 一个 Phase |

> **绝对禁止**：旧"Phase A = 骨架 / Phase B = 完整"两段式切分已弃用。

### §1.4 Phase 三要素契约（来自宪法 §4.3）

每设计一个 Phase 必须带齐三要素，对应 `featurexxx_phasexxx_*.md` 提示词文件中的固定章节：

1. **入口条件（Entry Gate）**：前置 Phase 的退出条件全部满足；
2. **异常退出码（Exit Code）**：该 Phase 失败时返回的 exit code（落在该 Feature 段位内）；
3. **退出条件（Exit Gate）**：可执行、可验证的硬指标——由 `verify_phase_<f>_<n>.py` 验证脚本跑出 PASS/FAIL。

---

## §2 切分哲学：报错驱动开发

### §2.1 为什么是"报错驱动开发"

立项书 §1.5.1 明确 Speckit 是 TDD 工具，但**每个 Feature 都涉及大量功能点，无法一次跑完所有 user story**。本项目采用与 TDD 同构的**报错驱动开发**作为 Phase 划分哲学：

| TDD | 报错驱动开发（Phase 划分） |
|---|---|
| 先写失败的测试 | 先列该 Feature 的所有**正常功能**与**异常状态** |
| 写最小实现让测试通过 | 为每个**大概率出现的异常**分配 exit code + Error class |
| 重构 | 持续合并同类异常、剥离罕见异常 |
| 一个测试 → 一个实现 | **一个异常状态 → 正常业务代码 + 一个 Error class** → 一个**退出码** |

**核心论断**（立项书 §1.5.1 第 3 条已暗含）：一个正常功能可以有一个或多个异常状态；用退出码反推正常软件开发流程是好办法——**退出码不是"失败的附属品"，而是"功能契约的硬边界"**。

### §2.2 用奥卡姆剃刀约束退出码分配

**奥卡姆剃刀**（Occam's Razor）原文："如无必要，勿增实体"（Entities should not be multiplied beyond necessity）。本项目将其转译为退出码分配原则：

| 原则 | 含义 |
|---|---|
| **大概率原则** | 用户**实际会遇到**的报错必须分配 exit code（CI 脚本能精确判断失败类型） |
| **稀有合并原则** | 一年遇不到几次的报错**不单独分配**；合并到上一个相邻错误码（如 `IO 失败` 与 `磁盘满` 合并） |
| **预留扩展原则** | 每个 Feature 段位保留 **1~N 个码值**作为预留码，给未来发现的新错误场景（v1.x 试运行期常见） |
| **不冗余原则** | 不要为了"看上去齐全"分配一堆空跑的错误码；空码位 = 浪费段位 |

> **奥卡姆剃刀与"报错驱动开发"的关系**：报错驱动开发是 Phase 划分的**正向流程**（从功能 → 异常 → exit code）；奥卡姆剃刀是**反向校验**（已有的 exit code 分配是否"如无必要"——把罕见错误砍掉 / 合并）。两者配合使用：先按报错驱动列全异常，再用奥卡姆剃刀砍冗余。

### §2.3 Error class 设计约定

每个分配的退出码对应一个**异常类**（class XxxError），位于 `core/exceptions.py`：

```python
class PathNotFoundError(WorkspaceInitError):
    """exit code: 1"""

class PathPermissionError(WorkspaceInitError):
    """exit code: 2"""

class TemplateGenerationError(WorkspaceInitError):
    """exit code: 3"""

class BuiltinToolGenerationError(WorkspaceInitError):
    """exit code: 4"""

# exit code 5-10 已预留
```

**继承关系**：`XxxError` → `WorkspaceInitError`（F001 基类）/ `WorkspaceLoadError`（F002 基类）/ `SessionError`（F003 基类）/ `RunError`（F004 基类）/ `WebError`（F005 基类）/ `GuiError`（F006 基类）→ `DonkeyError`（总基类）。

**Error class 命名约定**：`<Subject><Verb>Error`，Subject = 操作对象（Path / Workspace / Template / Skill / ...），Verb = 错误动作（NotFound / PermissionDenied / Write / ...）。

---

## §3 Phase 一览总表（核心）

> **本表是本 README 的核心交付物**。每一行 = 一个 exit code = 一个 Error class = 一个 Phase 的一个异常状态。
>
> 表中"预留" = 该码值有意保留，不分配 Error class，留给 v1.x 试运行期发现的新报错。

### §3.1 F001 `donkey init`（段位 1-10，3 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F001 | P1 | `PathNotFoundError` | 1 | PATH 父目录不存在 / 路径解析失败（如相对路径、非法字符） | 高 |
| F001 | P1 | `PathPermissionError` | 2 | PATH 权限不足（父目录和 workspace 缺失读 / 写 / 执行权限） | 高 |
| F001 | P2 | `TemplateGenerationError` | 3 | 模板骨架生成失败（合并项：源缺失 / 渲染失败 / 文件写入失败；用户修复动作相同） | 低 |
| F001 | P3 | `BuiltinToolGenerationError` | 4 | 内置 `@tool` + Skills example 生成失败（合并三项：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、端到端集成预演失败） | 低 |
| F001 | — | （预留） | 5-10 | 留给 v1.x 试运行期发现的新错误 | — |

> **设计说明**：
> 1. F001 的职责是"存活检查"——只管"能不能生成文件"，不管"生成的文件格式是否合法"。文件格式的合法性属于 F002 静态检查范畴（exit 11-14）。
> 2. `donkey init` 是**幂等**的（详见 §4.1.1 四场景说明）：已存在 workspace + 无 `--force` 不是错误，**已删除 `WorkspaceExistsError`**。
> 3. `BuiltinToolGenerationError`（exit 4）合并了原 `BuiltinToolWriteError` / `SkillsExampleWriteError` / `EndToEndVerifyError` 三项——三者对用户的修复动作相同（重装 donkey / 检查权限 / 重试 init），按奥卡姆剃刀合并为单一 exit code。
> 4. **退出码实际使用连号**（1-4），预留码（5-10）放末尾；不强求段位按 N-N-N 等分。

### §3.2 F002 `donkey load`（段位 11-20，3 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F002 | P1 | `ProviderTomlSyntaxError` | 11 | `provider.toml` TOML 语法错误（`tomllib.TOMLDecodeError`） | 高 |
| F002 | P1 | `McpJsonSyntaxError` | 12 | `mcp/mcp.json` JSON 语法错误 | 高 |
| F002 | P1 | `SkillFrontmatterError` | 13 | `skills/*/SKILL.md` YAML frontmatter 错误（缺 `name` / `description`） | 高 |
| F002 | P2 | `InstructionMissingError` | 14 | `instruction.md` 缺失 / 目录结构不完整 | 高 |
| F002 | P2 | `ProviderConnectivityError` | 15 | 模型连通性失败（`init_chat_model` + ping 超时 / 鉴权失败） | 中 |
| F002 | P2 | `SqliteSchemaError` | 16 | `memory/checkpoint.sqlite3` 不可读 / schema 不健康 | 低 |
| F002 | P3 | `ToolLoadError` | 17 | `tools/*.py` `@tool` 自动发现失败（import 错误 / 函数签名不合规） | 中 |
| F002 | P3 | `SkillLoadError` | 18 | `skills/*/SKILL.md` 通过自研 loader 加载失败（Level 2 读取异常） | 中 |
| F002 | P3 | `McpServerError` | 19 | `MCPAdapter` 拉起 server 失败（stdio / http 连接失败） | 中 |
| F002 | — | （预留） | 20 | 留给 v1.x 试运行期发现的新错误 | — |

### §3.3 F003 `donkey session`（段位 21-30，4 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F003 | P1 = list | `SessionListSqliteError` | 21 | sqlite 读失败 / sqlite 锁等待超时（list 时） | 低 |
| F003 | P1 = list | （预留） | 22 | 留给未来 list 相关错误 | — |
| F003 | P2 = new | `SessionNewSqliteError` | 23 | sqlite 写失败（new 时） | 低 |
| F003 | P2 = new | `SessionNewLockError` | 24 | sqlite 锁等待超时（new 时） | 低 |
| F003 | P2 = new | （预留） | 25 | 留给未来 new 相关错误 | — |
| F003 | P3 = remove | `SessionRemoveSqliteError` | 26 | sqlite 删除失败（remove 时） | 低 |
| F003 | P3 = remove | `SessionNotFoundError` | 27 | 标题不存在（remove 时） | 中 |
| F003 | P4 = import | `SessionImportFormatError` | 28 | 导入文件格式错误（非 sqlite3 / 损坏文件） | 低 |
| F003 | P4 = import | `SessionImportSqliteError` | 29 | 导入时 sqlite 写失败（主键冲突 / 容量不足） | 低 |
| F003 | — | （预留） | 30 | 留给 v1.x 试运行期发现的新错误 | — |

### §3.4 F004 `donkey run`（段位 31-100，7 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F004 | P1 = tools | `ToolImportError` | 31 | 工具 import 失败（`tools/*.py` 语法 / 循环引用） | 中 |
| F004 | P1 = tools | `ToolExecutionError` | 32 | 工具执行异常（用户自定义 @tool 抛错） | **高** |
| F004 | P1 = tools | `ToolTimeoutError` | 33 | 工具超时（`commandline.py` / `webfetch.py` 超时掐断） | **高** |
| F004 | P1 = tools | `ToolArgumentError` | 34 | 工具参数错误（缺必填 / 类型不匹配） | **高** |
| F004 | P1 = tools | （预留） | 35-40 | 留给未来 tools 相关错误（5 个） | — |
| F004 | P2 = skills | `SkillFrontmatterParseError` | 41 | SKILL.md frontmatter 解析失败（runtime 期间重扫） | 低 |
| F004 | P2 = skills | `SkillToolRegisterError` | 42 | per-skill `load_skill_<name>` 工具注册失败（重名 / 签名错） | 低 |
| F004 | P2 = skills | `SkillLoadBodyError` | 43 | Level 2 body 读取失败（文件 IO 异常） | 低 |
| F004 | P2 = skills | （预留） | 44-50 | 留给未来 skills 相关错误（7 个） | — |
| F004 | P3 = mcp | `McpConfigError` | 51 | `mcp/mcp.json` 解析失败（runtime 重载） | 低 |
| F004 | P3 = mcp | `McpServerConnectError` | 52 | server 连接失败（stdio / http） | 中 |
| F004 | P3 = mcp | `McpToolCallError` | 53 | 工具调用失败（server 通信异常 / timeout） | 中 |
| F004 | P3 = mcp | （预留） | 54-60 | 留给未来 mcp 相关错误（7 个） | — |
| F004 | P4 = saver | `SaverOpenError` | 61 | sqlite 打开失败（runtime 期间） | 低 |
| F004 | P4 = saver | `SaverWriteError` | 62 | checkpoint 写入失败（磁盘满 / 锁等待超时） | 中 |
| F004 | P4 = saver | `SaverReadError` | 63 | checkpoint 读取失败（schema 不兼容） | 低 |
| F004 | P4 = saver | （预留） | 64-70 | 留给未来 saver 相关错误（7 个） | — |
| F004 | P5 = store | （预留） | 71-80 | v1 用 `InMemoryStore` 几乎不出错；10 个全部预留 | — |
| F004 | P6 = middleware | `ToolErrorMiddlewareError` | 81 | ToolError 中间件异常（不可恢复，绕过 wrap-style） | 低 |
| F004 | P6 = middleware | `ToolRetryMiddlewareError` | 82 | ToolRetry 重试超限（exponential backoff 用尽） | 中 |
| F004 | P6 = middleware | `ModelRetryMiddlewareError` | 83 | ModelRetry 重试超限（429/503 用尽） | 中 |
| F004 | P6 = middleware | `SummarizationMiddlewareError` | 84 | 摘要生成失败（token 上限触发的压缩出错） | 低 |
| F004 | P6 = middleware | `ModelCallLimitMiddlewareError` | 85 | 调用次数超限（thread 级 / run 级熔断） | **高** |
| F004 | P6 = middleware | `PIIMiddlewareError` | 86 | PII 检测异常（策略配置错 / redact 函数抛错） | 低 |
| F004 | P6 = middleware | `TodoListMiddlewareError` | 87 | TodoList 系统提示注入失败 | 低 |
| F004 | P6 = middleware | `LLMToolSelectorMiddlewareError` | 88 | 工具预筛选调用失败（小模型 API 异常） | 中 |
| F004 | P6 = middleware | `ContextEditingMiddlewareError` | 89 | 上下文清理异常（ClearToolUsesEdit 抛错） | 低 |
| F004 | P6 = middleware | （预留） | 90 | 留给 FilesystemFileSearch 等无 hook 中间件的异常 | — |
| F004 | P7 = agent loop | `GraphCompileError` | 91 | LangGraph 图编译失败（State schema 异常 / 节点名冲突） | 低 |
| F004 | P7 = agent loop | `StateSchemaError` | 92 | State schema 不匹配（字段缺失 / 类型不符） | 低 |
| F004 | P7 = agent loop | `NodeTypeError` | 93 | 节点类型不匹配（function / dataclass 错配） | 低 |
| F004 | P7 = agent loop | `EdgeConnectError` | 94 | Edge 连接错误（条件边判断异常） | 低 |
| F004 | P7 = agent loop | （预留） | 95-100 | 留给未来 Agent Loop 相关错误（6 个） | — |

### §3.5 F005 `donkey web`（段位 101-170，7 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F005 | P1 = event stream | `WebSocketConnectError` | 101 | WebSocket 连接失败（握手失败 / 协议不匹配） | 中 |
| F005 | P1 = event stream | `SSEError` | 102 | SSE 事件流断流 / 解析失败 | 中 |
| F005 | P1 = event stream | `MessageSerializeError` | 103 | 消息序列化失败（JSON 编码 / 类型转换） | 中 |
| F005 | P1 = event stream | `StreamReconnectError` | 104 | 断流重连失败（重试上限用尽） | 低 |
| F005 | P1 = event stream | （预留） | 105-110 | 留给未来 event stream 相关错误（6 个） | — |
| F005 | P2 = ipc bridge | `IPCInvokeError` | 111 | CLI/Web 进程间调用失败（child process 异常退出） | 中 |
| F005 | P2 = ipc bridge | `IPCSerializeError` | 112 | IPC 序列化失败（pickle / JSON 不兼容） | 中 |
| F005 | P2 = ipc bridge | `IPCTimeoutError` | 113 | IPC 调用超时（长任务未响应） | 中 |
| F005 | P2 = ipc bridge | （预留） | 114-120 | 留给未来 IPC 相关错误（7 个） | — |
| F005 | P3 = render | `ComponentRenderError` | 121 | React/Vue 组件渲染异常（prop 错误 / hook 规则违反） | 中 |
| F005 | P3 = render | `SSRHydrationError` | 122 | SSR-CSR 水合失配（HTML 与客户端树不一致） | 低 |
| F005 | P3 = render | `MarkdownRenderError` | 123 | Markdown 渲染失败（语法解析异常） | 低 |
| F005 | P3 = render | `CodeHighlightError` | 124 | 代码高亮失败（语言不支持 / 词法分析异常） | 低 |
| F005 | P3 = render | （预留） | 125-130 | 留给未来 render 相关错误（6 个） | — |
| F005 | P4 = state | `SessionSyncError` | 131 | session 状态同步失败（前端 ↔ 后端不一致） | 中 |
| F005 | P4 = state | `StoreSyncError` | 132 | store 状态同步失败 | 低 |
| F005 | P4 = state | `StateRollbackError` | 133 | 状态回滚失败（事务不一致） | 低 |
| F005 | P4 = state | （预留） | 134-140 | 留给未来 state 相关错误（7 个） | — |
| F005 | P5 = auth | `CORSError` | 141 | 跨域请求被拒（CORS 头缺失 / origin 不在白名单） | 中 |
| F005 | P5 = auth | `CSPViolationError` | 142 | CSP 策略违规（unsafe-inline / unsafe-eval 触发） | 低 |
| F005 | P5 = auth | `TokenExpiredError` | 143 | 鉴权 token 过期（refresh 失败） | 中 |
| F005 | P5 = auth | （预留） | 144-150 | 留给未来 auth 相关错误（7 个） | — |
| F005 | P6 = resource | `ChunkLoadError` | 151 | chunk 加载失败（动态 import 404） | 中 |
| F005 | P6 = resource | `CDNError` | 152 | CDN 资源加载失败 | 低 |
| F005 | P6 = resource | `WasmLoadError` | 153 | WebAssembly 模块加载失败 | 低 |
| F005 | P6 = resource | （预留） | 154-160 | 留给未来 resource 相关错误（7 个） | — |
| F005 | P7 = misc | `BrowserCompatError` | 161 | 浏览器兼容性错误（特性不支持） | 低 |
| F005 | P7 = misc | `InputValidationError` | 162 | 用户输入校验失败（XSS / 超长字符串） | 中 |
| F005 | P7 = misc | （预留） | 163-170 | 留给未来 misc 相关错误（8 个） | — |

### §3.6 F006 `donkey gui`（段位 171-200，3 Phase）

| Feature | Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F006 | P1 = main process | `AppLifecycleError` | 171 | Electron app 生命周期异常（启动 / 退出失败） | 低 |
| F006 | P1 = main process | `MenuError` | 172 | 菜单注册失败（macOS 应用菜单 / context menu） | 低 |
| F006 | P1 = main process | `TrayError` | 173 | 系统托盘图标创建失败 | 低 |
| F006 | P1 = main process | （预留） | 174-180 | 留给未来 main process 相关错误（7 个） | — |
| F006 | P2 = window | `WindowCreateError` | 181 | 窗口创建失败 | 低 |
| F006 | P2 = window | `WindowRestoreError` | 182 | 窗口恢复失败（崩溃恢复 / 多显示器场景） | 低 |
| F006 | P2 = window | `WindowFocusError` | 183 | 窗口聚焦失败 | 低 |
| F006 | P2 = window | `MultiWindowError` | 184 | 多窗口管理失败 | 低 |
| F006 | P2 = window | （预留） | 185-190 | 留给未来 window 相关错误（6 个） | — |
| F006 | P3 = native glue | `FileDialogError` | 191 | 系统文件对话框调用失败 | 低 |
| F006 | P3 = native glue | `NotificationError` | 192 | 系统通知发送失败（macOS / Linux 各异） | 低 |
| F006 | P3 = native glue | `ClipboardError` | 193 | 剪贴板读写失败 | 低 |
| F006 | P3 = native glue | `SystemAPIError` | 194 | 系统 API 调用失败（dock / taskbar / 电源管理） | 低 |
| F006 | P3 = native glue | （预留） | 195-200 | 留给未来 native glue 相关错误（6 个） | — |

---

## §4 F001 `donkey init` —— 详细设计（当前开发起点）

### §4.1 F001 整体范围

- **核心库 API**：`core.api.init_workspace(path, name, force) -> InitResult`
- **段位**：exit `1-10`（3 Phase，4 错误码，6 预留；实际使用 1-4 连号，预留 5-10）
- **切分规则**：规则 B（按退出码段位切）
- **权威引用**：
  - 立项书 §4.5（库 API 契约）+ §4.6.1（workspace 目录结构）+ §5.5.1（F001 整体范围）
  - 宪法 §2.4（Skills 三层模型）+ §2.5（内置 `@tool` 与中间件职责正交）+ §2.6（workspace 必填项）
  - 调研 `内置工具应该自己实现还是调用中间件.md`（三大内置 `@tool` 决策依据）

#### §4.1.1 `donkey init` 四场景与幂等性设计（核心）

`donkey init` **必须幂等**（"无则增，有则跳过"）。下面是 4 种典型场景与对应行为：

| 场景 | 命令 | workspace 状态 | 行为 | exit |
|---|---|---|---|---|
| **1. 全新创建** | `donkey init /tmp/ws` | 目录不存在 | 新建全部目录 + 全部模板文件 | 0 |
| **2. 幂等补齐**（最常用） | `donkey init /tmp/ws` | 目录存在 | **遍历模板清单**：缺失的补齐；已存在的**完全不动**；用户内容（非模板）**完全不动** | 0 |
| **3. 模板重置** | `donkey init /tmp/ws --force` | 目录存在 | **遍历模板清单**：先 `delete` 每个模板文件（含子目录如 `skills/example/`），再 `create` 默认内容；用户内容**完全不动** | 0 |
| **4. 放弃重做** | （用户手动）`rm -rf /tmp/ws` + `donkey init /tmp/ws` | 目录被用户删除 | 同场景 1 | 0 |

**关键边界**——donkey 必须维护一份**模板文件清单**（位于 `core/workspace/templates/manifest.json` 或代码内常量），列出 donkey 自动生成的所有文件路径：

```
templates/
├── instruction.md          ← 模板
├── provider.toml           ← 模板
├── mcp/mcp.json            ← 模板
├── skills/example/         ← 模板（含子文件 SKILL.md + reference/ + scripts/ + templates/）
├── tools/filesystem.py     ← 模板
├── tools/commandline.py    ← 模板
├── tools/webfetch.py       ← 模板
├── tools/__init__.py       ← 模板
├── tools/README.md         ← 模板
├── mcp/README.md           ← 模板
├── skills/README.md        ← 模板
├── memory/README.md        ← 模板
├── README.md               ← 模板
└── .gitignore              ← 模板
```

**用户内容**（donkey 不动）：
- 用户自定义的 `tools/*.py`（不在清单内）
- 用户自定义的 `skills/*/`（不在清单内）
- 用户任意创建的目录 / 文件（如 `media/` / `videos/` / `notes/`）

**`--force` 行为细节**：
- 遍历模板清单，对每个模板路径执行 `delete`（文件或目录递归删除）+ `create`（默认内容）；
- 不在清单内的任何文件 / 目录**完全不动**；
- 模板清单本身（如 `templates/manifest.json`）也属于模板，`--force` 会刷新它（用于 donkey 升级引入新模板）；
- 用户的 `instruction.md` / `provider.toml`（用户已编辑过）**不会被覆盖**——因为这些是"可能被用户编辑的模板"，仅在模板损坏时由用户手动删除后再 init 补齐（场景 2 的子操作）。

**幂等性 + 损坏恢复的工作流**（用户视角）：
1. 用户发现某模板文件损坏 → 用户 `rm` 该文件 → 用户跑 `donkey init` → 幂等补齐该文件
2. 用户希望全部模板重置 → 用户跑 `donkey init --force` → 清空 + 重生成全部模板
3. 用户希望整个 workspace 推倒重来 → 用户 `rm -rf workspace` → 跑 `donkey init`（不用 `--force`）

### §4.2 F001 Phase 划分

| Phase | 文件名提示词 | 段位 | 主要工作 | Error 类 |
|---|---|---|---|---|
| **F001-P1** | `feature001_phase001_cli_validation.md` | exit `1-2` | CLI 入口 + 路径 / 权限校验 + 模板清单加载 | `PathNotFoundError` / `PathPermissionError` |
| **F001-P2** | `feature001_phase002_template_skeleton.md` | exit `3` | 幂等生成模板骨架（补齐缺失 / `--force` 重置）+ 模板清单驱动 | `TemplateGenerationError` |
| **F001-P3** | `feature001_phase003_builtin_tools.md` | exit `4` | 幂等生成 3 个内置 `@tool` + Skills example 三层 | `BuiltinToolGenerationError` |

### §4.3 F001-P1 = `cli_validation`（exit 1-2）

**入口条件（Entry Gate）**：
- `donkey/core/` / `donkey/cli/` / `donkey/web/` / `donkey/gui/` 目录已创建；
- `donkey/core/exit_codes.py` 已实现 exit code 段位常量；
- `donkey/core/exceptions.py` 已定义基类 `DonkeyError` 与 F001 基类 `WorkspaceInitError`，并定义 2 个具体异常类（`PathNotFoundError` / `PathPermissionError`，对应 exit 1 / 2）；
- `core/workspace/templates/manifest.json`（模板清单）已定义；
- `core/workspace/templates/*.txt`（模板源文件，至少含 `instruction.md.txt` / `provider.toml.txt` / `mcp.json.txt`）已就位。

**实现要点**：
- `core/api.py`：`init_workspace(path, name=None, force=False) -> InitResult` 函数签名稳定（允许 `raise NotImplementedError` stub）。
- `core/workspace/init.py`：核心逻辑骨架：
  - `check_path(path) -> Path` — 解析为绝对路径，验证父目录存在；失败抛 `PathNotFoundError`；
  - `check_permission(path) -> None` — 验证当前用户对 path 有写权限；失败抛 `PathPermissionError`；
  - `load_template_manifest() -> list[Path]` — 加载 `core/workspace/templates/manifest.json`，返回模板文件路径列表；
  - `validate_init_request(path, name, force)` — 综合校验。
  - **不**再检查 "workspace 已存在"——幂等设计下已存在不是错误（详见 §4.1.1）。
- `cli/cli_client.py`：argparse 入口，仅 `init` 子命令：
  - 位置参数 `<PATH>` 必填；
  - `--name` 可选，默认取 `path.basename()`；
  - `--force` flag。
- `cli` **不**直接 import `pathlib` 之外的 IO 库；所有 IO 通过 `core.api` 调用（**宪法 N-04 / N-05**）。

**异常退出码**（详见 §3.1 表）：
- exit 1 = `PathNotFoundError` —— PATH 父目录不存在 / 路径解析失败；
- exit 2 = `PathPermissionError` —— PATH 权限不足。

**退出条件（Exit Gate）**：
- `verify_phase_f001_p1.py` 通过以下断言：
  1. `donkey init /tmp/empty-ws` → exit 0（场景 1：全新创建）；
  2. `donkey init /nonexistent/parent/ws` → exit 1；
  3. `donkey init /root/forbidden`（无权限场景，假设 root-only 目录）→ exit 2；
  4. `donkey init /tmp/ws`（已存在 workspace，无 `--force`）→ exit 0（场景 2：幂等补齐，不报错）；
  5. `donkey init /tmp/ws --force`（已存在 workspace，传 `--force`）→ exit 0（场景 3：模板重置）；
  6. 加载模板清单失败（如 `manifest.json` 损坏）→ exit 1（path / 权限异常的合并报错）；
  7. **不**检查模板渲染 / 目录内容（属于 P2）；允许 init 出来的目录"仅含占位空文件"或"创建空目录"。

**绝对不做**：
- 不生成 `tools/` / `skills/` 等子目录内容（推迟到 P2 / P3）；
- **不**做"workspace 已存在则报错"的判断（幂等设计，已存在不是错误）；
- 不挂载任何中间件（属于 F004 run 域）；
- 不解析 `provider.toml`（属于 F002 load 域）。

---

### §4.4 F001-P2 = `template_skeleton`（exit 3）

**入口条件**：F001-P1 退出条件全部满足 + P1 抛出的 2 个异常类已通过单元测试。

**实现要点**：
- **6 大必填目录**（**宪法 §2.6**）：`tools/`、`mcp/`、`skills/`、`memory/`。
- **必填文件**（**立项书 §4.6.1**）：
  - `instruction.md`（系统提示词模板，含占位符说明）；
  - `provider.toml`（含 `[provider]` section：`protocol` / `model_name` / `secret_key` / `base_url` 等字段占位）；
  - `mcp/mcp.json`（`{"mcpServers": {}}` 空对象模板）；
  - `skills/example/SKILL.md`（仅含 Level 1 frontmatter 占位 `name` + `description`）。
- **支撑文件**：
  - 根 `README.md`（workspace 总览模板）；
  - `tools/README.md`（工具开发规范说明）；
  - `mcp/README.md`、`skills/README.md`、`memory/README.md`；
  - `.gitignore`（忽略 `memory/*.sqlite3`、`__pycache__/`）。
- `core/workspace/templates/`：模板源文件（`.md.txt` / `.toml.txt` / `.json.txt`）；
- `core/workspace/templates/manifest.json`：模板清单（列出 donkey 自动生成的所有文件路径；详见 §4.1.1）；
- `core/workspace/init.py`：新增 `render_templates(path, name, force)` 函数：
  - 遍历 `manifest.json` 中的每个模板路径；
  - **不传 `force`**：仅当文件不存在时创建；已存在跳过；
  - **传 `force`**：先 `delete` 再 `create`；
  - 用户内容（非模板）不动；
  - 任一步骤失败 → 抛 `TemplateGenerationError`。
- `core/workspace/manifest.py`：workspace manifest 写入与解析（**D-01**：manifest 字段最少化，可仅含 `version` + `created_at` + `donkey_version`）：
  - **不传 `force`**：若 manifest 已存在则跳过（保留原 `created_at`）；
  - **传 `force`**：刷新 `created_at` 为当前时间；
  - 字段 `donkey_version` 记录生成本次 manifest 的 donkey 版本号（用于未来迁移提示）。
- `--name` 参数注入：`name` 注入到 `provider.toml` 注释、`README.md` 标题、manifest。

**异常退出码**（详见 §3.1 表）：
- exit 3 = `TemplateGenerationError` —— 模板骨架生成失败（合并三项：源缺失 + 渲染失败 + 文件写入失败；用户修复动作相同：重装 donkey / 检查权限 / 重试 init）。

**退出条件**：
- `verify_phase_f001_p2.py` 通过以下断言：
  1. **场景 1**：`donkey init /tmp/empty-ws` → exit 0，目录树与立项书 §4.6.1 **逐项一致**；
  2. 生成的 `provider.toml` 用 `tomllib` 解析无异常；
  3. 生成的 `mcp/mcp.json` 用 `json.loads` 解析无异常；
  4. 生成的 `skills/example/SKILL.md` frontmatter 用 `python-frontmatter` 解析，含 `name` + `description`；
  5. `--name=foo` 注入后，README 标题与 provider.toml 注释含 "foo"；
  6. **场景 2 幂等**：`donkey init /tmp/ws`（已存在）→ exit 0；用户手动编辑过的 `instruction.md` 内容**不变**（mtime 不变）；
  7. **场景 2 子操作**（用户损坏恢复）：`rm /tmp/ws/instruction.md` 后 `donkey init /tmp/ws` → exit 0；该文件被补齐；
  8. **场景 3 模板重置**：`donkey init /tmp/ws --force` → exit 0；用户编辑过的 `instruction.md` 也被覆盖（恢复出厂内容）；用户自建的 `media/` 目录**不动**；
  9. **场景 3 完整验证**：第 8 步后用户 `media/` 仍在 + `donkey.log` 仍在（如果有）；
  10. **场景 4**：手动 `rm -rf /tmp/ws` 后 `donkey init /tmp/ws` → exit 0；同场景 1；
  11. 缺失 `templates/instruction.md.txt` 时手动删除 → `donkey init /tmp/ws --force` → exit 3；
  12. **不**要求 `tools/filesystem.py` 等内置 `@tool` 文件存在（属于 P3）；
  13. **不**要求生成的 workspace 能通过 F002 静态检查（属于 F002 域）。

**绝对不做**：
- 不生成 3 个内置 `@tool` 文件（推迟到 P3）；
- 不生成 Skills example 的 Level 2/3 内容（推迟到 P3）；
- **不**做"init 后跑 F002 静态检查"——文件格式合法性属于 F002 静态检查范畴（exit 11-14），F001 不重复。

---

### §4.5 F001-P3 = `builtin_tools`（exit 4）

**入口条件**：F001-P2 退出条件全部满足 + P2 抛出的 `TemplateGenerationError` 已通过单元测试。

**实现要点**：
- **`tools/__init__.py`**：空文件或最小初始化（保证 `from tools import filesystem` 可用）。
- **`tools/filesystem.py`**：7 个 `@tool`（**立项书 §4.6.1 + 调研 §三**）：
  - `read_file(path) -> str` / `write_file(path, content)` / `copy_file(src, dst)` / `move_file(src, dst)` / `delete_file(path)` / `list_dir(path) -> list[str]` / `stat(path) -> dict`；
  - 实现：`pathlib` / `shutil`；路径白名单由用户自管（donkey 不强制）；
  - **不**含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管，**宪法 §2.5**）。
- **`tools/commandline.py`**：1 个 `@tool`：
  - `run_shell(command, timeout=60) -> str`；
  - 实现：`subprocess.run([...], shell=False, timeout=...)`，每次新进程，**不**走持久 shell（避免 HITL 冲突）。
- **`tools/webfetch.py`**：1 个 `@tool`：
  - `fetch_url(url, method="GET", headers=None, timeout=30) -> str`；
  - 实现：`httpx` / `requests` 同步 + 显式 timeout；不持久化 cookies。
- **`tools/README.md`**：工具开发规范（命名、参数、错误处理、timeout）。
- **`skills/example/SKILL.md`**：完整三层示例（**宪法 §2.4**）：
  - Level 1：frontmatter `name` + `description`；
  - Level 2：Markdown 主体；
  - Level 3 目录占位：`skills/example/reference/` / `scripts/` / `templates/` 各含 1 个示例文件。
- `core/workspace/templates/manifest.json` **追加**：把上述 5 个 builtin tool 文件 + Skills example 路径加入模板清单（P2 已有 instruction.md / provider.toml 等基础模板；P3 追加 builtin 模板条目）。
- `core/workspace/init.py`：复用 P2 的 `render_templates(path, name, force)` 幂等逻辑（**不重复实现**）：
  - 遍历 manifest.json 新追加的 builtin 模板条目；
  - 不传 `force`：仅当文件不存在时创建；已存在跳过（用户自定义 `tools/*.py` 不在清单内，不动）；
  - 传 `force`：先 `delete` 再 `create`；用户自定义 `tools/my_tool.py` 不动。
- **端到端集成预演**（**注意：仅做"import 路径 + 函数签名"测试，不做 F002 静态格式检查**）：`tests/e2e/test_init_to_load.py` 验证 init 完的 workspace 能被 Python import 路径正确发现 `@tool` 函数。

**异常退出码**（详见 §3.1 表）：
- exit 4 = `BuiltinToolGenerationError` —— 内置 `@tool` + Skills example 生成失败（合并三项：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、集成预演 import 失败）。

**退出条件**：
- `verify_phase_f001_p3.py` 通过以下断言：
  1. 生成的 workspace 包含 `tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py` / `tools/__init__.py` / `tools/README.md`；
  2. 三个 builtin tool 文件均可 import，每个 `@tool` 函数有完整 docstring；
  3. `commandline.py` 执行 `run_shell("echo hello")` 返回 `"hello\n"`（集成测试）；
  4. `filesystem.py` 7 个 `@tool` 单元测试全绿；
  5. `webfetch.py` HTTP mock（`httpx.MockTransport`）GET/POST 测试通过；
  6. `skills/example/SKILL.md` frontmatter 合法 + Level 2 非空 + Level 3 含至少 1 个文件；
  7. `tools/` 子目录内的 3 个内置工具**不**含 `glob_search` / `grep_search`；
  8. **幂等场景 2**：用户 `rm /tmp/ws/tools/filesystem.py` 后 `donkey init /tmp/ws` → exit 0；该文件被补齐；
  9. **`--force` 场景 3**：用户自建 `tools/my_custom_tool.py`（不在清单内）后 `donkey init /tmp/ws --force` → exit 0；`filesystem.py` 被覆盖（恢复出厂内容），但 `my_custom_tool.py` **仍在**；
  10. 集成预演：`from tools.filesystem import read_file` 等 import 语句无异常；
  11. **不**做"init 后跑 F002 静态检查"——F002-P1 才会做（exit 11-14）。

**绝对不做**：
- 不挂载任何 LangChain 中间件（属于 F004 run 域）；
- 不调用 `init_chat_model` 做连通性测试（属于 F002 load 域）；
- 不创建 sqlite3 数据库文件（属于 F002 load 域）；
- **不**做"init 后跑 F002 静态检查"——F002 静态格式检查属 F002 域；
- 不引入 `ShellToolMiddleware` / `FilesystemMiddleware` / `FilesystemFileSearchMiddleware` 等任何 LangChain 中间件（属于 F004 run 域；**宪法 §3.2**）。

---

## §5 F002 `donkey load` —— 详细设计

### §5.1 F002 整体范围

- **核心库 API**：`core.api.load_workspace(path) -> LoadResult`
- **段位**：exit `11-20`（3 Phase，9 错误码，1 预留）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**（**宪法 N-06 / N-07**）：
  - 失败时 exit code 非 0，但**不修改** workspace 任何文件；
  - 不依赖 `init`：用户可跳过 init 直接跑 load，必须检测并清晰报告"未 init"；
  - 多错误优先级：遇到第一个 hard error 立即返回，不累积；
  - warning 不计入失败（`--strict-warnings` 列入 v2 候选）。

### §5.2 F002 Phase 划分

| Phase | 文件名提示词 | 段位 | 主要工作 | Error 类 |
|---|---|---|---|---|
| **F002-P1** | `feature002_phase001_static_format.md` | exit `11-13` | 静态 1-3：`provider.toml` / `mcp.json` / `SKILL.md` 语法解析 | `ProviderTomlSyntaxError` / `McpJsonSyntaxError` / `SkillFrontmatterError` |
| **F002-P2** | `feature002_phase002_static_dynamic_basic.md` | exit `14-16` | 静态 4（目录完整性）+ 动态 1-2（连通性 + sqlite） | `InstructionMissingError` / `ProviderConnectivityError` / `SqliteSchemaError` |
| **F002-P3** | `feature002_phase003_dynamic_runtime.md` | exit `17-19` | 动态 3-5（tools / skills / mcp loader） | `ToolLoadError` / `SkillLoadError` / `McpServerError` |

### §5.3 F002-P1 = `static_format`

- **核心逻辑**：用 `tomllib` / `json` / `python-frontmatter` 解析 workspace 内的静态文件，第一个语法错误立即抛出对应 Error。
- **退出条件**：人造损坏 workspace（手动改坏 TOML/JSON/YAML）→ 对应 exit code 触发；正常 init 完的 workspace → exit 0。

### §5.4 F002-P2 = `static_dynamic_basic`

- **核心逻辑**：检查 `instruction.md` 存在性与目录结构完整性；用 `init_chat_model` + ping 验证模型连通性；用 `sqlite3` + `PRAGMA integrity_check` 验证 sqlite schema。
- **退出条件**：删除 `instruction.md` → exit 14；`provider.toml` 填错 base_url → exit 15；损坏 `checkpoint.sqlite3` → exit 16。

### §5.5 F002-P3 = `dynamic_runtime`

- **核心逻辑**：扫描 `tools/*.py` 跑 `importlib` 验证 `@tool` 可加载；跑自研 Skills loader 验证 SKILL.md 可加载；用 `MCPAdapter` 拉起 server 验证可达。
- **退出条件**：故意写错的 `tools/*.py`（语法错）→ exit 17；损坏的 SKILL.md → exit 18；填错的 mcp server URL → exit 19。

---

## §6 F003 `donkey session` —— 详细设计

### §6.1 F003 整体范围

- **核心库 API**：`list_sessions / new_session / remove_session / import_session`
- **段位**：exit `21-30`（4 Phase，6 错误码，4 预留）
- **切分规则**：规则 A（按二级命令切）—— 每个二级命令 = 一个 Phase
- **关键约束**（**宪法 N-09 / N-10**）：
  - 对外标识是**标题**，thread_id 仅作内部引用；
  - `session new` 默认标题"无标题会话"；给了首轮 prompt 时**必须**在 `core.api.new_session` 内部由 LLM 总结 ≤ 20 字标题并写回 sqlite3；**严禁**实现为 `before_agent` 中间件（不新增 LangGraph 节点、不触发 `x+1`）。

### §6.2 F003 Phase 划分

| Phase | 二级命令 | 文件名提示词 | 段位 | 主要工作 | Error 类 |
|---|---|---|---|---|---|
| **F003-P1** | `list` | `feature003_phase001_list.md` | exit `21-22` | 扫描 `memory/checkpoint.sqlite3` 列出所有会话（按标题） | `SessionListSqliteError` |
| **F003-P2** | `new` | `feature003_phase002_new.md` | exit `23-25` | 新建会话；可选 `--first-prompt` 触发 LLM 总结标题（**不**进 Agent Loop 图） | `SessionNewSqliteError` / `SessionNewLockError` |
| **F003-P3** | `remove` | `feature003_phase003_remove.md` | exit `26-27` | 按标题定位，物理删除 sqlite 中对应 thread 的全部 checkpoint | `SessionRemoveSqliteError` / `SessionNotFoundError` |
| **F003-P4** | `import` | `feature003_phase004_import.md` | exit `28-30` | 从外部 sqlite 文件导入历史会话 | `SessionImportFormatError` / `SessionImportSqliteError` |

### §6.3 关键 Phase 说明

**F003-P2 = `new`（最复杂）**：
- `core.api.new_session(path, first_prompt=None, title=None) -> SessionMeta` 内部流程：
  1. 分配 thread_id，INSERT SqliteSaver 元数据；
  2. 决定标题（**N-10**）：用户显式传 `title` → 用 title（≤ 20 字截断）；用户传 `first_prompt` → 调 `init_chat_model` 总结 ≤ 20 字；失败/超时/空返回 → 回写"无标题会话"；都不传 → 默认"无标题会话"；
  3. UPDATE `thread_title` 回 sqlite3。
- 标题总结失败**不**抛异常 → session 创建本身始终成功（exit 0）。

---

## §7 F004 `donkey run` —— 详细设计（v1 主战场）

### §7.1 F004 整体范围

- **核心库 API**：`core.api.run_session(path, session_id)`
- **段位**：exit `31-100`（7 Phase，19 错误码，51 预留——大段预留给中间件扩展与 v2/v3 接入）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：
  - **v1 主图节点数 = 10**（立项书 §4.4.2）：4 基线 + 6 中间件节点；
  - **v1 中间件录用 10 项**（立项书 §1.5.4 + 宪法 §2.7.1）；
  - **v1 不挂 Store**（SqliteStore 留给 v3），v1/v2 用 `InMemoryStore` 临时顶替；
  - **版本号 `x+1` 触发条件**见立项书 §1.5.2 边界细则表。

### §7.2 F004 7 子段位 Phase 划分

| Phase | 文件名提示词 | 段位 | 失败域 | 主要工作 |
|---|---|---|---|---|
| **F004-P1** | `feature004_phase001_tools.md` | exit `31-35`（4 码 + 1 预留） | tools 调用 | 加载 `tools/*.py` → `@tool` 自动发现；执行失败处理 |
| **F004-P2** | `feature004_phase002_skills.md` | exit `41-43`（3 码 + 7 预留） | Skills 加载 | 扫描 `skills/*/SKILL.md` → 自研渐进披露 loader |
| **F004-P3** | `feature004_phase003_mcp.md` | exit `51-53`（3 码 + 7 预留） | MCP server | 加载 `mcp/mcp.json` → `MCPAdapter` |
| **F004-P4** | `feature004_phase004_saver.md` | exit `61-63`（3 码 + 7 预留） | 短期记忆（Saver） | 挂 `SqliteSaver(memory/checkpoint.sqlite3)` |
| **F004-P5** | `feature004_phase005_store.md` | exit `71-80`（10 码全预留） | 长期记忆（Store） | v1 用 `InMemoryStore`；段位全预留 |
| **F004-P6** | `feature004_phase006_middleware.md` | exit `81-89`（9 码 + 1 预留） | 中间件 | 10 项 v1 中间件挂载 + 错误处理 |
| **F004-P7** | `feature004_phase007_agent_loop.md` | exit `91-94`（4 码 + 6 预留） | Agent Loop | LangGraph 主图编译 + 状态机 |

---

## §8 F005 `donkey web` —— 详细设计

### §8.1 F005 整体范围

- **核心库 API**：前端复用 F001-F004 库 API，无独立后端 API
- **段位**：exit `101-170`（7 Phase，17 错误码，53 预留）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：Web **不**直接 import `langchain` / `langgraph` / `sqlite3`（**宪法 N-04**）；全部走 `donkey.core.api`。

### §8.2 F005 7 子段位 Phase 划分

| Phase | 文件名提示词 | 段位 | 失败域 | 主要工作 |
|---|---|---|---|---|
| **F005-P1** | `feature005_phase001_event_stream.md` | exit `101-104` | 事件流 | WebSocket / SSE / 序列化 / 断流重连 |
| **F005-P2** | `feature005_phase002_ipc_bridge.md` | exit `111-113` | IPC 桥接 | CLI ↔ Web 进程间调用 / 超时 / 序列化 |
| **F005-P3** | `feature005_phase003_render.md` | exit `121-124` | 渲染 | 组件异常 / SSR-CSR 失配 / Markdown + 代码高亮 |
| **F005-P4** | `feature005_phase004_state.md` | exit `131-133` | 状态管理 | session / store 同步 / 回滚 |
| **F005-P5** | `feature005_phase005_auth.md` | exit `141-143` | 鉴权 / CORS / CSP | 跨域 / cookie / token |
| **F005-P6** | `feature005_phase006_resource.md` | exit `151-153` | 资源加载 | chunk 404 / CDN / WebAssembly |
| **F005-P7** | `feature005_phase007_misc.md` | exit `161-162` | 其它 | 浏览器兼容性 / 用户输入校验 |

---

## §9 F006 `donkey gui` —— 详细设计

### §9.1 F006 整体范围

- **核心库 API**：前端复用 F001-F004 库 API，无独立后端 API
- **段位**：exit `171-200`（3 Phase，12 错误码，18 预留）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：
  - **GUI = Electron 包壳**：100% 复用 Web 渲染层（**立项书 §5.5.6**）；
  - **最薄壳**：工作量约 40 人时；
  - 三端打包脚本（macOS dmg / Windows nsis / Linux AppImage）属 F006-P3 范围。

### §9.2 F006 3 子段位 Phase 划分

| Phase | 文件名提示词 | 段位 | 失败域 | 主要工作 |
|---|---|---|---|---|
| **F006-P1** | `feature006_phase001_main_process.md` | exit `171-173` | Electron 主进程 | app 生命周期 / 菜单 / 托盘 |
| **F006-P2** | `feature006_phase002_window.md` | exit `181-184` | 窗口 | 创建 / 恢复 / 聚焦 / 多窗口 |
| **F006-P3** | `feature006_phase003_native_glue.md` | exit `191-194` | 原生胶水 | 文件对话框 / 通知 / 剪贴板 / 系统 API |

---

## §10 开发顺序与依赖关系

### §10.1 关键路径（串行）

```
F001 → F002 → F003 → F004 → F005 → F006 → 三套官方模板 → Release v1.0.0
```

每个 Feature 内部 Phase 严格串行；跨 Feature 可滚动并行（详见 §10.2）。

### §10.2 跨 Feature 滚动策略（来自立项书 §5.2.1 + 宪法 §4.3）

| 时段 | 可并行任务 |
|---|---|
| **时段 A（F001 / F002 启动期）** | F001-P1 + F002-P1 可并行（共享 `core/exit_codes.py` + `core/exceptions.py`） |
| **时段 B（F003 启动期）** | F001-P2/P3 + F002-P2 + F003-P1 可并行 |
| **时段 C（F004 启动期）** | F002-P3 + F003-P2/P3/P4 + F004-P1~P7 可并行 |
| **时段 D（F005 / F006 启动期）** | F005 7 子段 + F006 3 子段 + 三套官方模板可并行；CLI 渐进补齐穿插 |

### §10.3 客户端开发顺序（洋葱架构）

| 客户端 | 时间窗 | 工作量 | 与后端关系 |
|---|---|---|---|
| **CLI** | F001 → F004 期间渐进补齐 | ~80 人时 | 后端 API 的"探针"，强迫 `core.api` 稳定 |
| **Web**（主战场） | F005 时段 | ~200 人时 | 1:1 调 `donkey.core.api`；所有交互、事件流、Markdown/代码高亮、会话管理在 Web 完成 |
| **GUI = Electron 包壳** | F006 时段 | ~40 人时 | **复用 Web 100% 渲染层**；仅追加 Electron 主进程 + 原生 API 胶水 |

**禁止**：Web 未完成就启动 GUI；跳过 CLI 直接做 Web。

### §10.4 三套官方模板（v1.0.0 收尾）

- 通用型 workspace（带 Skills / Tools / provider 通用品）
- 编程型 workspace（编程人格 + 编程 Skills + 编程 Tools + 模型选型）
- 技能型 workspace（SOP 沉淀型 Skills 集）

> 三套模板**不承诺**提供 diff 审阅（**宪法 N-11 / 立项书 AC-5**）；如需 diff，走 fork 路线。

---

## §11 exit code 段位速查表（来自宪法 §4.4）

| 段位 | 归属 | 已用码 | 预留码 | Phase 数 |
|---|---|---|---|---|
| `0` | 全子命令 | 1（OK） | 0 | — |
| `1-10` | F001 init | 4（1-4 连号） | 6（5-10） | 3 |
| `11-20` | F002 load | 9 | 1 | 3 |
| `21-30` | F003 session | 6 | 4 | 4 |
| `31-100` | F004 run | 19 | 51 | 7 |
| `101-170` | F005 web | 17 | 53 | 7 |
| `171-200` | F006 gui | 12 | 18 | 3 |
| `201+` | v2/v3/v4 扩展 | 0 | 全部 | — |

**总分配**：49 个具体错误码 + 133 个预留码 + 1 个 OK = **183 个码值**（立项书 §5.5.3 段位表完整覆盖）。

**预留比例**：
- F001 60% 预留（init 是简单存活检查，4 个错误码已覆盖所有场景——实际使用 1-4 连号，预留 5-10 留给 v1.x 试运行期发现的新错误）；
- F002 10% 预留（静态 + 动态 9 项检查全覆盖，几乎没有冗余）；
- F003 40% 预留（4 个二级命令，每个 Phase 2 码值已够用，预留多）；
- F004 73% 预留（大 Feature + v3 接入预留 + 中间件扩展预留）；
- F005 76% 预留（前端领域未探索，重在预留）；
- F006 60% 预留（最薄壳，预留适度）。

---

## §12 Phase 提示词文件落地约定

### §12.1 文件位置与命名

```
harness/features/
├── README.md                                  ← 本文件（总目录）
├── 立项书.md                                  ← F 编号唯一权威
├── 立项书-大纲目录.md
├── 宪法初稿.md
├── feature001_phase001_cli_validation.md      ← F001-P1 提示词
├── feature001_phase002_template_skeleton.md   ← F001-P2 提示词
├── feature001_phase003_builtin_tools.md       ← F001-P3 提示词
├── feature002_phase001_static_format.md       ← F002-P1 提示词（待开发）
├── ...                                        ← 其他 Phase 提示词（待开发）
```

### §12.2 提示词文件内容契约

每个 `feature*_phase*.md` 提示词文件须包含：

1. **目标声明**：引用本文档对应章节的 Phase 范围；
2. **入口条件**：引用 §X.Y "入口条件"段；
3. **异常退出码表**：从 §3 一览总表复制该 Phase 涉及的所有 Error 类与退出码；
4. **退出条件**：引用 §X.Y "退出条件"段；
5. **可执行命令 / 测试列表**：明确"完成 Phase = 跑通下列命令 / 测试"；
6. **绝对不做清单**：明确"Phase 不做这些，留给下 Phase / 下 Feature"；
7. **引用链接**：立项书对应章节 + 宪法对应条款 + 调研报告对应章节。

### §12.3 Speckit 工作流串联

```
1. 新开会话执行 /speckit.specify + featurexxx_phasexxx_*.md
   → 生成 specs/<branch>/spec.md
2. （可选 1-2 轮）/speckit.clarify → 消除歧义
3. /speckit.plan → 生成 plan.md
4. /speckit.tasks → 生成 tasks.md
5. /speckit.analyze → 三件套一致性检查
6. /speckit.implement → TDD 编码 + 测试
7. 跑 verify_phase_<f>_<n>.py → 必须 PASS
8. Maintainer 复核 → Phase 完成
```

---

## §13 变更日志

| 版本 | 日期 | 作者 | 修订摘要 |
|---|---|---|---|
| v0.1 草稿 | 2026-10-15 | Speckit 起稿 | 首版：F001 三 Phase 详细设计 + F002-F006 Phase 划分总览 + 段位速查表 |
| **v0.2 草稿** | **2026-10-15** | **Speckit 起稿 / Maintainer 待审** | **重大重构**：（1）采用"报错驱动开发"作为 Phase 划分主哲学；（2）新增 §3 Phase 一览总表，列出所有 F001-F006 的 Error class + exit code 映射；（3）严格按奥卡姆剃刀约束退出码分配——大概率错误给码，罕见错误合并或预留；（4）F001-P1 异常类从"举例说明"改为 3 个具体类名 + exit code 锁定（`PathNotFoundError`=1 / `PathPermissionError`=2 / `WorkspaceExistsError`=3）；（5）修复 §2 标题中括号误用问题，把 Occam's Razor 移到正文 §2.2 并加中文译名"奥卡姆剃刀" |
| **v0.3 草稿** | **2026-10-15** | **Speckit 起稿 / Maintainer 待审** | **F001 错误码精简**：（1）删除 F001 exit 9 `EndToEndVerifyError`——静态格式检查属于 F002 域，F001 不重复；（2）合并 exit 4-6 `TemplateSourceMissingError` / `TemplateRenderError` / `FileWriteError` → exit 4 `TemplateGenerationError`（用户修复动作相同）；（3）合并 exit 7-9 `BuiltinToolWriteError` / `SkillsExampleWriteError` / `EndToEndVerifyError` → exit 5 `BuiltinToolGenerationError`；（4）F001 错误码总数从 9 个砍到 5 个，预留从 1 个扩到 5 个（50% 预留）；（5）§11 段位速查表更新：总错误码从 54 降到 50，预留码从 128 升到 132；（6）§4.4 / §4.5 的"绝对不做"清单新增"F001 不做静态格式检查，由 F002 负责" |
| **v0.4 草稿** | **2026-10-15** | **Speckit 起稿 / Maintainer 待审** | **F001 幂等性重构**：（1）采纳 Maintainer 四场景设计（场景 1 全新创建 / 场景 2 幂等补齐 / 场景 3 `--force` 模板重置 / 场景 4 手动放弃重做），删除原 `WorkspaceExistsError`（exit 3）改为预留；（2）`BuiltinToolGenerationError` 从 exit 5 上移到 exit 7，段位按 3-3-4 连续分配（P1=1-3, P2=4-6, P3=7-10）；（3）新增 §4.1.1 "四场景与幂等性设计"段，详细说明 `donkey init` 幂等语义 + `--force` 删除 + 重新补齐模板的边界 + 模板清单 `core/workspace/templates/manifest.json` 的角色；（4）新增 §4.1.1 末尾的"用户视角工作流"小节（损坏恢复 / 全部重置 / 推倒重来）；（5）§4.4 / §4.5 退出条件新增对场景 1-4 的全面断言（幂等场景 2 / `--force` 场景 3 / 手动放弃场景 4 / 用户内容保护验证）；（6）§11 总错误码从 50 降到 49，预留码从 132 升到 133，F001 预留比例从 50% 升到 60% |
| **v0.5 草稿** | **2026-10-15** | **Speckit 起稿 / Maintainer 待审** | **F001 退出码连号紧凑化**：（1）采纳 Maintainer 反馈——不强求段位按 3-3-4 等分，实际使用 exit 1-4 连号，预留 5-10 放末尾；（2）`TemplateGenerationError` 从 exit 4 下移到 exit 3，`BuiltinToolGenerationError` 从 exit 7 下移到 exit 4；（3）§4.2 / §4.3 / §4.4 / §4.5 标题与正文所有 exit code 引用同步更新；（4）§11 段位速查表 F001 行注明"1-4 连号 / 5-10 预留"；（5）§3.1 设计说明第 4 条改写为"退出码实际使用连号，预留码放末尾；不强求段位按 N-N-N 等分" |

---

**Version**：v0.5 草稿
**Source of truth**：
- `harness/features/立项书.md`（F 编号唯一权威）
- `.specify/memory/constitution.md`（Phase 切分规则 / 段位表 / 不可妥协原则 N-01~N-12）
- `harness/prompt/speckit.md`（Speckit 工作流）
