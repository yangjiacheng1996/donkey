---

description: "Task list for F001-P2 template_skeleton —— donkey init workspace 模板骨架幂等生成"
---

# Tasks: F001-P2 `template_skeleton` —— `donkey init` workspace 模板骨架幂等生成

**Input**: Design documents from `specs/001-donkey-init-workspace/phase-2-template-skeleton/`
（spec.md · plan.md · research.md · data-model.md · contracts/ ×4 · quickstart.md）

**Prerequisites**: plan.md（必需）、spec.md（必需，用户故事）、research.md、data-model.md、contracts/、quickstart.md

**Tests**: 含测试任务 —— spec FR-055 明确要求**不少于 16 个单元测试用例**并逐条列出必备类别，FR-058 要求覆盖 sqlite3 构造器三项能力，FR-059 要求 14 个黑盒场景断言函数。故本清单**强制**按 TDD 组织（先写测试 → 确认失败 → 再补实现）。

**Organization**: 任务按用户故事分组。**本 Phase 的 14 个用户故事是"验收切片"而非"实现切片"** —— 14 个故事 ↔ 14 个 e2e 黑盒场景一一对应，但实现上共享同一套渲染引擎与同一份模板清单（data-model.md §1）。故本清单的组织原则为：

| 层次 | 内容 | 对应 Phase |
|---|---|---|
| **共享引擎** | 渲染内核 + 工作区清单 + sqlite3 构造器 + 门面（被 14 个故事共同依赖） | Phase 2 ~ Phase 5（Foundational） |
| **模板资产** | 37 个源文件 + 46 条清单条目（决定"落地什么"） | **全部在 Phase 6（US1）**；US2 ~ US14 只做内容质量校验与行为硬化 |
| **行为硬化** | 每故事的幂等 / 强制 / 边界语义与对应单测 | 各故事阶段 |
| **黑盒验收** | 14 个场景断言函数（跨故事集成验收） | Phase 20 |

> ⚠️ **为什么 e2e 脚本集中在 Phase 20 而不是分散到 14 个故事阶段**：spec FR-059 要求 14 个 `test_scenario_*` 函数位于**同一个文件** `tests/e2e/phase/verify_phase_f001_p2.py`；且**场景 1 一次性断言全部 46 条落地物**（含 26 份 provider 配置，**其资产由 US1 在 Phase 6 一次性就位**）→ 但 14 个场景函数同文件，在 US1 阶段写场景 1 会造成"同一文件被多阶段反复追加"的串行冲突，会破坏"故事独立可测"。故：故事级独立可测性由**各故事的单元测试**承担（各阶段独立落盘于 `tests/unit/test_template_skeleton.py`），黑盒脚本作为**跨故事集成验收**集中交付。故事 ↔ 场景对照表见「Dependencies & Execution Order」。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成任务的依赖）
- **[Story]**: 该任务归属的用户故事（US1 ~ US14）
- 描述中 MUST 含**精确文件路径**

> **编号编排说明**：任务 ID 按**逻辑分组**编排（T058 属 Phase 2 的错误语义组、T015 属 Phase 5 的门面组），**非文档序**；ID 一经分配 MUST NOT 重排或复用。
>
> **T083 ~ T086 的来源**：`/speckit.analyze` 三文档交叉复核后的**定点修订**新增 —— T083（步骤 ⑤ 失败不回滚，spec 澄清 #26）/ T085（步骤 ③ 一切失败含 `ENOSPC` 归退出码 `2`）/ T084（工作区重命名后保留旧名，spec 澄清 #27）/ T086（B1 ~ B12 全套汇总，承接 T032 拆分）。四者均为 **FR-055 的 16 类之外**的补充类别，MUST NOT 计入或替换 FR-055 的 16 类。
>
> **T087 ~ T091 的来源**：`/speckit.analyze` 三文档交叉复核后新增的 **5 条内容级断言任务** —— FR-043（`instruction.md` 标题 + 三留白小节）/ FR-050（工作区说明文档目录职责）/ FR-051（三份目录说明文档内容契约）/ FR-052（记忆库说明文档内容契约）/ FR-053（`.gitignore` 9 行内容）。这 5 条 FR 原先**只有实现任务、没有任何断言任务**（SC-014 的"一致性三处"按设计不含 `instruction.md`，故 FR-043 的验证落点确实为零）。五者均为 **FR-055 的 16 类之外**的补充类别，MUST NOT 计入或替换 FR-055 的 16 类 —— FR-055 / SC-008 的"16 个类别 / 不少于 16 个用例"口径**保持不变**。
>
> **计数口径的权威源**：计数口径（`templates_loaded` / `files_created` / `files_skipped`）的**唯一权威源 = spec FR-017 / FR-026**；plan R-08、data-model §5、contracts（library-api §2 A3~A5 / §3.2、cli-contract §3.1）与本清单各处均为**镜像** —— 口径变更 MUST 先改 spec，再逐处同步镜像。

## Path Conventions

- **单包结构**：仓库根即包根 `donkey/`；`donkey/core/` 为引擎层、`donkey/cli/` 为客户端层
- **测试**：`tests/unit/`（函数级）、`tests/e2e/phase/`（黑盒子进程验收）、`tests/integration/`（本 Phase 为空占位）
- **模板资产**：`donkey/core/workspace/templates/`（安装包内，与源码同树）

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 引入本 Phase 唯一的运行期依赖并闭合依赖链门禁

- [X] T001 在 `pyproject.toml` 的 `[project].dependencies` 声明 `langgraph-checkpoint-sqlite>=3.1,<4`（当前该列表为**空** `[]`）；**MUST NOT** 改动 `[project.optional-dependencies].dev`（`pytest>=7` / `pytest-cov` / `ruff` / `mypy` 已就位，本 Phase 无新增 dev 依赖）、`[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`（含 `python_files = ["test_*.py", "verify_phase_*.py"]` —— 新脚本 `verify_phase_f001_p2.py` 靠它被 pytest 收齐，plan G13）。**`[tool.setuptools.package-data]` MUST **核对**（**该显式条目已在工作树就位** —— `"donkey.core.workspace.templates" = ["**/*.txt", "**/*.json", ".gitignore.txt"]`；若缺失则 MUST 补上）。**实测依据**：setuptools `build_py.find_data_files` 用 `glob(..., recursive=True)`，而 `glob` 会过滤**以 `.` 开头的文件名** → 隐藏源 `templates/.gitignore.txt` 默认**不进 wheel**（已用真实 wheel 构建实证：`manifest.json` ✅、`providers/openai.toml.txt` ✅、`.gitignore.txt` ❌）。后果：editable 安装（`pip install -e .`）无感，但 wheel / sdist 安装时清单条目 `.gitignore` 的源缺失 → FR-007 → 退出码 `3` → **`donkey init` 整体不可用**（spec FR-041）。已实测补该条目后 wheel 内含 `.gitignore.txt`。**版本下界 MUST 取 `>=3.1`**：`>=3.1` 才能解析出 `langgraph-checkpoint>=4.3.0`；本机用户级 site-packages 存在 `sqlite 3.1.1` + `checkpoint 4.2.0` 的**不兼容组合**，导入即 `ImportError: cannot import name 'writes_sort_key'`（research.md R-01）。MUST NOT 声明其它第三方运行期依赖（spec FR-067 / SC-021：恰为 1 个直接依赖）
- [X] T002 执行 `.venv/bin/pip install -e ".[dev]"`（仓库内 `.venv`，与 quickstart §0 一致），核对 `.venv/bin/pip list` 中 `langgraph-checkpoint` **≥ 4.3.0** 且 `langgraph-checkpoint-sqlite` 在 `3.1.x`；若解析结果不满足，回到 T001 调整版本约束后重装
- [X] T003 执行 quickstart §1 的**环境自检**：① 依赖解析自检；② 上游 saver 冒烟（**MUST 直接跑 quickstart §1 ② 的完整脚本**——`from langgraph.checkpoint.sqlite import SqliteSaver` → `SqliteSaver(conn).setup()` → **再补一步 `CREATE TABLE IF NOT EXISTS sessions_metadata (...)`** → 断言 3 张表建成）→ **期望打印 `OK 3 tables` 且 `langsmith in sys.modules` 为 `False`**。**⚠️ 步骤 ② 的"3 张表"来自「上游 2 张（`checkpoints` / `writes`）+ 自管 1 张（`sessions_metadata`）」—— 只跑 `setup()` 只会得到 `OK 2 tables`，那是脚本漏了补建 `sessions_metadata`，不是门禁失败**。**langsmith 进入进程即为门禁失败**（宪法 N-12 违例），MUST 停止实施并按 quickstart §9 排查表处置（research.md R-02：实测导入上游 saver 新增 471 个模块、langsmith 相关 0 个）

**Checkpoint**: 依赖链就位且 N-12 门禁实证闭合

---

## Phase 2: Foundational — 错误类 / 退出码 / 工作区清单模块

**Purpose**: 建立被 14 个故事共同依赖的"错误语义"与"工作区清单"两块底层资产

**⚠️ CRITICAL**: 本阶段未完成前，任何用户故事都不能开工

- [X] T004 [P] 在 `donkey/core/exceptions.py` 追加 `class TemplateGenerationError(WorkspaceInitError)`：docstring MUST 标注 `exit code: 3` 并**引用**本 spec『模板生成类失败的 7 类成因（权威分类法）』段与 [contracts/exit-codes.md](contracts/exit-codes.md) §4 的 7 行表 —— **只引用、MUST NOT 逐条复述该清单**（spec FR-035 明文禁止错误类自行复述；7 类清单的唯一权威源是 spec 段、其镜像在 exit-codes §4，避免出现第 5 份副本而漂移）+ 用户修复动作说明；**MUST NOT** 修改既有的 `DonkeyError` / `WorkspaceInitError` / `PathNotFoundError` / `PathPermissionError`（spec FR-035，异常层次 MUST 保持为 总基类 ← F001 基类 ← 三个具体错误类）；**MUST 同步更新本模块 docstring 顶部的异常层次树**，使其含 `TemplateGenerationError`。**同一模块内追加模板类失败的"下一步"文案常量 `_NEXT_STEP_TEMPLATE`**（形如 "下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。"）—— MUST 与 P1 已有的 `_NEXT_STEP`（路径类，位于 `donkey/core/workspace/init.py`）**并列而非替换**，二者语义不同（research.md R-12 / spec FR-069）。**MUST NOT 把 `_NEXT_STEP_TEMPLATE` 放在 `init.py`** —— `init.py` 需 import `manifest.py`，而 `manifest.py` / `sqlite3_templates.py` 也需要该文案，常量若在 `init.py` 会形成 `manifest.py → init.py → manifest.py` 的循环 import；**MUST NOT** 改动 P1 已有的 `_NEXT_STEP`（FR-029 禁止改动 P1 已有代码）
- [X] T005 [P] 在 `donkey/core/exit_codes.py` 把 `EXIT_CODE_TEMPLATE_GENERATION = 3` 的注释从"属 F001-P2（子段 2）/ 本阶段 MUST NOT 使用"改为"**本阶段启用**（模板骨架生成失败）"；**常量值 MUST 保持 3 不变**（P1 已建档），`EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` MUST 仍标注为"P3 预留、本阶段不触发"（spec FR-037：退出码 `4` / `5-10` MUST NOT 被本阶段任何代码路径触发）
- [X] T058 在 `donkey/cli/cli_client.py` 的模块级 `_EXCEPTION_TO_EXIT_CODE` 映射表**追加 1 行**：`TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION`（**MUST 从 `donkey.core.exit_codes` 导入该常量，MUST NOT 写字面量 `3`** —— 退出码不得双源，contracts/exit-codes.md §3）；基类 `WorkspaceInitError` 仍不登记、未登记子类仍兜底到 `1`；**MUST NOT** 改动 `main()` 的 `try/except WorkspaceInitError` 结构 —— 按 `type(e)` 查表自动生效（spec FR-036）。**本任务不带 [Story] 标签** —— 它承接的是 FR-036（客户端异常映射），与任何单个用户故事无关；spec 的需求追溯矩阵亦把 FR-036 归在「§4.4 客户端映射」。**从 Phase 17 移至本阶段**（与 T004 / T005 同属"错误类与退出码语义"，原挂在 US12 下会造成 story 标签与任务内容错配）
- [X] T006 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 **5** 个工作区清单测试（FR-055 的第 12~15 项）——`test_manifest_write_new`（新 workspace → 写出 `manifest.json`）/ `test_manifest_skip_existing_no_force`（已存在且无 force → 内容不被覆盖、`created_at` 保留原值）/ `test_manifest_refresh_force`（已存在 + force → 覆盖且 `created_at` 刷新）/ `test_manifest_field_minimal`（字段集合**恰为** `version` / `name` / `created_at` / `donkey_version` 四项，无第五项；**并断言取值** —— `version` 为整数 `1`、`donkey_version` 为硬编码字符串 `"0.1.0"`（MUST NOT 随内部 `__version__` 漂移）、`name` 等于传入名 —— spec FR-019 / FR-021）/ `test_manifest_json_encoding`（**新增** —— 写入结果的**编码形态**：缩进 **2 空格**、非 ASCII 字符**保留原文**（MUST NOT 被转义为 `\uXXXX`）、**UTF-8 无 BOM** —— spec FR-022）。**FR-055 的第 16 类由 T081 承接**。**写完先跑一次确认失败**（模块尚不存在 → ImportError / AttributeError），再进入 T081 / T082 / T007
- [X] T081 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_manifest_read_invalid_json_raises`（spec FR-055 的**第 16 类** / FR-018 / US6 场景 4）：在临时目录下写入**非法 JSON** 的 `manifest.json` → 调用 `read_workspace_manifest` MUST 抛 `TemplateGenerationError`（退出码 `3`），MUST NOT 抛 `PathNotFoundError`，MUST NOT 返回 `None`；再写 `test_manifest_force_overwrites_invalid_json`：已存在**非法 JSON** 的 `manifest.json` + `--force` → MUST 被覆盖为**合法**内容（4 字段、`created_at` 刷新为当前时刻），MUST NOT 抛异常（spec §Edge Cases「其它边界」）。**写完先跑一次确认失败**（模块尚不存在 → ImportError），再进入 T082 / T007。
- [X] T082 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_manifest_read_missing_returns_none`（spec FR-018 —— 工作区清单的**读取**能力在文件不存在时 MUST 返回「无」（`None`），MUST NOT 抛 `TemplateGenerationError`、MUST NOT 抛 `PathNotFoundError`）：对**不存在**的 `manifest.json` 调 `read_workspace_manifest` → 断言返回 `None`；再写 `test_ensure_manifest_equivalent_to_write`（spec FR-023 / research.md R-10 / contracts/library-api.md §4）：断言 `ensure_workspace_manifest` 与 `write_workspace_manifest` 在两个组合下结果**严格等价** —— ① 「坏 JSON + force」：二者 MUST 都把 `manifest.json` 覆盖为**合法**内容（4 字段、`created_at` 刷新为当前时刻），MUST NOT 抛异常；② 「坏 JSON + 不带 force」：二者 MUST 都抛 `TemplateGenerationError`（退出码 `3`）且 MUST NOT 覆盖原文件。**写完先跑一次确认失败**（模块尚不存在 → ImportError），再进入 T007。
- [X] T007 创建 `donkey/core/workspace/manifest.py`（**独立模块，MUST NOT** 塞进 `init.py` —— plan Complexity Tracking 已登记该拆分理由）：`WORKSPACE_MANIFEST_FILENAME = "manifest.json"` + `write_workspace_manifest(workspace_path: Path, name: str, force: bool) -> dict` + `read_workspace_manifest(workspace_path: Path) -> dict | None` + `ensure_workspace_manifest(workspace_path: Path, name: str, force: bool) -> dict`（spec FR-019 —— 字段 MUST **恰好且仅**为四项；spec FR-023 —— 「确保存在」便捷封装）。字段 MUST **恰好且仅**为四项：`version`（整数，v1 填 `1`）/ `name`（字符串）/ `created_at`（`datetime.now(timezone.utc).isoformat()`，**带时区**）/ `donkey_version`（**硬编码 `"0.1.0"`**，MUST NOT import 内部 `__version__` —— 循环依赖，spec FR-021）。写入 MUST 用 `json.dumps(manifest, indent=2, ensure_ascii=False)` + **UTF-8 无 BOM**（spec FR-022）。`write_workspace_manifest` 的覆盖语义：**无 force 且已存在 → 不覆盖、返回既有内容**（`created_at` 保留原值）；**有 force → 覆盖并把 `created_at` 刷新为当前时刻**；**不存在 → 无条件创建**（spec FR-020）。`read_workspace_manifest`：文件不存在 → 返回 `None`；JSON 非法 → 抛 `TemplateGenerationError`（exit 3，spec FR-018）。`ensure_workspace_manifest` MUST **委托** `write_workspace_manifest` 的同一判定顺序（research.md R-10 / contracts/library-api.md §4）：**带 force → 直接覆盖（MUST NOT 先读旧文件）**；不带 force 且已存在 → 读（解析失败 → `TemplateGenerationError` exit 3）/ 不覆盖并返回既有内容；不存在 → 无条件创建。二者语义 MUST 严格等价（含'坏 JSON + force → 覆盖为合法内容'与'坏 JSON + 不带 force → exit 3'两个组合）。

