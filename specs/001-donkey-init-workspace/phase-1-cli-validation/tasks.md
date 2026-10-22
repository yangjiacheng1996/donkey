---
description: "Task list for F001-P1 cli_validation — donkey init 命令入口与 workspace 路径校验"
---

# Tasks: F001-P1 `cli_validation` —— `donkey init` 命令入口与 workspace 路径校验

**Input**: Design documents from `specs/001-donkey-init-workspace/phase-1-cli-validation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: 包含测试任务 —— spec FR-024 要求 ≥9 个单元测试用例（本轮实现共 20 个：core 层 17 个 + CLI 层 3 个），FR-025 要求 7 个黑盒验收场景；spec SC-016 另要求 `donkey.core` 单元测试行覆盖率 ≥ 80%（由 Polish 阶段的覆盖率验证任务度量）；宪法 §4.1 规定 TDD 流程。每个用户故事阶段**先写测试 → 确认失败 → 再实现**。

**Organization**: 任务按用户故事分组，每个故事可独立实现、独立测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）——写同一文件的两个任务**不可**同时标 `[P]`（见「Parallel Opportunities」的「受限」条目）
- **任务 ID**: 编号**不重排**——`T002b` 是后补插入的 Setup 阶段任务（`cli/cli_client.py` 最小骨架前移），其排序位置不代表执行顺序（真正的次序约束以正文描述与「Dependencies & Execution Order」为准）
- **测试函数 vs 断言组**：一个 `test_` 函数 = 1 个测试函数，内部可含多个断言组（如 T044 的「末段名带尾部分隔符」内嵌于 `test_init_workspace_accepts_arbitrary_basename`）。本文件与 `plan.md` / `quickstart.md` 的「20 个单元测试用例」口径一律指 **20 个测试函数**（core 层 17 + CLI 层 3）；断言组数可多于 20，但不计入该口径
- **[Story]**: 所属用户故事（US1~US7，对应 spec 的 P1~P7）
- 描述中含确切文件路径

## Path Conventions

- **单包结构**：包根 = 仓库根的 `donkey/`；测试根 = 仓库根的 `tests/`（与 `donkey/` 同级，宪法 §3.1）
- 核心层 `donkey/core/`（零进程感知）→ 客户端层 `donkey/cli/` → 打包入口 `pyproject.toml` / `donkey/__main__.py`
- 引用契约：`specs/001-donkey-init-workspace/phase-1-cli-validation/contracts/`（`cli-contract.md` / `library-api.md` / `exit-codes.md`）

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 建立可安装、可运行、可测试的工程基座

- [X] T001 创建 `pyproject.toml`：[build-system] setuptools>=68 + [project] name="donkey" / version="0.1.0" / requires-python=">=3.11" / dependencies=[]（运行时零第三方依赖）+ [project.scripts] `donkey = "donkey.cli.cli_client:main"` + [tool.setuptools.packages.find] include=["donkey*"] + [tool.setuptools.package-data] "donkey.core.workspace.templates"=["**/*.txt","**/*.json"]；**MUST 显式声明 `namespaces = true`**——`donkey/core/workspace/templates/` 是**无 `__init__.py` 的纯数据目录**，依赖 setuptools 的命名空间包发现才能被收集并使 `package-data` 生效（setuptools ≥61 的 `tool.setuptools.packages.find` 该项默认值即为 `true`，此处显式声明是为防默认值变化；若该值被置为 `false`，3 个模板源会**静默不进安装包**，F001-P2 渲染时才以 exit 3 暴露）
- [X] T002 [P] 创建包骨架 `donkey/__init__.py`（`__version__ = "0.1.0"`）、`donkey/core/__init__.py`、`donkey/cli/__init__.py`、`donkey/core/workspace/__init__.py`（均为空或仅含版本号）；**并创建 `donkey/web/.gitkeep` 与 `donkey/gui/.gitkeep` 两个空占位**（plan Project Structure 承诺 `web/` / `gui/` 占位目录，且 spec Assumptions「仓库与骨架」已按本轮修订订正为「四个子目录由本阶段创建」——git 不跟踪空目录，故 MUST 以 `.gitkeep` 固化，比照 `tests/integration/.gitkeep` 的做法；**不**建 `__init__.py`，由 F005 / F006 实施时决定；本 Phase MUST NOT 在其中填入任何内容）
- [X] T003 [P] 创建 `donkey/__main__.py`：`import sys` + `from donkey.cli.cli_client import main` + `sys.exit(main())`（模块入口，与控制台脚本行为一致，research.md R-02）
- [X] T002b [P] 创建 `donkey/cli/cli_client.py` **最小骨架**：`DonkeyArgumentParser(argparse.ArgumentParser)` 覆写 `error()` → `self.exit(1, ...)`（用法提示与错误信息写 stderr）；`_build_parser()` 返回 `argparse.ArgumentParser(prog="donkey", ...)`——**MUST 显式传 `prog="donkey"`**（argparse 默认取 `sys.argv[0]` 的 basename，`python -m donkey` 下会得到 `__main__.py`，使两条入口的 stderr usage 提示不一致，违反 spec FR-023「两种入口 MUST 产生完全相同的退出码与输出」；依据 research.md R-01 / plan 决策表 R-01）；`main(argv: list[str] | None = None) -> int` 落一个最小实现（解析参数后 `return 0`，**MUST NOT** 在本任务 import `donkey.core.exit_codes`——该模块 T008 才创建，Setup 阶段不可依赖；`EXIT_CODE_OK` 的使用留待 T019）；本任务只保证 `donkey --help` 与 `python -m donkey --help` 可用，FR-001「未指定子命令 → 退出码 1」由 T014 的 `add_subparsers(..., required=True)` + `error()` 覆写共同兑现；**T002b ~ T019 窗口内 `donkey init <path>` 会返回 `0` 但不建目录**（`init` 分支留待 T019）——该窗口内 MUST NOT 以 `donkey init` 作为功能验收证据，功能验收以 T020 为准
- [X] T004 在 `pyproject.toml` 配置 ruff：`[tool.ruff]` line-length=100 / target-version="py311" / src=["donkey","tests"]；`[tool.ruff.lint]` select=["E","F","I","UP"]
- [X] T005 在 `pyproject.toml` 配置 mypy：python_version="3.11" / strict=true / explicit_package_bases=true / mypy_path="." / files=["donkey"]（`files` 仅为「无参数裸跑 `mypy`」时的兜底目标；T052 的 `mypy donkey/ tests/` 以命令行参数为准，命令行参数会覆盖 `files`）；**MUST 同时声明 `explicit_package_bases` 与 `mypy_path`**——mypy 的模块名解析规则：目录下无 `__init__.py` 时模块名取文件名本身（`tests/unit/test_init_workspace.py` → `test_init_workspace`；`tests/e2e/phase/verify_phase_f001_p1.py` → `verify_phase_f001_p1`），只有开启 `explicit_package_bases` 并给出基准目录（`mypy_path="."`）后模块名才成为 `tests.unit.test_init_workspace` / `tests.e2e.phase.verify_phase_f001_p1`，`[[tool.mypy.overrides]]` 的 `module="tests.*"` 才真正命中；否则 `strict` 全量作用于测试层，T052 的「零 error 零 warning」必然失败——20 个无标注测试函数会报 `no-untyped-def`）；`[[tool.mypy.overrides]]` module="tests.*" 时 MUST 放宽全部与「测试函数无需完整类型标注」相关的严格项——`disallow_untyped_defs=false` / `disallow_any_generics=false` / `disallow_untyped_calls=false` / `disallow_untyped_decorators=false` / `warn_return_any=false` / `warn_unused_ignores=false` / `no_implicit_reexport=false`（`strict=true` 隐含开启上述各项，仅放宽 `disallow_untyped_defs` 一项不足以让 20 个测试函数通过 T052 的「零 error 零 warning」判据；其余严格项在 `donkey/` 上保持全量开启）
- [X] T006 在 `pyproject.toml` 配置 pytest（`[tool.pytest.ini_options]` testpaths=["tests"] / pythonpath=["."] / addopts="-ra" / python_files=["test_*.py", "verify_phase_*.py"]）并创建 `tests/unit/`、`tests/e2e/phase/` 目录与 `tests/integration/.gitkeep` 占位（**`tests/integration/` 本 Phase 为空占位**——P1 仅一个子模块、无跨模块集成面，跨层边界由 e2e 黑盒场景覆盖，故 §4.1「单元 + 集成 + e2e」在本 Phase 退化为「单元 + e2e」；`pythonpath` ini 选项需 pytest ≥7，dev 依赖须锁 `pytest>=7`）；**MUST** 显式声明 `python_files = ["test_*.py", "verify_phase_*.py"]`——黑盒验收脚本按宪法 §3.1 固定命名为 `verify_phase_<f>_<n>.py`，不匹配 pytest 默认 `python_files`，不显式声明则 `pytest tests/` 不会收集它、7 个 e2e 场景在 CI 中零证据（plan G13 / research.md R-07）；**MUST NOT** 把 `--cov` / `--cov-fail-under` 写入 `[tool.pytest.ini_options]` 的 `addopts`（否则 e2e 黑盒脚本单独运行时不 import 业务代码，会把覆盖率拉到 0 而误报失败）——覆盖率 MUST 以**独立命令**度量（见 Polish 阶段的覆盖率验证任务）
- [X] T007 在 `pyproject.toml` 加可选依赖组 `[project.optional-dependencies] dev = ["pytest>=7", "pytest-cov", "ruff", "mypy"]`（`pytest>=7` 下限：T006 的 `pythonpath` ini 选项自 pytest 7.0 起提供），然后执行 `.venv/bin/pip install -e ".[dev]"`（用仓库内的 `.venv`，与 quickstart §0 保持一致；`.venv` 已存在时该命令为幂等复用）并确认 `donkey --help` 与 `python -m donkey --help` 均可用；安装后确认覆盖率插件可用（`pytest --help` 中可见 `--cov` 选项，即 `pytest-cov` 已就位）；**本任务 MUST 在 T002b 之后执行**——T003 的 `donkey/__main__.py` 直接 `from donkey.cli.cli_client import main`，缺 `cli_client.py` 时 `donkey --help` 与 `python -m donkey --help` 均会 ImportError

**Checkpoint**: 工程可安装、双入口可执行、工具链就绪

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全部用户故事共享、且不依赖任何单一场景的底层资产

**⚠️ CRITICAL**: 本阶段未完成前，任何用户故事都不能开工

- [X] T008 创建 `donkey/core/exit_codes.py`：`EXIT_CODE_OK=0` / `EXIT_CODE_PATH_NOT_FOUND=1` / `EXIT_CODE_PATH_PERMISSION=2` / `EXIT_CODE_TEMPLATE_GENERATION=3`（P2 预留）/ `EXIT_CODE_BUILTIN_TOOL_GENERATION=4`（P3 预留）/ `EXIT_CODE_SEGMENT_INIT=(1, 10)` 及 F002~F006 段位元组；**F001 段位 `1-10` 内的 `3` / `4` / `5-10`**（`3` 属 F001-P2、`4` 属 F001-P3、`5-10` 为 v1.x 预留）在 P1 只建档，MUST NOT 被代码路径使用；`EXIT_CODE_TEMPLATE_GENERATION=3` / `EXIT_CODE_BUILTIN_TOOL_GENERATION=4` 仅建档；F001-P2 / F001-P3 MUST 复用本文件定义，MUST NOT 重复定义
- [X] T009 [P] 创建 `donkey/core/exceptions.py`：`DonkeyError(Exception)` ← `WorkspaceInitError(DonkeyError)` ← `PathNotFoundError`（docstring 标注 exit code: 1）/ `PathPermissionError`（docstring 标注 exit code: 2）
- [X] T010 [P] 创建 `donkey/core/workspace/templates/manifest.json`：`{"version": 1, "entries": [{"path": "instruction.md", "format": "markdown"}, {"path": "providers/default.toml", "format": "toml"}, {"path": "mcp/mcp.json", "format": "json"}]}`（P1 只建档，MUST NOT 被代码加载）
- [X] T011 [P] 创建 3 个模板源占位：`donkey/core/workspace/templates/instruction.md.txt`、`donkey/core/workspace/templates/providers/default.toml.txt`（含 `default_provider` + `default_model` 键名）、`donkey/core/workspace/templates/mcp/mcp.json.txt` —— **路径 MUST 由条目 `path` 派生**（research.md R-06：第三个源是 `mcp/mcp.json.txt` 而非 `mcp.json.txt`）
- [X] T012 创建 `donkey/core/workspace/init.py` 骨架：`check_path(path: str | Path) -> Path`（接受 str|Path，用 `Path(path).resolve(strict=False)` 解析为绝对路径后返回，本阶段只建骨架）、`check_permission(path: Path) -> None`、`validate_init_request(path, name, force) -> tuple[Path, str, bool]` 三个函数的签名 + docstring + 类型标注（不含 `argparse` / `sys.argv` / `langchain` / `langgraph` / `sqlite3`）；类型标注 MUST 用 `str | None` 形式，**MUST NOT 使用 `typing.Optional`**（ruff `UP` 规则集含 UP007，`Optional[X]` 会被判违规——见 Polish 阶段 T051）
- [X] T013 [P] 创建 `donkey/core/api.py`：`@dataclass(frozen=True) class InitResult`，字段顺序与类型固定为 `workspace_path: Path` / `name: str` / `force: bool` / `templates_loaded: int` / `files_created: int` / `files_skipped: int`（data-model.md §1）；**并同时落下 `init_workspace(path, name=None, force=False) -> InitResult` 的签名与桩实现**（函数体 `raise NotImplementedError`），使 `tests/unit/test_init_workspace.py` 在 US1 之前即可被 pytest 收集、失败形态为"测试失败"而非"收集错误"
- [X] T014 扩展 `donkey/cli/cli_client.py`（骨架已由 T002b 建立）：`_build_parser()` 用 `add_subparsers(dest="command", required=True)` 注册唯一子命令 `init`（位置参数 `path` + 布尔开关 `--force`，**MUST NOT** 提供 `--name`；顶层 parser 的 `prog="donkey"` 由 T002b 设定，**MUST NOT** 在本任务改成其它值——否则 `python -m donkey` 的 usage 提示会退化为 `__main__.py`，spec FR-023「两种入口 MUST 产生完全相同的退出码与输出」不成立）；模块级 `_EXCEPTION_TO_EXIT_CODE` 映射表 = {`PathNotFoundError`: `EXIT_CODE_PATH_NOT_FOUND`, `PathPermissionError`: `EXIT_CODE_PATH_PERMISSION`}（**MUST 从 `donkey.core.exit_codes` 导入这两个常量，MUST NOT 写字面量 `1` / `2`**——退出码不得双源；契约见 `contracts/exit-codes.md` §3；基类不登记，未登记子类兜底 1）；`main()` 的 `init` 分支留待 T019 实现（**T002b ~ T019 窗口内 `donkey init` 尚未接线，MUST NOT 作为功能验收证据——验收以 T020 为准**）

**Checkpoint**: 底层资产与骨架就位，尚无任何可用行为

---

## Phase 3: User Story 1 - 新建 workspace 根目录 (Priority: P1) 🎯 MVP

**Goal**: 合法路径下 `donkey init <PATH>` 退出码 0，workspace 根目录被创建，并输出一行结果摘要

**Independent Test**: 对父目录已存在的新路径执行 `donkey init <PATH>` → 退出码 0、目录存在、摘要含绝对路径与名称

### Tests for User Story 1 (TDD) ⚠️

> **先写测试并确认失败**

- [X] T015 [US1] 在 `tests/unit/test_init_workspace.py` 写 `test_init_workspace_creates_root_dir`：全新路径 → 目录被创建；`InitResult.files_created == 0` / `files_skipped == 0` / `templates_loaded == 0`；`workspace_path` 为绝对路径；追加断言：分别以 **str** 与 **Path** 两种形态传入目标路径调用 `init_workspace` → 两者均成功，且 `workspace_path` 均为**绝对路径**（spec FR-005「path MUST 接受字符串与路径对象两种形态」；同时覆盖 FR-024 的"绝对路径解析成功"类别）
- [X] T016 [US1] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_1_new_workspace`：以子进程跑 `donkey init <tmp_path>/ws` → 退出码 0 且目录存在（**黑盒**：不 import `donkey.*` 业务代码；命令解析用 `shutil.which("donkey")`，取不到则回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**（由 `tests/e2e/phase/verify_phase_f001_p1.py` 自身位置向上推导），确保被测对象是当前工作树的代码）；并在同一文件中建立**供 US2~US7 六个场景复用的命令解析辅助函数**（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`，回落时以仓库根为工作目录，由脚本自身位置向上推导），后续六个场景一律调用它；**辅助函数 MUST 对 PATH 上的 `donkey` 做「当前工作树归属」校验**——解析该命令对应的 `donkey` 包安装位置（`donkey.__file__` 所在的包目录），若其**不在当前仓库根之内**（即 PATH 上是已安装的其它版本或另一个工作树），MUST 视为该命令**不可用**并按回落分支处理，避免验收脚本测到错误的代码（spec FR-025；plan 风险表「验收脚本可能测到 PATH 上的另一份 donkey 安装」）；**辅助函数 MUST 在发生回落时打印一次显式告警**（如「环境性未验证：控制台脚本不可用，已回落 `python -m donkey`」）——MUST NOT 静默回落（Setup 的 T007 已保证两条入口均可用，该分支只应出现在未安装环境）；追加断言：以子进程分别经**控制台脚本** `donkey` 与**模块入口** `[sys.executable, "-m", "donkey"]` 对同一目标路径各执行一次 → 两者**退出码相同**且 **stdout 摘要逐字相同**（spec FR-023「两种入口 MUST 产生完全相同的退出码与输出」）；控制台脚本不可用时只跑模块入口，**MUST 打印显式告警**（同上），MUST NOT 静默跳过该对比断言；**追加 stderr 对比断言**：两条入口各执行一次**参数用法错误**（如 `init` 缺必填位置参数）→ 两者 **stderr 的 usage 提示逐字相同**（两条入口的 `prog` 均须为 `donkey`；若实现侧漏设 `prog="donkey"`，`python -m donkey` 的 usage 前缀会是 `__main__.py`，此断言即失败——spec FR-023 / FR-002 / research.md R-01）；MUST NOT 新增 e2e 场景函数（本文件仍为 7 个 `test_scenario_*`）

### Implementation for User Story 1

- [X] T017 [US1] 在 `donkey/core/workspace/init.py` 实现 `validate_init_request(path, name, force) -> tuple[Path, str, bool]`：串联 `check_path` → `check_permission` → 名称定夺（**最小 + 完整**口径：`name` 为 `None` / 空串 → 取解析后路径的末段名，MUST 用路径对象的末段名属性，MUST NOT 手写字符串切分；`name` 为**非空串** → MUST 以该值为准，spec FR-005 / FR-017——库 API 通道的名称优先规则在本任务一次性落地，MUST NOT 把 `name` 形参忽略或静默丢弃；CLI 通道永不传该参数，故命令行名称恒由路径派生）；MUST NOT 把"目标已存在"当错误
- [X] T018 [US1] 在 `donkey/core/api.py` 用真实实现替换 T013 落的桩并实现 `init_workspace(path, name=None, force=False) -> InitResult`：调 `validate_init_request` → `abs_path.mkdir(exist_ok=True)`（MUST NOT 补建缺失的父目录——父目录缺失已在 `check_path` 阶段按 spec FR-009 判为路径类错误并拒绝）→ 返回 `InitResult`（三个计数恒 0）
- [X] T019 [US1] 在 `donkey/cli/cli_client.py` 实现 `main(argv: list[str] | None = None) -> int` 的 `init` 分支：**import 形态 MUST 固定为** `import donkey.core.api as core_api` + 调用 `core_api.init_workspace(...)`（**MUST NOT** 用 `from donkey.core.api import init_workspace`——那样 T022 的打桩目标 `donkey.core.api.init_workspace` 将不生效，未登记异常子类兜底分支会假绿）→ 打印单行摘要 `[donkey init] workspace=... name=... force=... templates=... created=... skipped=...` 到 stdout → 返回 `EXIT_CODE_OK`；`except WorkspaceInitError` 分支按 `_EXCEPTION_TO_EXIT_CODE` 映射退出码并把错误信息写 stderr（MUST NOT 用 `except Exception` 吞掉）
- [X] T020 [US1] 跑 `pytest tests/unit/test_init_workspace.py -v` 与 `pytest tests/e2e/phase/verify_phase_f001_p1.py -v`，确认 US1 相关用例全绿

**Checkpoint**: US1 可独立交付（命令可用 + 根目录落地）——**MVP 达成点**

---

## Phase 4: User Story 2 - 路径不合法时给出明确指引 (Priority: P2)

**Goal**: 父目录不存在 / 路径非法 / 根路径 → 退出码 1，错误信息含可识别标识，且不创建任何目录

**Independent Test**: 对父目录不存在的路径、对 `/` 分别执行 `donkey init` → 均退出码 1，stderr 含 "PathNotFoundError" 或 "父目录不存在"

### Tests for User Story 2 (TDD) ⚠️

- [X] T021 [US2] 在 `tests/unit/test_init_workspace.py` 写 5 个用例：`test_check_path_nonexistent_parent`（父目录不存在 → `PathNotFoundError`）、`test_check_path_resolve_relative`（相对路径在 cwd 下父目录不存在 → `PathNotFoundError`）、`test_check_path_root_path`（`/` → `PathNotFoundError`，因为末段名为空）、`test_check_path_nul_character`（含 NUL → `PathNotFoundError`，注意 `resolve()` 抛的是 `ValueError`，research.md R-05）、`test_check_path_target_is_file_or_parent_is_file_or_empty_path`（目标为普通文件 → `PathNotFoundError` 且 MUST NOT 覆盖该文件；父目录是文件 → `PathNotFoundError`；空字符串路径 → `PathNotFoundError` 且 MUST NOT 把进程工作目录误当成 workspace 根——spec FR-030 第 5 轮口径：这三项由同一个用例一并覆盖，不要求各自独立成例）；**追加断言组（MUST NOT 新增测试函数，core 层仍为 17 个）**：`test_check_path_nonexistent_parent` 内追加「抛错后该缺失父目录**仍不存在**」（`not missing_parent.exists()`）——覆盖 spec US2 的 Given/When/Then 场景 1「**不会**创建任何目录（包括缺失的父目录）」与 SC-003 的「不产生任何新建目录（含缺失的父目录）」，确保 FR-009（`mkdir(parents=True)` 回归）可被测出（spec FR-009 / SC-003 / US2 场景 1）
- [X] T022 [P] [US2] 新建 `tests/unit/test_cli_client.py` 写 3 个 CLI 层用例：`test_main_without_subcommand_exits_1`（缺子命令 → `pytest.raises(SystemExit)` 且 `excinfo.value.code == 1`；注意 `DonkeyArgumentParser.error()` 走 `self.exit(1, ...)`，是抛 `SystemExit` 而**不是**返回 `1`）、`test_main_missing_path_argument_exits_1`（缺必填位置参数 → 同样断言 `code == 1`；并捕获 stderr 断言其含用法提示（usage），作为参数用法类失败的用户可执行下一步（spec FR-019 / SC-012 的参数用法类，与 US7 的 Given/When/Then 场景 2 同一口径）—— **并在 `test_main_missing_path_argument_exits_1` 之后追加断言组（`MUST NOT` 新增测试函数，CLI 层仍为 3 个）**：`main(["init", "<路径>", "--name", "alice"])` → `pytest.raises(SystemExit)` 且 `excinfo.value.code == 1`（spec FR-024 的「命令行用法错误（缺少子命令 / 缺少必填位置参数 / **未知参数**）→ 退出码 1」三个子项 MUST 全部在**单测层**有落点——此前「未知参数」仅出现在 e2e 场景 7，单元测试层无落点；SC-008 与 FR-024 逐字镜像，镜像关系不得破坏）、`test_main_unregistered_exception_falls_back_to_1`（构造一个未登记进 `_EXCEPTION_TO_EXIT_CODE` 的 `WorkspaceInitError` 子类，并让 `init_workspace` 抛出该子类——例如用 `monkeypatch.setattr("donkey.cli.cli_client.core_api.init_workspace", fake)` 打桩（打桩目标依赖 T019 固定的 `import donkey.core.api as core_api` 形态；**MUST NOT** 打桩 `donkey.core.api.init_workspace`——若 cli 侧是 `from ... import` 绑定，该打桩不生效、本用例会假绿）——再断言 `main(["init", "<路径>"])` **返回 1**，这一条走正常返回而非 `SystemExit`）
- [X] T023 [US2] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_2_path_not_found`：父目录不存在 → 退出码 1 且 stderr 含 "PathNotFoundError" 或 "父目录不存在"，**且含一条用户可执行的下一步（建目录 / 换路径）**（spec US2 的 Given/When/Then 场景 2 / FR-019）；**追加断言：执行后该缺失的父目录 MUST 仍不存在**（`not missing_parent.exists()`）——覆盖 spec US2 的 Given/When/Then 场景 1「**不会**创建任何目录（包括缺失的父目录）」与 SC-003「不产生任何新建目录（含缺失的父目录）」，使 FR-009 的 `mkdir(parents=True)` 回归可被黑盒测出（spec FR-009 / SC-003）；追加断言：对 `/` 执行 → 退出码 `1`（根目录不是合法 workspace 根），且 `/` 下**不**出现任何新建内容；追加断言：stderr 首行 MUST 以 `[donkey init] 失败：` 开头（`contracts/cli-contract.md` §3.2 冻结格式）；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 2

