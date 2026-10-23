---

description: "Task list for F001-P3 builtin_tools —— donkey init 内置工具与变更记录契约幂等生成"
---

# Tasks: F001-P3 `builtin_tools` —— `donkey init` 内置工具与变更记录契约幂等生成

**Input**: Design documents from `specs/001-donkey-init-workspace/phase-3-builtin-tools/`
（spec.md · plan.md · research.md · data-model.md · contracts/ ×5 · quickstart.md）

**Prerequisites**: plan.md（必需）、spec.md（必需，用户故事）、research.md、data-model.md、contracts/、quickstart.md

**Tests**: 含测试任务 —— spec FR-058 明确要求**不少于 15 个单元测试用例**并逐条列出必备类别，FR-060 要求集成层**不少于 4 个**用例，FR-064 要求黑盒脚本含 **16** 个断言函数。故本清单**强制**按 TDD 组织（先写测试 → 确认失败 → 再补实现）。

**Organization**: 任务按用户故事分组。**本 Phase 的 15 个用户故事是"验收切片"而非"实现切片"** —— 15 个故事 ↔ 15 个 e2e 黑盒场景一一对应，但实现上共享同一套契约库与同一份模板清单（data-model.md §1）。故本清单的组织原则为：

| 层次 | 内容 | 对应 Phase |
|---|---|---|
| **共享地基** | Phase 2 内 **3 处**改动（核心层 2 处：退出码 / 异常类 + 客户端映射 1 行）+ 单元测试夹具（本 Phase 全局 **4 处** —— 第 4 处 = 编排层条目级豁免 → Phase 11 / T049） | Phase 2（Foundational） |
| **模板资产** | 6 个 `tools/` 文件 + 8 条清单条目 + 8 个新源 + 2 处覆盖源（决定"落地什么"） | **全部在 Phase 3（US1）**；US2 ~ US15 只做行为硬化与断言 |
| **行为硬化** | 每故事的幂等 / 强制 / 边界语义与对应单测 | 各故事阶段（Phase 4 ~ 17） |
| **黑盒验收** | 16 个场景断言函数（Phase 18） + 改写 P2 的**阶段边界断言组**（T094 / T095，**已前移至 Phase 3 末尾**） | Phase 18 + Phase 3 末尾 |

> ⚠️ **为什么 3 个工具模板在 US1 阶段一次性写完、而不是分散到 US3/US4/US5**：spec 的 **US1 验收场景 1** 要求"init 后 `tools/` 下**同时**存在 `__init__.py` / `changes.py` / `filesystem.py` / `commandline.py` / `webfetch.py` / `README.md` **6 个文件**" → US1 要能**独立验证**，6 个文件就必须同时就位。若把工具模板推迟到 US3/US4/US5，US1 的独立测试将永远无法通过（且同一文件被多阶段反复改写 → 破坏"不同文件、无依赖"的并行前提）。故：**工具模板在 US1 阶段写完整**，US3/US4/US5 的阶段只做**行为硬化 + 断言**（与 F001-P2 的"模板资产全在 US1、其余故事只做内容校验与行为硬化"同构 —— 见 [phase-2 tasks.md](../../phase-2-template-skeleton/tasks.md) 的 Organization 段）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可**并行推进**（**无未完成任务的依赖**）—— ⚠️ **同一文件内的多个 `[P]` 任务 MUST 分批提交**（本清单的多数断言任务都写同一个 `tests/unit/test_builtin_tools.py` / `tests/integration/test_init_to_load.py`；逐文件约束见下方「受限（不可并行）」表）
- **[Story]**: 该任务归属的用户故事（US1 ~ US15）
- 描述中 MUST 含**精确文件路径**

> **编号编排说明**：任务 ID 按**逻辑分组**编排（T005 ~ T008 属 Phase 2 的核心层组、T009 ~ T021 属 US1 的资产组），**非文档序**；ID 一经分配 MUST NOT 重排或复用。
> **两处非文档序的特例（2026-10-23 `/speckit.analyze` 后补）**：`T094` / `T095`（改写 P2 的阶段边界断言）已从 Phase 18 **前移至 Phase 3 末尾** —— 清单条目一变（P3 的 T014），P2 的绝对值断言即失效，改写 MUST 紧随其后，P2 套件才尽早恢复绿（见「P2 套件的中间态」段）；`T101`（依赖安装）、`T102`（单元测试覆盖面核查）与 `T103`（构建产物打包核对）为分析后补插，编号落在末位但分别位于 Phase 1 与 Phase 19；`T104`（命令工具 `timeout` 无上限断言，spec FR-028）为 2026-10-23 spec 定点修订轮补插，编号落在末位但位于 **Phase 5（US3）** 段末尾（T029 之后）；`T105`（退出码 4 的映射与错误信息断言）位于 **Phase 2** 段末（T007 之后）、`T106`（三个记忆库文件未被触碰断言）位于 **Phase 3** 段内（T019 之后）、`T107`（网络工具边界陈述断言）位于 **Phase 7（US5）** 段末（T042 之后）、`T108`（读取侧分页边界断言）位于 **Phase 6（US4）** 段末（T035 之后）—— 同为 2026-10-23 定点修订轮补插，编号落在末位但**相位各不相同**（编号 ≠ 相位）。
>
> **本清单的权威源与镜像**：契约值（12 基线字段 / 2000 行 / 50 KiB / 5 MiB / 120 秒 / 54 条 / 48 / 49 / 10 / 47-1-54 计数）的**唯一权威源 = spec FR 与 contracts/**；plan R-xx、data-model §、本清单各处均为**镜像** —— 口径变更 MUST 先改 spec，再逐处同步镜像。
>
> **实现要点引用**：涉及非显然实现选择的任务 MUST 标注对应的 research.md 决策编号（R-xx）—— 实现者 MUST 先读该决策的"理由"再动手。

### 本轮对齐登记（2026-10-23 · spec 定点修订轮第二轮 + plan 对齐轮）

> spec 已完成第二轮定点修订（`## Clarifications` 新增第 5 段 / 4 项决策 —— **需求层语义逐条未变**，FR 仍 **105** 条、SC 仍 **24** 条，编号一字未动），plan 已随之对齐。本清单据此**原地改写** —— **未新增 / 未删除 / 未重编号任何任务**（下游依赖 〔覆盖 spec FR-xxx · SC-xxx〕 标签）：

| spec 决策 | 本清单落点 | 性质 |
|---|---|---|
| **S1** FR-050 的授权来源由"spec 自设豁免 + 强制登记口径"改为**引用宪法例外 E-02 + §5 章 [D-19]** | **T016**（模板产出约束）、**T046**（断言）、**T094 ③**（P2 持久不变量的口径） | **授权来源改引用** —— 本清单 MUST NOT 再写"spec 自设豁免"，MUST NOT 自设任何宪法例外 |
| **S1b** E-02 的两条边界（MUST NOT 命名为 `agent.py` / `main.py`；MUST NOT 承担"创建智能体"职责） | **T016**（实现约束）+ **T046**（① ~ ④ 四条断言） | **边界落地**（宪法 E-02 早已列明，非 spec 新增） |
| **S2** FR-004 的指纹"为空"钉死为 `null`（Python 侧 `None`，MUST NOT 用空串） | **T060**（`previous_hash is None`）、**T062**（基线键集合）、**T073**（`new_hash is None`） | **表述钉死** —— 契约层本就按 `null` 落地（contracts/change-record-contract.md §1 第 7 / 9 行） |
| **S3** SC-021 改写为**两类可判定判据**（行为层报错 + 静态层措辞 ≥ 1 次） | **T012**（模板实现约束）、**T107**（静态层措辞 + 地址范围放行 + 与 T038 ~ T041 的分工）、**T038 / T039 / T040 / T041**（行为层四道边界各自报错） | **判据可判定化** —— 四项边界、5 MiB 数值、"不限制地址范围"的结论均未变 |
| **S4** FR-068(a) 的嵌套加粗修复 | 无 —— 纯 Markdown 格式 | **纯格式** |
| **S5** "read_file 返回值语义变更"收敛为 **FR-015** 单一权威表述 | **T010**（`read_file` 返回**呈现文本**的形态约束） | **维护面收敛**（×3 → ×1），语义未变 |
| **分析轮**（2026-10-23 · `/speckit.analyze` 交叉核对） | **T008 ~ T012**（补 FR-076 / FR-079 的实现侧约束）、**T012**（补 FR-090 的 docstring 义务）、**T008**（覆盖标签补 FR-005 / FR-012 / FR-091）、**T100**（计数纠偏）、Phase 18 子标题、US15 Independent Test（指纹"为 `null`"）、头部 `[P]` 定义 | **表述对齐 + 落点补齐** —— 任务 ID T001 ~ T108 与相位一律未动 |

> **实施者须知**：本轮**未新增任何任务** —— 全部对齐都落在既有任务的描述内。故**任务 ID（T001 ~ T108）与相位 MUST NOT 重排**；下游的 〔覆盖 spec FR-xxx · SC-xxx〕 标签保持有效。

## Path Conventions

- **单包结构**：仓库根即包根 `donkey/`；`donkey/core/` 为引擎层、`donkey/cli/` 为客户端层
- **测试**：`tests/unit/`（函数级）、`tests/integration/`（**本 Phase 首次启用**）、`tests/e2e/phase/`（黑盒子进程验收）
- **模板资产**：`donkey/core/workspace/templates/`（安装包内，与源码同树）—— **本 Phase 的主战场**
- **仓库级**：`pyproject.toml`、`.github/workflows/ci.yml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 引入本 Phase 唯一的**新增**开发期依赖、**安装 dev 依赖并核对版本**（T101）、交付 CI 工作流（闭合宪法 §6.3 临时例外 E-01）、跑一次门禁冒烟

- [X] T001 [P] 在 `pyproject.toml` 的 `[project.optional-dependencies].dev` 追加 `pytest-httpx>=0.35`（实测装入 0.36.2，兼容 httpx 0.28.1）。**MUST NOT** 进 `[project].dependencies` —— donkey 自身的运行期依赖 MUST 仍恰为 **1** 个（`langgraph-checkpoint-sqlite>=3.1,<4`）。**MUST NOT** 改动 `[tool.setuptools.package-data]`（已是 `"**/*.txt"`，新增的 8 个 `.txt` 自动被携带 —— research.md R-09）、`[tool.ruff]`、`[tool.mypy]`、`[tool.pytest.ini_options]`（`python_files = ["test_*.py", "verify_phase_*.py"]` 已被新脚本 `verify_phase_f001_p3.py` 依赖，plan G13）　〔覆盖 spec FR-080 · SC-015〕
- [X] T101 安装依赖并核对版本：执行 `.venv/bin/pip install -e ".[dev]"`（仓库内 `.venv`，与 quickstart §0 一致），核对 `.venv/bin/pip list` 中 `pytest-httpx` **≥ 0.35** 且 `httpx` **≥ 0.23** （二者是网络工具用例的硬依赖 —— 缺则 T036 ~ T042 全部以 `ModuleNotFoundError` 失败）；MUST NOT 把 `pytest-httpx` 装进运行期依赖（spec FR-080）　〔覆盖 spec FR-080 · SC-015〕
- [X] T002 [P] 新建 `.github/workflows/ci.yml`：MUST 含四类命令 —— `pytest tests/`、`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80`、`ruff check donkey/ tests/`、`mypy donkey/ tests/`；Python 版本矩阵 MUST 覆盖 **3.11 与 3.12**（`requires-python = ">=3.11"`）；覆盖率 MUST 用**独立命令**度量，**MUST NOT** 写入 pytest 全局 `addopts`（否则 e2e 单独跑时不 import 业务代码会把覆盖率拉到 0 而误报 —— research.md R-14）　〔覆盖 spec FR-065 · SC-001〕
- [X] T003 执行 `quickstart.md` §1 的**门禁冒烟**：`python -c "import sys, donkey.core.api, donkey.cli.cli_client; print('langsmith' in sys.modules)"` 的输出 MUST 为 `False`（langsmith 进入进程即为宪法 N-12 违例，MUST 停止实施并按 quickstart §9 排查）。**口径**：该检查 MUST 限定为 **donkey 自有代码路径**的导入链，MUST NOT 拿"用户导入渲染产物"的语境去复核它（spec FR-078）　〔覆盖 spec FR-078 · SC-012〕

