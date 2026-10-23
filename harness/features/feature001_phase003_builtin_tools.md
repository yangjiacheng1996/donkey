# F001-P3 `builtin_tools` —— `/speckit.specify` 开发提示词

> 本文件是 `donkey init` F001 第 3 个 Phase（也是 F001 的最后一个 Phase）的 **spec 输入**。把它整体作为参数传入 `/speckit.specify` 命令即可生成 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md`。`/speckit.specify` 完成后，本 Phase 闭包即代表 F001 (`donkey init`) 整体完成。
>
> **自包含契约**：本提示词包含完整的 Phase 范围、入口条件、退出条件、约束、实现要点；执行 `/speckit.specify` 时**无需**翻阅 `harness/features/` 内其他 F001 兄弟 Phase 提示词文件、也**无需**翻阅立项书 / README / 调研报告——所有必要信息均已内化在本文件内。本文件对其他 F001 Phase 的引用仅限于"Phase 标识符"层面（例如"由 F001-P1 提供" / "由 F001-P2 实现"），**不**复制其 spec 内容——但会在本文件中以独立小节复述必要的接口契约（如 `init_workspace_inner` 路径、manifest 条目追加方式、模板清单 schema），避免跨文件依赖。
>
> 本提示词**不**描述 `/speckit.plan` / `/speckit.tasks` / `/speckit.implement` / `/speckit.analyze` 的细节——那些命令是 spec 的下游延伸，由 Speckit 工作流按 `harness/prompt/speckit.md` 串行处理即可，本 Phase 不提前撰写。

---

## 0. Phase 元信息

| 字段 | 值 |
|---|---|
| **Feature 编号** | F001（`donkey init`） |
| **核心库 API** | `core.api.init_workspace(path, name=None, force=False) -> InitResult` |
| **Phase 编号** | F001-P3 |
| **Phase 英文名** | `builtin_tools` |
| **Phase 中文描述** | 幂等生成 3 个内置 `@tool`（filesystem / commandline / webfetch）+ **1 个变更记录契约库（`tools/changes.py`，diff-ready 地基）** + Skills example 三层 + `tools/` 支撑文件 + 端到端集成预演 |
| **段位** | F001 段位 1–10；本 Phase 占用 F001 子段 3（exit 4） |
| **已用 exit code** | 4（`BuiltinToolGenerationError`） |
| **预留 exit code** | 5–10（留给 v1.x 试运行期新错误） |
| **本 Phase 不占用的 exit code** | 1 / 2（F001-P1）、3（F001-P2）、5–10 |
| **对应验收脚本** | `tests/e2e/phase/verify_phase_f001_p3.py` |
| **闭环复杂度（断言数）** | 中（16 断言） |
| **变更记录契约版本** | `CHANGE_RECORD_VERSION = 1`（见 §2.9 —— v4 diff 展示的接入面） |
| **准入条件** | F001-P2 退出条件全部满足 + F001-P2 抛出的 `TemplateGenerationError` 已通过单元测试 |

---

## 1. Phase 目标声明（一句话）

实现 `donkey init` 的 3 个内置 `@tool` 文件生成（`tools/filesystem.py` 含 7 个工具函数 / `tools/commandline.py` 含 1 个工具函数 / `tools/webfetch.py` 含 1 个工具函数）+ **1 个变更记录契约库 `tools/changes.py`（非 `@tool`，为 v4 diff 展示铺垫的"变更原材料"产地 —— 见 §2.9）** + Skills example 三层示例（Level 1 frontmatter + Level 2 主体 + Level 3 reference/scripts/templates 目录）+ `tools/` 支撑文件（`tools/__init__.py` / `tools/README.md`），并把上述条目追加到模板清单。**所有改文件的 `@tool` 一律返回统一的"变更记录"（change record）：原子写 + 旧内容 hash + unified diff + 乐观锁 + dry_run 预览**（§2.9 四条硬规则 R-D1 ~ R-D4）。本 Phase **不**引入任何 LangChain 中间件（F004 域），**不**做 F002 静态检查，**不**构造 sqlite3 schema（F001-P2 域），**不**调用 `init_chat_model`（F002 域），**不**实现 diff 审阅 UI / 审批 / 回滚（引擎层 v4 或 fork 能力，AC-5）。

---

## 2. 背景与设计意图（实现者必须先理解）

### 2.1 项目身份

donkey 是一个**智能体材料层的可移植运行时引擎**——workspace 目录 = 智能体的全部材料层（人格、知识、手脚、大脑），用户可任意替换；Agent Loop、中间件挂载、客户端渲染、上下文治理等由引擎统一实现，不开放配置；改引擎层需 fork 仓库。

### 2.2 两层模型

- **材料层**（workspace 层）：Instructions / Model / Tools / Skills，由用户定义（一个目录），可移植性高；
- **引擎层**（harness / runtime 层）：Agent Loop、中间件链、客户端渲染、上下文治理，由 `donkey` 代码定义，**无任何配置项**。

### 2.3 workspace 原子性原则

- 一个 workspace 目录 = 一个 Agent；
- workspace 自带 manifest；
- 依赖与配置随 workspace 走；运行数据可选择性导出；
- workspace 有格式版本号。

### 2.4 Skills 三层渐进披露原则（核心）

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

### 2.5 内置 `@tool` 与中间件职责正交原则（核心）

| 工具来源 | 职责 | 调用场景 |
|---|---|---|
| `FilesystemFileSearchMiddleware`（引擎侧 LangChain 中间件） | `glob_search` + `grep_search`（ripgrep 后端） | "找文件"、"找内容" |
| `tools/filesystem.py`（workspace 内置 `@tool`，材料层） | 文件操作：read / write / copy / move / delete / list_dir / stat；**改文件的工具一律返回统一"变更记录"**（§2.9） | "读这个文件"、"改那个文件" |
| `tools/commandline.py`（workspace 内置 `@tool`） | `run_shell` —— `subprocess.run([...], shell=False, timeout=...)`；**每次新建进程**，不走持久 shell | 命令执行 |
| `tools/webfetch.py`（workspace 内置 `@tool`） | `fetch_url` —— HTTP GET/POST + timeout；不持久化 cookies | HTTP 拉取 |
| `tools/changes.py`（workspace 内置**契约库**，材料层，**非 `@tool`**） | 变更记录契约：原子写 + hash + unified diff + 乐观锁；**所有改文件的工具（含用户自写工具）的共同底座** | 不直接被模型调用；被 `tools/filesystem.py` 与用户工具 import |

**职责正交不重叠**：内置 3 个 `@tool` + `FilesystemFileSearchMiddleware` 中间件共同构成 Skill Level 3 的完整访问通道，按场景选用。

### 2.6 `tools/filesystem.py` 不含 glob/grep 的原因

`glob_search` / `grep_search` 由 `FilesystemFileSearchMiddleware`（LangChain 中间件）接管——它是纯 LangChain（不依赖 deepagents）+ ripgrep 后端高效。`tools/filesystem.py` 仅做"读 / 写 / 复制 / 移动 / 删除 / 列目录 / stat"这些"对单一文件或目录的精确操作"。"找文件 / 找内容"属于中间件职责，**禁止**在 `tools/filesystem.py` 内实现。

### 2.7 `commandline.py` 不走持久 shell 的原因

`ShellToolMiddleware` 的持久 shell session 与未来 v2 HITL（interrupt）冲突——persistent shell 不支持 interrupt。本项目**禁用** `ShellToolMiddleware`，由 `tools/commandline.py` 用 `subprocess.run([...], shell=False, timeout=...)` 替代：每次新进程 + 显式 timeout 掐断 + 显式命令数组（不走 shell 字符串，从源头避免 shell injection + HITL 冲突）。

### 2.8 `donkey init` 幂等性

继续遵循 F001-P2 已确立的 4 场景幂等性：本 Phase 生成的 builtin tool + Skills example 模板条目均纳入 manifest 清单，遵循"无则增 / 已存在跳过 / --force 重置"三规则；用户自定义的 `tools/my_tool.py`（不在清单）**永远不动**。

### 2.9 内置工具的 diff-ready 契约（向后兼容设计——为 v4 "diff 展示" 铺垫）

**动机（为什么现在就要定形状）**：

- 立项书 §1.5.3 版本演进规划把 **"diff 展示"** 列入 **v4**（"v4 编程智能体深度适配：增加 project 选择、相对路径系统提示词、diff 展示、分支选择"）——diff 一定会回来；
- 立项书 §1.2.3 已经写死了 diff 的闭环形态：**"工具写入 → 拦截变更 → 生成 diff → 前端展示 / 人工确认 → 回写或回滚"**；
- 但 v1 **不承诺** diff 审阅（AC-5 / TD-04"缺 diff 中间件 → 不纳入（需 fork）"）——**diff 的计算 / 展示 / 审批 / 回滚属于引擎层**；v1 材料层只负责把"改了什么"**完整、不可丢失**地交出去。

**结论**：材料层（本 Phase 生成的 3 个 `@tool` + 契约库 `tools/changes.py`）负责**产出变更原材料**；引擎层（v4 或 fork）负责**渲染 diff / 人工确认 / 回滚**。今天在材料层做的每一处设计，都必须是"未来能接上 diff"的形状——**这是本 Phase 三大内置工具的第一性约束，优先于"接口简洁"**。

**四条硬规则**（`tools/filesystem.py` 的所有写类工具必须遵守）：

| 编号 | 规则 | 落地方式 | 若违反的后果 |
|---|---|---|---|
| **R-D1** | **原子写** | `tools.changes.atomic_write_bytes`：同目录临时文件 + `os.replace`（POSIX / Windows 均原子） | 写到一半失败 = 旧文件被截成半截 → diff 的"前"半边永久丢失，且无法回滚 |
| **R-D2** | **不丢旧内容** | 写前读出旧字节 → 记 `previous_hash` / `previous_size`；`include_previous=True` 时附带旧正文 | 覆盖后旧内容不可得 → 引擎层无从生成 diff / 无从回滚 |
| **R-D3** | **可预览** | `dry_run=True` 只算 diff、不落盘 | 模型无法"先看 diff 再决定写不写"——diff 审阅的基本交互缺失 |
| **R-D4** | **并发安全** | `expected_hash` 乐观锁：写入方声明"我读到的版本"，不匹配则 `FileChangedError` | 人类 / 另一个 agent 在中途改了文件 → 被静默覆盖（lost update） |

> **R-D1 已有项目内先例**：`harness/report/大模型toml参数设计.md §12.2` 的"批量保存"已定规矩——"每个文件原子写入：写临时文件 + `os.replace`"。本 Phase 把它推广到**所有**材料层文件写入。

**变更记录（change record）schema**——`tools.changes.build_change_record` 的输出（`CHANGE_RECORD_VERSION = 1`）：

| 字段 | 类型 | 必现 | 含义 |
|---|---|---|---|
| `version` | int | ✓ | 契约版本（当前 `1`）；消费方按它分派，不靠猜字段 |
| `action` | str | ✓ | `create` / `update` / `delete` / `copy` / `move` |
| `path` | str | ✓ | 变更目标的**绝对**路径 |
| `rel_path` | str | ✓ | 相对 workspace 根的 POSIX 路径（diff 头用 `a/<rel_path>` / `b/<rel_path>`——workspace 可搬移，路径必须可移植） |
| `previous_exists` | bool | ✓ | 变更前文件是否存在 |
| `previous_size` | int | ✓ | 变更前字节数（不存在 = 0） |
| `previous_hash` | str \| None | ✓ | 变更前内容的 `sha256:<hex>`（不存在 = `null`） |
| `new_size` | int | ✓ | 变更后字节数（删除后 = 0） |
| `new_hash` | str \| None | ✓ | 变更后内容的 `sha256:<hex>`（删除后 = `null`） |
| `unified_diff` | str | ✓ | 标准 unified diff 文本（`--- a/…` / `+++ b/…` / `@@ … @@`） |
| `diff_truncated` | bool | ✓ | diff 超过 64 KiB 时截断（超长 diff 不进模型上下文） |
| `applied` | bool | ✓ | 是否真的落盘（`dry_run` = `false`） |
| `src` / `src_rel_path` | str | 仅 `copy` / `move` | 源路径 |
| `previous_content` | str | 仅 `include_previous=True` 且旧正文 ≤ 256 KiB | 旧正文全文（回滚用） |
| `previous_content_truncated` | bool | 仅 `include_previous=True` 且旧正文过大 | 旧正文被省略时为 `true` |

> **必现基线 = 12 个字段**：`version` / `action` / `path` / `rel_path` / `previous_exists` / `previous_size` / `previous_hash` / `new_size` / `new_hash` / `unified_diff` / `diff_truncated` / `applied`。**任何 action 下这 12 个字段都必须在**——单测按"基线键集合"断言（§4.8 `test_changes_contract_version_stable`）；条件字段按上文规则出现/缺席。

**向后兼容三原则（binding on future changes）**：

1. **只增不改（additive-only）**：新字段可加；已有字段的**名字与语义冻结**。消费方**必须**忽略不认识的字段。
2. **版本分派**：`CHANGE_RECORD_VERSION` 只在**破坏性**变更时 +1；消费方按 `version` 分派，禁止"靠字段是否存在猜版本"。
3. **单一来源**：任何改文件的工具（含用户自写工具）**必须**复用 `tools/changes.py`，禁止自造第二套 hash / diff 逻辑——否则同一 workspace 内出现两种变更记录格式，引擎层无法统一渲染。

**已知缺口（v1 明确不补，v4 用快照对账）**：

| 缺口 | 后果 | v4 的兜底 |
|---|---|---|
| `run_shell` 造成的文件副作用**不**进变更记录（shell 绕过 `@tool` 写路径） | 引擎层看到的"已记录变更"少于"实际变更" | 引擎层在审阅前做一次 workspace 快照（hash 扫描）与变更记录对账 |
| 目录删除按**目录粒度**记录（不枚举内部逐文件 diff） | 删目录时只得到一条目录级记录 | 同上（快照对账可还原被删文件清单） |
| 越过 workspace 根的绝对路径写入 | 变更记录里的 `path` 指向 workspace 之外 | 引擎层按 `rel_path` 判定是否在审阅范围内（越界记录单独标注） |

> **不违反 AC-5**：AC-5 禁的是"workspace 内出现 diff 审阅入口（`agent.py` / `main.py` 之类）"，**不是**禁工具返回值里带 diff 文本。材料层交出 diff 文本 ≠ 实现 diff 审阅流程。

---

## 3. 入口条件（Entry Gate）

### 3.1 前置 Phase 已完成

- **F001-P1 (`cli_validation`) 已完成**：7 个 verify 断言（场景 1 / 2 / 3 / 4 / 5 / 6 / 7）全部 PASS；`PathNotFoundError` / `PathPermissionError` 单测全绿。
- **F001-P2 (`template_skeleton`) 已完成**：14 个 verify 断言（场景 1 ~ 14）全部 PASS；`TemplateGenerationError` 单测全绿（`tests/unit/test_template_skeleton.py` 至少 14 个用例）。

### 3.2 本 Phase 不重复实现的接口契约（来自 F001-P1 / F001-P2，本 Phase 直接复用）

| 接口 | 来源 Phase | F001-P3 调用契约（**仅引用签名与行为，不复述实现**） |
|---|---|---|
| `validate_init_request(path, name, force) -> tuple[Path, str, bool]` | F001-P2 `core/workspace/init.py` | 由 `init_workspace_inner` 入口首行调用；返回 `(abs_path, resolved_name, force)` |
| `render_templates(workspace_path, name, force, manifest_entries)` | F001-P2 `core/workspace/init.py` | 由 `init_workspace_inner` 顺序调用；遍历 manifest 条目按 format 分派（text 类复制 .txt 源；sqlite3 类调对应 builder；directory 类 mkdir）；返回 `(files_created, files_skipped)` |
| `init_workspace_inner(path, name, force) -> tuple[Path, str, bool, int, int, int]` | F001-P2 `core/workspace/init.py` | 由 `init_workspace` 函数体首行调用；串行 `validate_init_request` → `load_template_manifest` → `render_templates` → `write_workspace_manifest`；返回 6 元组 `(abs_path, resolved_name, force, files_created, files_skipped, templates_loaded)` |
| `init_workspace(path, name=None, force=False) -> InitResult` | F001-P2 `core/api.py` | CLI 入口调用；函数体已由 F001-P2 补齐 |
| `_EXCEPTION_TO_EXIT_CODE` 异常映射表 | F001-P1 / F001-P2 `cli/cli_client.py` | 已映射 `PathNotFoundError` / `PathPermissionError` / `TemplateGenerationError`；本 Phase 在表**追加** 1 行：`BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION` |
| `templates/manifest.json` manifest 清单 | F001-P1 初始化 schema（3 条）+ F001-P2 已含 46 条目 | 本 Phase **追加** 8 条新 entry（`tools/__init__.py` + `tools/changes.py` + 3 个内置 tool + 3 个 Skills Level 3 示例）→ **累计 54 条**；追加方式是"在原 `entries` 数组末尾 push"，**不**修改 F001-P2 已有条目 |
| `templates/{entry['path']}.txt` 模板源 | F001-P2 已有 37 个 .txt 源（P1 的 3 个 + P2 的 34 个） | 本 Phase **新增** 8 个 .txt（`tools/__init__.py.txt` + `tools/changes.py.txt` + 3 个内置 tool + 3 个 Skills Level 3）+ **覆盖** 1 个已有 .txt（`skills/example/SKILL.md.txt` 补完整 Level 2 正文） |

### 3.3 提前就绪的模块资产（Phase 启动时已存在）

| 资产 | 路径 | 内容约束 |
|---|---|---|
| **核心库 API** | `donkey/core/api.py` | `init_workspace` 函数体已补齐（F001-P2）；本 Phase **不**修改 api.py。 |
| **核心逻辑骨架** | `donkey/core/workspace/init.py` | 已有 `validate_init_request` / `render_templates` / `init_workspace_inner`（F001-P2）；本 Phase **不**修改 init.py——复用 `render_templates` 即可。 |
| **CLI 入口** | `donkey/cli/cli_client.py` | argparse + 异常处理已就位；本 Phase **追加** 1 行异常映射：`BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION`。 |
| **exit code 常量** | `donkey/core/exit_codes.py` | 已定义 F001 已用码（0 / 1 / 2 / 3）；本 Phase **追加** `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4`。 |
| **异常类层次** | `donkey/core/exceptions.py` | 已定义 `DonkeyError` / `WorkspaceInitError` / `PathNotFoundError` / `PathPermissionError` / `TemplateGenerationError`；本 Phase **追加** `BuiltinToolGenerationError(WorkspaceInitError)` —— 对应 exit code 4。 |
| **workspace manifest** | `donkey/core/workspace/manifest.py` | 已实现 `write_workspace_manifest` / `read_workspace_manifest` / `ensure_workspace_manifest`（F001-P2）。本 Phase **不**修改。 |
| **模板清单** | `donkey/core/workspace/templates/manifest.json` | 已含 F001-P2 模板条目（instruction.md / `providers/`（default.toml + README.md + 26 个 stub）/ mcp/mcp.json / skills/example/SKILL.md / README 系列 / .gitignore）。本 Phase **追加** 8 个新条目（详见 §4.7）。 |
| **模板源文件** | `donkey/core/workspace/templates/{entry['path']}.txt` | 已含 F001-P2 的 37 个 .txt 源文件。**源文件路径规则**：`templates/{entry['path']}.txt`（与 manifest entry 的 `path` 一一对应）。本 Phase **新增** 8 个 .txt（`tools/__init__.py.txt` + `tools/changes.py.txt` + 3 个内置 tool + 3 个 Skills Level 3）+ **覆盖** `skills/example/SKILL.md.txt`（补完整 Level 2 正文）。 |
| **Skills example Level 1 + 2** | `donkey/core/workspace/templates/skills/example/SKILL.md.txt` | F001-P2 已生成（frontmatter `name` + `description` + Level 2 占位）；本 Phase **覆盖**其 Level 2 正文为完整内容，并新增 Level 3 子目录文件（`reference/` / `scripts/` / `templates/`）。 |
| **三个 sqlite3 模板** | `memory/{sessions,store,knowledge}.sqlite3` | 已由 F001-P2 init 阶段预创建（schema-built sessions + 占位空文件 store/knowledge）；本 Phase **不**触碰。本 Phase 假设 sqlite3 schema 健康；若发现 schema 缺失，应让 `donkey init --force` 重建（属 F001-P2 / F002-P2 域，不属本 Phase）。 |

### 3.4 技术栈就绪

- Python 3.11+；
- `httpx`（用于 `webfetch.py.txt` 模板与测试；如选 `requests` 也可，但 spec 默认 httpx）——
  **依赖归属见 §9**：`httpx` 是**渲染进用户工作区**的模板依赖，**donkey 自身的运行期依赖仍恰为 1 个**（SC-021 不变）；`pytest-httpx` 是**新增 dev 依赖**，MUST 声明到 `[project.optional-dependencies].dev`；
- pytest + `pytest-httpx`（用于 webfetch 的 HTTP mock 测试）；
- `langchain_core.tools.tool` 装饰器（**纯 LangChain 内置**——`@tool` 装饰器从 `langchain_core.tools` import，**不**违反 N-04 / N-12；N-04 仅约束 cli/web/gui 客户端不直接 import langchain，`donkey.core` 允许使用 langchain 库 API）——**N-12 边界见 §9.1 的 D-17 说明**；
- ruff + mypy + GitHub Actions —— **本 Phase MUST 交付 `.github/workflows/ci.yml`**（见 §6.16）。

### 3.5 本 Phase 必须改写的 F001-P2 阶段边界断言（**P2 的断言按设计会被本 Phase 打破**）

> **为什么需要这一节**：§7 要求「F001-P1 / F001-P2 前置套件必须全绿」，但 F001-P2 的若干
> 断言**编码的是 P2 的阶段边界**（"清单恰 46 条" / "workspace 内无任何 `.py` 文件" /
> "退出码集合恰为 {0,1,2,3}"），而本 Phase **按设计**要打破这些边界。
> 故 P3 MUST **显式改写**下列断言（**MUST NOT** 改动 P2 的**持久**不变量，也 MUST NOT
> 靠"改红 P2 的测试"或"让 P2 红着提交"蒙混过关）—— 与 F001-P1 → F001-P2 时
> 「P1 的 3 处阶段边界断言被改写」的处理方式同构。

| # | 落点 | P2 阶段的断言 | P3 落地后的正确口径 |
|---|---|---|---|
| 1 | `tests/unit/test_template_skeleton.py::test_template_assets_render_to_expected_tree` | `templates_loaded == 46` / `files_created == 40` / 落地 41 文件 | 清单 **54** 条、文件型 **48** 条、落地 **49** 文件（54 − 6 目录 + 1 工作区清单）；断言 MUST 改为**动态口径**（按 loader 实际返回值计算），绝对值 54/48/49 作为独立断言 |
| 2 | `tests/unit/test_template_skeleton.py::test_no_builtin_tool_files_generated` | workspace 内**无任何 `.py` 文件**；`tools/` 下无 `filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py` | **本 Phase 落地这 5 个 `.py` 文件** → 该断言 MUST 改为「**除本 Phase 新增的 5 个内置工具文件外**无其它 `.py` 文件」，且 MUST 保留"无 `agent.py` / `main.py`"这条 **N-01 持久不变量**（宪法 N-01 只禁 Python **入口**文件，不禁工具模块） |
| 3 | `tests/unit/test_template_skeleton.py::test_exit_code_set_is_exactly_0_to_3` | 本阶段使用的退出码集合恰为 `{0,1,2,3}` | 本 Phase **启用 exit 4**（`BuiltinToolGenerationError`）→ 集合变为 `{0,1,2,3,4}`；同时"运行期依赖恰为 1 个"的断言**保持不变**（SC-021 不受本 Phase 影响） |
| 4 | `tests/e2e/phase/verify_phase_f001_p2.py::test_scenario_1_new_workspace_full_tree` | 落地 41 文件 / 7 目录；`templates=46 created=40 skipped=0` | 落地 **49** 文件 / 7 目录；`templates=54 created=48 skipped=0`（**P2 的 14 个场景断言本身仍必须全绿** —— 它们是 P2 的验收基线） |

> **P2 的 e2e 场景 11（`test_scenario_11_no_builtin_tools_yet`）MUST 同样改写** —— 它断言
> "tools/ 下无内置工具文件"，而那正是**本 Phase 的交付物**。P3 的 §6.1 / §6.7 是它的继任者。
> P3 MUST 把 P2 的场景 11 改为「**除本 Phase 的 3 个内置工具外**无其它内置工具文件」，
> 并把"无内置工具"的边界断言移交 P3 自己的场景。

---

## 4. 实现要点（spec 必须覆盖的功能点）

### 4.1 `donkey/core/workspace/templates/filesystem.py.txt` —— 7 个 `@tool`（材料层）

**模板内容**（写入 workspace 后即为 `tools/filesystem.py`）：

```python
"""Filesystem operations @tool set for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user. When deleted, file
operations become unavailable, but Level 3 content can still be searched via
`FilesystemFileSearchMiddleware.glob_search` / `grep_search`.

NOTE: This module intentionally does NOT include `glob_search` / `grep_search`.
Those are provided by the engine-layer middleware `FilesystemFileSearchMiddleware`
(see donkey's constitution §2.5).

Every tool that mutates a file returns a **change record** (`change` key of
the JSON result) built by `tools.changes`: atomic write, hash of the previous
and the new content, a unified diff, an optional dry-run preview and an
optimistic-lock guard. The engine layer can therefore render a diff, ask a
human to confirm, or roll back **later** without changing this file (v4
feature — v1 itself does not promise diff review, charter AC-5).

Do NOT replace `atomic_write_bytes` with a plain `Path.write_text` when
editing this file: an in-place overwrite destroys the previous content and
makes any future diff / rollback impossible.
"""
from __future__ import annotations

