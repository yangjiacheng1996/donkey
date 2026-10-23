# donkey 项目开发目录（features / phases 总索引）

> 本文件是 `harness/features/` 下所有 `featurexxx_phasexxx_<phase_name>.md` 提示词文件的**总目录**。
>
> - **权威源**：所有 F 编号定义以 `harness/features/立项书.md` 为准；不可妥协原则、Phase 切分规则、段位表以 `.specify/memory/constitution.md` 为准。
> - **维护人**：Maintainer（yangjiacheng）；由 Speckit 起稿、人工复核修订。

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
| ★★ | `harness/report/大模型toml参数设计.md` | `providers/` 目录 schema 权威（provider 白名单 / 字段 / `enabled` 开关 / 三档鉴权 / exit 11 校验清单） |
| ★★ | `harness/report/sessions_sqlite表结构一览.md` | `memory/*.sqlite3` schema 权威（`sessions_metadata` 表设计 + F002-P2 健康检查口径） |
| ★ | `harness/LangChain_doc/`、`harness/LangGraph_doc/`、`harness/Managed_deep_agents/` | 官方文档镜像 |
| ★ | `harness/prompt/speckit.md` | Speckit 工作流提示词 |
| ★★★ | `harness/features/README.md`（本文档）| **各 Feature 段位内 exit code 落地映射**（F001 见 §3.1+§4.1、F002 见 §3.2+§5、F003 见 §3.3+§6、F004 见 §3.4+§7、F005 见 §3.5+§8、F006 见 §3.6+§9）。段位边界与冗余性原则仍以立项书 §5.5.3 + 宪法 §4.4 为权威 |

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

### §1.2 提示词文件命名格式

```
featurexxx_phasexxx_<phase name>.md
```

- `xxx` 三位数字，左侧补 0；第一个 `xxx` = F 编号，第二个 `xxx` = Phase 编号（**与 §3 一览总表 / §X.Y 章节号 / verify 脚本名严格一致**）；
- `<phase name>` 用英文短横线连字符（kebab-case），与 §X.Y 章节标题保持一致（`cli_validation` / `template_skeleton` / `builtin_tools` / `static_format` / `dynamic_runtime` / `list` / `new` / `tools` / `middleware` / `agent_loop` 等）；
- **1 Phase = 1 提示词文件 = 1 次 `/speckit.specify` 闭环**（9 步流程见 §12.4）；v1 baseline 27 Phase = 27 文件（详见 §12）；
- 例：`feature001_phase001_cli_validation.md`（F001-P1）、`feature003_phase002_new.md`（F003-P2）、`feature004_phase006_middleware.md`（F004-P6）；
- **Phase 编号严格串行**：同 Feature 内 Phase 编号严格递增；Phase 编号不跨 Feature 复用；
- **本规则与 §1.5 术语表配套**：Phase = dev unit，**不**用作 exit code 子段或 Error class 分组的抽象概念（那两者用"子段"和"Error class"分别表达）。

### §1.3 Phase 切分规则（来自宪法 §4.3 + 立项书 §5.2.1）

| 规则 | 适用 Feature | 切分单位 |
|---|---|---|
| **规则 A：按二级命令切** | 含二级命令的 Feature（如 F003） | 每个二级命令 = 一个 Phase |
| **规则 B：按退出码段位切** | 无二级命令的 Feature（如 F001/F002/F004/F005/F006） | 每 N 个功能相似的退出码组合 = 一个 Phase |



### §1.4 Phase 三要素契约（来自宪法 §4.3）

每设计一个 Phase 必须带齐三要素，对应 `featurexxx_phasexxx_*.md` 提示词文件中的固定章节：

1. **入口条件（Entry Gate）**：前置 Phase 的退出条件全部满足（可能跨 Feature——按 §10.2 跨 Feature 推进策略 / 门控关系）；
2. **异常退出码（Exit Code）**：该 Phase 覆盖的子段内 Error class 对应的 exit code 集合（落在该 Feature 段位内；具体码值见 §3.1-§3.6 一览总表对应行）；
3. **退出条件（Exit Gate）**：可执行、可验证的硬指标——由 `verify_phase_<f>_<n>.py` 验证脚本跑出 PASS/FAIL。

### §1.5 核心术语区分（避免 Phase / 段位 / 子段 / Error class 概念混用）

| 术语 | 定义 | 标识 | 用途 | v1 baseline 数 |
|---|---|---|---|---|
| **Phase** | **开发阶段**——1 次 `/speckit.specify` 闭环单位（见 §12.4（1 次 /speckit.specify 闭环的 9 步流程）） | `F###-P#` | 提示词文件命名、§X.Y 章节、跨 Phase 滚动规划 | 27 |
| **段位** | exit code 段位——一个 Feature 拥有的 exit code 连续范围（详见立项书 §5.5.3 段位分配总表） | `1-10` / `11-20` / `21-30` / `31-100` / `101-170` / `171-200` | 段位预留冗余性、跨 Feature 不重叠 | 6（F001 / F002 / F003 / F004 / F005 / F006） |
| **子段** | 段位内的 exit code 子分组——Phase 在段位内"占用"的 exit code 范围（含已用 + 预留） | `F001 子段 1` = exit 1-2；`F001 子段 2` = exit 3；`F001 子段 3` = exit 4 | §3.1-§3.6 一览总表每行；段位切 Phase 的产物 | 27（v1 baseline 1:1 与 Phase 数对齐） |
| **Error class** | 具体 Python 异常类（`PathNotFoundError` / `PathPermissionError` / ...） | 类名 | 代码中的 `raise` / `except` 捕获 | **89**（v1 实装码位 80 个 → 其中 exit 11 是 1 个伞形类 + 7 个子类 = 8 个类，故 v1 实装类 = 80 − 1 + 8 = **87**；再加 F003-P4 import 的 2 个 v1.x 留接口类 `SessionImportFormatError` / `SessionImportSqliteError` → 定义态共 **89**；详见 §3.1~§3.6 + §11 总分配。**注**：F004-P5 的 3 个 Store 码（71-73）是 **v3 占位**，不计入 v1 实装） |

**关键区分**：

- **Phase** 是**开发视角**的单位（"我下一轮要写什么"）；
- **段位 / 子段** 是**错误视角**的单位（"哪个码值表示什么失败"）；
- **Error class** 是**代码视角**的单位（"raise / except 的具体类型"）。

v1 baseline 27 Phase 与 27 子段 1:1 对齐（"一个 Phase 占用 1 个子段"）是设计选择，不是逻辑必须。理论上：
- 1 个 Phase 可以**覆盖多个子段**（合并开发，如"一次 /speckit.specify 同时实现 F001-P2 + F001-P3"——v1 不采用但理论允许）；
- 1 个子段 也可以**被拆为多个 Phase**（如"F004-P6 middleware 9 错误拆为 2 个 Phase"——高复杂度时按需拆分）。

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

### §3.1 F001 `donkey init`（段位 1-10，3 子段）

> **v1 baseline**：F001 的 3 子段与 3 Phase 1:1 对齐（Phase 1 = 子段 1 = exit 1-2；Phase 2 = 子段 2 = exit 3；Phase 3 = 子段 3 = exit 4）。术语精确表达见 §1.5。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F001 | 子段 1（= Phase P1）| `PathNotFoundError` | 1 | PATH 父目录不存在 / 路径解析失败（如相对路径、非法字符） | 高 |
| F001 | 子段 1（= Phase P1）| `PathPermissionError` | 2 | PATH 权限不足（父目录和 workspace 缺失读 / 写 / 执行权限） | 高 |
| F001 | 子段 2（= Phase P2）| `TemplateGenerationError` | 3 | 模板骨架生成失败（合并四项：源缺失 / 渲染失败 / 文件写入失败 / sqlite3 schema 构造失败；用户修复动作相同） | 低 |
| F001 | 子段 3（= Phase P3）| `BuiltinToolGenerationError` | 4 | 内置 `@tool` + Skills example 生成失败（合并三项：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、端到端集成预演失败） | 低 |
| F001 | 子段预留 | （预留） | 5-10 | 留给 v1.x 试运行期发现的新错误 | — |

> **设计说明**：
> 1. F001 的职责是"存活检查"——只管"能不能生成文件"，不管"生成的文件格式是否合法"。文件格式的合法性属于 F002 静态检查范畴（exit 11-14）。
> 2. `donkey init` 是**幂等**的（详见 §4.1.1 四场景说明）：已存在 workspace + 无 `--force` 不是错误。
> 3. `BuiltinToolGenerationError`（exit 4）覆盖内置工具写入失败 / SKILL.md 三层写入失败 / 集成预演 import 失败三项——三者对用户的修复动作相同（重装 donkey / 检查权限 / 重试 init），按奥卡姆剃刀合并为单一 exit code。
> 4. **退出码实际使用连号**（1-4），预留码（5-10）放末尾；不强求段位按 N-N-N 等分。
>
> **v1 不引入 Path basename 命名校验**（立项书 §4.6.4 注脚）：当前决定**不**强制 workspace 路径 basename 满足 Python 标识符命名规则；用户在 v1 可使用任意目录名（含 `-` / `.` / 空格 / Unicode 等）。如果 v2 引入 workspace-as-package 需求，再补规则——避免为不存在的 v2 假想场景写代码。

### §3.2 F002 `donkey load`（段位 11-20，3 子段）