**Checkpoint**: 依赖就位 + CI 已交付 + N-12 门禁实证闭合

---

## Phase 2: Foundational — 核心层 2 处 + 客户端映射 1 行（共 3 处）+ 单元测试夹具

**Purpose**: 落地 exit 4 的改动 —— **本 Phase 2 内 = 3 处**（新增异常类 1 个 + 退出码常量文档串 1 处 + 客户端映射 1 行），**本 Phase 全局 = 4 处**（第 4 处 = **编排层条目级豁免**，落在 **Phase 11 / T049** —— 见 contracts/cli-contract.md §1「3 处 + 1 处编排层豁免」与 §6、research.md R-07 / R-10），并建立所有后续单元用例共享的夹具

- [X] T004 在 `donkey/core/exit_codes.py` 把 `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` 的文档串从"属 F001-P3（子段 3），本阶段不触发"改为"**本阶段启用（F001-P3）**"；**常量值 MUST NOT 改动**（已由 F001-P1 建档，MUST NOT 重复定义 —— research.md R-10）；同时把模块 docstring 里的阶段说明补上 exit 4　〔覆盖 spec FR-070 / FR-074 · SC-011〕
- [X] T005 在 `donkey/core/exceptions.py` 新增 `class BuiltinToolGenerationError(WorkspaceInitError)`：docstring MUST 标注退出码 `4`、MUST **引用** `contracts/exit-codes.md` §3 的两类成因表（**MUST NOT 复述**该表 —— 避免第 2 份副本）、MUST NOT 自行返回退出码 / 打印 / 退出进程（宪法 N-05）；同时新增模块级常量 `_NEXT_STEP_BUILTIN = "下一步：请重装 donkey，或检查目标目录的写权限后重试 init。"` —— **MUST 落本模块**，`MUST NOT` 落 `core/workspace/init.py`（否则 `manifest.py → init.py → manifest.py` 循环 import —— F001-P2 的 R-12 教训）　〔覆盖 spec FR-070 / FR-071 / FR-072 / FR-075 · SC-011 / SC-016〕
- [X] T006 在 `donkey/cli/cli_client.py` 的 `_EXCEPTION_TO_EXIT_CODE` 映射表**追加一行** `BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION`（MUST 引用 `exit_codes.py` 的常量，MUST NOT 内联字面量 `4`）；**MUST NOT** 新增任何分支逻辑、**MUST NOT** 引入任何智能体框架的导入（宪法 N-04）、**MUST NOT** 改动任何其它客户端行为（不新增输出 / 不改摘要 / 不改 `--help` 文案 —— spec FR-088）　〔覆盖 spec FR-070 / FR-073 / FR-088 · SC-011〕
- [X] T007 在 `tests/unit/test_builtin_tools.py` 建立**共享夹具**（research.md R-02）：① `render_workspace(tmp_path)` —— 调用 `donkey.core.api.init_workspace` 把工作区渲染到临时目录；② `import_tool_module(workspace, name)` —— 把**工作区根**加入 `sys.path` 后用 `importlib.import_module(f"tools.{name}")` 导入；③ teardown MUST 从 `sys.modules` 摘除 `tools` / `tools.filesystem` / `tools.commandline` / `tools.webfetch` / `tools.changes`，**且 MUST 一并摘除"顶层模块形态"的 4 个键**（`filesystem` / `changes` / `commandline` / `webfetch` —— T023 会引入它们；否则后续用例会拿到上一个工作区的产物 → 验收假绿）；④ `assert_compiles(path)` 辅助 —— 每个渲染出的 `.py` MUST `compile()` 成功（模板正文是 `.txt`，**零静态检查覆盖** —— research.md R-08）　〔覆盖 spec FR-059 / FR-062〕
- [X] T105 [US9] 在 `tests/unit/test_builtin_tools.py` 写**退出码 4 的映射与错误信息**断言（本 Phase 的头号交付物此前**零测试触发**）：① **映射** —— `_EXCEPTION_TO_EXIT_CODE[BuiltinToolGenerationError]` MUST 恰为 `EXIT_CODE_BUILTIN_TOOL_GENERATION`（= `4`），且退出码 `4` MUST **未被**其它异常类型复用（与 `1` / `2` / `3` 语义独立，spec FR-071 / FR-073 / SC-011）；② **端到端触发** —— 以打桩渲染入口（`donkey.core.workspace.init.render_templates`）抛出 `BuiltinToolGenerationError` 的方式构造一次"内置工具生成失败"，经 `donkey.cli.cli_client.main(["init", <path>])` 触发，断言返回码恰为 `4`；③ **错误信息口径** —— 该次的标准错误输出 MUST 含**可识别的错误标识**与**一条**用户可执行的下一步（"重装 donkey" / "检查权限" / "重试 init" 三者之一），MUST NOT 只抛裸异常而不给下一步（spec FR-075 / SC-016）　〔覆盖 spec FR-071 / FR-073 / FR-075 · SC-011 / SC-016〕

**Checkpoint**: 本 Phase 2 的 3 处改动就位（核心层 2 处 + 客户端映射 1 行）+ 夹具可用 —— 用户故事实现可开始

---

## Phase 3: User Story 1 - 一次 init 得到可用的内置工具与契约库 (Priority: P1) 🎯 MVP

**Goal**: `donkey init` 之后，工作区的 `tools/` 下齐备 6 个文件（3 个内置 `@tool` 模块 + 契约库 + 包初始化 + 规范文档），清单条目从 46 增至 **54**，磁盘落地 **49** 个文件 / **10** 个目录

**Independent Test**: 对一个新路径执行 `donkey init`，断言退出码 `0`、`tools/` 下 6 个文件齐备、清单 54 条 / 文件型 48 条、命令输出含 `templates=54 created=48 skipped=0`

### Implementation for User Story 1