import json
import shutil
from typing import Any

from langchain_core.tools import tool

try:  # normal case: imported as part of the workspace `tools` package
    from .changes import (
        atomic_write_bytes,
        build_change_record,
        check_expected_hash,
        read_existing_bytes,
        resolve_path,
        sha256_bytes,
    )
except ImportError:  # pragma: no cover - loaded as a top-level module
    from changes import (  # type: ignore[no-redef]
        atomic_write_bytes,
        build_change_record,
        check_expected_hash,
        read_existing_bytes,
        resolve_path,
        sha256_bytes,
    )


@tool
def read_file(path: str, start_line: int = 1, num_lines: int | None = None) -> str:
    """Read the entire content of a file as a UTF-8 string.

    Args:
        path: Absolute path, or a path relative to the workspace root.
        start_line: 1-based first line to return (default 1 = whole file).
        num_lines: Number of lines to return (default None = until EOF).
            Use it to read the region around a diff hunk without loading
            the whole file.

    Returns:
        File content as UTF-8 string.

    Raises:
        FileNotFoundError: If `path` does not exist.
        IsADirectoryError: If `path` is a directory.
        PermissionError: If the file is not readable.
    """
    p = resolve_path(path)
    text = p.read_text(encoding="utf-8")
    if start_line <= 1 and num_lines is None:
        return text
    lines = text.splitlines(keepends=True)
    begin = max(start_line - 1, 0)
    end = len(lines) if num_lines is None else begin + max(num_lines, 0)
    return "".join(lines[begin:end])