> **v1 baseline**：F002 的 3 子段与 3 Phase 1:1 对齐。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F002 | 子段 1（= Phase P1，**伞形码**）| **`ProviderTomlLoadError`**（伞形） | **11** | **`providers/` 目录加载阶段任何失败**——覆盖 7 个子类（详见下表 §3.2.1）：`ProviderTomlSyntaxError`（TOML 解析）/ `ProviderTomlFieldError`（字段名拼写、必填缺失、零 enabled provider、默认项跨文件不一致）/ `ProviderTomlFieldTypeError`（字段类型）/ `ProviderTomlFieldValueError`（字段值硬越界、URL 合法性）/ `ProviderTomlScopeError`（scope 检查：白名单 / 永久黑名单 / 暂不支持清单 / v2+ 候选）/ `ProviderTomlMissingModelError`（default_model 不在 default provider 的 `[models]` 表）/ `ProviderTomlHostNotAllowedError`（api_host 不被该 provider 类允许） | 高 |
| F002 | 子段 1（= Phase P1）| `McpJsonSyntaxError` | 12 | `mcp/mcp.json` JSON 语法错误 | 高 |
| F002 | 子段 1（= Phase P1）| `SkillFrontmatterError` | 13 | `skills/*/SKILL.md` YAML frontmatter 错误（缺 `name` / `description`） | 高 |
| F002 | 子段 2（= Phase P2）| `InstructionMissingError` | 14 | `instruction.md` 缺失 / 目录结构不完整 | 高 |
| F002 | 子段 2（= Phase P2）| `ProviderConnectivityError` | 15 | 模型连通性失败（`init_chat_model` + ping 超时 / 鉴权失败 401/403）——**凭据无效不走本码**：云端 provider 的空 `api_key` 在**构造期**即被拒（`Missing credentials`）→ exit 11 伞形（见 §3.2.1 + 调研 §9.1.1 / §9.2）；本码只留给"凭据有效但连通性失败" | 中 |
| F002 | 子段 2（= Phase P2）| `SqliteSchemaError` | 16 | `memory/sessions.sqlite3` 不可读 / schema 不健康（**5 项断言**：`PRAGMA table_info(checkpoints)` + `PRAGMA table_info(writes)` + `PRAGMA table_info(sessions_metadata)` 6 字段 + `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 索引名 + `PRAGMA integrity_check`；详见 `sessions_sqlite表结构一览.md` §7） | 低 |
| F002 | 子段 3（= Phase P3）| `ToolLoadError` | 17 | `tools/*.py` `@tool` 自动发现失败（import 错误 / 函数签名不合规） | 中 |
| F002 | 子段 3（= Phase P3）| `SkillLoadError` | 18 | `skills/*/SKILL.md` 通过自研 loader 加载失败（Level 2 读取异常） | 中 |
| F002 | 子段 3（= Phase P3）| `McpServerError` | 19 | `MCPAdapter` 拉起 server 失败（stdio / http 连接失败） | 中 |
| F002 | 子段预留 | （预留） | 20 | 留给 v1.x 试运行期发现的新错误 | — |

#### §3.2.1 `ProviderTomlLoadError`（exit 11）子类清单

> **设计原则**：exit 11 归 `ProviderTomlLoadError` **伞形 Error class**，承载下表 **7 个子类**（伞形本身 + 7 子类 = 8 个 Error class）——所有这些错误的用户修复动作相同（“打开 `providers/` 目录检查 / 修正字段后重试 `donkey load`”），按奥卡姆剃刀合并为单一 exit code；子错误在 traceback 中仍可区分。**多文件布局下，错误消息必须携带文件路径**（`providers/<id>.toml: ...`）。

| 子类 Error class（继承 `ProviderTomlLoadError`） | 触发条件 | 报错概率 | 备注 |
|---|---|---|---|
| `ProviderTomlSyntaxError` | `tomllib.TOMLDecodeError` —— TOML 解析失败 | 高 | 原 exit 11 唯一场景，保留为伞形的一个子类型 |
| `ProviderTomlFieldError` | Pydantic schema reject —— 字段名拼写错误（如 `temprature`） / 必填字段缺失 | 高 | sub-class |
| `ProviderTomlFieldTypeError` | 字段值类型不匹配（如 `api_key = 42` / `api_key = [...]`） | 高 | sub-class |
| `ProviderTomlFieldValueError` | 字段值**硬越界**（如 `temperature = 3.0`、`api_host` 非 URL 格式） | 中 | **注意**：硬边界 = `temperature ∈ [0.0, 2.0]`（OpenAI 协议硬限）；`temperature > 1.5` 这类**软越界**走 warning（exit 0），**不抛**此异常 |
| `ProviderTomlScopeError` | scope 检查失败：`default_provider` 不在白名单 / 是永久黑名单成员（v1 空集合）/ 是暂不支持清单成员（v1 空集合）/ 是 v2+ 候选成员（baidu / iflytek / sensetime，详见调研报告 §3.5）——v2+ 候选只是"未排期开发"、不是独立错误类，与"白名单外"同属 scope 判定 | 中 | sub-class |
| `ProviderTomlMissingModelError` | `default_model` 不在该 provider 的 `models` 列表内 | 低 | sub-class |
| `ProviderTomlHostNotAllowedError` | `api_host` 已声明但 provider 类的 langchain 不允许自定义 host（如 Bedrock via Converse） | 低 | sub-class |

> **关键约束**：
> - **所有子类抛错时，最终 CLI 层映射的 exit code 都是 11**——`compute_exit_code()` 优先查伞形 Error class，再匹配子类（详见 §11 exit code 常量定义）；
> - **warning 不抛此伞形**——`temperature` 软越界、`openai-compatible` 的空 `api_key` → warning 路径，不触发 exit code 11；
>   （**云端 provider 的空 `api_key` 是硬错 exit 11**——实测它在**构造 ChatModel 阶段**就失败（`Missing credentials`），且报错文案指向 env var（违背"绝不读 env var"立场）；而**本地 provider**（`ollama` / `meta`）空 `api_key` **合法**——本地端点（Ollama / vLLM / LiteLLM）本就不校验鉴权。完整分档表见调研报告 §9.2）；
> - 单一 exit code 是**奥卡姆合并**——用户修复动作一致，无需区分 7 种子类于脚本判断；
> - 子类**仍可在 traceback 中区分**（每个子类的 docstring 标注具体原因），便于日志排查。

### §3.3 F003 `donkey session`（段位 21-30，4 子段）

> **v1 baseline**：F003 的 4 子段与 4 Phase 1:1 对齐（按 §1.3 规则 A——每个二级命令 = 1 个 Phase / 1 个子段）。
>
> **标题生成契约（N-10）**：`session new` 的标题**必须在 `new_session` 内、落库前定稿**——用户显式 `--title` → 用它；给了 `--first-prompt` → 调 LLM 总结 ≤ 20 字（超时 ≤ 5s），**总结失败 / 超时 / 空返回 → 回退为首轮 prompt 的前 20 字**（**绝不**回退成"无标题会话"）；两者都不给 → 默认"无标题会话"。因此**标题总结失败不产生任何 exit code**（session 创建始终成功，exit 0）——exit 25 改绑给 `SessionNewCheckpointError`（SqliteSaver 写 initial checkpoint 失败）。详见立项书 §5.5.4.5。

`memory/sessions.sqlite3` 文件**同时承载三张表与两个索引**（与 SqliteSaver 同文件共存，详见 §4.1.1 "memory/ 模板边界"）：
- **SqliteSaver 自有表**（`checkpoints` / `writes`）—— 短期 message 历史；`thread_id` 即 SqliteSaver 主键；schema 由 `langgraph-checkpoint-sqlite` 包管理；
- **`sessions_metadata` 表**（donkey 自管，**`donkey init` 阶段作为模板预创建**，含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 索引）—— 会话元数据（`thread_id` ↔ `title` 映射、`created_at` / `updated_at` / `donkey_version` / `first_prompt`）；donkey 用户的 `list` / `remove` / `--title` 全部走此表，**不**用 SqliteSaver 状态反推。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F003 | 子段 1（= Phase P1 = list）| `SessionListSqliteError` | 21 | `sessions_metadata` 表读失败（list 时） | 低 |
| F003 | 子段 1（= Phase P1 = list）| `SessionListLockError` | 22 | sqlite 锁等待超时（list 时, ≤ 1s; 立项书 §5.5.4.1 退出条件 4） | 低 |
| F003 | 子段 2（= Phase P2 = new）| `SessionNewSqliteError` | 23 | `sessions_metadata` 表写失败（new 时：INSERT 失败 / `donkey_version` 不匹配） | 低 |
| F003 | 子段 2（= Phase P2 = new）| `SessionNewLockError` | 24 | sqlite 锁等待超时（new 时） | 低 |
| F003 | 子段 2（= Phase P2 = new）| `SessionNewCheckpointError` | 25 | SqliteSaver 写 initial checkpoint 失败（new 时：checkpoint 落盘错误） | 低 |
| F003 | 子段 3（= Phase P3 = remove）| `SessionRemoveSqliteError` | 26 | sqlite 删除失败（remove 时：DELETE FROM sessions_metadata 或 SqliteSaver 物理清 checkpoint 失败） | 低 |
| F003 | 子段 3（= Phase P3 = remove）| `SessionNotFoundError` | 27 | 标题不存在（`sessions_metadata` 表 WHERE title=? 查询无结果，remove 时） | 中 |
| F003 | 子段 4（= Phase P4 = import）| `SessionImportFormatError` | 28 | 导入文件格式错误（非 sqlite3 / 损坏文件；**v1 留接口, v1.x 落地**, 立项书 §5.5.4.4） | 低 |
| F003 | 子段 4（= Phase P4 = import）| `SessionImportSqliteError` | 29 | 导入时 sqlite 写失败（主键冲突 / 容量不足；**v1 留接口, v1.x 落地**, 立项书 §5.5.4.4） | 低 |
| F003 | 子段 4（= Phase P4 = import）| （v1 留接口位）| 30 | 留给 v1.x import 落地时绑定 Error class（立项书 §5.5.4.4） | — |

### §3.4 F004 `donkey run`（段位 31-100，7 子段）

> **v1 baseline**：F004 的 7 子段与 7 Phase 1:1 对齐（按 §1.3 规则 B——按退出码段位切，每 10 个连续码 = 1 个 Phase / 1 个子段）。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
|---|---|---|---|---|---|
| F004 | P1 = tools | `ToolImportError` | 31 | 工具 import 失败（`tools/*.py` 语法 / 循环引用） | 中 |
| F004 | P1 = tools | `ToolExecutionError` | 32 | 工具执行异常（用户自定义 @tool 抛错） | **高** |
| F004 | P1 = tools | `ToolTimeoutError` | 33 | 工具超时（`commandline.py` / `webfetch.py` 超时掐断） | **高** |
| F004 | P1 = tools | `ToolArgumentError` | 34 | 工具参数错误（缺必填 / 类型不匹配） | **高** |
| F004 | P1 = tools | （预留） | 35-40 | 留给未来 tools 相关错误（6 个） | — |
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
| F004 | P5 = store | `StoreOpenError` | 71 | store 初始化失败（v3 SqliteStore 文件路径无效 / 权限不足）——**v3 占位码，v1 不实装**（v1/v2 用 `InMemoryStore`，不落盘、不抛此错；见立项书 §5.5.5） | 低（v3） |
| F004 | P5 = store | `StoreWriteError` | 72 | store 写入失败（`aput` 抛错；Schema 不兼容 / 容量不足）——**v3 占位码，v1 不实装** | 低（v3） |
| F004 | P5 = store | `StoreReadError` | 73 | store 读取失败（`aget` / `asearch` 抛错；JSON 反序列化失败）——**v3 占位码，v1 不实装** | 低（v3） |
| F004 | P5 = store | （预留） | 74-80 | 留给 v1.x 试运行期发现的新错误（Store 相关） | — |
| F004 | P6 = middleware | `ToolErrorMiddlewareError` | 81 | ToolError 中间件异常（不可恢复，绕过 wrap-style） | 低 |
| F004 | P6 = middleware | `ToolRetryMiddlewareError` | 82 | ToolRetry 重试超限（exponential backoff 用尽） | 中 |
| F004 | P6 = middleware | `ModelRetryMiddlewareError` | 83 | ModelRetry 重试超限（429/503 用尽） | 中 |
| F004 | P6 = middleware | `SummarizationMiddlewareError` | 84 | 摘要生成失败（token 上限触发的压缩出错） | 低 |
| F004 | P6 = middleware | `ModelCallLimitMiddlewareError` | 85 | 调用次数超限（thread 级 / run 级熔断） | **高** |
| F004 | P6 = middleware | `PIIMiddlewareError` | 86 | PII 检测异常（策略配置错 / redact 函数抛错） | 低 |
| F004 | P6 = middleware | `TodoListMiddlewareError` | 87 | TodoList 系统提示注入失败 | 低 |
| F004 | P6 = middleware | `LLMToolSelectorMiddlewareError` | 88 | 工具预筛选调用失败（小模型 API 异常） | 中 |
| F004 | P6 = middleware | `ContextEditingMiddlewareError` | 89 | 上下文清理异常（ClearToolUsesEdit 抛错） | 低 |
| F004 | P6 = middleware | `ModelAuthenticationError` | 90 | **LangChain LLM provider 鉴权失败**（401/403 / 模型不存在 404；属 non-retryable，**首次即抛**） | 中 |
| F004 | P7 = agent loop | `GraphCompileError` | 91 | LangGraph 图编译失败（State schema 异常 / 节点名冲突） | 低 |
| F004 | P7 = agent loop | `StateSchemaError` | 92 | State schema 不匹配（字段缺失 / 类型不符） | 低 |
| F004 | P7 = agent loop | `NodeTypeError` | 93 | 节点类型不匹配（function / dataclass 错配） | 低 |
| F004 | P7 = agent loop | `EdgeConnectError` | 94 | Edge 连接错误（条件边判断异常） | 低 |
| F004 | P7 = agent loop | （预留） | 95-100 | 留给未来 Agent Loop 相关错误（6 个） | — |

#### §3.4.1 LLM Provider Runtime 异常 → exit code 映射

> F004-P6 (middleware) 主要覆盖 donkey 自身中间件的异常；LangChain 1.x 的 LLM provider 异常（`ModelAuthenticationError` / `ModelRateLimitError` / `ModelConnectionError` / `ModelTimeoutError` 等）在 donkey 内被中间件层 + 各国 ChatModel 类的 retry policy 包装处理后映射到 exit code。**本节定义映射规则**，与上面 §3.4 P6/P7 的 Error class 保持一致。

| LangChain 异常类 (langchain_core.exceptions) | 是否 retryable | 默认 retry policy | donkey v1 映射 exit code | Error class |
|---|---|---|---|---|
| `ModelAuthenticationError` | ❌（**401/403** 永久拒绝） | 不重试 | **90**（F004-P6 已分配） | `ModelAuthenticationError` |
| `ModelPermissionDeniedError` | ❌（权限不足，非短期可恢复） | 不重试 | **90**（同 ModelAuthenticationError 处理，伞形合并按奥卡姆） | `ModelAuthenticationError` |
| `ModelInvalidRequestError` | ❌（400 bad request，用户的 prompt 或参数错） | 不重试 | **83**（F004-P6 middleware 拦截后抛 `ModelRetryMiddlewareError` 反映"请求始终失败"，v1 baseline 用 83） | `ModelRetryMiddlewareError` |
| `ModelNotFoundError` | ❌（404 模型不存在） | 不重试 | **90**（同 ModelAuthenticationError 伞形） | `ModelAuthenticationError` |
| `ModelRateLimitError` | ✅（429 短期） | exponential backoff 重试，直到耗尽 | **83**（F004-P6 `ModelRetryMiddlewareError`，重试超限） | `ModelRetryMiddlewareError` |
| `ModelAPIError` | ✅（5xx provider 服务故障） | exponential backoff 重试，直到耗尽 | **83**（同上） | `ModelRetryMiddlewareError` |
| `ModelConnectionError` | ✅（网络故障） | exponential backoff 重试，直到耗尽 | **83**（同上） | `ModelRetryMiddlewareError` |
| `ModelTimeoutError` | ✅（请求超时） | exponential backoff 重试，直到耗尽 | **83**（同上） | `ModelRetryMiddlewareError` |
| `ContextOverflowError` | ❌（输入超上下文窗口） | 不重试 | **85**（F004-P6 `ModelCallLimitMiddlewareError`——"调用次数超限/输入超限"伞形合并） | `ModelCallLimitMiddlewareError` |
| **（构造期）`openai.OpenAIError: Missing credentials`** | ❌ | 不重试 | **90** | `ModelAuthenticationError` |

> **实测补充**：最后一行是实测新增——`api_key` 缺失 / 为空串时，底层 SDK 在**构造 ChatModel / client 阶段**就抛 `Missing credentials`（**不是**运行时的 401），因此 §3.2.1 的"空 `api_key` → warning"路径终点是**构造期失败**。该异常原始文案含"or set the `OPENAI_API_KEY` ... environment variable"——与"donkey 绝不读 env var"立场冲突，**CLI 层必须改写文案**（如"api_key 未配置或为空，请检查 providers/<provider_id>.toml"），不得把用户引向 env var 路径。详见 `harness/report/大模型toml参数设计.md §9.1.1 / §9.2`。

> **奥卡姆合并逻辑**（依据 §1.5 哲学 + 大概率原则）：
> - **retryable 错误**（429 / 5xx / 网络 / 超时 / **400 请求格式错**）→ 全部退避后都汇总到 exit 83 (`ModelRetryMiddlewareError`)。用户的修复动作相同——"等会儿重试 / 改写 prompt / 切换 provider"；
> - **non-retryable 鉴权类**（401/403/404 + 构造期 `Missing credentials`）→ 退避无效，首次即抛，汇总到 exit 90 (`ModelAuthenticationError`)。用户的修复动作相同——"检查 API key / 检查 model 名"；
> - **non-retryable 输入超限类**（`ContextOverflowError`）→ exit 85 (`ModelCallLimitMiddlewareError`)；
> - 4 种退出码覆盖 9 种 LangChain 异常 + 1 类构造期错误（按"修复动作合并"原则）。
>
> **边界说明**：`ModelInvalidRequestError`（400）归 **83**（"请求始终失败"，可降低 token / 改写 prompt 后重试），`ContextOverflowError` 单独留在 85。
>
> **v1 警示**：未来若 LangChain 增加新异常类且不属于上述合并类别，**优先**尝试上述合并；若用户实测发现"修复动作实际不同"，开新 exit code（90 已被占用，需要从 P7 预留 95-100 段借）。

### §3.5 F005 `donkey web`（段位 101-170，7 子段）

> **v1 baseline**：F005 的 7 子段与 7 Phase 1:1 对齐（按 §1.3 规则 B）。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
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

### §3.6 F006 `donkey gui`（段位 171-200，3 子段）

> **v1 baseline**：F006 的 3 子段与 3 Phase 1:1 对齐（按 §1.3 规则 B）。

| Feature | 子段 / Phase | 异常类名 | 退出码 | 异常原因描述 | 报错概率 |
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
├── instruction.md              ← 模板（文本）
├── providers/                  ← 模板目录（**一 provider 一文件**）
│   ├── default.toml            ← 模板（文本）—— 全局默认（default_provider / default_model）
│   ├── README.md               ← 模板（文本）—— 26 家白名单目录快照
│   ├── openai.toml             ← 模板（文本）—— provider stub（enabled = false）
│   └── ...                     ← 共 26 个 provider stub（v1 白名单）
├── mcp/mcp.json                ← 模板（JSON 文本）
├── skills/example/             ← 模板（含子文件 SKILL.md + reference/ + scripts/ + templates/）
├── tools/filesystem.py         ← 模板（内置 7 个 @tool）
├── tools/commandline.py        ← 模板（内置 run_shell）
├── tools/webfetch.py           ← 模板（内置 fetch_url）
├── tools/__init__.py           ← 模板
├── tools/README.md             ← 模板
├── mcp/README.md               ← 模板
├── skills/README.md            ← 模板
├── memory/README.md            ← 模板（说明 sqlite3 是模板 + --force 行为）
├── memory/sessions.sqlite3   ← 模板（init 阶段 schema-built 空 sqlite3；SqliteSaver 表 + sessions_metadata 表 + 索引一次创建）
├── memory/store.sqlite3        ← 模板（init 阶段**空文件**——schema 全部推迟到 v3 SqliteStore 实施时）
├── memory/knowledge.sqlite3          ← 模板（init 阶段空 sqlite3；schema 待 v3+ 选型后正式化）
├── README.md                   ← 模板
└── .gitignore                  ← 模板（已含 `memory/*.sqlite3`）
```

> **manifest 分阶段追加（v1 baseline = 54 条）**：模板清单**不一次性预列全部路径**，而是随各 Phase 逐段追加——**保证"清单里的每一条都已有对应的模板源 .txt"**（否则 P2 的 `render_templates` 会因源缺失抛 exit 3）：
>
> | 阶段 | 追加条数 | 累计 | 内容 |
> |---|---|---|---|
> | **F001-P1** | 3 | 3 | `instruction.md` / `providers/default.toml` / `mcp/mcp.json`（与 P1 已就位的 3 个 .txt 占位一一对应；**P1 只建档清单（3 条），不加载、不解析、不渲染**） |
> | **F001-P2** | +43 | 46 | 其余 7 个文本模板 + 6 个目录条目（`tools/` `mcp/` `skills/` `skills/example/` `memory/` **`providers/`**）+ 3 个 sqlite3 模板 + **`providers/README.md` + 26 个 provider stub（`providers/<id>.toml`）** |
> | **F001-P3** | +8 | 54 | `tools/__init__.py` + **`tools/changes.py`（变更记录契约库，diff-ready 地基）** + 3 个内置 tool + 3 个 Skills Level 3 示例 |
>
> **包内 `templates/manifest.json` ≠ workspace 根的 `manifest.json`**：前者是**模板文件清单**（装在 donkey 包内，驱动 `render_templates` 幂等渲染）；后者是 **D-01 的 workspace manifest**（落在 `<workspace>/manifest.json`，含 `version` / `name` / `created_at` / `donkey_version` 4 字段，由 `core/workspace/manifest.py` 单独写入，**不**进模板清单）。

> **文本模板 vs sqlite3 模板**：`templates/` 下文本类模板（`*.md` / `*.toml` / `*.json` / `*.py`）以文本源码形式随包分发；sqlite3 类模板（`memory/*.sqlite3`）由 `core/workspace/sqlite3_templates.py` 在 `donkey init` 阶段**程序化构造**：
>
> - `sessions.sqlite3` → 调 `SqliteSaver(conn).setup()`（**实例方法**）创建 SqliteSaver 自身 `checkpoints` / `writes` 表 + donkey 自管 `sessions_metadata` 表（6 字段）+ 2 索引（schema 在 v1 就绪）；
> - `store.sqlite3` → **v1 仅触发空 sqlite3 文件创建**，schema 全部推迟到 v3 SqliteStore 实施时（详见 F001-P2 §4.7.6 + `sessions_sqlite表结构一览.md` §3 + 立项书 §4.10 TD-02 路线图步骤 1）；
> - `knowledge.sqlite3` → **v1 仅触发空 sqlite3 文件创建**，schema 待 v3+ RAG 引擎选型后正式化。
>
> —— 不在包内携带二进制 sqlite3 文件，避免 schema 漂移。**v1 不挂 Store / 不接 RAG**：donkey 本体 v1/v2 不读 `store.sqlite3`（F004-P5 用 `InMemoryStore` 顶替），更不读 `knowledge.sqlite3`——空文件即正确契约。

> **memory/ 模板边界**（关键 design intent——`--force` 等于"恢复出厂设置"，sqlite3 文件是模板而非保留型运行数据；该边界是 §4.4 F001-P2 测试 14 / 15 的设定依据）：
>
> - `memory/` 目录 + `memory/README.md` + `memory/sessions.sqlite3` + `memory/store.sqlite3` + `memory/knowledge.sqlite3` **全部纳入 `templates/manifest.json` 模板清单**，由 `donkey init` 阶段统一预创建；
> - **三个 sqlite3 模板的程序化构造**（`core/workspace/sqlite3_templates.py` 内定义 schema builder，由 `core/workspace/init.py::render_templates` 按条目 `format` 分派调用，**不**在包内携带二进制模板文件——避免 schema 与代码漂移）：
>   - `memory/sessions.sqlite3`：连接 sqlite3 → 构造 `SqliteSaver(conn)` 并调 `saver.setup()` 创建 `checkpoints` / `writes` 表 → `CREATE TABLE IF NOT EXISTS sessions_metadata (thread_id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL, donkey_version TEXT NOT NULL, first_prompt TEXT)` + `CREATE INDEX idx_sessions_metadata_title` + `CREATE INDEX idx_sessions_metadata_updated_at`；
>   - `memory/store.sqlite3`：连接 sqlite3 **仅触发空文件创建**——**不**建任何表 / 索引；schema 全部推迟到 v3 SqliteStore 实施时（届时 Maintainer 修改 F001-P2 §4.7.6 + `harness/report/sessions_sqlite表结构一览.md` §3 + 立项书 §4.10 TD-02 路线图后追加 `store_items` 等建表 SQL）；
>   - `memory/knowledge.sqlite3`：连接 sqlite3 创建空文件，**不**预设 schema——向量引擎（sqlite-vec / faiss+sqlite）选型待 v3+ 决定后再正式化；该文件占位让 workspace zip 备份结构稳定；
> - **`--force` 行为**（"恢复出厂设置"语义，与"清空 sqlite3"等价）：遍历模板清单 → 删 + 重建**全部模板文件**。`memory/sessions.sqlite3` 被重建后，SqliteSaver 历史与 sessions_metadata 元数据**一并清空**；用户**必须**在 `--force` 前手动备份（`cp memory/sessions.sqlite3 /tmp/backup.sqlite3` 等）。**这是 trade-off**：换来了"模板清单驱动一切"的统一心智模型 + workspace 迁移快照与 `--force` 输出一致；
> - **幂等语义**：未传 `--force` 时，已存在 sqlite3 文件**不重建**——与其它文本模板一致；
> - **D-02 "运行数据可选择性导出"语义保留**：sqlite3 文件虽属模板，但仍可在 workspace zip 备份时**选择性剔除**（如客户端实现 `--include-memory` flag 选择是否带 sqlite3）；即"模板身份" ≠ "必须导出"。**导出的 workspace 在 `donkey load` 时若 sqlite3 缺失，按模板语义由 init 一次性补齐**（含 schema）；
> - **退出码联动**：首次 init 后 sqlite3 schema 健康；后续用户手工破坏 sqlite3（如手动编辑 / 误删表）触发 F002-P2 `SqliteSchemaError` (exit 16) ——这正是该 exit code 现在唯一可靠的触发场景（init 阶段不再产生 schema 不健康文件）。

**用户内容**（donkey 不动）：
- 用户自定义的 `tools/*.py`（不在清单内）
- 用户自定义的 `skills/*/`（不在清单内）
- 用户任意创建的目录 / 文件（如 `media/` / `videos/` / `notes/`）

**`--force` 行为细节**：
- 遍历模板清单，对每个模板路径执行 `delete`（文件或目录递归删除）+ `create`（默认内容）；
- 不在清单内的任何文件 / 目录**完全不动**；
- **清单内的模板文件一律被覆盖回出厂内容**——包括用户可能编辑过的 `instruction.md` / **`providers/*.toml`（含用户填的 `api_key`！）** / `skills/example/SKILL.md`（"恢复出厂设置"语义，见 F001-P2 §6.8 断言）；用户想保留自己的内容，应**先备份**再 `--force`；
- **两个 manifest 的处置不同**：`<workspace>/manifest.json`（D-01 workspace manifest）在 `--force` 时被**覆盖并刷新 `created_at`**（F001-P2 §4.2）；**包内**的 `core/workspace/templates/manifest.json`（模板文件清单）**不**由 `--force` 触碰——它随 donkey 发行版发布，由"donkey 升级"更新（用于引入新模板）。

**幂等性 + 损坏恢复的工作流**（用户视角）：
1. 用户发现某模板文件损坏 → 用户 `rm` 该文件 → 用户跑 `donkey init` → 幂等补齐该文件
2. 用户希望全部模板重置 → 用户跑 `donkey init --force` → 清空 + 重生成全部模板
3. 用户希望整个 workspace 推倒重来 → 用户 `rm -rf workspace` → 跑 `donkey init`（不用 `--force`）

### §4.2 F001 Phase 划分

| Phase | 提示词文件 | 子段（exit code 范围） | 主要工作 | Error 类 |
|---|---|---|---|---|
| **F001-P1** | `feature001_phase001_cli_validation.md` | `1-2` | CLI 入口 + 路径 / 权限校验 + 创建 workspace 根目录（**不加载模板清单**——推迟到 P2） | `PathNotFoundError` / `PathPermissionError` |
| **F001-P2** | `feature001_phase002_template_skeleton.md` | `3` | 幂等生成模板骨架（补齐缺失 / `--force` 重置）+ 模板清单驱动（追加 43 条 → 累计 46 条） | `TemplateGenerationError` |
| **F001-P3** | `feature001_phase003_builtin_tools.md` | `4` | 幂等生成 3 个内置 `@tool` + **`tools/changes.py` 变更记录契约库（diff-ready）** + Skills example 三层（追加 8 条 → 累计 54 条） | `BuiltinToolGenerationError` |

### §4.3 F001-P1 = `cli_validation`（exit 1-2）

**入口条件（Entry Gate）**：无前置（仓库初始化即可启动；见 §12.2「准入条件」列）。

**本 Phase 交付物（由本 Phase 自建，不属入口条件）**：
- `donkey/core/` / `donkey/cli/` / `donkey/web/` / `donkey/gui/` 目录已创建；
- `donkey/core/exit_codes.py` 已实现 exit code 段位常量；
- `donkey/core/exceptions.py` 已定义基类 `DonkeyError` 与 F001 基类 `WorkspaceInitError`，并定义 2 个具体异常类（`PathNotFoundError` / `PathPermissionError`，对应 exit 1 / 2）；
- `core/workspace/templates/manifest.json`（模板清单）已定义——**P1 阶段仅 3 条 entry**（`instruction.md` / `providers/default.toml` / `mcp/mcp.json`）；清单**分阶段追加**（P1 3 → P2 +43 = 46 → P3 +8 = 54），保证每条 entry 都有对应源文件；
- `core/workspace/templates/{entry['path']}.txt`（模板源文件，P1 阶段至少含 `instruction.md.txt` / `providers/default.toml.txt` / `mcp/mcp.json.txt`）已就位。

**实现要点**：
- `core/api.py`：`init_workspace(path, name=None, force=False) -> InitResult` 函数签名稳定 + **P1 最小实现**（校验 + **创建 workspace 根目录**；**不**加载模板清单、**不**渲染模板内容——均属 P2 域）。
- `core/workspace/init.py`：核心逻辑骨架：
  - `check_path(path) -> Path` — 解析为绝对路径，验证父目录存在；失败抛 `PathNotFoundError`；
  - `check_permission(path) -> None` — 验证当前用户对 path 有写权限；失败抛 `PathPermissionError`；
  - `validate_init_request(path, name, force)` — 综合校验。
  - **本 Phase 不实现 `load_template_manifest`**——模板清单加载推迟到 F001-P2（其失败归 `TemplateGenerationError` exit 3），口径与 `harness/features/feature001_phase001_cli_validation.md` L181 / L244 一致。
  - **不**再检查 "workspace 已存在"——幂等设计下已存在不是错误（详见 §4.1.1）。
- `cli/cli_client.py`：argparse 入口，仅 `init` 子命令：
  - 位置参数 `<PATH>` 必填；
  - `--force` flag；
  - **v1 不提供 `--name`**——workspace 名称恒取 `path.basename()`（避免"路径说一套、名字说另一套"的身份混淆）。
- `cli` **不**直接 import `pathlib` 之外的 IO 库；所有 IO 通过 `core.api` 调用（**宪法 N-04 / N-05**）。

**异常退出码**（详见 §3.1 表）：
- exit 1 = `PathNotFoundError` —— PATH 父目录不存在 / 路径解析失败；
- exit 2 = `PathPermissionError` —— PATH 权限不足。

**退出条件（Exit Gate）**：
- `verify_phase_f001_p1.py` 通过以下断言：
  1. `donkey init /tmp/empty-ws` → exit 0（场景 1：全新创建）；
  2. `donkey init /nonexistent/parent/ws` → exit 1（场景 2）；
  3. `donkey init <只读父目录>/ws`（`chmod 0o555` 模拟无写位，**root 下同样被拒**，见 `research.md` R-04）→ exit 2（场景 3）；
  4. `donkey init /tmp/ws`（已存在 workspace，无 `--force`）→ exit 0（场景 4：幂等，不报错）；
  5. `donkey init /tmp/ws --force`（已存在 workspace，传 `--force`）→ exit 0（场景 5：强制标志；**P1 仅记录不重置**，重置属 F001-P2）；
  6. **不**检查模板渲染 / 目录内容（属于 P2）；P1 只创建**空目录**（三个计数恒 0，不生成任何文件）（场景 6）；
  7. 名称派生：workspace 名称 = 路径末段（v1 **无** `--name`），结果摘要回显绝对路径与名称；误传命名类参数 → exit 1（场景 7）。

**绝对不做**：
- 不生成 `tools/` / `skills/` 等子目录内容（推迟到 P2 / P3）；
- **不**做"workspace 已存在则报错"的判断（幂等设计，已存在不是错误）；
- 不挂载任何中间件（属于 F004 run 域）；
- 不解析 `providers/` 下的任何 TOML（属于 F002 load 域）；
- **不**交付 `.github/workflows/ci.yml`（C1 工作流文件 Deferred——属仓库级资产，非单 Phase 交付物；已按宪法 §6.3 登记临时例外 E-01，替代保障为 plan G5 记录的 CI 最小内容骨架 + 本地命令清单作为完成证据，最迟于 F001-P3 结束前交付）。
  > **E-01 范围扩展（2026-10-23，Maintainer 批准）**：原登记范围「仅 F001-P1」→ 扩展为「**仅 F001-P1 与 F001-P2**」（F001-P2 引入第一个运行期依赖与 14 个黑盒验收场景，测试面进一步扩大，CI 文件仍属仓库级资产）。本次扩展**不改变**过期时间（F001-P3 结束前）、**不改变**替代保障清单、**不新增**任何豁免条款。权威文本见宪法 §6.3 E-01。

---

### §4.4 F001-P2 = `template_skeleton`（exit 3）

**入口条件**：
- F001-P1 退出条件全部满足 + P1 抛出的 2 个异常类已通过单元测试；
- **本 Phase 新建** `core/workspace/sqlite3_templates.py`——3 个 schema builder（构造 `sessions.sqlite3` 的 SqliteSaver 表 + `sessions_metadata` 表 + 索引；`store.sqlite3` / `knowledge.sqlite3` 仅触发空文件创建，schema 推迟到 v3；schema 由 `langgraph-checkpoint-sqlite` 的 `SqliteSaver(conn).setup()`（**实例方法**）+ donkey 自管的 6 列 + 2 索引构成），并配单元测试覆盖"空目录首次构建" + "已存在 sqlite3 跳过" + "`--force` 重建" 三场景。**该模块是 P2 自身的交付物，不在 P2 的入口条件里**（见 F001-P2 §4.7.6 / `harness/report/sessions_sqlite表结构一览.md` §2.3）。

**实现要点**：
- **5 大必填目录**（**宪法 §2.6**）：`tools/`、`mcp/`、`skills/`、`memory/`、**`providers/`**。
- **必填文件**（**立项书 §4.6.1**）：
  - `instruction.md`（系统提示词模板，含占位符说明）；
  - **`providers/` 目录**（per-provider schema + **一 provider 一文件**：文件名 stem == provider_id，小写 kebab-case）：
    - `providers/default.toml`（必填，保留名）：`default_provider` + `default_model` 两个全局字段；`default_model` 必须存在于 default provider 文件的 `[models]` 表（跨文件校验 → exit 11）；
    - `providers/<provider_id>.toml`（按需创建，init 阶段生成 26 个 stub 全部 `enabled = false`）：含 **`enabled` 开关**（缺省 `true`；`false` = 完全惰性：不校验字段 / 不要求 `api_key` / 不参与连通性检查）+ `api_key`（TOML 明文，不读 env var）+ `api_host`（**23 个 provider 选填**，Ollama 允许 `api_host = "default"`；`openai-compatible` / `meta` / `databricks` **必填**——见调研 §10.1 / §16 Q-3）+ `models` 子表（`[models.model_id]`）+ 11 个通用字段（enabled / api_key / api_host / models / timeout / max_retries / temperature / max_tokens / top_p / stop / stream）；详见 `harness/report/大模型toml参数设计.md §7` / §8.3 与 立项书 §4.6.2）。
    - `providers/bedrock.toml` 特殊：4 个独立 `aws_*` 字段（不用 `api_key`）；`baidu` / `iflytek` / `sensetime` 在 v1 报错（exit 11），因为它们是 v2+ 自研候选（调研报告 §3.5）；任何不在调研报告 §3.1 白名单 / 调研报告 §3.5 v2+ 候选的 provider（含此前可能列入暂不支持清单的 provider）统一走 `ProviderTomlScopeError`（exit 11），错误信息引导"改用 `openai-compatible` 或提 issue 申请调研报告 §3.1 升级评估"；详见调研报告 §3.0 Provider 治理原则。
  - `mcp/mcp.json`（`{"mcpServers": {}}` 空对象模板）；
  - `skills/example/SKILL.md`（仅含 Level 1 frontmatter 占位 `name` + `description`）。
- **支撑文件**：
  - 根 `README.md`（workspace 总览模板）；
  - `tools/README.md`（工具开发规范说明）；
  - `mcp/README.md`、`skills/README.md`、`memory/README.md`（**memory/README.md 模板正文见 F001-P2 §4.7.5** —— 用于向用户解释 sqlite3 是 init 阶段预创建的模板 + `--force` 会清空 + 备份要点，避免用户误删/误重置历史 session）；
  - `.gitignore`（忽略 `memory/*.sqlite3`、`__pycache__/`）——**`memory/*.sqlite3` 已含在 .gitignore 模板中**。

  > `memory/README.md` 模板正文（`core/workspace/templates/memory/README.md.txt`）见 **F001-P2 §4.7.5**（唯一权威源，避免两处漂移）。
- `core/workspace/templates/`：模板源文件（`.md.txt` / `.toml.txt` / `.json.txt`）；
- `core/workspace/templates/manifest.json`：模板清单（列出 donkey 自动生成的所有文件路径；详见 §4.1.1）——含**文本模板**（`instruction.md` / `providers/*.toml` / `mcp/mcp.json` / `tools/*.py` 等）与 **sqlite3 模板**（`memory/sessions.sqlite3` / `memory/store.sqlite3` / `memory/knowledge.sqlite3`，由 `core/workspace/sqlite3_templates.py` 的 schema builder 在 init 阶段程序化构造；**不**在包内携带二进制 sqlite3 文件，避免 schema 漂移）；
- `core/workspace/init.py`：新增 `render_templates(path, name, force)` 函数：
  - 遍历 `manifest.json` 中的每个模板路径（含文本模板 + sqlite3 模板）；
  - **不传 `force`**：仅当文件不存在时创建；已存在跳过；
  - **传 `force`**：先 `delete` 再 `create`；sqlite3 模板调用 schema builder 重建 SqliteSaver 表 / `sessions_metadata` 表 / SqliteStore 表 / knowledge 空文件；
  - 用户内容（非模板清单内）**不动**（包括用户自定义 `tools/my_tool.py` / 用户自建 `media/` 目录等）；
  - 任一步骤失败 → 抛 `TemplateGenerationError` 或 `BuiltinToolGenerationError`（按 §3.1 表）。
- `core/workspace/manifest.py`：workspace manifest 写入与解析（**D-01**：manifest 字段最少化，可仅含 `version` + `created_at` + `donkey_version`）：
  - **不传 `force`**：若 manifest 已存在则跳过（保留原 `created_at`）；
  - **传 `force`**：刷新 `created_at` 为当前时间；
  - 字段 `donkey_version` 记录生成本次 manifest 的 donkey 版本号（用于未来迁移提示）。
- 名称注入：workspace 名称（= 路径末段 `path.basename()`）注入到 `providers/default.toml` 注释、`README.md` 标题、manifest。

**异常退出码**（详见 §3.1 表）：
- exit 3 = `TemplateGenerationError` —— 模板骨架生成失败（合并四项：源缺失 + 渲染失败 + 文件写入失败 + sqlite3 schema 构造失败；用户修复动作相同：重装 donkey / 检查权限 / 重试 init）。

**退出条件**：
- `verify_phase_f001_p2.py` 通过以下断言：
  1. **场景 1**：`donkey init /tmp/empty-ws` → exit 0，目录树与立项书 §4.6.1 **逐项一致**；
  2. 生成的 `providers/default.toml` + 26 个 provider stub 用 `tomllib` 解析无异常；
  3. 生成的 `mcp/mcp.json` 用 `json.loads` 解析无异常；
  4. 生成的 `skills/example/SKILL.md` frontmatter 用 `python-frontmatter` 解析，含 `name` + `description`；
  5. 名称注入：workspace 路径末段为 `foo` 时，README 标题与 `providers/default.toml` 注释含 "foo"；
  6. **场景 2 幂等**：`donkey init /tmp/ws`（已存在）→ exit 0；用户手动编辑过的 `instruction.md` 内容**不变**（mtime 不变）；
  7. **场景 2 子操作**（用户损坏恢复）：`rm /tmp/ws/instruction.md` 后 `donkey init /tmp/ws` → exit 0；该文件被补齐；
  8. **场景 3 模板重置**：`donkey init /tmp/ws --force` → exit 0；用户编辑过的 `instruction.md` 也被覆盖（恢复出厂内容）；用户自建的 `media/` 目录**不动**；
  9. **场景 3 完整验证**：第 8 步后用户 `media/` 仍在 + `donkey.log` 仍在（如果有）；
  10. **场景 4**：手动 `rm -rf /tmp/ws` 后 `donkey init /tmp/ws` → exit 0；同场景 1；
  11. 缺失 `templates/instruction.md.txt` 时手动删除 → `donkey init /tmp/ws --force` → exit 3；
  12. **不**要求 `tools/filesystem.py` 等内置 `@tool` 文件存在（属于 P3）；
  13. **不**要求生成的 workspace 能通过 F002 静态检查（属于 F002 域）；
  14. **memory/ 模板边界**（与 §4.1.1 设计意图一致）：`donkey init /tmp/empty-ws` 后 `memory/sessions.sqlite3` / `memory/store.sqlite3` / `memory/knowledge.sqlite3` **三个文件全部存在**（init 阶段预创建，schema-built 空 sqlite3）；`donkey init /tmp/ws --force` 后 mtime **变更**（重建 sqlite3 + 新建 schema），`memory/README.md` 内容被恢复出厂内容——验证 `--force` 等于"恢复出厂设置"，会清空全部 sqlite3；
  15. `memory/` 目录 + `memory/README.md` + `memory/sessions.sqlite3` + `memory/store.sqlite3` + `memory/knowledge.sqlite3` 一定**全部存在**；init 阶段仅 `sessions.sqlite3` 含 schema（`PRAGMA table_info(checkpoints)` + `PRAGMA table_info(sessions_metadata)` 均有返回 + 2 索引；`SELECT COUNT(*) FROM sessions_metadata` 返回 0），`store.sqlite3` / `knowledge.sqlite3` 是空文件（`PRAGMA table_info` 返回空集——schema 推迟 v3）；

**绝对不做**：
- 不生成 3 个内置 `@tool` 文件（推迟到 P3）；
- 不生成 Skills example 的 Level 2/3 内容（推迟到 P3）；
- **不**做"init 后跑 F002 静态检查"——文件格式合法性属于 F002 静态检查范畴（exit 11-14），F001 不重复。

**落地状态（2026-10-23 · F001-P2 已交付）**：

| 项 | 落点 | 状态 |
|---|---|---|
| 运行期依赖 | `pyproject.toml` → `dependencies = ["langgraph-checkpoint-sqlite>=3.1,<4"]`（**恰为 1 个**直接运行期依赖） | ✅ |
| 错误类 | `core/exceptions.py` → `TemplateGenerationError(WorkspaceInitError)` + `_NEXT_STEP_TEMPLATE` | ✅ |
| 退出码 | `core/exit_codes.py` → `EXIT_CODE_TEMPLATE_GENERATION = 3` **本阶段启用**；`4`（P3）与 `5-10` 仍不触发 | ✅ |
| 客户端映射 | `cli/cli_client.py` → `_EXCEPTION_TO_EXIT_CODE` 追加 `TemplateGenerationError: 3`（**客户端改动共 3 项**：映射 1 行 + 强制清空提示 1 行 + `--help` 文案同步） | ✅ |
| 模板清单加载 | `core/workspace/init.py` → `load_template_manifest`（**未去重**的原始条目列表；schema 校验 V1~V6） | ✅ |
| 渲染内核 | `core/workspace/init.py` → `render_templates`（按**唯一路径**去重、后者胜出；幂等三态；父目录先建 → 顺序无关） | ✅ |
| 内部流水线 | `core/workspace/init.py` → `init_workspace_inner`（五步：校验 → 加载清单 → 建根目录 → 渲染 → 写工作区清单；步骤 ⑤ 失败**不回滚**） | ✅ |
| 工作区清单 | `core/workspace/manifest.py`（**新增模块**）→ `write` / `read` / `ensure`（字段恰 4 项；`ensure` 与 `write` 严格等价） | ✅ |
| sqlite3 构造器 | `core/workspace/sqlite3_templates.py`（**新增模块**）→ `build_sessions_sqlite` / `build_store_sqlite` / `build_knowledge_sqlite` | ✅ |
| 模板资产 | `core/workspace/templates/` → **46 条清单**（P1 的 3 条 + P2 追加 43 条）+ **37 个文本模板源**（含隐藏名 `.gitignore.txt`）；`package-data` 显式列入 `.gitignore.txt` → wheel 内齐备 | ✅ |
| 供应商配置 | 26 份 provider stub（**脚本抽取**调研 §8.3.3~§8.3.28，逐字保留注释）+ `providers/README.md`（26 家索引）+ `providers/default.toml`（两字段出厂为空串） | ✅ |
| 单元测试 | `tests/unit/test_template_skeleton.py`（**72** 个用例，覆盖 FR-055 的 16 类 + 边界护栏 + 内容级断言 + **spec Edge Cases 段的全部 MUST 边界**）+ `tests/unit/test_cli_client.py`（新增 1 个强制清空提示行用例） | ✅ |
| 黑盒验收 | `tests/e2e/phase/verify_phase_f001_p2.py`（**14** 个 `test_scenario_*` 场景断言，全绿） | ✅ |
| 静态检查 | `ruff check donkey/ tests/` + `mypy donkey/ tests/` → 零 error 零 warning | ✅ |
| 覆盖率 | `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` → `donkey.core` 行覆盖率 **92%** | ✅ |

**本阶段实际使用的退出码**（SC-010）：`{0, 1, 2, 3}` —— `1` = 输入 / 路径 / 参数用法不合法；`2` = 权限不足（前置校验阶段 + 工作区根目录创建阶段）；`3` = 模板骨架生成失败（渲染阶段 + 工作区清单写入阶段）。

---

### §4.5 F001-P3 = `builtin_tools`（exit 4）

**入口条件**：F001-P2 退出条件全部满足 + P2 抛出的 `TemplateGenerationError` 已通过单元测试。

**实现要点**：
- **`tools/__init__.py`**：空文件或最小初始化（保证 `from tools import filesystem` 可用）。
- **`tools/changes.py`**：**变更记录契约库**（**0 个 `@tool`**，纯 stdlib）——原子写 + sha256 + unified diff + 乐观锁的**唯一产地**；所有改文件的工具（含用户自写工具）都 import 它，产出**统一 schema** 的"变更记录"（`CHANGE_RECORD_VERSION = 1`）。**这是 v4"diff 展示"（立项书 §1.5.3）的接入面**：材料层交出变更原材料，引擎层负责渲染 diff / 人工确认 / 回滚（v1 不承诺 diff 审阅，AC-5）。详见 F001-P3 §2.9。
- **`tools/filesystem.py`**：7 个 `@tool`（**立项书 §4.6.1 + 调研 §三**）：
  - `read_file(path, start_line=1, num_lines=None) -> str` / `write_file(path, content, dry_run=False, include_previous=False, expected_hash=None)` / `copy_file(src, dst)` / `move_file(src, dst)` / `delete_file(path, include_previous=False)` / `list_dir(path, include_hidden=True) -> list[str]` / `stat(path, with_hash=False) -> dict`；
  - 实现：`pathlib` / `shutil`；路径白名单由用户自管（donkey 不强制）；
  - **写类工具一律返回 `change` 变更记录**（`action` / `previous_hash` / `new_hash` / `unified_diff` / `applied`）+ **原子写**（同目录临时文件 + `os.replace`）；新增参数**全部可选且带默认值**（旧调用方式逐字节不变 = 向后兼容）；
  - **不**含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管，**宪法 §2.5**）。
- **`tools/commandline.py`**：1 个 `@tool`：
  - `run_shell(command, timeout=60, cwd=None) -> str`（`cwd` 默认 = workspace 根，不依赖进程 cwd）；
  - 实现：`subprocess.run([...], shell=False, timeout=...)`，每次新进程，**不**走持久 shell（避免 HITL 冲突）。
- **`tools/webfetch.py`**：1 个 `@tool`：
  - `fetch_url(url, method="GET", headers=None, timeout=30) -> str`；
  - 实现：`httpx` / `requests` 同步 + 显式 timeout；不持久化 cookies。
- **`tools/README.md`**：工具开发规范（命名、参数、错误处理、timeout）。
- **`skills/example/SKILL.md`**：完整三层示例（**宪法 §2.4**）：
  - Level 1：frontmatter `name` + `description`；
  - Level 2：Markdown 主体；
  - Level 3 目录占位：`skills/example/reference/` / `scripts/` / `templates/` 各含 1 个示例文件。
- `core/workspace/templates/manifest.json` **追加**：把上述 8 条新 entry（tools/__init__.py + **`tools/changes.py`（变更记录契约库）** + 3 个内置 tool + 3 个 Skills Level 3 示例）加入模板清单（P2 已有 instruction.md / `providers/` 等基础模板 + sqlite3 模板；P3 追加 builtin 模板条目）；
- `core/workspace/init.py`：**不重复实现** `render_templates`——P2 实现的 `render_templates` 已遍历 manifest.json **全量条目**实现幂等 + `--force`；本 Phase 仅**追加** manifest 条目，运行期 `donkey init` 调用 `render_templates` 时会自动覆盖本 Phase 加入的 builtin 工具条目。具体行为：
  - 不传 `force`：仅当文件不存在时创建；已存在跳过（用户自定义 `tools/*.py` 不在清单内，不动）；
  - 传 `force`：先 `delete` 再 `create`；sqlite3 模板也会被重建（见 §4.4 P2 实现要点 + §4.1.1 "memory/ 模板边界"）。
- **端到端集成预演**（**注意：仅做"import 路径 + 函数签名"测试，不做 F002 静态格式检查**）：`tests/integration/test_init_to_load.py` 验证 init 完的 workspace 能被 Python import 路径正确发现 `@tool` 函数。

**异常退出码**（详见 §3.1 表）：
- exit 4 = `BuiltinToolGenerationError` —— 内置 `@tool` + Skills example 生成失败（合并三项：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、集成预演 import 失败）。

**退出条件**：
- `verify_phase_f001_p3.py` 通过以下断言：
  1. 生成的 workspace 包含 `tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py` / `tools/__init__.py` / `tools/README.md`；
  2. 三个 builtin tool 文件均可 import，每个 `@tool` 函数有完整 docstring；
  3. `commandline.py` 执行 `run_shell("echo hello")` 返回 **JSON 字符串**（`{"stdout": "hello\n", "stderr": "", "returncode": 0, "timed_out": false}`）——`stdout` 字段含 `"hello\n"`（集成测试）；
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
- 不创建 sqlite3 数据库文件——`memory/*.sqlite3` 由 F001-P2 阶段作为模板预创建（含 schema builder），本 Phase 入口条件已假定 sqlite3 模板已就绪；不重复；
- **不**做"init 后跑 F002 静态检查"——F002 静态格式检查属 F002 域；
- 不引入 `ShellToolMiddleware` / `FilesystemMiddleware` 等任何 LangChain 中间件（属于 F004 run 域；宪法 §2.7.2 禁用清单 / §2.7.1 录用清单）。

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

| Phase | 提示词文件 | 子段（exit code 范围） | 主要工作 | Error 类 |
|---|---|---|---|---|
| **F002-P1** | `feature002_phase001_static_format.md` | `11-13` | 静态 1-3：`providers/` 目录（伞形 `ProviderTomlLoadError`）/ `mcp.json`（`McpJsonSyntaxError`）/ `SKILL.md`（`SkillFrontmatterError`）| `ProviderTomlLoadError`（含子类）/ `McpJsonSyntaxError` / `SkillFrontmatterError` |
| **F002-P2** | `feature002_phase002_static_dynamic_basic.md` | `14-16` | 静态 4（目录完整性）+ 动态 1-2（连通性 + sqlite） | `InstructionMissingError` / `ProviderConnectivityError` / `SqliteSchemaError` |
| **F002-P3** | `feature002_phase003_dynamic_runtime.md` | `17-20`（已用 17-19 + 预留 20） | 动态 3-5（tools / skills / mcp loader） | `ToolLoadError` / `SkillLoadError` / `McpServerError` |

### §5.3 F002-P1 = `static_format`

- **核心逻辑**：用 `tomllib` / `json` / `python-frontmatter` 解析 workspace 内的静态文件，第一个语法错误立即抛出对应 Error。
- **退出条件**：人造损坏 workspace（手动改坏 TOML/JSON/YAML）→ 对应 exit code 触发；正常 init 完的 workspace → exit 0。

### §5.4 F002-P2 = `static_dynamic_basic`

- **核心逻辑**：检查 `instruction.md` 存在性与目录结构完整性；用 `init_chat_model` + ping 验证模型连通性；用 `sqlite3` + `PRAGMA` 验证 sqlite schema（**5 项断言**：`checkpoints` 表 / `writes` 表 / `sessions_metadata` 表 6 字段 / 2 索引名 / `integrity_check`——口径以 `sessions_sqlite表结构一览.md` §7 为准）。
- **退出条件**：删除 `instruction.md` → exit 14；损坏 `sessions.sqlite3` → exit 16；**模型连通性失败 → exit 15**（仅限"凭据有效但 ping 超时 / 401 鉴权失败"）。
  > **归属边界**：`providers/` 的**字段级**错误（`api_host` 非 URL 格式 / Bedrock 禁 host 覆盖 / 云端 provider 空 `api_key` / `api_key` 类型错 / scope 越界 / 零 enabled provider）**全部属 F002-P1 静态检查 → exit 11 伞形**（子类见 §3.2.1；调研 §7.3 / §9.1.1 / §9.2），**不走 exit 15**。特别地：云端 provider 的**空 `api_key` 在构造期**即被拒（`Missing credentials`）→ exit 11；出厂 stub 的 `api_key = ""` 因 `enabled = false` 完全惰性、不触发任何检查（**`REPLACE_ME` 占位符已于 v1 废除**，见立项书 §3.2.3 ③）。

### §5.5 F002-P3 = `dynamic_runtime`

- **核心逻辑**：扫描 `tools/*.py` 跑 `importlib` 验证 `@tool` 可加载；跑自研 Skills loader 验证 SKILL.md 可加载；用 `MCPAdapter` 拉起 server 验证可达。
- **退出条件**：故意写错的 `tools/*.py`（语法错）→ exit 17；损坏的 SKILL.md → exit 18；填错的 mcp server URL → exit 19。

---

## §6 F003 `donkey session` —— 详细设计

### §6.1 F003 整体范围

- **核心库 API**：`list_sessions / new_session / remove_session / import_session`
- **段位**：exit `21-30`（4 Phase，7 错误码 = 21-27，3 个 v1 留接口位 = 28-30 import，见 §3.3）
- **切分规则**：规则 A（按二级命令切）—— 每个二级命令 = 一个 Phase
- **关键约束**（**宪法 N-09 / N-10**）：
  - 对外标识是**标题**，thread_id 仅作内部引用；
  - `session new` 默认标题"无标题会话"；给了首轮 prompt 时**必须**在 `core.api.new_session` 内部由 LLM 总结 ≤ 20 字标题并写回 sqlite3；**严禁**实现为 `before_agent` 中间件（不新增 LangGraph 节点、不触发 `x+1`）。

### §6.2 F003 Phase 划分

| Phase | 二级命令 | 文件名提示词 | 子段（exit code 范围） | 主要工作 | Error 类 |
|---|---|---|---|---|---|
| **F003-P1** | `list` | `feature003_phase001_list.md` | `21-22` | 扫描 `sessions_metadata` 表列出所有会话（按 `updated_at` DESC；标题不重复）；sqlite 锁等待 ≤ 1s（超时报 22） | `SessionListSqliteError` / `SessionListLockError` |
| **F003-P2** | `new` | `feature003_phase002_new.md` | `23-25` | 新建会话：分配 thread_id → 写 SqliteSaver initial checkpoint + `INSERT INTO sessions_metadata`；可选 `--first-prompt` 触发 LLM 总结标题（**不**进 Agent Loop 图, ≤ 5s 超时 → **回退为首轮 prompt 前 20 字**，绝不回退成"无标题会话"；session 创建始终成功，exit 0） | `SessionNewSqliteError` / `SessionNewLockError` / `SessionNewCheckpointError` |
| **F003-P3** | `remove` | `feature003_phase003_remove.md` | `26-27` | 按标题定位 → 物理删除 SqliteSaver 该 `thread_id` 全部 checkpoint + `DELETE FROM sessions_metadata WHERE thread_id=?` | `SessionRemoveSqliteError` / `SessionNotFoundError` |
| **F003-P4** | `import` | `feature003_phase004_import.md` | `28-30` | 从外部 sqlite 文件导入历史会话（**v1 留接口, v1.x 落地**, 立项书 §5.5.4.4） | `SessionImportFormatError` / `SessionImportSqliteError` / `(v1 留接口位)` |

### §6.3 关键 Phase 说明

**F003-P2 = `new`（最复杂）**：
- `core.api.new_session(path, first_prompt=None, title=None) -> SessionMeta` 内部流程：
  1. 分配 thread_id（UUID）；**`sessions_metadata` 表 + 索引 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 在 `donkey init` 阶段已由 schema builder 预创建**（见 §4.1.1 "memory/ 模板边界" + §4.4 P2）；**此处不重复 CREATE**——若 schema 不存在说明 workspace 未 init / `--force` 后被外部破坏，**必须**报错交 `SessionNewSqliteError`（exit 23）而不是再次 `CREATE TABLE IF NOT EXISTS`（那会掩盖 init 缺失问题）；
  2. 决定标题（**N-10**，**先定标题再落库**）：用户显式传 `title` → 用 title（≤ 20 字截断）；用户传 `first_prompt` → 调 `init_chat_model` 总结 ≤ 20 字，**失败 / 超时 / 空返回 → 回退为首轮 prompt 的前 20 字**（**绝不**回退成"无标题会话"——不允许出现"Agent Loop 已启动但标题仍是占位符"）；都不传 → 默认"无标题会话"；
  3. `INSERT INTO sessions_metadata(thread_id, title, created_at, updated_at, donkey_version, first_prompt) VALUES (...)`；同时 SqliteSaver 写 initial checkpoint（thread_id 已注册）——该步失败 → `SessionNewCheckpointError`（exit 25）；
  4. 标题总结失败 / 超时**不**抛异常 → **不**影响 INSERT 落库——session 创建始终成功（exit 0）。
- 标题总结失败**不**抛异常 → session 创建本身始终成功（exit 0）；失败时在三端日志/UI 上提示"标题由首轮 prompt 截取生成"。

---

## §7 F004 `donkey run` —— 详细设计（v1 主战场）

### §7.1 F004 整体范围

- **核心库 API**：`core.api.run_session(path, session_id)`
- **段位**：exit `31-100`（7 Phase，30 错误码，40 预留——大段预留给中间件扩展与 v2/v3 接入）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：
  - **v1 主图节点数 = 10**（立项书 §4.4.2）：4 基线 + 6 中间件节点；
  - **v1 中间件录用 10 项**（立项书 §1.5.4 + 宪法 §2.7.1）；
  - **v1 不挂 Store**（SqliteStore 留给 v3），v1/v2 用 `InMemoryStore` 临时顶替；
  - **版本号 `x+1` 触发条件**见立项书 §1.5.2 边界细则表。

### §7.2 F004 7 子段位 Phase 划分

| Phase | 提示词文件 | 子段（exit code 范围） | 失败域 | 主要工作 | Error 类 |
|---|---|---|---|---|---|
| **F004-P1** | `feature004_phase001_tools.md` | 段位 `31-40`（已用 31-34 + 预留 35-40） | tools 调用 | 加载 `tools/*.py` → `@tool` 自动发现；执行失败处理 | `ToolImportError` / `ToolExecutionError` / `ToolTimeoutError` / `ToolArgumentError` |
| **F004-P2** | `feature004_phase002_skills.md` | 段位 `41-50`（已用 41-43 + 预留 44-50） | Skills 加载 | 扫描 `skills/*/SKILL.md` → 自研渐进披露 loader | `SkillFrontmatterParseError` / `SkillToolRegisterError` / `SkillLoadBodyError` |
| **F004-P3** | `feature004_phase003_mcp.md` | 段位 `51-60`（已用 51-53 + 预留 54-60） | MCP server | 加载 `mcp/mcp.json` → `MCPAdapter` | `McpConfigError` / `McpServerConnectError` / `McpToolCallError` |
| **F004-P4** | `feature004_phase004_saver.md` | 段位 `61-70`（已用 61-63 + 预留 64-70） | 短期记忆（Saver） | 挂 `SqliteSaver(memory/sessions.sqlite3)` | `SaverOpenError` / `SaverWriteError` / `SaverReadError` |
| **F004-P5** | `feature004_phase005_store.md` | 段位 `71-80`（**71-73 = v3 占位，v1 不实装** + 预留 74-80） | 长期记忆（Store） | v1/v2 用 `InMemoryStore`（不落盘、极少触发）；v3 自研 SqliteStore 才启用这 3 码 | `StoreOpenError` / `StoreWriteError` / `StoreReadError`（**v3**） |
| **F004-P6** | `feature004_phase006_middleware.md` | 段位 `81-90`（10 码全部实装，无预留） | 中间件 | 10 项 v1 中间件挂载 + 错误处理 | `ToolErrorMiddlewareError` / `ToolRetryMiddlewareError` / `ModelRetryMiddlewareError` / `SummarizationMiddlewareError` / `ModelCallLimitMiddlewareError` / `PIIMiddlewareError` / `TodoListMiddlewareError` / `LLMToolSelectorMiddlewareError` / `ContextEditingMiddlewareError` / `ModelAuthenticationError` |
| **F004-P7** | `feature004_phase007_agent_loop.md` | 段位 `91-100`（已用 91-94 + 预留 95-100） | Agent Loop | LangGraph 主图编译 + 状态机 | `GraphCompileError` / `StateSchemaError` / `NodeTypeError` / `EdgeConnectError` |

---

## §8 F005 `donkey web` —— 详细设计

### §8.1 F005 整体范围

- **核心库 API**：前端复用 F001-F004 库 API，无独立后端 API
- **段位**：exit `101-170`（7 Phase，22 错误码，48 预留）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：Web **不**直接 import `langchain` / `langgraph` / `sqlite3`（**宪法 N-04**）；全部走 `donkey.core.api`。

### §8.2 F005 7 子段位 Phase 划分

| Phase | 提示词文件 | 子段（exit code 范围） | 失败域 | 主要工作 |
|---|---|---|---|---|
| **F005-P1** | `feature005_phase001_event_stream.md` | 段位 `101-110`（已用 101-104 + 预留 105-110） | 事件流 | WebSocket / SSE / 序列化 / 断流重连 |
| **F005-P2** | `feature005_phase002_ipc_bridge.md` | 段位 `111-120`（已用 111-113 + 预留 114-120） | IPC 桥接 | CLI ↔ Web 进程间调用 / 超时 / 序列化 |
| **F005-P3** | `feature005_phase003_render.md` | 段位 `121-130`（已用 121-124 + 预留 125-130） | 渲染 | 组件异常 / SSR-CSR 失配 / Markdown + 代码高亮 |
| **F005-P4** | `feature005_phase004_state.md` | 段位 `131-140`（已用 131-133 + 预留 134-140） | 状态管理 | session / store 同步 / 回滚 |
| **F005-P5** | `feature005_phase005_auth.md` | 段位 `141-150`（已用 141-143 + 预留 144-150） | 鉴权 / CORS / CSP | 跨域 / cookie / token |
| **F005-P6** | `feature005_phase006_resource.md` | 段位 `151-160`（已用 151-153 + 预留 154-160） | 资源加载 | chunk 404 / CDN / WebAssembly |
| **F005-P7** | `feature005_phase007_misc.md` | 段位 `161-170`（已用 161-162 + 预留 163-170） | 其它 | 浏览器兼容性 / 用户输入校验 |

---

## §9 F006 `donkey gui` —— 详细设计

### §9.1 F006 整体范围

- **核心库 API**：前端复用 F001-F004 库 API，无独立后端 API
- **段位**：exit `171-200`（3 Phase，11 错误码，19 预留）
- **切分规则**：规则 B（按退出码段位切）
- **关键约束**：
  - **GUI = Electron 包壳**：100% 复用 Web 渲染层（**立项书 §5.5.6**）；
  - **最薄壳**：工作量约 40 人时；
  - 三端打包脚本（macOS dmg / Windows nsis / Linux AppImage）属 F006-P3 范围。

### §9.2 F006 3 子段位 Phase 划分

| Phase | 提示词文件 | 子段（exit code 范围） | 失败域 | 主要工作 |
|---|---|---|---|---|
| **F006-P1** | `feature006_phase001_main_process.md` | 段位 `171-180`（已用 171-173 + 预留 174-180） | Electron 主进程 | app 生命周期 / 菜单 / 托盘 |
| **F006-P2** | `feature006_phase002_window.md` | 段位 `181-190`（已用 181-184 + 预留 185-190） | 窗口 | 创建 / 恢复 / 聚焦 / 多窗口 |
| **F006-P3** | `feature006_phase003_native_glue.md` | 段位 `191-200`（已用 191-194 + 预留 195-200） | 原生胶水 | 文件对话框 / 通知 / 剪贴板 / 系统 API |

---

## §10 开发顺序与依赖关系

### §10.1 关键路径（串行）

```
F001 → F002 → F003 → F004 → F005 → F006 → 三套官方模板 → Release v1.0.0
```

每个 Feature 内部 Phase 严格串行；跨 Feature 的推进关系以 §12.2 准入条件链为准（详见 §10.2）。

### §10.2 跨 Feature 推进策略（以 §12.2 准入条件链为唯一依据）

**门控关系（来自 §12.2「准入条件」列，不可自相矛盾）**：

```
F001-P1 → F001-P2 → F001-P3
       → F002-P1 → F002-P2 → F002-P3
       → F003-P1 → … → F003-P4
       → F004-P1 → … → F004-P7
       → F005-P1 → … → F005-P7
       → F006-P1 → … → F006-P3

