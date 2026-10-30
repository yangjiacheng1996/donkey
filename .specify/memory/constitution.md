# donkey 宪法（初稿）

> 本文档是 donkey 项目的最高治理规则，由 Maintainer 立项书中的"不可妥协"原则沉淀而来。
> 与立项书冲突时，以本宪法为准；与本宪法冲突的代码 / 文档 / 流程一律无效，须按 Governance 流程修订。

**关联文档索引**：
- 立项书：`harness/features/立项书.md`
- Phase 进度与映射：`harness/features/README.md`
- sqlite schema 权威：`harness/report/sessions_sqlite表结构一览.md`
- 长期记忆选型：`harness/report/Saver和Store.md`

---

## 第 1 章 项目身份与不可妥协原则

### 1.1 项目身份

**donkey** 是一个**智能体材料层的可移植运行时引擎**。其核心主张：

- **材料归用户**：workspace 目录 = 智能体的全部材料层（人格、知识、手脚、大脑），用户可任意替换；
- **运行归引擎**：Agent Loop、中间件挂载、客户端渲染、上下文治理等统一由引擎实现，不开放配置；
- **改引擎请 fork**：workspace 没有任何配置项能改变引擎层行为，需要 diff 审阅、路径权限交互、自定义图流程等能力的唯一官方路线是 fork donkey 本仓库二次开发。

### 1.2 不可妥协原则清单（编号在立项书中沉淀，不可删除）

| 编号 | 条款 | 来源 |
|---|---|---|
| **N-01** | workspace 内**禁止**出现 `agent.py` / `main.py` 或任何 Python 入口文件 | 立项书 §3.4 |
| **N-02** | **禁止** subagent / 子智能体相关目录或字段（哲学："agent = 人"，不存在把人降级为子工具的概念） | 立项书 §1.2.3 |
| **N-03** | `donkey.core` **禁止** import 任何 client（cli / web / gui） | 立项书 §4.1.1 |
| **N-04** | `cli` **禁止**直接 import `langchain` / `langgraph` / `sqlite3`；所有 LangChain / LangGraph / sqlite3 调用封在 `donkey/core/` 内（web / gui 客户端同理） | 立项书 §4.1.1 |
| **N-05** | `donkey.core` **禁止** import `argparse` / `sys.argv` / `click` / `typer`（保持业务 / 客户端边界） | 立项书 §4.1.1 |
| **N-06** | `donkey load` 失败时 exit code **非 0**，但**不得**修改 workspace 中任何文件 | 立项书 §5.5.3 |
| **N-07** | `donkey load` 不依赖 `init`：用户可跳过 `init` 直接跑 load，load 必须检测并清晰报告"未 init" | 立项书 §5.5.3 |
| **N-08** | `donkey` 全子命令 exit code 段位空间严格不重叠（详见第 4 章 §4.4） | 立项书 §5.5.3 |
| **N-09** | `donkey session` 的**对外标识是标题**，thread_id 仅作内部引用 | 立项书 §5.5.4 |
| **N-10** | `donkey session new` 默认标题"无标题会话"；若给了首轮 prompt，**必须**在 `donkey.core.api.new_session` **内部**由 LLM 总结 ≤ 20 字标题并写回 sqlite3；**标题总结失败 / 超时时必须回退为首轮 prompt 的前 20 字**（**严禁**回退成"无标题会话"——不允许出现"Agent Loop 已启动但标题仍是占位符"的状态）；**严禁**实现为 `before_agent` 中间件（**不**进 Agent Loop 图，**不**新增 LangGraph 节点，**不**触发版本号 `x+1`） | 立项书 §5.5.4.5 |
| **N-11** | v1 **必须**同时交付 cli / web / gui 三种客户端，缺一不可；任何客户端**不**允许出现"功能仅 cli 独有"的情况 | 立项书 §5.5.6 |
| **N-12** | **禁止**使用任何 LangSmith 相关代码（包含但不**限于** `langsmith` 包 / LangSmith Cloud / Studio UI / Tracing / Deployment / Hub / `langchain[langsmith]` extras / `LANGSMITH_TRACING` 等环境变量）；**禁止**直接 `import langsmith` 或任何 langsmith.* 子包（包括用于诊断智能体的场景）。**边界（2026-10-23 澄清，见 [D-17]）**：本条的约束对象是 **donkey 自有代码路径**（`donkey.core` / `cli` / `web` / `gui`）的 **import 与使用**；第三方库的**传递依赖被安装到磁盘**不构成"使用"——但 MUST 在 plan 中显式登记，且 MUST 由门禁实证"donkey 永不 import"（不设 `LANGSMITH_*` 等环境变量） | `harness/report/全开源最佳实践.md` §0 |

---

## 第 2 章 核心设计原则

### 2.1 两层模型（材料层 vs 引擎层）—— **最高架构原则**

| 层 | 包含 | 定义方 | 交付方式 | 可移植性 | 配置接口 |
|---|---|---|---|---|---|
| **材料层**（workspace 层） | Instructions / Model / Tools / Skills | 用户 | 一个目录 | 高：zip / git 带走 | workspace 内 4 类材料文件 |
| **引擎层**（harness / runtime 层） | Agent Loop 图流程、middleware 链、diff 审阅、路径权限交互、前端渲染、上下文治理、客户端渲染 | `donkey` 代码 | fork 本仓库 | 低：fork | **无任何配置项** |

**三条结论**（贯穿全文）：

1. 换 workspace 可以改变人格 / Skills / 工具 / 模型，但**不能**把 donkey 变成 OpenCode（diff、路径权限等能力不可配置）；
2. 需要引擎层能力的用户，**唯一官方路线是 fork** —— donkey 不通过配置提供这些能力；
3. 编程型 workspace 提供的是**编程人格 / Skills / 工具 / 模型**（材料层），官方模板**不承诺**提供 diff 审阅（AC-5）。

### 2.2 路径绝对化原则（§立项书 1.2.2 P3）

- workspace 内的所有相对路径引用**以 workspace 绝对路径为唯一根**；
- **禁止**依赖进程 cwd / HOME / 属主隐藏目录约定；
- workspace 可存放在任意路径（用户有适配执行权限即可），donkey 不要求它位于属主目录或任何隐藏目录下。

### 2.3 workspace 原子性原则（§立项书 1.2.2 P1+P2）

- **一个 workspace 目录 = 一个 Agent**，workspace 自带 manifest；
- 依赖与配置随 workspace 走；运行数据可选择性导出；
- workspace 有格式版本号，donkey 升级时提供迁移路径。

### 2.4 Skills 三层渐进披露原则（§立项书 1.2.4）

每个 Skill 目录 `skills/<name>/SKILL.md` 按访问频度分为三级，**这是 donkey 的核心设计**：

| 级别 | 内容 | 加载方式 | 触发时机 |
|---|---|---|---|
| **Level 1** | `SKILL.md` frontmatter 必填两字段：`name` + `description` | `donkey.core` 扫描后**自动注册为独立 `@tool`**（工具名 `load_skill_<slugify(name)>`） | 工具列表常驻 |
| **Level 2** | `SKILL.md` frontmatter 下方的 Markdown 主体 | 通过 Level 1 工具调用返回（返回值含 Level 2 完整内容） | 模型判断相关时调用 |
| **Level 3** | Skill 目录内除 `SKILL.md` 之外的文件 | 由 workspace 内置 `@tool`（filesystem / commandline / webfetch）或 `FilesystemFileSearchMiddleware.glob_search/grep_search` 读取 | 模型需要深层细节 / 执行时调用 |

**Skills frontmatter schema 严格性**：
- 仅 `name` + `description` 两字段必填（与 MDA / Anthropic Agent Skills 协议对齐）；
- **不允许**自定义额外字段（`when_to_use` / `version` / `tags` 等）——donkey v1 不解析，避免 schema 漂移；
- 想加元信息写在 Markdown 主体（Level 2）即可。