- [X] T008 [US1] 创建 `donkey/core/workspace/templates/tools/changes.py.txt` —— **变更记录契约库**（contracts/change-record-contract.md + contracts/tool-contracts.md §5）：3 个冻结常量 `CHANGE_RECORD_VERSION = 1` / `MAX_DIFF_BYTES = 64 * 1024` / `MAX_PREVIOUS_BYTES = 256 * 1024`；异常类 `FileChangedError(RuntimeError)`；9 个公开函数 `workspace_root()` / `resolve_path(path)` / `relative_path(path)` / `sha256_bytes(data)` / `read_existing_bytes(path)` / `atomic_write_bytes(path, data)` / `build_unified_diff(old_text, new_text, rel)` / `build_change_record(action, path, previous_bytes, new_bytes, *, src=None, include_previous=False)` / `check_expected_hash(path, expected_hash)`。**硬约束**：**0 个 `@tool`**、**零框架导入**（纯标准库）、**无 `__main__`** 块、`workspace_root()` 恒为 `Path(__file__).resolve().parent.parent` 且 **MUST NOT 读任何环境变量**（spec FR-002 / FR-104）、指纹与体积 MUST 按**原始字节**计算（MUST NOT 先解码再编码，spec FR-006）、原子写 MUST **同目录** `tempfile.mkstemp` → `flush` + `os.fsync` → `os.replace` 且任何异常路径 MUST 清临时文件（research.md R-06）、行切分 MUST 用 `split("\n")`（**MUST NOT** `splitlines()` —— research.md R-05）、差异头 MUST 用 `a/<rel_path>` / `b/<rel_path>` MUST NOT 含任何**可观测性后端**相关字样、MUST NOT 含**子智能体**相关目录或字段（spec FR-076 / FR-079）；　〔覆盖 spec FR-001 / FR-002 / FR-003 / FR-005 / FR-006 / FR-007 / FR-008 / FR-009 / FR-010 / FR-011 / FR-012 / FR-084 / FR-091 · SC-007〕
- [X] T009 [US1] 创建 `donkey/core/workspace/templates/tools/__init__.py.txt` —— **仅 docstring** 的包初始化：MUST 说明该包由初始化阶段自动生成、3 个内置工具模块位于此、**契约库位于此且不含任何工具函数**、用户可自行追加工具模块；**MUST NOT** 定义任何工具函数（spec FR-043） MUST NOT 含任何**可观测性后端**相关字样、MUST NOT 含**子智能体**相关目录或字段（spec FR-076 / FR-079）；　〔覆盖 spec FR-043〕
- [X] T010 [US1] 创建 `donkey/core/workspace/templates/tools/filesystem.py.txt` —— **7 个 `@tool`**（contracts/tool-contracts.md §2）：`read_file(path, start_line=1, num_lines=None)` / `write_file(path, content, dry_run=False, include_previous=False, expected_hash=None)` / `copy_file(src, dst, dry_run=False, expected_hash=None)` / `move_file(src, dst, dry_run=False, expected_hash=None)` / `delete_file(path, include_previous=False, dry_run=False, expected_hash=None)` / `list_dir(path, include_hidden=True, offset=0, limit=None)` / `stat(path, with_hash=False)`。**硬约束**：每个函数 MUST 有完整 docstring 且 `Args:` 段写清**每个新增可选参数**的语义与默认值（spec FR-023）；`from .changes import ...` MUST 带 `except ImportError` 回退到绝对导入 `from changes import ...`（spec FR-026 —— 回退路径需要 **`tools/` 目录**在 `sys.path` 上，不是工作区根，research.md R-02）；读取 MUST 走**统一分页路径**（起始行缺省 1、行数上限 **2000**、字节上限 **50 KiB**、单行上限 **2000** 字符并附 `... (line truncated to 2000 chars)`），返回**呈现文本**（首行 `Read file {路径}, lines {起}-{止}` + 每行 `<行号>: ` 前缀 + 截断时附 `[Output truncated. Continue reading with offset: N]`），二进制（含 NUL 字节）与图片 / PDF MUST 明确报错，目录 MUST 走目录分支（首行 `Read directory {路径}, entries {起}-{止}`）；MUST **不**含 `glob_search` / `grep_search`（spec FR-025） MUST NOT 含任何**可观测性后端**相关字样、MUST NOT 含**子智能体**相关目录或字段（spec FR-076 / FR-079）；　〔覆盖 spec FR-013 / FR-014 / FR-015 / FR-016 / FR-017 / FR-018 / FR-019 / FR-020 / FR-021 / FR-022 / FR-023 / FR-024 / FR-025 / FR-026 / FR-027 / FR-082 / FR-092 / FR-093 / FR-094 / FR-095 / FR-096 / FR-097 / FR-098 · SC-006 / SC-013 / SC-014 / SC-022〕
- [X] T011 [US1] 创建 `donkey/core/workspace/templates/tools/commandline.py.txt` —— **1 个 `@tool`** `run_shell(command: str, timeout: int = 60, cwd: str | None = None)`（contracts/tool-contracts.md §3）：MUST 每次新建进程（`subprocess.run(shlex.split(command), shell=False, timeout=...)`）、MUST NOT 交给命令解释器、工作目录 MUST 默认**工作区根**、超时 MUST 以**返回 JSON**（`timed_out=true` + `returncode=-1`）表达而**不抛异常**（spec FR-031）、返回值 MUST 含 `stdout` / `stderr` / `returncode` / `timed_out` / `cwd` / `argv` + **新增** `truncated`、输出超限 MUST 截断并附 `[showing lines 1-{已保留} of {总数}; full output not saved]`、**完整输出 MUST NOT 落盘**（spec FR-100 / FR-101）、docstring MUST 写明已知缺口"命令造成的文件副作用不进变更记录"（spec FR-035） MUST NOT 含任何**可观测性后端**相关字样、MUST NOT 含**子智能体**相关目录或字段（spec FR-076 / FR-079）；　〔覆盖 spec FR-028 / FR-029 / FR-030 / FR-031 / FR-032 / FR-033 / FR-034 / FR-035 / FR-036 / FR-083 / FR-099 / FR-100 / FR-101 / FR-102 / FR-103 · SC-023〕
- [X] T012 [US1] 创建 `donkey/core/workspace/templates/tools/webfetch.py.txt` —— **1 个 `@tool`** `fetch_url(url: str, method: str = "GET", headers: dict[str, str] | None = None, timeout: int = 30)`（contracts/tool-contracts.md §4）：MUST 用 **流式**读取（`httpx.Client(trust_env=False, follow_redirects=True, timeout=...)` + `client.stream(...)` —— `httpx.request()` 无法"读取中守上限"，research.md R-03）；**客户端 MUST 以 `trust_env=False` 构造** —— httpx 的 `trust_env` 默认为 `True`，会隐式读取 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `.netrc` 来决定请求走向，违反 spec FR-104「工具 MUST 不读任何环境变量」，且与 FR-089 的"MUST NOT 实现…代理"相悖（research.md R-19）；四道边界 MUST 全部实现 —— 协议白名单（仅 http/https）、响应体上限 **5 MiB**（先看 `Content-Length` 再在读取过程中守住）、非文本 MIME 拒绝、非 2xx 报错，且四项 MUST 各自在对应输入下**报错**（MUST NOT 放行 —— spec SC-021(a)）；**"地址范围"限制 MUST NOT 被实现** —— MUST NOT 存在任何地址黑名单 / 白名单 / 代理 / 沙箱（spec FR-089 / SC-021(a)）；**docstring MUST 逐条写明**四道边界及其触发后果 —— 协议白名单（http / https）/ 响应体上限（5 MiB）/ 非文本 MIME 拒绝 / 非 2xx 报错，MUST NOT 保留任何与实际行为不符的措辞（spec FR-090 / SC-021(b)）；`timeout > 120` MUST 在发请求前报错；返回 JSON MUST 恰含 `status_code` / `body` / `headers` / `url` 四字段且 **MUST NOT** 含变更记录字段；**MUST NOT** 做 HTML → Markdown 转换 MUST NOT 含任何**可观测性后端**相关字样、MUST NOT 含**子智能体**相关目录或字段（spec FR-076 / FR-079）；　〔覆盖 spec FR-037 / FR-038 / FR-039 / FR-040 / FR-041 / FR-042 / FR-089 / FR-090 · SC-021〕
- [X] T013 [US1] 创建 `donkey/core/workspace/templates/tools/README.md.txt` —— **覆盖** P2 的占位正文（spec FR-056）：MUST 覆盖 8 项（工具装饰器的官方导入位置 / 函数必须有 docstring / 路径白名单由用户自管 / 推荐的超时配置（命令 60 秒 · 网络 30 秒）/ 错误处理建议 / **工作区根的推导方式**（恒为"存放 `tools/` 的那个目录"，不读环境变量）/ **契约库与用户自写工具是一套的**（强制重置不覆盖契约库，重置前先备份）/ **网络工具需自行安装 HTTP 客户端库**），MUST 含"改文件的工具怎么写（变更记录契约）"小节（6 条：必须用原子写 / 写前取旧字节写后生成 change 记录 / schema 只增不改按版本分派 / **MUST** 提供期望指纹乐观锁 + **建议**提供预览开关 / 落盘后把 applied 置真 / 不要自己造指纹差异逻辑），并 MUST 明确声明契约库**是契约库、不是工具**　〔覆盖 spec FR-044 / FR-045 / FR-046〕
- [X] T014 [US1] 在 `donkey/core/workspace/templates/manifest.json` 的 `entries` 数组**末尾追加 8 条**（**MUST NOT** 修改 P2 已有的 46 条的路径与格式值）：`tools/__init__.py` / `tools/changes.py` / `tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py`（格式均为 `python`）+ `skills/example/reference/example.md`（`markdown`）+ `skills/example/scripts/example.py`（`python`）+ `skills/example/templates/example.md`（`markdown`）；追加后 MUST 核对总数为 **54** = 45 个文本型 + 3 个 sqlite3 型 + 6 个目录型　〔覆盖 spec FR-052 / FR-053 / FR-054 / FR-055 · SC-003〕
- [X] T015 [P] [US1] 创建 `donkey/core/workspace/templates/skills/example/reference/example.md.txt` —— Level 3 参考文档示例（spec FR-049）：MUST 说明"模型不会主动加载本文件"，并给出模型读取它的**工作区根相对**路径　〔覆盖 spec FR-049〕
- [X] T016 [P] [US1] 创建 `donkey/core/workspace/templates/skills/example/scripts/example.py.txt` —— Level 3 脚本示例：**MUST 保留** `if __name__ == "__main__": sys.exit(main())` 入口块（与源提示词模板逐字一致）；**授权来源 = 宪法 §6.3 例外 E-02 + §5 章 [D-19]**（N-01 的边界澄清："Python 入口文件"指**智能体入口**）—— spec FR-050 MUST **引用**该例外，本任务 MUST NOT 自设任何宪法例外；内容 MUST 仅演示"打印一行输出"；MUST NOT 位于 `tools/` 目录下；MUST NOT 命名为 `agent.py` / `main.py`；MUST NOT 承担"创建智能体"职责（正文 MUST NOT 引用 / 调用智能体创建入口 —— 智能体的唯一官方入口仍是 `donkey.core.api.create_agent`）　〔覆盖 spec FR-049 / FR-050〕
- [X] T017 [P] [US1] 创建 `donkey/core/workspace/templates/skills/example/templates/example.md.txt` —— Level 3 模板文件示例：**示例占位 MUST NOT 使用 `{{ … }}` 记法**（spec FR-049 的占位记法约束）—— 渲染器只替换 `{{ workspace_name }}`（见 `donkey/core/workspace/init.py` 的 `_substitute_placeholders`），其余 `{{ … }}` 会**原样保留**并出现在渲染产物中，直接破坏 F001-P2 契约 B12「渲染后无占位符残留」这条**持久不变量**（该不变量由 P2 的 `tests/unit/test_template_skeleton.py:753` / `:778` / `:982` 与 `tests/e2e/phase/verify_phase_f001_p2.py:395` 断言 —— MUST NOT 被削弱，spec FR-069）；MUST 改用 `<<title>>` / `<title>` 之类**非 `{{ }}`** 记法，并在文件内注明其为示例占位（例："以下为示例占位，实际使用时请替换"）　〔覆盖 spec FR-049 / FR-056 / FR-069〕
- [X] T018 [P] [US1] **覆盖** `donkey/core/workspace/templates/skills/example/SKILL.md.txt` 的 Level 2 正文（spec FR-056，**不新增清单条目**）：frontmatter MUST 保持恰含 `name` + `description` 两字段（宪法 D-07）；正文 MUST 讲清三层模型 + 给出"如何按需使用第三层"的具体指引，且指引中的**示例路径 MUST 以工作区根为基准**（与命令工具的工作目录基准一致，spec FR-048 —— 否则模型照抄会跑不通），并 MUST 说明"改本 Skill 请保留头部元信息"与"其它字段不被解析"（spec FR-051）　〔覆盖 spec FR-047 / FR-048 / FR-051 / FR-056 · SC-018〕
- [X] T019 [US1] 在 `tests/unit/test_builtin_tools.py` 写资产齐备断言：清单条数 == **54**、文件型条目 == **48**、**渲染后落地文件数 == 49**（**48 个清单文件型条目 + 1 份工作区清单** —— spec FR-068(a) 要求保留的**绝对值四项**为 54 / 48 / **49** / 10，此处补齐第三项）、45 个文本型条目的 `<条目路径>.txt` **全部存在**（缺一个 → 安装后 init 报 exit 3）、渲染后 `tools/` 下 6 个文件齐备、**渲染后磁盘目录数 == 10**（根 + 6 个清单目录 + 3 个 Skill Level 3 子目录 —— spec SC-003 的目录口径）、`changes.py` 与 `__init__.py` 各含 **0** 个 `@tool`、6 个 `.py` 全部 `compile()` 成功、渲染产物 MUST NOT 含**子智能体相关目录 / 字段名**（spec FR-076 的第二子句）、渲染产物 MUST NOT 含 `langsmith` / `os.environ` / `getenv` 字样（spec FR-079 / FR-104）、渲染出的 `tools/webfetch.py` MUST 含 **`trust_env=False`**（httpx 的 `trust_env` 默认值为 `True`，会隐式读取 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `.netrc` 来决定请求走向 —— 违反 spec FR-104「工具 MUST 不读任何环境变量」，且与 FR-089 的"MUST NOT 实现…代理"相悖；research.md R-03 / R-19）　〔覆盖 spec FR-057 / FR-076 / FR-077 / FR-079 / FR-104 · SC-003 / SC-006 / SC-008 / SC-012 / SC-014〕
- [X] T106 [US1] 在 `tests/unit/test_builtin_tools.py` 写**记忆库未被触碰**断言：在目标 workspace 内**预先放置**三个**哨兵内容**的记忆库文件（`memory/sessions.sqlite3` / `memory/store.sqlite3` / `memory/knowledge.sqlite3`），执行 `init_workspace` 后三者的**内容与 mtime MUST 完全不变**（证明本 Phase 未对记忆库做任何写入 / schema 构造 / 结构健康检查），且 MUST NOT 出现任何记忆库结构副作用（spec FR-085 / FR-081）　〔覆盖 spec FR-085〕
- [X] T020 [US1] 跑 US1 的独立验证（quickstart §2）：`rm -rf /tmp/p3ws && donkey init /tmp/p3ws` → 退出码 `0`、`ls -1 /tmp/p3ws/tools` 输出恰为 6 个文件、命令行摘要含 `templates=54 created=48 skipped=0`；再次 init MUST 输出 `templates=54 created=0 skipped=48`　〔覆盖 spec FR-087 · SC-003 / SC-004 / SC-019〕

**⚠️ 本 Phase 末尾先把 F001-P2 的既有套件恢复绿**（P2 的阶段边界断言在清单条目变更后必然失效 —— 详见「P2 套件的中间态」段）：

- [X] T094 在 `tests/unit/test_template_skeleton.py` 按 **文件 + 行号逐条**改写 F001-P2 中编码了**阶段边界**的断言（research.md R-16 / spec FR-068(a)(b)(c)(d)）—— **MUST NOT 以任何概括性计数（如"5 条 / 2 条"）为准**：**具体语句以 P2 测试文件的实际内容为准**，MUST NOT 遗漏任何一条会因本 Phase 交付而失效的断言。下表为**逐行核对后的完整清单**（行号以本仓库当前 `tests/unit/test_template_skeleton.py` 为准；实施前 MUST 复核 —— 行号随 P2 文件演进而漂移）：

  | # | 位置 | 所属用例 | P2 的原断言 | P3 的正确口径 |
  |---|---|---|---|---|
  | 1 | `:737` | `test_template_assets_render_to_expected_tree` | `assert result.templates_loaded == 46` | `== 54` |
  | 2 | `:738` | 同上 | `assert result.files_created == 40` | `== 48` |
  | 3 | `:744` | 同上 | `assert len(files) == 41` | `== 49`（48 个清单文件型条目 + 1 份工作区清单） |
  | 4 | `:746` | 同上 | `assert len(directories) + 1 == 7` | `== 10`（根 + 6 个清单目录 + 3 个 Skill Level 3 子目录） |
  | 5 | `:817` | `test_dir_readme_templates_content` | `assert "内置工具由后续阶段生成" in tools_doc` | 随 FR-056 的正文覆盖改写为"正文 MUST 含 P3 阶段写入的 **8 项**规范要点"（口径见 FR-044） |
  | 6 | `:1099-1100` | `test_no_builtin_tool_files_generated` | `assert not (workspace / "tools" / name).exists()` —— **4 条**（`filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py`，循环内） | MUST 改为"这 4 个文件**已存在**"（P3 起它们是清单内条目，否定断言必然失败） |
  | 7 | `:1104` | 同上 | `assert [p for p in workspace.rglob("*.py")] == []` | MUST 改为"**除本 Phase 新增的 6 个 `.py` 文件外**无其它 `.py` 文件"（`tools/` 下 5：3 工具 + 契约库 + 包初始化；Skill 第三层演示脚本 1） |
  | 8 | `:1252` | `test_exit_code_set_is_exactly_0_to_3` | `assert used == {0, 1, 2, 3}` | `== {0, 1, 2, 3, 4}` |
  | 9 | `:1261` | 同上 | `assert set(cli_client._EXCEPTION_TO_EXIT_CODE.values()) == {1, 2, 3}` | `== {1, 2, 3, 4}` |
  | 10 | `:1266` | 同上 | `assert exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION not in used` | MUST 改为"退出码 4 **已在**实际使用集合中"（P3 起 4 进入映射表） |
  | 11 | `:1130` | `test_init_does_not_validate_provider_content` | `assert result.templates_loaded == 46` | `== 54` |
  | 12 | `:1454` | `test_broken_memory_template_preserved_without_force` | `assert result.templates_loaded == 46` | `== 54` |

  > **注意**：`templates_loaded == 46` 在 P2 的单元测试中**出现于 3 个不同的用例函数**（上表第 1 / 11 / 12 行）→ MUST **全部**改写为 54，MUST NOT 只改第一处。

  **MUST 保留的持久不变量**（MUST NOT 削弱 —— spec FR-069）：① `:753` / `:778` / `:982` 的"渲染产物 MUST 无 `{{ … }}` 占位符残留"断言 → **MUST NOT 改写**（其成立由 FR-049 的占位记法约束保证，**不是**靠删断言兑现）；② `:1272` 的"运行期依赖恰为 1 个"断言 → **MUST 保持不变**；③ `test_no_builtin_tool_files_generated` 内的"工作区内无**智能体入口文件**"断言 → MUST **保留**（口径按 FR-050 引用的**宪法 §6.3 例外 E-02 + §5 章 [D-19]**：Skill 第三层演示脚本**获宪法授权**，**不计入**该不变量的违例 —— FR-050 已于 2026-10-23 定点改写为引用口径，MUST NOT 自设豁免）；④ `:1253` / `:1262` / `:1265` 三条断言在 P3 下**仍成立** → MUST NOT 改动。

  **MUST NOT**：改动上表未列出的任何断言 —— 尤其 `:705` / `:706` 的**动态口径**断言（`== len(entries)` / `== len(file_type_entries)`）与 `:509` / `:629` / `:1389` / `:1396` 的**自定义清单**断言，它们在 P3 下仍成立　〔覆盖 spec FR-068 / FR-069 · SC-002〕
