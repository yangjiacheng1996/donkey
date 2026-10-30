# Implementation Plan: F001-P4 `cli_version` —— `donkey version` 查询版本号

**Branch**: `main`（spec 目录名 `001-donkey-init-workspace/phase-4-cli-version` 与 git 分支相互独立，见 spec.md 头部说明） | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-donkey-init-workspace/phase-4-cli-version/spec.md`（38 条 FR / 16 条 SC / 7 个 User Story / Clarifications **2 段 9 项决策** —— 以 spec.md 的 `## Clarifications` 段为准；**Session 2026-10-30** 的 5 项 = Q1 图版本取值（**已被 Q2 覆盖作废**，留痕）/ Q2 包版本出口与输出形态 / Q3 `y`/`z` 分量读法 / Q4 顶层 `--version` 标志 / Q5 范围边界与宪法修订落地方式；**Session 2026-10-30（analyse 缺陷修复轮）** 的 4 项 = Q6 宪法 v1 baseline 与提示词文件口径一并豁免 / Q7 版本一致性以 FR-018 为准 / Q8 宪法 [D-20] 行为权威文本 / Q9 宪法 §4.5 读法登记）

---

## Summary

**目标**：为 donkey CLI 增加一条**只读**的版本查询命令 `donkey version` —— stdout 输出**恰好一行裸版本值 `v0.1.0`**（`v` 为显示前缀，底层取值 `0.1.0` 在**常规安装形态下**与 `pyproject.toml` / 包内 `__version__` / 工作区清单 `donkey_version` 字段**逐字节一致**；陈旧安装形态下以**安装分发元数据**为准，FR-018），退出码 `0`；参数用法错误沿用既有全局映射表以退出码 `1` 失败。

**技术路线**：**一个纯函数 + 一行 print**。本 Phase 的运行时代码面被压缩到最小 —— 核心层新增一个 20 行级的纯模块，客户端层只加一个子命令与一行 `print()`；**零新增依赖、零新增 exit code、零新增 Error class、零改动既有测试文件**。

```text
donkey/core/version.py               ← 本 Phase 唯一的运行时代码新增（纯 stdlib，无 IO 副作用）
donkey/cli/cli_client.py             ← 注册 `version` 子命令（无参数）+ 一行 print + 2 处过期文案（46 → 54）
donkey/core/api.py                   ← InitResult docstring 的 3 处过期计数（46/40/40 → 54/48/48）
.specify/memory/constitution.md       ← 宪法修订（**Maintainer 已于 2026-10-30 前置落地，4 处**；本 Phase 只核对，不改）
tests/unit/test_cli_version.py       ← 新增（版本解析三分支 + 输出形态）
tests/e2e/phase/verify_phase_f001_p4.py ← 新增（7 个黑盒断言 ↔ 7 个 User Story）
```

**关键决策**（R-01 ~ R-19 详见 [research.md](research.md)）：