### 2.5 内置 `@tool` 与中间件职责正交原则（§立项书 1.2.4 + 1.5.4 + 4.6.1）

| 工具来源 | 职责 | 调用场景 |
|---|---|---|
| `FilesystemFileSearchMiddleware`（引擎侧 LangChain 中间件） | `glob_search` + `grep_search`（ripgrep 后端） | "找文件"、"找内容" |
| `tools/filesystem.py`（workspace 内置 `@tool`，材料层） | 文件操作：read / write / copy / move / delete / list_dir / stat | "读这个文件"、"改那个文件" |
| `tools/commandline.py`（workspace 内置 `@tool`） | `run_shell` —— `subprocess.run([...], shell=False, timeout=...)`；**每次新建进程**，不走持久 shell | 命令执行 |
| `tools/webfetch.py`（workspace 内置 `@tool`） | `fetch_url` —— HTTP GET/POST + timeout；不持久化 cookies | HTTP 拉取 |

**职责正交不重叠**：内置 3 个 `@tool` + `FilesystemFileSearchMiddleware` 中间件共同构成 Skill Level 3 的完整访问通道，按场景选用。

### 2.6 workspace 目录必填项（§立项书 4.6.1）

**必须存在**：`instruction.md` / **`providers/`**（内含必填的 `providers/default.toml`）/ `tools/` / `mcp/mcp.json` / `skills/` / `memory/`

**另由 `donkey init` 生成（donkey 自管，非用户材料）**：`<workspace>/manifest.json` —— D-01 的 workspace manifest，字段最少化（`version` / `name` / `created_at` / `donkey_version`）。它与**包内**的 `core/workspace/templates/manifest.json`（模板文件清单）**是两个不同的文件**，前者落在 workspace 根，后者落在 donkey 安装包内。

**显式排除**（workspace 内不出现）：
- ❌ `agent.py` / `main.py` / 任何 Python 入口
  > **边界（2026-10-23 澄清，见 [D-19]）**：本条的"任何 Python 入口"指**智能体入口**（能直接启动智能体的文件）；Skill **第三层附属资源目录**（`skills/<name>/scripts/` 等）下的**普通演示脚本**（如 `skills/example/scripts/example.py`）属**用户代码路径的普通脚本**，**不属**该范畴 —— 智能体的唯一官方入口仍是 `donkey.core.api.create_agent`。
  > **授权来源（2026-10-23 正式化）**：本边界原经 §6.3 **例外 E-02** 临时授权；E-02 到期时经 Maintainer 裁决**正式纳入宪法** —— 载体即 §5 章 **[D-19]**（该条自此为正式条款，不再依赖临时例外）。E-02 转为历史登记。
- ❌ `middleware/`（中间件属引擎侧）
- ❌ `connectors/` / `channel/` / `schedules/` / `evals/` / `identity/` / `sandbox/`
- ❌ `memory.py`（长期记忆文件）
- ❌ `mcp/*.py`（自定义 MCP server 代码）
- ❌ `.git/`（donkey 不自动 `git init`）

### 2.7 中间件录用与禁用清单（§立项书 1.5.4 + 1.5.5）

#### 2.7.1 v1 录用中间件（10 项）

| # | 中间件 | hook 风格 | 对主图节点数影响 |
|---|---|---|---|
| 1 | `ToolErrorMiddleware` | wrap-style | 0（嵌套） |
| 2 | `ToolRetryMiddleware` | wrap-style | 0（嵌套） |
| 3 | `ModelRetryMiddleware` | wrap-style | 0（嵌套） |
| 4 | `SummarizationMiddleware` | node-style（`before_model`） | +1 |
| 5 | `ModelCallLimitMiddleware` | node-style（`before_model` + `after_model`） | +2 |
| 6 | `PIIMiddleware` | both（**框架始终编译为 2 节点**，与 `apply_to_*` 配置无关） | +2 |
| 7 | `TodoListMiddleware` | both（`after_model` 节点 + `wrap_model_call`） | +1 |
| 8 | `LLMToolSelectorMiddleware` | wrap-style | 0（嵌套） |
| 9 | `ContextEditingMiddleware` + `ClearToolUsesEdit` | wrap-style | 0（嵌套） |
| 10 | `FilesystemFileSearchMiddleware` | 无 hook（仅工具注册） | 0（仅多 2 个工具） |

**v1 主图节点合计 10 个**：4 基线（`__start__` / `model` / `tools` / `__end__`）+ 6 中间件节点（见立项书 §4.4.2）。

#### 2.7.2 v1 永久禁用中间件

| 中间件 | 禁用理由 |
|---|---|
| `ModelFallbackMiddleware` | retry 已能扛住；降级模型上下文与主模型不一致会引入新故障 |
| `ToolCallLimitMiddleware` | 与 `ModelCallLimitMiddleware` 功能重叠，v1 粗粒度已够用；工具级细粒度留给 fork |
| `ProviderToolSearchMiddleware` | 供应商覆盖度低 |
| `HumanInTheLoopMiddleware` | v2 专攻 HITL（§立项书 1.5.3）；v1 不挂 |
| `LLMToolEmulator` | 测试用，不用于生产 |
| `ShellToolMiddleware` | 持久 shell session 与 HITL 冲突；由 `tools/commandline.py` 替代（每次新进程 + timeout） |
| `FilesystemMiddleware`（deepagents） | deepagents 专有（违反 N-12）+ 默认 backend 不是磁盘 |
| `SubAgentMiddleware`（deepagents） | deepagents 专有 + 违反 N-02 |
| `RubricMiddleware`（deepagents） | deepagents 专有 + 标注为 Beta + 违反 N-12 |
| `SkillsMiddleware`（deepagents） | deepagents 专有；donkey 自研 Skills loader（§2.4 三层模型） |
| `MemoryMiddleware`（deepagents） | deepagents 专有；v3 自研 `SqliteStore` |

### 2.8 客户端三端对等原则（§立项书 N-11 + 5.5.6）

- v1 **必须**同时交付 cli / web / gui 三种客户端；
- 任何客户端**不**允许出现"功能仅 cli 独有"的情况 —— 每个客户端都覆盖同一组最小子命令集（`init` / `load` / `session {list,new,rm,import}` / `run`）；
- 三端**共用 `donkey.core.api` 库 API**，不重复实现业务逻辑；
- **开发顺序**（与洋葱架构一致）：CLI 在 F001–F004 期间渐进补齐 → Web 主攻 v1 UI → GUI = Electron 包壳（100% 复用 Web 渲染层）；
- **不**允许 Web 未完成就启动 GUI（违反洋葱架构），也**不**允许跳过 CLI 直接做 Web（违反 §4.1.1 库 API 必须先稳定的约束）。

### 2.9 Skills 自研 + 禁止 deepagents 依赖原则（§立项书 1.2.4 + 调研 `LangChain与DeepAgents的选择.md`）

- donkey v1 **不依赖** `deepagents` 包（违反 §N-01 ~ N-12 一致性）；
- Skills 加载器自研，**遵循** LangChain `AgentMiddleware.wrap_model_call` 模式（参考 `LangChain_doc/multi-agent/skills-sql-assistant.md:165-225` 的 `SkillMiddleware` 参考实现），行为与 DeepAgents SkillsMiddleware **对齐但无 deepagents 依赖**；
- 内置 3 个 `@tool`（filesystem / commandline / webfetch）**全部自研**，不依赖 `FilesystemMiddleware`（deepagents + 默认 backend 非磁盘）与 `ShellToolMiddleware`（持久 shell + HITL 冲突）。

---

## 第 3 章 不可妥协约束

### 3.1 技术栈与依赖硬约束