- [X] T095 在 `tests/e2e/phase/verify_phase_f001_p2.py` 改写 P2 的**两个**场景（research.md R-15 / R-16）—— **MUST NOT 以任何概括性计数为准**；**具体语句以 P2 测试文件的实际内容为准**：

  | # | 位置 | 场景 | P2 的原断言 | P3 的正确口径 |
  |---|---|---|---|---|
  | 1 | `:249` | 场景 1 `test_scenario_1_new_workspace_full_tree` | `assert "templates=46 created=40 skipped=0" in completed.stdout` | `templates=54 created=48 skipped=0` |
  | 2 | `:272` | 同上 | `assert len(files) == 41` | `== 49`（48 个清单文件型条目 + 1 份工作区清单） |
  | 3 | `:273` | 同上 | `assert len(directories) + 1 == 7` | `== 10`（根 + 6 个清单目录 + 3 个 Skill Level 3 子目录） |
  | 4 | `:515-516` | 场景 11 `test_scenario_11_no_builtin_tools_yet` | `assert not (ws / "tools" / name).exists()` —— **4 条**（`filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py`，循环内） | MUST 改为"这 4 个文件**已存在**"；场景名与 docstring MUST 一并更新为 P3 口径；`tools/README.md` 仍在（`:517` 不变） |

  **MUST NOT 改写**：P2 **场景 5** `test_scenario_5_name_injection` 的"渲染产物 MUST NOT 残留 `{{ … }}` 占位符"断言（`:393-395`）→ **MUST 保持原样** —— 其成立由 spec FR-049 的**占位记法约束**保证（spec FR-068(e)），MUST NOT 靠删断言兑现（spec FR-069 的持久不变量）。

  **MUST NOT**：删除这两个场景，MUST NOT 让 P2 的其余 **12** 个场景（14 个场景减去已改写的场景 1 与场景 11）与全部持久不变量变红（spec FR-069）　〔覆盖 spec FR-068 / FR-069 · SC-002〕

**Checkpoint**: US1 可独立验证 —— `donkey init` 产出可用的内置工具与契约库（MVP）

---

## Phase 4: User Story 2 - 工具能被真的导入并用起来 (Priority: P2)

**Goal**: 9 个 `@tool` 在两种导入形态下都能被真正导入，且每个都有完整说明文字

**Independent Test**: 在独立子进程中导入 9 个工具函数并读取各自 docstring 长度；断言每个长度 > 20。**口径**：独立**子进程**版本由 e2e 场景 2（T079）承载 —— 本阶段的任务是**进程内**单元测试

### Tests for User Story 2 (TDD) ⚠️

- [X] T021 [P] [US2] 在 `tests/unit/test_builtin_tools.py` 写 docstring 断言：9 个 `@tool` 的 `description` 长度 MUST > 20、函数名即工具名、`args` schema MUST 含各自的全部参数且新参数的默认值与 spec 一致（如 `start_line` 默认 1、`num_lines` 默认 `None`、`dry_run` 默认 `False`、`include_hidden` 默认 `True`、`offset` 默认 `0`）　〔覆盖 spec FR-014 / FR-023〕
- [X] T022 [P] [US2] 在 `tests/unit/test_builtin_tools.py` 写**相对导入形态**断言：把工作区根加入 `sys.path` 后 `importlib.import_module("tools.filesystem")` MUST 成功、`tools.changes` 的 9 个公开函数 MUST 全部可取到　〔覆盖 spec FR-026〕
- [X] T023 [P] [US2] 在 `tests/unit/test_builtin_tools.py` 写**顶层模块形态**断言：把 **`tools/` 目录**（不是工作区根 —— research.md R-02 实测）加入 `sys.path` 后 `importlib.import_module("filesystem")` MUST 成功（走 `except ImportError` 回退到绝对导入）　〔覆盖 US2 · spec FR-026〕
- [X] T024 [P] [US2] 在 `tests/unit/test_builtin_tools.py` 写工具计数断言：`tools.filesystem` 恰 7 个 `@tool`、`tools.commandline` 恰 1 个、`tools.webfetch` 恰 1 个、`tools.changes` 与 `tools.__init__` 恰 **0** 个；**并须断言契约库可被导入而无框架导入**（`tools.changes` 的 `sys.modules` 中 MUST NOT 出现任何框架模块 —— spec FR-011 / FR-091：未来的工具扫描器 MUST 容忍"无 `@tool` 的辅助模块"，该兼容性依赖契约库的零框架身份）　〔覆盖 spec FR-091〕

**Checkpoint**: US1 与 US2 均可独立验证

---

## Phase 5: User Story 3 - 命令工具能在新进程里跑并回报结果 (Priority: P3)

**Goal**: `run_shell` 每次新建进程执行命令，如实回报输出 / 退出码 / 超时，并在输出超限时截断

**Independent Test**: 在独立子进程中执行回显命令，解析返回 JSON 并断言 `stdout` 含回显内容、`returncode == 0`、`timed_out is False`。**口径**：独立**子进程**版本由 e2e 场景 3（T080）承载 —— 本阶段的任务是**进程内**单元测试

### Tests for User Story 3 (TDD) ⚠️

- [X] T025 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写 `run_shell("echo hello")` 断言：返回值 MUST 是可被标准 JSON 解析的**字符串**，解析后 `stdout` 含 `"hello\n"`、`returncode == 0`、`timed_out is False`、`stderr == ""`、`argv == ["echo", "hello"]`、`cwd` 等于**工作区根**（非进程 cwd）　〔覆盖 spec FR-022 / FR-032 / FR-033〕
- [X] T026 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写超时断言：`run_shell("sleep 5", timeout=1)` MUST 返回可解析的 JSON 且 `timed_out is True`、`returncode == -1`，且 **MUST NOT 抛异常**（spec FR-031 的"返回标记而非抛出"口径 —— 与网络工具的异常透传构成**有意的不对称**，spec FR-041）　〔覆盖 spec FR-031〕
- [X] T027 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写工作目录断言：传相对 `cwd` 时 MUST 以工作区根为基准解析；MUST NOT 依赖进程当前目录　〔覆盖 US3 · spec FR-032〕
- [X] T028 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写**输出截断**断言：构造超限输出（> 2000 行或 > 50 KiB）→ 返回结果 `truncated` MUST 为 `true`、末尾 MUST 含 `[showing lines 1-{已保留} of {总数}; full output not saved]`、**工作区内 MUST NOT 新增任何文件**（完整输出不落盘，spec FR-101）　〔覆盖 spec FR-099 / FR-100 / FR-101 / FR-103 · SC-023〕
- [X] T029 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写**上限常量一致性**断言：`tools.filesystem` 与 `tools.commandline` 两侧的行数上限（2000）与字节上限（50 KiB）MUST 相等（spec FR-099 / FR-103 —— 防将来漂移）　〔覆盖 spec FR-099 / FR-103〕
- [X] T104 [P] [US3] 在 `tests/unit/test_builtin_tools.py` 写**命令工具 `timeout` 无上限**断言：`run_shell("echo x", timeout=999)` MUST **不报错**、MUST 正常返回可解析的 JSON（`returncode == 0`、`timed_out is False`、`stdout` 含 `x`）—— 命令工具的 `timeout` **不设上限**，MUST NOT 被实现成任何隐式上限（spec FR-028）；这与网络工具 `fetch_url` 的 **120 秒**上限（spec FR-037，超限 MUST 报错）构成**有意的不对称**：命令工具的超时值由调用方按场景自定。**注**：本类别已由 2026-10-23 的 spec 定点修订**正式登记**进 FR-058 的类别表（**第 23 类**）与 SC-008 的"23 个类别"门槛 —— 本任务 MUST NOT 反过来改写 FR-058 的类别表或 SC-008 的门槛（见 T102）　〔覆盖 spec FR-028 / FR-037〕

**Checkpoint**: US1 ~ US3 均可独立验证

---

## Phase 6: User Story 4 - 文件工具的七个动作都能用且不破坏旧用法 (Priority: P4)

**Goal**: 文件工具的读 / 写 / 复制 / 移动 / 删除 / 列目录 / 看属性七个动作全部可用，且新增参数全部可选、旧调用方式行为不变

**Independent Test**: 在独立子进程中完成"写 → 读 → 复制 → 列目录 → 看属性 → 删除"的连续操作并断言每步结果。**口径**：独立**子进程**版本由 e2e 场景 4（T081）承载 —— 本阶段的任务是**进程内**单元测试

### Tests for User Story 4 (TDD) ⚠️

- [X] T030 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写"写后读"断言：`write_file` 后 `read_file` 的返回 MUST 包含写入内容，**去掉呈现文本的包装后逐字一致**（呈现文本的包装 = 页范围头 + 行号前缀 —— 定义见 data-model.md §10 术语表「呈现文本」；spec 澄清第一轮 Q4 的连带修订）　〔覆盖 spec FR-015 / FR-094 · SC-022〕
- [X] T031 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写"复制-移动-删除"三件套断言：复制后目标存在且内容一致、移动后源消失且目标内容一致、删除后文件不存在、目录删除按目录粒度　〔覆盖 US4 · spec FR-017 / FR-021〕
- [X] T032 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写 `list_dir` 断言：返回**名称列表**（`list[str]`，MUST NOT 是 JSON 文本）、`include_hidden=False` 过滤点开头项、**默认值为 `True`**（旧行为）、`offset` 为 **0 基**跳过、`limit` 上限 **2000**、排序为**名称代码点序**（research.md R-13 —— MUST NOT 是目录优先 + 本地化序）　〔覆盖 spec FR-015 / FR-097〕
- [X] T033 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写 `stat` 断言：返回**映射**（MUST NOT 是 JSON 文本），含 `size` / `mtime` / `is_file` / `is_dir` / `exists`；`with_hash=True` 时追加 `sha256` 且值形如 `sha256:<hex>`（与契约库同格式，带前缀）；路径不存在时返回 `exists: False` 的映射而**不抛异常**　〔覆盖 spec FR-015〕
- [X] T034 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写**呈现格式**断言：首行 MUST 形如 `Read file {路径}, lines 1-{末行}`、每行 MUST 带 `<行号>: ` 前缀、空文件 MUST 为 `Read file {路径}, 0 lines`、单行 > 2000 字符 MUST 被截断并附 `... (line truncated to 2000 chars)`；**并须断言"小文件走整份返回"**：一个体积 ≤ 50 KiB **且 行数 ≤ 2000** **且 未指定**起始行 / 行数的文件 MUST 返回**全部**行、MUST NOT 出现续读提示（FR-095 —— 否则"整份 vs 分页"的分支无任何用例覆盖；**FR-095 的"行数 ≤ 2000"是独立于体积的第二个条件，缺它则 spec 新增的区分用例无处落点**）　〔覆盖 spec FR-094 / FR-095 · SC-022〕
- [X] T035 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写**读取侧双上限**断言：① 行数 > 2000 的文件 MUST 被截断并附 `[Output truncated. Continue reading with offset: N]`；② 体积 > 50 KiB 的文件同样被截断；③ **双上限"先到者生效"的区分断言（spec FR-092 / FR-095 / FR-098(d) / SC-022）** —— MUST 构造一个**体积 ≤ 50 KiB 但行数 > 2000** 的文件（短行、够多），其返回值 MUST **仍被截断**并给出续读指针，MUST NOT 因"体积小"而整份返回超限行数（**行数上限无条件生效** —— FR-098(d) 的偏离登记）；④ 起始行越界 MUST **报错**；⑤ 二进制文件（含 NUL 字节）MUST **报错**且 MUST NOT 返回乱码；⑥ 图片 / PDF MUST **报错**　〔覆盖 spec FR-092 / FR-093 / FR-095 / FR-096 / FR-098 · SC-022〕
- [X] T108 [P] [US4] 在 `tests/unit/test_builtin_tools.py` 写**读取侧分页边界**断言（补齐 spec Edge Cases 中三条此前无用例落点的边界）：① `read_file` 读**目录** MUST 按目录分支呈现（首行 `Read directory {路径}, entries {起始}-{结束}`，条目超上限时附续读提示），MUST NOT 报"是目录"类错误；② `read_file(num_lines=9999)` MUST **截到 2000 行**且 MUST **NOT 报错**；③ `list_dir(limit=9999)` MUST **截到 2000 个条目**且 MUST **NOT 报错**（spec FR-092 / FR-096 / FR-097 / Edge Cases「读取一个目录」「请求的行数超过 2000」「列目录的条目超过 2000」）　〔覆盖 spec FR-092 / FR-096 / FR-097 · SC-022〕