| # | 决策 | 落点 |
|---|---|---|
| R-01 | 版本取值解析落在**核心层**新模块 `donkey/core/version.py`（FR-020） | `donkey/core/version.py` |
| R-02 | 核心层暴露 `resolve_version()`（底层取值）与 `version_string()`（展示值 `"v" + ...`）两个函数 —— `v` 前缀逻辑**单点收敛**，三端将来复用同一函数 | `donkey/core/version.py` |
| R-03 | 版本来源 = **安装分发元数据** `importlib.metadata.version("donkey")`（FR-016，与 F001-P2 FR-021 同口径） | `donkey/core/version.py` |
| R-04 | 元数据不可得（`PackageNotFoundError`）→ 回退包自身 `__version__`；`donkey/__init__.py` **零 import** → 无循环依赖（FR-017） | `donkey/core/version.py` |
| R-05 | 元数据与 `__version__` 不一致 → **以元数据为准**，不比较、不告警（FR-018；告警会污染 FR-007 / FR-009） | `donkey/core/version.py` |
| R-06 | 子命令**无任何参数**；argparse 自动的 `-h/--help` 走 `exit(0)`；三类误用实测均落**退出码 1**（FR-001 / FR-002 / FR-004） | `donkey/cli/cli_client.py` |
| R-07 | 顶层**不**提供 `--version`（FR-038 / Q4）—— `donkey --version` 按未知参数以 `1` 失败 | `donkey/cli/cli_client.py` |
| R-08 | 输出用 `print()` → 恰好一行 + 一个行终止符；判据以「**去掉行终止符后**」的正文为准（FR-007） | `donkey/cli/cli_client.py` |
| R-09 | e2e 期望值取自**工作树声明**（`pyproject.toml` 的 `version`，`tomllib` 解析）+ 另行断言该声明为 `0.1.0`（SC-003）—— **注**：本条的「期望值**来源**」部分已被 **R-18**（双比对）取代，**仅**保留其「另行断言工作树声明值当前为 `0.1.0`」这一半（该断言仍 MUST 执行） | `tests/e2e/phase/verify_phase_f001_p4.py` |
| R-10 | e2e「元数据不可得」的**真黑盒**复现 = 把 `donkey/` **包目录**复制到临时目录（副本同级无 `*.egg-info`）**并用 `python -S` 屏蔽 site-packages** → 实测命中 `PackageNotFoundError`（**`-S` 不可省**：已安装 donkey 的环境里 site-packages 的 `dist-info` 仍会被发现 —— 见 research.md R-10 的修正记录）（FR-017 / SC-007 / US6） | `tests/e2e/phase/verify_phase_f001_p4.py` |
| R-11 | 单元测试落点 = **新建** `tests/unit/test_cli_version.py`（SC-007 明文要求回退路径有单元覆盖）；**不动** F001-P1 的 `test_cli_client.py`（FR-034） | `tests/unit/test_cli_version.py` |
| R-12 | 宪法修订**四处**锚点（§4.2.1 新增 / §4.3 第 253 行括注 / §4.3 第 269 行 v1 baseline 限定语 / 第 5 章 [D-20]）—— **已落地**（Maintainer 于 2026-10-30 前置落地；此处行号为**修订后**的实际行号） | `.specify/memory/constitution.md`（只核对） |
| R-13 | `harness/features/README.md` **逐字未改**；F001-P4 的登记载体 = [D-20] 的**影响面**条目（FR-030 / SC-012 / FR-036 + Session 2026-10-30（analyse 缺陷修复轮）Q6 / Q8） | —— |
| R-14 | 过期计数修正 = **2 个文件 5 处**：`cli_client.py` 的 `help` + `description` 两处、**`api.py` 的 `InitResult` docstring 三处**（46/40/40 → 54/48/48）；**明确不改** F001-P2 的三份冻结 `contracts/*.md`（FR-037） | `donkey/cli/cli_client.py` / `donkey/core/api.py` |
| R-15 | 既有断言兼容性核对：`tests/` 下「46 个模板条目」**0 命中**、`templates=46` **0 命中**、无断言依赖子命令列表 → **无需**登记阶段边界改写 | —— |
| R-16 | e2e 脚本**自包含**（自带 `_resolve_donkey_command()` 副本）—— 与 P1 / P2 / P3 三套脚本的既有惯例一致，不抽公共模块、不改动冻结脚本 | `tests/e2e/phase/verify_phase_f001_p4.py` |
| R-17 | 耗时上限 **5 秒**（实测毫秒级；P3 的 10 秒是落 49 个文件才需要的量级） | `tests/e2e/phase/verify_phase_f001_p4.py` |
| R-18 | 版本一致性判据 = **双比对**（工作树声明值 + 安装分发元数据值）；二者相等 → 输出 MUST == 二者；二者不等（陈旧安装）→ 输出 MUST == **安装分发元数据值**（FR-018），且该不等情形 MUST 由验收脚本**显式断言**、MUST NOT 被静默接受。**取代 R-09 的「期望值来源」部分** —— R-09 保留其「另行断言工作树声明值当前为 `0.1.0`」这一半（该断言仍 MUST 执行） | `tests/e2e/phase/verify_phase_f001_p4.py` |
| R-19 | 宪法修订前置落地 → 本 Phase 的 T002~T004 由『编辑任务』改为『核对 + 自检任务』 | `tests/e2e/phase/verify_phase_f001_p4.py` / `quickstart.md` §5 |

---

## Technical Context

**Language/Version**: Python 3.11+（本机实测 3.12.3；`tomllib` 内置，e2e 读 `pyproject.toml` 用它）

**Primary Dependencies**: **donkey 自身仍恰为 1 个直接运行期依赖** = `langgraph-checkpoint-sqlite>=3.1,<4`（**不变**）；
**本 Phase 新增依赖：0 个** —— 运行期只用标准库 `argparse` / `importlib.metadata`；测试侧用 `tomllib`（标准库）与既有 `pytest`；
**不引入** `langchain` / `langgraph` / `sqlite3` 的任何导入（宪法 N-04，spec FR-027）

**Storage**: **无** —— 本命令是纯只读（spec FR-022），不创建 / 修改 / 删除任何文件，不读取工作区

**Testing**: pytest —— `tests/unit/test_cli_version.py`（**新增**）+ `tests/e2e/phase/verify_phase_f001_p4.py`（**新增**，7 个黑盒断言）+ F001-P1 / P2 / P3 的既有三层套件（**必须仍全绿**，spec FR-034 / SC-009）

**Target Platform**: Linux / macOS（跨平台**行终止符**差异已在判据层消解 —— FR-007 以"去掉行终止符后"的正文为准；Windows 不在本 Phase 实现范围）

**Project Type**: single-package library + CLI（`donkey.core` 库 API + `donkey.cli` argparse 客户端；web / gui 维持空占位）

**Performance Goals**: 单次 `donkey version` 在 **5 秒**内返回（spec SC-011；纯内存 + 一次元数据查询，**无网络、无文件写入**，实测毫秒级）

**Constraints**: 宪法 N-03（core 不 import 客户端）/ N-04（cli 不直接 import langchain·langgraph·sqlite3）/ N-05（core 不 import argparse·sys.argv·click·typer）/ N-08（退出码段位不重叠）/ N-11（三端对等，阶段性）；CLI 框架限标准库 `argparse`；**本 Phase 不占用任何 exit code 子段、不新增 Error class**（spec FR-028 / FR-029）；**输出 MUST 是裸版本值、MUST NOT 套用 `key=value` 摘要形态**（spec FR-010）

**Scale/Scope**: **1 个** CLI 子命令 / **1 个**新运行时代码模块（`donkey/core/version.py`，2 个公开函数）/ **0 个**新依赖 / **0 个**新退出码 / **0 个**新 Error class / **38 条 FR** / **16 条 SC** / **7 个 User Story** / **7 个** e2e 黑盒断言 / **4 处宪法修订（已落地）** / **3 个**新增测试文件（`test_cli_version.py` / `verify_phase_f001_p4.py` / `test_init_report.py`）/ **实施期改动既有源文件 4 个**（`cli_client.py` / `api.py` / `workspace/init.py` / `workspace/manifest.py`）/ `constitution.md` 已在前置修订中落地 / **5 个**既有测试文件的断言改写（P1 单测 1 · P2 单测 9 · P3 单测 1 · P2 e2e 2 · P3 e2e 3 —— 逐条登记见 spec.md文末「后续修订登记」§2）/ **6 处宪法修订**（[D-20] 前置落地 4 处 + [D-21] / [D-22] 本轮落地 2 条 ADR）