| 维度 | 硬约束 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | LangChain / LangGraph 官方语言；`tomllib` 内置 |
| Agent 框架 | LangChain 1.x `create_agent` | 直接返回编译图，中间件插件化（`agents.md:19`） |
| 图运行时 | LangGraph 当前稳定版 | 业内事实标准 |
| **短期记忆** | `memory/sessions.sqlite3`（**单文件三表两索引**：`checkpoints` / `writes` 由上游 saver 拥有 + `sessions_metadata` 由 donkey 自管）——init 阶段 schema builder 创建，运行时 `SqliteSaver` 落盘历史 + `core.api.new_session` 写元数据（INSERT，**不**重复 `CREATE TABLE`）；长期 / 知识库另列（`store.sqlite3` v3 / `knowledge.sqlite3` v3+ 占位）。**详见下方 §3.1.1** | 唯一零配置本地文件选项；`sessions_metadata` 提供 title ↔ thread_id 映射 + 元数据持久化；F002-P2 `SqliteSchemaError` (exit 16) 通过 **5 项断言**判定 schema 健康（口径以 `harness/report/sessions_sqlite表结构一览.md` §7 为准） |

#### 3.1.1 短期记忆实现细则（`memory/sessions.sqlite3`）

- **单文件三表两索引**：`SqliteSaver` 自有 `checkpoints` / `writes`（短期 message 历史，`thread_id` 即主键）+ donkey 自管 `sessions_metadata`（元数据）；另加 2 个索引；
- **`sessions_metadata` 6 字段**：`thread_id` ↔ `title` + `created_at` / `updated_at` / `donkey_version` / `first_prompt`（N-09 / N-10 实现机制；详见 `harness/report/sessions_sqlite表结构一览.md` §2.2）；
- **写元数据不建表**：`core.api.new_session` 只 INSERT，**不**重复 `CREATE TABLE`（掩盖 init 缺失 / `--force` 后被破坏等异常）；
- **`--force` = 恢复出厂设置**：删 + 重建 sqlite3（含 schema），用户须在 `--force` 前手动备份（`cp memory/*.sqlite3 /tmp/backup-*.sqlite3`）；"运行数据可选择性导出"仍生效——sqlite3 模板身份 ≠ 必须导出；
| 长期记忆 | v1~v2：LangGraph `InMemoryStore`（进程重启即丢，仅开发 / 测试）；v3：自研 `SqliteStore`（仿照 PostgresStore） | LangGraph 官方无 SQLite Store（见 `Saver和Store.md` §2.1；自研 SqliteStore 详细 SQLite 端口三处适配：`namespace` 数组→JSON 字符串 + `value` JSONB→TEXT + GIN→json_each/FTS5，详见 `sessions_sqlite表结构一览.md` §3.3） |
| MCP | LangChain `MCPAdapter` + `MCPConfig` dict | 官方推荐 / 跨编辑器通用 |
| 配置格式 | TOML | LangChain / LangGraph 生态趋势 |
| CLI | `argparse`（stdlib） | 不引入 typer / click 以保持业务 / 客户端边界（N-05） |
| 测试 | pytest + LangChain 内置测试模式；测试代码放在 `tests/` 目录（与 `core/` / `cli/` / `web/` / `gui/` 同级；分 unit / integration / e2e/phase 三层；**`tests/e2e/phase/verify_phase_<f>_<n>.py` 黑盒测试**——只跑 `subprocess.run(["donkey", ...])` 验证 exit code 与文件系统副作用，**不** import `donkey.*` 业务代码） | 社区标准 |

### 3.2 永不使用清单

- ❌ **LangSmith** 任何形态（详见 N-12）：**禁止**使用 LangSmith Cloud / Studio UI / Tracing / Deployment / Hub / `langchain[langsmith]` extras / `LANGSMITH_TRACING` 等环境变量；**禁止**在 `donkey.core` / cli / web / gui 任何代码路径中 `import langsmith` 或 `import langchain.langsmith / langchain_community.langsmith / langgraph.langsmith` 等任何 langsmith.* 子包（包括但不限于为了"诊断智能体"或"打印运行轨迹"等用途）—— 智能体诊断统一通过 `donkey.core` 自有输出（stdout 日志 / 事件流 / 后续自研 tracer）实现，受 `harness/report/全开源最佳实践.md` §0 约束。
  > **边界（2026-10-23 澄清，见 [D-17]）**：以上禁令的约束对象是 **donkey 自有代码路径**的 import 与使用；第三方库的**传递依赖被安装到磁盘**不构成"使用"（例：`langchain-core` 会把 `langsmith` 作为硬传递依赖装上磁盘，但 donkey 自有代码永不 import 它）。此类依赖 MUST 在 plan 中显式登记其影响面与门禁验证方式，MUST NOT 以"安装"之名引入任何实际的 LangSmith 使用。
- ❌ **deepagents** 包（含 `create_deep_agent` / FilesystemMiddleware / SubAgentMiddleware / RubricMiddleware / SkillsMiddleware / MemoryMiddleware）—— 见 §2.7.2；
- ❌ **ShellToolMiddleware**（持久 shell + HITL 冲突）—— 由 `tools/commandline.py` 替代；
- ❌ **subagent / 子智能体相关任何目录或字段**（`agent = 人`）—— N-02；
- ❌ **workspace 内 Python 入口文件**（`agent.py` / `main.py`）—— N-01。

### 3.3 长期记忆硬约束

- v1 / v2：**仅**使用 LangGraph `InMemoryStore`；接受"进程重启即丢"——v1 / v2 不需要长期记忆；
- v3：自研 `SqliteStore`，**仿照 `langgraph-checkpoint-postgres` 的 `PostgresStore`** 实现（接口契约参考调研 `Saver和Store.md` §七 + §十二）；
- 自研 Store **必须**显式继承 `BaseStore` 接口；
- 自研 Store 落地时机由立项书 §4.10 TD-02 路线图决定，**不**挤占 v1 时间线；
- **SQLite 端口三处硬适配**（与 `sessions_sqlite表结构一览.md` §3.3 第 0 / 3 / 4 项对齐）：
  1. **数组语法**：`namespace TEXT[]` → JSON 字符串 TEXT（如 `'["alice","memories"]'`，参考 `LangGraph_doc/stores.md:73`）；
  2. **JSONB → TEXT**：`value JSONB` → `TEXT` + `json_extract` / `json_each`；
  3. **GIN 索引** → SQLite 端：`json_each` 展开为虚拟表 + B-Tree / FTS5 / 自定义 LIKE 前缀函数 / 触发器（SQLite 无 GIN）。

### 3.4 Skills 三层加载硬约束

- `core.skills.loader` 必须实现 §2.4 表中 Level 1 / 2 / 3 三级加载路径；
- per-skill tool 命名规则：`load_skill_<slugify(name)>`，工具 description = `frontmatter.description` 轻度改写 + 1 句触发短语；
- `donkey init` 必须自动生成 3 个内置 `@tool`（filesystem / commandline / webfetch）作为 Skill Level 3 的标准访问通道。

### 3.5 数据安全分级

- `providers/*.toml` 的 `api_key` / `aws_secret_access_key` 等凭据字段（per-provider 明文字段，**不读 env var**）**视为高敏感**；
- `donkey load` 异常 / 默认错误输出**自动脱敏**（不打印密钥明文）；
- workspace 凭据由用户自负；donkey 不上传 workspace 内容。

---

## 第 4 章 开发流程与版本治理

### 4.1 实施方法论（§立项书 1.5.1 + 5.1）

- **方法**：瀑布式 + 小步快跑；洋葱架构先核心后外层；
- **TDD**：每个 feature 用 Speckit 的 specify → plan → tasks → implement 四件套流程；
- **质量保障**：单元测试 + 集成测试 + e2e（迁移验收用例 100% 覆盖）；
- **CI/CD**：GitHub Actions；pytest + ruff + mypy；Release 通过 GitHub Releases。

### 4.2 Feature 划分与编号唯一性（§立项书 3.2.1 + 5.2）

**F 编号是 donkey 全项目唯一权威 Feature 编号**，与立项书 §3.2.1 一一对应：