**Checkpoint**: US1 ~ US4 均可独立验证

---

## Phase 7: User Story 5 - 网络工具能拉取网页 (Priority: P5)

**Goal**: `fetch_url` 能按方法发请求、带自定义请求头、有超时保护，并按 OpenCode 的四道边界拒绝非法请求

**Independent Test**: 在带网络拦截的进程内请求一个地址并断言状态码与正文。**口径**：独立**子进程**版本由 e2e 场景 5（T082）承载 —— 本阶段的任务是**进程内**单元测试（网络拦截只对当前进程生效，spec FR-067 / research.md R-20）

### Tests for User Story 5 (TDD) ⚠️

- [X] T036 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写成功路径断言（用 `pytest-httpx` 的 `httpx_mock` fixture）：`httpx_mock.add_response(url="https://example.com", method="GET", status_code=200, text="mocked body")` → 返回值 MUST 是可解析的 JSON，`status_code == 200`、`body` 含 `"mocked body"`、含 `headers` 与 `url` 四字段且**无变更记录字段**　〔覆盖 spec FR-039 / FR-040 · SC-021〕
- [X] T037 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写超时断言：`httpx_mock.add_exception(httpx.ReadTimeout("too slow"), url="https://slow.example")` → MUST **抛出** `httpx.TimeoutException`（异常透传，spec FR-041 —— 与命令工具的"返回标记"有意不对称）　〔覆盖 US5 · spec FR-041〕
- [X] T038 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**协议白名单**断言：`ftp://` 与 `file://` MUST **报错**且 MUST NOT 发起请求（spec FR-089(a)）　〔覆盖 US5 · spec FR-089(a)〕
- [X] T039 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**非文本 MIME 拒绝**断言：非文本 MIME（含 `image/png`）MUST **报错**、MUST NOT 放行（spec FR-089(c) / SC-021(a)）　〔覆盖 US5 · spec FR-089(c)〕
- [X] T040 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**非 2xx**断言：状态码 500 MUST **报错**且 MUST NOT 返回正文（spec FR-089(d)）　〔覆盖 US5 · spec FR-089(d)〕
- [X] T041 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**5 MiB 上限**断言：用 `httpx_mock.add_response(content=iter([b"x" * 65536] * 200))` 制造**无 `Content-Length` 的流式响应** → MUST 在**读取过程中**报错（spec FR-089(b) —— 这正是 MUST 用流式而非 `httpx.request()` 的原因，research.md R-03）　〔覆盖 US5 · spec FR-089(b)〕
- [X] T042 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**超时上限**断言：`timeout=999` MUST 在发请求前**报错**（上限 120 秒，spec FR-037）　〔覆盖 spec FR-037〕
- [X] T107 [P] [US5] 在 `tests/unit/test_builtin_tools.py` 写**网络工具边界陈述**断言（spec SC-021 的两类可判定判据）：① **静态层** —— 渲染产物的 `fetch_url` docstring MUST **逐条出现**四项边界的措辞 —— "http" 与 "https"（协议白名单）/ "5 MiB"（响应体上限）/ "MIME" 或 "文本"（非文本拒绝）/ "2xx"（非 2xx 报错），四项各 **≥ 1** 次（spec FR-090 / SC-021(b)）；② **行为层 · 无地址范围限制** —— 对**回环地址**（如 `http://127.0.0.1:8000/x`）的请求 MUST **被放行**并正常返回（用 `httpx_mock` 拦截），MUST NOT 被任何"地址黑名单 / 白名单 / 代理 / 沙箱"式过滤器拒绝（spec FR-089 / SC-021(a)）；③ **隐式环境变量** —— 渲染产物的 `tools/webfetch.py` MUST 含 `trust_env=False`（httpx 的 `trust_env` 默认 `True` 会隐式读取代理 / 证书环境变量，违反 spec FR-104；research.md R-03 / R-19）。**行为层的另一半（四道边界各自报错）由 T038 / T039 / T040 / T041 承载** —— SC-021(a) 的两项 MUST **方向相反**（四道边界 MUST 报错 / 地址范围 MUST NOT 被拦），MUST 同时命中，缺一即为判据未达成　〔覆盖 spec FR-089 / FR-090 / FR-104 · SC-021〕

**Checkpoint**: US1 ~ US5 均可独立验证

---

## Phase 8: User Story 6 - 示例 Skill 的三层结构齐备 (Priority: P6)

**Goal**: 示例 Skill 的第一层头部元信息合规、第二层正文讲清三层模型、第三层三个子目录各有一个资源

**Independent Test**: 对新路径执行 `donkey init`，检查示例 Skill 的头部元信息块、正文非空、第三层子目录中至少有一个文件

### Tests for User Story 6 (TDD) ⚠️

- [X] T043 [P] [US6] 在 `tests/unit/test_builtin_tools.py` 写 frontmatter 断言：文件 MUST 以 `---\n` 开头、`name` 与 `description` **恰两字段**（宪法 D-07 —— MUST NOT 含 `when_to_use` / `version` / `tags` 等自定义字段）　〔覆盖 spec FR-047〕
- [X] T044 [P] [US6] 在 `tests/unit/test_builtin_tools.py` 写三层结构断言：Level 2 正文 MUST 非空且含"Level 2"字样、Level 3 的 `reference/` / `scripts/` / `templates/` 三个子目录 MUST 各含 ≥ 1 个文件、三个子目录 MUST **不**作为清单条目新增（清单仍为 54 条）　〔覆盖 spec FR-049 · SC-018〕
- [X] T045 [P] [US6] 在 `tests/unit/test_builtin_tools.py` 写**路径基准**断言：Level 2 正文中的示例路径 MUST 以**工作区根**为基准（如 `skills/example/scripts/example.py`），MUST NOT 是未说明基准的 Skill 目录相对路径（spec FR-048 —— 否则模型照抄会跑不通）　〔覆盖 US6 · spec FR-048〕
- [X] T046 [P] [US6] 在 `tests/unit/test_builtin_tools.py` 写**宪法 E-02 授权**断言（spec FR-050，**授权来源 = 宪法 §6.3 例外 E-02 + §5 章 [D-19]** —— 本清单 MUST NOT 自设宪法例外）：① `skills/example/scripts/example.py` MUST 含 `if __name__ == "__main__":` 入口块（与源提示词模板逐字一致）；② 工作区内 MUST NOT 出现 `agent.py` / `main.py` 这类**智能体入口文件**；③ 该脚本 MUST NOT 命名为 `agent.py` / `main.py`；④ 该脚本 MUST NOT 承担"创建智能体"职责（渲染产物 MUST NOT 引用 / 调用智能体创建入口）　〔覆盖 spec FR-050 / FR-068 · SC-014〕

**Checkpoint**: US1 ~ US6 均可独立验证

---

## Phase 9: User Story 7 - 找文件找内容不归内置工具管 (Priority: P7)

**Goal**: 3 个内置工具文件内**不含**"按文件名搜 / 按内容搜"两个能力（职责正交，属引擎侧检索中间件）

**Independent Test**: 对新路径执行 `donkey init`，逐个检查 3 个内置工具文件的正文，确认其中不含那两个能力的名字

### Tests for User Story 7 (TDD) ⚠️

- [X] T047 [P] [US7] 在 `tests/unit/test_builtin_tools.py` 写职责正交断言：`tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py` 三个渲染产物的正文 MUST **不**出现 `glob_search` 与 `grep_search`（宪法 §2.5 / §2.6，spec FR-025）　〔覆盖 spec FR-025 · SC-013〕

**Checkpoint**: US1 ~ US7 均可独立验证

---

## Phase 10: User Story 8 - 删掉内置工具后再 init 会补齐 (Priority: P8)

**Goal**: 清单内条目被用户删除后，再次 `donkey init` MUST 补齐

**Independent Test**: 对新路径执行 `donkey init`，删掉一个内置工具文件，再次执行 `donkey init`，断言该文件重新出现且退出码为 `0`

### Tests for User Story 8 (TDD) ⚠️

- [X] T048 [P] [US8] 在 `tests/unit/test_builtin_tools.py` 写补齐断言：删除 `tools/filesystem.py` 与一个 Level 3 文件后再次 `init_workspace`，两者 MUST 重新出现、退出码 `0`；**非强制**模式下用户改写过的其它文件内容与 mtime MUST 不变　〔覆盖 spec FR-087 · SC-004〕

**Checkpoint**: US1 ~ US8 均可独立验证

---

## Phase 11: User Story 9 - 强制重置不会误伤我自己的工具 (Priority: P9)

**Goal**: `--force` 恢复出厂状态时，**不覆盖**已存在的契约库、**不删除**清单外的用户自写工具；其余清单内条目 100% 恢复出厂

**Independent Test**: 对新路径执行 `donkey init`，新建一个清单外的自定义工具文件并改写契约库，执行带强制标志的 init，断言自定义文件仍在、契约库逐字节未变、其余条目已恢复出厂

### Implementation for User Story 9

- [X] T049 [US9] 在 `donkey/core/workspace/init.py` 的 `init_workspace_inner` **步骤 ④** 增加条目级强制重置豁免（research.md R-07 / contracts/cli-contract.md §3）：当 `force=True` **且**契约库路径已存在于 workspace 时，把该条目**从传给 `render_templates` 的条目列表中剔除**并将该条目计入 `files_skipped`（**MUST 过滤进一个新列表变量，MUST NOT 就地改写 `manifest_entries`** —— `templates_loaded` 取 `len(manifest_entries)`，就地过滤会变成 53，与 FR-069 的 54/47/1 冲突；实现口径见 contracts/cli-contract.md §3.1）；`render_templates` 本身 **MUST 一字不改**（P2 的通用通则 MUST 对其余条目原样成立 —— spec FR-069）；契约库**不存在**时 MUST 按出厂内容正常创建　〔覆盖 spec FR-069 / FR-070 / FR-087 / FR-105 · SC-024〕

### Tests for User Story 9 (TDD) ⚠️

