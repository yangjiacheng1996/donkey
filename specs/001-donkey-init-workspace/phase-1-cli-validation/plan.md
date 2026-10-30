# Implementation Plan: F001-P1 `cli_validation` —— `donkey init` 命令入口与 workspace 路径校验

**Branch**: `main`（spec 目录名 `001-donkey-init-workspace/phase-1-cli-validation` 与 git 分支相互独立，见 spec.md 头部说明） | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md`（含澄清会话共 **12 项**决策——截至 2026-10-22 已累积 12 条 Clarifications 记录）

---

## Summary

**目标**：交付 `donkey init` 的**命令入口 + 路径解析 / 权限校验 + workspace 根目录创建**（F001-P1 子段 1，退出码 `1-2`），**不**加载模板清单、**不**生成任何模板内容。

**技术路线**：三层落地 —— `donkey/core/`（纯业务与校验，零进程感知）→ `donkey/cli/`（argparse 入口与退出码映射）→ 打包入口（`donkey` 控制台脚本 + `python -m donkey` 双通道）。核心库 API `init_workspace(path, name=None, force=False) -> InitResult` 作为 v1 门面契约冻结，供 F002 / F003 / F004 复用。

**关键决策**（详见 `research.md`）：

| # | 决策 | 落点 |
|---|---|---|
| R-01 | 子类化 `ArgumentParser` 覆写 `error()` → 用法错误退出码 `1`（子类自动传播到子命令）；**并显式设 `prog="donkey"`**，保证 `donkey` 与 `python -m donkey` 两条入口的 stderr usage 提示逐字一致（spec FR-023 / research R-01） | `cli/cli_client.py` |
| R-02 | `main()` 返回 `int`，由入口点 `sys.exit()` 落地；控制台脚本与模块入口行为一致 | `cli/cli_client.py` / `__main__.py` |
| R-03 | 根路径以"解析后末段名为空 ⇒ 路径非法"拦截（覆盖 `/`、`D:\`、UNC 共享根） | `core/workspace/init.py` |
| R-04 | 权限用 `os.access`；`0o555`（无写位）模拟可靠，**不依赖特权账号** | `core/workspace/init.py` |
| R-05 | `resolve()` 对 NUL 抛 `ValueError` → 捕获转 `PathNotFoundError` | `core/workspace/init.py` |
| R-06 | 模板源路径 MUST 由条目 `path` 派生（`mcp/mcp.json` → `templates/mcp/mcp.json.txt`） | `core/workspace/templates/` |
| R-07 | setuptools + PEP 621；运行时零第三方依赖；ruff/mypy/pytest 配置落 `pyproject.toml` | `pyproject.toml` |
| R-08 | CI 工作流文件不属本 Phase（仓库级资产，Deferred） | plan §后续 |

## Technical Context

**Language/Version**: Python 3.11+（本机实测 3.12.3；依赖 `tomllib` 内置）

**Primary Dependencies**: **运行时零第三方依赖**（仅标准库 `pathlib` / `os` / `argparse` / `sys` / `json`）；dev 依赖 `pytest` / `pytest-cov` / `ruff` / `mypy`

**Storage**: 文件系统（workspace 根目录）；本 Phase 无数据库、无状态文件

**Testing**: pytest —— `tests/unit/`（函数级单测）+ `tests/e2e/phase/`（黑盒验收脚本，仅子进程观察退出码与文件系统副作用）

**Target Platform**: Linux / macOS（POSIX 权限语义；Windows 不在本 Phase 实现范围，但路径规则按平台无关表述编写）

**Project Type**: single-package library + CLI（`donkey.core` 库 API + `donkey.cli` argparse 客户端；web / gui 本 Phase 为空占位）

**Performance Goals**: 单次 `donkey init` 在 10 秒内返回（spec SC-013；纯本地文件系统操作，无网络依赖）

**Constraints**: 宪法 N-03（core 不依赖客户端）/ N-04（cli 不依赖 langchain·langgraph·sqlite3）/ N-05（core 不依赖 argparse·sys.argv）/ N-08（退出码段位不重叠）/ N-12（禁 LangSmith 任何形态）；CLI 框架限标准库 `argparse`；核心层 MUST 无副作用

**Scale/Scope**: 1 个子命令 / 2 个错误类 / 31 条 FR / 16 条 SC / 7 个 e2e 黑盒场景 / 20 个单元测试用例（core 层 17 + CLI 层 3） / 6 个功能源文件（`api.py`·`init.py`·`cli_client.py`·`exit_codes.py`·`exceptions.py`·`__main__.py`，**不含 4 个 `__init__.py`**）+ 4 个模板资产（`manifest.json` + 3 个 `.txt` 源）+ 2 个空占位（`donkey/web/.gitkeep` + `donkey/gui/.gitkeep`）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 门 | 宪法条款 | 判定 | 依据 / 落地方式 |
|---|---|---|---|
| G1 | §3.1 Python 3.11+；§3.1 CLI 用 stdlib `argparse`（禁 typer / click） | ✅ PASS | 运行时零第三方依赖；`pyproject.toml` 的 `dependencies = []` |
| G2 | N-03 核心层不 import 客户端；N-04 cli 不直接 import langchain / langgraph / sqlite3；N-05 核心层不 import argparse / sys.argv | ✅ PASS | `core/` 仅依赖标准库 + `core.exceptions`；`cli/` 仅依赖 `argparse` / `sys` / `core.*`（quickstart §5 有 grep 自检） |
| G3 | N-08 退出码段位严格不重叠（§4.4） | ✅ PASS | 本 Phase 仅用 `0/1/2`，落在 F001 段位 `1-10` 的子段 1；`3/4/5-10` 不触发（`contracts/exit-codes.md`） |
| G4 | §3.1 测试三层 `unit` / `integration` / `e2e/phase`；黑盒脚本只跑子进程、不 import 业务代码 | ✅ PASS | `tests/e2e/phase/verify_phase_f001_p1.py` 仅用 `subprocess` + `shutil.which`；**`tests/integration/` 本 Phase 为空占位**（仅 `.gitkeep`）——P1 仅一个子模块，无跨模块集成面，跨层边界由 e2e 黑盒场景（子进程 + 文件系统副作用）覆盖，故 §4.1「单元 + 集成 + e2e」三件套在本 Phase 退化为「单元 + e2e」，集成层留待后续 Phase 首次出现多模块协作时启用 |
| G5 | §4.1 CI：pytest + ruff + mypy；§4.1 TDD 四件套流程 | ⚠️ 部分 | 静态检查与测试命令已定义（`pyproject.toml` 配置 + quickstart §3）；**CI 工作流文件 Deferred**（R-08，仓库级资产），不阻塞本 Phase；已按宪法 §6.3 登记临时例外 E-01（范围 / 理由 / 过期时间见宪法 Governance §6.3） |
| G6 | §3.2 永不使用清单（LangSmith / deepagents / ShellToolMiddleware / subagent） | ✅ PASS | 本 Phase 无任何 LangChain 调用；quickstart §5 含 `langsmith` grep 自检 |
| G7 | §2.2 路径绝对化原则 | ✅ PASS | 相对路径解析一次即转绝对路径（FR-010）；名称取解析后末段（FR-003 / FR-012） |
| G8 | §2.3 / AC-3 workspace 原子性 + init 幂等 | ✅ PASS | FR-008 / FR-028：已存在不报错、不破坏；`--force` 在 P1 仅记录 |
| G9 | §2.8 / D-08 三端共用 `core.api` 库 API | ✅ PASS | `init_workspace` 门面 + `InitResult` 冻结（`contracts/library-api.md`）—— **契约 v2**（2026-10-30 · 宪法 [D-22]）：v1 六字段**逐字保留、顺序不变**，追加 `files_overwritten` / `dirs_created` / `dirs_skipped` / `items` 四字段 + `INIT_RESULT_CONTRACT_VERSION = 2`；**三端共用面未变** |
| G10 | N-03 入口点不得位于 `core/` | ✅ PASS | 入口点在 `donkey/cli/cli_client.py` + `donkey/__main__.py` + `[project.scripts]` |
| G11 | §3.4 / D-05 模板与 sqlite3 schema 属 P2 | ✅ PASS | P1 只建档模板清单（3 条）+ 3 个同名 `.txt` 源，**不加载、不渲染、不写任何文件** |
| G12 | §4.6 技术指标：单元测试覆盖率 ≥ 80%（`donkey.core`） | ✅ PASS | spec SC-016；以**独立命令** `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` 度量（**MUST NOT** 写入 pytest 全局 `addopts`，否则 e2e 黑盒脚本单独运行时不 import 业务代码会把覆盖率拉到 0 而误报失败）；dev 依赖新增 `pytest-cov` |
| G13 | §3.1 测试三层：`tests/e2e/phase/verify_phase_<f>_<n>.py` 黑盒脚本必须真正被 pytest 收集 | ✅ PASS | 验收脚本文件名由宪法 §3.1 固定，默认 `python_files` 不匹配 → 在 `[tool.pytest.ini_options]` 增 `python_files = ["test_*.py", "verify_phase_*.py"]`，使 `pytest tests/` 收齐 7 个 e2e 场景；覆盖率度量仍只跑 `tests/unit/`（SC-016 / G12 不受影响）；验收命令见 `quickstart.md` §6（`pytest tests/` 一次收齐 unit + e2e 三层） |
| G14 | N-01 workspace 内禁止出现 `agent.py` / `main.py` 或任何 Python 入口文件 | ✅ PASS | P1 只创建**空根目录**、不写任何文件内容（FR-007 / FR-029）；US6 单测与 e2e 场景 6 断言目录内无任何文件 |
| G15 | N-11 / §2.8 三端对等（cli / web / gui 共用 `core.api`） | ✅ PASS（阶段性） | 本 Phase 仅交付 cli 通道，`web/` / `gui/` 维持空占位（spec Assumptions）；三端对等由 F005 / F006 达成——符合 §2.8「开发顺序 CLI → Web → GUI」 |
| G16 | §2.6 workspace 目录必填项（`instruction.md` / `providers/` / `tools/` / `mcp/mcp.json` / `skills/` / `memory/`） | ✅ PASS（阶段性 · 交接 F001-P2） | 本 Phase 只创建**空根目录**（FR-007 / FR-028 / FR-029：三个计数恒 0、不写任何文件）；§2.6 的 6 项必填由 F001-P2 的模板骨架生成达成、D-01 的 workspace `manifest.json` 同属 P2（见「后续 Phase / 仓库级」表）——P1 交付的空根目录为**过渡态**，非违例 |

**门禁结论**：无违例（G5 为显式 Deferred，非违例；G12 覆盖率判据由 SC-016 承载并有独立度量命令；G13 e2e 收集缺口由 `python_files` 配置闭合；G14 / G15 / G16 为追加自检行）。**Phase 0 research 放行。**

## Project Structure

### Documentation (this feature)

```text
specs/001-donkey-init-workspace/phase-1-cli-validation/
├── plan.md              # 本文件（/speckit.plan 输出）
├── research.md          # Phase 0 输出（8 条决策 R-01 ~ R-08 + 实验证据）
├── data-model.md        # Phase 1 输出（实体 / 异常层次 / 段位 / 模板清单）
├── quickstart.md        # Phase 1 输出（可复制执行的验证指南）
├── contracts/           # Phase 1 输出
│   ├── cli-contract.md      # 命令行接口契约（参数 / 退出码 / 输出 / 行为）
│   ├── library-api.md       # 核心库 API 契约（init_workspace / InitResult / 校验能力）
│   └── exit-codes.md        # 退出码段位与异常映射表
├── spec.md              # 需求来源（已冻结）
├── checklists/
│   └── requirements.md  # 质量检查清单（16/16）
└── tasks.md             # Phase 2 输出（/speckit.tasks 生成，已产出）
```

> **本 Phase 另同步 2 处仓库级文档**（实现阶段执行，见 tasks T059 / T060）：`harness/features/README.md`（§12.2 落地状态 + §4.3 的 Deferred 结论 + §3.x 表格「P1 只建档、不加载」订正）与 `harness/features/feature001_phase001_cli_validation.md`（`name` 语义复核 + §4.1 的 `mkdir` 口径订正，与 spec FR-005 / FR-009 对齐）；两处 MUST NOT 改动其它章节。

### Source Code (repository root)

```text
donkey/                              # 顶层 Python 包（仓库根即包根）
├── __init__.py                      # 包标识（版本号来源）
├── __main__.py                      # python -m donkey 入口 → sys.exit(main())
├── core/                            # 引擎层 / 库 API（零进程感知）
│   ├── __init__.py
│   ├── api.py                       # InitResult + init_workspace 门面（TDD：先落桩后补实现）
│   │                                #   —— 契约 v2（宪法 [D-22]）：追加 files_overwritten /
│   │                                #      dirs_created / dirs_skipped / items 四字段
│   ├── exit_codes.py                # 段位常量（0/1/2 使用；3/4 与段位元组建档备用）
│   ├── exceptions.py                # DonkeyError ← WorkspaceInitError ← {PathNotFound, PathPermission}
│   └── workspace/
│       ├── __init__.py
│       ├── init.py                  # check_path / check_permission / validate_init_request
│       └── templates/               # P1 只建档，不加载不渲染
│           ├── manifest.json        # 模板清单（3 条：instruction.md / providers/default.toml / mcp/mcp.json）
│           ├── instruction.md.txt
│           ├── providers/
│           │   └── default.toml.txt
│           └── mcp/
│               └── mcp.json.txt
├── cli/                             # 客户端层
│   ├── __init__.py
│   └── cli_client.py                # argparse 入口 + 异常→退出码映射表（Setup 阶段先建最小骨架，见「实施顺序」第 1 步）
├── web/                             # 空占位（`.gitkeep`，F005 实施，本 Phase 不填内容）
└── gui/                             # 空占位（`.gitkeep`，F006 实施，本 Phase 不填内容）