| 编号 | 子命令 / 客户端 | 核心库 API |
|---|---|---|
| **F001** | `donkey init` | `init_workspace(path, name, force)` |
| **F002** | `donkey load` | `load_workspace(path) -> LoadResult` |
| **F003** | `donkey session` | `list_sessions / new_session / remove_session / import_session` |
| **F004** | `donkey run` | `run_session(path, session_id)` |
| **F005** | `donkey web` | （前端，复用 F001–F004 核心 API） |
| **F006** | `donkey gui` | （前端，复用 F001–F004 核心 API） |
| Scheduler | 长期记忆 + 任务调度 + cron | （v3） |

任何 spec / plan / tasks / 代码 / 文档中出现 F 编号引用必须与上表**字面对齐**。

#### 4.2.1 元信息命令豁免

F 编号表锁定的是**核心功能**的一级命令；**元信息命令**（只读地暴露工程元信息、不承载业务能力、不占用 exit code 段位、不需要 `donkey.core.api` 库 API）**豁免 F 编号登记**，当前唯一成员是 `donkey version`。

边界：元信息命令 MUST NOT 被后续 Feature 扩张为业务命令 —— 一旦它开始承载可失败的业务能力（需要 Error class / exit code 段位 / 库 API），MUST 先按 §6.2 Governance 流程取得 F 编号。

### 4.3 Phase 切分规则（§立项书 5.2.1）

**核心原则**：Phase 是 Feature 内部的**开发阶段**（dev unit，1 次 `/speckit.specify` 闭环单位），**不再按一级命令划分**（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）。Phase 与 exit code 子段在 v1 baseline 中 1:1 对齐（4 术语区分详见 README §1.5）：

| 规则 | 适用 Feature | 切分单位 | 产物 |
|---|---|---|---|
| **规则 A：按二级命令切** | 含二级命令的 Feature（如 F003 `donkey session list / new / remove / import`） | 每个二级命令 = 一个子段 = 一个 Phase（v1 baseline 1:1） | 1 子段 + 1 Phase + 1 提示词文件 + 1 verify 脚本 |
| **规则 B：按退出码段位切** | 无二级命令的 Feature（如 F001 / F002 / F004 / F005 / F006） | 每 N 个连续退出码（落在该 Feature 段位内）= 一个子段 = 一个 Phase（v1 baseline 1:1；N 由该 Feature 失败场景数量决定） | 同上 |

**4 术语严格分层**（详见 README §1.5）：

| 术语 | 定义 | 视角 | 标识 |
|---|---|---|---|
| **Phase** | 开发阶段（1 次 `/speckit.specify` 闭环） | 开发 | `F###-P#` |
| **段位** | 一个 Feature 拥有的 exit code 连续范围 | 错误 | `1-10` / `11-20` / `21-30` / `31-100` / `101-170` / `171-200` |
| **子段** | 段位内的 exit code 子分组（Phase 在段位内占用的码范围，含已用 + 预留） | 错误 | `F001 子段 1` = exit 1-2 |
| **Error class** | 具体 Python 异常类 | 代码 | `PathNotFoundError` 等 |

**v1 baseline**：1 Phase = 1 子段 = 1 提示词文件 = 1 verify 脚本（27 Phase = 27 文件 / 27 脚本）；如未来某 Phase 工作量超出 1 次 `/speckit.specify` 闭环容量，Maintainer 显式决策拆 / 合（不自动推断，参见 README §12.2 备注）。**（元信息命令按 §4.2 豁免）**：§4.2.1 定义的元信息命令**不占用** exit code 子段、**不需要**提示词文件，故本句的 1:1 口径对元信息命令**不适用**（当前唯一成员 = `donkey version`，见 [D-20]）。

**每设计一个 Phase 必带三要素**：
1. **入口条件（Entry Gate）**：前置 Phase 的退出条件必须全部满足（可执行命令 / 测试验证通过；可能跨 Feature——按 §4.4 Speckit 协作方式滚动推进）；
2. **异常退出码（Exit Code）**：该 Phase 覆盖的子段内 Error class 对应的 exit code 集合（落在该 Feature 段位内；具体码值见 §4.4 + 立项书 §5.5.3 + README §3 一览总表对应行）；
3. **退出条件（Exit Gate）**：可执行、可验证的硬指标 —— 由 `verify_phase_<f>_<n>.py` 验证脚本跑出 PASS/FAIL，**不**依赖 Maintainer 主观判断。

**Phase 编号规则**：
- 同 Feature 内 Phase 编号严格串行、严格递增（`P1` → `P2` → `P3` …）；
- Phase 编号**不**跨 Feature 复用（`F001-P1` 与 `F002-P1` 是两个不同 Phase）；
- Phase 编号出现在 §3 一览总表行号、§X.Y 章节号、提示词文件名（`featurexxx_phasexxx_<phase_name>.md`）、verify 脚本名（`verify_phase_<f>_<n>.py`）。

**Speckit 协作方式**：按跨 Feature 滚动推进 —— 同一时段并行多个 Feature 的同 Phase 任务；Feature 内部 Phase 严格串行。

具体 Phase 编号、退出码分配、退出条件细节在各自 Feature spec（即 README §3 / §4 / §6 / §7 / §8 / §9）中规定；宪法与立项书 §5.2.1 只规定**切分原理**，**不**展开具体编号。

### 4.4 exit code 段位分配总表（§立项书 §5.5.3 + N-08）

`donkey` 各子命令 exit code 段位严格不重叠（同时也是 §4.3 规则 B 切 Phase 的基础）：

| 段位 | 归属 | 冗余性 | 说明 |
|---|---|---|---|
| `0` | 全子命令 | 1 码 | 一切正常 |
| `1-10` | `donkey init` | 10 码 | F001 域 —— 按 §4.3 规则 B 切 Phase |
| `11-20` | `donkey load` | 10 码 | F002 域 —— 按 §4.3 规则 B 切 Phase |
| `21-30` | `donkey session` | 10 码 | F003 域 —— 按 §4.3 规则 A 切 Phase（4 个 Phase = list / new / remove / import，每个二级命令均分 2-3 码值 + 保留） |
| `31-40` | `donkey run` → tools 调用 | 10 码 | F004 子段 1：用户 / 系统 `@tool` 执行错误；按 §4.3 规则 B，对应 F004 的一个 Phase |
| `41-50` | `donkey run` → Skills 加载 | 10 码 | F004 子段 2：per-skill tool / SKILL.md 加载错误；F004 的一个 Phase |
| `51-60` | `donkey run` → MCP server | 10 码 | F004 子段 3：`MCPAdapter` / server 通信错误；F004 的一个 Phase |
| `61-70` | `donkey run` → 短期记忆（Saver） | 10 码 | F004 子段 4：`SqliteSaver` 读写错误；F004 的一个 Phase |
| `71-80` | `donkey run` → 长期记忆（Store） | 10 码 | F004 子段 5：`SqliteStore`（v3）/ `InMemoryStore`（v1/v2）；F004 的一个 Phase |
| `81-90` | `donkey run` → 中间件 | 10 码 | F004 子段 6：10 项 v1 中间件 + 后续中间件错误；F004 的一个 Phase |
| `91-100` | `donkey run` → Agent Loop | 10 码 | F004 子段 7：图编译失败 / 节点类型不匹配 / State schema 异常；F004 的一个 Phase |
| `101-110` | `donkey web` → 事件流 | 10 码 | F005 子段 1：WebSocket / SSE 连接 / 消息序列化 / 断流重连 |
| `111-120` | `donkey web` → IPC 桥接 | 10 码 | F005 子段 2：cli ↔ web 进程间调用 / 超时 / 序列化 |
| `121-130` | `donkey web` → 渲染 | 10 码 | F005 子段 3：组件异常 / SSR-CSR 失配 / Markdown-代码高亮 |
| `131-140` | `donkey web` → 状态管理 | 10 码 | F005 子段 4：session / store 同步 / 状态丢失 / 回滚失败 |
| `141-150` | `donkey web` → 鉴权 / CORS / CSP | 10 码 | F005 子段 5：跨域 / cookie / token 过期 |
| `151-160` | `donkey web` → 资源加载 | 10 码 | F005 子段 6：chunk 404 / CDN 失败 / WebAssembly |
| `161-170` | `donkey web` → 其它 | 10 码 | F005 子段 7：浏览器兼容性 / 用户输入校验 / 未分类 |
| `171-180` | `donkey gui` → Electron 主进程 | 10 码 | F006 子段 1：app 生命周期 / 菜单 / 托盘 |
| `181-190` | `donkey gui` → 窗口 | 10 码 | F006 子段 2：窗口创建 / 恢复 / 聚焦 / 多窗口 |
| `191-200` | `donkey gui` → 原生胶水 | 10 码 | F006 子段 3：文件对话框 / 通知 / 剪贴板 / 系统 API |
| `201+` | v2 / v3 / v4+ 扩展 | 预留 | 留给后续版本（v2 HITL / v3 长期记忆特性 / v4 编程智能体深度适配） |