> **（2026-10-30 补登 · 宪法 [D-21] / [D-22]）**：原口径「**0 个**既有测试文件改动」已被本轮两项变更打破 —— [D-21]（工作区清单字段变更）与 [D-22]（`donkey init` 执行报告变更）分别改写了既有测试文件的断言；FR-034 的登记要求见 spec.md 文末「后续修订登记」§2。**库 API 契约升为 v2**（`InitResult` +4 字段 + `items`）。

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 门 | 宪法条款 | 判定 | 依据 / 落地方式 |
|---|---|---|---|
| G1 | §3.1 Python 3.11+；§3.1 CLI 用 stdlib `argparse` | ✅ PASS | CLI 框架不变；本 Phase 只加一个**无参数**子解析器（R-06） |
| G2 | N-03 core 不 import 客户端；N-04 cli 不直接 import langchain / langgraph / sqlite3；N-05 core 不 import argparse / sys.argv | ✅ PASS | 新模块 `donkey/core/version.py` 是**纯 stdlib**（`importlib.metadata` + `from donkey import __version__`），**零** argparse / 框架 / sqlite3 导入；cli 侧**零新增**框架 / sqlite3 导入（**唯一**新增的 import 是 `from donkey.core.version import version_string` —— research.md R-02，**不是**框架依赖） |
| G3 | N-08 退出码段位严格不重叠（§4.4） | ✅ PASS（**不占用段位**） | 本 Phase **不新增**任何码值、不新增 Error class、不改映射表与段位表（spec FR-029 / SC-008）；只走 `0`（全子命令共用段）与既有 `1`（参数用法错误） |
| G4 | §3.1 测试三层 `unit` / `integration` / `e2e/phase`；黑盒脚本只跑子进程、不 import 业务代码 | ✅ PASS | 新增 `unit/test_cli_version.py`（版本解析三分支）与 `e2e/phase/verify_phase_f001_p4.py`（7 断言，纯子进程）；**`integration/` 层本 Phase 不新增用例**（该层已由 F001-P3 启用 —— `tests/integration/test_init_to_load.py` 存在且含 ≥4 个用例，**不**是空占位）—— 本 Phase 无跨模块协作（核心层纯函数 + 客户端一行 print），P3 启用该层的理由**不**适用于本 Phase |
| G5 | §4.1 CI：pytest + ruff + mypy | ✅ PASS | `.github/workflows/ci.yml` 已由 F001-P3 交付（`pip install -e ".[dev]"` + 四类命令）；本 Phase **无新增 CI 交付物**、**不新增 CI 检查断言**（spec 已明确） |
| G6 | §3.2 永不使用清单（LangSmith / deepagents / ShellToolMiddleware / subagent） | ✅ PASS | 本 Phase 新增代码**零**框架 / 可观测性后端导入；`donkey.egg-info` 属安装元数据，与任何"使用"无关 |
| G7 | §2.2 路径绝对化原则 | ✅ PASS（**不适用**） | 本命令**不涉及任何路径**（不读工作区、不接受路径参数） |
| G8 | §2.3 / AC-3 workspace 原子性 + init 幂等；D-01 workspace 自带 manifest | ✅ PASS（**不适用**） | 本命令**只读**（FR-022），对 workspace **零副作用**；`donkey init` 的幂等三态**一字不改** |
| G9 | §2.8 / D-08 三端共用 `core.api` 库 API | ✅ PASS（**豁免** + **契约 v2**） | 本 Phase 是**元信息命令**（宪法 §4.2 修订后）—— 不需要 `donkey.core.api` 库 API（spec FR-020 末句）；版本解析落在 `donkey/core/version.py`，**不是** `core.api` 的对外库 API |
| G10 | N-03 入口点不得位于 `core/` | ✅ PASS | 入口点仍在 `cli/cli_client.py` + `__main__.py` + `[project.scripts]`，本 Phase 不动 |
| G11 | §3.1 `tests/e2e/phase/verify_phase_<f>_<n>.py` 必须真正被 pytest 收集 | ✅ PASS | `python_files = ["test_*.py", "verify_phase_*.py"]` 已含该模式 → 新脚本自动被收集 |
| G12 | §4.6 技术指标：单元测试覆盖率 ≥ 80%（`donkey.core`） | ✅ PASS | 新模块 `donkey/core/version.py` 100% 由 `unit/test_cli_version.py` 覆盖（解析三分支 + 前缀拼接 + CLI 输出形态）→ 覆盖率只增不减 |
| G13 | §4.2 / §4.3 F 编号唯一性与 Phase 切分规则 | ✅ **PASS（修订后 · 4 处 · 已落地）+ 2 条 ADR（[D-21] / [D-22]）** | 宪法修订共 **4 处** —— §4.2.1 新增「元信息命令豁免」小节 / §4.3 第 253 行括注「（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）」/ §4.3 第 269 行 v1 baseline 句的「**（元信息命令按 §4.2 豁免）**」限定语 / 第 5 章 **[D-20]**；**已由 Maintainer 于 2026-10-30 前置落地**（R-12 / R-19），本 Phase 只**核对、不改**。§4.3 的 v1 baseline 句亦已加限定语（元信息命令不占子段、不需提示词文件）—— 原文本轮 analyse 发现的 CRITICAL 缺陷已闭合。**spec MUST NOT 自设宪法例外**（FR-031）—— 本 plan 只**引用**该修订 |
| G14 | N-01 / D-10 workspace 内禁止出现 Python 入口文件 | ✅ PASS（**不适用**） | 本 Phase **不在 workspace 内产生任何文件**（只读命令） |
| G15 | N-11 / §2.8 三端对等（cli / web / gui 共用 `core.api`） | ✅ PASS（**阶段性 · 已登记缺口**） | 本 Phase 只交付 cli 通道的版本入口；`donkey web version` / `donkey gui version` 归 **F005 / F006**，本 Phase **只登记、不实现、不写解析器占位**（spec FR-005 / FR-023 / G 段） |
| G16 | §4.5 版本号规则（`vx.y.z`；x = 图版本 / y = 节点 id / z = 节点修改次数） | ✅ PASS | 版本值按 §4.5 记法展示（带 `v` 前缀），三个分量**严格**按 §4.5 的字面定义读（Clarifications Q3；§4.5 的 `x` 定义含「前端版本**或**后端图版本」两分支，本 Phase 取**后端图版本**分支 —— 读法登记见 spec FR-013）；底层取值与包 / 发布版本**逐字节一致**（FR-012 / FR-013 —— 口径**限定在常规安装形态下**，陈旧安装形态以分发元数据为准，FR-018 / R-18）；**不输出**节点清单或节点级版本号（FR-015） |
| G17 | N-02 禁止 subagent / 子智能体任何目录或字段 | ✅ PASS | 本 Phase 新增代码零 subagent 相关字段 |
| G18 | §3.5 数据安全分级（凭据高敏感 / 自动脱敏 / 不上传 workspace） | ✅ PASS（**不适用**） | 本命令不读 workspace、不打印任何内容（仅一行版本值） |
| G19 | §6.2 宪法修订流程（动机 / Maintainer 批准 / 影响评估 / 迁移计划 / 记录修订） | ✅ PASS | 五要件齐备且**已随宪法 [D-20] 行逐字落地**（动机 / 影响面 / 不变项 / 迁移路径 / 边界 —— 见宪法第 5 章 [D-20] 行与 spec H 段 (c)）；Maintainer 批准**已取得**（spec 的 Clarifications 与 H 段载明）；ADR 编号**只增不删**（[D-20] 置于表尾，R-12） |
| G20 | §4.6 技术验收：所有 exit code 与 §4.4 完全一致 | ✅ PASS | 本 Phase 实际可返回的退出码集合 = `{0, 1}`，二者都在 §4.4 的既有表内（`0` 全子命令 / `1` F001 段位） |
| G21 | §4.4 exit code 段位分配总表 | ✅ PASS（**表不动**） | 段位表**逐字不改**（spec FR-029）；`version` 不占用任何子段 |
| G22 | N-06 / N-07 / N-09 / N-10（load 失败不改 workspace / load 不依赖 init / session 标题即对外标识 / session 首轮提示词摘要） | **不适用** | 四条均属 **`donkey load` / `donkey session` 域**（退出码段位 `11-20` / `21-30`），本 Phase 只做 `version` 的只读查询 → **明确不适用**（未被覆盖 ≠ 已覆盖） |
| G23 | §2.1 两层模型（材料层 vs 引擎层）/ §2.4 Skills 三层 / §2.5 内置 `@tool` 与中间件职责正交 / §2.7 中间件录用与禁用清单 | ✅ PASS（**不适用**） | 本 Phase 不涉材料层、不涉 Skills、不挂任何中间件（FR-027）；只读地暴露工程元信息，正落在引擎层的"元信息"职责内 |
| G24 | §4.1 TDD 四件套流程（specify → plan → tasks → implement） | ✅ PASS | 本 Phase 的文档顺序：spec.md（已完成）→ **plan.md + research.md + data-model.md + contracts/ + quickstart.md（本轮）** → tasks.md → implement |