规则：同 Feature 内 Phase 串行；每个 Feature 的 P1 准入 = 上一个 Feature 全部 Phase 退出
```

**结论（按上表逐条读出来的真实约束）**：

| # | 结论 | 依据 |
|---|---|---|
| 1 | **Feature 内部 Phase 严格串行** | 宪法 §4.3 + §12.2 准入链（F00N-P2 准入 = F00N-P1 退出，依此类推） |
| 2 | **Feature 之间是门控串行**——F00(N+1) 的 P1 准入 = F00N **全部** Phase 退出 | §12.2 准入条件列（F002-P1 = F001 3 Phase 全退出；F003-P1 = F002 3 Phase 全退出；…） |
| 3 | 因此 §10.1 的关键路径 `F001 → F002 → … → F006` 就是**唯一无冲突的推进顺序**；**同一时刻不存在"两个 Feature 的 Phase 同时在写 `core/`"的情况** | 结论 1 + 2 |
| 4 | **真正可并行的只有横切任务**：CLI 渐进补齐（贯穿 F001–F004）、文档 / fork 指南（贯穿全程）、三套官方模板（v1 收尾） | §10.3 + 立项书 §5.4 甘特图 |
| 5 | 宪法 §4.3 的"同一时段并行多个 Feature 的同 Phase 任务"是**方法层面允许**，但按 §12.2 的准入链，v1 baseline 下**没有一对 Feature 满足并行准入**——若 Maintainer 要并行，必须**显式放宽某个 Phase 的准入条件**并写进该 Phase 的提示词文件（不自动推断） | 宪法 §4.3 + §12.2 |

> **⚠️ 口径澄清（避免把 §10.2 读成"可以随便并行"）**：本节表格是**门控关系图**，不是"时段 × 可并行任务"的排期表。按 §12.2 准入链，v1 baseline 的 27 个 Phase 实际是**串行**推进的（单人 + Speckit 辅助下这正是 §5.4 甘特图 T0+47w 的由来）；旧版表格里"F002-P1 + F001-P1 可并行""F004-P1~P7 可并行"等说法与准入链冲突，已删除。

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

> 三套模板**不承诺**提供 diff 审阅（**宪法 §2.1 结论 3 / 立项书 AC-5**）；如需 diff，走 fork 路线。

---

## §11 exit code 段位速查表（基于 §3.1~§3.6 实际清点）

> **清点源**：本表数据 = §3.1~§3.6 各 Feature 段位内 Error 分配的清点求和；段位边界与冗余性原则仍以立项书 §5.5.3 / 宪法 §4.4 为权威。
>
> **列含义**：
> - **总码值**：段位大小（OK 段位为 1）；
> - **v1 实装**：v1.0.0 发布时已绑定 Error class 的码数；
> - **v1 留接口位**：段位内已 allocate 但 v1.x 才落地的码位（如 F003-P4 = import 占 28-30）；
> - **预留码**：段位内留给 v1.x 试运行期新发现错误的码位。

| 段位 | 归属 | 总码值 | v1 实装 | v1 留接口位 | 预留码 | Phase 数 |
|---|---|---|---|---|---|---|
| `0` | 全子命令 | 1 | 1（OK）| 0 | 0 | — |
| `1-10` | F001 init | 10 | 4（1-4 连号）| 0 | 6（5-10）| 3 |
| `11-20` | F002 load | 10 | 9（11-19）| 0 | 1（20）| 3 |
| `21-30` | F003 session | 10 | 7（21-27）| 3（28-30 = import v1.x 落地，立项书 §5.5.4.4）| 0 | 4 |
| `31-100` | F004 run | 70 | 27 | 0 | 43 | 7 |
| `101-170` | F005 web | 70 | 22 | 0 | 48 | 7 |
| `171-200` | F006 gui | 30 | 11 | 0 | 19 | 3 |
| `201+` | v2/v3/v4 扩展 | 全部 | 0 | 0 | 全部 | — |
| **合计 v1.0.0 范围** | — | **201** | **81** | **3** | **117** | **27** |

**总分配**：81 个 v1 实装（含 OK 的 1 码 → 80 个 Error class 码）+ 3 个 v1 留接口位 + 117 个预留码 = **201 个码值**（立项书 §5.5.3 段位分配总表完整覆盖；与 §3.1~§3.6 加总一致）。

> **与宪法 §4.4「每段位预留 10 个码值」原则的偏离（有意为之，已核对）**：F001 预留 6（实装 1-4 连号）、F002 预留 1（实装 11-19，9 项检查已占满）、F003 预留 0（28-30 是 import 的 v1.x 留接口位，不是通用错误预留）——这三条是**实装密度高导致的自然结果**，不是漏分配；F004~F006 仍按每子段 10 码整段预留。

**段位内"未绑定 v1 实装 Error"比例**（v1 留接口位 + 预留码）/ 总码值：

- **F001**：6/10 = **60%**（init 是简单存活检查，4 个错误码已覆盖所有场景——实际使用 1-4 连号，5-10 预留）
- **F002**：1/10 = **10%**（静态 + 动态 9 项检查全覆盖，几乎没有冗余；实际使用 11-19，20 预留）
- **F003**：3/10 = **30%**（4 个二级命令中 3 个 v1 实装 = 7 个 Error class + import v1 留接口位 = 3 码；不预留段位内通用码位——立项书 §5.5.3 "本段位由 4 个二级命令均分 + 保留" 表述中"保留"实际指 28-30 = import v1.x 落地占位，并非通用错误预留）
- **F004**：43/70 ≈ **61%**（大 Feature + v3 接入预留 + 中间件扩展预留；**P5 段位 71-73 的 3 码（`StoreOpenError` / `StoreWriteError` / `StoreReadError`）是 v3 占位、v1 不实装**——v1/v2 用 `InMemoryStore` 不落盘不抛错，见立项书 §5.5.5；**注意：F004-P6 段位 81-90 的 10 码已全部实装（81-89 中间件错误 + 90 鉴权错误），本子段无预留**——新增中间件错误统一从 P7 预留 95-100 借位）
- **F005**：48/70 ≈ **69%**（前端领域未探索，重在预留）
- **F006**：19/30 ≈ **63%**（最薄壳，预留适度）

---

## §12 提示词文件落地约定（Phase ↔ 文件 1:1）

> **本节为 v1 启动期核心交付物**——README 的 3 个作用（§0 总览 + §3/§4-§9 设计 + §12 落地）以本节闭环。

### §12.1 命名规则（与 §1.2 配套）

格式：

```
featurexxx_phasexxx_<phase_name>.md
```

- 第一个 `xxx`：3 位数字，左侧补 0，与 F 编号一致（`001` = F001，`002` = F002，…）；
- 第二个 `xxx`：3 位数字，左侧补 0，与 Phase 编号一致（`001` = 同 Feature 内第 1 个 Phase；`002` = 第 2 个；以此类推；**不**跨 Feature 复用——`feature001_phase001` 与 `feature002_phase001` 是两个不同 Phase）；
- `<phase_name>`：英文短横线连字符（kebab-case），与 §X.Y 章节标题保持一致；
- **v1 baseline：1 Phase = 1 提示词文件 = 1 次 `/speckit.specify` 闭环**（见 §12.4）；27 Phase = 27 文件（详见 §12.2）；
- 例：`feature001_phase001_cli_validation.md`、`feature003_phase002_new.md`、`feature004_phase006_middleware.md`。

**配套 verify 脚本路径**（详见立项书 §4.1.1 `tests/` 目录约定）：

```
tests/e2e/phase/verify_phase_f<XXX>_p<Y>.py
```

- `verify_phase_<f>_<n>.py` 与提示词文件 1:1 对应（v1 baseline 27 = 27）；
- pytest 风格，**黑盒测试**：只跑 `subprocess.run(["donkey", "init", ...])` 验证 exit code 与文件系统副作用，**不** import `donkey.*` 业务代码；
- CI 集成：`.github/workflows/ci.yml` 跑 `pytest tests/` 一键触发（**文件待建**——仓库当前尚无 .github/ 与 tests/ 目录）；Maintainer 评审单个 Phase 时 `pytest tests/e2e/phase/verify_phase_<f>_<n>.py` 单独跑；
- 例：`tests/e2e/phase/verify_phase_f001_p1.py` ↔ `feature001_phase001_cli_validation.md`。

### §12.2 提示词文件 ↔ Phase 映射表（v1 启动期 baseline）

> **当前粒度**：1 Phase = 1 提示词文件（27 Phase = 27 文件）；如未来某 Phase 工作量超出 1 次 `/speckit.specify` 闭环（如 F004-P6 middleware 10 错误 + 10 中间件），需 Maintainer 显式决策拆 / 合（**不**自动推断；如拆：1 Phase 拆为 2 文件，文件名按"phase 编号 + 后缀"，如 `feature004_phase006_middleware_register.md` / `_runtime.md`）。
>
> **落地状态（v1 启动期）**：上表 27 个提示词文件中，**已完成 1 个**（F001-P1）+ **已就绪 2 个**（F001-P2 / F001-P3）——`harness/features/feature001_phase001_cli_validation.md` / `feature001_phase002_template_skeleton.md` / `feature001_phase003_builtin_tools.md`；**其余 24 个待创建**（F002~F006），按上表"准入条件"列逐个解锁。
>
> **准入条件缩写**："F001-P1 退出条件" = §4.3 "退出条件" 全部跑出 PASS；"无前置" = 仓库初始化即可启动。
>
> **闭环复杂度**：根据 verify 脚本断言数与跨子模块数估（高 = 30+ 断言 / 跨 2+ 子模块；中 = 10-30 断言 / 1-2 子模块；低 = < 10 断言 / 1 子模块）。
>
> **段位列约定**：本列展示该 Phase 对应的**子段**（= 该 Phase 占用的 exit code 范围，含已用 + 预留；术语定义见 §1.5），与 §4.2 / §5.2 / §6.2 / §7.2 / §8.2 / §9.2 各 Phase 划分表一致。例：F004-P1 子段 `31-40` = 4 码已用（31-34）+ 6 码预留（35-40）；F001-P1 子段 `1-2`（F001 段位 `1-10` 中未归属任何 Phase 的 5-10 为段位级预留）。

| # | 提示词文件 | 覆盖 Phase | 段位 | 已用 exit code | 准入条件 | 验证脚本 | 闭环复杂度 |
|---|---|---|---|---|---|---|---|
| 1 | `feature001_phase001_cli_validation.md` | F001-P1 | `1-2` | 1, 2 | 无前置 | `verify_phase_f001_p1.py` | 低（7 断言） |
| 2 | `feature001_phase002_template_skeleton.md` | F001-P2 | `3` | 3 | F001-P1 退出条件 | `verify_phase_f001_p2.py` | 中（14 断言） |
| 3 | `feature001_phase003_builtin_tools.md` | F001-P3 | `4` | 4 | F001-P2 退出条件 | `verify_phase_f001_p3.py` | 中（11 断言） |
| 4 | `feature002_phase001_static_format.md` | F002-P1 | `11-13` | 11, 12, 13 | F001 3 Phase 全退出 | `verify_phase_f002_p1.py` | 中 |
| 5 | `feature002_phase002_static_dynamic_basic.md` | F002-P2 | `14-16` | 14, 15, 16 | F002-P1 退出条件 | `verify_phase_f002_p2.py` | 中 |
| 6 | `feature002_phase003_dynamic_runtime.md` | F002-P3 | `17-20` | 17, 18, 19 | F002-P2 退出条件 | `verify_phase_f002_p3.py` | 中 |
| 7 | `feature003_phase001_list.md` | F003-P1 | `21-22` | 21, 22 | F002 3 Phase 全退出 | `verify_phase_f003_p1.py` | 低 |
| 8 | `feature003_phase002_new.md` | F003-P2 | `23-25` | 23, 24, 25 | F003-P1 退出条件 | `verify_phase_f003_p2.py` | 中（涉及 sessions_metadata 表 + 标题总结 N-10） |
| 9 | `feature003_phase003_remove.md` | F003-P3 | `26-27` | 26, 27 | F003-P2 退出条件 | `verify_phase_f003_p3.py` | 低 |
| 10 | `feature003_phase004_import.md` | F003-P4 | `28-30` | 28, 29, 30 | F003-P3 退出条件；**v1 留接口, v1.x 落地** | `verify_phase_f003_p4.py` | 低（接口 stub） |
| 11 | `feature004_phase001_tools.md` | F004-P1 | `31-40` | 31, 32, 33, 34 | F003 4 Phase 全退出 | `verify_phase_f004_p1.py` | 中 |
| 12 | `feature004_phase002_skills.md` | F004-P2 | `41-50` | 41, 42, 43 | F004-P1 退出条件 | `verify_phase_f004_p2.py` | 高（自研 loader + per-skill tool 注册） |
| 13 | `feature004_phase003_mcp.md` | F004-P3 | `51-60` | 51, 52, 53 | F004-P2 退出条件 | `verify_phase_f004_p3.py` | 中 |
| 14 | `feature004_phase004_saver.md` | F004-P4 | `61-70` | 61, 62, 63 | F004-P3 退出条件 | `verify_phase_f004_p4.py` | 低 |
| 15 | `feature004_phase005_store.md` | F004-P5 | `71-80` | 71, 72, 73 | F004-P4 退出条件；v1/v2 用 InMemoryStore，3 码 v3 自研 SqliteStore 占位 | `verify_phase_f004_p5.py` | 低 |
| 16 | `feature004_phase006_middleware.md` | F004-P6 | `81-90` | 81, 82, 83, 84, 85, 86, 87, 88, 89, 90 | F004-P5 退出条件 | `verify_phase_f004_p6.py` | **高**（10 错误 + 10 中间件集成；可拆为 `phase006_middleware_register.md` + `_runtime.md`） |
| 17 | `feature004_phase007_agent_loop.md` | F004-P7 | `91-100` | 91, 92, 93, 94 | F004-P6 退出条件 | `verify_phase_f004_p7.py` | **高**（图编译 + 状态机 + 24h 长稳） |
| 18 | `feature005_phase001_event_stream.md` | F005-P1 | `101-110` | 101, 102, 103, 104 | F004 7 Phase 全退出 + 后端 API 稳定 | `verify_phase_f005_p1.py` | 中 |
| 19 | `feature005_phase002_ipc_bridge.md` | F005-P2 | `111-120` | 111, 112, 113 | F005-P1 退出条件 | `verify_phase_f005_p2.py` | 中 |
| 20 | `feature005_phase003_render.md` | F005-P3 | `121-130` | 121, 122, 123, 124 | F005-P2 退出条件 | `verify_phase_f005_p3.py` | 高（前端框架 + Markdown/代码高亮） |
| 21 | `feature005_phase004_state.md` | F005-P4 | `131-140` | 131, 132, 133 | F005-P3 退出条件 | `verify_phase_f005_p4.py` | 中 |
| 22 | `feature005_phase005_auth.md` | F005-P5 | `141-150` | 141, 142, 143 | F005-P4 退出条件 | `verify_phase_f005_p5.py` | 中 |
| 23 | `feature005_phase006_resource.md` | F005-P6 | `151-160` | 151, 152, 153 | F005-P5 退出条件 | `verify_phase_f005_p6.py` | 低 |
| 24 | `feature005_phase007_misc.md` | F005-P7 | `161-170` | 161, 162 | F005-P6 退出条件 | `verify_phase_f005_p7.py` | 低 |
| 25 | `feature006_phase001_main_process.md` | F006-P1 | `171-180` | 171, 172, 173 | F005 7 Phase 全退出 + Electron 选型敲定 | `verify_phase_f006_p1.py` | 中 |
| 26 | `feature006_phase002_window.md` | F006-P2 | `181-190` | 181, 182, 183, 184 | F006-P1 退出条件 | `verify_phase_f006_p2.py` | 中 |
| 27 | `feature006_phase003_native_glue.md` | F006-P3 | `191-200` | 191, 192, 193, 194 | F006-P2 退出条件 | `verify_phase_f006_p3.py` | 中 |

**汇总**：v1 baseline = **27 提示词文件 = 27 Phase**（1:1）。

### §12.3 提示词文件内容契约

每个 `featurexxx_phasexxx_<phase_name>.md` 提示词文件须包含：

1. **目标声明**：引用本文档对应章节的 Phase 范围（含 Phase 编号 + 段位 + Error class）；
2. **入口条件**：引用 §X.Y "入口条件"段；
3. **异常退出码表**：从 §3 一览总表复制该 Phase 涉及的所有 Error 类与退出码；
4. **退出条件**：引用 §X.Y "退出条件"段；
5. **可执行命令 / 测试列表**：明确"完成 Phase = 跑通下列命令 / 测试"；
6. **绝对不做清单**：明确"Phase 不做这些，留给下 Phase / 下 Feature"；
7. **引用链接**：立项书对应章节 + 宪法对应条款 + 调研报告对应章节 + 同 Feature 兄弟 Phase 文件名。

### §12.4 Speckit 工作流串联

```
1. Maintainer 在 §12.2 选下一个未完成 Phase（按 §10.2 跨 Feature 推进策略 / 门控关系）
2. 新开会话执行 /speckit.specify + featurexxx_phasexxx_<phase_name>.md
   → 生成 specs/<branch>/spec.md