- [X] T024 [US2] 在 `donkey/core/workspace/init.py` 的 `check_path` 补齐错误分支：`resolve()` 抛 `ValueError`（非法字符）**或 `OSError`**（解析失败）→ `PathNotFoundError`（research.md R-05：两类 MUST 一并捕获，统一转路径类错误）；`abs_path.parent` 不存在 → `PathNotFoundError`；`abs_path.name` 为空（文件系统根 / 盘符根 / UNC 共享根）→ `PathNotFoundError`；空字符串路径 → **MUST 在 `resolve()` 之前判空**并抛 `PathNotFoundError`——`Path("").resolve()` 返回进程工作目录（末段名非空），若先 resolve 再判末段名，空路径会被误判为合法（spec FR-030 / Edge Cases「传入空字符串路径 → 不得把进程工作目录误当成 workspace 根」）；**「空」的判定 MUST 只认长度为 0 的空串**（纯空白串如 `"   "` 按普通路径处理——其末段名非空；`Path("")` 已被 `pathlib` 折叠为 `"."`，库 API 通道传入 `Path("")` 等价于 `"."`，CLI 通道始终传原始字符串）；**`check_path` 内的全部 stat 类调用**（`exists()` / `is_dir()` / `stat()`）**MUST 置于 `try/except OSError → PathNotFoundError` 内**——Python 3.11+ 的 `Path.exists()` 对超长路径会**抛出** `OSError(ENAMETOOLONG)`（`_IGNORED_ERRNOS` 仅含 ENOENT / ENOTDIR / EBADF / ELOOP），不返回 False，若不捕获将漏出未捕获异常堆栈（违反 spec FR-030 / 契约 C-06）；`check_path` MUST 无副作用（不写文件、不建目录、不改任何状态），其返回值 MUST 可被调用方直接使用（spec FR-016）
- [X] T025 [US2] 在 `donkey/core/workspace/init.py` 的 `check_path` 补齐"目标存在但不是目录"与"父目录是文件"两个分支 → 均为 `PathNotFoundError`（MUST NOT 覆盖或删除该文件）；实现时同样覆盖"悬空符号链接"与"路径过长"两个低频分支（FR-030 要求实现覆盖，但不要求独立测试）；**四个分支的判据 MUST 明确**：①「目标存在但不是目录」→ **目标已存在**（`p.exists()` 为真）**且** `p.is_dir()` 为假即拒（**目标尚不存在**属正常路径，MUST NOT 在本分支拒绝；**MUST NOT** 先覆盖或删除该文件）；②「父目录是文件」→ `parent.is_dir()` 为假即拒；③「悬空符号链接」→ MUST 在 `resolve()` **之前**对**原始输入路径**判定——`os.path.islink(p)` 为真**且** `p.exists()` 为假即拒（**MUST NOT** 用 `Path.resolve(strict=False)` 之后的路径做该判定：resolve 会把悬空链接静默解析成目标路径，谓词恒为假 → 该分支永不可达）；④「路径过长」→ **由 T024 的统一 `except OSError` 覆盖**（`Path.exists()` / `Path.is_dir()` / `Path.stat()` 在超长路径上抛 `OSError(ENAMETOOLONG)` → `PathNotFoundError`），MUST NOT 另设捕获点（避免两处 try/except），亦**MUST NOT** 依赖 `resolve()` 抛错来覆盖——实测 `Path(超长).resolve(strict=False)` **正常返回、不抛异常**，仅靠该捕获点该分支永不可达；**判据作用对象 MUST 明确**：① ② 作用于**解析后的绝对路径** `abs_path`（目标是指向目录的符号链接时按 `abs_path` 判定，不拒），③ 作用于**原始输入路径**；①②③ 中的 `exists()` / `is_dir()` 调用 MUST 置于 T024 统一的 `try/except OSError` 内
- [X] T026 [US2] 打磨 `donkey/core/workspace/init.py` 中 `PathNotFoundError` 的错误文案：消息含可识别标识（如"父目录不存在：<路径>"、根目录场景含"根目录"），满足 stderr 断言与 spec FR-019（扩写后版本）；消息 MUST 同时含**一条用户可执行的下一步**（路径类："建目录 / 换路径"），以满足 spec FR-019 的"面向用户的三类失败 MUST 带一条用户可执行的下一步"与 spec SC-012（同步限定为面向用户的三类失败：路径类 / 权限类 / 参数用法类）
- [X] T027 [US2] 在 `donkey/cli/cli_client.py` 确认 `DonkeyArgumentParser.error()` 走 `self.exit(1, ...)`（用法提示写 stderr），且 `main()` 对未登记的 `WorkspaceInitError` 子类兜底返回 `1`（MUST NOT 用 `except Exception` 吞掉未分类错误，spec FR-018）；用法错误与未登记 `WorkspaceInitError` 子类兜底的 stderr 消息 MUST 含可识别标识；**参数用法类**消息 MUST 附用法提示（usage）作为用户可执行的下一步（spec FR-019 / SC-012）；未登记异常子类的**内部兜底**消息不要求带下一步；**本层 `except` 分支打印的失败消息 MUST 以 `[donkey init] 失败：` 开头、单行起头**（`contracts/cli-contract.md` §3.2 冻结格式；argparse 自身的 usage + error 输出不受此格式约束）
- [X] T028 [US2] 跑 `pytest tests/unit/test_init_workspace.py -v`（US2 的 5 个用例）、`pytest tests/unit/test_cli_client.py -v`（CLI 层 3 个用例）与 `pytest tests/e2e/phase/verify_phase_f001_p1.py -v`（场景 2），确认全绿