**（2026-10-30 补登 · 宪法 [D-21] / [D-22]）**：本轮另交付两项变更，门禁**复核后仍全部 PASS**，逐门要点：

| 门 | 复核结论 | 复核要点 |
|---|---|---|
| G2（分层） | ✅ 维持 PASS | `donkey/core/version.py` 仍为**纯 stdlib**；`workspace/init.py` 与 `workspace/manifest.py` 的新代码**零**框架 / `argparse` / `sqlite3` 导入；`cli_client.py` 新增的唯一 import 仍是 `donkey.core.version` |
| G4（测试三层） | ✅ 维持 PASS | 新增 `unit/test_init_report.py`（init 执行报告层）；`e2e/phase/verify_phase_f001_p4.py` 仍为**纯子进程**、零 `donkey.*` import；**integration 层本 Phase 仍不新增用例**（无跨模块协作） |
| G6（永不使用清单） | ✅ 维持 PASS | 新增代码**零**框架 / 可观测性后端导入 |
| G9（三端共用 `core.api`） | ✅ 维持 PASS（**豁免口径不变**） | `version` 命令**仍不需要** `core.api` 库 API（FR-020 末句豁免未变）；**但** `InitResult` 因 [D-22] 升为**契约 v2**（追加 4 字段 + `items`，`INIT_RESULT_CONTRACT_VERSION = 2`）—— v1 六字段**逐字保留、顺序不变**，**三端共用面未缩小**，F005 / F006 将来复用 `core.api` 不受影响 |
| G12（覆盖率） | ✅ 维持 PASS | `donkey/core/version.py` 仍 100%；新增的 `donkey/core/api.py` 亦 100%；`donkey.core` 总覆盖率 **93%**（≥ 80%） |
| G13（F 编号唯一性） | ✅ 维持 PASS | [D-20] 的**四处**逐字**未动**；本轮**追加** [D-21] / [D-22] 两条 ADR（编号只增不删，表尾连续 D-01 ~ D-22）—— **未新增任何 F 编号**，`version` 仍按 §4.2.1 豁免 |
| G16（§4.5 版本号规则） | ✅ 维持 PASS | 展示值仍为 `v` + 底层取值；[D-21] 把清单的 `donkey_version` 改为**动态取值** —— 与 FR-013 的「逐字节一致」口径**方向一致**（常规安装形态下恒等） |
| G20 / G21（退出码） | ✅ 维持 PASS | [D-22] **未新增**任何码值 / Error class / 映射表条目；`version` 路径仍只经 `0` 与既有 `1` |