@tool
def write_file(path: str,
               content: str,
               dry_run: bool = False,
               include_previous: bool = False,
               expected_hash: str | None = None) -> str:
    """Write `content` to `path` atomically and return a **change record**.

    The write is atomic (temp file + `os.replace`): if anything fails, the
    previous content of the file is left untouched. The returned record
    contains the unified diff between the previous and the new content, the
    hash of both versions and the action (`create` / `update`), so an
    engine-layer diff review can be built on top of this tool later.

    Args:
        path: Absolute path, or a path relative to the workspace root.
        content: Text content to write (UTF-8).
        dry_run: If True, compute the change record WITHOUT writing.
        include_previous: If True, include the full previous content in the
            record (needed for rollback; omitted above 256 KiB).
        expected_hash: Optional `sha256:...` of the file as the caller last
            read it. The write fails with `tools.changes.FileChangedError`
            when the file changed in the meantime (lost-update guard).

    Returns:
        JSON-encoded result with `path`, `action`, `bytes_written`, `applied`
        and a `change` record (`version`, `action`, `path`, `rel_path`,
        `previous_exists`, `previous_size`, `previous_hash`, `new_size`,
        `new_hash`, `unified_diff`, `diff_truncated`, `applied`).

    Raises:
        PermissionError: If the file or its parent directory is not writable.
        FileChangedError: If `expected_hash` does not match the current file.
    """
    p = resolve_path(path)
    previous_bytes = read_existing_bytes(p)
    check_expected_hash(p, expected_hash)
    new_bytes = content.encode("utf-8")
    action = "update" if previous_bytes is not None else "create"
    record = build_change_record(
        action, p, previous_bytes, new_bytes, include_previous=include_previous,
    )
    if dry_run:
        return json.dumps({
            "path": str(p),
            "action": action,
            "bytes_written": len(new_bytes),
            "applied": False,
            "change": record,
        }, ensure_ascii=False)
    atomic_write_bytes(p, new_bytes)
    record["applied"] = True
    return json.dumps({
        "path": str(p),
        "action": action,
        "bytes_written": len(new_bytes),
        "applied": True,
        "change": record,
    }, ensure_ascii=False)


@tool
def copy_file(src: str, dst: str) -> str:
    """Copy a file from `src` to `dst` and return a **change record**.

    The copy is atomic (temp file + `os.replace`) and the destination is
    described by a change record with action `copy`.

    Args:
        src: Source path.
        dst: Destination path (will be created if missing).

    Returns:
        JSON-encoded result with `src`, `dst`, `action` (`copy`), `applied`
        and a `change` record describing the destination file.

    Raises:
        FileNotFoundError: If `src` does not exist.
    """
    p_src = resolve_path(src)
    p_dst = resolve_path(dst)
    if not p_src.exists():
        raise FileNotFoundError(f"no such file: {p_src}")
    source_bytes = p_src.read_bytes()
    previous_bytes = read_existing_bytes(p_dst)
    atomic_write_bytes(p_dst, source_bytes)
    try:
        shutil.copystat(p_src, p_dst)
    except OSError:
        pass
    record = build_change_record("copy", p_dst, previous_bytes, source_bytes, src=p_src)
    record["applied"] = True
    return json.dumps({
        "src": str(p_src),
        "dst": str(p_dst),
        "action": "copy",
        "applied": True,
        "change": record,
    }, ensure_ascii=False)


@tool
def move_file(src: str, dst: str) -> str:
    """Move a file from `src` to `dst` and return a **change record**.

    Args:
        src: Source path.
        dst: Destination path.

    Returns:
        JSON-encoded result with `src`, `dst`, `action` (`move`), `applied`
        and a `change` record describing the destination path.

    Raises:
        FileNotFoundError: If `src` does not exist.
    """
    p_src = resolve_path(src)
    p_dst = resolve_path(dst)
    if not p_src.exists():
        raise FileNotFoundError(f"no such file: {p_src}")
    previous_bytes = read_existing_bytes(p_dst)
    shutil.move(str(p_src), str(p_dst))
    new_bytes = p_dst.read_bytes() if p_dst.is_file() else None
    record = build_change_record("move", p_dst, previous_bytes, new_bytes, src=p_src)
    record["applied"] = True
    return json.dumps({
        "src": str(p_src),
        "dst": str(p_dst),
        "action": "move",
        "applied": True,
        "change": record,
    }, ensure_ascii=False)


@tool
def delete_file(path: str, include_previous: bool = False) -> str:
    """Delete a file or a directory tree (careful!) and return a **change record**.

    Args:
        path: Path to delete.
        include_previous: If True, include the previous content of a
            deleted **file** in the record (needed for rollback). Directory
            trees are recorded at directory granularity — v1 does not
            enumerate per-file diffs inside a deleted tree.

    Returns:
        JSON-encoded result with `path`, `type` ('file' | 'directory'),
        `action` (`delete`), `applied` and a `change` record holding the
        previous hash (and previous content when requested).

    Raises:
        FileNotFoundError: If `path` does not exist.
    """
    p = resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(f"no such file: {p}")
    if p.is_dir():
        previous_bytes = None
        shutil.rmtree(p)
        kind = "directory"
    else:
        previous_bytes = read_existing_bytes(p)
        p.unlink()
        kind = "file"
    record = build_change_record(
        "delete", p, previous_bytes, None, include_previous=include_previous,
    )
    record["applied"] = True
    return json.dumps({
        "path": str(p),
        "type": kind,
        "action": "delete",
        "applied": True,
        "change": record,
    }, ensure_ascii=False)


@tool
def list_dir(path: str, include_hidden: bool = True) -> list[str]:
    """List immediate children of a directory (non-recursive).

    Args:
        path: Directory path.
        include_hidden: If False, dot-prefixed entries are skipped. Default
            True keeps the legacy behaviour of listing everything; atomic
            writes use dot-prefixed temp files that are removed immediately.

    Returns:
        Sorted list of child names (basename only).

    Raises:
        FileNotFoundError: If `path` does not exist.
        NotADirectoryError: If `path` is not a directory.
    """
    entries = sorted(p.name for p in resolve_path(path).iterdir())
    if include_hidden:
        return entries
    return [name for name in entries if not name.startswith(".")]


@tool
def stat(path: str, with_hash: bool = False) -> dict[str, Any]:
    """Return file/directory metadata.

    Args:
        path: Path to inspect.
        with_hash: If True, also compute the `sha256` digest of the file
            content (used by the engine layer to snapshot a workspace
            before rendering a diff).

    Returns:
        Dict with keys: `size` (bytes), `mtime` (epoch seconds, float),
        `is_file` (bool), `is_dir` (bool), `exists` (bool), plus `sha256`
        when `with_hash` is True and the path is a regular file.

    Raises:
        OSError: If `stat()` syscall fails (permission, etc.).
    """
    p = resolve_path(path)
    try:
        st = p.stat()
    except FileNotFoundError:
        return {"size": 0, "mtime": 0.0, "is_file": False, "is_dir": False, "exists": False}
    result: dict[str, Any] = {
        "size": st.st_size,
        "mtime": st.st_mtime,
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "exists": True,
    }
    if with_hash and p.is_file():
        result["sha256"] = sha256_bytes(p.read_bytes())
    return result
```

**spec 要求**：

- 7 个 `@tool` 函数：`read_file` / `write_file` / `copy_file` / `move_file` / `delete_file` / `list_dir` / `stat`；**函数名与既有语义不变**（`list_dir` 仍返回 `list[str]`，`stat` 仍返回 `dict`——**不**改成 JSON 字符串）；
- **只增不改（additive-only）**：所有新增参数**一律可选且带默认值**（`read_file` 的 `start_line` / `num_lines`、`write_file` 的 `dry_run` / `include_previous` / `expected_hash`、`delete_file` 的 `include_previous`、`list_dir` 的 `include_hidden`、`stat` 的 `with_hash`）；既有调用方式（不传新参数）行为**逐字节不变**——旧参数默认值必须复刻旧行为（例：`list_dir` 的 `include_hidden` 默认 `True` = 旧行为"列出全部子项"）；
- 返回 JSON **只加字段不改字段**：`write_file` 保留 `path` / `bytes_written` 并追加 `action` / `applied` / `change`；`copy_file` 保留 `src` / `dst` 并追加 `action` / `applied` / `change`；`move_file` 同上；`delete_file` 保留 `path` / `type` 并追加 `action` / `applied` / `change`；
- **所有改文件的工具必须返回 `change` 记录**（§2.9 schema），且**必须**经 `tools/changes.py` 生成（禁止自造 hash / diff 逻辑）；
- **所有改文件的工具必须走原子写**（`atomic_write_bytes`）——**禁止**用 `Path.write_text` / `open(..., "w")` 直接覆盖已有文件（R-D1）；`copy_file` 允许额外 `shutil.copystat` 复制元数据（失败可忽略）；
- `write_file` 保持旧语义"**创建父目录**"（`p.parent.mkdir(parents=True, exist_ok=True)` 由 `atomic_write_bytes` 内部完成）；`write_file` 对**已存在目录**报错（`IsADirectoryError`），不静默跳过；
- `expected_hash` 不匹配时抛 `tools.changes.FileChangedError`（**不**写入、不改文件）；
- `dry_run=True` 时**不产生任何磁盘副作用**（不建父目录、不写文件、不留临时文件），但仍返回完整 `change` 记录（`applied=false`）；
- 相对路径**以 workspace 根为基准**（§2.4 路径绝对化原则）——**不**依赖进程 cwd；绝对路径仍然允许（路径白名单由用户自管，见 `tools/README.md`）；
- 每个 `@tool` **必须**有完整 docstring（LangChain `@tool` 装饰器依赖 docstring 作为工具 description）；docstring 的 `Args` 段必须写清**新增可选参数**的语义与默认值；
- `@tool` 装饰器**必须**从 `langchain_core.tools` import（langchain 内置，**不**违反 N-04 / N-12 —— 因为 `donkey.core` 允许使用 langchain / langgraph 库 API；N-04 仅约束 `cli` / `web` / `gui` 客户端不直接 import）；
- **禁止**包含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管，§2.6）；
- `tools/filesystem.py` 内的 `from .changes import ...` 必须带 `except ImportError` 回退到绝对导入（`from changes import ...`）——兼容"以顶层模块方式加载"的场景（`tools/__init__.py` 存在 → 正常走相对导入）。

### 4.1.1 `donkey/core/workspace/templates/tools/changes.py.txt` —— 变更记录契约库（diff-ready 地基）

> **为什么单独一个文件**：`tools/changes.py` 是**契约库**，不是工具——它含 **0 个 `@tool`**，只被 `tools/filesystem.py` 与用户自写工具 import。把它独立成文件（而不是塞进 `filesystem.py`）是为了让**全 workspace 只有一套变更记录格式**：未来用户自写工具、未来的 `edit_file` / `patch_file` 工具、v4 引擎层的 diff 渲染器，都指向同一个 schema 与同一个版本号。

**模板内容**（写入 workspace 后即为 `tools/changes.py`）：

```python
"""Change-record contract for every file-mutating tool in the donkey workspace.

This module is part of the **material layer** (workspace) and contains **no
`@tool` functions** — it is a plain helper library shared by all
file-mutating tools (builtin and user-authored), so that every file change
recorded in a session speaks **one** schema.

Why this module exists
-----------------------
`donkey` v1 does **not** promise diff review (project charter AC-5): diff
rendering / human approval / rollback live in the **engine layer** and
arrive with v4 (or via a fork of this repository). What the engine layer
needs from the material layer is the **raw material** of every change,
captured *at write time*:

    tool write -> change record -> engine renders diff -> human confirms -> apply

If a tool overwrites a file without recording what was there before, the
"before" half of the diff is destroyed and **no** engine-layer diff (and no
rollback) can ever be built on top of it. Hence the four hard rules below.

Hard rules
----------
1. **Atomic** — content lands via a temp file + `os.replace`; a failed or
   interrupted write never truncates the previous version.
2. **Non-destructive** — the previous content is hashed (and can be
   returned in full) *before* it is replaced.
3. **Previewable** — a diff can be computed without touching the disk.
4. **Concurrency-safe** — a write may assert the hash it expects to
   overwrite, so a file edited by someone else in the meantime is not
   silently clobbered.

Backward-compatibility rules (binding on future changes)
---------------------------------------------------------
- **Additive only**: new fields may be added; existing fields never change
  their meaning. Consumers MUST ignore unknown fields.
- **Frozen names**: for a given ``CHANGE_RECORD_VERSION``, field names and
  shapes are stable.
- **Version dispatch**: breaking changes bump ``CHANGE_RECORD_VERSION``;
  consumers dispatch on it (never on field guessing).
- **Helper reuse**: user-authored tools SHOULD import this module instead of
  re-implementing write / hash / diff logic, so the whole workspace keeps a
  single record format.
"""
from __future__ import annotations