**Checkpoint**: 错误类 + 退出码 + 客户端异常映射 + 工作区清单模块就位，**9** 个清单单测全绿（T006 的 5 个 + T081 的 2 个 + T082 的 2 个）

---

## Phase 3: Foundational — sqlite3 结构构造器

**Purpose**: 交付"程序化建库"能力（宪法 D-05），服务 US1 / US13 / US14

- [X] T008 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 3 个构造器测试（FR-058 的三项能力）——`test_build_sessions_sqlite_schema`（调用后 `sqlite_master` 的 `type='table'` 集合含 `checkpoints` / `writes` / `sessions_metadata`；`type='index' AND tbl_name='sessions_metadata'` 含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at`；`sessions_metadata` 记录数为 `0`）/ `test_build_store_and_knowledge_are_empty`（两个占位文件各 0 表 0 索引）/ `test_build_sessions_sqlite_idempotent`（对同一路径连调两次 → 表与索引集合不变，既有表不被破坏）。**索引断言 MUST 用 `in` / `<=` 判定，MUST NOT 用集合相等** —— `sqlite_autoindex_*` 是 PRIMARY KEY 自动索引且其 `tbl_name` 亦为 `sessions_metadata`（research.md R-05）
- [X] T009 创建 `donkey/core/workspace/sqlite3_templates.py`（**独立模块，MUST NOT** 塞进 `init.py` —— 把"程序化建库"与"路径校验"两种关注点分开，plan Complexity Tracking）：`build_sessions_sqlite(path: Path) -> None` + `build_store_sqlite(path: Path) -> None` + `build_knowledge_sqlite(path: Path) -> None`。`build_sessions_sqlite` 的实现顺序 MUST 为：`sqlite3.connect(path)` → `SqliteSaver(conn)` → **`saver.setup()`（实例方法！）** → `CREATE TABLE IF NOT EXISTS sessions_metadata (...)`（6 字段：`thread_id TEXT PRIMARY KEY` / `title TEXT NOT NULL` / `created_at REAL NOT NULL` / `updated_at REAL NOT NULL` / `donkey_version TEXT NOT NULL` / `first_prompt TEXT`）→ `CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title ON sessions_metadata(title)` → `CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at ON sessions_metadata(updated_at)` → `commit()` → `close()`。**import 路径 MUST 为 `from langgraph.checkpoint.sqlite import SqliteSaver`**（**MUST NOT** 写成 `from langgraph_checkpoint_sqlite import ...` —— 那是分发包名，导入名是 `langgraph.checkpoint.sqlite`，research.md R-01）；**MUST NOT** 写成 `SqliteSaver.setup(conn)`（非实例调用会把 `conn` 误绑到 `self` 上抛 `AttributeError` —— 上游结构文档 §8 Q1 与 research.md R-01 / R-04 双重确认）；**MUST NOT** 手写 `checkpoints` / `writes` 的 DDL（spec FR-031：结构由上游维护，donkey 不承担漂移风险）。`build_store_sqlite` / `build_knowledge_sqlite` **MUST 只创建空的 sqlite3 文件**（0 表 0 索引，MUST NOT 建占位表；spec FR-032 / 宪法 D-11）—— **connect 之后 MUST NOT 执行任何 DDL / DML**（连 `CREATE TABLE` 都不许，否则表数不为 0）。三个函数内的任何异常（`sqlite3.Error` / `OSError` / `ImportError`）MUST 统一包成 `TemplateGenerationError`（spec FR-033 / FR-014：MUST NOT 以裸异常逃逸）

**Checkpoint**: 三个构造器就位，3 个构造器单测全绿

---

## Phase 4: Foundational — 模板清单加载与渲染引擎

**Purpose**: 交付"幂等渲染"内核（被 US1 / US6 ~ US9 / US13 共同依赖）

- [X] T010 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 9 个渲染测试（FR-055 的第 1~6 项 + 占位符 + 目标为目录分支 + 重复条目分支）——`test_render_new_file`（目标不存在 → 创建，`files_created=1` / `files_skipped=0`）/ `test_render_skip_existing_no_force`（目标已存在且用户改写过 → **完全不动**，`created=0` / `skipped=1`）/ `test_render_force_overwrite`（force → 删除后按默认内容重建）/ `test_render_force_directory`（force + `skills/example/` 已存在且含**清单外**子文件 → 目录条目**不删除任何文件**：清单外文件仍在、清单内文件由各自的条目重建为出厂内容（**内容为出厂内容而非"被删掉"**）、**目录本身不删**）/ `test_render_skip_user_content`（workspace 含 `media/` 与 `tools/my_tool.py`（不在清单内）→ force 下**不删**这些）/ `test_render_force_rebuilds_sqlite3`（`memory/sessions.sqlite3` 含假数据 → force 后**重建**（schema 重建 + 数据清空）且 `media/` 不动 —— **MUST 同时断言两侧**（spec FR-057：用户内容仍在 + sqlite3 数据已清空），不得只断言一侧）/ `test_render_placeholder_substitution`（`{{ workspace_name }}` 与 `{{workspace_name}}` 两种写法均被替换；未识别占位符**原样保留**）/ `test_render_target_is_directory`（**文本类条目**（`format` ∈ {`markdown` / `toml` / `json` / `python` / `text`}）或 `sqlite3` 条目的目标路径已存在且**是目录**（而非文件）→ 抛 `TemplateGenerationError`（**MUST NOT** 抛 `PathNotFoundError`），且 MUST NOT 递归删目录内容、目录内容原样保留；**`directory` 类条目已存在 MUST NOT 报错** —— 按 FR-010 保留不变，见 spec Edge Cases「渲染与幂等类」与本任务的 `test_render_force_directory`）/ `test_render_duplicate_manifest_entry`（清单内同一路径出现两次 → MUST NOT 报错；渲染 MUST 按唯一路径处理、以**最后出现**的条目为准（其 `format` 与源模板生效）；计数 MUST 按唯一路径计一次 —— 不得对同一路径既计 created 又计 skipped；**追加断言（本 Phase 唯一的去重判定点）**：loader 返回的原始列表长度（== `templates_loaded` 口径）**大于**唯一路径数，且 `created + skipped` == 唯一**文件型**路径数 —— spec FR-002 / FR-026 的「含重复条目」与「按唯一路径计」两条口径必须可被区分；T011 的补充 ② 只断言 loader「不报错 + 长度 == 2」，**MUST NOT** 在此重复去重判定）。测试 MUST 通过**注入 `templates_root` 到临时目录**构造夹具（spec FR-006 / FR-056），MUST NOT 依赖安装包内的真实模板资产
- [X] T011 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 **6** 个清单 / 渲染分支测试（FR-055 的第 7~10 项 + 2 个补充项）——`test_render_template_source_missing`（注入 tmp `templates_root` + 指向不存在 `.txt` 的 entry → 抛 `TemplateGenerationError`，**MUST NOT** 抛 `PathNotFoundError`）/ `test_load_template_manifest_corrupted`（tmp 目录下写非合法 JSON 的 `manifest.json` → 抛 `TemplateGenerationError`）/ `test_load_template_manifest_schema_invalid`（`entries` 不是 list / entry 缺 `path` / `format` 为未知值 → 抛 `TemplateGenerationError`）/ `test_render_permission_denied_midway`（**MUST 以注入式构造产生**：用 `monkeypatch` 在写入边界（`Path.write_text` / `Path.write_bytes` / `open` 之一）注入 `OSError(EACCES)`，**MUST NOT** 依赖 `chmod 0o555` 只读目录 —— **特权账号（root / `CAP_DAC_OVERRIDE`）绕过 DAC 权限检查**，其对 `0o555` 目录的写入**仍成功**，chmod 方案在 root CI 容器中必然假失败；spec Assumptions「特权环境说明」已同步修订 + plan R-18）→ 抛 `TemplateGenerationError`）/ **补充 ①** `test_load_template_manifest_format_omitted_defaults_to_text`（entry **省略** `format` 字段 → loader MUST NOT 报错，且该条目按 `text` 处理（源路径为 `<path>.txt`、按纯文本渲染）—— spec FR-002 澄清决策「省略时 MUST 按 `text` 处理」/ FR-003）/ **补充 ②** `test_load_template_manifest_duplicate_paths_no_error`（清单内同一路径出现两次 → loader MUST NOT 报错、返回**原始列表**（长度 == 2）—— **本用例只断言「不报错 + 长度口径」；「渲染层按唯一路径去重」的判定统一归 T010 的 `test_render_duplicate_manifest_entry`（唯一判定点，避免同一断言分散两处）** —— spec FR-002 / FR-026 / research R-15）。**四个失败分支 MUST 全部用临时目录注入构造，MUST NOT 破坏已安装包**（spec FR-056 / FR-061；黑盒脚本因此不测这两个分支）
- [X] T012 [P] 在 `donkey/core/workspace/init.py` 追加 `DEFAULT_TEMPLATES_ROOT = Path(__file__).parent / "templates"` 与 `load_template_manifest(manifest_path: Path | None = None) -> list[dict]`（spec FR-001 / FR-004 —— 清单 MUST 位于安装包内、且 MUST 与 workspace 根的工作区清单是两个不同的文件）：**MUST NOT** 修改 P1 已实现的 `check_path` / `check_permission` / `validate_init_request`（spec FR-029）。默认路径 = `DEFAULT_TEMPLATES_ROOT / "manifest.json"`；用 `json.loads` 解析；schema 校验 MUST 覆盖 data-model.md §2 的 V1~V6（`version` 为整数 / `entries` 为列表 / 每条目为对象 / 每条目含非空字符串 `path` / `format` 若存在则 ∈ {markdown, toml, json, python, text, directory, sqlite3} / 文件本身为合法 JSON）；返回 `entries` 列表且 **MUST NOT** 就地修改。清单缺失 / JSON 非法 / schema 非法 → 抛 `TemplateGenerationError`（exit 3），**MUST NOT** 抛 `PathNotFoundError`（spec FR-002 / FR-038：二者的用户修复动作不同 —— "重装 donkey" vs "建目录 / 换路径"）。`format` 省略时 MUST 按 `text` 处理（spec FR-002 / data-model.md §2 —— 缺省视为 `text`）；**本函数 MUST NOT 去重** —— 返回**未去重的原始条目列表**（长度即 `templates_loaded`，含目录条目、含重复条目）。清单条目路径重复时 MUST NOT 报错；去重由 `render_templates` 承担（spec FR-002 / FR-026 / research R-15）
- [X] T013 在 `donkey/core/workspace/init.py` 追加 `render_templates(workspace_path: Path, name: str, force: bool, manifest_entries: list[dict], templates_root: Path | None = None) -> tuple[int, int]`（spec FR-005 / FR-003）：**MUST 先按唯一路径去重**（同一路径只处理一次，以重复项中**最后出现**的条目为准，其 `format` 与源模板生效；MUST NOT 对同一路径既计 created 又计 skipped —— spec FR-002 / 澄清 #24；`render_templates` 是公开 API，MUST NOT 假定入参已去重），再按 `format` 分派 7 种取值 —— 文本类（markdown/toml/json/python/text）的源路径 MUST 为 `(templates_root or DEFAULT_TEMPLATES_ROOT) / f"{entry['path']}.txt"`（**MUST NOT** 硬编码路径，spec FR-007），源缺失 → `TemplateGenerationError`；`directory` → `mkdir(parents=True, exist_ok=True)`（父目录创建**仅限 workspace 根之下**）；`sqlite3` → 调 T009 的对应 builder。幂等三态 MUST 严格实现（data-model.md §6 的状态机）：目标不存在 → 写入 / 构造；目标已存在且**无 force** → **完全不动**（内容与 mtime 均不变）；**有 force** → 文本类 `unlink` 后重写（**MUST NOT** 用"打开覆盖写" —— 那会保留原权限位与 mtime 语义，spec FR-009）；sqlite3 类 `unlink` 主库 **+ `unlink` 同名 `-wal` / `-shm`** 后重建（spec FR-011 / R-03；**MUST NOT** 在注释或错误信息中声称"不删必然导致旧数据回放" —— 实测陈旧 WAL 因盐值不匹配被安全忽略，连带删除是**防御性**措施）；目录类：**不带 force 与带 force 一律不删除目录内的任何文件**（MUST NOT 删目录本身、MUST NOT 删清单内文件、MUST NOT 删清单外文件）—— 其内清单内文件的重置由各自的文本 / sqlite3 条目负责（FR-009 / FR-011）；**目录条目若删除文件，会与 FR-012 的顺序无关性冲突**（当前清单顺序为「37 文本 → 6 目录 → 3 sqlite3」，删除会抹掉 6 个目录内的 **34** 个文件（**32** 个本轮新建 + **2** 个 P1 已有的 `mcp/mcp.json` / `providers/default.toml`）且不再生成）。**另 MUST 覆盖 data-model.md §6 状态迁移表最后两行** —— 目标路径已存在且**是目录**（而非文件）→ MUST 抛 `TemplateGenerationError`（exit 3），MUST NOT 递归删目录内容、MUST NOT 静默跳过（**仅文本类与 sqlite3 类条目**；`directory` 类条目已存在 MUST NOT 报错 —— 按 FR-010 保留不变，见 data-model.md §6 状态迁移表）；`--force` 时目标文件删除失败（如只读文件）→ MUST 抛 `TemplateGenerationError`（exit 3），非 `--force` 模式下只读文件 MUST 跳过、不报错（spec Edge Cases「渲染与幂等类」/ data-model.md §6 / §9）。**MUST NOT 依赖条目顺序** —— 写任何文件前 MUST 先确保其**父目录**存在（spec FR-012 / R-06：清单把 `providers/default.toml` 排在 `providers` 目录条目之前，按序渲染必然失败）。占位符替换 MUST 同时识别 `{{ workspace_name }}` 与 `{{workspace_name}}`，未识别占位符 MUST 原样保留（spec FR-015）；工作区名称含空格 / Unicode / 特殊字符时 MUST 原样注入，MUST NOT 转义、MUST NOT 截断（spec FR-015）。计数 MUST **仅统计文件型条目**（文本 + sqlite3），目录条目 MUST NOT 计入 `created` / `skipped`（spec FR-017）。任何 IO / sqlite 失败 MUST 包成 `TemplateGenerationError`，MUST NOT 逃逸裸 `OSError` / `sqlite3.Error`（spec FR-014）
- [X] T014 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_template_error_message_has_next_step`（FR-055 的第 11 项）：用临时目录下**非合法 JSON** 的 `manifest.json` 触发 `load_template_manifest` 抛出的 `TemplateGenerationError` → 断言 `str(exc)` 含「下一步」字样与可执行动作关键词（重装 donkey / 检查权限 / 重试 init 之一），且含可识别的失败标识（错误类别名或具体关键词）——MUST NOT 只报异常类别而不给下一步（spec FR-069 / SC-020；与 P1 的 `_NEXT_STEP` 模式对齐，research.md R-12）。**本任务 MUST 在 T012 / T013 实现之后才可能转绿**