**冗余性设计原则**：
- 每个段位预留 10 个码值，吸收 v1.x 试运行期间发现的额外失败场景；
- `0` 是唯一正常返回码；任何 `> 0` 都视为失败；
- `201+` 留给未来大版本 —— 每个大版本占 100 个码值（含 1 个正常返回）；
- `donkey load` 段位起点 `11`（与 F002 域一致），9 项 hard error 占 `11-19`，`20` 留冗余；
- **warning 不计入失败**（如 `providers/*.toml` 的 `temperature` 软越界 / `openai-compatible` 的空 `api_key`）—— `--strict-warnings` 列入 v2 候选；
- **"不读 env var"立场的边界**：该立场只约束**凭据**（`api_key` 等），**网络出口**仍由本机环境决定——httpx / openai SDK 默认读取 `ALL_PROXY` / `HTTPS_PROXY` / `HTTP_PROXY` 等代理变量。donkey **不主动读、不主动写**这些变量，但必须在构造任何 client 前做一次**防御性检查**（识别 httpx 不认的 `socks://` scheme / 缺 `socksio` 扩展并降级），否则用户本机代理配置会让所有 provider 调用在**构造期**直接失败。详见 `harness/report/大模型toml参数设计.md` §9.4。

**多错误优先级**：load 检查按 §立项书 5.5.3 检查清单顺序逐项执行，遇到第一个 hard error 立即返回 —— `exit_code` 取该错误码值，**不**累积多错误码。

### 4.5 版本号规则（§立项书 1.5.2）

格式 `vx.y.z`，x / y / z 取自然数（0 到正无穷）：

- **`x`**：前端版本或 donkey 后端 LangGraph 图版本 —— LangGraph State 结构变化 / Edge 连接变化 / 节点数变化（依据调研 `LangGraph的节点到底是什么东西.md`：wrap-style 中间件**不**创建节点、node-style 中间件**每个 hook 创建 1 个节点**、无 hook 中间件**0 节点**）；`x+1` 触发条件见 §立项书 1.5.2 边界细则表；
- **`y`**：当前图版本中各节点与中间件的 id —— LangGraph 主图节点对应一个 id，中间件每个节点对应一个 id；
- **`z`**：当前节点 id 的修改次数 —— 某节点每修改一次，`z+1`。

### 4.6 验收标准（§立项书 3.2.3 + 3.5 + 9.3）

**业务验收**：
- **AC-1**：workspace 在 ≤ 100 MB 范围内，`donkey load` 通过率 100%（**不**设下限）。**通过口径 = "配置完成后的 workspace" 100% 通过**——配置完成 = 至少 1 个 provider 文件 `enabled = true` + `providers/default.toml` 填好 `default_provider` / `default_model` + 必填凭据到位；**出厂态豁免**——`donkey init` 刚生成的 workspace（26 个 provider stub 全部 `enabled = false`、零 enabled provider）**不纳入本条**，此时 `donkey load` 必然报 **exit 11**（`ProviderTomlFieldError`），且错误消息必须自带三步配置指引（详见 立项书 §3.2.3 ③ / README §3.2.1）。**豁免理由（硬）**：① 选 provider + 填凭据是**必须由用户决策**的问题（奥卡姆原则：error = 用户必须决策的硬问题），出厂态无从"通过"；② 零 enabled provider 会让**后续动态检查（模型连通性 exit 15）无模型可测** → 必须在静态检查阶段就报错，**不得降级为 warning**；
- **AC-2**：workspace 迁移（zip → 解压 → 任意路径）后 `donkey run` 不出现路径相关错误；
- **AC-3**：`donkey init` 幂等 —— 重复执行**不**破坏已存在文件（除非 `--force`）；
- **AC-4**：换 workspace 后模型 / 工具 / Skills / 提示词全部随之切换，**无需重启 donkey**；
- **AC-5**：v1 官方模板**不承诺**提供 diff 审阅 / 路径权限交互等引擎层能力。

AC-1 ~ AC-5 全部通过；三套官方模板 workspace（通用型 / 编程型 / 技能型）各跑通 1 条主流程（**官方模板须先完成 provider 配置**——即满足 AC-1 的"配置完成"口径，否则出厂态 exit 11 属预期行为）；cli / web / gui 三种客户端均通过 e2e。

**技术验收**：所有 `donkey` 子命令 exit code 与本宪法 §4.4 完全一致；引擎核心 LangGraph 图在 24 小时持续运行测试中无未捕获异常。

**技术指标**：
- load 9 项检查覆盖率 100%（§立项书 §5.5.3 清单 9 项）；
- 中间件录用率 100%（v1 承诺的 10 项全部挂载）；
- 单元测试覆盖率 ≥ 80%（`donkey.core`）。

---

## 第 5 章 关键设计决策记录（ADR）

> 本章沉淀立项书附录 F 中的 `[D-xx]` 决策；任何 `D-xx` 一经纳入**不**可删除，仅可修订。**本章是 ADR 的唯一权威源**（立项书附录 F 为镜像摘要，冲突时以本章为准）。