- [X] T050 [P] [US9] 在 `tests/unit/test_builtin_tools.py` 写豁免断言：`--force` 后已存在的契约库内容 MUST **逐字节未变**、被覆盖的文件数 == 0（spec FR-105 / SC-024）　〔覆盖 spec FR-105 · SC-024〕
- [X] T051 [P] [US9] 在 `tests/unit/test_builtin_tools.py` 写"其余条目恢复出厂"断言：`--force` 后 3 个内置工具 + 包初始化 + Skills 三层 + `tools/README.md` MUST **100%** 恢复出厂内容（豁免 MUST NOT 削弱该通则，spec FR-069）　〔覆盖 spec FR-069〕
- [X] T052 [P] [US9] 在 `tests/unit/test_builtin_tools.py` 写计数断言：`--force` 且契约库已存在时 MUST 为 `templates=54 created=47 skipped=1`；全新创建 MUST 为 `54 / 48 / 0`；非强制二次 init MUST 为 `54 / 0 / 48`（contracts/cli-contract.md §3.2）　〔覆盖 spec FR-068 · SC-003〕
- [X] T053 [P] [US9] 在 `tests/unit/test_builtin_tools.py` 写"用户自写工具不被删"断言：`tools/my_custom_tool.py`（清单外）在 `--force` 后 MUST 仍在（spec FR-087 / FR-013）　〔覆盖 spec FR-087 · SC-005〕

**Checkpoint**: US1 ~ US9 均可独立验证

---

## Phase 12: User Story 10 - 生成出来的工具能被另一个进程真正用起来 (Priority: P10)

**Goal**: 工作区产物可被**独立进程**导入并调用（可移植性），且集成测试层首次启用

**Independent Test**: 对新路径执行 `donkey init`，在独立子进程中导入全部 9 个工具函数并断言它们全部可调用

### Implementation for User Story 10

- [X] T054 [US10] 创建 `tests/integration/test_init_to_load.py`：**MUST** 用**独立子进程**导入工作区产物（`subprocess.run([sys.executable, "-c", snippet], cwd=workspace)` —— MUST NOT 在测试进程内把工作区路径塞进 `sys.path` 后直接导入，模块按名缓存会导致后续场景测到**第一个**工作区的产物 → 验收假绿，spec FR-062）；子进程 MUST 用 `-c`（`-c` 才把 cwd 放进 `sys.path`，用脚本文件会因 `sys.path[0]` 是脚本目录而找不到 `tools` 包 —— research.md R-20）　〔覆盖 spec FR-060 / FR-061 / FR-062 / FR-063 · SC-009〕

### Tests for User Story 10 (TDD) ⚠️

- [X] T055 [P] [US10] 在 `tests/integration/test_init_to_load.py` 写导入文件工具断言：子进程内 `from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat` MUST 无异常　〔覆盖 spec FR-060〕
- [X] T056 [P] [US10] 在 `tests/integration/test_init_to_load.py` 写导入命令工具并调用断言：子进程内 `from tools.commandline import run_shell` + 调一次 `run_shell("echo integration")`，输出 MUST 含 `integration`　〔覆盖 US10 · spec FR-060〕
- [X] T057 [P] [US10] 在 `tests/integration/test_init_to_load.py` 写导入网络工具并调用断言：子进程内**先**打桩 `httpx.Client.send`（MUST NOT 依赖测试进程的 `httpx_mock` —— 它只对当前进程生效，spec FR-067 / research.md R-20），**再** `from tools.webfetch import fetch_url` 并调用一次　〔覆盖 US10 · spec FR-060 / FR-067〕
- [X] T058 [P] [US10] 在 `tests/integration/test_init_to_load.py` 写契约库断言：子进程内 `from tools.changes import CHANGE_RECORD_VERSION, atomic_write_bytes, build_change_record` MUST 成功且 `CHANGE_RECORD_VERSION == 1`；契约库与 `tools/filesystem.py` MUST **同批存在**（MUST NOT 出现"工具在、契约库不在"的半残工作区，spec FR-060）　〔覆盖 spec FR-055 / FR-060〕

**Checkpoint**: US1 ~ US10 均可独立验证；**集成测试层首次启用**（P2 的"留空"理由已失效，spec FR-061）

---

## Phase 13: User Story 11 - init 阶段不做配置检查 (Priority: P11)

**Goal**: 初始化阶段不替用户做配置内容的合法性判定（那属 F002 的 `donkey load`）

**Independent Test**: 对新路径执行 `donkey init`，断言退出码为 `0`，且过程中未触发任何配置类检查

### Tests for User Story 11 (TDD) ⚠️

- [X] T059 [P] [US11] 在 `tests/unit/test_builtin_tools.py` 写"不做配置检查"断言：把渲染出的某个内置工具文件改坏后再次 `init_workspace`，MUST 仍以成功状态结束（非强制模式下"已存在即跳过"）、MUST NOT 抛任何配置类异常（spec FR-081）　〔覆盖 spec FR-081〕

**Checkpoint**: US1 ~ US11 均可独立验证

---

## Phase 14: User Story 12 - 写文件会带回"改了什么" (Priority: P12)

**Goal**: 所有改文件的工具都返回统一的变更记录（原子写 + 旧内容指纹 + 统一差异 + 预览 + 乐观锁）

**Independent Test**: 在独立子进程中连续写同一文件两次，断言两次返回的变更记录（版本 / 动作 / 旧版本指纹 / 新版本指纹 / 差异文本）

### Tests for User Story 12 (TDD) ⚠️

- [X] T060 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写"创建"的变更记录断言：首次写入 MUST 返回 `action == "create"`、`applied is True`，`change.version == 1`、`change.previous_exists is False`、`change.previous_hash is None`（spec FR-004 已钉死：指纹"不存在时" MUST 为 `null` / Python 侧 `None`，**MUST NOT 用空串**）、`change.new_hash` 非空且形如 `sha256:<hex>`、`change.unified_diff` 含新增行（spec FR-012 / FR-016）　〔覆盖 spec FR-012 / FR-016〕
- [X] T061 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写"更新"的变更记录断言：第二次写入 MUST 返回 `action == "update"`、`change.previous_exists is True`、`change.previous_hash` == **上次写入后**的 `new_hash`、`change.unified_diff` 同时含被替换行与新增行　〔覆盖 US12 · spec FR-004 / FR-016〕
- [X] T062 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写**基线键集合**断言：`change` 的键集合 MUST **恰好**等于 12 个基线字段（`version` / `action` / `path` / `rel_path` / `previous_exists` / `previous_size` / `previous_hash` / `new_size` / `new_hash` / `unified_diff` / `diff_truncated` / `applied`）—— **任何动作下都必须全部存在**（spec FR-004）；且两个指纹字段在"不存在 / 删除后"场景下的取值 MUST 为 `null` / Python 侧 `None`，**MUST NOT 用空串**（spec FR-004）　〔覆盖 spec FR-004 · SC-007〕
- [X] T063 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写**条件字段**断言：`copy` / `move` 的 `change` MUST 额外含 `src` 与 `src_rel_path`；`include_previous=True` 且旧正文 ≤ 256 KiB 时 MUST 含 `previous_content`；> 256 KiB 时 MUST 改为含 `previous_content_truncated is True` 且**不含** `previous_content`（spec FR-005）　〔覆盖 spec FR-005 · SC-007〕
- [X] T064 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写**路径与差异头**断言：`change.rel_path` MUST 是**工作区相对**的 POSIX 路径、工作区之外的路径 MUST 回退为绝对路径（MUST NOT 抛异常）、`unified_diff` 的头 MUST 为 `--- a/<rel_path>` / `+++ b/<rel_path>`（spec FR-007）　〔覆盖 spec FR-007〕
- [X] T065 [P] [US12] 在 `tests/unit/test_builtin_tools.py` 写**差异截断**断言：差异超过 64 KiB 时 MUST 截断且 `diff_truncated is True`（spec FR-003）　〔覆盖 spec FR-003〕

**Checkpoint**: US1 ~ US12 均可独立验证

---

## Phase 15: User Story 13 - 先看后写，不落盘 (Priority: P13)

**Goal**: 四个改文件的工具都支持"只算不写"的预览 —— 零磁盘副作用，但照常返回完整变更记录

**Independent Test**: 在独立子进程中先写入旧内容、再以预览模式写入新内容，断言文件内容未变、返回记录标明未落盘、差异文本非空、目录下无临时文件残留

### Tests for User Story 13 (TDD) ⚠️

- [X] T066 [P] [US13] 在 `tests/unit/test_builtin_tools.py` 写 `write_file` 预览断言：`dry_run=True` 时磁盘内容 MUST **逐字节未变**、返回 MUST 含 `applied is False` 且 `change.applied is False`、`change.unified_diff` 仍**非空**（含被替换行）、目录中 MUST NOT 有 `.donkey-tmp` 残留（spec FR-020）　〔覆盖 spec FR-020 · SC-017〕
- [X] T067 [P] [US13] 在 `tests/unit/test_builtin_tools.py` 写 `copy_file` / `move_file` / `delete_file` 预览断言：三者预览时 MUST **无任何磁盘副作用**（不写目标 / 不移源 / 不删文件）但 MUST 仍返回完整变更记录且 `applied is False`（spec FR-020 的适用范围）　〔覆盖 US13 · spec FR-020〕
- [X] T068 [P] [US13] 在 `tests/unit/test_builtin_tools.py` 写"预览不建父目录"断言：对**不存在**的父目录做预览写入 MUST NOT 创建该父目录（spec FR-020）　〔覆盖 US13 · spec FR-020〕

**Checkpoint**: US1 ~ US13 均可独立验证

---

## Phase 16: User Story 14 - 写失败不会毁掉旧内容 (Priority: P14)

**Goal**: 所有写路径原子 —— 写到一半失败时旧文件完好，且不留临时文件残留

**Independent Test**: 让目标路径的父路径是一个**已存在的文件**（使写入必然失败），断言写入抛错、原文件内容未变、目录下无临时文件残留

### Tests for User Story 14 (TDD) ⚠️

- [X] T069 [P] [US14] 在 `tests/unit/test_builtin_tools.py` 写"失败不毁旧内容"断言：目标路径的父路径是一个已存在的**文件**时，写入 MUST 抛异常、该文件内容 MUST **逐字节未变**、其所在目录 MUST NOT 有 `.donkey-tmp` 残留（spec FR-008 / FR-017）　〔覆盖 spec FR-008 / FR-017 · SC-017〕
- [X] T070 [P] [US14] 在 `tests/unit/test_builtin_tools.py` 写"原子写建父目录"与"目标是目录"断言：① 写向**不存在**的父目录 MUST 成功创建父目录并落盘（spec FR-009 / FR-018）；② 目标路径**已存在且是目录**时 MUST 抛"是目录"类错误，MUST NOT 静默跳过、MUST NOT 递归删除目录内容（spec FR-018）　〔覆盖 spec FR-009 / FR-018 · SC-017〕
- [X] T071 [P] [US14] 在 `tests/unit/test_builtin_tools.py` 写"指纹按原始字节"断言：含 BOM 或含非法 UTF-8 字节的文件，其指纹 MUST 与 `sha256_bytes(原始字节)` **逐字相等**（MUST NOT 先解码再编码 —— spec FR-006）　〔覆盖 spec FR-006〕
- [X] T072 [P] [US14] 在 `tests/unit/test_builtin_tools.py` 写"临时文件清理"断言：写入成功后目标目录 MUST NOT 残留任何 `.donkey-tmp` 文件（临时文件名点开头，spec FR-008）　〔覆盖 US14 · spec FR-008〕

**Checkpoint**: US1 ~ US14 均可独立验证

---

## Phase 17: User Story 15 - 删除也有记录、契约版本冻结 (Priority: P15)

**Goal**: 删除动作同样留下变更记录（旧指纹 + 可选旧正文），且变更记录的契约版本恒为 `1`

**Independent Test**: 在独立子进程中写入后删除，断言返回记录标明动作 `delete`、类型 `file`、旧版本指纹非空、新版本指纹**为 `null`**、文件确实不在了，且契约版本为 `1`

### Tests for User Story 15 (TDD) ⚠️