**Checkpoint**: 清单加载 + 渲染内核就位，**16 个**渲染与失败分支单测全绿（T010 的 9 个 + T011 的 6 个 + T014 的 1 个；T015 已移至 Phase 5 —— 它断言的是门面 `init_workspace`，Phase 4 的门面函数体尚未替换）

---

## Phase 5: Foundational — 内部流程与核心库门面

**Purpose**: 把"校验 → 加载清单 → 建根目录 → 渲染 → 写工作区清单"串成一条流水线并接到门面

- [X] T083 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_init_manifest_write_failure_keeps_rendered_files`（spec 澄清决策 **#26** / plan R-16 —— **步骤 ⑤ 失败 MUST NOT 回滚步骤 ④**）：构造"步骤 ⑤（写工作区清单）失败"的场景 —— 用临时目录 + `monkeypatch` 让 `write_workspace_manifest` 抛 `TemplateGenerationError`（**注入式构造**，MUST NOT 破坏已安装包、MUST NOT 依赖运行账号的特权状态，plan R-18）→ 断言：① 抛出的异常为 `TemplateGenerationError`（退出码 `3`）；② **步骤 ④ 已落地的模板文件仍在**（内容为出厂内容，MUST NOT 被删除或还原）；③ `manifest.json` 未被写入。**本用例是「无回滚」的护栏** —— 实现中一旦引入任何补偿逻辑（临时目录 + 原子替换 / 失败即清空 / 删除已落地文件）本用例即失败。**写完先跑一次确认失败**（此时 `init_workspace_inner` 尚不存在 → ImportError），再进入 T016 的实现核对
- [X] T085 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_root_dir_creation_failure_maps_to_exit_2`（spec FR-027 / FR-038 的阶段切分 + plan R-16 同批修订 —— **步骤 ③（创建 workspace 根目录）的一切失败，含磁盘满 `ENOSPC`，一律归退出码 `2`**）：用 `monkeypatch` 注入 `OSError(ENOSPC)`（可参数化覆盖 `PermissionError`）到根目录创建 → 断言抛出的是 `PathPermissionError`（退出码 `2`），MUST NOT 是裸 `OSError`、亦 MUST NOT 是 `TemplateGenerationError`（退出码 `3` —— `3` 侧的"磁盘满"仅指**渲染阶段步骤 ④**的写入失败）。**注入式构造**，MUST NOT 依赖运行账号的特权状态（plan R-18）。**写完先跑一次确认失败**（当前实现以裸 `OSError` 逃逸，违反 FR-038），再进入 T016 的实现核对