import difflib
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any

#: Version of the change-record contract. Bump only on breaking changes.
CHANGE_RECORD_VERSION = 1

#: Maximum size (bytes) of the ``unified_diff`` payload kept in a record.
MAX_DIFF_BYTES = 64 * 1024

#: Maximum size (bytes) of ``previous_content`` returned when asked for.
MAX_PREVIOUS_BYTES = 256 * 1024


class FileChangedError(RuntimeError):
    """Raised when the file on disk no longer matches the expected hash."""


def workspace_root() -> Path:
    """Absolute path of the workspace root (the directory holding ``tools/``)."""
    override = os.environ.get("DONKEY_WORKSPACE")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def resolve_path(path: str) -> Path:
    """Resolve ``path`` against the workspace root.

    Absolute paths are kept as-is (path policy is the user's business — see
    ``tools/README.md``); relative paths are anchored at the workspace root,
    never at the process CWD (charter §2.4 path absolutization).
    """
    p = Path(path).expanduser()
    return p if p.is_absolute() else workspace_root() / p


def relative_path(path: Path) -> str:
    """Workspace-relative POSIX path of ``path`` (absolute path as fallback)."""
    root = workspace_root()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_bytes(data: bytes) -> str:
    """``sha256:<hex>`` digest of ``data``."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_existing_bytes(path: Path) -> bytes | None:
    """Read ``path`` as raw bytes; ``None`` when it does not exist."""
    if not path.exists():
        return None
    if path.is_dir():
        raise IsADirectoryError(f"not a file: {path}")
    return path.read_bytes()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically.

    The payload is written to a temp file in the **same directory** and then
    moved into place with ``os.replace`` (atomic on POSIX and Windows). A
    failure at any point leaves the previous file content untouched. The
    temp file is dot-prefixed and removed on every failure path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".donkey-tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def build_unified_diff(old_text: str, new_text: str, rel: str) -> str:
    """Unified diff between two texts, with workspace-relative headers."""
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )


def build_change_record(
    action: str,
    path: Path,
    previous_bytes: bytes | None,
    new_bytes: bytes | None,
    *,
    src: Path | None = None,
    include_previous: bool = False,
) -> dict[str, Any]:
    """Build the canonical change record (see module docstring).

    ``previous_bytes`` / ``new_bytes`` are ``None`` when that side does not
    exist (created file / deleted file). The caller flips ``applied`` to
    ``True`` after the change was actually persisted.
    """
    previous_text = (
        previous_bytes.decode("utf-8", errors="replace")
        if previous_bytes is not None else None
    )
    new_text = (
        new_bytes.decode("utf-8", errors="replace")
        if new_bytes is not None else None
    )
    rel = relative_path(path)
    diff = build_unified_diff(previous_text or "", new_text or "", rel)
    diff_bytes = diff.encode("utf-8")
    truncated = len(diff_bytes) > MAX_DIFF_BYTES
    if truncated:
        diff = diff_bytes[:MAX_DIFF_BYTES].decode("utf-8", errors="ignore")
    record: dict[str, Any] = {
        "version": CHANGE_RECORD_VERSION,
        "action": action,
        "path": str(path),
        "rel_path": rel,
        "previous_exists": previous_bytes is not None,
        "previous_size": len(previous_bytes) if previous_bytes is not None else 0,
        "previous_hash": (
            sha256_bytes(previous_bytes) if previous_bytes is not None else None
        ),
        "new_size": len(new_bytes) if new_bytes is not None else 0,
        "new_hash": sha256_bytes(new_bytes) if new_bytes is not None else None,
        "unified_diff": diff,
        "diff_truncated": truncated,
        "applied": False,
    }
    if src is not None:
        record["src"] = str(src)
        record["src_rel_path"] = relative_path(src)
    if include_previous and previous_bytes is not None:
        if len(previous_bytes) <= MAX_PREVIOUS_BYTES:
            record["previous_content"] = previous_text
            record["previous_content_truncated"] = False
        else:
            record["previous_content_truncated"] = True
    return record


def check_expected_hash(path: Path, expected_hash: str | None) -> None:
    """Assert that ``path`` still hashes to ``expected_hash`` (optimistic lock).

    ``None`` disables the check. Raises :class:`FileChangedError` when the
    file changed since the caller read it — the caller should re-read and
    retry instead of clobbering someone else's edit.
    """
    if not expected_hash:
        return
    current = read_existing_bytes(path)
    actual = sha256_bytes(current) if current is not None else None
    if actual != expected_hash:
        raise FileChangedError(
            f"{path} changed since it was read "
            f"(expected {expected_hash}, found {actual}); "
            f"re-read the file and retry"
        )
```

**spec 要求**：

- **0 个 `@tool`**——它是契约库；`tools/README.md` 必须说明这一点，且**未来 F002 的 tools 扫描器必须容忍"无 `@tool` 的辅助模块"**（`tools/__init__.py` 已是同类先例）——记入 §8 风险清单；
- `CHANGE_RECORD_VERSION = 1` + `MAX_DIFF_BYTES`（64 KiB）+ `MAX_PREVIOUS_BYTES`（256 KiB）三个常量**冻结**；
- 公开函数清单（**契约面**，只增不改）：`workspace_root()` / `resolve_path(path)` / `relative_path(path)` / `sha256_bytes(data)` / `read_existing_bytes(path)` / `atomic_write_bytes(path, data)` / `build_unified_diff(old, new, rel)` / `build_change_record(action, path, previous_bytes, new_bytes, *, src=None, include_previous=False)` / `check_expected_hash(path, expected_hash)` + 异常类 `FileChangedError(RuntimeError)`；
- **`build_change_record` 收字节不收字符串**——hash 与 size 必须按**原始字节**计算（decode 再 encode 会改变 BOM / 非法字节文件的 hash）；
- `atomic_write_bytes` 必须在**同目录**建临时文件（跨目录 `os.replace` 不保证原子）并用 `os.replace` 落位；临时文件名为 `.<原名>.<随机>.donkey-tmp`（点开头 → 不污染 `list_dir` 默认视图）；**任何异常路径都要 `unlink` 临时文件**（不留 `.donkey-tmp` 残留）；
- `atomic_write_bytes` 负责 `path.parent.mkdir(parents=True, exist_ok=True)`（保持 `write_file` 的旧语义"自动建父目录"）；
- `relative_path` 对 workspace 之外的路径**回退为绝对路径**（不抛异常）；
- `build_unified_diff` 的 diff 头用 **workspace 相对路径**（`a/<rel>` / `b/<rel>`）——workspace 可搬移，diff 必须可移植；
- `check_expected_hash` 在文件不存在且 `expected_hash` 非 `None` 时同样视为不匹配（`actual=None`）；
- **本模块不得 import `langchain*`**（纯 stdlib 库，保持"非工具模块"身份清晰 + 未来 F002 扫描器零歧义）；
- 本模块**不含** `__main__` 块（宪法 N-01：workspace 内禁止 Python 入口文件）。


### 4.2 `donkey/core/workspace/templates/commandline.py.txt` —— 1 个 `@tool`

**模板内容**：

```python
"""Shell command execution @tool for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user.

IMPORTANT: This module intentionally does NOT use a persistent shell session
(ShellToolMiddleware). Persistent shells conflict with future v2 HITL
(interrupts). Each invocation spawns a new process via `subprocess.run`,
which is interrupt-safe and timeout-bounded.
"""
from __future__ import annotations

import json
import shlex
import subprocess

from langchain_core.tools import tool

try:  # normal case: imported as part of the workspace `tools` package
    from .changes import resolve_path, workspace_root
except ImportError:  # pragma: no cover - loaded as a top-level module
    from changes import resolve_path, workspace_root  # type: ignore[no-redef]


@tool
def run_shell(command: str, timeout: int = 60, cwd: str | None = None) -> str:
    """Execute a shell command in a fresh subprocess and return its combined stdout/stderr.

    Each invocation creates a NEW subprocess (no persistent shell session).
    The command line is split into an argv array and executed via
    `subprocess.run` with `shell=False` to avoid shell injection. If the command
    runs longer than `timeout` seconds, it is killed (TimeoutExpired). Exit code 0
    is treated as success; non-zero is included in the returned JSON.

    The working directory defaults to the **workspace root** (never the
    process CWD), so relative paths in the command refer to workspace files
    (charter §2.4). Files changed by the command are NOT recorded as change
    records — shell side effects bypass the `@tool` write path and are
    invisible to the diff layer; the engine layer reconciles them with a
    workspace snapshot (see §2.9 known gaps).

    Args:
        command: The shell command line to execute (e.g. "ls -la /tmp").
        timeout: Maximum execution time in seconds (default 60).
        cwd: Working directory (absolute, or relative to the workspace root).
            Default: the workspace root.

    Returns:
        JSON-encoded result with keys:
        - `stdout`: str (combined stdout+stderr)
        - `stderr`: str (typically empty; stdout already includes stderr)
        - `returncode`: int (0 on success)
        - `timed_out`: bool (True if killed by timeout)
        - `cwd`: str (resolved working directory)
        - `argv`: list[str] (the parsed command, exactly as executed)

    Raises:
        subprocess.TimeoutExpired: Re-raised after the JSON result is returned
            (caller should handle via `timed_out` field).
    """
    work_dir = resolve_path(cwd) if cwd else workspace_root()
    argv = shlex.split(command)
    try:
        completed = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
        )
        return json.dumps({
            "stdout": completed.stdout + completed.stderr,
            "stderr": "",
            "returncode": completed.returncode,
            "timed_out": False,
            "cwd": str(work_dir),
            "argv": argv,
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired as e:
        return json.dumps({
            "stdout": (e.stdout or "") + (e.stderr or ""),
            "stderr": "",
            "returncode": -1,
            "timed_out": True,
            "cwd": str(work_dir),
            "argv": argv,
        }, ensure_ascii=False)
```

**spec 要求**：

- 1 个 `@tool` 函数：`run_shell(command, timeout=60, cwd=None)`；
- **每次新建进程**（`subprocess.run(shlex.split(command), shell=False, timeout=...)`）——显式命令数组不走 shell 字符串，从源头避免 shell injection；与"v1 不走持久 shell"约束一致（每次都是新进程）。管道 / 重定向不支持（需用户自行拆分或改用脚本）；
- 显式 `timeout` 掐断；
- 返回值必须含 `timed_out` 字段，模型据此决定重试 / 放弃；
- **`cwd` 默认 = workspace 根**（§2.4 路径绝对化原则）：**不**依赖进程 cwd；`cwd` 为相对路径时同样以 workspace 根为基准；返回值新增 `cwd` + `argv` 两个字段（**只增不改**：`stdout` / `stderr` / `returncode` / `timed_out` 语义冻结）；
- **不**依赖 LangChain `ShellToolMiddleware`（被 v1 永久禁用）；
- docstring 完整；
- **已知缺口（必须写进 docstring）**：`run_shell` 造成的文件副作用**不**进变更记录——shell 绕过 `@tool` 写路径，引擎层 diff 需靠 workspace 快照对账（§2.9 已知缺口表）。**不**在本 Phase 试图拦截 shell 副作用。

### 4.3 `donkey/core/workspace/templates/webfetch.py.txt` —— 1 个 `@tool`

**模板内容**：

```python
"""HTTP fetch @tool for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user.