tests/
├── unit/
│   ├── test_init_workspace.py       # 17 个用例（core 层；CLI 层 3 个见 tests/unit/test_cli_client.py）
│   └── test_cli_client.py           # 3 个用例（缺子命令 / 缺必填参数 / 未登记异常子类兜底；含 FR-024「未知参数 → 退出码 1」断言组）
├── integration/                     # 本 Phase 无集成层用例（目录占位）
└── e2e/
    └── phase/
        └── verify_phase_f001_p1.py  # 7 个黑盒场景断言

pyproject.toml                       # 打包 + 工具配置（ruff / mypy / pytest / [project.scripts]）
```

**Structure Decision**：采用**单包 + 客户端分层**结构（而非 `src/` 布局）——仓库根即包根 `donkey/`，与宪法 §3.1 规定的"测试目录 `tests/` 与 `core/` / `cli/` / `web/` / `gui/` 同级"一致，且与既有 `harness/`（研究资料，非可发布代码）不冲突。`web/` / `gui/` 保留空占位，不在本 Phase 填入任何内容。

## 复杂度与风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| 模板源命名规则与提示词占位清单曾不一致（`mcp.json.txt` vs `mcp/mcp.json.txt`） | 已闭合 —— 上游提示词已于 2026-10-21 按 R-06 修正为 `mcp/mcp.json.txt` | 以规则为准建档（R-06）；本 Phase 建档的 3 个源路径已与修正后的提示词一致（`templates/mcp/mcp.json.txt`） |
| 权限断言在特权账号下被绕过 | 场景 3 假阳性通过 | `chmod 0o555`（无写位）模拟——该目录不含任何写位，按 POSIX 语义**即使以 root 运行 `os.access(dir, W_OK)` 亦为 False**，故模拟**不依赖特权账号**（R-04）；**MUST NOT** 用 root-only 目录（如 `/root/...`）模拟——root 对其实际可写，断言不成立 |
| 验收脚本在未安装环境找不到 `donkey` | 7 个场景全挂（环境性失败） | `shutil.which("donkey")` → 回落 `python -m donkey`（FR-025） |
| `resolve()` 对 NUL 抛 `ValueError` 而非 `OSError` | 未捕获异常堆栈 | 显式捕获 `ValueError` → `PathNotFoundError`（R-05 / FR-013） |
| 后续 Phase 误用 `name` 参数造成"路径与名字不一致" | 身份混淆复发 | 库 API 保留形参但 CLI 不暴露；FR-003 / FR-017 明文禁止不一致命名 |
| 验收脚本可能测到 PATH 上的另一份 donkey 安装 | 测错代码，验收失真 | spec FR-025 已约束回落时以仓库根为工作目录；本地开发建议用可编辑安装 |
| 单元测试覆盖率未达 80% | spec SC-016 不达标，Phase 完成判据不成立 | dev 依赖加 `pytest-cov`；覆盖率以 `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` 独立度量（不写入全局 addopts）；不足时优先补单测而非下调阈值 |
| e2e 黑盒脚本被计入覆盖率 | e2e 不 import 业务代码，会把覆盖率拉到 0 而误报失败 | 覆盖率命令只跑 `tests/unit/`；MUST NOT 把 `--cov` 写入 pytest 全局 `addopts`（与 G12 一致） |
| FR-030 的 3 个非豁免路径分支（目标为普通文件 / 父目录为文件 / 空路径）漏测 | 该 MUST 无断言落点，回归时静默退化 | 由同一个单元测试用例一并覆盖（不要求各自独立成例，spec FR-030 第 5 轮口径）；core 层单测由 16 增至 17 个 |
| 双入口 usage 提示不一致（`argparse` 默认 `prog` 取 `sys.argv[0]` 的 basename，`python -m donkey` 下为 `__main__.py`） | spec FR-023「两种入口输出完全相同」不成立，且现有 e2e 只断言 stdout → 缺陷静默 | 解析器显式 `prog="donkey"`（research R-01 / 决策表 R-01）；e2e 场景 1 追加 stderr usage 提示逐字相同断言 |
| Setup 阶段安装验证（`donkey --help`）早于 `cli/cli_client.py` 存在 | 两条入口均 ImportError → Setup 检查点「双入口可执行」不可达成 | `cli/cli_client.py` 最小骨架前移至工程基座（见「实施顺序」第 1 步），Foundational 阶段相应收窄为「子命令注册 + 退出码映射表」 |

## 实施顺序（任务拆解留给 `/speckit.tasks`）

> 本节只给**依赖顺序**（谁必须先存在），不规定逐条任务。

1. **工程基座**：`pyproject.toml` + 包骨架（`__init__.py` × 4、`__main__.py`、`web/.gitkeep` + `gui/.gitkeep` 两个空占位）+ **`cli/cli_client.py` 最小骨架**（`ArgumentParser(prog="donkey")` + `error()` 覆写 + 一个可返回 `0` 的 `main()`；此时尚未注册 `init` 子命令）→ 控制台入口可运行（`donkey --help` 与 `python -m donkey --help` 均可用，供 Setup 阶段安装验证）；
2. **核心资产**：`core/exit_codes.py`、`core/exceptions.py` → 退出码常量与异常层次就位；
3. **模板建档**：`core/workspace/templates/manifest.json` + 3 个 `.txt` 源（路径按 R-06 派生）；
4. **校验层**：`core/workspace/init.py`（`check_path` → `check_permission` → `validate_init_request`）；
5. **门面层**：`core/api.py`（`InitResult` + `init_workspace`）（先落 `init_workspace` 桩 `raise NotImplementedError`，使单测文件可被收集、失败形态正确）；
6. **客户端层**：扩写 `cli/cli_client.py`（第 1 步已建骨架）——注册 `init` 子命令（位置参数 `path` + `--force`）+ 完整 `main()` + 退出码映射表；
7. **单测层**：`tests/unit/`（20 个用例：test_init_workspace.py 17 个 + test_cli_client.py 3 个）——依赖 §4.1~§4.3 的**签名 / 契约**就位（**非**实现就位），**按 TDD 逐故事穿插执行**（每个故事内：先写测试并确认失败 → 再补实现 → 跑该故事单测 + 验收场景），而非在 §4.1~§4.3 全部实现完成后才补测（见 tasks T015 → T017 → T020 的先后）；
8. **验收层**：`tests/e2e/phase/verify_phase_f001_p1.py`（7 个场景）；
9. **验证**：quickstart §1 ~ §6 全部命令跑通。
10. **覆盖率验证**：`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` → `donkey.core` 行覆盖率 ≥ 80%（spec SC-016 / 宪法 §4.6）；e2e 黑盒脚本不参与该度量。

## 后续 Phase / 仓库级（不属本 Phase）

| 事项 | 归属 | 说明 |
|---|---|---|
| 模板清单加载 + 渲染 + 模板骨架内容（46 条条目） | F001-P2 | 本 Phase 只建档 3 条；**宪法 §2.6 的 workspace 必填项（`instruction.md` / `providers/default.toml` / `tools/` / `mcp/mcp.json` / `skills/` / `memory/`）与 §3.4 的 3 个内置 `@tool` 由该 Phase 达成**——本 Phase 交付的是空根目录（过渡态），§2.6 / §3.4 的符合性即以此为交接条件 |
| `render_templates` / `init_workspace_inner` / workspace manifest 写入 | F001-P2 | — |
| 3 个内置 `@tool` + Skills 三层示例（+7 条） | F001-P3 | — |
| `.github/workflows/ci.yml` | 仓库级（Deferred） | 最小内容已备：`pytest tests/`（按 G13 收齐 unit + e2e 三层）+ `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80`（G12 / SC-016）+ `ruff check donkey/ tests/` + `mypy donkey/ tests/`（R-08）；骨架已齐备，待仓库级 CI 落地时直接取用 |
| `donkey load` / `session` / `run` 子命令 | F002 / F003 / F004 | 复用 `core.api` 门面 |

## Complexity Tracking

**无违例**——Constitution Check 全部 PASS（G5 为显式 Deferred，非违例）。本表登记**超出本计划范围的复杂度增量 / 需豁免的偏离**；「复杂度与风险」表登记的是**已识别风险**，二者不重复。

| 复杂度增量 | 说明 |
|---|---|
| Setup 阶段 +1 个任务 | `cli/cli_client.py` 最小骨架前移（双入口 `--help` 安装验证需要），Foundational 阶段相应收窄为「子命令注册 + 退出码映射表」；总任务数 +1，其余阶段任务数与顺序不变 |