3. （可选 1-2 轮）/speckit.clarify → 消除歧义
4. /speckit.plan → 生成 plan.md
5. /speckit.tasks → 生成 tasks.md
6. /speckit.analyze → 三件套一致性检查（与 §12.2 映射表 / §3 一览总表 / 立项书交叉验证）
7. /speckit.implement → TDD 编码 + 测试
8. 跑 verify_phase_<f>_<n>.py → 必须 PASS
9. Maintainer 复核 → Phase 完成
```

**Phase 完成的硬性证据**：
- 该 Phase 的 `verify_phase_<f>_<n>.py` 全部 PASS；
- §3.1-§3.6 对应表行的 exit code 实测通过；
- §X.Y "退出条件"逐项打勾（Maintainer 人工）；
- 后续 Phase 的入口条件不被破坏。

---

**Source of truth**：
- `harness/features/立项书.md`（F 编号唯一权威）
- `.specify/memory/constitution.md`（Phase 切分规则 / 段位表 / 不可妥协原则 N-01~N-12）
- `harness/prompt/speckit.md`（Speckit 工作流）

---

## 附录：donkey 文档体系总索引（v1 baseline）

| 类型 | 文件 | 作用 |
|---|---|---|
| **宪法** | `.specify/memory/constitution.md` | 不可妥协原则 N-01~N-12 + 段位表 + ADR（D-01~D-13） |
| **立项** | `harness/features/立项书.md` | F 编号唯一权威 + Feature 范围 + Phase 总览 |
| **目录** | `harness/features/README.md`（本文档） | Phase 与 exit code 落地映射 + Speckit 流程 |
| **官方文档镜像** | `harness/LangChain_doc/`、`harness/LangGraph_doc/`、`harness/Managed_deep_agents/` | Speckit 资料引用基线 |
| **调研报告** | `harness/report/Saver和Store.md` | Saver/Store 选型与 13 个官方实现对比 |
|  | `harness/report/全开源最佳实践.md` | 内网部署不依赖 LangSmith |
|  | `harness/report/LangChain内置中间件速查表.md` | v1 录用 / 禁用中间件清单 |
|  | `harness/report/关于subagent的实现方式.md` | subagent 路线 A/B 选型 |
|  | `harness/report/内置工具应该自己实现还是调用中间件.md` | 三大内置 `@tool` 设计决策 |
|  | `harness/report/LangGraph的节点到底是什么东西.md` | 中间件 hook 风格 → 节点数映射 |
|  | `harness/report/大模型toml参数设计.md` | **`providers/` 目录 schema 权威**（26 家白名单 / 字段全集 / `enabled` 开关 / 三档鉴权 / exit 11 校验清单） |
|  | `harness/report/sessions_sqlite表结构一览.md` | **sqlite3 schema 权威**（v1 baseline = sessions schema-built / store+knowledge v1 占位；F002-P2 健康检查 5 项断言口径） |
| **提示词文件（已就绪）** | `harness/features/feature001_phase001_cli_validation.md` / `feature001_phase002_template_skeleton.md` / `feature001_phase003_builtin_tools.md` | F001-P1 / P2 / P3 三个提示词文件已就绪 |
|  | 后续 24 个提示词文件待创建（见 §12.2 映射表） | F002~F006 的 Phase 提示词文件尚未落地 |
| **历史留档** | `harness/features/宪法初稿.md`（已被 .specify/memory/constitution.md 取代，不具治理效力）、`harness/features/立项书-大纲目录.md` | 仅供追溯，不具治理效力 |