Uses httpx (synchronous). Does NOT persist cookies between calls.
"""
from __future__ import annotations

import json

import httpx
from langchain_core.tools import tool


@tool
def fetch_url(url: str,
              method: str = "GET",
              headers: dict[str, str] | None = None,
              timeout: int = 30) -> str:
    """Make an HTTP request to `url` and return the response body as a string.

    Args:
        url: Target URL (must include scheme, e.g. https://example.com).
        method: HTTP method (default "GET"). Supports "GET" / "POST" / "PUT"
                / "DELETE" / "PATCH" / "HEAD".
        headers: Optional dict of HTTP headers.
        timeout: Request timeout in seconds (default 30).

    Returns:
        JSON-encoded result with keys:
        - `status_code`: int (HTTP status, e.g. 200)
        - `body`: str (response body decoded as UTF-8)
        - `headers`: dict[str, str] (response headers)
        - `url`: str (final URL after redirects)

    Raises:
        httpx.HTTPError: On network / protocol errors.
        httpx.TimeoutException: On timeout (after `timeout` seconds).
    """
    response = httpx.request(
        method=method.upper(),
        url=url,
        headers=headers or {},
        timeout=timeout,
        follow_redirects=True,
    )
    return json.dumps({
        "status_code": response.status_code,
        "body": response.text,
        "headers": dict(response.headers),
        "url": str(response.url),
    })
```

**spec 要求**：

- 1 个 `@tool` 函数：`fetch_url(url, method="GET", headers=None, timeout=30)`；
- 使用 `httpx` 同步调用（不持久化 cookies；每次新连接）；
- 显式 `timeout`；
- 不引入 LangChain 任何 webfetch 中间件（v1 不存在）；
- **返回 JSON 形状冻结**（`status_code` / `body` / `headers` / `url` 四个字段的名字与语义不得改动）——`fetch_url` 是**只读**工具，**不**产生变更记录（无 `change` 字段）；
- **未来若支持"下载到文件"**：必须**新增独立 `@tool`**（如 `download_to_file`）并复用 `tools/changes.py` 的原子写 + 变更记录契约，**禁止**给 `fetch_url` 增加"顺手落盘"的副作用参数（会污染只读语义 + 破坏 diff 记录的可追溯性）。

### 4.4 `donkey/core/workspace/templates/tools/__init__.py.txt` —— `tools/__init__.py` 占位

**模板内容**：

```python
"""donkey workspace tools package.

This package is auto-generated by `donkey init`. The 3 builtin @tool modules
(filesystem / commandline / webfetch) live here, together with `changes.py`
— the change-record contract library (0 @tool functions) shared by every
tool that writes files. Users may add additional @tool modules of their own.
"""
```

**spec 要求**：最小占位即可（仅 docstring）。**必须**说明 `changes.py` 是**契约库（非 `@tool`）**——避免未来 F002 的 tools 扫描器把它误判为工具模块。

### 4.5 `donkey/core/workspace/templates/tools/README.md.txt` —— `tools/README.md` 工具开发规范

> **注意**：`tools/README.md` 的 **manifest entry 与目标文件由 F001-P2 创建**（P2 已把它列入 46 条清单 + 生成占位 .txt）；本 Phase **不新增 entry**，只**覆盖** `templates/tools/README.md.txt` 源文件，把占位正文替换为完整规范（`--force` 时按出厂内容重写）。
>
> （`tools/changes.py` 则**是**本 Phase 的**新 entry**——见 §4.1.1 与 §4.7。）

spec 必须列出 `tools/README.md` 的初始内容（建议长度 25–40 行），包含：

- `@tool` 装饰器从 `langchain_core.tools` 导入；
- 函数必须有 docstring（作为工具 description）；
- 路径白名单由用户自管，donkey 不强制；
- 推荐 timeout 配置（`commandline` 默认 60s / `webfetch` 默认 30s）；
- 错误处理建议（raise 具体异常类型 / 返回 JSON 含 `error` 字段）；
- **改文件的工具必须遵守"变更记录契约"**（新增小节，见下）：

> **改文件的工具怎么写（变更记录契约）**
>
> 1. **必须**用 `tools.changes.atomic_write_bytes(path, data)` 写文件，**禁止** `Path.write_text` / `open(..., "w")` 直接覆盖——非原子覆盖会毁掉旧内容，未来的 diff / 回滚就无从谈起。
> 2. 写前用 `read_existing_bytes(path)` 取旧字节，写后用 `build_change_record(action, path, old_bytes, new_bytes)` 生成 `change` 记录，**放进返回 JSON 的 `change` 字段**。
> 3. `change` 记录的 schema 由 `tools.changes.CHANGE_RECORD_VERSION`（当前 `1`）冻结：**只增不改**——新字段可加，旧字段语义不动；引擎层按 `version` 分派。
> 4. 建议同时提供 `dry_run`（只算 diff 不落盘）与 `expected_hash`（乐观锁，防覆盖别人的改动）。
> 5. 写完把 `change["applied"]` 置 `True`；`dry_run` 保持 `False`。
> 6. **不要自己造 hash / diff 逻辑**——`tools/changes.py` 是全 workspace 唯一的变更记录产地；用户自写工具 import 它即可（`from .changes import ...`）。

> **注**：`tools/changes.py` 是**契约库，不是工具**——它含 0 个 `@tool`，只被 import。写自己的工具时不要在 `tools/changes.py` 里加 `@tool`。

### 4.6 Skills example 三层示例

#### 4.6.1 Level 1 + Level 2（`donkey/core/workspace/templates/skills/example/SKILL.md.txt`——**覆盖** F001-P2 的同名源）

```markdown
---
name: example
description: 示例 Skill —— 展示 Skills 三层模型（Level 1 frontmatter + Level 2 主体 + Level 3 reference/scripts/templates）。
---

# Example Skill（Level 2）

本文件由 `donkey init` 自动生成，演示 Skills 三层模型：

- **Level 1**（本文件顶部 frontmatter）：`name` + `description` 两字段必填；donkey 自动注册为独立 `@tool` `load_skill_example`。
- **Level 2**（frontmatter 下方的 Markdown 主体）：模型调用 `load_skill_example` 时返回的内容。
- **Level 3**（同目录下除 SKILL.md 之外的文件）：放在 `reference/` / `scripts/` / `templates/` 等子目录；由内置 `@tool`（filesystem / commandline / webfetch）或 `FilesystemFileSearchMiddleware` 读取。

## 使用示例

模型判断相关时调用 `load_skill_example`，获得本文件全部内容，然后：

- 如需看 `reference/` 子目录的细节 → 调 `filesystem.list_dir` 或 `grep_search`
- 如需运行 `scripts/example.py` → 调 `commandline.run_shell`
- 如需渲染 `templates/example.md` 模板 → 调 `filesystem.read_file`

## 注意事项

- 修改本 Skill 时请保留 frontmatter 的 `name` + `description` 字段；
- 其它字段（如 `when_to_use` / `tags` / `version`）**不**被 donkey 解析，会被忽略。
```

#### 4.6.2 Level 3：reference / scripts / templates

`donkey/core/workspace/templates/skills/example/reference/example.md.txt`：

```markdown
# Example Reference（Level 3 示例）

本文件演示 Skill 的 Level 3 内容——模型用内置 `@tool`（filesystem / commandline / webfetch）按需读取。

## 内容

此处填写 Skill 的深层参考文档（API 手册 / 术语表 / 长篇背景知识）。

- 模型**不**会主动加载本文件；
- 模型调用 `load_skill_example` 获得 Level 2 主体后，如需更深内容才会触发 `filesystem.read_file("skills/example/reference/example.md")`。
```

`donkey/core/workspace/templates/skills/example/scripts/example.py.txt`：

```python
"""Example Script（Level 3 示例）。

本文件演示 Skill 的 Level 3 内容——可由模型通过 `commandline.run_shell` 调用。
"""
import sys


def main() -> int:
    print("Hello from skills/example/scripts/example.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`donkey/core/workspace/templates/skills/example/templates/example.md.txt`：

```markdown
# Example Template（Level 3 示例）

本文件演示 Skill 的 Level 3 内容——模板文件（如 Jinja2 模板 / Markdown 模板）。

模型调用 `filesystem.read_file("skills/example/templates/example.md")` 后再渲染。

---

**Title**: {{ title }}
**Date**: {{ date }}

## Body

{{ body }}
```

### 4.7 模板清单追加条目（P3：+8 条 → 累计 54 条）

`donkey/core/workspace/templates/manifest.json` 在 P2 已有 46 条基础上**追加**如下 8 条（追加操作 = "在原 entries 数组末尾 push"，**不**修改 P2 已有条目）。下表是 **P3 完成后的最终形态（54 条）**：

```json
{
  "version": 1,
  "entries": [
    {"path": "instruction.md", "format": "markdown"},
    {"path": "providers/default.toml", "format": "toml"},
    {"path": "mcp/mcp.json", "format": "json"},
    {"path": "skills/example/SKILL.md", "format": "markdown"},
    {"path": "README.md", "format": "markdown"},
    {"path": "tools/README.md", "format": "markdown"},
    {"path": "mcp/README.md", "format": "markdown"},
    {"path": "skills/README.md", "format": "markdown"},
    {"path": "memory/README.md", "format": "markdown"},
    {"path": ".gitignore", "format": "text"},
    {"path": "providers/README.md", "format": "markdown"},
    {"path": "providers/openai.toml", "format": "toml"},
    {"path": "providers/anthropic.toml", "format": "toml"},
    {"path": "providers/google.toml", "format": "toml"},
    {"path": "providers/ollama.toml", "format": "toml"},
    {"path": "providers/xai.toml", "format": "toml"},
    {"path": "providers/mistral.toml", "format": "toml"},
    {"path": "providers/qwen.toml", "format": "toml"},
    {"path": "providers/deepseek.toml", "format": "toml"},
    {"path": "providers/doubao.toml", "format": "toml"},
    {"path": "providers/kimi.toml", "format": "toml"},
    {"path": "providers/zhipu.toml", "format": "toml"},
    {"path": "providers/minimax.toml", "format": "toml"},
    {"path": "providers/tencent.toml", "format": "toml"},
    {"path": "providers/xiaomi.toml", "format": "toml"},
    {"path": "providers/stepfun.toml", "format": "toml"},
    {"path": "providers/openai-compatible.toml", "format": "toml"},
    {"path": "providers/meta.toml", "format": "toml"},
    {"path": "providers/bedrock.toml", "format": "toml"},
    {"path": "providers/groq.toml", "format": "toml"},
    {"path": "providers/fireworks.toml", "format": "toml"},
    {"path": "providers/together.toml", "format": "toml"},
    {"path": "providers/cohere.toml", "format": "toml"},
    {"path": "providers/perplexity.toml", "format": "toml"},
    {"path": "providers/databricks.toml", "format": "toml"},
    {"path": "providers/cerebras.toml", "format": "toml"},
    {"path": "providers/openrouter.toml", "format": "toml"},
    {"path": "tools", "format": "directory"},
    {"path": "mcp", "format": "directory"},
    {"path": "skills", "format": "directory"},
    {"path": "skills/example", "format": "directory"},
    {"path": "memory", "format": "directory"},
    {"path": "providers", "format": "directory"},
    {"path": "memory/sessions.sqlite3", "format": "sqlite3"},
    {"path": "memory/store.sqlite3", "format": "sqlite3"},
    {"path": "memory/knowledge.sqlite3", "format": "sqlite3"},
    {"path": "tools/__init__.py", "format": "python"},
    {"path": "tools/changes.py", "format": "python"},
    {"path": "tools/filesystem.py", "format": "python"},
    {"path": "tools/commandline.py", "format": "python"},
    {"path": "tools/webfetch.py", "format": "python"},
    {"path": "skills/example/reference/example.md", "format": "markdown"},
    {"path": "skills/example/scripts/example.py", "format": "python"},
    {"path": "skills/example/templates/example.md", "format": "markdown"}
  ]
}
```

**spec 要求**：

- `format` 字段取值：`markdown` / `toml` / `json` / `python` / `text` / `directory` / `sqlite3`；
- P3 追加的 `tools/__init__.py` + **`tools/changes.py`（变更记录契约库）** + 3 个内置 tool + 3 个 Skills Level 3 示例 共 **8** 条新 entry（叠加 P1 的 3 条 + P2 的 43 条 → 累计 **46** 条 → **本 Phase 结束后累计 54 条**，即 v1 baseline）；
- `tools/changes.py` 的 entry **必须**与 3 个内置 tool 同批生成（`tools/filesystem.py` import 它 → 两者必须同时存在，缺一则 workspace 的文件工具直接 ImportError）；
- `load_template_manifest()` 由 **F001-P2** 实现并已做 schema 校验（F001-P1 只**建档**清单、**不加载不解析**，spec FR-029）；本 Phase 不修改 manifest 加载逻辑——P2 的 `render_templates` 已能驱动新条目。

### 4.8 单元测试（`tests/unit/test_builtin_tools.py`）

**spec 必须列出**下列单测用例（**至少 15 个** = 8 个基础 + 7 个变更记录 / diff-ready）：

| 用例 | 输入 | 期望 |
|---|---|---|
| `test_filesystem_read_write` | write_file → read_file | 内容一致 |
| `test_filesystem_copy_move_delete` | copy / move / delete 三件套 | 操作符合预期 |
| `test_filesystem_list_dir_stat` | list_dir / stat | 返回结构正确 |
| `test_commandline_run_shell_echo` | `run_shell("echo hello")` | 返回 **JSON 字符串**（`json.dumps`）——解析后 `stdout` 含 `"hello\n"`、`returncode == 0`、`timed_out is False` |
| `test_commandline_run_shell_timeout` | `run_shell("sleep 5", timeout=1)` | 返回 **JSON 字符串**——解析后 `timed_out is True` |
| `test_webfetch_get_mock` | 用 pytest-httpx mock 一个 GET 200 | 返回 JSON 含 `status_code=200`, `body="..."` |
| `test_webfetch_timeout` | 用 pytest-httpx mock 延迟 5s + timeout=1 | **抛 `httpx.TimeoutException`**（模板的 `fetch_url` **不**捕获超时——异常透传给调用方，由 `ToolTimeoutError`（exit 33）在 F004 run 域统一映射） |
| `test_tools_init_importable` | `from tools import filesystem, commandline, webfetch` | 无异常；3 个 tool 模块各至少 1 个 `@tool` 函数；`tools.changes` **0 个** `@tool`（契约库） |
| `test_write_file_returns_change_record` | write_file 写新文件 | 返回 JSON 含 `change.version == 1` / `change.action == "create"` / `change.previous_exists is False` / `change.previous_hash is None` / `change.new_hash` 非空 / `change.unified_diff` 含 `+` 行 |
| `test_write_file_update_records_diff` | 先写 `"a\nb\n"`，再写 `"a\nc\n"` | `change.action == "update"`；`change.previous_hash` == 首次写入后文件的 sha256；`unified_diff` 含 `-b` 与 `+c` |
| `test_write_file_dry_run_leaves_disk_untouched` | `dry_run=True` 写已存在文件 | 文件内容**不变**；返回 `applied is False`；`change.unified_diff` 仍非空；**无** `.donkey-tmp` 残留 |
| `test_write_file_expected_hash_mismatch` | 传入与当前文件不符的 `expected_hash` | 抛 `tools.changes.FileChangedError`；文件内容**不变** |
| `test_write_file_atomic_leaves_old_content_on_failure` | 目标路径的父路径是**已存在的文件**（`mkdir` 失败） | 抛异常；原文件内容**不变**；目录下**无** `.donkey-tmp` 残留 |
| `test_delete_file_records_previous_hash` | delete_file 一个已存在文件 | `action == "delete"`；`change.previous_hash` 非空；`include_previous=True` 时 `change.previous_content` == 原内容 |
| `test_changes_contract_version_stable` | `from tools.changes import CHANGE_RECORD_VERSION, build_change_record` | `CHANGE_RECORD_VERSION == 1`；`build_change_record` 返回的**基线 12 字段**（§2.9）与 spec **完全一致**（键集合断言，防止字段漂移）；`copy` / `move` 追加 `src` + `src_rel_path`；`include_previous=True` 追加 `previous_content`（超限时改为 `previous_content_truncated=true`） |

### 4.9 集成测试（`tests/integration/test_init_to_load.py`）

> **⚠️ 集成层在本 Phase 首次启用** —— F001-P2 的 `plan.md` G4 曾论证「`tests/integration/`
> 保持空占位（P2 的 2 个新 core 模块由单一流水线串联、无跨模块协作契约）」，**该理由在本 Phase
> 失效**：本 Phase 出现**真正的跨模块协作** —— `donkey init`（core 层）产出的 workspace 产物
> （渲染层）被**独立进程** import 并调用（用户侧），这正是集成层的定义。
> 故 P3 的 `plan.md` MUST **重新论证 G4**（从"留空"改为"启用"），并把
> `tests/integration/` 从"空占位"改为实际测试目录。
> **import 方式 MUST 与 §4.10 同口径** —— 用**独立子进程** import 渲染产物，MUST NOT 在测试
> 进程内 `sys.path.insert` + `from tools.X import ...`（`sys.modules` 按名缓存会让后续场景
> 测到**第一个** workspace 的产物，验收假绿）。

**spec 必须列出**以下集成测试（**端到端集成预演**——**仅做 import 路径 + 函数签名测试，不做 F002 静态格式检查**）：

| 用例 | 验证内容 |
|---|---|
| `test_init_then_import_filesystem` | `donkey init` 后 `from tools.filesystem import read_file` 等 import 语句无异常 |
| `test_init_then_import_commandline` | `from tools.commandline import run_shell` + 调一次 `run_shell("echo integration")` |
| `test_init_then_import_webfetch` | `from tools.webfetch import fetch_url` + 调一次（用 pytest-httpx mock） |
| `test_init_then_import_changes_contract` | `from tools.changes import CHANGE_RECORD_VERSION, atomic_write_bytes, build_change_record` 导入成功；`CHANGE_RECORD_VERSION == 1`；`tools/filesystem.py` 与 `tools/changes.py` **同批存在**（不会出现"工具在、契约库不在"的半残 workspace） |

### 4.10 verify 脚本（`tests/e2e/phase/verify_phase_f001_p3.py`）

**黑盒测试**（禁止 import `donkey.*` 业务代码；只跑 `subprocess.run(["donkey", ...])`），16 个断言对应 §6 退出条件。

> **⚠️ MUST NOT 在测试进程内 `import` workspace 产物**（`from tools.filesystem import ...`）——
> `sys.modules` 按**模块名**缓存，`sys.path.remove()` **不会**卸载模块：实测从 workspace A
> 导入过 `tools.m` 后，再从 workspace B 导入拿到的**仍是 A 的模块**（`sys.modules["tools.m"]`
> 命中缓存）→ 后续场景实际测的是**第一个** workspace 的产物，验收假绿。
> 故凡需 import workspace 代码的场景，MUST 用**独立子进程**（`subprocess.run([sys.executable,
> "-c", snippet], cwd=workspace)`）——既避开模块缓存，也更贴合宪法 §3.1「黑盒脚本只跑子进程」。

---

## 5. 异常退出码表（Phase 全量 Error class 映射）

| Error class（`donkey.core.exceptions`） | exit code | 触发条件 | 报错概率 |
|---|---|---|---|
| `BuiltinToolGenerationError` | **4** | 内置 `@tool` + Skills example 生成失败（**合并三项**：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、集成预演 import 失败）。用户修复动作相同：重装 donkey / 检查权限 / 重试 init；按奥卡姆剃刀合并到 1 个码值 | 低 |
| exit 5–10 | （预留） | 留给 v1.x 试运行期新错误 | — |

**奥卡姆剃刀原则**：本 Phase 仅占 1 个码值（4）。原本可能拆分为 `BuiltinToolWriteError`（写入失败）/ `SkillsExampleWriteError`（Skills 三层失败）/ `EndToEndVerifyError`（集成预演失败）三个，对用户而言修复动作相同（重装 / 检查权限 / 重试），合并为单一 `BuiltinToolGenerationError` —— 若分开分配会浪费 2 个码值给稀有错误。

---

## 6. 退出条件（Exit Gate）

**`tests/e2e/phase/verify_phase_f001_p3.py` 必须跑通以下 15 个场景断言**（顺序固定，每条独立可测），**且第 16 项 CI 交付条件同时满足**：

### 6.1 生成的 workspace 含 3 个 builtin tool + tools/__init__.py + tools/changes.py + tools/README.md

```python
def test_scenario_1_builtin_tools_present(tmp_path):
    """场景 1：init 后含 3 个 builtin tool + __init__.py + changes.py + README.md"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    assert (ws / "tools" / "__init__.py").exists()
    assert (ws / "tools" / "changes.py").exists()
    assert (ws / "tools" / "filesystem.py").exists()
    assert (ws / "tools" / "commandline.py").exists()
    assert (ws / "tools" / "webfetch.py").exists()
    assert (ws / "tools" / "README.md").exists()
```

### 6.2 三个 builtin tool 文件均可 import，每个 `@tool` 函数有完整 docstring

```python
def test_scenario_2_tools_importable_with_docstrings(tmp_path):
    """场景 2：3 个 builtin tool 可 import，每个 @tool 有 docstring"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    # 独立子进程 import —— 避开 sys.modules 的按名缓存（见 §4.10 的说明）。
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
from tools.commandline import run_shell
from tools.webfetch import fetch_url
fns = [read_file, write_file, copy_file, move_file, delete_file, list_dir, stat, run_shell, fetch_url]
print(json.dumps({f.__name__: len(f.__doc__ or "") for f in fns}))
"""],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    doc_lengths = json.loads(completed.stdout)
    for name, length in doc_lengths.items():
        assert length > 20, name