**门禁结论**：**无违例**。唯一一处需要宪法修订的是 **G13**（**Phase ↔ exit code 子段 1:1** 与 **Phase ↔ 提示词文件 1:1** 两项惯例）—— 该修订**已由 Maintainer 批准并于 2026-10-30 前置落地**（**4 处**，内容**逐字**取自 spec H 段 (a) / (b) / (b2) / (c)），本 Phase 只**核对、不改**（R-12 / R-19）；本 plan **只引用、不自设**任何宪法例外（spec FR-031）。G15 是本 Phase 登记的**阶段性缺口**（web / gui 的版本入口归 F005 / F006），G4 的集成层**本 Phase 不新增用例**（该层已由 F001-P3 启用；本 Phase 无跨模块协作）。

**Phase 0 research 放行**（R-01 ~ R-19 已落地，NEEDS CLARIFICATION 残留 **0** 项；新增依赖 0 / 新增退出码 0 / 既有测试文件改动 0）。

### Phase 1 设计后复核（Re-check）

| 门 | 复核结论 | 复核要点 |
|---|---|---|
| G2（分层） | ✅ 维持 PASS | `donkey/core/version.py` 的 import 面 = `importlib.metadata` + `from donkey import __version__`，**零** argparse / 框架 / sqlite3；cli 侧**零新增 import**（只新增 1 个子解析器 + 1 行 print）。quickstart §3 给出 2 条 grep 自检 |
| G3 / G20 / G21（退出码） | ✅ 维持 PASS | [contracts/exit-codes.md](contracts/exit-codes.md) 明确「本 Phase 新增码值 0 个 / 新增 Error class 0 个 / 映射表与段位表逐字未改」；实际可返回集合 = `{0, 1}` |
| G4（测试三层） | ✅ 维持 PASS | `unit` 层新增独立文件（R-11，不动 F001-P1 冻结文件）；`e2e/phase` 层新增 7 断言（纯子进程，FR-033）；`integration/` 层**本 Phase 不新增用例**（该层已由 F001-P3 启用 —— `tests/integration/test_init_to_load.py` 存在且含 ≥4 个用例，**不**是空占位）；本 Phase 无跨模块协作，P3 启用它的理由不适用 |
| G6（永不使用清单） | ✅ 维持 PASS（**新增证据**） | 新模块**零**框架导入 → 门禁冒烟（CI 的 `import donkey.core.api, donkey.cli.cli_client`）不受影响；quickstart §3 给出 grep 自检 |
| G9（库 API） | ✅ 维持 PASS（**新增证据**） | `donkey/core/version.py` **不是** `donkey.core.api` 的对外库 API（spec FR-020 末句）；`core/api.py` 本 Phase **只改 docstring**、函数体一字不动 |
| G12（覆盖率） | ✅ 维持 PASS（**新增证据**） | 新模块 100% 被 `unit/test_cli_version.py` 覆盖 → `donkey.core` 覆盖率只增不减 |
| G13（宪法修订） | ✅ 维持 PASS（**新增证据**） | **四处**修订文本**逐字**取自 spec H 段 (a) / (b) / (b2) / (c)，且**已由 Maintainer 于 2026-10-30 前置落地**；[contracts/constitution-amendment.md](contracts/constitution-amendment.md) 给出逐字文本与锚点行号（R-12），实施期 MUST **只核对、不改**（R-19），MUST NOT 改写措辞 |
| G15（三端对等） | ✅ 维持 PASS（**阶段性 · 已登记**） | [contracts/cli-contract.md](contracts/cli-contract.md) §「范围外登记」明列 `donkey web version` / `donkey gui version` 归 F005 / F006；**无任何解析器占位**（FR-023） |
| G16（版本号规则） | ✅ 维持 PASS（**新增证据**） | [contracts/version-contract.md](contracts/version-contract.md) 把「底层取值 ↔ `v` 展示值 ↔ §4.5 三分量 ↔ 工作区清单 `donkey_version`」的对应关系写成一张表；`v` 前缀逻辑单点收敛（R-02） |
| G24（流程） | ✅ 维持 PASS | 本轮产出 `plan.md` + `research.md` + `data-model.md` + `contracts/` × 4 + `quickstart.md`；`tasks.md` 留待 `/speckit.tasks` |