**Checkpoint**: US1 + US2 均可独立验证

---

## Phase 5: User Story 3 - 权限不足时说清缺哪种权限 (Priority: P3)

**Goal**: 权限不足 → 退出码 2，错误信息同时指明缺失的权限种类与对应路径，且不创建任何目录

**Independent Test**: `chmod 555` 父目录后执行 `donkey init` → 退出码 2，stderr 含权限标识与路径

### Tests for User Story 3 (TDD) ⚠️

- [X] T029 [US3] 在 `tests/unit/test_init_workspace.py` 写 3 个用例：`test_check_permission_readonly_parent`（`chmod 0o555` 父目录 → `PathPermissionError`，消息 MUST 同时含缺失的权限种类（"写权限"）与对应路径（该只读父目录路径））、`test_check_permission_existing_missing_read`（已存在目录 `chmod 0o333` → `PathPermissionError`，消息 MUST 同时含缺失的权限种类（"读权限"）与对应路径（该目录路径））、`test_check_permission_ok`（正常路径 → 返回 `None`）；用例内 MUST 用 try/finally 恢复目录权限；**权限模拟 MUST NOT 依赖特权账号**——`0o555` 目录不含任何写位，按 POSIX 语义**即使以 root 运行 `os.access(dir, W_OK)` 亦为 False**（`research.md` R-04），故该模拟在 root 下同样成立；MUST NOT 用 root-only 目录模拟
- [X] T030 [US3] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_3_permission_denied`：只读父目录 → 退出码 2 且 stderr 含 "PathPermissionError" 或 "权限"，**且 MUST 同时含缺失的权限种类（"写权限"）与对应路径（该只读父目录路径）**（spec FR-015 / SC-004），**且含一条用户可执行的下一步（调整权限）**（spec US3 的 Given/When/Then 场景 2 / FR-019）；**追加断言：执行后目标目录 MUST 未被创建**（`not ws.exists()`）——覆盖 spec US3 的 Given/When/Then 场景 1「且不创建任何目录」；finally 恢复 `0o755`；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 3

- [X] T031 [US3] 在 `donkey/core/workspace/init.py` 实现 `check_permission(path: Path) -> None`：用 `os.access(path, mode)`；目标**不存在** → 校验**父目录**的 `W_OK | X_OK`（能否在其中创建子项）；目标**已存在** → 校验**目标自身**的 `R_OK | W_OK | X_OK`；任一不足 → `PathPermissionError`，消息 MUST 同时含缺失的权限种类（读/写/执行）与对应路径，并 MUST 含**一条用户可执行的下一步**（权限类："调整权限"），以满足 spec SC-012 与 spec FR-019（扩写后版本，"面向用户的三类失败"含权限类）；`check_permission` MUST 无副作用（不写文件、不建目录、不改任何状态），其判定结果通过**正常返回**（权限充足）或**抛出 `PathPermissionError`**（权限不足）表达（spec FR-016 第 5 轮订正后口径）
- [X] T032 [US3] 在 `donkey/core/workspace/init.py` 的 `validate_init_request` 中接入 `check_permission`（MUST 在目录创建之前），并跑 US3 的 3 个单测 + 验收场景 3 确认全绿

**Checkpoint**: US1~US3 均可独立验证；失败面覆盖完毕

---

## Phase 6: User Story 4 - 重复执行不报错、不破坏 (Priority: P4)

**Goal**: 已存在 workspace → 退出码 0，不报错、不删除、不覆盖任何已有内容

**Independent Test**: 建好含用户文件的 workspace 后再执行 `donkey init` → 退出码 0，文件内容与 mtime 均不变

### Tests for User Story 4 (TDD) ⚠️

- [X] T033 [US4] 在 `tests/unit/test_init_workspace.py` 写 `test_init_workspace_existing_is_not_error`：预先建好含用户文件的目录 → `init_workspace` 不抛异常、返回 `files_created == 0`、用户文件内容与 mtime 不变
- [X] T034 [US4] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_4_idempotent_no_force`：已存在 workspace → 退出码 0，且 MUST NOT 出现"已存在"类错误；追加断言：对同一已存在 workspace **连续执行两次** `donkey init` → 两次均退出码 `0`，且已有用户文件的内容与 **mtime** 在两次执行之间保持不变（spec SC-005）；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 4