```

### 6.3 `commandline.run_shell("echo hello")` 返回 **JSON 字符串**（`stdout` / `stderr` / `returncode` / `timed_out`）

```python
def test_scenario_3_commandline_run_shell_echo(tmp_path):
    """场景 3：run_shell("echo hello") 集成测试"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.commandline import run_shell
result = run_shell.invoke({"command": "echo hello"})
print(result)
"""],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    # run_shell 的返回契约：**JSON 字符串**（与 §4.8 单测表逐字一致）。
    result_dict = json.loads(completed.stdout)
    assert "hello" in result_dict["stdout"]
    assert result_dict["returncode"] == 0
    assert result_dict["timed_out"] is False
```

### 6.4 `filesystem.py` 7 个 `@tool` 单元测试全绿

```python
def test_scenario_4_filesystem_seven_tools(tmp_path):
    """场景 4：filesystem.py 7 个 @tool 单元测试（旧调用方式仍可用 = 向后兼容断言）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
ws = %r
# write + read
write_file.invoke({"path": ws + "/test.txt", "content": "hi"})
read_back = read_file.invoke({"path": ws + "/test.txt"})
# copy + move
copy_file.invoke({"src": ws + "/test.txt", "dst": ws + "/test_copy.txt"})
# list_dir
names = list_dir.invoke({"path": ws})
# stat —— 返回 dict（不是 JSON 字符串），直接取字段
st = stat.invoke({"path": ws + "/test.txt"})
# delete
delete_file.invoke({"path": ws + "/test_copy.txt"})
print(json.dumps({"read_back": read_back, "names": names, "stat": st}))
""" % str(ws)],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert "hi" in payload["read_back"]
    assert (ws / "test_copy.txt").exists()
    assert "test.txt" in payload["names"]
    # stat —— 返回 dict（不是 JSON 字符串），直接取字段
    assert payload["stat"]["is_file"] is True
    assert payload["stat"]["size"] > 0
    # delete
    assert not (ws / "test_copy.txt").exists()
```

### 6.5 `webfetch.py` HTTP mock 测试通过

```python
def test_scenario_5_webfetch_http_mock(tmp_path, httpx_mock):
    """场景 5：webfetch HTTP mock 测试（pytest-httpx 的 httpx_mock fixture）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    # httpx_mock fixture 只对**本进程**生效 —— 故 mock 与 import MUST 同处一个
    # 子进程（见 §4.10：MUST NOT 在测试进程内 import workspace 产物）。
    with httpx_mock:
        httpx_mock.add_response(
            url="https://example.com",
            method="GET",
            status_code=200,
            text="mocked body",
        )
        completed = subprocess.run(
            [sys.executable, "-c", """
import json
from tools.webfetch import fetch_url
print(fetch_url.invoke({"url": "https://example.com"}))
"""],
            capture_output=True, text=True, cwd=str(ws), timeout=60,
        )
    assert completed.returncode == 0, completed.stderr
    result = completed.stdout
    result_dict = json.loads(result)
    assert result_dict["status_code"] == 200
    assert "mocked body" in result_dict["body"]
```

### 6.6 Skills example 三层完整

```python
def test_scenario_6_skills_three_levels(tmp_path):
    """场景 6：SKILL.md frontmatter 合法 + Level 2 非空 + Level 3 含至少 1 个文件"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    skill_path = ws / "skills" / "example" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    # Level 1: frontmatter
    assert text.startswith("---\n")
    assert "name: example" in text
    assert "description:" in text
    # Level 2: markdown body 非空
    assert "Level 2" in text
    # Level 3: 至少 1 个文件（reference 或 scripts 或 templates）
    level3_count = 0
    for sub in ["reference", "scripts", "templates"]:
        sub_dir = ws / "skills" / "example" / sub
        if sub_dir.is_dir():
            level3_count += sum(1 for _ in sub_dir.iterdir())
    assert level3_count >= 1