| 编号 | 决策 | 来源 |
|---|---|---|
| **[D-01]** | 一个 workspace 目录 = 一个 Agent；workspace 自带 manifest（仅 `name` / `created_at` / `donkey_version` **三字段**最少化 —— 原"版本号（整数 `1`）"字段已删除，见 [D-21]） | 立项书 §1.2.2 P1 |
| **[D-02]** | 依赖与配置随 workspace 走；运行数据（含 `memory/*.sqlite3`）可选择性导出——"模板身份" ≠ "必须导出" | 立项书 §1.2.2 P2 |
| **[D-03]** | workspace 记录**donkey 版本号**（`manifest.json` 的 `donkey_version` 字段），donkey 升级时提供迁移路径；`sessions_metadata.donkey_version` 列作为迁移提示。**（原"格式版本号"字段已删除 —— 见 [D-21]；若将来清单结构出现不兼容演进，MUST 重新引入显式格式版本并同步本条）** | 立项书 §1.3 |
| **[D-04]** | `cli` / `web` / `gui` 客户端**禁止**直接 import `langchain` / `langgraph` / `sqlite3`（N-04） | N-04 |
| **[D-05]** | `donkey init` 在 init 阶段**程序化构造 sqlite3 schema**（非携带二进制模板）——sessions.sqlite3 由 `SqliteSaver(conn).setup()` + donkey 自管表组成；store.sqlite3 / knowledge.sqlite3 v1 仅空文件占位，schema 推迟 v3 SqliteStore / RAG 引擎选型 | `sessions_sqlite表结构一览.md` |
| **[D-06]** | donkey 不依赖 LangSmith 任何形态（Cloud / Studio / Tracing / Deployment / Hub / `langchain[langsmith]` extras / `LANGSMITH_*` 环境变量 / `import langsmith.*`）；用 `stream_mode` + 自定义 Middleware + 标准 OpenTelemetry / Logging 替代 | N-12 + `全开源最佳实践.md` |
| **[D-07]** | Skills frontmatter 严格仅 `name` + `description` 两必填字段；不允许自定义字段（`when_to_use` / `version` / `tags` 等） | 立项书 §1.2.4 |
| **[D-08]** | 客户端三端（cli / web / gui）共用 `donkey.core.api` 库 API，不重复实现业务逻辑；开发顺序：CLI → Web → GUI | N-11 |
| **[D-09]** | Donkey v1 不依赖 `deepagents` 包（违反 N-02 / N-12 一致性）；Skills 加载器自研 | 立项书 §1.2.4 |
| **[D-10]** | workspace 内**禁止**出现 `agent.py` / `main.py` 或任何 Python 入口文件（`创建 agent 的唯一官方入口` = `donkey.core.api.create_agent`） | N-01 |
| **[D-11]** | donkey 的 `store.sqlite3` / `knowledge.sqlite3` v1 仅占位空文件——不建占位表、不挂 store、donkey 本体不读；v3 SqliteStore 由 Maintainer 启动时实施 | 立项书 §4.10 TD-02 |
| **[D-12]** | F002 load 9 项硬检查失败 → `exit code ≠ 0`，但**不修改** workspace 中任何文件（"load 失败不改 workspace"原则，N-06） | N-06 |
| **[D-13]** | 提供 fork 指南（配置边界 / 适配层说明 / 扩展点清单）——"改引擎请 fork"是 §1.1 项目身份的核心 | 立项书 §1.1 |
| **[D-14]** | **AC-1 的出厂态豁免**——`donkey load` 的"100% 通过"口径 = **配置完成后**的 workspace；`donkey init` 刚生成的出厂态（26 个 provider stub 全部 `enabled = false`、零 enabled provider）**豁免**，必然报 exit 11（`ProviderTomlFieldError`）并自带三步配置指引。**零 enabled 不得降级为 warning**：它会让后续动态检查（模型连通性 exit 15）无模型可测 → 必须在静态检查阶段就失败 | 立项书 §3.2.3 ③ + README §3.2.1 |
| **[D-15]** | **subagent 永不纳入**——宪法 N-02"agent = 人"是项目身份级哲学，**任何版本号都不为其预留功能位**（v1.5.3 版本演进规划 / §5.4 甘特图中均不得出现 subagent 交付物） | N-02 + 立项书 §1.5.3 / §4.10 TD-05 / §10.3.2 Q-05 |
| **[D-16]** | **v1 LLM 接入零自研解析层**——26 个 provider 全部复用 LangChain 官方类（唯一抽象 = `ReusableProvider` 薄包装）；`provider_id` → LangChain 类的翻译由 **donkey facade** 完成，**禁止**把 TOML 的 `default_provider` 直接喂 `init_chat_model`；donkey 在解析层的唯一职责是**配置层严格校验**（per-provider schema + F002 load 校验，exit 11 伞形）。配置布局 = `providers/` 目录 + 一 provider 一文件 + `enabled` 开关 | `大模型toml参数设计.md` §2 / §7 / §15 |
| **[D-17]** | **N-12 的边界澄清**——N-12 禁止的是 **donkey 自有代码路径**（`donkey.core` / `cli` / `web` / `gui`）对 LangSmith 任何形态的 **import 与使用**；第三方库的**传递依赖被安装到磁盘**不构成"使用"，但 MUST 在 plan 中显式登记影响面，且 MUST 由门禁实证"donkey 永不 import"（不设 `LANGSMITH_*` 等环境变量）。**动机**：F001-P2 引入 `langgraph-checkpoint-sqlite`（短期记忆库的历史表 / 写入表 MUST 由上游 saver 的实例 `setup()` 创建，donkey MUST NOT 手写 DDL），其传递依赖 `langchain-core` 会把 `langsmith` **安装到磁盘** —— 实测导入上游 saver 新增 471 个模块、langsmith 相关 **0** 个进入进程。若不加边界澄清，plan 将被迫对宪法 MUST 作单方面重新解释（违反 §6.1 宪法权威）。**影响面**：仅 N-12 / §3.2 的读法澄清，**不放宽任何 import 禁令**；受影响产物 = F001-P2 的 `plan.md`（G6 / 风险表 / R-02）、`quickstart.md` §4~§5 的 grep 自检、`spec.md` SC-017 | N-12 + F001-P2 Maintainer 裁决（2026-10-23） |
| **[D-18]** | **短期记忆库的表数量口径** —— §3.1 表格原写"单文件双表"，实为 **3 张表 + 2 个索引**：`checkpoints` / `writes`（上游 `langgraph-checkpoint-sqlite` 的 `SqliteSaver` 拥有）+ `sessions_metadata`（donkey 自管，含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 两个索引）。权威结构定义见 `harness/report/sessions_sqlite表结构一览.md` §2.2 与 §7（5 项健康断言）。**本条只澄清 §3.1 表格措辞，不放宽任何约束**：F002-P2 的 `SqliteSchemaError`（exit 16）5 项断言口径不变。**同源措辞已一并同步**（原「单文件双表」在 3 处遗留，现全部改为「单文件三表两索引」）：① 本宪法 §3.1.1 首条的标签；② 立项书 §4.6.3「模板预创建」行与「`sessions.sqlite3` 单文件三表两索引设计」小节（含其「承载三张表」「三张表互不干扰」两句）；③ 宪法 §3.1 表格（本条前半段所述）。各处**表数 / 索引数 / 字段 / 断言口径逐字未动**，仅标签与「两套表 → 三张表」的计数措辞对齐 | 立项书 §5.5.3 + `sessions_sqlite表结构一览.md` §2.2 / §7 |
| **[D-19]** | **N-01 的边界澄清 —— "Python 入口文件"指*智能体入口***：N-01 / D-10 / §2.6 / §3.2 所禁的"任何 Python 入口文件"，指**能直接启动智能体的文件**（`agent.py` / `main.py` 这类）；Skill **第三层附属资源目录**（`skills/<name>/scripts/` 等）下的**普通用户脚本**（如 `skills/example/scripts/example.py`）**不属**该范畴 —— 它是**用户代码路径**下的普通脚本，唯一用途是"被内置命令工具调用并打印一行输出"，智能体的唯一官方入口仍是 `donkey.core.api.create_agent`。**动机**：F001-P3 交付的示例 Skill 需以"第三层可执行脚本"展示"模型如何按需调用附属资源"，该脚本必须保留 `if __name__ == "__main__": sys.exit(main())` 入口块（与源提示词模板逐字一致）；若按 N-01 的字面口径禁止一切入口块，则该示例无法演示"被调用"这一语义，或必须偏离源模板正文。**影响评估**：仅 F001-P3（`specs/001-donkey-init-workspace/phase-3-builtin-tools/`）的 `spec.md` FR-050 / Edge Cases「阶段边界类」/ Phase 元信息「治理依据」行、`plan.md` 的 G14 与 Complexity Tracking、`tasks.md` 的 T016 / T046 与 T094 的持久不变量口径 —— 均为**登记与引用**层面，**不改动任何需求层语义**（入口块仍 MUST 保留）；工作区内 MUST NOT 出现 `agent.py` / `main.py` 这条**持久不变量**不变。**迁移路径**：本条经 §6.3 **例外 E-02** 临时授权；E-02 到期（见其过期时间）时须正式纳入宪法（修订本条或新增 D-xx），或移除该演示脚本的入口块 —— 两者择一，由 Maintainer 裁决。**✅ 已正式化（2026-10-23，Maintainer 裁决「正式纳入宪法」）**：E-02 到期时选**第一条**路径 —— 本条**自此即为宪法正式条款，不再依赖任何临时例外**（E-02 转为历史登记，临时授权阶段结束）；第二条路径（移除演示脚本的入口块）**未被采用**（会与 F001-P3 `spec.md` FR-050「MUST NOT 被改写成无入口块的形态」冲突）。**正式化后本条的口径一字未改**：入口块仍 MUST 保留、三条范围边界（MUST NOT 位于 `tools/` 目录 / MUST NOT 命名为 `agent.py` · `main.py` / MUST NOT 承担"创建智能体"职责）仍适用、"工作区内 MUST NOT 出现 `agent.py` / `main.py`"这条持久不变量仍成立 | 立项书 §3.4 + N-01 / D-10 的立法目的 + F001-P3 Maintainer 裁决（2026-10-23） |
| **[D-20]** | **元信息命令豁免 F 编号登记** —— 版本号查询不可缺少但不属于核心功能，套用 F 编号会污染 §4.2 的"核心功能"语义与 §4.5 的图版本口径。**影响面**：宪法 §4.2 新增「元信息命令豁免」小节（§4.2.1）+ §4.3 的**两处**限定语（「（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）」+ v1 baseline 句的「**（元信息命令按 §4.2 豁免）**」）+ `specs/001-donkey-init-workspace/phase-4-cli-version/` 全套（F001-P4 `cli_version` Phase）。**不变项**：F001-P1 / P2 / P3 的 FR / SC 编号与断言**一律不动**；§4.3 的规则 A / 规则 B 两张表逐字未动。**迁移路径**：无（纯新增能力，不改变任何既有行为）。**边界**：元信息命令一旦开始承载可失败的业务能力（需要 Error class / exit code 段位 / 库 API），MUST 先按 §6.2 取得 F 编号 | 立项书 §1.5.2 + §3.2.1 + F001-P4 Maintainer 裁决（2026-10-30） |
| **[D-21]** | **工作区清单删除"版本号"字段、`donkey_version` 改动态取值** —— 原清单的 `"version": 1`（清单**格式版本**，整数）与 `donkey_version`（donkey **软件版本**，字符串）并排，读作"两个打架的版本号"；而前者**全仓无人读取**（`init.py` 读的是**包内模板清单**的同名 `version`，是另一个文件、另一个含义，且**被强制校验**）。真正被使用的是 `donkey_version` —— 它是 F002 `donkey load` 迁移提示的唯一依据。**影响面**：① 宪法 D-01（四字段 → **三字段**）与 D-03（"格式版本号" → "**donkey 版本号**"，并保留"将来结构不兼容演进时 MUST 重新引入显式格式版本"的兜底）；② `donkey/core/workspace/manifest.py`（删 `_MANIFEST_VERSION` 与 `"version"` 字段；`donkey_version` 改为 `donkey.core.version.resolve_version()` **动态取值**）；③ `tests/unit/test_template_skeleton.py` 的**清单字段断言**（4 处断言逐条改写，见该文件`test_manifest_field_minimal` 的「断言改写登记」注记）与 F001-P2 spec 的 FR-019 / FR-021；④ `harness/features/立项书.md` §1.3 目标 5 / Q-07 / §4.6.1 字段描述；⑤ `harness/features/README.md` §5 的 **F002 必读备忘录**。**不变项**：F001-P1 / P2 / P3 的 **FR / SC 编号**一律不动；仅上述**断言**按宪法 §4.3 的"显式登记改写"机制改写；**包内模板清单** `donkey/core/workspace/templates/manifest.json` 的 `version` 字段**逐字不动**（它是**被强制校验**的真实格式契约，与本条无关）。**动机**：① 消除"两个 version 并排"的阅读歧义；② 修掉硬编码的真实缺陷 —— 版本 bump 后**新建**的工作区仍记旧版本号，会让 F002 的迁移提示**误判**工作区陈旧（F001-P2 FR-021 自身已预留该演进路径："将来若改为动态获取，MUST 使用包元数据查询方式"；其"循环依赖风险"的理由因 `donkey.core.version` 的诞生而**已不复存在** —— `donkey/__init__.py` 零 import）。**迁移路径**：存量工作区的清单里可能仍带 `"version": 1` —— 读取端原样返回字典、**不解析**该键，故**不影响任何读路径**；`donkey init --force` 重写时该键被自然清除（归一到三字段形态）。**边界**：删除格式版本号意味着**清单结构失去显式的演进标记** —— 故 D-03 与 F002 备忘录 MUST 写明：将来若清单结构出现**不兼容**演进（如 F002 引入 workspace 快照），MUST **重新引入**显式格式版本并同步 D-03 | 立项书 §1.2.2 P1 + §1.3 目标 5 + F001-P2 FR-019 / FR-021 + F001-P4 Maintainer 裁决（2026-10-30） |
| **[D-22]** | **`donkey init` 的执行报告改为「摘要 + 逐项明细」，计数按「对象 × 动作」分解** —— 原摘要的 `templates=54` 与 `created=48` 是**两个口径**（清单条目总数 vs 文件型条目数），差额 6 个目录条目**在输出里不可见**，用户无法自行对账；且 `created` 在 `--force` 下把**覆盖**并入**新建**，两个动作不可区分。**影响面**：① **库 API 契约 v2** —— `InitResult` 新增 `files_overwritten` / `dirs_created` / `dirs_skipped` / `items` 四个字段（v1 的六个字段**逐字保留、顺序不变**），并引入 `INIT_RESULT_CONTRACT_VERSION = 2`（F001-P1 FR-006 要求"字段语义不得在本阶段之后**无版本号**变更"）；② `core/workspace/init.py` 的 `render_templates` 由返回 `(files_created, files_skipped)` 改为返回**逐项明细** `list[InitItem]`（`path` / `kind` / `action`），各计数由明细**投影**而来（**单一真相源**）；③ `cli/cli_client.py` 的摘要扩为**九个字段**并新增**逐项明细**（每条目一行，走 stdout）；④ F001-P1 / P2 / P3 的**既有断言改写**（P1 单测 1 处、P2 单测 8 处 + e2e 2 处、P3 单测 1 处 + e2e 3 处），逐条登记在各文件内。**不变项**：F001-P1 / P2 / P3 的 **FR / SC 编号**一律不动；`donkey init` 的**参数面**（仅 `path` + `--force`）不动 —— 故明细**恒定输出**、MUST NOT 新增 `--quiet` / `--verbose`。**动机**：① 让输出的各数**算术自洽**（`templates` == 五类计数之和）；② 让"这次到底动了哪些文件"**可见**（逐项明细）；③ 让"新建 / 覆盖 / 跳过"三个动作**分列**（`--force` 的 47 个是**覆盖**而非新建）。**迁移路径**：解析摘要的脚本 MUST 由 `created=` / `skipped=` 改读 `files_created=` / `files_skipped=`；`--force` 情形的 `files_created` 由 47 归位为 **0**（覆盖另计入 `files_overwritten`）—— 这是 FR-006 字面口径「本次新建文件数」的**归位**，非新语义。**边界**：目录条目**永不**"覆盖"（既有目录一律保留不动），故只有 `dirs_created` / `dirs_skipped` 两态；目录的"新建/跳过"以**本次运行开始前**的存在状态判定（否则会被其子条目的父目录创建提前建出，导致结果依赖清单顺序） | 立项书 §4.6.1 + F001-P1 FR-006 / FR-003 + F001-P3 FR-068 改写机制 + Maintainer 裁决（2026-10-30） |