- [X] T035 [US4] 在 `donkey/core/api.py` 保证幂等：`mkdir(exist_ok=True)`（MUST NOT 补建缺失的父目录，spec FR-009）；MUST NOT 删除 / 覆盖 / 改写任何已存在内容；MUST NOT 写入任何模板文件（spec FR-028）
- [X] T036 [US4] 在 `donkey/core/workspace/init.py` 复核 `check_path` 不会因"目标已存在"抛错（幂等设计：已存在不是错误），并跑 US4 的单测 + 验收场景 4 确认全绿

**Checkpoint**: 幂等语义成立（业务验收 AC-3 的 P1 部分）

---

## Phase 7: User Story 5 - `--force` 先被记住但不误伤 (Priority: P5)

**Goal**: `--force` 被接受、被记录、被回显，但本阶段不触发任何删除或重置

**Independent Test**: 对已存在 workspace 执行 `donkey init <ws> --force` → 退出码 0，已有内容未被删除或覆盖

### Tests for User Story 5 (TDD) ⚠️

- [X] T037 [US5] 在 `tests/unit/test_init_workspace.py` 写 `test_init_workspace_force_recorded_not_applied`：`force=True` → `InitResult.force is True`，且目录内容不变（未发生重置）
- [X] T038 [US5] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_5_force_no_reset_yet`：已存在 workspace + `--force` → 退出码 0、摘要含 `force=true`、已有内容未被删除或覆盖；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 5

- [X] T039 [US5] 在 `donkey/cli/cli_client.py` 把 `--force` 透传给 `init_workspace` 并在摘要回显；本阶段 MUST NOT 实现任何重置 / 删除逻辑（重置属 F001-P2 的 `render_templates`），并跑 US5 的单测 + 验收场景 5 确认全绿

**Checkpoint**: US1~US5 均可独立验证

---

## Phase 8: User Story 6 - 清楚知道这一步只到哪 (Priority: P6)

**Goal**: 本阶段不加载模板清单、不生成模板内容；清单 / 模板源缺失或损坏不导致失败

**Independent Test**: 移走模板清单后执行 `donkey init` → 仍退出码 0，结果目录存在且不含模板文件，三个计数为 0

### Tests for User Story 6 (TDD) ⚠️

- [X] T040 [US6] 在 `tests/unit/test_init_workspace.py` 写 `test_init_workspace_does_not_load_manifest`：把 `donkey/core/workspace/templates/manifest.json` 临时改名 → `init_workspace` 仍成功、`templates_loaded == 0`、目标目录内无任何文件（finally 改名还原）；追加覆盖：再临时移走任一模板源占位（如 `donkey/core/workspace/templates/instruction.md.txt`）→ `init_workspace` 仍成功、`templates_loaded == 0`、目标目录内无任何文件（finally 还原）；**模板资产路径 MUST 由仓库源树定位**（`Path(__file__).resolve().parents[2] / "donkey/core/workspace/templates"`），MUST NOT 依赖已安装包位置——若以非 editable 方式安装，改名会落到 site-packages 上（污染环境或因只读而失败）；MUST NOT 新增**第 2 个**测试函数——追加覆盖 MUST 在 `test_init_workspace_does_not_load_manifest` 内扩写断言组（core 层用例数仍为 17）
- [X] T041 [US6] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_6_p1_no_template_rendering`：退出码 0 + `ws.is_dir()`；追加断言：stdout 摘要 MUST 含 `templates=0 created=0 skipped=0`（spec FR-020 / US6 的 Given/When/Then 场景 3）；**追加断言：目标目录内 MUST 无任何文件**（`list(ws.iterdir()) == []`）——兑现 plan G14「US6 单测与 e2e 场景 6 断言目录内无任何文件」与宪法 N-01（workspace 内不出现任何 Python 入口文件）；MUST NOT 断言存在 `instruction.md` / `providers/default.toml` 等模板文件；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 6