```

### 6.7 `tools/` 子目录内的 3 个内置工具**不**含 `glob_search` / `grep_search`

```python
def test_scenario_7_no_glob_grep_in_builtin(tmp_path):
    """场景 7：3 个 builtin tool 文件不含 glob_search / grep_search"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    for tool_file in [ws / "tools" / "filesystem.py",
                      ws / "tools" / "commandline.py",
                      ws / "tools" / "webfetch.py"]:
        text = tool_file.read_text(encoding="utf-8")
        assert "glob_search" not in text
        assert "grep_search" not in text
```

### 6.8 幂等场景 2：用户 `rm filesystem.py` 后 init 补齐

```python
def test_scenario_8_idempotent_replenish(tmp_path):
    """场景 2 子操作：rm filesystem.py 后 init 补齐"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    (ws / "tools" / "filesystem.py").unlink()
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "tools" / "filesystem.py").exists()
```

### 6.9 `--force` 场景 3：用户自建 `tools/my_custom_tool.py`（不在清单内）后 `--force` 不删

```python
def test_scenario_9_force_preserves_user_tool(tmp_path):
    """场景 3：--force 不动用户的 tools/my_custom_tool.py（不在 manifest）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    user_tool = ws / "tools" / "my_custom_tool.py"
    user_tool.write_text("# 用户自定义工具\n", encoding="utf-8")

    result = subprocess.run(["donkey", "init", str(ws), "--force"], capture_output=True, text=True)
    assert result.returncode == 0
    assert user_tool.exists()  # 用户自定义 tool 不动
    # filesystem.py 被恢复出厂
    fs_content = (ws / "tools" / "filesystem.py").read_text(encoding="utf-8")
    assert "用户自定义工具" not in fs_content
```

### 6.10 集成预演：`from tools.filesystem import read_file` 等 import 语句无异常

```python
def test_scenario_10_integration_imports(tmp_path):
    """场景 10：集成预演——所有 builtin tool 可正常 import"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
from tools.commandline import run_shell
from tools.webfetch import fetch_url
fns = [read_file, write_file, copy_file, move_file, delete_file, list_dir, stat, run_shell, fetch_url]
print(json.dumps({"callable": all(callable(f) for f in fns), "count": len(fns)}))
"""],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["callable"] is True
    assert payload["count"] == 9
```

### 6.11 不做 F002 静态检查

```python
def test_scenario_11_no_f002_static_check(tmp_path):
    """场景 11：P3 init 后不跑 F002 静态检查（属 F002 域）"""
    ws = tmp_path / "ws"
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    # 即便 builtin tool 文件有问题（人为改坏），init 阶段也不应跑 F002 检查
    # F002 才会校验
```

### 6.12 write_file 返回统一变更记录（action + hash + unified_diff）

```python
def test_scenario_12_write_file_returns_change_record(tmp_path):
    """场景 12：write_file 返回 change 记录（含 unified_diff / hash / action）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import write_file
target = %r
# 首次创建
r1 = json.loads(write_file.invoke({"path": target, "content": "a\nb\n"}))
# 二次更新：记录旧版本 hash + 真实 diff
r2 = json.loads(write_file.invoke({"path": target, "content": "a\nc\n"}))
print(json.dumps({"r1": r1, "r2": r2}))
""" % str(ws / "demo.txt")],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    r1 = payload["r1"]
    assert r1["action"] == "create"
    assert r1["applied"] is True
    change = r1["change"]
    assert change["version"] == 1
    assert change["action"] == "create"
    assert change["previous_exists"] is False
    assert change["previous_hash"] is None
    assert change["new_hash"].startswith("sha256:")
    assert "+b" in change["unified_diff"]
    # 二次更新：记录旧版本 hash + 真实 diff
    r2 = payload["r2"]
    change2 = r2["change"]
    assert r2["action"] == "update"
    assert change2["previous_exists"] is True
    assert change2["previous_hash"] == change["new_hash"]
    assert "-b" in change2["unified_diff"] and "+c" in change2["unified_diff"]
```

### 6.13 dry_run 只预览不落盘

```python
def test_scenario_13_dry_run_does_not_touch_disk(tmp_path):
    """场景 13：dry_run=True 不产生任何磁盘副作用，但仍返回 diff"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import write_file