**复核结论**：**无违例**。Phase 1 设计（[data-model.md](data-model.md) + [contracts/](contracts/) × 4 + [quickstart.md](quickstart.md)）未引入任何新的宪法冲突；**唯一**的宪法相关动作 = G13 的**四处**修订落地（内容逐字取自 spec H 段，spec MUST NOT 自设例外）—— 该修订**已由 Maintainer 于 2026-10-30 前置落地**，本 Phase 只核对（R-19）。→ **Phase 1 设计放行** → 可进入 `/speckit.tasks`。

---

## Project Structure

### Documentation (this feature)

```text
specs/001-donkey-init-workspace/phase-4-cli-version/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output（决策 R-01 ~ R-19）
├── data-model.md        # Phase 1 output（实体 / 版本取值状态机 / 计数口径）
├── quickstart.md        # Phase 1 output（可执行的验证指南）
├── contracts/           # Phase 1 output
│   ├── cli-contract.md            # `version` 命令面 + 输出契约 + 退出码 + 范围外登记
│   ├── version-contract.md        # 版本取值来源契约（元数据优先 / 回退 / 不一致 / `v` 前缀）
│   ├── exit-codes.md              # 本 Phase 不新增任何码值 —— 与既有全局映射表的关系
│   └── constitution-amendment.md  # 宪法四处修订的逐字文本与锚点（FR-036 / H 段）
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
donkey/
├── __init__.py                      # 不动（__version__ = "0.1.0" 是回退源，FR-017 / FR-026）
├── __main__.py                      # 不动（模块入口，FR-006 的等价性载体）
├── core/
│   ├── version.py                   # ← 本 Phase 唯一的运行时代码新增
│   │                                #   resolve_version()  底层取值（元数据优先 → __version__ 回退）
│   │                                #   version_string()  展示值 "v" + 底层取值
│   ├── api.py                       # 仅改 InitResult docstring 的 3 处计数（R-14）
│   │                                # + 【D-22】InitResult 升为契约 v2（+4 字段 + items）
│   ├── exceptions.py                # 不动（不新增 Error class，FR-029）
│   ├── exit_codes.py                # 不动（不新增码值，FR-029）
│   └── workspace/
│       ├── init.py                  # 【D-22】render_templates 改返回逐项明细 list[InitItem]
│       └── manifest.py              # 【D-21】删 "version" 字段；donkey_version 改动态取值
├── cli/
│   └── cli_client.py                # 注册 version 子命令（无参数）+ 一行 print
│                                    # + init 子解析器 help/description 的 2 处过期文案（46 → 54）
│                                    # + 【D-22】init 摘要九字段 + 逐项明细

tests/
├── unit/
│   ├── test_cli_version.py          # 新增（版本解析三分支 + 前缀拼接 + CLI 输出形态）
│   ├── test_init_report.py          # 新增（【D-22】init 执行报告：摘要分解 + 逐项明细）
│   ├── test_cli_client.py           # P1 既有 —— 【D-22】1 处断言改写（登记见 spec 后续修订登记 §2b）
│   ├── test_init_workspace.py       # P1 既有 —— 不动
│   ├── test_template_skeleton.py    # P2 既有 —— 【D-21】清单字段断言 + 【D-22】9 处断言改写
│   └── test_builtin_tools.py        # P3 既有 —— 【D-22】1 处计数断言改写
├── integration/
│   ├── .gitkeep                     # 目录占位（保留）
│   └── test_init_to_load.py         # P3 既有 —— 不动（本 Phase 不新增集成层用例，G4）
└── e2e/phase/
    ├── verify_phase_f001_p1.py      # P1 既有 —— 不动（必须仍全绿）
    ├── verify_phase_f001_p2.py      # P2 既有 —— 【D-22】2 处字面量改写
    ├── verify_phase_f001_p3.py      # P3 既有 —— 【D-22】3 处字面量改写
    └── verify_phase_f001_p4.py      # 新增（7 个黑盒断言 ↔ 7 个 User Story）

.specify/memory/constitution.md      # 宪法修订：[D-20]（4 处，前置落地）+【D-21】/【D-22】（本轮落地）
harness/features/README.md           # 【D-21】§5.6 F002 必读备忘录 +【D-22】§4.8 init 执行报告
harness/features/立项书.md            # 【D-21】§1.3 / Q-07 / §4.6.1 +【D-22】§4.6.1 执行报告
specs/.../phase-2-template-skeleton/spec.md   # 【D-21】追加「后续修订登记」段（FR-019 / FR-021 / FR-017）
docs/User_Guide/01_init_workspace.md           # 用户手册同步（清单三字段 + init 输出形态）
```

> **（2026-10-30 补登 · 宪法 [D-21] / [D-22]）**：上表已补齐本轮两项变更实际触及的**全部**文件 ——
> 交付面比原计划大：除 `version` 命令本身外，还包含「工作区清单字段变更」与「`donkey init`
> 执行报告变更」两条线（后者牵动**库 API 契约 v2** 与 **5 个既有测试文件**的断言改写）。
> 逐条登记见 spec.md 文末「后续修订登记」段。

**Structure Decision**：沿用**单包 + 三层测试**结构（**Option 1**，与 F001-P1 / P2 / P3 完全一致）—— 不引入新包、不引入新分层、不新增顶层目录。本 Phase 的结构变化是**一条新的核心层模块 + 三个新测试文件 + 四处既有源文件改动 + 五个既有测试文件的断言改写 + 五份既有文档的同步**（`constitution.md` 的 [D-20] 修订已由 Maintainer 于 2026-10-30 前置落地，不计入实施期改动）。

---