- [X] T073 [P] [US15] 在 `tests/unit/test_builtin_tools.py` 写删除记录断言：删除已存在文件 MUST 返回 `action == "delete"`、`type == "file"`、`change.previous_hash` 非空、`change.new_hash is None`（spec FR-004：指纹"删除后" MUST 为 `null` / Python 侧 `None`，**MUST NOT 用空串**）、`change.new_size == 0`，且文件确实不存在（spec FR-004 / FR-005）　〔覆盖 spec FR-004 / FR-005 · SC-007〕
- [X] T074 [P] [US15] 在 `tests/unit/test_builtin_tools.py` 写"请求旧正文"断言：`include_previous=True` 且目标是**文件**时 `change.previous_content` MUST 等于原内容；目标是**目录**时 MUST NOT 出现任何旧正文字段（目录粒度记录 —— 该缺口的登记位置是 spec 的 Edge Cases「删除目录」条与 Key Entities「已知缺口与风险登记」，**不是** FR-096；FR-096 讲的是二进制 / 媒体读取报错与 `read_file` 的目录分支）　〔覆盖 spec FR-005 · SC-007〕
- [X] T075 [P] [US15] 在 `tests/unit/test_builtin_tools.py` 写**契约版本冻结**断言：`CHANGE_RECORD_VERSION == 1`；`build_change_record` 的返回 MUST 含**恰好 12 个基线键**（与 spec FR-004 逐字一致，防字段漂移）；三个常量 MUST 为 `1` / `64 * 1024` / `256 * 1024`（spec FR-003）　〔覆盖 spec FR-003 / FR-004 · SC-007〕
- [X] T076 [P] [US15] 在 `tests/unit/test_builtin_tools.py` 写**期望指纹守卫**断言：`write_file` / `copy_file` / `move_file` / `delete_file` 四个工具传入**不匹配**的期望指纹时 MUST **拒绝执行**并抛 `tools.changes.FileChangedError`、MUST **无任何磁盘副作用**、文件内容 MUST 未变；不传期望指纹时行为 MUST 与旧调用方式**逐字节一致**（spec FR-019）　〔覆盖 spec FR-010 / FR-019〕

**Checkpoint**: US1 ~ US15 全部可独立验证 —— 15 个故事的**单元与集成**层完成

---

## Phase 18: 验收层 — 黑盒验收脚本（16 个断言）

**Purpose**: 交付跨故事的黑盒验收（16 个 `test_scenario_*` 函数，同一文件）。**F001-P2 的阶段边界断言组改写（T094 / T095）已前移至 Phase 3（随资产落地即刻执行）**，使 P2 套件尽早恢复绿

### Implementation for 全部 15 个 User Story（验收脚本主体：16 个黑盒断言）

- [X] T077 [US1] 创建 `tests/e2e/phase/verify_phase_f001_p3.py` 的骨架：MUST **黑盒**（MUST NOT import `donkey.*` 业务代码，只以子进程观察退出码 / stdout / stderr 与文件系统副作用 —— spec FR-066）；`donkey` 命令的解析规则 MUST 沿用 F001-P1 的口径（优先用 PATH 上的控制台脚本 + 校验其解析到的包位于当前工作树内，不可用时回落到 `python -m donkey` 并**打印一次显式告警**，回落时以仓库根为工作目录 —— 与 P1 / P2 的既有脚本一致）；MUST 沿用 10 秒的单次耗时上限（spec SC-019）　〔覆盖 spec FR-064 / FR-066 · SC-001 / SC-019〕
- [X] T078 [US1] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 1**（init 后 `tools/` 下 6 个文件齐备 —— spec US1 场景 1）　〔覆盖 US1 · spec FR-043 / FR-053 · SC-003〕
- [X] T079 [US2] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 2**（3 个工具可 import + 每个 `@tool` 的 docstring 长度 > 20 —— 用**独立子进程**导入，spec US2）　〔覆盖 US2 · spec FR-023 · SC-006〕
- [X] T080 [US3] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 3**（`run_shell("echo hello")` 返回可解析 JSON，`stdout` 含 `hello`、`returncode == 0`、`timed_out is False` —— spec US3）　〔覆盖 US3 · spec FR-031 · SC-023〕
- [X] T081 [US4] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 4**（文件工具七动作的连续操作 —— 写 / 读 / 复制 / 列目录 / stat / 删除，spec US4）**注**：本场景**不**断言截断 / 续读指针（该判据由 T034 / T035 在单元层承载，SC-022）　〔覆盖 US4 · spec FR-013 / FR-022 · SC-006〕
- [X] T082 [US5] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 5**（网络工具 HTTP mock —— **mock 与 import MUST 同处一个子进程**：子进程内先打桩 `httpx.Client.send` 再导入调用，spec FR-067 / research.md R-20）　〔覆盖 US5 · spec FR-067 / FR-089 · SC-021〕
- [X] T083 [US6] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 6**（Skills 三层：frontmatter 合法 + Level 2 非空 + Level 3 ≥ 1 个文件，spec US6）　〔覆盖 US6 · spec FR-049 · SC-018〕
- [X] T084 [US7] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 7**（3 个内置工具文件 MUST NOT 含 `glob_search` / `grep_search`，spec US7）　〔覆盖 US7 · spec FR-025 · SC-013〕
- [X] T085 [US8] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 8**（`rm tools/filesystem.py` 后 init 补齐，spec US8）　〔覆盖 US8 · spec FR-087 · SC-003〕
- [X] T086 [US9] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 9**（`--force` 不动用户的 `tools/my_custom_tool.py`，且内置工具已恢复出厂 —— spec US9）　〔覆盖 US9 · spec FR-105 · SC-024〕
- [X] T087 [US10] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 10**（9 个工具函数在独立子进程中全部可调用，spec US10）　〔覆盖 US10 · spec FR-062 · SC-009〕
- [X] T088 [US11] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 11**（init 不做 F002 静态检查 —— 即使内置工具文件有问题，init 仍以退出码 `0` 结束，spec US11）　〔覆盖 US11 · spec FR-081 · SC-010〕
- [X] T089 [US12] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 12**（`write_file` 返回统一变更记录 —— 首次 `create`、二次 `update` 且 `previous_hash` == 上次的 `new_hash`、差异含 `-b` 与 `+c`，spec US12）　〔覆盖 US12 · spec FR-004 / FR-016 · SC-007〕
- [X] T090 [US13] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 13**（`dry_run=True` 不产生磁盘副作用 —— 文件内容逐字节未变、`applied is False`、差异含 `-old`、无 `.donkey-tmp` 残留，spec US13）　〔覆盖 US13 · spec FR-020 · SC-017〕
- [X] T091 [US14] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 14**（写失败时旧文件内容完好且无临时文件残留 —— 用"父路径是文件"构造失败，spec US14）　〔覆盖 US14 · spec FR-008 · SC-017〕
- [X] T092 [US15] 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 15**（`delete_file` 返回 `action=delete` + `type=file` + `previous_hash` 非空 + `new_hash is None`，且契约版本 == `1`，spec US15）　〔覆盖 US15 · spec FR-003 · SC-007〕
- [X] T093 在 `tests/e2e/phase/verify_phase_f001_p3.py` 实现**场景 16**（**CI 交付检查** —— `.github/workflows/ci.yml` MUST 存在且含四类关键命令：`pytest tests/` / `--cov=donkey.core` / `--cov-fail-under=80` / `ruff check` / `mypy`；宪法 §6.3 临时例外 E-01 到期闭合，spec FR-065）　〔覆盖 spec FR-065 · SC-001〕（**CI 交付检查不是 User Story** —— spec FR-064 的 16 个断言 = 15 个功能场景 + 1 个 CI 检查；本任务无 [Story] 标签，与本文件的 e2e 映射表"（非故事）"行一致）


**Checkpoint**: 16 个黑盒断言齐备 —— 可跑全量（P2 边界断言已于 Phase 3 改写完毕）

---

## Phase 19: Polish & Cross-Cutting Concerns

**Purpose**: 静态检查、覆盖率、构建产物打包核对、全量验证与文档收口

- [X] T096 [P] 执行 `ruff check donkey/ tests/` 与 `mypy donkey/ tests/` 并清零 error（spec FR-086）—— **注意**：模板正文是 `.txt`，**不在**这两个工具的检查口径内（research.md R-08），其质量由 T019 的 `compile()` 自检兜底　〔覆盖 spec FR-086 · SC-010〕
- [X] T097 执行 `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` 并确认覆盖率 ≥ 80%（spec SC-020 —— MUST 用**独立命令**，MUST NOT 写进 pytest 全局 `addopts`）　〔覆盖 spec SC-020〕
- [X] T098 执行全量 `pytest tests/ -v` 并确认 **F001-P1 / P2 / P3 全部 PASS**（spec SC-002：P1 的 7 个 + P2 的 14 个 e2e 断言与两个既有单测文件仍全绿）。**MUST 逐条跑通 plan「可执行测试命令列表 ① 前置套件 + ② 本 Phase 套件」的 5 条命令**（`verify_phase_f001_p1.py` / `verify_phase_f001_p2.py` / `test_init_workspace.py` / `test_template_skeleton.py` / `test_builtin_tools.py` / `test_init_to_load.py` / `verify_phase_f001_p3.py`）　〔覆盖 spec FR-085 · SC-002〕
- [X] T099 [P] 执行 `quickstart.md` §1 的门禁冒烟复跑（确认渲染产物侧的导入**未**把可观测性后端带进 donkey 自有代码路径）与 §9 的排查指引逐条走查（确认无遗留项）　〔覆盖 spec FR-078 · SC-012〕
- [X] T100 核对 spec 的**已回填项**并把结论**留痕**：确认 FR-070 的定点修订（允许 `init_workspace_inner` 步骤 ④ 增加一条条目级强制重置豁免）与 FR-098 的"**五处**有意偏离"确已写入 spec（2026-10-23 `/speckit.analyze` 后已直接修正）；**并确认 2026-10-23 第二轮定点修订的 **5 项改动**已落盘**（`## Clarifications` 第 5 段 / **4 项决策** + 1 项纯格式：① FR-050 改为**引用**宪法 §6.3 例外 E-02 + §5 章 [D-19]、MUST NOT 自设豁免 ② FR-004 的指纹"为空"钉死为 `null` / Python 侧 `None`、MUST NOT 用空串 ③ SC-021 改写为**两类可判定判据** ④ FR-068(a) 的嵌套加粗修复 ⑤ read_file 返回值语义收敛至 FR-015 单一权威表述），且 FR 仍 **105** 条 / SC 仍 **24** 条、编号未增删改；MUST NOT 在本任务中改动 spec 的其它内容；research.md 的「待回填 spec 的清单」MUST 随之标注为已闭合（**2026-10-23 已在本轮直接闭合**）。**本任务是纯核对 + 留痕**（不产生新的 spec 改动）—— 核对结论 MUST 以一行文字写入本 Phase 的交付说明（PR 描述 / 交付清单），MUST NOT 改动 spec / plan / tasks 的其它任何内容　〔覆盖 spec FR-069 · SC-002〕
- [X] T102 核对**单元测试覆盖面**：统计 `tests/unit/test_builtin_tools.py` 的测试函数数 MUST **≥ 15**，且 MUST 逐条命中 **FR-058 列出的 23 个类别**（写后读一致 / 复制-移动-删除 / 列目录与属性 / 命令回显 / 命令超时 / 网络成功 / 网络超时 / 三个模块可导入 / 写文件变更记录 / **复制-移动-删除的期望指纹守卫** / **复制-移动-删除的预览开关** / 更新记录差异 / 预览不落盘 / 期望指纹不匹配 / 原子写失败保旧内容 / 删除记录旧指纹 / 契约版本稳定 / 读取双上限与截断留痕 / 二进制与媒体报错 / 网络四道边界 / 命令输出超限截断 / 两侧上限常量一致 / **命令 `timeout` 无上限** —— `run_shell(..., timeout=999)` MUST 不报错、MUST 正常返回，spec FR-028，与 FR-037 的 120 秒上限构成**有意的不对称**）；**另须命中本 Phase 在 FR-058 类别表之外补齐的 4 类**（T105 ~ T108）—— ① 退出码 4 的映射与错误信息口径（T105）② 三个记忆库文件未被触碰（T106）③ 网络工具说明文字的四项边界陈述 + 无地址范围过滤 + `trust_env=False`（T107）④ 读取侧分页边界（目录分支 / 请求行数超上限 / `list_dir` 条目超上限）（T108）；MUST NOT 以"用例数够了"替代"类别齐了"（spec FR-058 / SC-008）。**口径**：第 23 类已于 2026-10-23 的 spec 定点修订**正式登记**进 FR-058 的类别表与 SC-008 的"23 个类别"门槛 —— 本任务 MUST NOT 反过来改写 FR-058 的类别表或 SC-008 的门槛　〔覆盖 spec FR-028 / FR-058 · SC-008〕