target = %r
write_file.invoke({"path": target, "content": "old\n"})
r = json.loads(write_file.invoke({"path": target, "content": "new\n", "dry_run": True}))
print(json.dumps({"r": r}))
""" % str(ws / "demo.txt")],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    r = json.loads(completed.stdout)["r"]
    assert r["applied"] is False
    assert r["change"]["applied"] is False
    assert "-old" in r["change"]["unified_diff"]
    # 文件内容未变
    assert (ws / "demo.txt").read_text(encoding="utf-8") == "old\n"
    # 无临时文件残留
    assert not list(ws.glob("*.donkey-tmp"))
```

### 6.14 写失败不破坏旧内容 + 无临时文件残留（原子写）

```python
def test_scenario_14_atomic_write_failure_keeps_old_content(tmp_path):
    """场景 14：写失败时旧文件内容完好、且无 .donkey-tmp 残留"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    blocker = ws / "blocker"
    blocker.write_text("原内容\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.filesystem import write_file
try:
    write_file.invoke({"path": %r, "content": "新内容\n"})
except OSError as exc:
    print(json.dumps({"raised": type(exc).__name__}))
else:
    print(json.dumps({"raised": None}))
""" % str(blocker / "child.txt")],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    # 父路径是文件 → mkdir 失败 → 写入整体失败
    assert json.loads(completed.stdout)["raised"] is not None
    # 旧内容完好
    assert blocker.read_text(encoding="utf-8") == "原内容\n"
    # 无临时文件残留
    assert not list(ws.glob("*.donkey-tmp"))
    assert not list(ws.glob(".*.donkey-tmp"))
```

### 6.15 delete_file 返回变更记录 + 契约版本冻结为 1

```python
def test_scenario_15_delete_record_and_contract_version(tmp_path):
    """场景 15：delete_file 返回 action=delete + previous_hash；契约版本 == 1"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    completed = subprocess.run(
        [sys.executable, "-c", """
import json
from tools.changes import CHANGE_RECORD_VERSION
from tools.filesystem import delete_file, write_file
target = %r
write_file.invoke({"path": target, "content": "x\n"})
r = json.loads(delete_file.invoke({"path": target}))
print(json.dumps({"version": CHANGE_RECORD_VERSION, "r": r}))
""" % str(ws / "demo.txt")],
        capture_output=True, text=True, cwd=str(ws), timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["version"] == 1
    r = payload["r"]
    assert r["action"] == "delete"
    assert r["type"] == "file"
    assert r["change"]["previous_hash"].startswith("sha256:")
    assert r["change"]["new_hash"] is None
    assert not (ws / "demo.txt").exists()
```

### 6.16 CI 工作流文件已交付（临时例外 E-01 到期闭合）

> **⚠️ 本条是宪法强制项，不是可选项**：宪法 §6.3 的临时例外 **E-01**（"F001-P1 与 F001-P2
> **均不**交付 `.github/workflows/ci.yml`）的**过期时间是「F001-P3 结束前」** —— 即
> **本 Phase MUST 交付该文件**（或由 Maintainer 显式决定转为正式纳入宪法；本 Phase 采用前者）。
> 若 15 个场景断言全绿而 `ci.yml` 缺失 → 临时例外已过期 → **F001-P3 收尾即宪法违例**。

```python
def test_scenario_16_ci_workflow_delivered():
    """场景 16：CI 工作流文件已交付（宪法 §6.3 临时例外 E-01 到期闭合）"""
    workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert workflow.is_file(), "临时例外 E-01 已到期：.github/workflows/ci.yml MUST 在本 Phase 内交付"
    content = workflow.read_text(encoding="utf-8")
    # 最小内容骨架（= plan G5 记录的 CI 最小内容）
    assert "pytest tests/" in content
    assert "--cov=donkey.core" in content
    assert "--cov-fail-under=80" in content
    assert "ruff check" in content
    assert "mypy" in content
```

> **注意**：本脚本是**黑盒**的 —— 它只断言**仓库内的一个文件是否存在且含关键命令**，
> MUST NOT import `donkey.*` 业务代码，也 MUST NOT 跑 CI（CI 自身的执行属 GitHub 侧）。

### 6.17 退出条件总览

verify_phase_f001_p3.py 的 15 个 `test_*` 函数 + §6.16 的 CI 交付条件全部 PASS → F001-P3 完成。**F001 整体完成**。

---

## 7. 可执行测试命令列表（"Phase 完成" 的硬性证据）

按以下顺序执行，全部 PASS 即视为 Phase 完成（**Phase 完成 = F001 `donkey init` 整体完成**）：

1. **前置 Phase 套件（F001-P1 + F001-P2）**：
   ```bash
   pytest tests/e2e/phase/verify_phase_f001_p1.py -v
   pytest tests/e2e/phase/verify_phase_f001_p2.py -v
   pytest tests/unit/test_init_workspace.py -v
   pytest tests/unit/test_template_skeleton.py -v
   ```
   必须全绿（验证 F001-P1 / F001-P2 退出条件未被破坏）。

2. **本 Phase 套件**：
   ```bash
   pytest tests/unit/test_builtin_tools.py -v                    # 至少 15 个
   pytest tests/integration/test_init_to_load.py -v              # 至少 4 个
   pytest tests/e2e/phase/verify_phase_f001_p3.py -v             # 15 个场景断言
   ```

3. **静态检查**：
   ```bash
   ruff check donkey/ tests/
   mypy donkey/ tests/
   ```

4. **CLI 手动冒烟（可选）**：
   ```bash
   donkey init /tmp/test-ws
   ls /tmp/test-ws/tools  # 应含 filesystem.py / commandline.py / webfetch.py / changes.py / __init__.py / README.md
   python -c "import sys; sys.path.insert(0, '/tmp/test-ws'); from tools.commandline import run_shell; print(run_shell.invoke({'command': 'echo hi'}))"
   # 变更记录冒烟：写入 → 打印 change 记录（含 unified_diff / previous_hash）
   python -c "
   import sys, json; sys.path.insert(0, '/tmp/test-ws')
   from tools.filesystem import write_file
   print(write_file.invoke({'path': '/tmp/test-ws/smoke.txt', 'content': 'hello\n'}))
   print(json.loads(write_file.invoke({'path': '/tmp/test-ws/smoke.txt', 'content': 'world\n'}))['change']['unified_diff'])
   "
   ```

5. **完整 CI 套件**：
   ```bash
   pytest tests/ -v
   ```
   F001-P1 / P2 / P3 全部测试 PASS；其它 Phase（F002 ~ F006）的测试允许 FAIL。

6. **CI 工作流交付自检**（宪法 §6.3 临时例外 E-01 到期，**本 Phase MUST 交付**）：
   ```bash
   test -f .github/workflows/ci.yml && echo "OK ci.yml 已交付" || echo "FAIL E-01 已到期，ci.yml 缺失"
   grep -cE "pytest tests/|--cov=donkey.core|--cov-fail-under=80|ruff check|mypy" .github/workflows/ci.yml
   ```
   期望：文件存在，且 5 条关键命令全部命中（≥ 5）。

---

## 8. 绝对不做清单（推迟到后续 Phase / Feature）

| 不做的内容 | 推迟到 |
|---|---|
| 任何 LangChain 中间件挂载（`ToolErrorMiddleware` / `ToolRetryMiddleware` / `ModelRetryMiddleware` / `SummarizationMiddleware` / `ModelCallLimitMiddleware` / `PIIMiddleware` / `TodoListMiddleware` / `LLMToolSelectorMiddleware` / `ContextEditingMiddleware` / `FilesystemFileSearchMiddleware`） | F004 (`donkey run`) |
| `init_chat_model` / 模型连通性测试（`providers/` 目录解析 + ping） | F002 (`donkey load`) |
| sqlite3 数据库文件 schema 构造（含 `memory/sessions.sqlite3` 的 SqliteSaver 表 + `sessions_metadata` + 索引） | F001-P2（`template_skeleton` 已实现 schema builder；详见 F001-P2 sqlite3_templates 模块） |
| 任何 `donkey load` 静态检查（`providers/` 字段 / mcp/mcp.json 字段 / SKILL.md 字段） | F002 (`donkey load`) |
| Skills 自研 loader 实现（Level 1 扫描 + Level 2 读取 + Level 3 工具集成 = `core/skills/loader.py`） | F004-P2 (`donkey run` → Skills 加载) |
| `donkey session list` / `new` / `remove` / `import` 等子命令 | F003 (`donkey session`) |
| `donkey run` Agent Loop / LangGraph 图编译 / 10 个 v1 中间件挂载 | F004 (`donkey run`) |
| `donkey web` 前端 | F005 |
| `donkey gui` Electron 包壳 | F006 |
| 引入 `ShellToolMiddleware` / `FilesystemMiddleware`（deepagents）/ `SubAgentMiddleware` / `SkillsMiddleware`（deepagents）等任何禁用中间件 | 永不使用（N-02 / N-12 / 宪法 §2.7.2） |
| workspace 路径 basename 命名校验（v1 不引入） | v2+ |
| 修改 F001-P1 / F001-P2 已实现的代码（仅允许**追加**——F001-P1 的 4 个 init 函数 / F001-P2 的 `render_templates` / `manifest.py` / `sqlite3_templates.py` 一律不动） | — |
| 引入 langsmith 任何形态 | 永不使用（N-12 / §3.2 永不使用清单） |
| 引入 deepagents 包 | 永不使用（宪法 §3.2） |
| 在 `tools/filesystem.py` 内实现 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 在 F004 中间件域接管） | —（永不在 `tools/filesystem.py` 内实现） |
| **diff 审阅 UI / 人工审批 / 回滚流程**（引擎层能力，AC-5） | 引擎层 v4（"diff 展示"）/ fork 路线（立项书 §1.2.3 结论 2） |
| **引擎层 diff 中间件**（`after_agent` 拦截变更 + `HumanInTheLoopMiddleware` 中断-恢复） | F004（v2 HITL）+ v4 diff 展示 |
| **三方合并 / 冲突解决 / patch 应用算法**（`git apply` 式） | 永不在材料层实现 |
| **把 `run_shell` 的文件副作用纳入变更记录**（shell 绕过 `@tool` 写路径） | v4 用 workspace 快照对账（已知缺口，§2.9） |
| 在 `tools/changes.py` 内加 `@tool`（它是**契约库**，不是工具） | —（永远 0 个 `@tool`） |
| F002 的 tools 扫描器"每个 `tools/*.py` 至少 1 个 `@tool`"的假设（`tools/changes.py` 有 **0** 个） | **风险登记项**：F002 必须容忍"无 `@tool` 的辅助模块"（`tools/__init__.py` 已是先例） |

---

## 9. 技术栈与依赖硬约束

- **Python 3.11+**；
- **HTTP 客户端**：`httpx`（用于 `tools/webfetch.py` **模板**与测试）；`pytest-httpx` 用于 mock；
  - **依赖归属（MUST 写清，否则读者会误判 SC-021 变成 2）**：
    - `httpx` 是**渲染进用户工作区**的**模板依赖** —— 用户在自己的 workspace 里跑
      `tools/webfetch.py` 时才需要它；**donkey 自身的运行期依赖不变，仍恰为 1 个**
      （`langgraph-checkpoint-sqlite`，spec SC-021 / FR-067 **不受影响**）；
    - `pytest-httpx` 是**新增 dev 依赖** —— MUST 声明到 `pyproject.toml` 的
      `[project.optional-dependencies].dev`（**不**进 `[project].dependencies`）。
      F001-P1 / P1-P2 均明确「本 Phase 无新增 dev 依赖」，**本 Phase 是第一次**；
- **LangChain 内置工具装饰器**：`from langchain_core.tools import tool` —— `@tool` 是 LangChain 内置功能，**不**违反 N-04 / N-12；N-04 仅约束 `cli` / `web` / `gui` 客户端不直接 import langchain，**`donkey.core` 允许使用 langchain 库 API**；
  - **N-12 边界（见 §9.1 的补充说明）**：`langchain-core` 会把 `langsmith` 作为**硬传递依赖**装到磁盘，
    且 `from langchain_core.tools import tool` 会让 `langsmith` 进入**导入方进程**（实测
    `langsmith in sys.modules == True`）。按宪法 **D-17**，N-12 的约束对象是 **donkey 自有代码路径**
    （`donkey.core` / `cli` / `web` / `gui`）的 import 与使用；`tools/*.py` 是**渲染进用户工作区**的
    产物、属**用户代码路径** → **合规**。但 MUST 在 P3 的 spec 中显式登记这条推理（否则按
    quickstart §1 的门禁冒烟口径复核时会误判为门禁失败）；
- **测试**：pytest + pytest-httpx；
- **静态检查**：ruff + mypy；
- **CI**：GitHub Actions —— **本 Phase MUST 交付 `.github/workflows/ci.yml`**（宪法 §6.3 临时例外
  E-01 到期；见 §6.16）。

### 9.1 永不使用清单

- ❌ LangSmith 任何形态（详见 N-12）；
- ❌ deepagents 包（`create_deep_agent` / FilesystemMiddleware / SubAgentMiddleware / RubricMiddleware / SkillsMiddleware / MemoryMiddleware）；
- ❌ `ShellToolMiddleware`（持久 shell + HITL 冲突，由 `tools/commandline.py` 替代）；
- ❌ subagent / 子智能体任何目录或字段；
- ❌ `tools/filesystem.py` 内含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管）；
- ❌ `import langsmith` 或 `langchain.langsmith` / `langchain_community.langsmith` / `langgraph.langsmith` 等任何 langsmith.* 子包。

> **边界说明（N-12 × D-17，2026-10-23 澄清）**：本 Phase 的 `tools/*.py` 模板会
> `from langchain_core.tools import tool` —— `langchain-core` 把 `langsmith` 作为**硬传递依赖**，
> 因此 `langsmith` 会（a）被装到磁盘、（b）在**导入该模板的进程**里进入 `sys.modules`
> （实测 `True`）。按宪法 **D-17**，N-12 约束的是 **donkey 自有代码路径**的 import 与使用 ——
> `tools/*.py` 是**渲染进用户工作区**的产物，属**用户代码路径**，donkey 自身**永不 import** 它
> → **合规**。落地要求：
> ① 本 Phase 的 spec MUST 显式登记这条边界推理；
> ② quickstart §1 的门禁冒烟（`langsmith in sys.modules` MUST 为 False）MUST 限定为
> **donkey 自有代码路径**的导入链 —— 不得拿"用户 import 渲染产物"的语境去复核它；
> ③ 渲染产物本身 MUST NOT 含任何 langsmith 字样（SC-017 的 workspace 侧）。

### 9.2 分层架构硬约束（N-01 ~ N-12）

| 编号 | 条款 | 本 Phase 落地 |
|---|---|---|
| **N-01** | workspace 内禁止 `agent.py` / `main.py` | ✓ 生成的 3 个 builtin tool 文件 + `tools/changes.py` **均不含** `if __name__ == "__main__": sys.exit(...)` 形式入口（Skills example 的 `scripts/example.py` 是 Level 3 演示脚本，**允许**含 `__main__` 块，但**不是** workspace 入口） |
| **N-02** | 禁止 subagent / 子智能体相关目录或字段 | ✓ 生成的 3 个 builtin tool 无任何 subagent 字段；Skills example 不涉及 subagent |
| **N-03** | `donkey.core` 禁止 import `cli` / `web` / `gui` | ✓ 本 Phase **不修改** `core/workspace/` 下任何已有模块（`init.py` / `manifest.py` / `sqlite3_templates.py` 一律不动），只追加 `.txt` 模板源；仅在 `core/exceptions.py` 追加 1 个错误类、`core/exit_codes.py` 追加 1 个常量（**均不引入新 import**） |
| **N-04** | `cli` 禁止直接 import `langchain` / `langgraph` / `sqlite3` | ✓ 本 Phase 仅修改 `cli/cli_client.py` 1 行（追加异常映射）；无 langchain import |
| **N-05** | `donkey.core` 禁止 import `argparse` / `sys.argv` / `click` / `typer` | ✓ |
| **N-08** | exit code 段位不重叠 | ✓ 本 Phase 占 exit 4，落在 F001 段位 1–10 内 |
| **N-11** | v1 必须同时交付 cli / web / gui 三种客户端 | 本 Phase 不涉及客户端（仅 init 业务）；cli 端 F001-P1 已落地；web / gui 推迟到 F005 / F006 |
| **N-12** | 禁止 LangSmith | ✓ |

---

## 10. 验收标准（business AC）

| 验收项 | 说明 |
|---|---|
| **AC-1（workspace 加载通过率 100%）** | 本 Phase 仅保证"生成模板"；AC-1 的通过口径是"**配置完成后** 100% 通过"——出厂态（26 个 stub 全 `enabled = false` + `api_key = ""`）在 F002 **静态检查**阶段即报 exit 11（零 enabled provider + 三步配置指引），属**预期行为**（详见立项书 §3.2.3 AC-1 ③ + 宪法 §4.6 AC-1 出厂态豁免）；本 Phase 不承担 F002 的 9 项检查 |
| **AC-2（路径无关）** | init 后 workspace 移到任意路径，import 路径仍能正确发现 `@tool` 函数（本 Phase 通过 `tools/__init__.py` + 集成测试落地） |
| **AC-3（init 幂等）** | 重复执行 `donkey init <已存在 ws>` 不破坏用户内容；`--force` 仅重置 manifest 内模板，不动 manifest 外（用户内容） |
| **AC-4（换 workspace 切换模型 / 工具 / Skills / 提示词）** | workspace 模板含 `instruction.md` / `providers/` / `tools/` / `skills/`，未来 F004 run 时模型 / 工具 / Skills / 提示词均从 workspace 加载——本 Phase 完成"workspace 模板就绪"前置条件 |
| **AC-5（v1 模板不承诺 diff 审阅）** | workspace 内不含 `agent.py` / `main.py` 等 diff 审阅入口。**但**材料层已按 §2.9 交付"变更记录"（原子写 + 旧内容 hash + unified diff + `dry_run` 预览 + `expected_hash` 乐观锁，契约版本 `CHANGE_RECORD_VERSION = 1`）作为 v4"diff 展示"的接入面——**交出原材料 ≠ 实现审阅流程**，不违反 AC-5 |

**技术验收**：F001 段位 1–10 中 4 个码值（1 / 2 / 3 / 4）全部实测通过；预留码 5–10 不触发；F001 整体完成。

---

## 11. Spec 输出格式要求（给 `/speckit.specify` 的提示）

执行 `/speckit.specify` 后生成的 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md` **必须**包含：

1. **User Stories**：按优先级 P1 → P15 列出 15 个核心场景（对应 §6 的 15 个 verify 场景断言）；
2. **Functional Requirements (FR-001 ~ FR-NNN)**：覆盖 §4 的 10 个子节（4.1 ~ 4.10），含 9 个 `@tool` 函数签名、**变更记录契约（`CHANGE_RECORD_VERSION = 1` + §2.9 的 15 个字段 schema + 四条硬规则 R-D1 ~ R-D4 + 只增不改三原则）**、Skills 三层文件清单、manifest 追加条目；FR 中如需引用 F001-P1 / F001-P2 已实现的函数（`validate_init_request` / `render_templates` / `init_workspace_inner` 等），仅引用**函数签名与行为契约**，不复述其实现细节（详见 §3.2 函数契约小节）；
3. **Edge Cases**：本 Phase 边界条件（用户自定义 `tools/*.py` 不被 `--force` 删 / 用户 rm builtin tool 后 init 补齐 / Skills Level 3 目录被 `--force` 递归清空 / `expected_hash` 不匹配导致写入被拒 / 写失败后旧内容完好 / `run_shell` 副作用不进变更记录 / 等）；
4. **Success Criteria (SC-001 ~ SC-NNN)**：可量化的退出条件（"15 个 verify 场景断言全部 PASS + CI 工作流文件已交付"、"F001-P1 7 个 + F001-P2 14 个断言仍全绿"、"单测 15 个 + 集成测试 4 个 + verify 15 个全绿"、"变更记录 schema 字段集与 §2.9 完全一致（键集合断言）"、"ruff + mypy 零 error"等）；
5. **Key Entities**：`BuiltinToolGenerationError` 异常类；`filesystem.read_file` / `write_file` / `copy_file` / `move_file` / `delete_file` / `list_dir` / `stat` / `commandline.run_shell` / `webfetch.fetch_url` 共 9 个 `@tool` 工具函数；**变更记录（change record）契约**（`tools.changes` 契约库 + `CHANGE_RECORD_VERSION` + 记录字段集 + `FileChangedError`）；Skills Level 1/2/3 三层模型；
6. **Assumptions**：F001-P1 (`cli_validation`) + F001-P2 (`template_skeleton`) 均已完成并退出；`langchain_core.tools.tool` 装饰器可用；`httpx` 与 `pytest-httpx` 已安装；**diff 审阅归引擎层**（v4 或 fork，AC-5）——本 Phase 只交出变更记录。

**Spec 禁止**包含的内容（留给 `/speckit.plan` 处理）：

- 具体实现步骤（如"先写 filesystem.py 再写 commandline.py 再写 webfetch.py"）—— plan 才规定顺序；
- 测试用例的具体代码（除 §6 / §4.8 / §4.9 中已作为参考示例给出的）；
- 依赖包版本号。

---

**End of F001-P3 spec input. F001 `donkey init` 整体完成的最后 Phase.** 将本文件整体作为参数传入 `/speckit.specify` 即可。