---

## Governance

### 6.1 宪法权威

- 本宪法**凌驾**于 donkey 仓库内其他实践之上；
- 与本宪法冲突的代码 / 文档 / 流程一律无效；
- 任何 spec / plan / tasks / 代码 / 文档提交前**必须**对照 §1.2 N-01 ~ N-12 + §2 核心设计原则 + §3 不可妥协约束 + §4 开发流程自检；Phase / 段位 / 子段 / Error class 4 术语严格按 §4.3 + README §1.5 分层使用。

### 6.2 修订流程

宪法修订必须满足：
1. **明确动机**：写在 ADR 中，作为变更记录；
2. **Maintainer 批准**：仅 Maintainer（yangjiacheng）有最终批准权；
3. **影响评估**：列出受影响的 spec / plan / tasks / 代码 / 文档清单；
4. **迁移计划**：若影响现有用户，须附迁移路径；
5. **记录修订**：修订的动机与结论写入第 5 章 ADR（`[D-xx]`，编号只增不删、不可删除既有条目）；**本宪法不设版本号**——它在 v1 开发期随时可能修订，版本化由 ADR 编号 + git 历史承担。

### 6.3 例外

任何对本宪法条款的临时例外（如临时启用 `ShellToolMiddleware` 做实验）必须：
1. 由 Maintainer 显式批准；
2. 在 PR 描述中显式声明例外范围与过期时间；
3. 在过期前完成合规修复或正式纳入宪法。