## 复杂度与风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| **版本值有两个来源**（分发元数据 vs `__version__`） | 用户看到两个不同的版本号 → 正是 Q2 要消灭的"五花八门" | R-03/R-04/R-05 钉死**单一解析序**（元数据 → 回退 `__version__` → 不一致时以元数据为准）；FR-019 要求运行期**只有一个**来源 |
| **`v` 前缀逻辑散落三端** | F005 / F006 各拼一次 → 将来出现 `0.1.0` 与 `v0.1.0` 两种记法 | R-02 把拼接收敛到核心层 `version_string()`，三端复用同一函数 |
| **e2e 期望值随安装形态漂移** | 安装陈旧时硬编码断言假失败 | R-09：期望值取自工作树 `pyproject.toml` 的声明值 + 另行断言该声明为 `0.1.0`（SC-003）；R-18：**双比对**（工作树声明值 + 安装分发元数据值）—— 两者不等（陈旧安装）时以**元数据值**为期望值并**显式断言**该不等情形 |
| **"元数据不可得"分支难以真复现** | SC-007 / US6 的回退路径只能靠打桩 → 违背 FR-033 的黑盒约束 | R-10 的**副本法**（复制 `donkey/` 包到临时目录 → 同级无 `*.egg-info`）**实测**命中 `PackageNotFoundError`，全程零打桩、零业务代码 import |
| **`PYTHONPATH` 方案的陷阱**（曾被考虑） | 指向仓库根时 `donkey.egg-info` 会随之被发现 → 元数据照样命中，**无法**复现回退分支 | R-10 已**实测排除**该方案；副本法不依赖 `PYTHONPATH` |
| **元信息命令被后续 Feature 扩张为业务命令** | `version` 开始需要 Error class / exit code 段位 / 库 API → 绕过 F 编号与段位治理 | 宪法 §4.2 修订条款自带**边界条款**（spec H 段 (a) 末句）；spec FR-023 / FR-029 把它固化为本 Phase 的约束；一旦越界 MUST 先按 §6.2 取得 F 编号 |
| **README 与本 Phase 脱节** | 项目索引里看不到 F001-P4 | R-13：登记载体 = [D-20] 的**影响面**条目（已指名本 Phase 目录）；README **逐字未改**（D-3 的有意例外，SC-012 承载） |
| **既有断言被本 Phase 改红** | 违反 FR-034 / SC-009 | R-15 已**逐项 grep 核对**：「46 个模板条目」0 命中、`templates=46` 0 命中、无断言依赖子命令列表 → **无需**任何阶段边界改写；本 Phase **不动** 4 个既有测试文件 |
| **退出码段位表被扩张** | 违反 N-08 | FR-029 / SC-008：新增码值 0 个、新增 Error class 0 个、映射表与段位表**逐字不改**；`version` 只走既有的 `0` 与 `1` |

---

## 实施顺序（任务拆解留给 `/speckit.tasks`）

```text
① 宪法修订核对   constitution.md：§4.2.1 豁免小节 / §4.3 第 253 行括注 / §4.3 第 269 行 v1 baseline 限定语 / 第 5 章 [D-20]
                 —— **已由 Maintainer 于 2026-10-30 前置落地（4 处）**，本 Phase 只**核对、不改**（R-12 / R-19）
② 版本解析模块   donkey/core/version.py：resolve_version() + version_string()（R-01 ~ R-05）
③ 单元测试       tests/unit/test_cli_version.py：解析三分支 + 前缀 + 输出形态（R-11）—— **TDD：先写测试并确认失败**
④ CLI 子命令     cli_client.py：注册 version 子命令（无参数）+ 一行 print（R-06 ~ R-08）
⑤ 黑盒验收       tests/e2e/phase/verify_phase_f001_p4.py：7 断言 ↔ 7 个 User Story（R-09 / R-10 / R-16 / R-18）
⑥ 过期文案       cli_client.py 的 2 处 + api.py 的 3 处（R-14）—— **落在 tasks Phase 10**（与 ④ 同文件 MUST 顺序提交）
⑦ 全量验证       既有三套 verify + 单元 + 静态检查 + 门禁冒烟（§"可执行测试命令列表"）
```

> **编号 ≠ 相位**：① 是**核对**而非编辑 —— 宪法修订**已由 Maintainer 于 2026-10-30 前置落地**，实施期 MUST **保持其逐字不变**（spec FR-036 / R-19）；其余按依赖排列（③ 单元测试 MUST **先于** ④ CLI 子命令 —— 本 Phase 强制 TDD；⑥ 过期文案落在 **tasks Phase 10**，因与 ④ 同文件 MUST 顺序提交）。

---

## 后续 Phase / 仓库级（不属本 Phase）

| 事项 | 归属 |
|---|---|
| `donkey web version` / `donkey gui version`（客户端版本入口） | **F005 / F006**（spec FR-005 / FR-023 / G 段；宪法 N-11 / §2.8 的三端对等要求） |
| 节点级版本号（`vx.y.z` 的节点枚举与逐节点版本） | **F004-P7 `agent_loop`**（spec FR-015 / FR-024） |
| 工作区清单 `donkey_version` 与当前运行时版本的对比 / 迁移提示 | **F002 `donkey load`**（spec FR-025；宪法 D-03） |
| 节点清单 / 节点 id 序号的展示 | **F004-P7** |
| 三套版本号体系（软件版本 / 图版本 / workspace 格式版本）之间关系的**规定** | 全文至今**无规定** —— 本 Phase **不**自设（spec FR-021 / Edge Cases「其它边界」） |
| 图形化版本展示（web / gui 的版本页） | F005 / F006 |