- [X] T103 核对**构建产物的打包完整性**（contracts/template-manifest.md B3 / spec FR-057）：构建 wheel 与 sdist，核对**45 个文本型条目的 `<条目路径>.txt` 全部在产物内**（含本 Phase 新增的 8 个）；MUST NOT 通过"源码树里有"替代"产物里有"；MUST NOT 改动 `[tool.setuptools.package-data]`（已是 `"**/*.txt"` —— research.md R-09）　〔覆盖 spec FR-057 · SC-003〕

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 —— 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup —— **阻塞**所有用户故事
- **User Stories (Phase 3 ~ 17)**: 全部依赖 Phase 2 完成
  - **Phase 3（US1）是 MVP** —— 它一次性交付全部模板资产，**并在末尾改写 P2 的阶段边界断言使 P2 套件恢复绿**；后续故事在其之上做行为硬化
  - US2 ~ US15 之间无实现依赖（都只动 `tests/unit/test_builtin_tools.py` 的不同区段），可并行（受"同文件串行"限制，见下）
- **验收层 (Phase 18)**: 依赖 Phase 4 ~ 17 —— 黑盒脚本断言全部 15 个故事的行为
- **Polish (Phase 19)**: 依赖所有期望交付的故事完成（含 T094 / T095 的 P2 改写落地）

### User Story Dependencies

| 故事 | 依赖 | 备注 |
|---|---|---|
| US1 (P1) | Phase 2 | 交付 6 个 `tools/` 文件 + 8 条清单条目 → **MVP** |
| US2 (P2) | US1（资产） | 只加断言，不改实现 |
| US3 (P3) | US1 | 只加断言 |
| US4 (P4) | US1 | 只加断言 |
| US5 (P5) | US1 | 只加断言 |
| US6 (P6) | US1 | 只加断言（Level 3 源已在 US1 就位） |
| US7 (P7) | US1 | 只加断言 |
| US8 (P8) | US1 | 只加断言 |
| US9 (P9) | US1 | **唯一带实现改动的后续故事** —— 渲染层豁免（T049） |
| US10 (P10) | US1 | 新增 `tests/integration/test_init_to_load.py` |
| US11 (P11) | US1 | 只加断言 |
| US12 (P12) | US1 | 只加断言 |
| US13 (P13) | US1 | 只加断言 |
| US14 (P14) | US1 | 只加断言 |
| US15 (P15) | US1 | 只加断言 |

### 用户故事 ↔ e2e 黑盒场景对照（spec 的 1:1 映射）

| 故事 | 优先级 | e2e 场景 | 场景断言任务 |
|---|---|---|---|
| US1 | P1 | 场景 1（6 个文件齐备） | T078 |
| US2 | P2 | 场景 2（可 import + docstring） | T079 |
| US3 | P3 | 场景 3（回显命令） | T080 |
| US4 | P4 | 场景 4（七动作） | T081 |
| US5 | P5 | 场景 5（HTTP mock） | T082 |
| US6 | P6 | 场景 6（Skills 三层） | T083 |
| US7 | P7 | 场景 7（无检索能力） | T084 |
| US8 | P8 | 场景 8（幂等补齐） | T085 |
| US9 | P9 | 场景 9（--force 不误伤） | T086 |
| US10 | P10 | 场景 10（跨进程可用） | T087 |
| US11 | P11 | 场景 11（不做配置检查） | T088 |
| US12 | P12 | 场景 12（写文件带回变更记录） | T089 |
| US13 | P13 | 场景 13（预览不落盘） | T090 |
| US14 | P14 | 场景 14（写失败不毁旧内容） | T091 |
| US15 | P15 | 场景 15（删除记录 + 版本冻结） | T092 |
| —（非故事） | — | 场景 16（CI 交付检查） | T093 |

### Within Each User Story

- 测试 MUST 先写并确认**失败**，再补实现（对已就位的资产，测试写完即应通过 —— 此时失败即说明实现有偏差）
- 契约库 → 文件工具 → 命令工具 → 网络工具（依赖方向）
- 故事完成后再进入下一优先级

### Parallel Opportunities

- Phase 1 的 T001 / T002 可并行
- Phase 3 的 T015 / T016 / T017 可并行（三个不同的 Level 3 源文件）
- US2 ~ US8、US11 ~ US15 的**测试任务**可并行（不同故事，不同断言区段）
- Phase 18 的 16 个场景断言任务在**不同故事之间**可并行（同文件 → 实际需串行或分批提交，见下）
- Phase 19 的 T096 / T099 可并行

### 受限（不可并行）

| 受限项 | 原因 | 缓解 |
|---|---|---|
| **T007 / T019 / T021 ~ T076 / T104 / T105 ~ T108 全部写同一个文件** `tests/unit/test_builtin_tools.py` | 同文件并发写会互相覆盖 | 按故事**串行**执行，或每人只改自己故事对应的区段并**分批提交** |
| **T008 ~ T018 全部写同一目录** `donkey/core/workspace/templates/` | 虽文件名不同，但 T010 / T018 是**覆盖**既有源文件 | 不同文件可并行；覆盖操作 MUST NOT 与其它任务同时触碰同一文件 |
| **T077 ~ T093 全部写同一个文件** `tests/e2e/phase/verify_phase_f001_p3.py` | 同上 | 串行或分批提交 |
| **T094 / T095 改写 P2 的既有测试（已前移至 Phase 3）** | 同上，且 MUST NOT 让 P2 的断言变红 | 已前移至 **Phase 3 末尾**；T095 MUST 在 T094 之后（e2e 的场景 1 依赖单测的计数口径已统一） |
| **T049 改 `core/workspace/init.py`** | 会影响所有后续计数断言 | MUST 在 Phase 11 单独完成并立即跑 T052 验证计数 |

---

## Parallel Example: User Story 12

```bash
# 同一故事内的测试断言可并行（不同断言区段，同一文件 → 分批提交）：
Task: "写'创建'的变更记录断言 in tests/unit/test_builtin_tools.py"
Task: "写'更新'的变更记录断言 in tests/unit/test_builtin_tools.py"
Task: "写基线键集合断言 in tests/unit/test_builtin_tools.py"
Task: "写条件字段断言 in tests/unit/test_builtin_tools.py"

# 不同故事之间可并行（不同人）：
Task: "US3 的命令工具断言 in tests/unit/test_builtin_tools.py"
Task: "US5 的网络工具断言 in tests/unit/test_builtin_tools.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup（dev 依赖 + CI + 门禁冒烟）
2. 完成 Phase 2: Foundational（3 处改动：核心层 2 处 + 客户端映射 1 行 + 测试夹具 + exit 4 的断言 T105）
3. 完成 Phase 3: User Story 1 —— 6 个 `tools/` 文件 + 8 条清单条目 + 8 个新源 + 2 处覆盖源
4. **停下来验证**：`donkey init` → `tools/` 下 6 个文件齐备、计数 `54 / 48 / 0`、工具可被导入调用（quickstart §2 / §3）
5. 演示 / 交付 MVP

> **US1 的价值是真实的**：它交付的就是"一次 init 得到可用的内置工具与契约库" —— 用户拿到的工作区**已经可以**跑 `write_file` / `read_file` / `run_shell` / `fetch_url` 并拿到变更记录（只是边界行为还未被断言锁死）。

### Incremental Delivery

1. Phase 1 + Phase 2 → 地基就位
2. Phase 3（US1）→ **验证** → 演示（MVP：工作区里已有可用的工具）
3. Phase 4 ~ 11（US2 ~ US9）→ 逐个故事加断言 → 每个故事独立可测
4. Phase 12（US10）→ 集成测试层启用（可移植性实证）
5. Phase 13 ~ 17（US11 ~ US15）→ 边界与契约行为锁死
6. Phase 3 末尾 → 改写 P2 边界断言（T094 / T095，使 P2 套件恢复绿）；Phase 18 → 黑盒验收
7. Phase 19 → 静态检查 / 覆盖率 / 全量 / 回填 spec

**每个阶段都增不减**：后续故事 MUST NOT 破坏已交付故事的行为 —— 这正是 P2 的**持久不变量**在 P3 的延续。

### Parallel Team Strategy

多人并行时：

1. 团队共同完成 Phase 1 + Phase 2（含夹具 —— 它是所有故事共享的写入目标，MUST 由**一人**先建好）
2. Phase 3（US1）由**一人**完成（模板资产是本 Phase 的主体，且是所有故事的依赖）
3. Phase 4 ~ 17：**每人认领一个故事**，但 `tests/unit/test_builtin_tools.py` 的写入 MUST **串行化**（分批提交）—— 建议每人只在自己的故事区段追加，并在提交前 rebase
4. Phase 18 的 16 个场景：**一人**完成（同一文件）

---

## P2 套件的中间态（**实施者必读**）

F001-P2 的既有套件（`tests/unit/test_template_skeleton.py` 与 `tests/e2e/phase/verify_phase_f001_p2.py`）中有一批断言编码的是 P2 的"**阶段边界**"（清单 46 条 / 文件型 40 / 落地 41 / 落地目录 7 / "工作区内无任何 `.py` 文件" / "内置工具文件不存在" / "退出码集合恰为 `{0,1,2,3}`" / "映射表取值集合恰为 `{1,2,3}`" / "退出码 4 不在使用集合中" / "`tools/README.md` 正文含'内置工具由后续阶段生成'"）。本 Phase 一旦执行 **T014**（清单 46 → 54），这些断言**必然变红** —— 这是**设计使然**，不是实现出错。

**断言条数与位置 MUST 以两个 P2 测试文件的实际内容为准**（T094 / T095 已改为按**文件 + 行号逐条枚举**）—— MUST NOT 以任何概括性计数为准。

| 区间 | P2 套件状态 | 原因 |
|---|---|---|
| T001 ~ T013（Phase 1 ~ Phase 3 前半） | 🟢 全绿 | 清单仍是 46 条 |
| **T014（清单 46 → 54）之后、T094 / T095 完成之前** | 🔴 **预期为红** | 清单已 54 条，P2 的阶段边界断言失效（T094 / T095 已前移至 Phase 3 末尾，红灯窗口止于 Phase 3 内） |
| **T094 / T095 完成之后** | 🟢 全绿 | 阶段边界断言组已按 P3 口径逐条改写 |

**处置**：T094 / T095 已**前移至 Phase 3 末尾**（紧随 T014 与全部资产落地）→ 红灯窗口被压到最短。实施者若在 T014 之后看到 P2 套件变红，**MUST NOT** 试图"修好" P2 的断言 —— MUST 等 T094 / T095 到位（它们的实现口径见 research.md R-15 / R-16）。

**MUST NOT 改写**：P2 **场景 5**（`test_scenario_5_name_injection`）的"渲染产物 MUST NOT 残留 `{{ … }}` 占位符"断言（`tests/e2e/phase/verify_phase_f001_p2.py:393-395`）与单测侧同源的 3 处（`tests/unit/test_template_skeleton.py:753` / `:778` / `:982`）→ **MUST 保持原样** —— 它们是 P2 的**持久不变量**，其成立由 spec FR-049 的**占位记法约束**保证（T017 / T095 承载），MUST NOT 靠删断言兑现（spec FR-069）。

**最终门槛不变**：SC-002 要求 P1 的 7 个 + P2 的 14 个 e2e 断言与两个既有单测文件**在交付时全绿**（T098 承载）。

---

## Notes

- [P] 任务 = 不同文件、无未完成任务的依赖
- [Story] 标签把任务映射到具体用户故事，供追溯用
- **每个故事 MUST 能独立完成并独立验证** —— 独立验证的方式见各阶段的 "Independent Test"
- 模板正文是 `.txt` → **零静态检查覆盖**（research.md R-08）→ T019 的 `compile()` 自检是它的兜底，MUST NOT 跳过
- 涉及非显然实现选择的任务 MUST 先读 research.md 对应的 R-xx
- 每完成一个任务或一组逻辑任务就提交
- 可在任何 checkpoint 处停下，单独验证该故事
- 避免：含糊的任务、同文件并发冲突、破坏故事独立性的跨故事依赖
- **提交前必查**：`git status` 里 MUST NOT 出现 `donkey/core/workspace/templates/tools/` 之外的意外改动；P2 的两个既有测试文件 MUST 只含 T094 / T095 的**定点改写**