- [X] T042 [US6] 代码审查 `donkey/core/api.py` 与 `donkey/core/workspace/init.py`：MUST NOT 存在任何清单加载 / 模板渲染 / sqlite3 schema 构造的代码路径（`grep -rn "manifest\|render_templates\|sqlite3" donkey/core/ --exclude-dir=templates` 只允许命中非模板资源的代码路径；模板资源本身不参与该检查）
- [X] T043 [US6] 复核 `InitResult` 不变量：P1 阶段 `templates_loaded` / `files_created` / `files_skipped` MUST 恒为 `0`（data-model.md §1），并跑 US6 的单测 + 验收场景 6 确认全绿

**Checkpoint**: 范围边界成立，F001-P2 的入口条件（模板清单 3 条 + 3 个同名 `.txt` 源）未被破坏

---

## Phase 9: User Story 7 - workspace 的名字就是它的位置 (Priority: P7)

**Goal**: 名称恒取路径末段；CLI 不接受独立命名参数；摘要同时回显绝对路径与名称

**Independent Test**: 对 `.../my-agent` 执行 `donkey init` → 名称 == `my-agent`；误传 `--name alice` → 退出码 1

### Tests for User Story 7 (TDD) ⚠️

- [X] T044 [US7] 在 `tests/unit/test_init_workspace.py` 写 5 个测试函数（6 个用例 —— 第 6 个用例为「末段名带尾部分隔符」，内嵌于 `test_init_workspace_accepts_arbitrary_basename`，MUST NOT 新增测试函数）：`test_init_workspace_name_from_basename`（名称 == 路径末段）、`test_init_workspace_name_empty_falls_back_to_basename`（库 API 显式传 `name=""` → 回退为 basename）、`test_init_workspace_explicit_name_wins`（库 API 显式传 `name="alice"` → `InitResult.name == "alice"`，同时确认 `workspace_path` 仍由 path 决定）、`test_init_workspace_rejects_root_path`（`/` → `PathNotFoundError`，末段名为空）、`test_init_workspace_accepts_arbitrary_basename`（末段名含空格 / Unicode（如 `我的 工作区`）→ `init_workspace` 成功、`InitResult.name` **原样等于**该末段名——不校验、不改写、不拒绝，spec FR-003 / FR-024；追加断言：末段名带尾部分隔符（`.../ws/`）→ 名称仍等于 `ws`，与不带分隔符等价（spec Edge Cases「路径类」组；由 FR-003 的末段名派生隐式覆盖））
- [X] T045 [US7] 在 `tests/e2e/phase/verify_phase_f001_p1.py` 写 `test_scenario_7_name_derived_from_path`：摘要含末段名与绝对路径；追加断言 `donkey init <ws> --name alice` → 退出码 1（参数用法错误归 `1`，不是 argparse 默认的 `2`），且 stderr MUST 含用法提示（usage）作为一条用户可执行的下一步（spec FR-019 / SC-012 的参数用法类）；再追加断言：末段名含空格 / Unicode 的路径（如 `.../我的 工作区`）→ 退出码 `0` 且摘要中的名称**原样保留**该末段名（spec US7 的 Given/When/Then 场景 4）；MUST NOT 新增 e2e 场景函数——本文件仍为 7 个 `test_scenario_*`；命令解析 MUST 复用 US1 阶段建立的辅助函数（`shutil.which("donkey")` → 回落 `[sys.executable, "-m", "donkey"]`；**回落时 MUST 以仓库根为工作目录**，由脚本自身位置向上推导），MUST NOT 各自重复实现或遗漏该约束