- [X] T016 在 `donkey/core/workspace/init.py` 追加 `init_workspace_inner(path: str | Path, name: str | None, force: bool) -> tuple[Path, str, bool, int, int, int]`：五步流水线 MUST 严格按序（spec FR-027）—— ① `validate_init_request(path, name, force)` → ② `load_template_manifest()` → ③ `abs_path.mkdir(exist_ok=True)` → ④ `render_templates(abs_path, resolved_name, force, manifest_entries)` → ⑤ `write_workspace_manifest(abs_path, resolved_name, force)`；返回 `(abs_path, resolved_name, force, created, skipped, manifest_total)`，其中 `manifest_total` = `len(manifest_entries)`（步骤 ② 已在手的**原始列表长度**，含重复条目；loader 不去重，故直接取长度 —— spec FR-002 / FR-026 / research R-15）。**MUST NOT 为此二次调用 `load_template_manifest()`** —— 会带来重复 IO 与第二个失败点，且与步骤 ② 的结果可能不自洽。步骤 ③ MUST 只用 `mkdir(exist_ok=True)`，**MUST NOT** 用 `parents=True`（父目录缺失已在 ① 判为路径类错误并拒绝，spec FR-028；仅 workspace 根**之下**的目录条目 MAY 递归建父目录）。**步骤 ③ 的 `mkdir` 若抛 `OSError`（含 `PermissionError` / 磁盘满 `ENOSPC`）MUST 被包装为 `PathPermissionError`（退出码 `2`）再向上抛**，MUST NOT 以裸 `OSError` 逃逸（spec FR-038 的阶段化语义 + contracts/exit-codes.md §6 + E4；**步骤 ③ 的一切失败一律归 `2`**，由 T085 固化）。**步骤 ⑤ 失败 MUST NOT 回滚步骤 ④**（plan R-16 / spec 澄清 #26）—— 步骤 ④ 已落地的文件 MUST 保留（不删除、不还原），本 Phase **MUST NOT** 实现任何事务回滚机制（无补偿逻辑、无临时目录 + 原子替换、无"失败即清空"）；由 T083 固化。**注入点仅限库层单测**（`load_template_manifest(manifest_path=...)` / `render_templates(..., templates_root=...)`）；本函数不暴露注入参数
- [X] T017 [P] 在 `donkey/core/api.py` 把 `init_workspace` 的函数体替换为「调 `init_workspace_inner` + 构造 `InitResult`」：`from donkey.core.workspace.init import init_workspace_inner` 置于模块顶部；`InitResult` dataclass **MUST NOT** 增删字段 / 改顺序 / 改类型（spec FR-025，该契约为 F002~F006 共同依赖）；`templates_loaded` MUST 等于 loader 返回的**原始**条目列表长度（spec FR-026）。门面层 **MUST NOT** 承载业务逻辑（spec FR-024）。**MUST 移除** `donkey/core/api.py` 中已不再使用的 `from donkey.core.workspace.init import validate_init_request`（否则 ruff F401 报错，违反 spec FR-065 / SC-009）；并 **MUST 更新** `InitResult` 的 docstring（现仍写"templates_loaded —— P1 恒为 0" → 改为 P2 的 46 / 40 / 0）**并同步更新 `init_workspace` 函数自身的 docstring**（现写'失败：抛出 ``WorkspaceInitError`` 的子类（``PathNotFoundError`` / ``PathPermissionError``）' → MUST 补上 `TemplateGenerationError`）。
- [X] T015 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_init_workspace_counts_and_manifest`：**依赖 T016 / T017**（门面函数体在本阶段才被替换）→ 调用 `init_workspace` → `templates_loaded` == loader 返回的**原始条目列表长度**（**动态计算**：含目录条目、含重复条目 — spec FR-002 / FR-026）、`files_created` / `files_skipped` == **文件型条目数**（**动态计算**：文本 + sqlite3，目录条目不计入 — spec FR-017）、workspace 根存在 `manifest.json` 且 `name` 字段 == 路径末段名、`InitResult` 的字段集合与顺序与 P1 冻结值完全一致（spec FR-025）。**本任务 MUST NOT 硬断言 `46` / `40`** —— 此刻安装包内的模板清单仍是 F001-P1 的 3 条（追加 43 条的 T031 在 Phase 6），硬断言必然失败；**绝对值口径（`templates_loaded == 46` / `files_created == 40` / `files_skipped == 0`）由 T018 承接**（T018 MUST 在 T019 ~ T031 的资产任务全部完成后才可能转绿）

**Checkpoint**: 渲染流水线贯通；`init_workspace` 已能产出完整 `InitResult`；Phase 5 的 **3** 个单测（T083 + T085 + T015）全绿 —— **动态计数口径**（相对 loader 实际返回值）+ **两条边界护栏**（步骤 ⑤ 失败不回滚 / 步骤 ③ 一切失败归 `2`）；绝对值 `46 / 40 / 0` 的复验在 **T018**（依赖 Phase 6 的 T031 追加 43 条清单）

---

## Phase 6: User Story 1 - 一次 init 得到完整可用的 workspace 骨架 (Priority: P1) 🎯 MVP

**Goal**: `donkey init <PATH>` 一次性落地**全部 46 个模板条目**（37 个文本模板源 + 6 个目录 + 3 个 sqlite3，**含 26 份供应商配置与 `providers/README.md`**）+ 1 份工作区清单

**Independent Test**: 在临时目录执行 `donkey init <tmp>/ws` → 退出码 **0**（37 个模板源一次性齐备，MUST NOT 触发「源模板缺失」的 exit 3）；workspace 内文件数 = **41**（37 文本 + 3 sqlite3 + 1 工作区清单）、目录数 = **7**（根 + 5 必填 + `skills/example`）；26 份供应商配置 + `providers/README.md` **均就位**；摘要输出 `templates=46 created=40 skipped=0`；三个 sqlite3 文件存在且 `sessions.sqlite3` 结构完整（US14 的断言）

> **US1 的资产边界**：US1 交付**全部 37 个文本模板源**（含 26 份供应商配置与 `providers/README.md`）+ 6 个目录 + 3 个 sqlite3 —— **MUST 一次性全部就位**。理由：模板清单的 46 条是一个**原子集合**（spec FR-039 / FR-040 / FR-041），而 spec FR-007 规定「文本模板类条目的源文件缺失 MUST 抛 `TemplateGenerationError` → 退出码 `3`」→ 清单里有条目而源缺失时，`donkey init` 会**直接 exit 3**、workspace 建不出来。故 MUST NOT 把模板源拆成「先一部分、后一部分」的两段交付。**US2 负责的是供应商目录的「内容质量」**（可解析 / 全关闭 / 51 条模型条目 / `bedrock` 无 `api_key` / 索引说明含 26 个 id），**不是资产的创建**。

### Tests for User Story 1 (TDD) ⚠️

> **先写测试并确认失败**

- [X] T018 [US1] ⏳ **（执行位置在本阶段末尾）** 在 `tests/unit/test_template_skeleton.py` 写 `test_template_assets_render_to_expected_tree`：以**安装包内真实资产**（`DEFAULT_TEMPLATES_ROOT`，非注入）渲染到 `tmp_path` → 断言落地文件数 == 41、目录数 == 7、`manifest.json` 存在、**渲染结果中无 `{{` 残留**（spec SC-014）、`templates_loaded` == 46（模板清单的**原始条目总数**，含目录条目、含重复条目）、`files_created` == 40（文件型条目：37 文本 + 3 sqlite3，目录条目不计入，spec FR-017 / R-08）。**本任务 MUST 在 T019 ~ T031 的资产任务全部完成后才可能转绿** —— 故其执行位置在本阶段末尾

- [X] T087 [US1] ⏳ **（执行位置在本阶段末尾）** 在 `tests/unit/test_template_skeleton.py` 写 `test_gitignore_template_content`（spec FR-053 —— **本用例是 FR-053 的唯一验证落点**，FR-055 的 16 类不含该项 → 属**补充类别**，MUST NOT 计入或替换 FR-055 的 16 类中任何一类）：读取 `donkey/core/workspace/templates/.gitignore.txt` → 断言逐行含 `__pycache__/` / `*.pyc` / `*.pyo` / `*.egg-info/` / `.venv/` / `venv/` / `memory/*.sqlite3` / `memory/*.sqlite3-wal` / `memory/*.sqlite3-shm` 共 **9 条**（MUST 忽略 Python 缓存与虚拟环境产物、MUST 忽略记忆库文件及其 WAL / SHM 附属文件）；断言渲染后 workspace 根 `.gitignore` 内容一致且无 `{{` 残留。**MUST NOT** 断言含 `providers/*.toml`（该遗留已登记为 plan G18 / v2 议题，本 Phase 不擅自改动）。**写完先跑一次确认失败**（源尚未就位 → T023 之前即失败），**本任务 MUST 在 T023 完成后才可能转绿**
- [X] T088 [US1] ⏳ **（执行位置在本阶段末尾）** 在 `tests/unit/test_template_skeleton.py` 写 `test_instruction_template_title_and_sections`（spec FR-043 —— **本用例是 FR-043 的唯一验证落点**；属 FR-055 的 16 类之外的补充类别）：读取 `donkey/core/workspace/templates/instruction.md.txt` → 断言首行标题含 `{{ workspace_name }}`（渲染后 MUST 出现工作区名称）且正文**恰含** `## 角色` / `## 风格` / `## 限制` 三个留白小节（**MUST NOT** 出现第四个留白小节）；断言不含任何 Python 入口内容（宪法 N-01）。**注意**：SC-014 的"一致性三处"按设计**不含** `instruction.md`（它是"注入点"而非"校验点"）→ 本用例与 SC-014 **MUST NOT 混用**。**写完先跑一次确认失败**，**MUST 在 T019 完成后才可能转绿**
- [X] T089 [US1] ⏳ **（执行位置在本阶段末尾）** 在 `tests/unit/test_template_skeleton.py` 写 `test_workspace_readme_template_content`（spec FR-050 —— 属 FR-055 的 16 类之外的补充类别）：读取 `donkey/core/workspace/templates/README.md.txt` → 断言含 `{{ workspace_name }}` 占位符且正文**逐一出现** `instruction.md` / `providers/` / `tools/` / `mcp/` / `skills/` / `memory/` 六个目录名（"概述目录职责"）；断言**不含**引擎层能力承诺关键词（`diff` 审阅 / 路径权限交互 / fork 改引擎）—— 宪法 AC-5 / §2.1「官方模板不承诺提供 diff 审阅」。**写完先跑一次确认失败**，**MUST 在 T022 完成后才可能转绿**
- [X] T090 [US1] ⏳ **（执行位置在本阶段末尾）** 在 `tests/unit/test_template_skeleton.py` 写 `test_dir_readme_templates_content`（spec FR-051 —— 属 FR-055 的 16 类之外的补充类别）：`templates/tools/README.md.txt` MUST 含工具开发约定四要素关键词（命名 / 参数 / 错误处理 / 超时）**且**含"内置工具由后续阶段生成"的标注（FR-051 / US11）；`templates/mcp/README.md.txt` MUST 含配置形状关键词（`mcpServers`）与"用户自行填写"定位（FR-051）；`templates/skills/README.md.txt` MUST 含三层模型关键词（`name` / `description` / Level 2 / Level 3）**且**含"不允许自定义额外字段"（宪法 D-07 / FR-051）。**写完先跑一次确认失败**，**MUST 在 T024 / T025 / T026 完成后才可能转绿**

### Implementation for User Story 1

- [X] T019 [US1] 覆盖 `donkey/core/workspace/templates/instruction.md.txt`（spec FR-043 —— 标题用工作区名称 + 角色/风格/限制三个留白小节；P1 的占位源，**MUST 整体覆盖**，MUST NOT 增量修补 —— P1 占位含 `{{workspace_path}}` 与"待 F001-P2 填充"，覆盖后该占位符消失，spec FR-042 / R-07）：内容为 `# {{ workspace_name }} 的系统提示词` 标题 + "本文件由 `donkey init` 生成；用户可自由编辑" + `## 角色` / `## 风格` / `## 限制` 三个留白小节（含 HTML 注释占位说明）。MUST NOT 含任何 Python 入口文件（宪法 N-01）
- [X] T020 [P] [US1] 覆盖 `donkey/core/workspace/templates/providers/default.toml.txt`（P1 的占位源，含 `{{default_provider}}` / `{{default_model}}` 占位符，**MUST 整体覆盖**）：注释头含 `{{ workspace_name }}` + 字段契约说明（`default_provider` 须指向 `providers/<provider_id>.toml` 且该文件 `enabled = true`；`default_model` 须存在于该 provider 的 `[models]` 表中）+ 两个字段 `default_provider = ""` / `default_model = ""`（**出厂态均为空串**，MUST NOT 残留任何占位符字面量，spec FR-044）
- [X] T021 [P] [US1] 覆盖 `donkey/core/workspace/templates/mcp/mcp.json.txt`（P1 的占位源，内容已与目标一致，**仍 MUST 按 spec 覆盖以保证一致性**）：`{ "mcpServers": {} }` —— 合法 JSON、空服务器表、无任何预置服务器定义
- [X] T022 [P] [US1] 新建 `donkey/core/workspace/templates/README.md.txt`（工作区总览）：标题含 `{{ workspace_name }}` 占位符（渲染后 MUST 出现工作区名称，spec FR-050）+ 概述 `instruction.md` / `providers/` / `tools/` / `mcp/` / `skills/` / `memory/` 六个目录职责 + 提示"运行数据可选择性导出"。MUST NOT 承诺引擎层能力（diff 审阅 / 路径权限交互，宪法 AC-5）
- [X] T023 [P] [US1] 新建 `donkey/core/workspace/templates/.gitignore.txt`：逐行为 `__pycache__/` / `*.pyc` / `*.pyo` / `*.egg-info/` / `.venv/` / `venv/` / `memory/*.sqlite3` / `memory/*.sqlite3-wal` / `memory/*.sqlite3-shm`（spec FR-053）。**MUST NOT** 加入 `providers/*.toml` —— 提示词固定了本文件内容，且宪法 §3.5 定"凭据由用户自负"；该遗留已登记为 plan G18 / v2 议题，**本 Phase 不擅自改动**
- [X] T024 [P] [US1] 新建 `donkey/core/workspace/templates/tools/README.md.txt`：工具开发约定（命名 / 参数 / 错误处理 / timeout 建议）+ **明确标注 3 个内置 `@tool` 文件属后续阶段生成**（spec FR-051 / US11）
- [X] T025 [P] [US1] 新建 `donkey/core/workspace/templates/mcp/README.md.txt`：MCP 配置形状说明 + "用户自行填写"的定位（spec FR-051）
- [X] T026 [P] [US1] 新建 `donkey/core/workspace/templates/skills/README.md.txt`：Skills 三层渐进披露模型（Level 1 frontmatter 两必填字段 `name` + `description` / Level 2 正文主体 / Level 3 附属资源）+ 宪法 D-07 的"不允许自定义额外字段"（spec FR-051）
- [X] T027 [P] [US1] 新建 `donkey/core/workspace/templates/memory/README.md.txt`：MUST 明确告知 ① `memory/` 目录与三个 sqlite3 文件**全部是模板**、由 init 阶段预创建；② `sessions.sqlite3` 含上游 saver 的 `checkpoints` / `writes` + donkey 自管的 `sessions_metadata`（6 字段 + 2 索引）；③ `store.sqlite3` / `knowledge.sqlite3` 当前版本**仅占位空文件**、schema 推迟到后续版本；④ **`--force` 会删掉重建三个文件并清空历史与元数据、用户须在执行前手动备份** + MUST 给出备份命令示例（**对齐宪法 §3.1.1 的规范形态** `cp memory/*.sqlite3 /tmp/backup-*.sqlite3` —— 覆盖三个库；可另附单文件示例 `cp memory/sessions.sqlite3 /tmp/backup-sessions.sqlite3`，但 MUST NOT 只给单文件而遗漏另两个库）；⑤ "运行数据可选择性导出"仍成立（模板身份 ≠ 必须导出，宪法 D-02）（spec FR-052 / SC-018）
- [X] T028 [P] [US1] 新建 `donkey/core/workspace/templates/skills/example/SKILL.md.txt`：以 `---` frontmatter 开头，**恰含** `name: example` 与 `description: ...` **两个字段**（MUST NOT 有任何第三个字段，宪法 D-07 / spec FR-049）+ 正文体现三层模型并**明确标注**"完整第二层正文 + 第三层示例由 F001-P3 覆盖写入"（Level 2/Level 3 内容属 P3，spec FR-066）
- [X] T029 [US1] **用脚本抽取** 26 份 provider 配置源到 `donkey/core/workspace/templates/providers/<id>.toml.txt`（从 `harness/report/大模型toml参数设计.md` §8.3.3 ~ §8.3.28 的 ```toml fenced code block 逐块抽取：`##### 8.3.x` 标题定位 provider id，围栏内正文原样落盘，26 个 id 一一对应）。**MUST NOT 手工誊写** —— 誊写必漏注释行与空行（research.md R-09）；抽取脚本属一次性工具，**MUST NOT** 落进仓库；抽取后 MUST 人工复核 diff。**本任务 MUST 在 T031 之前完成** —— 清单条目须与源文件一一对应（T031 的追加依赖本任务的产出）
- [X] T030 [US1] 新建 `donkey/core/workspace/templates/providers/README.md.txt`（目录索引，spec FR-045）：MUST 列出**全部 26 个** provider id（一行一个，MUST NOT 用 `...` 省略 —— 它是用户查找"我该改哪个文件"的索引）+ "一 provider 一文件、文件名 stem == provider_id"的命名规则 + 启用三步（① `enabled = true` → ② 填凭据（`api_key` / `aws_*`）→ ③ 在 `providers/default.toml` 设 `default_provider` + `default_model`）+ "未启用的文件**完全惰性**（不校验字段 / 不要求 `api_key` / 不参与连通性检查）"的说明 + "文件名不在 v1 白名单（26 家）→ `donkey load` 会报错（错误码见 `donkey load` 文档）"的指引 —— **MUST NOT** 在模板正文里写死某个具体退出码（`donkey load` 属 F002，其错误类与码值尚未在本仓库定义，写死会与 F002 的最终分配冲突）
- [X] T031 [US1] 在 `donkey/core/workspace/templates/manifest.json` 的 `entries` 数组**末尾追加 43 条**（spec FR-040 —— 条目 MUST 覆盖 7 个文本模板 + 供应商目录 27 条 + 6 个目录条目 + 3 个 sqlite3 条目）（MUST NOT 修改 P1 已有的 3 条 —— 追加纪律，spec FR-039）：7 个文本模板（`skills/example/SKILL.md` / `README.md` / `tools/README.md` / `mcp/README.md` / `skills/README.md` / `memory/README.md` / `.gitignore`）+ 供应商目录 27 条（`providers/README.md` + 26 个 `<id>.toml`）+ 6 个目录条目（`tools` / `mcp` / `skills` / `skills/example` / `memory` / `providers`）+ 3 个 sqlite3 条目（`memory/sessions.sqlite3` / `memory/store.sqlite3` / `memory/knowledge.sqlite3`）。**完整 JSON 逐条内容以 [contracts/template-manifest.md](contracts/template-manifest.md) §2 为准**（该节给出了 46 条的完整清单，可直接照抄，MUST NOT 自行增删路径或 `format` 值）；`version` MUST 保持 `1`。**本任务依赖 T029** —— 26 个 provider 源文件就位后清单条目才与其一一对应
- [X] T032 [US1] 跑 [contracts/template-manifest.md](contracts/template-manifest.md) §7 的构建期自检中**本阶段可完成的那部分**：**B1 / B2 / B3 / B4 / B11**（MUST 全部通过；**B12 的唯一判定点为 T018 / T043** —— 本任务 MUST NOT 自行断言 B12，避免与 T086 双重认领；**B2 MUST 另跑 quickstart §7.1 的 B2b「按打包产物核对」** —— 缺任一即判失败）（spec FR-041 —— 37 个文本条目 MUST 与源文件**双向**一一对应，且 MUST 全部进入打包产物）：清单条目总数 == 46；**清单的**前 **3** 条** MUST 与 F001-P1 已建档的 3 条逐字一致**（`instruction.md` / `providers/default.toml` / `mcp/mcp.json` —— 路径与 `format` 均未变，spec FR-039 的「追加纪律」）；文本条目 ↔ 源文件**双向**一一对应（各 37）；6 个目录条目与 3 个 sqlite3 条目**无**同名 `.txt` 源；`templates/` 下**无**任何 `.sqlite3` / `.db` 二进制文件（spec FR-030 / 宪法 D-05）；渲染后**无 `{{` 占位符残留**；wheel / sdist 解包后含全部 37 个 `.txt` 源（**含隐藏名 `.gitignore.txt`**）。**⚠️ B5 / B6 / B7 / B8 / B9 / B10 不在本任务范围** —— 它们分别由 **T034**（B5 / B6 / B8，Phase 7）、**T035**（B7，Phase 7）、**T039**（B9，Phase 8）、**T041**（B10，Phase 9）承载，最终由 **T086**（Phase 21）汇总核对 —— 本任务 MUST NOT 声称"B1 ~ B12 全套已通过"
- [X] T033 [US1] 跑 `pytest tests/unit/test_template_skeleton.py -v` → US1 相关用例（含 T018）全绿（spec SC-003 —— 46 条落地物缺失数为 0）；再跑 quickstart §2 场景 1 手动冒烟 → 退出码 0、文件数 41、目录数 7、摘要 `templates=46 created=40 skipped=0`

**Checkpoint**: US1 可独立交付（骨架 + 清单 + 计数 + 工作区清单 + 三个 sqlite3 就位）—— **MVP 达成点**；**5 条内容级断言（T018 + T087 ~ T090）全绿** —— FR-043 / FR-050 / FR-051 / FR-053 的内容契约已有自动化验证落点

---

## Phase 7: User Story 2 - 供应商配置目录开箱即用且可被机器读取 (Priority: P2)

**Goal**: `providers/` 目录的**内容质量**达标 —— 26 份供应商配置可被标准 TOML 解析器读取、出厂态全部关闭、模型条目齐全（51 条）、`bedrock` 用专属账号字段，且 26 家索引说明完整无省略

**Independent Test**: 渲染后用 `tomllib` 逐份解析 `providers/*.toml` → 26/26 无异常、`enabled` 全为 `False`、凭据字段为空、`bedrock.toml` 无 `api_key` 且含 4 个 `aws_*` 字段；`providers/default.toml` 含两个出厂为空串的字段；26 份配置的 `[models.*]` 条目**合计恰为 51 条**；`providers/README.md` **恰含 26 个** provider id（无省略）

### Tests for User Story 2 (TDD) ⚠️

- [X] T034 [US2] 在 `tests/unit/test_template_skeleton.py` 写 `test_providers_dir_parseable_and_disabled`：以 `tomllib` 解析 `templates/providers/` 下的 **26** 份供应商配置源 `<id>.toml.txt` → 断言 26/26 无异常、`enabled is False`、凭据字段为空（或按该 provider 的专属账号字段规则为空）、`bedrock.toml` **不含** `api_key` 且含 4 个 `aws_*` 字段（spec FR-047）；再断言 `providers/default.toml` 可解析且含 `default_provider` / `default_model` 两字段且值为空串。**文件选择 MUST 显式排除 `default.toml.txt`**（它是保留名、非供应商配置；naive glob `*.toml.txt` 会匹配到 27 个文件）—— 建议按 `contracts/template-manifest.md` §2 的 26 个 provider id 遍历，而非按 glob
- [X] T035 [US2] 在 `tests/unit/test_template_skeleton.py` 写 `test_provider_models_count_is_51`：统计 26 份供应商配置源中 `^\[models\.` 开头的行数 → **恰好 51 条**（与调研 §8.3 逐条一致，spec SC-015 的硬指标；缺失或多余任一条即失败）。**统计范围 MUST 与 T034 一致**（仅 26 份 `<id>.toml.txt`，不含 `default.toml.txt`）

- [X] T036 [US2] 在 `tests/unit/test_template_skeleton.py` 写 `test_providers_index_lists_all_26`：读取 `donkey/core/workspace/templates/providers/README.md.txt` → 断言其中列出的 provider id **恰为 26 个**（与调研 §3.1 白名单逐条一致，MUST NOT 用 `...` 省略 —— 它是用户查找"我该改哪个文件"的索引）；并断言正文含三段说明：「一 provider 一文件、文件名 stem == provider_id」的命名规则、启用三步（`enabled = true` → 填凭据 → 设 `default_provider` + `default_model`）、「未启用的文件**完全惰性**」（不校验字段 / 不要求凭据 / 不参与连通性检查）（spec FR-045）

### Implementation for User Story 2

- [X] T037 [US2] 逐份核对 **T029** 抽取的 26 份 provider 配置内容并修正：① `enabled = false`；② 凭据字段出厂为空串、**MUST NOT** 出现 `REPLACE_ME` 类占位符（spec FR-046）；③ `bedrock.toml` MUST NOT 含通用 `api_key`，改用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` / `aws_session_token` 四字段（出厂全为空串）；④ `[models.*]` 条目合计 51 条；⑤ 解释性注释**完整保留**（research.md R-09）；⑥ `ollama` / `meta` 等本地或自托管 provider 的凭据字段出厂为空串且 MUST NOT 被要求填写。**解释性注释 MUST 完整保留（逐字照抄 §8.3 对应小节），人工复核 diff 时逐行核对注释行数**（spec FR-046 的"注释一并照抄"核对锚点）
- [X] T038 [US2] 跑 `pytest tests/unit/test_template_skeleton.py -v` → US2 相关用例全绿

**Checkpoint**: US2 可独立交付（供应商目录机器可读 + 出厂态关闭 + 51 条模型）

---

## Phase 8: User Story 3 - MCP 配置起点是合法 JSON (Priority: P3)

**Goal**: 生成的 `mcp/mcp.json` 可被标准 JSON 解析器读取，且形状对用户自明

**Independent Test**: `json.loads` 读取渲染后的 `mcp/mcp.json` → 不抛异常，且结果含 `mcpServers` 键

### Tests for User Story 3 (TDD) ⚠️

- [X] T039 [US3] 在 `tests/unit/test_template_skeleton.py` 写 `test_mcp_json_parseable`：`json.loads` 解析 `templates/mcp/mcp.json.txt` → 不抛异常，且结果含 `mcpServers` 键、其值为空对象（无预置服务器定义，spec FR-048）

### Implementation for User Story 3

- [X] T040 [US3] 核对 `donkey/core/workspace/templates/mcp/mcp.json.txt` 的内容为合法 JSON + 空 `mcpServers` + 无任何预置服务器定义；与 T021 的覆盖结果一致（若 T021 已落实，本任务仅做最终核对，MUST NOT 引入第二份内容来源）

**Checkpoint**: US3 可独立交付

---

## Phase 9: User Story 4 - 示例 Skill 的元信息合规 (Priority: P4)

**Goal**: `skills/example/SKILL.md` 的 frontmatter 恰含 `name` + `description` 两个字段

**Independent Test**: 读取渲染后的 `skills/example/SKILL.md` → 以 `---` 开头，frontmatter 字段集合恰为 2 项

### Tests for User Story 4 (TDD) ⚠️

- [X] T041 [US4] 在 `tests/unit/test_template_skeleton.py` 写 `test_skill_frontmatter_exactly_two_fields`：以纯文本 split 解析（`---` 分隔，**MUST NOT** 引入 `python-frontmatter` 依赖 —— spec FR-067：运行期依赖恰为 1 个）→ frontmatter 字段集合**恰为** `{name, description}`，`name` 值为 `example`，且**无**任何自定义额外字段（宪法 D-07 / spec FR-049）

### Implementation for User Story 4

- [X] T042 [US4] 核对 `donkey/core/workspace/templates/skills/example/SKILL.md.txt`：frontmatter 恰两字段（`name: example` + `description: ...`）；正文体现三层渐进披露（Level 1 frontmatter / Level 2 正文主体 / Level 3 reference·scripts·templates 附属资源）并**明确标注**"完整第二层正文与第三层示例由 F001-P3 覆盖写入"（spec FR-049 / FR-066：P2 只写占位级 Level 2）

**Checkpoint**: US4 可独立交付

---

## Phase 10: User Story 5 - 工作区处处带着自己的名字 (Priority: P5)

**Goal**: 工作区名称在**三处**逐字一致：工作区说明文档正文、供应商全局默认文件正文、工作区清单 `name` 字段

**Independent Test**: 对末段名为 `foo` 的路径执行 init → 三处均含 / 等于 `foo`；渲染结果中无名字占位符残留

### Tests for User Story 5 (TDD) ⚠️

- [X] T043 [US5] 在 `tests/unit/test_template_skeleton.py` 写 `test_workspace_name_injected_three_places`：以 `name="foo"` 渲染到 `tmp_path` → 断言 `README.md` 正文含 `foo`、`providers/default.toml` 正文含 `foo`、工作区清单 `name` 字段**严格等于** `foo`；且渲染产物中**无 `{{` 残留**（spec FR-015 / SC-014）；另用含空格 / Unicode / 特殊字符的名称（如 `my ws ✨`）重跑一次，断言三处**逐字一致**、无转义序列、无截断（spec FR-015）

### Implementation for User Story 5

- [X] T044 [US5] 核对**三个模板注入点**的占位符写法（**"三个注入点" ≠ SC-014 的"一致性三处"** —— 前者指**模板正文里写入工作区名称的位置**，后者指**验收时的三个校验点**；SC-014 的三处 = `README.md` 正文 + `providers/default.toml` 正文 + 工作区清单 `name` 字段）：`templates/instruction.md.txt`（**FR-043：标题用工作区名称**）、`templates/README.md.txt`（FR-050：正文含工作区名称）用 `{{ workspace_name }}`；`templates/providers/default.toml.txt` 的注释头用 `{{ workspace_name }}`；工作区清单的 `name` 取 `init_workspace_inner` 解析出的**最终名称**（CLI 通道恒等于路径末段名，F001-P1 已定夺）。**MUST NOT** 在模板正文里硬编码任何具体名称；名称含空格 / Unicode / 特殊字符时 MUST 原样注入（不转义、不截断，spec FR-015）

**Checkpoint**: US5 可独立交付

---

## Phase 11: User Story 6 - 反复跑 init 不会碰用户写的东西 (Priority: P6)

**Goal**: 无 `--force` 时已存在文件的**内容与修改时间**均不变

**Independent Test**: 改写某模板文件 → 再 init → 内容不变且 **mtime 完全相同**

### Tests for User Story 6 (TDD) ⚠️

- [X] T045 [US6] 在 `tests/unit/test_template_skeleton.py` 写 `test_render_skip_existing_keeps_mtime`：写入自定义内容后记录 `st_mtime` → 无 force 渲染 → 断言内容未变且 `st_mtime` **完全相同**（不是"内容相同但被重写过"，spec FR-008 / SC-004）

### Implementation for User Story 6

- [X] T046 [US6] 核对 `donkey/core/workspace/init.py` 中 `render_templates` 的"无 force + 已存在"分支（spec FR-016 —— 已存在 MUST NOT 报错；spec FR-062 —— init 的幂等契约）：MUST **完全不触碰**目标文件（MUST NOT 打开写入 —— 那会刷新 mtime，违反 I1 不变量），计数 `skipped +1`；已存在但**只读**的文件 MUST 跳过而非报错（Edge Cases「渲染与幂等类」）
- [X] T084 [US6] 先写并确认失败：在 `tests/unit/test_template_skeleton.py` 写 `test_init_after_rename_keeps_old_name`（spec 澄清决策 **#27** / plan R-17 —— 工作区被**重命名**后再执行**非强制** init）：① 先 init 出工作区（名称 `old_name`）→ ② 把整个目录重命名为 `new_name` → ③ 再执行**非强制** init → 断言：**命令成功（退出码 `0`）**、MUST NOT 触发退出码 `3`；**工作区清单的 `name` 字段仍为 `old_name`**（非强制模式下 MUST NOT 覆盖，FR-008 / FR-020）；**模板正文内的名称仍为 `old_name`**（已存在文件 MUST 完全不动）；**命令行报告的名称为路径末段名 `new_name`**（`InitResult.name` 恒等于末段名）。二者不一致 MUST NOT 被当作错误、亦 MUST NOT 以任何形式宣称一致 —— 本 Phase 以**文档化口径**满足（spec Edge Cases「其它边界」已登记 + SC-014 的适用边界已明确），**MUST NOT** 新增任何命令行输出（客户端改动仍限 FR-064 的三项）。**本用例锁定的是「不报错」与「不被静默改成新名」两项**，不要求二者一致。**写完先跑一次确认失败**（若实现误在非强制模式下刷新清单 `name` 或改写模板正文，本用例即失败 —— 它是这两项的护栏）

**Checkpoint**: US6 可独立交付（含 T084 的重命名边界护栏）

---

## Phase 12: User Story 7 - 删掉的文件会被补回来 (Priority: P7)

**Goal**: 清单内缺失的条目在下次 init 时被补齐，且不影响其它文件

**Independent Test**: 删掉一个模板文件 → 再 init → 该文件重新存在；其它文件的 mtime 未变

### Tests for User Story 7 (TDD) ⚠️

- [X] T047 [US7] 在 `tests/unit/test_template_skeleton.py` 写 `test_render_missing_file_is_recreated` 与 `test_render_missing_file_does_not_touch_others`：删除目标文件后渲染 → 目标文件重新存在且内容为出厂内容；同期未缺失的其它文件**内容与 mtime 均未变**

### Implementation for User Story 7

- [X] T048 [US7] 核对 `donkey/core/workspace/init.py` 中 `render_templates` 的"无 force + 目标不存在"分支：MUST 写入默认内容并计入 `created`；**MUST NOT** 因为清单中同一条目已在上一次渲染中被处理过而跳过（渲染 MUST NOT 跨调用缓存状态）

**Checkpoint**: US7 可独立交付

---

## Phase 13: User Story 8 - `--force` 把模板恢复成出厂状态 (Priority: P8)

**Goal**: `--force` 后被改写的模板文件恢复出厂内容，且工作区清单被覆盖并刷新创建时间

**Independent Test**: 改写模板文件 → `--force` → 内容不含用户自定义字样；工作区清单 `created_at` 被刷新

### Tests for User Story 8 (TDD) ⚠️

- [X] T049 [US8] 在 `tests/unit/test_template_skeleton.py` 写 `test_force_restores_factory_content_and_manifest_created_at`：改写模板文件 + 记录工作区清单原 `created_at` → force 渲染 → 断言模板文件内容不含用户自定义字样、工作区清单被覆盖且 `created_at` **已刷新**（与原值不同或至少被重写为当前时刻，spec FR-020）

### Implementation for User Story 8

- [X] T050 [US8] 核对 `donkey/core/workspace/init.py` 中 `render_templates` 的"有 force + 已存在"分支（spec SC-005 —— 被改写的模板文件 100% 恢复出厂内容）：文本类 MUST 先 `unlink` 再按默认内容重建（**MUST NOT** 用"打开覆盖写"，spec FR-009）；`write_workspace_manifest` 在 force 下 MUST 覆盖并刷新 `created_at`（工作区清单是 `--force` 唯一会覆盖的"清单外"路径，research.md R-10）

**Checkpoint**: US8 可独立交付

---

## Phase 14: User Story 9 - `--force` 也不碰用户自己的东西 (Priority: P9)

**Goal**: `--force` 的作用域严格限定在模板清单条目内

**Independent Test**: 建 `media/`（含文件）与 `donkey.log` → `--force` → 二者存在性与内容均不变

### Tests for User Story 9 (TDD) ⚠️

- [X] T051 [US9] 在 `tests/unit/test_template_skeleton.py` 写 `test_force_preserves_user_content`：workspace 含 `media/video.mp4` 与 `donkey.log`（均不在清单内）→ force 渲染 → 断言二者**依然存在**且 `donkey.log` 内容未变

### Implementation for User Story 9

- [X] T052 [US9] 核对 `donkey/core/workspace/init.py` 中 `render_templates` 的强制重置作用域：MUST NOT 触碰任何清单外路径（用户自建目录 / 自建文件 / 自定义工具脚本 / 自定义 Skill 目录 / `memory/` 下的非清单文件）；**目录条目在 force 下 MUST NOT 删除目录内的任何文件**（MUST NOT 删目录本身、MUST NOT 删清单内文件、MUST NOT 删清单外文件）—— 其内清单内文件的重置由各自的文本 / sqlite3 条目负责（spec FR-010 / FR-013）

**Checkpoint**: US9 可独立交付

---

## Phase 15: User Story 10 - 删掉整个工作区再来一次也无妨 (Priority: P10)

**Goal**: 用户手动整体删除 workspace 后再 init，结果与首次创建完全一致

**Independent Test**: init → `shutil.rmtree` → 再 init → 模板文件重新出现，目录结构与首次一致

### Tests for User Story 10 (TDD) ⚠️

- [X] T053 [US10] 在 `tests/unit/test_template_skeleton.py` 写 `test_init_after_full_removal_equals_fresh`：首次 init → 记录落地文件的相对路径集合 → `shutil.rmtree(workspace)` → 再 init → 断言落地集合与首次**完全一致**（spec US10 场景 2）

### Implementation for User Story 10

- [X] T054 [US10] 核对 `donkey/core/workspace/init.py` 中 `init_workspace_inner` 步骤 ③ 在"目标已被用户删除"的情形下 MUST 重建根目录（`mkdir(exist_ok=True)` 对已删除路径同样成立）；MUST NOT 把"用户删掉了 workspace"当错误

**Checkpoint**: US10 可独立交付

---

## Phase 16: User Story 11 - 现在还不会出现内置工具文件 (Priority: P11)

**Goal**: `tools/` 目录存在但**不含**任何内置工具脚本与包初始化文件

**Independent Test**: 渲染后 `tools/` 下 `filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py` **均不存在**

### Tests for User Story 11 (TDD) ⚠️

- [X] T055 [US11] 在 `tests/unit/test_template_skeleton.py` 写 `test_no_builtin_tool_files_generated`：渲染后断言 `tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py` / `tools/__init__.py` **均不存在**，且 `tools/README.md` 存在（spec FR-054 / SC-016 —— 模板内容 MUST NOT 含 Python 入口文件 / subagent 相关目录或字段 / LangSmith 任何形态）（spec FR-066 / 宪法 N-01）。追加两条断言：**workspace 全量扫描**（递归遍历全部落地物）**无任何 `.py` 文件**；工作区内容**不含**子智能体相关目录或字段（无 `agents/` / `subagent` / `subagents/` 目录，模板正文中无子智能体相关字段名）（spec SC-016 / FR-054 / 宪法 N-01 / N-02）。**追加第三条断言（补 SC-017 的 workspace 侧）**：workspace 内全部落地物的**文本内容**中**不含** `langsmith` / `LangSmith` / `LANGSMITH_` 任一字样（逐文件读取文本后大小写不敏感匹配）—— SC-017 明写「初始化后的工作区 MUST 100% 不含任何 LangSmith 相关内容（代码 / 配置 / 依赖声明）」，此前仅代码侧由 T071 / T080 的全仓 grep 覆盖，workspace 侧无断言

### Implementation for User Story 11

- [X] T056 [US11] 核对模板清单中**无**任何 `format: "python"` 条目（内置 `@tool` 属 F001-P3，清单格式值 `python` 已支持但本 Phase 零条目 —— 这正是宪法 N-01 门禁 plan G14 的依据）；核对 `tools/README.md.txt` 中已标注"内置工具文件由后续阶段生成"

**Checkpoint**: US11 可独立交付

---

## Phase 17: User Story 12 - init 不会替我做配置检查 (Priority: P12)

**Goal**: init 阶段不对工作区内的供应商 / MCP / Skill 内容做任何合法性判定；出厂态（全关闭）仍 exit 0

**Independent Test**: 在工作区写入故意损坏的 provider TOML → 再 init → 仍 exit 0

### Tests for User Story 12 (TDD) ⚠️

- [X] T057 [US12] 在 `tests/unit/test_template_skeleton.py` 写 `test_init_does_not_validate_provider_content`（spec SC-011 —— 初始化阶段 0 次做配置内容判定）：先建工作区 → 把 `providers/default.toml` 改成非法 TOML → 再执行 init → 断言**成功**（不抛异常、不产生 exit 3），且**未**校验 `providers/` / `mcp/mcp.json` / `skills/*/SKILL.md` 的内容（spec FR-063）

### Implementation for User Story 12

**本故事无独立的客户端实现任务** —— US12 的行为由"渲染阶段对工作区内的供应商 / MCP / Skill 内容**零次**合法性判定"保证（T013 的实现边界 + T057 的断言）；客户端异常映射表的新增行（**T058**）已移至 **Phase 2**（承接 FR-036，与错误类 / 退出码语义同源，避免 story 标签与任务内容错配）。

**Checkpoint**: US12 可独立交付

---

## Phase 18: User Story 13 - `--force` 会重建记忆库文件 (Priority: P13)

**Goal**: `--force` 后三个 sqlite3 被删掉重建（结构完好、数据清空），且命令行**显式提示**记忆库数据已被清空

**Independent Test**: 写入一条会话记录 → `--force` → 记录消失、表结构完好、备份文件不受影响、输出含清空提示行

### Tests for User Story 13 (TDD) ⚠️

- [X] T059 [US13] 在 `tests/unit/test_template_skeleton.py` 写 `test_force_rebuilds_sqlite_and_clears_metadata`：向 `sessions_metadata` 插入 1 条记录 → force 渲染 → 断言三张表**仍存在**（结构完好）且 `sessions_metadata` 记录数 == `0`（spec FR-011 / SC-007）
- [X] T060 [US13] 在 `tests/unit/test_cli_client.py` 写 `test_cli_force_warning_line`：调用客户端的 init 路径 → 带 `--force` 时 stdout **额外有一行**清空提示、不带时**没有**该行；且通用摘要的 `workspace` / `name` / `force` / `templates` / `created` / `skipped` 六个字段**仍完整可见**（spec FR-068 / SC-019）
- [X] T091 [US13] 在 `tests/unit/test_template_skeleton.py` 写 `test_memory_readme_template_content`（spec FR-052 / SC-018 —— **本用例是 SC-018 的单元侧落点**，与 T069 场景 13 的黑盒侧断言互为补充、MUST NOT 互相替代；属 FR-055 的 16 类之外的补充类别）：读取 `donkey/core/workspace/templates/memory/README.md.txt` → 断言含**三个**记忆库文件名（`sessions.sqlite3` / `store.sqlite3` / `knowledge.sqlite3`）、含 `--force`、含**可执行的备份命令示例**（`cp memory/*.sqlite3` 形态 —— **MUST NOT** 只出现单文件示例而遗漏另两个库，宪法 §3.1.1）、含"仅占位空文件 / schema 推迟到后续版本"与"运行数据可选择性导出"（FR-052 / 宪法 D-02）。**写完先跑一次确认失败**，**MUST 在 T027 完成后才可能转绿**

### Implementation for User Story 13

- [X] T061 [US13] 在 `donkey/cli/cli_client.py` 的 `_run_init` 打印段**追加 1 行**：带 `--force` 时在通用摘要**之后**输出强制清空提示行（**文案 MUST 同时涵盖「已清空 / 已重建」两种情形** —— 形如 `[donkey init] 警告：memory/ 下的三个记忆库文件已被清空并重建为出厂状态（会话历史与会话元数据一并清空，--force 恢复出厂设置）。如需保留请先备份。`；**MUST NOT** 只写「已被清空」而遗漏「已重建」情形，理由见下）。MUST 与通用摘要**分行**、MUST 输出到 **stdout**（成功路径提示，非失败信息）、MUST NOT 挤占摘要的六个字段、MUST **恒定输出**（即使工作区此前不存在 sqlite3 文件 —— 此时亦无数据可清空，故文案 MUST 同时涵盖"已清空 / 已重建"两种情形）、**不带** `--force` 时 MUST **不输出**该行（research.md R-11）
- [X] T062 [US13] 核对 `donkey/core/workspace/init.py` 中 `render_templates` 的 sqlite3 force 分支：MUST `unlink` 主库 **+ `unlink` 同名 `-wal` / `-shm`** 后重建（spec FR-011；非 force 时 MUST NOT 触碰附属文件）

**Checkpoint**: US13 可独立交付（含 T091 的记忆库说明文档内容断言 → SC-018 的单元侧落点闭合）

---

## Phase 19: User Story 14 - 记忆库文件开箱就是结构完好的空库 (Priority: P14)

**Goal**: 三个 sqlite3 全部存在；`sessions.sqlite3` 三表两索引齐备且记录数 0；两个占位文件 0 表

**Independent Test**: 渲染后逐个打开三个 sqlite3 → 结构与计数符合预期

### Tests for User Story 14 (TDD) ⚠️

- [X] T063 [US14] 在 `tests/unit/test_template_skeleton.py` 写 `test_sessions_sqlite_full_schema_with_indexes`（spec SC-006 —— 三表两索引齐备 + 记录数 0）：渲染后打开 `memory/sessions.sqlite3` → 断言 `type='table'` 集合含 `checkpoints` / `writes` / `sessions_metadata`；`type='index' AND tbl_name='sessions_metadata'` 含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at`；`sessions_metadata` 记录数 == `0`。**索引断言 MUST 用 `in` / `<=` 判定** —— `sqlite_autoindex_*` 是 PRIMARY KEY 自动索引且 `tbl_name` 亦为 `sessions_metadata`（research.md R-05）
- [X] T064 [US14] 在 `tests/unit/test_template_skeleton.py` 写 `test_memory_sqlite_templates_exist_and_placeholders_empty`：断言三个 sqlite3 文件**均存在**；`store.sqlite3` 与 `knowledge.sqlite3` 的表数各 == `0`、索引数各 == `0`（spec FR-032 / 宪法 D-11）

### Implementation for User Story 14

- [X] T065 [US14] 核对 `build_sessions_sqlite` 的产出与 `harness/report/sessions_sqlite表结构一览.md` §2.2 的 DDL **逐字一致**（6 字段 + 2 索引，spec FR-034）；核对 `sessions_metadata` 的字段顺序不影响存储（§8 Q2：SQLite 按列名匹配，PRAGMA 顺序与 INSERT 不一致无碍）；确认**安装包内无二进制 sqlite3 模板**（`templates/` 下无 `.sqlite3` / `.db` 文件）

**Checkpoint**: US14 可独立交付

---

## Phase 20: 验收层 — 黑盒验收脚本（14 个场景）

**Purpose**: 跨故事的黑盒集成验收 —— 只跑子进程，只观察退出码与文件系统副作用

**⚠️ 本 Phase 不带 [Story] 标签**：spec FR-059 要求 14 个 `test_scenario_*` 函数位于**同一文件**，拆到 14 个故事阶段会造成同文件串行冲突；且**场景 1 一次性断言全部 46 条落地物**（含 26 份 provider 配置，**其资产由 US1 在 Phase 6 一次性就位**）。故黑盒脚本作为**集成验收**集中交付；故事级独立可测性由各故事阶段的单元测试承担。

- [X] T066 创建 `tests/e2e/phase/verify_phase_f001_p2.py`：**MUST NOT** import `donkey.*` 业务代码（宪法 §3.1 黑盒约束）；建立**供 14 个场景复用的被测命令解析辅助函数**（沿用 F001-P1 已确立的口径，spec FR-060）：优先 `shutil.which("donkey")` 控制台脚本 → **MUST 校验其解析到的 `donkey` 包安装位置位于当前工作树之内**（不在则视为不可用，避免测到已安装的其它版本或其它工作树）→ 不可用时回落到 `[sys.executable, "-m", "donkey"]`，回落时 MUST 以**仓库根**为工作目录（由脚本自身位置向上推导）且 MUST 打印**一次**显式告警，MUST NOT 静默回落；两条入口 MUST 产生完全相同的退出码与文件系统副作用。另建**单场景计时器**（上限 10 秒，spec SC-012）；**在 `test_scenario_1_new_workspace` 之内追加双入口一致性断言**（spec FR-060 —— F001-P1 已确立的口径，本 Phase MUST 继承；**沿用 P1 的惯例** —— P1 把该断言并入场景 1，MUST NOT 新增第 15 个测试函数，否则 FR-059 的「14 个 `test_scenario_*` 场景断言函数」与 SC-001 的「14 个场景断言」口径将被稀释）：以子进程分别经**控制台脚本 `donkey`** 与**模块入口 `[sys.executable, "-m", "donkey"]`** 对同一目标路径各执行一次 → 两者**退出码相同**且 **stdout 逐字相同**（**含 `--force` 的强制清空提示行**）；再对**参数用法错误**各执行一次 → 两者 **stderr 的 usage 提示逐字相同**；控制台脚本不可用时只跑模块入口，**MUST 打印一次显式告警**、MUST NOT 静默跳过该对比断言
- [X] T067 追加**场景 1 ~ 5** 到 `tests/e2e/phase/verify_phase_f001_p2.py`：`test_scenario_1_new_workspace_full_tree`（exit 0 + 必填文件 + 五大必填目录 + `skills/example/` + 26 份 provider 配置 + 子文件 + 3 个 sqlite3 + `manifest.json` 全部存在）/ `test_scenario_2_providers_dir_valid`（`tomllib` 解析 `default.toml` 含两字段；**全部 26 份** stub **逐份**解析成功 + `enabled is False` + 凭据为空 —— **MUST NOT 抽样**；并断言 26 份配置中预填的 `[models.*]` 模型条目**合计恰为 51 条**；**集合断言**：providers/ 下以供应商 id 命名的 `.toml` 文件数**恰为 26**（另有 1 个全局默认文件 `default.toml` + 1 份目录索引说明 `README.md`）；`providers/README.md` **恰含 26 个** provider id、无 `...` 省略）—— 对应 spec SC-015（**渲染后**的 workspace 产物，MUST 覆盖全部 26 份）/ `test_scenario_3_mcp_json_valid`（`json.loads` 不抛异常 + 含 `mcpServers`）/ `test_scenario_4_skill_frontmatter_valid`（以 `---` 开头 + `name: example` + `description:`）/ `test_scenario_5_name_injection`（末段名 `foo` → README 正文含 `foo` + `providers/default.toml` 正文含 `foo` + 工作区清单 `name == "foo"`）
- [X] T068 追加**场景 6 ~ 10**：`test_scenario_6_idempotent_no_force`（用户改写 `instruction.md` → 二次 init → 内容不变且 **mtime 不变**，且 stdout **不含**强制清空提示行（FR-059 / SC-019）；**追加子断言** —— 把 `<ws>/manifest.json` 改写为**非法 JSON** 后再执行 `donkey init` → 退出码 `3` + stderr 含可识别的错误标识 + 含一条"下一步" —— 该分支**不破坏安装包**（与 FR-061 排除的两个分支不同），完全可黑盒触发 → 承接 spec US6 场景 4 / FR-069 / SC-020）/ `test_scenario_7_corruption_recovery`（`rm instruction.md` → init → 补齐）/ `test_scenario_8_force_overwrites`（`--force` → 内容恢复出厂、不含用户自定义字样，且 stdout **含**强制清空提示行（FR-059 / SC-019））/ `test_scenario_9_force_preserves_user_content`（`--force` → `media/video.mp4` 与 `donkey.log` 均不变）/ `test_scenario_10_rm_then_init`（`shutil.rmtree` → init → exit 0 且 `instruction.md` 重建）
- [X] T069 追加**场景 11 ~ 14**：`test_scenario_11_no_builtin_tools_yet`（`tools/` 下无 `filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py`）/ `test_scenario_12_no_f002_static_check`（init 不校验 `providers/` 内容 → exit 0）/ `test_scenario_13_force_rebuilds_sqlite3_templates`（插 1 条 `sessions_metadata` → 备份 → `--force` → 三表仍存在 + 记录数 0 + 备份文件非空 + `memory/README.md` 含 `sessions.sqlite3` 与 `--force` 字样；**追加子断言（FR-052 / SC-018 的黑盒侧）** —— `memory/README.md` MUST 同时含**三个**记忆库文件名（`sessions.sqlite3` / `store.sqlite3` / `knowledge.sqlite3`）、含 `--force`、含**可执行的备份命令示例**（`cp memory/*.sqlite3` 形态 —— MUST NOT 只出现单文件示例而遗漏另两个库））/ `test_scenario_14_sqlite3_templates_with_schema`（三文件存在 + `sessions.sqlite3` 三表两索引 + 记录数 0；两个占位文件 0 表）
- [X] T070 跑 `pytest tests/e2e/phase/verify_phase_f001_p2.py -v` → **14 个场景断言 100% 通过**（spec SC-001）

**Checkpoint**: 跨故事黑盒验收闭合（14 / 14 PASS）

---

## Phase 21: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的收口 —— 静态检查、回归、覆盖率、文档同步

- [X] T071 [P] 跑 `ruff check donkey/ tests/`（覆盖 `donkey/core/` / `donkey/cli/` 与 `tests/unit/` / `tests/e2e/phase/` 全部源码与测试文件）→ 零 error 零 warning；逐条修复（spec FR-064 —— 分层约束 MUST 保持；spec FR-065 —— 静态检查零 error；spec SC-017 —— 全仓 MUST NOT 出现 LangSmith 任何形态；spec SC-009）
- [X] T072 [P] 跑 `mypy donkey/ tests/`（覆盖 `donkey/core/` / `donkey/cli/` 与 `tests/unit/` / `tests/e2e/phase/` 全部源码与测试文件）→ 零 error 零 warning；逐条修复（spec SC-009）。**注意**：mypy 的 `[[tool.mypy.overrides]] module="tests.*"` 已放宽测试层的严格项（F001-P1 已配置），新增测试函数无需完整类型标注
- [X] T074 在 `tests/unit/test_template_skeleton.py` 写 `test_exit_code_set_is_exactly_0_to_3`：**写完先跑一次确认失败**（断言当前不成立），再继续。断言 ① `donkey/core/exit_codes.py` 中**数字型退出码常量**（`EXIT_CODE_*` 且值为 `int`）里，**本阶段使用的那批恰为** `{EXIT_CODE_OK=0, EXIT_CODE_PATH_NOT_FOUND=1, EXIT_CODE_PATH_PERMISSION=2, EXIT_CODE_TEMPLATE_GENERATION=3}` —— **注意**：该模块同时定义 `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` 与 6 个**段位元组**（`EXIT_CODE_SEGMENT_*`，值为 tuple，MUST NOT 计入本断言），故 MUST 先按「值为 int 且名字以 `EXIT_CODE_` 开头（排除 `EXIT_CODE_SEGMENT_`）」过滤，**MUST NOT** 直接对模块内全部常量做集合相等；断言 ② `donkey/cli/cli_client.py` 的 `_EXCEPTION_TO_EXIT_CODE` 登记的码值集合**恰为** `{1, 2, 3}`（基类 `WorkspaceInitError` 不登记、未登记子类兜底 `1`）；断言 ③ `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` **未被**本 Phase 任何映射登记，码值 `4` / `5-10` 未被触发（spec FR-037 / FR-038 / SC-010）；断言 ④ `pyproject.toml` 的 `[project].dependencies` 列表长度恰为 **1** 且该唯一项为 `langgraph-checkpoint-sqlite`（spec SC-021 / FR-067 —— MUST NOT 存在其它第三方运行期依赖）
- [X] T073 回归（**MUST 在 T074 之后执行** —— 否则本次回归不含 T074 新增的 `test_exit_code_set_is_exactly_0_to_3`）：`pytest tests/e2e/phase/verify_phase_f001_p1.py -v` + `pytest tests/unit/test_init_workspace.py tests/unit/test_cli_client.py tests/unit/test_template_skeleton.py -v` → **全部仍全绿**（spec SC-002 —— 前置 Phase 退出条件 MUST NOT 被破坏；spec SC-008 —— 单测不少于 **16** 个且覆盖 FR-055 的 **16** 类）
- [X] T075 覆盖率：`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` → `donkey.core` 行覆盖率 **≥ 80%**（spec SC-013 / 宪法 §4.6）。**MUST NOT** 把 `--cov` 写进 pytest 全局 `addopts`（否则 e2e 单独运行时会因不 import 业务代码把覆盖率拉到 0 而误报失败，research.md R-13）；e2e 黑盒脚本**不计入**该覆盖率；不足时**优先补单测**而非下调阈值
- [X] T076 全量：`pytest tests/ -v`（收集 `tests/unit/` 与 `tests/e2e/phase/` 全部用例）→ F001-P1 + F001-P2 全部 PASS（其它 Phase 的测试允许 FAIL）
- [X] T077 跑 quickstart §7.1 的 **B2b 打包产物自检**：**先 `rm -rf build *.egg-info /tmp/f001p2-wheel`**（setuptools 会把源文件复制进 `build/lib/` 且不清除隐藏文件 —— 残留的 `build/` 会让旧配置的缺陷被掩盖）→ `python3 -m pip wheel . --no-deps --no-build-isolation -w /tmp/f001p2-wheel` → 解包断言 `donkey/core/workspace/templates/` 下的 **37 个 `.txt` 源文件全部在 wheel 内**，且**必须含** `donkey/core/workspace/templates/.gitignore.txt`（隐藏名）—— 缺一即代表"安装后 `donkey init` 报源模板缺失 exit 3"（spec FR-041 / FR-007）。**MUST NOT** 用 `pathlib.rglob` 代替打包产物核对（`rglob` 会包含隐藏文件 → 假阳性）
- [X] T078 在 `donkey/cli/cli_client.py` 更新 `donkey init` 的**子命令 help / description** 与 **`--force` 的 help** 文案：删除 P1 遗留的"不加载模板清单、不生成模板内容"与"本阶段仅记录并回显，不触发任何删除 / 重置"，改为与 P2 实际行为一致（"生成 workspace 模板骨架（46 个模板条目）+ 工作区清单"；"--force 恢复出厂设置：模板文件与三个记忆库模板被删后重建，记忆库历史与元数据一并清空"）。属 spec FR-064 ③ / cli-contract §5 第 3 行（**客户端改动共 3 项**）；MUST NOT 引入其它客户端行为变更。**MUST 在 T058 之后执行**（同一文件）
- [X] T079 [P] 同步仓库级文档：`harness/features/README.md`（F001-P2 的落地状态 + 段位/退出码表；**sqlite3 模板构造落点已于 2026-10-23 同步为 `core/workspace/sqlite3_templates.py`**（§4.1.1 三处 + "memory/ 模板边界" 段）—— 本任务**只需核对**一致性，MUST NOT 重复改写；**并登记宪法临时例外 E-01 的范围扩展**（原范围「仅 F001-P1」→ 经 Maintainer 批准扩展至「仅 F001-P1 与 F001-P2」，过期时间「F001-P3 结束前」不变，见 plan G5））与 `harness/features/feature001_phase002_template_skeleton.md`（P2 部分的实现落点回填）。**⚠️ MUST 同时核对宪法 `.specify/memory/constitution.md` §6.3 的 E-01「范围」行** —— 该行**已回写为「仅 F001-P1（`cli_validation` Phase）与 F001-P2（`template_skeleton` Phase）」**（**宪法 §6.1 单一权威**：plan G5 虽被 E-01 列为登记位置之一，但宪法摘要行才是权威文本，两源 MUST 一致）→ 本任务**只需核对与 plan G5 一致，MUST NOT 再改动该行**；**过期时间行与替代保障清单 MUST NOT 改动**。**MUST NOT** 改动其它 Phase 的章节
- [X] T080 跑 [quickstart.md](quickstart.md) §1 ~ §10 的全部验证命令并记录结果（含 §4 的 4 条分层 grep 自检、§7 的 12 项构建期自检 + §7.1 的 B2b 打包自检、§8 的 sqlite3 结构自检、§10 的 21 条 SC 对照表 + §10.1 的打包完整性门禁）。**§7 的 B1 ~ B12 汇总以 T086 为准**（本任务覆盖 §7 的命令执行，B5 ~ B10 的判定结果由 T086 汇总）
- [X] T086 汇总核对 [contracts/template-manifest.md](contracts/template-manifest.md) §7 的 **B1 ~ B12 全套**（承接拆解后的 T032 尾段 —— T032 在 Phase 6 只跑 B1 / B2 / B3 / B4 / B11 / B12 + §7.1 的 B2b，B5 ~ B10 由各故事阶段的测试承载）：**MUST 逐项确认** —— ① B1（清单条目总数 == 46）与 B2 / B2b（37 个源双向一一对应 + wheel 内含隐藏名 `.gitignore.txt`；**B2b 为 quickstart §7.1 的扩展项，非契约 §7 的独立编号**）由 **T032** 覆盖；② B5 / B6 / B8（26 份 provider 可被 `tomllib` 解析 + 开关全关 + 凭据为空 + `default.toml` 两字段为空串）由 **T034** 覆盖；③ B7（`[models.` 行数 == **51**）由 **T035** 覆盖；④ B9（`mcp/mcp.json` 可被 `json.loads` 解析且含 `mcpServers`）由 **T039** 覆盖；⑤ B10（`SKILL.md` frontmatter 恰 2 字段）由 **T041** 覆盖；⑥ B11（安装包无二进制 sqlite3 模板）由 **T032** 覆盖；⑦ B12（渲染后无 `{{` 占位符残留）由 **T018 / T043** 覆盖（**唯一判定点** —— T032 MUST NOT 自行断言）；⑧ **B3 / B4**（6 个目录条目与 3 个 sqlite3 条目 MUST NOT 配备同名 `.txt` 源）由 **T032** 覆盖。**B1 ~ B12 共 12 项 MUST 全部通过**（spec FR-041 / FR-030 / FR-046 / FR-048 / FR-049；任一缺失或任一不通过即判 Phase 未达成）

**Checkpoint**: F001-P2 全部退出条件达成

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**：无依赖 —— 可立即开始（**T001 → T002 → T003 严格串行** —— T003 要跑上游 saver 导入 + 建表冒烟，而本机用户级 site-packages 存在 `langgraph-checkpoint-sqlite 3.1.1` + `langgraph-checkpoint 4.2.0` 的不兼容组合（导入即 ImportError），T003 MUST 在 T002 把依赖装好之后才能跑，research.md R-01）
- **Foundational (Phase 2 ~ 5)**：依赖 Setup 完成 —— **BLOCKS 所有用户故事**
  - Phase 2（错误类 / 退出码 / 工作区清单）→ Phase 3（sqlite3 构造器）→ Phase 4（清单加载与渲染）→ Phase 5（内部流程与门面）
  - Phase 3 与 Phase 2 **可并行**（**实现**文件不同、无相互依赖；**但 T006 / T081 / T082 与 T008 同写 `tests/unit/test_template_skeleton.py` → 同文件，建议错峰**，见「Parallel Opportunities」）
  - Phase 4 的 T013 依赖 Phase 2 的 T004（异常类）+ Phase 3 的 T009（构造器）
  - Phase 5 的 T015 依赖 Phase 5 的 T016 / T017（门面函数体在本阶段才被替换）；T015 的**绝对值**复验（`46 / 40 / 0`）依赖 Phase 6 的 **T031**（追加 43 条清单）—— 故 T015 采用动态计数口径，绝对值由 T018 承接
  - Phase 5 的 **T083**（步骤 ⑤ 失败不回滚，spec 澄清 #26 / plan R-16）与 **T085**（步骤 ③ 一切失败含 `ENOSPC` 归退出码 `2`）是 **T016 的护栏单测** → 两者 MUST **先于 T016** 写入并确认失败（此时 `init_workspace_inner` 尚不存在 → ImportError），T016 落地后转绿；T083 / T085 同写 `tests/unit/test_template_skeleton.py` → 与 T015 同文件，**建议错峰**
  - Phase 2 的 **T081**（FR-055 第 16 类：工作区清单解析失败 → exit 3）与 T006 同组，同属 Phase 2（Foundational）；二者写完先确认失败，待 T007（`manifest.py` 落地）后转绿
  - Phase 2 的 **T082**（FR-018 的「读取文件不存在 → 返回『无』」与 FR-023 的「`ensure` 与 `write` 严格等价」）与 T081 同组、同属 Phase 2（Foundational）；同样待 T007 后转绿
- **User Stories (Phase 6 ~ 19)**：全部依赖 Foundational 完成（含 Phase 2 的 T081 —— FR-055 第 16 类的清单解析失败 → exit 3 单测）
  - Phase 6 的 **T087 ~ T090**（FR-053 / FR-043 / FR-050 / FR-051 的内容级断言）依赖 **T019 / T022 / T023 / T024 ~ T026** 的模板源产出 → MUST 在 Phase 6 末尾执行（与 T018 同批）
  - Phase 11 的 **T084**（工作区重命名后保留旧名，spec 澄清 #27 / plan R-17）依赖 Foundational 完成 + US1 的模板资产就位（需先 init 出真实工作区再改名）
- **验收层 (Phase 20)**：依赖 Phase 6 ~ 19 全部完成（场景 1 需要 US1 交付的 provider 资产）
- **Polish (Phase 21)**：依赖全部故事 + 验收层完成；其中 **T086**（B1 ~ B12 全套汇总）依赖 T032 / T034 / T035 / T039 / T041 / T018 / T043 **全部完成** —— 即 T086 MUST 在 Phase 6 ~ 10 全部收口后执行（**这是 T032 拆分后新增的跨阶段依赖**，B5 ~ B10 不在 T032 的范围内）

### User Story Dependencies

| 故事 | 依赖 | 独立可测性 |
|---|---|---|
| **US1 (P1)** | 仅 Foundational（含 Phase 2 的 **T081** —— FR-055 第 16 类的清单解析失败 → exit 3 单测，属 Foundational 而非 US1） | ✅ 单测 T018（渲染后 41 文件 / 7 目录 / 计数 46·40·0 / 无占位符残留 / **37 个源齐备 → exit 0**）+ **T087 ~ T090**（FR-053 / FR-043 / FR-050 / FR-051 的**内容级**断言）。**US1 交付全部 37 个文本源**（含 26 份 provider 配置与 `providers/README.md`）；US2 只做**内容质量**验证 |
| **US2 (P2)** | US1 的模板资产目录（`templates/providers/`，**资产由 US1 创建**） | ✅ 单测 T034 / T035 / T036（26 份可解析 + 全关闭 + 51 条模型 + 索引含 26 个 id） |
| **US3 (P3)** | Foundational | ✅ 单测 T039 |
| **US4 (P4)** | Foundational | ✅ 单测 T041 |
| **US5 (P5)** | US1 的 `README.md.txt` / `default.toml.txt` + Phase 2 的工作区清单 | ✅ 单测 T043（**一致性三处**名称一致 + 无占位符残留） |
| **US6 (P6)** | Foundational | ✅ 单测 T045（内容 + mtime 双断言）+ T084（重命名后保留旧名 + 不报错） |
| **US7 (P7)** | Foundational | ✅ 单测 T047 |
| **US8 (P8)** | Foundational + Phase 2 的工作区清单 | ✅ 单测 T049 |
| **US9 (P9)** | Foundational | ✅ 单测 T051 |
| **US10 (P10)** | Foundational | ✅ 单测 T053 |
| **US11 (P11)** | US1 的 `tools/README.md.txt` | ✅ 单测 T055 |
| **US12 (P12)** | Foundational | ✅ 单测 T057 + e2e 场景 12（客户端异常映射 T058 属 Foundational，不属本故事） |
| **US13 (P13)** | Phase 3 的构造器 + Foundational | ✅ 单测 T059 / T060 + **T091**（FR-052 / SC-018 的单元侧内容断言）|
| **US14 (P14)** | Phase 3 的构造器 + Foundational | ✅ 单测 T063 / T064 |

### 用户故事 ↔ e2e 黑盒场景对照（spec 的 1:1 映射）

| 故事 | e2e 场景 | 故事 | e2e 场景 |
|---|---|---|---|
| US1 (P1) | 场景 1 · 全新创建 | US8 (P8) | 场景 8 · `--force` 恢复出厂 |
| US2 (P2) | 场景 2 · providers 可解析 | US9 (P9) | 场景 9 · `--force` 保留用户内容 |
| US3 (P3) | 场景 3 · mcp JSON 可解析 | US10 (P10) | 场景 10 · rm 后重建 |
| US4 (P4) | 场景 4 · SKILL frontmatter | US11 (P11) | 场景 11 · 无内置工具文件 |
| US5 (P5) | 场景 5 · 名称注入 | US12 (P12) | 场景 12 · 不做配置检查 |
| US6 (P6) | 场景 6 · 幂等不改 mtime | US13 (P13) | 场景 13 · `--force` 重建 sqlite3 |
| US7 (P7) | 场景 7 · 缺失补齐 | US14 (P14) | 场景 14 · sqlite3 结构完整 |

### Within Each User Story

- 测试 MUST 先写并确认**失败**，再补实现（TDD，spec FR-055 / FR-058）
- 模板资产任务（源文件 / 清单条目）先于该故事的自检任务
- 行为硬化任务（幂等 / 强制 / 边界）先于该故事的 e2e 断言
- 每个故事完成后可**独立验证**（跑该故事的单元测试）

### Parallel Opportunities

- Phase 1 的 T001 → T002 → T003 **严格串行**（理由同「Phase Dependencies」：T003 的上游 saver 导入 + 建表冒烟 MUST 在 T002 装好兼容版本之后才能跑，research.md R-01）
- Phase 2 的 T004 / T005 可并行（`exceptions.py` vs `exit_codes.py`，不同文件）
- Phase 2 的 T006 与 Phase 3 的 T008 可并行（同一测试文件的不同测试函数，但**同文件 → 建议错峰**）；Phase 2 的 T081 / T082 与 T006 同组（同文件 → 建议错峰或合并为一次批量写入）
- Phase 3 的 T009 与 Phase 4 的 T012 可并行（`sqlite3_templates.py` vs `init.py`）
- Phase 4 的 T010 / T011 / T014 可并行（同上，同文件 → 建议错峰）；Phase 5 的 T015 依赖 T016 / T017，不可与它们并行
- Phase 5 的 T017 与 Phase 4 的测试任务可并行；Phase 5 的 **T083 / T085** 与 Phase 4 的测试任务可并行（同一测试文件 → **建议错峰**），但二者 MUST **先于 T016**
- Phase 6 的 T019 ~ T031 几乎全部可并行（**每个模板源一个独立文件**）—— 这是本 Phase 最大规模的并行机会；**T087 ~ T090 依赖 T019 / T022 / T023 / T024 ~ T026 的产出 → MUST 在 Phase 6 末尾执行（与 T018 同批），不可与资产任务并行**
- Phase 7 的 T034 / T035 / T036 可并行（同文件 → 建议错峰）；T037（逐条核对与修正）依赖 T034 / T035 的断言结果
- Phase 8 ~ 19 的故事阶段**全部依赖 Foundational**，故可并行推进（不同故事改动的文件不同）；Phase 11 的 T084 与其它故事阶段可并行（同文件 → 建议错峰）
- Phase 21 的 T071 / T072 / T079 可并行（T074 已去掉 `[P]` —— MUST 在 T073 之前串行执行）；**T086 MUST 在 Phase 6 ~ 10 全部收口后执行**（依赖 T032 / T034 / T035 / T039 / T041 / T018 / T043），不可与它们并行

### 受限（不可并行）

- T019 ~ T031 全部写入 `donkey/core/workspace/templates/` 下**不同**文件 → 可并行；但 T031 改 `manifest.json`、T029 抽取 provider 源 → T031 依赖 T029 完成（清单条目须与源文件一一对应）
- T067 ~ T069 全部追加**同一文件** `tests/e2e/phase/verify_phase_f001_p2.py` → **严格串行**
- `tests/unit/test_template_skeleton.py` 的多个测试任务 → 同文件，**建议错峰**（或合并为一次批量写入）
- T073（回归）**依赖 T074**（新增 `test_exit_code_set_is_exactly_0_to_3`）→ Phase 21 内二者 MUST 串行，且 T074 在前
- **T016 依赖 T083 / T085**（二者是它的护栏单测，MUST 先写并确认失败）→ Phase 5 内 MUST 串行，且 T083 / T085 在前
- **T086 依赖 T032 / T034 / T035 / T039 / T041 / T018 / T043**（B5 ~ B10 由各故事阶段承载）→ Phase 21 内 MUST 串行，且在 Phase 6 ~ 10 全部收口之后
- T012 与 T013 同写 `donkey/core/workspace/init.py` → 同文件，**串行**（T012 的 `[P]` 仅指可与 T009 并行）

---

## Parallel Example: User Story 1

```bash
# 启动 US1 的模板源任务（每个写一个独立文件，可全部并行）
Task: "覆盖 donkey/core/workspace/templates/instruction.md.txt …"
Task: "覆盖 donkey/core/workspace/templates/providers/default.toml.txt …"
Task: "覆盖 donkey/core/workspace/templates/mcp/mcp.json.txt …"
Task: "新建 donkey/core/workspace/templates/README.md.txt …"
Task: "新建 donkey/core/workspace/templates/.gitignore.txt …"
Task: "新建 donkey/core/workspace/templates/tools/README.md.txt …"
Task: "新建 donkey/core/workspace/templates/mcp/README.md.txt …"
Task: "新建 donkey/core/workspace/templates/skills/README.md.txt …"
Task: "新建 donkey/core/workspace/templates/skills/example/SKILL.md.txt …"
Task: "新建 donkey/core/workspace/templates/memory/README.md.txt …"

# 串行的两步（清单条目依赖源文件就位）
Task: "抽取 26 份 provider 配置源到 templates/providers/<id>.toml.txt …"
Task: "在 manifest.json 的 entries 末尾追加 43 条 …"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup（依赖声明 + N-12 门禁闭合）
2. 完成 Phase 2 ~ 5: Foundational（**CRITICAL** —— 阻塞所有故事）
3. 完成 Phase 6: User Story 1（模板资产骨架 + 清单 + 计数口径）
4. **STOP and VALIDATE**：跑 `pytest tests/unit/test_template_skeleton.py -v` + quickstart §2 场景 1 → 骨架完整、41 文件 / 7 目录、计数 46·40·0
5. 交付 / 演示

### Incremental Delivery

1. Setup + Foundational → 引擎就绪（此时 `donkey init` 已能渲染，但清单只有 P1 的 3 条 → 需 **T031**（清单追加 43 条）+ **T019 ~ T030**（37 个源）全部就位后才有完整骨架）
2. US1 → 验证（骨架 + 计数 + 工作区清单）→ 交付
3. US2 → 验证（provider 目录机器可读）→ 交付 —— 至此 e2e 场景 2 具备绿灯条件（场景 1 的绿灯条件在 US1 完成时即已具备）
4. US3 ~ US14 → 逐个验证 → 交付
5. Phase 20 → 14 个黑盒场景统一验收
6. Phase 21 → 静态检查 + 回归 + 覆盖率 + 文档

### Parallel Team Strategy

多开发者并行时：

1. 团队共同完成 Setup + Foundational（Phase 1 ~ 5）—— 这部分**串行依赖强**，不宜拆分
2. Foundational 完成后：
   - 开发者 A：Phase 6（US1 —— 共 **16** 个任务 T018 ~ T033，其中模板资产任务 **13** 个 T019 ~ T031，天然并行）
   - 开发者 B：Phase 7（US2 provider **内容质量核对与修正**，T034~T037）；provider 源的 **抽取**（T029）属 Phase 6 / US1
   - 开发者 C：Phase 8 ~ 19（US3 ~ US14 的行为硬化，单测为主）
3. Phase 20 的 14 个场景**严格串行**（同一文件）—— 建议单人完成
4. Phase 21 并行收口

---

## Notes

- [P] 任务 = 不同文件、无未完成任务的依赖
- [Story] 标签映射到 spec.md 的 US1 ~ US14；Setup / Foundational / 验收层 / Polish 阶段**不带**故事标签
- **每个测试任务 MUST 先写并确认失败**（TDD），再执行对应的实现任务
- 每个故事完成后 MUST 跑该故事的单元测试做独立验证
- 每完成一个逻辑组即可提交（git commit）；**MUST NOT** 提交未通过静态检查的代码
- 遇到任何 checkpoint 停下即可独立验证
- 避免：含糊任务、同文件冲突、破坏故事独立性的跨故事依赖
- **禁止事项**：MUST NOT 引入 `langsmith` / `deepagents` / `ShellToolMiddleware`（宪法 N-12 / §3.2）；MUST NOT 生成内置 `@tool` 文件（属 P3）；MUST NOT 做 F002 的配置静态检查（属另一码段）；MUST NOT 在安装包内携带二进制 sqlite3 模板（宪法 D-05）