> **例外 E-01（2026-10-21，Maintainer 批准；2026-10-23 范围扩展至 F001-P2，Maintainer 批准）**：F001-P1 与 F001-P2 **均不**交付 `.github/workflows/ci.yml`。
> - **范围**：仅 F001-P1（`cli_validation` Phase）**与 F001-P2（`template_skeleton` Phase）**；`donkey init` 的 CI 工作流文件推迟到仓库级 CI 落地时创建。
>   （2026-10-23 扩展说明：F001-P2 引入第一个运行期依赖与 14 个黑盒验收场景，测试面进一步扩大，CI 文件仍属仓库级资产；
>   本次扩展**不改变**过期时间、**不改变**替代保障清单、**不新增**任何豁免条款。）
> - **理由**：CI 工作流文件属**仓库级资产**（宪法 §4.1 的项目级方法论），非单 Phase 交付物；
>   且 F001-P1 落地时仓库仅有 1 个 Phase 的测试面，首次落地 CI 的时序风险高于收益。
>   替代保障：plan G5 记录 CI 最小内容骨架（`pytest tests/` + `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80`
>   + `ruff check donkey/ tests/` + `mypy donkey/ tests/`），本 Phase 的完成证据以本地命令清单为准。
> - **过期时间**：F001-P3（`builtin_tools`）结束前 —— 最迟在该 Phase 内交付 `.github/workflows/ci.yml`，
>   或由 Maintainer 显式决定转为正式纳入宪法。
> - **登记位置**：F001-P1 的 `plan.md` G5 与 F001-P2 的 `plan.md` G5（判定保持「⚠️ 部分」，依据列补注本例外）；
>   `research.md` R-08（结论不变，仅记录例外已登记）；`harness/features/README.md` §4.3（登记范围扩展）；
>   **到期闭合登记**：`harness/features/feature001_phase003_builtin_tools.md` §6.16（F001-P3 的
>   **CI 工作流交付断言** —— 本 Phase 采用「P3 内交付 `.github/workflows/ci.yml`」的处置，
>   而非「转为正式纳入宪法」；该断言 MUST 与 15 个场景断言同时满足，F001-P3 方可收尾）。
> - **✅ 到期闭合（2026-10-23 · F001-P3 内交付，Maintainer 裁决）**：本例外走的是 §6.3 第 3 条的
>   **「完成合规修复」**路径 —— F001-P3 已交付 `.github/workflows/ci.yml`（含 `pytest tests/` +
>   `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` + `ruff check donkey/ tests/` +
>   `mypy donkey/ tests/` 四类命令，Python 3.11 / 3.12 矩阵，覆盖率用**独立命令**度量）。
>   故本临时例外**随交付而终止**，**不转为正式条款**（CI 工作流本属仓库级资产，宪法无须为其设立常设条款）。
>   闭合证据：F001-P3 的 `tests/e2e/phase/verify_phase_f001_p3.py` 场景 16（CI 交付检查断言）——
>   该断言与 15 个功能场景断言**同时**满足，F001-P3 方可收尾。
>
> **例外 E-02（2026-10-23，Maintainer 批准；2026-10-23 到期正式纳入宪法，Maintainer 裁决）**：F001-P3（`builtin_tools` Phase）交付的示例 Skill **第三层附属资源目录**下的**普通演示脚本**（如 `skills/example/scripts/example.py`）**不属** N-01 / D-10 / §2.6 / §3.2 所禁的"Python 入口文件"。
> - **范围**：仅限 **Skill 第三层附属资源目录**（`skills/<name>/scripts/` 等）下的**普通脚本**；该脚本 MUST NOT 位于 `tools/` 目录（否则会被工具扫描器当作工具模块）、MUST NOT 命名为 `agent.py` / `main.py`、MUST NOT 承担"创建智能体"职责（智能体的唯一官方入口仍是 `donkey.core.api.create_agent`）。
> - **理由**：N-01 的立法目的是"禁止工作区出现**智能体入口**，避免用户误以为可直接运行工作区里的 Python 文件来启动智能体"；Skill 第三层的演示脚本是**用户代码路径的普通脚本**，唯一用途是"被内置命令工具调用并打印一行输出"，与智能体入口无关（边界澄清见 §5 章 [D-19]）。
> - **替代保障**：① 该脚本 MUST 仅演示"被调用后打印一行输出"这一最小行为；② 工作区内 MUST NOT 出现 `agent.py` / `main.py` 这条**持久不变量**不变（F001-P2 的既有断言 MUST 保留）；③ 智能体入口的唯一性不变。
> - **过期时间**：F001-P3（`builtin_tools`）结束前 —— 最迟在该 Phase 内**正式纳入宪法**（修订 §5 章 [D-19] 或新增 D-xx），或移除该演示脚本的入口块；二者择一，由 Maintainer 裁决。
> - **登记位置**：§5 章 [D-19]；F001-P3 的 `spec.md` FR-050（**强制引用**本例外，MUST NOT 自设豁免）、`plan.md` G14 + Complexity Tracking、`tasks.md` T016 / T046。
> - **✅ 到期处置（2026-10-23，Maintainer 裁决「正式纳入宪法」）**：本例外选**第一条**路径 —— 其口径
>   **正式纳入宪法**，载体为 §5 章 **[D-19]**（该条的「迁移路径」段已相应改为正式化记录）。
>   故 **E-02 作为"临时授权"不再生效**；本条目转为**历史登记**保留在 §6.3，以维持 F001-P3
>   已冻结文档（`spec.md` FR-050 / `plan.md` G14 / `tasks.md` T016 · T046）中对"宪法 §6.3 例外 E-02
>   + §5 章 [D-19]"的引用**不悬空**。**第二条路径（移除演示脚本的入口块）未被采用** ——
>   它会与 F001-P3 `spec.md` FR-050「MUST NOT 被改写成无入口块的形态」直接冲突。
>   **工作区内的可观测行为不变**：入口块仍保留、仍受 D-19 的三条范围边界约束、
>   "工作区内 MUST NOT 出现 `agent.py` / `main.py`"这条持久不变量不变。

---

## 第 7 章 指南文档

- 运行时开发指引：`harness/features/立项书.md`（本宪法的唯一源文档）；
- Phase 进度与映射总表：`harness/features/README.md`（§3 一览总表 / §4-§9 详细设计 / §11 段位速查表 / §12 提示词文件落地约定，**含 §1.5 4 术语表**——Phase / 段位 / 子段 / Error class 严格分层在此表定义）；
- Speckit 工作流：`harness/prompt/speckit.md`；
- **LLM 配置 schema 权威**：`harness/report/大模型toml参数设计.md`（`providers/` 目录布局 / 26 家白名单 / per-provider 字段 / `enabled` 开关 / 三档鉴权 / exit 11 校验清单）；
- 中间件速查：`harness/report/LangChain内置中间件速查表.md`；
- Skills 自研依据：`harness/report/关于subagent的实现方式.md`、`harness/report/内置工具应该自己实现还是调用中间件.md`；
- 长期记忆依据（含 `sessions_metadata` 表设计蓝本）：`harness/report/Saver和Store.md`；
- 选型依据：`harness/report/LangChain与DeepAgents的选择.md`；
- 节点 / 中间件关系依据：`harness/report/LangGraph的节点到底是什么东西.md`；
- 开源合规：`harness/report/全开源最佳实践.md`。