### Implementation for User Story 7

- [X] T046 [US7] 在 `donkey/core/workspace/init.py` 复核 CLI 通道的名称派生：名称恒取解析后路径的末段名（CLI 通道永不传 `name`）；末段名一律原样接受，MUST NOT 对 basename 做任何字符白名单 / 正则 / 长度校验（spec FR-003 新增 MUST）
- [X] T047 [US7] 在 `donkey/core/workspace/init.py` 复核库 API 侧的名称定夺规则与 T017 落地的一致（`name` 为 `None` / 空串 → 解析后路径末段名；`name` 为非空串 → 采用该值，spec FR-005 / FR-017）；并确认 CLI 通道与库 API 通道的名称来源互不混淆（CLI 侧的 basename 边界收紧见 T046）
- [X] T048 [US7] 在 `donkey/cli/cli_client.py` 复核参数面只有 `path` + `--force`：MUST NOT 存在 `--name` 或任何等价入口；误传 `--name` → argparse 报未知参数 → 退出码 1（`DonkeyArgumentParser.error()` 已改写）
- [X] T049 [US7] 复核摘要输出符合 `contracts/cli-contract.md` §3.1：单行含 workspace 绝对路径 + name + force + templates + created + skipped
- [X] T050 [US7] 跑 US7 的 5 个单测（5 个测试函数；尾部分隔符用例内嵌于既有函数）+ 验收场景 7，确认全绿；并跑一次完整 `pytest tests/e2e/phase/verify_phase_f001_p1.py -v` 确认 7 个场景全绿

**Checkpoint**: 全部 7 个用户故事均可独立验证

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的收口与质量门禁

- [X] T051 [P] 跑 `ruff check donkey/ tests/`（配置见 `pyproject.toml`）→ 零 error；修掉全部 E/F/I/UP 告警（含 import 排序与未使用的 import）；类型标注一律用 `str | None` 形式，MUST NOT 出现 `typing.Optional`（ruff `UP` 规则集含 UP007，详见 T012）
- [X] T052 [P] 跑 `mypy donkey/ tests/`（`pyproject.toml` 中 `strict = true` / `explicit_package_bases = true` / `mypy_path = "."` / `files = ["donkey"]`）→ 零 error 零 warning（`donkey/` 全量严格；`tests/` 按 T005 的 `[[tool.mypy.overrides]] module = "tests.*"` 放宽项执行——该 override 的命中**依赖** T005 的 `explicit_package_bases` + `mypy_path`，缺任一项则 `strict` 全量作用于测试层、必然报 `no-untyped-def`）
- [X] T053 [P] 分层与永不使用清单自检（quickstart.md §5）：`grep -rnE "import (argparse|click|typer)|sys\.argv" donkey/core/` 无命中；`grep -rnE "^\s*(import|from) (langchain|langgraph|sqlite3)" donkey/cli/` 无命中；`grep -rnE "langsmith" donkey/` 无命中；**追加入口点位置检查**（spec SC-010 第三子项「可执行入口点不位于核心层」/ 宪法 N-03）：`ls donkey/core/` MUST NOT 出现 `__main__.py` / `cli*.py`，且 `pyproject.toml` 的 `[project.scripts] donkey` MUST 指向 `donkey.cli.*`
- [X] T054 在 `tests/e2e/phase/verify_phase_f001_p1.py` 为 7 个场景逐一加耗时断言：每个场景测量单次 `donkey init` 的耗时并断言 ≤ 10 秒（spec SC-013，纯本地文件系统操作、无网络依赖；阈值留足 CI 抖动余量），超时即判定该场景失败
- [X] T055 跑覆盖率验证：`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` → `donkey.core` 行覆盖率 ≥ 80%（spec SC-016 / 宪法 §4.6 / plan G12）；该命令 MUST 只度量 `tests/unit/`（与 plan G13 的 `python_files` 配置无关 —— 覆盖率命令显式限定路径为 `tests/unit/`，即使 pytest 全局已声明收集 e2e 脚本，该命令也不会收集它），MUST NOT 把 e2e 黑盒脚本（`tests/e2e/phase/verify_phase_f001_p1.py`）计入该度量，MUST NOT 把 `--cov` / `--cov-fail-under` 写入 pytest 全局 `addopts`（否则 e2e 单独运行会把覆盖率拉到 0 而误报失败）；不达标时 MUST 补单测而非下调阈值
- [X] T056 [P] 跑 quickstart.md §1~§6 全部命令并记录结果：单测 20 个用例全绿（core 层 17 + CLI 层 3）、验收脚本 7 场景全绿、ruff / mypy 零 error、手动冒烟 6 条退出码符合预期；并确认 `pytest tests/` 一次收齐 unit + e2e 三层（7 个 e2e 场景被真正收集，plan G13 / research.md R-07）
- [X] T057 逐条核对 `specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md` 的 31 条 FR 与 16 条 SC 与实现的对应关系（spec 内「需求追溯矩阵」），把未覆盖项补齐或记录原因；**核对 FR-021 / FR-022（分层边界）时注意其落点是 T053 的分层自检，而非 7 个 e2e 场景**（spec 追溯矩阵该行已于 2026-10-22 订正为「场景 1 ~ 场景 5、场景 7 + 分层静态检查（T053）」，本任务按订正后的口径核对即可）
- [X] T058 确认 P1 未触发的退出码（`3` / `4` / `5-10`）没有任何代码路径引用——只允许出现在 `donkey/core/exit_codes.py` 的建档定义中，且 `donkey/cli/cli_client.py` 的 `_EXCEPTION_TO_EXIT_CODE` 只含 1 / 2 两项
- [X] T059 [P] 同步仓库级文档 `harness/features/README.md`（3 处，MUST NOT 改动其它章节）：① §12.2 提示词文件 ↔ Phase 映射表**上方「落地状态」段落**——把「已就绪 3 个——F001-P1 / F001-P2 / F001-P3」改为「**已完成 1 个**（F001-P1）+ **已就绪 2 个**（F001-P2 / F001-P3）」；② §4.3 F001-P1 的「**绝对不做**」条目处追加一行，记录"C1 工作流文件 Deferred（仓库级资产，已按宪法 §6.3 登记临时例外 E-01）"的结论；③ §3.x「manifest 分阶段追加」表中 F001-P1 行的括注「P1 只加载清单、不渲染」改为「**P1 只建档清单（3 条），不加载、不解析、不渲染**」——原文与同文件 §4.3「本 Phase 不实现 `load_template_manifest`」及 spec FR-029「MUST NOT 加载或解析模板清单」冲突（README 内部自相矛盾），本轮订正
- [X] T060 [P] 同步上游权威副本 `harness/features/feature001_phase001_cli_validation.md`：**① 复核（不得无谓改写）**——上游 §3 的 `InitResult.name` 字段注释、§4.1 `init_workspace` docstring 的 `name` 条目、§4.2 `validate_init_request` 行为第 3 步三处**已于 2026-10-22 按 spec FR-005 / FR-006 / FR-017 同步**（口径：`name` 为 `None` / 空串 → 取解析后路径末段名；为非空串 → 以该值为准；v1 的 CLI 通道恒不传该参数）——本任务 MUST 逐处核对与 spec / data-model §1 §3 / contracts/library-api.md §1~§3 是否一致，已一致则只做确认，MUST NOT 重写；**② 订正残留漂移（唯一 MUST 的实质改动）**——上游 §4.1 的 `init_workspace` 代码样例仍写「创建 workspace 根目录（`parents=True, exist_ok=True`）」与 `abs_path.mkdir(parents=True, exist_ok=True)`，与 spec FR-009「MUST NOT 自动创建缺失的父目录」直接冲突（父目录缺失已在 `check_path` 阶段按 FR-009 判为路径类错误并拒绝），故 MUST 改为「（`exist_ok=True`，MUST NOT 补建缺失的父目录——父目录缺失已在 `check_path` 阶段按 spec FR-009 判为路径类错误并拒绝）」与 `abs_path.mkdir(exist_ok=True)`；③ 该文件其余内容（§0~§2 / §3.1~§3.3 / §4.2 除第 3 步外的部分 / §4.3~§4.6 / §5~§12）一字不动；④ 改后在 `specs/001-donkey-init-workspace/phase-1-cli-validation/checklists/requirements.md` 的 Notes 段**末尾追加 1 条**：「上游提示词 `harness/features/feature001_phase001_cli_validation.md` 的 `name` 语义已按 spec FR-005 / FR-017 同步（2026-10-22）；其 §4.1 的 `mkdir(parents=True)` 已按 spec FR-009 订正为 `mkdir(exist_ok=True)`（2026-10-22）」——其中 `name` 语义那半句**已存在**于该 Notes 段末尾（2026-10-22 追加），本任务**只追加 `mkdir(parents=True)` 订正那半句**，MUST NOT 重复追加已有的 `name` 语义记录

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始（**内部次序**：T002b MUST 在 T007 之前——T007 的双入口 `--help` 安装验证依赖 `cli_client.py` 最小骨架）
- **Foundational (Phase 2)**: 依赖 Setup —— **阻塞全部用户故事**
- **User Stories (Phase 3~9)**: 全部依赖 Foundational 完成
- **Polish (Phase 10)**: 依赖全部用户故事完成 —— 覆盖率验证任务（T055）依赖全部单测存在