---

## Complexity Tracking

> **本 Phase 涉及宪法修订 4 处（spec FR-036 + H 段，已由 Maintainer 批准并于 2026-10-30 前置落地）**：宪法 §4.2.1 新增「元信息命令豁免」小节、§4.3 第 253 行加括注限定语、§4.3 第 269 行 v1 baseline 句加限定语、第 5 章新增 **[D-20]**。实施期本 Phase 只**核对、不改**（R-19）。
> **本 Phase 不涉及任何宪法临时例外（§6.3）** —— E-01 已于 F001-P3 到期闭合、E-02 已于同日转为正式条款 [D-19] 并转为历史登记；本 Phase **不新增**临时豁免、**不新增** exit code 段位、**不新增** Error class、**不在 spec 内自设任何宪法例外**（spec FR-031）。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **依宪法 §4.3 第 269 行的既有豁免限定语执行**（该句**已含**「**（元信息命令按 §4.2 豁免）**：… 故本句的 1:1 口径对元信息命令**不适用**」—— 本 Phase 属该豁免的**适用对象**，**不是**「打破宪法」）：「1 Phase = 1 子段 = 1 提示词文件 = 1 verify 脚本」对 F001-P4 **不适用**两项（① 不占 exit code 子段；② 不需要提示词文件）** | `version` 是**只读元信息命令**：不承载可失败的业务能力、不需要 Error class / exit code 段位 / 库 API → 无子段可分配。**授权 = 宪法 §4.2.1 + §4.3 两处限定语 + [D-20]**（已由 Maintainer 于 2026-10-30 前置落地）。Maintainer 已决定**不修订** `harness/features/README.md`（其非强制），故该例外的**登记义务 MUST 落在 spec**（spec FR-030 / SC-012） | ❌ 给 `version` 分配一个空子段（如 exit 5）→ 凭空占用段位、违反 N-08 的"预留码不分配"惯例；❌ 把它并入 F001-P3 的子段 → 两个 Phase 共享一个子段，破坏"一个 Phase = 一个子段"的语义；❌ **改 README 消除该例外** → Maintainer 已明确决定不修订（非强制文档），改它等于擅自扩大本 Phase 范围 |
| **依宪法 §4.2.1 的「元信息命令豁免」条款执行**（`version` **不登记 F 编号** —— **不是**「打破『一级命令已被 F 编号锁死』惯例」；宪法 §4.3 第 253 行的限定语**已把该惯例的适用对象收窄为「核心功能的」一级命令**）** | 版本号查询不可缺少但不属于核心功能；套用 F 编号会污染 §4.2 的"核心功能"语义与 §4.5 的图版本口径（[D-20] 的动机）。宪法的**修订**（豁免条款 + 限定语）已由 Maintainer 批准并逐字登记在 spec H 段 | ❌ 把它登记成新的 F 编号（如 F007）→ 污染 F 编号表、且 F 编号表锁定的是"核心功能"的一级命令；❌ 在 spec 内**自设**豁免而不改宪法 → 违反宪法 §6.1（与宪法冲突者须按 Governance 流程修订）/ §6.3（例外须在宪法登记册登记），并与本 plan 的 Complexity Tracking 互斥 |
| （无其它） | —— | —— |

---

## 可执行测试命令列表（"Phase 完成" 的硬性证据）

```bash
# ① 前置套件（必须全绿 —— FR-034 / SC-009）
pytest tests/e2e/phase/verify_phase_f001_p1.py -v    # 7 个断言
pytest tests/e2e/phase/verify_phase_f001_p2.py -v    # 14 个断言
pytest tests/e2e/phase/verify_phase_f001_p3.py -v    # 16 个断言
pytest tests/unit/test_init_workspace.py -v
pytest tests/unit/test_template_skeleton.py -v
pytest tests/unit/test_builtin_tools.py -v
pytest tests/integration/test_init_to_load.py -v   # P3 既有 —— 必须仍全绿（与 tasks T006 的基线一致）

# ② 本 Phase 套件
pytest tests/unit/test_cli_version.py -v             # 版本解析三分支 + 输出形态
pytest tests/e2e/phase/verify_phase_f001_p4.py -v    # 7 个断言

# ③ 静态检查（FR-035 / SC-010）
ruff check donkey/ tests/
mypy donkey/ tests/

# ④ 覆盖率（独立命令，MUST NOT 写进 addopts）
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80

# ⑤ 完整套件
pytest tests/ -v

# ⑥ 宪法修订交付自检（FR-036 / SC-012）—— 4 处，已落地，本 Phase 只核对
grep -n "元信息命令" .specify/memory/constitution.md            # §4.2.1 豁免小节 / §4.3 括注 / §4.3 v1 baseline
grep -n "核心功能的" .specify/memory/constitution.md             # §4.3 第 253 行括注
grep -n "元信息命令按 §4.2 豁免" .specify/memory/constitution.md # §4.3 第 269 行 v1 baseline 限定语
grep -n "\[D-20\]" .specify/memory/constitution.md               # 第 5 章 [D-20]
git diff --stat harness/features/README.md                      # MUST 为空（逐字未改）

# ⑦ 命令面冒烟
python3 -m donkey version            # → v0.1.0（退出码 0）
python3 -m donkey version --bogus    # → 退出码 1（不是 2）
python3 -m donkey --version          # → 退出码 1（顶层无该标志）
```

**详细逐条验证步骤见 [quickstart.md](quickstart.md)。**