### User Story Dependencies

- **US1 (P1)**: 依赖 Foundational —— 无其它故事依赖
- **US2 (P2)**: 依赖 Foundational；实现落在 `check_path` 的错误分支，与 US1 成功路径互补；CLI 层单测 `tests/unit/test_cli_client.py`（T022）依赖 Foundational 已就位的 `DonkeyArgumentParser` 与 `_EXCEPTION_TO_EXIT_CODE`（T014），与 `tests/unit/test_init_workspace.py` 不同文件、可并行
- **US3 (P3)**: 依赖 Foundational；实现落在 `check_permission`
- **US4 (P4)**: 依赖 US1（幂等建立在"能建目录"之上）
- **US5 (P5)**: 依赖 US1 + US4（`--force` 的"不误伤"以幂等为前提）
- **US6 (P6)**: 依赖 US1；边界复核
- **US7 (P7)**: 依赖 US1 + US2（名称派生建立在路径解析之上）；US7 新增 1 个测试函数（2 个断言组：basename 合法性 + 末段名带尾部分隔符，后者内嵌于 `test_init_workspace_accepts_arbitrary_basename`）依赖 US1 的 `init_workspace` 落地；US7 的名称派生**收紧**（T046）依赖 US1 已落地的最小派生（T017）；US7 对库 API `name` 优先规则的**复核**（T047）依赖 US1 已落地的完整名称定夺（T017）
- 全部故事共享 `donkey/core/workspace/init.py`、`donkey/core/api.py`、`donkey/cli/cli_client.py` 三个文件 → **同一时刻只推进一个故事的实现任务**，避免同文件冲突

### Within Each User Story

- 测试 MUST 先写并确认失败，再写实现
- 校验层（`check_path` / `check_permission`）→ 编排层（`validate_init_request`）→ 门面层（`init_workspace`）→ 客户端层（`main`）
- 故事完成后跑该故事的单测 + 对应验收场景
- 每个检查点停下来独立验证

### Parallel Opportunities

- Setup 内 `[P]` 任务可并行（T002 / T003 / T002b——三者写不同文件）；T004~T006 均改写 `pyproject.toml`，**必须串行**；**T007 MUST 在 T002b 之后执行**（双入口 `--help` 验证依赖 `cli_client.py` 最小骨架）
- Foundational 内 T009 / T010 / T011 / T013 可并行
- 每个故事内标记 `[P]` 的测试任务可与其它故事的故事无关任务并行（**但同一故事内的实现任务与该故事测试任务不可并行**）
- US2 的 CLI 层单测任务（T022，写 `tests/unit/test_cli_client.py`）与 US2 的验收脚本任务（T023，写 `tests/e2e/phase/verify_phase_f001_p1.py`）写不同文件、无相互依赖——但 e2e 文件由 7 个故事共用（见「受限」条目），T023 MUST 与其它故事的 e2e 任务错峰
- Polish 内 T051~T053 / T059 可并行（T054 的耗时断言与 T055 的覆盖率验证需在 T056 跑 quickstart 之前串行完成；T055 覆盖率验证依赖全部单测存在，MUST NOT 标 `[P]`）
- ⚠️ 受限：`donkey/core/workspace/init.py`、`donkey/core/api.py`、`donkey/cli/cli_client.py` 被多故事共享，**同一时刻只允许一个故事修改这三者**（`donkey/cli/cli_client.py` 由 T002b 建骨架、T014 与 T019 依次扩写，**同一时刻只允许一个任务改写该文件**）；`tests/unit/test_init_workspace.py` 同样被 7 个故事共用（T015 / T021 / T029 / T033 / T037 / T040 / T044），`tests/e2e/phase/verify_phase_f001_p1.py` 亦被 7 个故事共用（T016 / T023 / T030 / T034 / T038 / T041 / T045——后 6 个还依赖 T016 建立的命令解析辅助函数），**同一时刻只允许一个故事改写这两个测试文件**（`[P]` 标记不改变此约束）；Setup 阶段的 `pyproject.toml` 由 T004 / T005 / T006 连续改写，**必须串行**

---

## Parallel Example: User Story 1

```bash
# 启动 US1 的两个测试任务（T015 与 T016 写不同文件；但两者所在的测试文件均被 7 个故事共用 → 需错峰推进，见「受限」条目）
Task: "T015 [US1] 在 tests/unit/test_init_workspace.py 写 test_init_workspace_creates_root_dir"
Task: "T016 [US1] 在 tests/e2e/phase/verify_phase_f001_p1.py 写 test_scenario_1_new_workspace"

# 再并行启动不冲突的实现任务
Task: "T013 [P] 创建 donkey/core/api.py 的 InitResult + init_workspace 桩"   # 已在 Foundational 完成
Task: "T019 [US1] 在 donkey/cli/cli_client.py 实现 main() 的 init 分支"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup —— 工程基座
2. Phase 2: Foundational —— **CRITICAL，阻塞所有故事**
3. Phase 3: User Story 1 —— 门面 + 客户端 + 根目录落地
4. **停下来验证**：`pytest tests/unit/test_init_workspace.py -v`（US1 阶段；US2 起追加 `tests/unit/test_cli_client.py`，即 `pytest tests/unit/ -v`）+ `pytest tests/e2e/phase/verify_phase_f001_p1.py -v`（US1 用例全绿）；**覆盖率验证不属 MVP 范围**（属 Polish 阶段）
5. 冒烟：`donkey init /tmp/test-ws` → 退出码 0、目录存在

### Incremental Delivery

1. Setup + Foundational → 底座就绪
2. US1 → 独立验证 → **可交付（MVP：命令可用）**
3. US2 → 独立验证 → 路径失败面完备
4. US3 → 独立验证 → 权限失败面完备
5. US4 / US5 → 幂等与强制标志语义
6. US6 / US7 → 范围边界与命名契约
7. Polish → 静态检查零 error + 追溯核对

### Parallel Team Strategy

多人协作时的分派（注意三处共享文件的独占约束）：

1. 全员共同完成 Setup + Foundational
2. 之后按故事分派，但**共享文件 `init.py` / `api.py` / `cli_client.py` 的改动需串行合并**：
   - 开发 A：US2（`init.py` 的 `check_path` 错误分支）
   - 开发 B：US3（`init.py` 的 `check_permission`）—— 与 A 同文件，需错峰或由同一人承接
   - 开发 C：US7 的验收脚本场景 7（`tests/e2e/phase/verify_phase_f001_p1.py`，与 A/B 不同文件，可完全并行）

---

## Notes

- [P] = 不同文件、无未完成依赖
- [Story] 标签映射到 spec 的 P1~P7（US1~US7）
- 每个用户故事 MUST 可独立完成与独立验证
- 提交粒度：每个任务或逻辑组一次提交
- 停在任一检查点可独立验证该故事
- 避免：模糊任务、同一文件冲突、破坏故事独立性的跨故事依赖
- 硬约束提醒：核心层禁 `argparse`/`sys.argv`（N-05）；客户端层禁 `langchain`/`langgraph`/`sqlite3`（N-04）；全仓禁 LangSmith 任何形态（N-12）；退出码只用 `{0,1,2}`（N-08）

---

## 附录：需求 → 任务映射（FR / SC → Task）

> 本表与 spec「需求追溯矩阵」互补：spec 矩阵给出「实现要点 → FR → 验收场景」，本表给出「FR / SC → 落地任务」，用于 T057 的逐条核对。任务编号含义：T0xx 为任务 ID，其余为承载该需求的实现/测试任务。

| 需求 | 承载任务 | 需求 | 承载任务 |
|---|---|---|---|
| FR-001 | T014, T022 | FR-017 | T017, T047 |
| FR-002 | T014, T022 | FR-018 | T014, T022, T027 |
| FR-003 | T014, T044, T046, T048 | FR-019 | T023, T026, T027, T030, T031, T045 |
| FR-004 | T014, T037, T038, T039 | FR-020 | T019, T041, T049 |
| FR-005 | T013, T017, T018, T044 | FR-021 | T053 |
| FR-006 | T013 | FR-022 | T053 |
| FR-007 | T015, T043 | FR-023 | T001, T003, T007, T016 |
| FR-008 | T018, T033, T035 | FR-024 | T015, T021, T029, T033, T037, T040, T044, T022 |
| FR-009 | T018, T021, T023, T024, T030, T035 | FR-025 | T016, T023, T030, T034, T038, T041, T045 |
| FR-010 | T015, T024 | FR-026 | T009 |
| FR-011 | T021, T024 | FR-027 | T008, T014, T058 |
| FR-012 | T021, T024, T044 | FR-028 | T033, T034, T035, T038 |
| FR-013 | T021, T024 | FR-029 | T040, T042 |
| FR-014 | T029, T031 | FR-030 | T021, T024, T025 |
| FR-015 | T029, T031 | FR-031 | T051, T052 |
| FR-016 | T012, T024, T031 | — | — |

| SC | 承载任务 | SC | 承载任务 |
|---|---|---|---|
| SC-001 | T016, T023, T030, T034, T038, T041, T045, T050 | SC-009 | T051, T052 |
| SC-002 | T016 | SC-010 | T053 |
| SC-003 | T021, T023 | SC-011 | T058 |
| SC-004 | T029, T030 | SC-012 | T023, T026, T027, T030, T031, T045 |
| SC-005 | T033, T034 | SC-013 | T054 |
| SC-006 | T037, T038 | SC-014 | T045 |
| SC-007 | T040, T041 | SC-015 | T021, T023, T044 |
| SC-008 | T015, T021, T022, T029, T033, T037, T040, T044 | SC-016 | T055 |

**无 FR / SC 直接对应的任务**（11 项，属工程配置 / 资产建档 / 收口 / 治理类，不承载产品需求）：`T002` / `T004` / `T005` / `T006` / `T007`（工程基座与工具链配置）/ `T010` / `T011`（模板资产建档）/ `T056`（quickstart 收口验证）/ `T057`（FR / SC 逐条追溯核对）/ `T059` / `T060`（仓库级与上游权威文档同步）。

---

## 附录：本轮（2026-10-22）一致性分析修订记录

> 本轮由 `/speckit.analyze` 三件套一致性检查产出，**FR 编号 `FR-001`~`FR-031`（31 条）、SC 编号 `SC-001`~`SC-016`（16 条）、7 个 e2e 黑盒场景、20 条 Given/When/Then 验收场景、20 个单元测试用例（core 17 + CLI 3）数量均未变**，仅修订机制表述与断言强度。

| 级别 | 位置 | 修订要点 |
|---|---|---|
| **High** | T005 / T052 | mypy 增 `explicit_package_bases = true` + `mypy_path = "."`——否则模块名实为 `test_init_workspace` / `verify_phase_f001_p1`，`module = "tests.*"` 永不命中，`strict` 全量作用于测试层，T052 必然失败 |
| **High** | T024 / T025 | 「路径过长」改由 T024 的**统一 `except OSError`** 覆盖（`Path.exists()` 在超长路径上抛 `OSError(ENAMETOOLONG)`；`Path.resolve(strict=False)` **不**抛错，MUST NOT 依赖它）；并明确 ①② 作用于解析后路径、③ 作用于原始输入路径 |
| **High** | T021 / T023 / T030 | 补「不创建任何目录」断言（缺失父目录仍不存在 / 目标目录未被创建）——兑现 spec US2 场景 1、US3 场景 1 与 SC-003，使 FR-009 的 `mkdir(parents=True)` 回归可被测出 |
| Med | T016 / spec FR-025 | e2e 辅助函数新增「PATH 上的 `donkey` 须位于当前工作树内」校验，不匹配即回落 + 告警，避免测到其它已安装版本 |
| Med | spec Edge Cases / Assumptions | 权限判定口径与 `research.md` R-04 拉齐（`0o555` 无写位 → root 下 `os.access(W_OK)` 亦为 False，**不依赖特权账号**） |
| Med | T041 | 补「目标目录内无任何文件」断言，兑现 plan G14 |
| Med | plan §实施顺序 | 单测层改为「按 TDD **逐故事穿插**执行」，与宪法 §4.1 及 tasks 的测试先行顺序一致 |
| Med | spec FR-006 / FR-017 / Key Entities | 名称定夺规则统一引用 FR-005（唯一规范表述），消除四处重复 |
| Med | spec FR-001 / FR-002 | 退出码映射口径统一引用 FR-018，消除重复 |
| Med | 本附录 | 「无 FR / SC 对应任务」由 2 项订正为 11 项全列 |
| Low | spec FR-016 / L2 / T040 / T007 / T006 / T001 / plan G4 / plan §Project Structure | 措辞与实现细节订正（FR-016 绕口、场景引用定名、T040 源树定位、T007 用 `.venv`、T006 锁 `pytest>=7` 与集成层豁免、T001 `namespaces` 默认值说明、plan G4 集成层豁免、plan tasks.md 注释） |
