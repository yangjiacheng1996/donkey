---

description: "Task list for F001-P4 cli_version —— donkey version 查询版本号"
---

# Tasks: F001-P4 `cli_version` —— `donkey version` 查询版本号

**Input**: Design documents from `specs/001-donkey-init-workspace/phase-4-cli-version/`
（spec.md · plan.md · research.md · data-model.md · contracts/ ×4 · quickstart.md）

**Prerequisites**: plan.md（必需）、spec.md（必需，用户故事）、research.md、data-model.md、contracts/、quickstart.md

**Tests**: 含测试任务 —— spec FR-032 要求黑盒脚本含 **7** 个断言函数、FR-033 要求其纯黑盒，SC-007 明文要求「该回退路径 MUST 有单元测试覆盖」。故本清单**强制**按 TDD 组织（先写测试 → 确认失败 → 再补实现）。

**Organization**: 任务按用户故事分组。**本 Phase 的 7 个用户故事是"验收切片"而非"实现切片"** —— 7 个故事 ↔ 7 个 e2e 黑盒场景一一对应，但实现上共享**同一条命令**与**同一个版本解析模块**（data-model.md §1）。故本清单的组织原则为：

| 层次 | 内容 | 对应 Phase |
|---|---|---|
| **授权基础** | 宪法**四处**修订（§4.2.1 豁免小节 / §4.3 第 253 行括注 / §4.3 第 269 行 v1 baseline 限定语 / [D-20]）—— **已由 Maintainer 于 2026-10-30 前置落地**，Phase 1 只**核对**、是其余一切交付物的授权前提 | Phase 1（Setup） |
| **共享地基** | 核心层版本解析模块 `donkey/core/version.py`（2 个公开函数）—— **7 个故事全部依赖它**（每个故事都要读版本值） | Phase 2（Foundational） |
| **实现切片** | CLI 子命令注册 + 一行 `print` —— **全 Phase 仅此一处实现**，在 US1 阶段一次写完 | Phase 3（US1） |
| **验收切片** | 每个故事的行为硬化断言（单元层）+ 对应的 e2e 黑盒场景函数 | Phase 3 ~ Phase 9（US1 ~ US7） |
| **收尾** | 过期文案同步（FR-037）+ 全量验证 + 静态检查 + 门禁冒烟 | Phase 10（Polish） |

> ⚠️ **为什么 CLI 实现在 US1 阶段一次写完、而不是分散到各故事**：spec 的 **US1 验收场景 1** 就要求"`donkey version` 退出码 `0`、stdout 恰好一行、内容为 `resolve_version()` 的解析结果（常规安装形态下 = `v0.1.0`）"→ US1 要能**独立验证**，该命令必须完整就位。若把子命令注册推迟到 US3/US5，US1 的独立测试将永远无法通过。故：**实现全在 US1**，US2 ~ US7 的阶段只做**行为硬化 + 断言**（与 F001-P2 / F001-P3 的"资产全在 US1、其余故事只做行为硬化与断言"同构）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可**并行推进**（**无未完成任务的依赖**）—— ⚠️ **同一文件内的多个 `[P]` 任务 MUST 分批提交**（逐文件约束见下方「受限（不可并行）」表）
- **[Story]**: 该任务归属的用户故事（US1 ~ US7）；Setup / Foundational / Polish 阶段**无** story 标签
- 描述中 MUST 含**精确文件路径**

> **编号编排说明**：任务 ID 按**逻辑分组**编排（T001 ~ T006 属 Phase 1、T007 ~ T011 属 Phase 2 …），**非文档序**；ID 一经分配 MUST NOT 重排或复用。
> **编号 ≠ 相位**：T032 / T033（过期文案同步）落在 **Phase 10**（收尾）而**不是** Phase 1 —— 因为 T033 改的是 `donkey/cli/cli_client.py`，与 US1 的 T015 **同文件**（同文件 MUST 顺序提交），放在 Phase 1 会造成跨相位同文件冲突。
>
> **本清单的权威源与镜像**：契约值（`v0.1.0` 展示形态 / 底层取值 `0.1.0` / 54 / 48 / 48 / 退出码 `{0,1}` / 5 秒上限）的**唯一权威源 = spec FR 与 contracts/**；plan R-xx、data-model §、本清单各处均为**镜像** —— 口径变更 MUST 先改 spec，再逐处同步镜像。
>
> **实现要点引用**：涉及非显然实现选择的任务 MUST 标注对应的 research.md 决策编号（R-xx）—— 实现者 MUST 先读该决策的"理由"再动手。

## Path Conventions

- **单包结构**：仓库根即包根 `donkey/`；`donkey/core/` 为引擎层、`donkey/cli/` 为客户端层
- **本 Phase 新增的唯一运行时代码文件**：`donkey/core/version.py`（核心层，spec FR-020）
- **测试**：`tests/unit/`（函数级，新增 `test_cli_version.py`）、`tests/e2e/phase/`（黑盒子进程验收，新增 `verify_phase_f001_p4.py`）
- **治理文件**：`.specify/memory/constitution.md`（宪法修订**已由 Maintainer 于 2026-10-30 前置落地（4 处）** —— 本 Phase 只**核对、不改**）、`harness/features/README.md`（**逐字未改**）

---

## Phase 1: Setup (Shared Infrastructure) — 宪法修订核对（授权基础）+ 基线快照

**Purpose**: **核对**宪法**四处**修订（**已由 Maintainer 于 2026-10-30 前置落地** —— 本 Phase 只核对、不改，它是其余一切交付物的授权前提，spec FR-036 / Clarifications Q5(a) + Session 2026-10-30（analyse 缺陷修复轮）Q6 / Q8），并固定"既有套件全绿"的基线快照。

- [X] T001 [P] 安装开发期依赖并确认控制台脚本可用：执行 `pip install -e ".[dev]"`（运行期依赖 MUST 仍恰为 **1** 个 `langgraph-checkpoint-sqlite>=3.1,<4`，**MUST NOT** 新增任何依赖 —— spec FR-027 / plan Technical Context）；确认 `which donkey` 可解析到本工作树内的包（解析规则见 contracts/cli-contract.md §5；不可用时验收脚本会回落到 `python -m donkey` 并打印一次告警，**不阻断**实施）　〔覆盖 spec FR-027 · SC-010〕
- [X] T002 **核对** `.specify/memory/constitution.md` 的 **§4.2.1「元信息命令豁免」小节**已落地（四处锚点与核对行号见 research.md R-12） —— 该小节 MUST 存在、且正文 MUST **逐字**等于 spec **H 段 (a)** 的两段（豁免条款正文 + 边界条款；宪法第 245-249 行）；宪法修订**已由 Maintainer 于 2026-10-30 前置落地**，本任务 MUST **只核对、不改写**（MUST NOT 再新增 / 改写 / 缩减该小节 —— spec FR-036）；**若发现不符，MUST 报错并停下**，MUST NOT 自行改写、不得"顺手修好"；**MUST NOT** 在 §4.2 的 F 编号表里加行、**MUST NOT** 改动表内既有任何一行、**MUST NOT** 改动"任何 spec / plan / tasks / 代码 / 文档中出现 F 编号引用必须与上表**字面对齐**。"这一句（spec FR-031）；**MUST NOT** 改动 `harness/features/README.md`（spec FR-030 / SC-012）。**授权来源 = Maintainer 已批准并已前置落地的宪法修订**（宪法 §6.2 第 2 条），spec MUST NOT 自设任何宪法例外（spec FR-031）　〔覆盖 spec FR-031 / FR-036 · SC-012〕
- [X] T003 **核对** `.specify/memory/constitution.md` 的 **§4.3 第 253 行**「**核心原则**」段的括注已落地 —— 该括注 MUST **逐字**等于 spec **H 段 (b)** 的登记文本（**内层文本**：「**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免」—— 宪法第 253 行的**外层圆括号**属句子的一部分，MUST NOT 因其判 FAIL；该括注的**完整句**逐字文本见 contracts/constitution-amendment.md §2）；**并核对 §4.3 第 269 行的 v1 baseline 句含「**（元信息命令按 §4.2 豁免）**」限定语**（spec **H 段 (b2)** —— 该限定语整段 MUST 与 H 段逐字一致）；宪法修订**已由 Maintainer 于 2026-10-30 前置落地**，本任务 MUST **只核对、不改写**这两处；**MUST NOT** 改动 §4.3 的规则 A / 规则 B 两张表、**MUST NOT** 改动"Phase 与 exit code 子段在 v1 baseline 中 1:1 对齐"这一句；**若发现不符，MUST 报错并停下**，MUST NOT 自行改写（spec FR-036 / H 段；核对文本见 contracts/constitution-amendment.md §2 与 §2b）　〔覆盖 spec FR-030 / FR-031 / FR-036 · SC-012〕
- [X] T004 **核对** `.specify/memory/constitution.md` 的 **第 5 章 ADR 表末尾**存在 **[D-20]** 一行 —— 该行 MUST **逐字**等于 spec **H 段 (c)**（= 宪法第 377 行的整行原文），且 [D-20] MUST 是表内**最后一行**（ADR 编号**只增不删**，当前最大为 [D-19]）；宪法修订**已由 Maintainer 于 2026-10-30 前置落地**，本任务 MUST **只核对、不改写**；**MUST NOT** 再追加 / 改写该行、**MUST NOT** 改动 [D-01] ~ [D-19] 任何一条、**MUST NOT** 在 §6.3 例外章节新增任何临时例外（本修订是**正式条款**）、**MUST NOT** 顺带修订 `harness/features/README.md`；**若发现不符，MUST 报错并停下**，MUST NOT 自行改写（spec FR-036 / H 段；核对文本见 contracts/constitution-amendment.md §3）　〔覆盖 spec FR-036 · SC-012〕
- [X] T005 执行 contracts/constitution-amendment.md §4 的**修订后自检清单**（**8 项**）：① `grep -n "元信息命令" .specify/memory/constitution.md` MUST 命中 **§4.2.1 / §4.3 括注 / §4.3 v1 baseline**；② `grep -n "核心功能的" .specify/memory/constitution.md` MUST 命中 §4.3 的「核心原则」段；③ `grep -n "元信息命令按 §4.2 豁免" .specify/memory/constitution.md` MUST 命中 §4.3 的 v1 baseline 句；④ `grep -n "\[D-20\]" .specify/memory/constitution.md` MUST 命中第 5 章；⑤ ADR 编号连续性（[D-01] ~ [D-20] 齐全且 [D-20] 在表尾）；⑥ 以**基线 commit**（实施开始前记录的 `HEAD`）为基准的 `git diff <基线commit> -- .specify/memory/constitution.md` 只含**四处**变更（§4.2.1 插入 / §4.3 改**两句**：第 253 行括注 + 第 269 行 v1 baseline 限定语 / 表尾加一行）—— **注**：MUST NOT 用裸 `git diff`（若宪法修订在实施开始前被单独提交，裸 `git diff` 会为空而误判 FAIL）；实施者 MUST 先记录基线 commit；⑦ **`git diff --stat harness/features/README.md` MUST 为空**（README 逐字未改 —— spec FR-030 / SC-012）+ 三个既有 Phase 目录 `git diff --stat` MUST 为空；⑧ **宪法四处措辞 MUST 与 spec H 段 (a) / (b) / (b2) / (c) 的登记文本逐字一致**（一字不差 —— 任一处不符即判 FAIL，MUST 报错并停下，MUST NOT 自行改写）；**(b) 处的比对基准 = H 段 (b) 的内层文本**（宪法第 253 行的**外层圆括号**属句子的一部分 —— MUST NOT 因其判 FAIL，见 spec H 段 (b) 的「核对基准」注 + contracts/constitution-amendment.md §4 第 8 项）　〔覆盖 spec FR-030 / FR-034 / FR-036 · SC-009 / SC-012〕
- [X] T006 [P] 固定**基线快照**：逐条执行 `pytest tests/e2e/phase/verify_phase_f001_p1.py -v`（**7** 个断言）/ `verify_phase_f001_p2.py -v`（**14** 个）/ `verify_phase_f001_p3.py -v`（**16** 个）/ `tests/unit/test_init_workspace.py` / `tests/unit/test_template_skeleton.py` / `tests/unit/test_builtin_tools.py` / `tests/integration/test_init_to_load.py`，确认 **全部 PASS** 并记录各文件的断言计数；另复核 research.md R-15 的结论（`tests/` 下「46 个模板条目」**0 命中**、`templates=46` **0 命中**、无断言依赖子命令列表）→ 本 Phase **无需**登记任何阶段边界改写。**该快照是 Phase 10 的对照基线**（spec FR-034 / SC-009）　〔覆盖 spec FR-034 · SC-009〕

**Checkpoint**: 宪法**四处**修订已核对并通过自检（8 项）+ 既有套件基线全绿 —— 实施其余交付物的授权前提已就位

---

## Phase 2: Foundational — 核心层版本解析模块（7 个故事共享地基）

**Purpose**: 落地 `donkey/core/version.py` —— 核心层版本取值解析（spec FR-016 ~ FR-021 / plan R-01 ~ R-05）。**7 个用户故事全部依赖它**（每个故事都要读版本值），故本阶段 MUST 在任何故事阶段之前完成。

- [X] T007 [P] 在 `tests/unit/test_cli_version.py` 写**核心层解析的单元测试**（单元测试落点见 research.md R-11 —— **新建**该文件，**不动** F001-P1 的 `test_cli_client.py`；先写，确认此时**失败**）：① **B-1 命中** —— 分发元数据可读时 `resolve_version()` 返回该值；② **B-2 不可得** —— 以 monkeypatch 让 `importlib.metadata.version` 抛 `importlib.metadata.PackageNotFoundError` 时，`resolve_version()` MUST 回退到 `donkey.__version__`（MUST NOT 抛异常、MUST NOT 返回空串 —— spec FR-017）；③ **B-3 不一致** —— 元数据值 ≠ `__version__` 时 MUST **以元数据为准**（MUST NOT 报错、MUST NOT 告警 —— spec FR-018）；④ `version_string()` MUST 等于 `"v" + resolve_version()`（spec FR-013）；⑤ MUST 只捕获 `PackageNotFoundError` —— 断言其它异常**不被**吞掉（沿用 F001-P1 契约 M-03 的"不得宽泛捕获"口径）。**MUST NOT** 打桩 `donkey.core.api`（本 Phase 不动它）　〔覆盖 spec FR-013 / FR-016 / FR-017 / FR-018 · SC-007〕
- [X] T008 在 `donkey/core/version.py` 创建模块骨架：docstring MUST 说明本模块是**core 版本取值解析**、**唯一运行期来源**（spec FR-019）、`v` 前缀的语义（显示前缀，非版本号的一部分 —— spec FR-013）、以及"**底层取值**与 `pyproject.toml` / `__version__` / 工作区清单 `donkey_version` 逐字节一致（**常规安装形态**下；陈旧安装形态以分发元数据为准 —— spec FR-018）"的契约；MUST 导出 `__all__ = ["resolve_version", "version_string"]`；**MUST NOT** import `langchain` / `langgraph` / `sqlite3` / `argparse` / `click` / `typer`（宪法 N-04 / N-05）、**MUST NOT** 读取任何环境变量、**MUST NOT** 打印 / 返回退出码 / 退出进程（宪法 N-05）　〔覆盖 spec FR-020 / FR-027 / FR-031 · SC-010〕
- [X] T009 在 `donkey/core/version.py` 实现 `resolve_version() -> str`：**优先**取 `importlib.metadata.version("donkey")`（发行版名固定为 `donkey` —— spec FR-016 / research.md R-03；**MUST NOT** 读 `pyproject.toml`，它是构建期文件）；捕获 `importlib.metadata.PackageNotFoundError` 后**回退** `from donkey import __version__`（`donkey/__init__.py` **零 import** → **无循环导入** —— research.md R-04）；元数据与 `__version__` **不一致时以元数据为准**、MUST NOT 报错 / 告警（research.md R-05）；**MUST 只捕获 `PackageNotFoundError`**（MUST NOT 用宽泛 `except Exception` —— F001-P1 契约 M-03）；**导入形态 MUST 钉死为 `import importlib.metadata` + 调用 `importlib.metadata.version("donkey")`**（MUST NOT 写成 `from importlib.metadata import version` —— 否则 T007 的 monkeypatch 打桩**静默失效**、用例假绿；F001-P1 `tests/unit/test_cli_client.py` 有同类教训）；MUST NOT 在本模块内硬编码任何版本字面量（取值 MUST 来自动态解析 —— spec FR-019；注意 `donkey/__init__.py` 的 `__version__` 与 `donkey/core/workspace/manifest.py` 的 `_DONKEY_VERSION` 属**别的用途**，MUST NOT 被误改 —— spec FR-026）　〔覆盖 spec FR-016 / FR-017 / FR-018 / FR-019 · SC-007〕
- [X] T010 在 `donkey/core/version.py` 实现 `version_string() -> str` = `"v" + resolve_version()` —— 前缀逻辑 MUST **单点收敛**在本函数（三端将来复用同一函数，否则同一值会出现 `0.1.0` 与 `v0.1.0` 两种记法 —— research.md R-02）；MUST NOT 返回任何其它内容、**MUST NOT** 读环境变量　〔覆盖 spec FR-012 / FR-013 · SC-003〕
- [X] T011 确认 T007 的单元测试**转绿**（`pytest tests/unit/test_cli_version.py -v`），并对 `donkey/core/version.py` 跑 `ruff check donkey/core/version.py` + `mypy donkey/core/version.py` 确认**零 error**（spec FR-035 / SC-010）；确认 `donkey.core.version` 的导入链中 `langsmith` **0 次**出现（宪法 N-12 / D-17 边界）　〔覆盖 spec FR-035 · SC-010〕

**Checkpoint**: 核心层版本解析就位且被单元测试覆盖 —— 用户故事实现可开始

---

## Phase 3: User Story 1 - 一条命令就能看到版本号 (Priority: P1) 🎯 MVP

**Goal**: `donkey version` 可用 —— stdout **恰好一行**、内容为 `resolve_version()` 的解析结果（**常规安装形态**下 = `v0.1.0`），退出码 `0`，stderr 为空；不需要 Python 绕路。

**Independent Test**: 执行 `donkey version`，断言退出码 `0`、stdout **恰好一行**且去掉行终止符后**逐字节等于** `resolve_version()` 的解析结果（**常规安装形态**下 = `v0.1.0`）、stderr 为空、两次执行 stdout **逐字节相同**；在**不存在 workspace** 的目录下执行同样成功。

### Tests for User Story 1 (TDD) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] 在 `tests/unit/test_cli_version.py` 写 **CLI 层输出形态**的单元测试：调用 `cli_client.main(["version"])` MUST 返回 `0`；`capsys` 捕获的 stdout MUST **恰好一行**、去掉行终止符后 == `"v" + resolve_version()`（即**元数据优先**的解析结果 —— spec FR-016 ~ FR-018），且在**常规安装形态**下（安装元数据值 == `donkey.__version__`）该值 MUST 等于 `v0.1.0`（spec FR-014）、MUST **不带** `[donkey version]` 前缀、**不带** `version=` 字段名、**无前导 / 尾随空白**（spec FR-007 / FR-010）；stderr MUST 为空（spec FR-009）；stdout 中版本值 MUST **恰好出现 1 次**（spec FR-008）；连续两次调用 stdout MUST **逐字节相同**（spec FR-011）。**若安装元数据与 `donkey.__version__` 不一致，MUST 按 FR-018 以**元数据**为准，MUST NOT 断言输出 == `donkey.__version__`（那会产生假失败）**　〔覆盖 spec FR-007 / FR-008 / FR-009 / FR-010 / FR-011 · SC-002 / SC-015〕
- [X] T013 [P] [US1] 创建 `tests/e2e/phase/verify_phase_f001_p4.py` 的骨架：MUST **黑盒**（MUST NOT import `donkey.*` 业务代码，只以子进程观察退出码 / stdout / stderr 与文件系统副作用 —— spec FR-033）；`donkey` 命令的解析规则 MUST 沿用 F001-P1 / P2 / P3 的口径（优先 PATH 上的控制台脚本 + 校验其解析到的包**位于当前工作树内**，不可用时回落到 `python -m donkey` 并**打印一次显式告警**，回落时以仓库根为工作目录 —— research.md R-16；辅助函数 MUST **自带一份副本**、MUST NOT 抽公共模块，MUST NOT 改动三个既有脚本）；MUST 提供**期望值取数**辅助（取数口径见 research.md R-09 + R-18）—— 该辅助 MUST **同时**提供**两个**期望来源：① **工作树声明值** = `pyproject.toml` 的 `version`（用标准库 `tomllib`）；② **安装分发元数据值** = `importlib.metadata.version("donkey")`（**允许** import 标准库 `importlib.metadata`；MUST NOT import `donkey.*` 业务代码 —— spec FR-033）；并**另行断言**工作树声明值当前为 `0.1.0`（spec SC-003 —— MUST NOT 让断言随安装形态漂移）；MUST 沿用 **5 秒**的单次耗时上限（spec SC-011 / research.md R-17）—— 且 MUST **断言**该上限（每次子进程调用 MUST 计时并在超限时 FAIL），MUST NOT 仅配置不断言；每次执行的**实测耗时 MUST 被记录**（供 T040 核对执行证据链）　〔覆盖 spec FR-032 / FR-033 · SC-001 / SC-003 / SC-011〕
- [X] T014 [US1] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 1**（US1 的 3 个验收场景）：① `donkey version` 退出码 `0`、stdout **恰好一行**、去掉行终止符后 == **期望值**（= T013 的**双比对**期望值：常规安装形态下 == `v0.1.0`；陈旧安装形态下 == **安装分发元数据值** —— spec SC-002 / SC-003 / FR-018；MUST NOT 把 `v0.1.0` 硬编码为唯一期望值）、stderr 为空；② 连续两次执行 stdout **逐字节相同**；③ 在**不存在 workspace** 的目录下执行同样退出码 `0`（MUST NOT 要求工作区存在）。**先写并确认此时失败**（命令尚未注册）　〔覆盖 US1 · spec FR-001 / FR-007 / FR-011 / FR-022 · SC-002 / SC-003 / SC-015〕

### Implementation for User Story 1

- [X] T015 [US1] 在 `donkey/cli/cli_client.py` 的 `_build_parser()` 注册 `version` 子命令（注册形态见 research.md R-06）：`subparsers.add_parser("version", help=..., description=...)`，**MUST NOT** 添加任何 `add_argument`（无位置参数、无可选开关 —— spec FR-001 / FR-002）；MUST NOT 在**顶层**添加 `--version` 标志（spec FR-038 / Clarifications Q4 / research.md R-07）；`main()` 中新增 `if args.command == "version": return _run_version()` 分支，`_run_version()` MUST 只做一件事 —— `print(version_string())`（**裸版本值**，MUST NOT 带前缀 / 字段名 —— spec FR-007 / FR-010；`print` 保证恰好一行 + 一个行终止符 —— research.md R-08），MUST **只 import** `donkey.core.version` 的 `version_string`（**MUST NOT** import `langchain` / `langgraph` / `sqlite3` —— 宪法 N-04）、MUST NOT 读任何环境变量、MUST NOT 触碰文件系统（spec FR-022）；MUST NOT 新增任何退出码 / Error class / 映射表条目（spec FR-029）；`prog="donkey"` 与 `add_subparsers(dest="command", required=True)` MUST NOT 改动　〔覆盖 US1 · spec FR-001 / FR-002 / FR-003 / FR-005 / FR-007 / FR-010 / FR-022 / FR-028 / FR-029 / FR-038 · SC-002 / SC-006 / SC-013 / SC-014〕
- [X] T016 [US1] 确认 T012 与 T014 **转绿**（`pytest tests/unit/test_cli_version.py -v` + `pytest tests/e2e/phase/verify_phase_f001_p4.py -v`），并跑 US1 的独立验证（quickstart **§2.1**）：`python3 -m donkey version` 输出 `resolve_version()` 的解析结果（**常规安装形态**下 = `v0.1.0`）、`| wc -l` == 1、两次执行逐字节相同（**§2.2 / §2.3 归 T019 / T022，MUST NOT 重复执行**；此处为**人工**独立验证路径，MUST NOT 与 T014 的自动化断言重复实现同一逻辑）；确认 `donkey --help` 的子命令列表**出现** `version` 条目（spec FR-003 / SC-013 —— 该断言的**自动化载体在 T026（场景 5 ⑤）**，此处为人工确认）　〔覆盖 US1 · spec FR-003 · SC-002 / SC-013〕

**Checkpoint**: User Story 1 完全可用 —— `donkey version` 可独立验证（本 Phase 的 MVP）

---

## Phase 4: User Story 2 - 版本号只有一个，不会出现两个打架的值 (Priority: P2)

**Goal**: 输出里**只有一个**版本值，且在**常规安装形态**下其底层取值与工作区清单的 `donkey_version` 字段**逐字节一致**（用户可直接拿它做迁移比对；陈旧安装形态以分发元数据为准 —— spec FR-018）。

**Independent Test**: 执行 `donkey version`，断言 stdout 中版本值**恰好出现 1 次**、形如 `v<数字>.<数字>.<数字>`；**常规安装形态**下去掉 `v` 前缀后的取值与工作区清单的 `donkey_version` 字段**逐字节一致**（陈旧安装形态以分发元数据为准 —— spec FR-018）。

### Tests for User Story 2 (TDD) ⚠️

- [X] T017 [P] [US2] 在 `tests/unit/test_cli_version.py` 写「**唯一版本值**」的单元测试：`version_string()` MUST 只含**一个**版本值（MUST NOT 出现第二个版本值、客户端版本、节点级版本信息、workspace 格式版本或工作区路径 —— spec FR-008）；其底层取值 MUST 与 **`importlib.metadata.version("donkey")`（可得时）** **逐字节一致**；该值**不依赖**安装形态（spec FR-016 / FR-018）。**常规安装形态**下该值 == `donkey.__version__` == `pyproject.toml` 的 `version` == 清单 `donkey_version`（spec FR-013）；MUST NOT 出现 workspace 格式版本（整数 `1`）—— spec FR-021。**若安装元数据与 `donkey.__version__` 不一致，MUST 按 FR-018 以**元数据**为准，MUST NOT 断言输出 == `donkey.__version__`（那会产生假失败）**　〔覆盖 US2 · spec FR-008 / FR-013 / FR-021 · SC-002 / SC-003〕
- [X] T018 [US2] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 2**（US2 的 2 个验收场景）：① stdout 中版本值**恰好出现 1 次**、形如 `^v\d+\.\d+\.\d+$`；② 去掉 `v` 前缀后的取值与**工作区清单的 `donkey_version` 字段**（`manifest.json`）**逐字节一致**（**常规安装形态下** —— 陈旧安装形态下该比较 MUST NOT 执行、亦 MUST NOT 断言，输出以**分发元数据**为准 —— spec FR-018 / SC-003 / US2 场景 2；**「陈旧清单」形态的额外跳过条件**：清单值被 F001-P2 FR-021 **锁死**为**当时的**版本，故该比对 MUST 以「**工作树声明值 == 清单字段**」为前提 —— 不成立时 MUST **跳过**该比对，MUST NOT 断言输出 == 清单字段（假失败），改以**分发元数据 / 工作树声明值**为准 —— spec Key Entities「常规安装形态 / 陈旧安装形态」+ Assumptions「版本号 bump 的跨 Phase 联动」）—— 该断言 MUST **只走真黑盒路径**：在临时目录以子进程执行 `donkey init` 生成一份工作区清单 → 读其 `donkey_version` 字段 → 与版本输出比对；**MUST NOT** 直接 import `donkey.core.workspace.manifest` 读取 `_DONKEY_VERSION`（那会 import `donkey.*` 业务代码，**违反 spec FR-033**）；MUST NOT 改写工作区清单（spec FR-026）；③ **双比对断言** —— 安装元数据值与工作树声明值**相等**时，输出底层取值 MUST == 二者；**不等**（陈旧安装）时，输出底层取值 MUST == **安装元数据值**（spec FR-018），且该不等情形 MUST 被**显式断言**（MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段 —— 那会产生假失败）（spec SC-003 / research.md R-18）　〔覆盖 US2 · spec FR-008 / FR-013 / FR-026 · SC-002 / SC-003〕

- [X] T019 [US2] 跑 US2 的独立验证（quickstart §2.2 —— 该节**只含**版本值计数核对）：`donkey version` 的版本值计数 == 1；确认 `tests/unit/test_cli_version.py` 与 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T017 / T018 转绿（**清单 `donkey_version` 的逐字节比对由 T018 ② 承载，MUST NOT 在此重复断言**）　〔覆盖 US2 · spec FR-008 · SC-002〕

**Checkpoint**: US1 与 US2 均可独立工作

---

## Phase 5: User Story 3 - 图还没建时也给得出确定的答案 (Priority: P3)

**Goal**: 主图尚未建成（F004-P7 之前）时，**常规安装形态**下版本值恒为 `resolve_version()` 的解析结果（= `v0.1.0`）—— 不是"未知"、不是"dev"、不是拿"图版本 0"冒充，且**不含**任何节点级版本信息。

**Independent Test**: 执行 `donkey version`，断言**常规安装形态**下其值恒为 `resolve_version()` 的解析结果（= `v0.1.0`；MUST NOT 是 `unknown` / `dev` / `v0.0.0` 一类的值），且输出中节点清单 / 节点独立版本号的出现次数为 **0**。

### Tests for User Story 3 (TDD) ⚠️

- [X] T020 [P] [US3] 在 `tests/unit/test_cli_version.py` 写「**取值恒定 + 无节点级信息**」的单元测试：展示值 MUST == `"v" + <底层取值>`，底层取值 MUST == `resolve_version()` 的解析结果（**元数据优先** —— spec FR-016 ~ FR-018）；**常规安装形态**下 == `donkey.__version__` == `0.1.0`（spec FR-014 / FR-013）；展示值在**常规安装形态**下恒为 `v0.1.0`、MUST NOT 是 `unknown` / `dev` / `v0.0.0` 一类的占位（spec FR-014）；输出 MUST **不含**节点清单、MUST NOT 含任何节点的独立版本号（MUST NOT 枚举节点 —— spec FR-015 / FR-024）；MUST NOT 取 workspace 格式版本（整数 `1`）—— spec FR-021。**若安装元数据与 `donkey.__version__` 不一致，MUST 按 FR-018 以**元数据**为准，MUST NOT 断言输出 == `donkey.__version__`（那会产生假失败）**　〔覆盖 US3 · spec FR-013 / FR-014 / FR-015 / FR-024 · SC-003〕
- [X] T021 [US3] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 3**（US3 的 2 个验收场景）：① **常规安装形态下**输出恒为 `v0.1.0`（MUST NOT 是 `unknown` / `dev` / `v0.0.0`；陈旧安装形态下按 FR-018 以**分发元数据**为准 —— spec US3 场景 1 / SC-003）；② 输出中**节点级版本信息的出现次数为 0**（MUST NOT 出现节点 id 清单或逐节点版本号）　〔覆盖 US3 · spec FR-014 / FR-015 / FR-024 · SC-003〕

- [X] T022 [US3] 跑 US3 的独立验证（quickstart §2.3）：`donkey version` 的值 == `resolve_version()` 的解析结果（**常规安装形态**下 == `v0.1.0`）、输出中无节点级信息；确认 `tests/unit/test_cli_version.py` 与 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T020 / T021 转绿　〔覆盖 US3 · spec FR-014 · SC-003〕

**Checkpoint**: US1 ~ US3 均可独立工作

---

## Phase 6: User Story 4 - 两种调用方式结果一致 (Priority: P4)

**Goal**: `donkey version` 与 `python -m donkey version` **完全等价** —— 退出码相同、stdout 逐字节相同、stderr 均为空。

**Independent Test**: 分别执行两条入口，断言退出码相同、stdout **逐字节相同**、stderr 均为空。

### Tests for User Story 4 (TDD) ⚠️

- [X] T023 [US4] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 4**（US4 的 2 个验收场景）：① 分别执行**控制台脚本**与**模块入口**，断言退出码相同、stdout **逐字节相同**、stderr 均为空；② 两条入口下的版本取值分别相等。**实现要点**：控制台脚本不可用时（解析不到本工作树内的包）该场景 MUST **显式跳过控制台脚本一侧**并只断言模块入口一侧 —— MUST NOT 因此**假失败**（spec FR-006 / research.md R-16 的既有约定）；控制台脚本不可用时 MUST 打印**一次显式告警**到 stderr（**非静默跳过**，沿用 F001-P1 既有约定）并只断言模块入口一侧；该降级 MUST 在 verify 脚本 stderr 中可见（spec SC-004 补充条款）　〔覆盖 US4 · spec FR-006 · SC-004〕
- [X] T024 [US4] 跑 US4 的独立验证（quickstart §2.4）：`donkey version` 与 `python -m donkey version` 的 stdout `diff` 为空、stderr 均为空、退出码相同；确认 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T023 转绿　〔覆盖 US4 · spec FR-006 · SC-004〕

**Checkpoint**: US1 ~ US4 均可独立工作

---

## Phase 7: User Story 5 - 用错了要报错，且报错方式跟别的命令一致 (Priority: P5)

**Goal**: 三类误用（未知开关 / 客户端参数 / 多余位置参数）**一律以退出码 `1`** 失败（**不是** argparse 默认的 `2`），stdout 为空、stderr 含用法提示；`donkey version --help` 以 `0` 结束；顶层 `donkey --version` 以 `1` 失败。

**Independent Test**: 断言三类误用的退出码**均为 `1`**、`--help` 为 `0`、顶层 `--version` 为 `1`。

### Tests for User Story 5 (TDD) ⚠️

- [X] T025 [P] [US5] 在 `tests/unit/test_cli_version.py` 写「**用法错误**」的单元测试：① `cli_client.main(["version", "--bogus"])` MUST 抛 `SystemExit` 且 `code == 1`（**MUST NOT** 为 `2` —— spec FR-028）；② `cli_client.main(["version", "web"])` 与 `cli_client.main(["version", "extra"])` MUST 同样 `code == 1`（MUST NOT 被静默忽略 —— spec FR-002 / FR-005）；③ `cli_client.main(["version", "--help"])` MUST 以 `code == 0` 结束（帮助请求**不**是用法错误 —— spec FR-004）；④ `cli_client.main(["--version"])` MUST 以 `code == 1` 失败（顶层**不提供**该标志 —— spec FR-038）；断言 MUST 取**退出码 == 1 且 stdout 不含任何版本号**，**MUST NOT 依赖 argparse 的具体报错措辞**（实测为「the following arguments are required: command」—— 因 `add_subparsers(dest="command", required=True)` 的必填校验**先于**未识别参数检查触发）。**口径**：子解析器 MUST 自动继承 `DonkeyArgumentParser` 的 `error()` 覆写（`add_parser` 以 `type(self)` 作 `parser_class` —— F001-P1 research.md R-01），MUST NOT 另建解析器类　〔覆盖 US5 · spec FR-002 / FR-004 / FR-005 / FR-028 / FR-038 · SC-006 / SC-013 / SC-014〕
- [X] T026 [US5] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 5**（US5 的 3 个验收场景）：① `donkey version --bogus` 退出码 **1**（MUST NOT `2`）、stdout 为空、stderr 含用法提示；② `donkey version web` / `donkey version extra` 退出码同为 **1**、stdout 为空；③ `donkey version --help` 退出码 **0**；④ `donkey --version` 退出码 **1** 且**不输出任何版本号**、**stdout 为空**；断言 **MUST NOT 依赖报错措辞**（实测为「the following arguments are required: command」—— 因 `add_subparsers(dest="command", required=True)` 的必填校验**先于**未识别参数检查触发，spec FR-038 / SC-014）；⑤ `donkey --help` 的子命令列表**出现** `version` 条目（spec FR-003 / SC-013）　〔覆盖 US5 · spec FR-002 / FR-003 / FR-004 / FR-028 / FR-038 · SC-006 / SC-013 / SC-014〕

- [X] T027 [US5] 跑 US5 的独立验证（quickstart §2.5）：三类误用（`--bogus` / `web` / `extra`）退出码均为 `1`、`donkey version --help` 为 `0`、`donkey --version` 为 `1`；确认 `tests/unit/test_cli_version.py` 与 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T025 / T026 转绿　〔覆盖 US5 · spec FR-028 · SC-006〕

**Checkpoint**: US1 ~ US5 均可独立工作

---

## Phase 8: User Story 6 - 装没装都能给出确定的版本 (Priority: P6)

**Goal**: 取不到安装分发元数据时（包未安装 / 非标准安装 / 从源码检出直接运行），命令**仍以退出码 `0`** 结束并给出**确定可解析**的版本值。

**Independent Test**: 在**取不到分发元数据**的环境下执行 `donkey version`，断言退出码 `0`、输出仍是确定可解析的版本值（不为空、不抛异常）。

### Tests for User Story 6 (TDD) ⚠️

- [X] T028 [US6] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 6**（US6 的 2 个验收场景）：**真黑盒**复现"分发元数据不可得" —— 把工作树的 `donkey/` **包目录**复制到 `tmp_path` 下（该副本**同级没有** `*.egg-info`），在该副本根执行 **`python -S -m donkey version`**（**MUST 带 `-S`** —— 屏蔽 site-packages）：① MUST 退出码 `0`、stdout 仍是一个**确定可解析**的版本值（MUST NOT 为空 / 抛异常 —— spec FR-017）；② 版本取值（底层取值）**不依赖**安装形态（取不到元数据时 MUST NOT 影响版本值 —— spec FR-017；FR-018 的**不一致**情形以**分发元数据**为准 —— spec US6 场景 2 / SC-007）。**实现要点**：MUST **先**在同一副本里断言 `importlib.metadata.version("donkey")` 确实抛 `PackageNotFoundError`（否则该场景**没有**真正覆盖回退分支 —— spec SC-007）；**`-S` 不可省** —— **实测**：已安装 donkey 的环境（如 CI 的 `pip install -e ".[dev]"`）里 site-packages 的 `donkey-*.dist-info` 仍会被 `importlib.metadata` 发现，仅靠"副本同级没有 `*.egg-info`**不足以**复现（research.md R-10 的修正记录）；`-S` 下 `donkey` 的导入链**完整**（实测不加载 `langgraph`，纯标准库）；MUST NOT 用 `PYTHONPATH` 指向仓库根（实测**无效**：仓库根的 `donkey.egg-info/` 会随之被发现、元数据照样命中 —— research.md R-10）；MUST NOT monkeypatch / import `donkey.*` 业务代码（spec FR-033）　〔覆盖 US6 · spec FR-017 · SC-007〕
- [X] T029 [US6] 跑 US6 的独立验证（quickstart §2.6）：副本内 `python -S -c "import importlib.metadata as md; md.version('donkey')"` 抛 `PackageNotFoundError`、`python -S -m donkey version` 仍输出 `v0.1.0` 且退出码 `0`；确认 `tests/unit/test_cli_version.py` 的 T007 **回退分支单元用例**与 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T028 均转绿（spec SC-007 要求回退路径**同时**有单元覆盖）　〔覆盖 US6 · spec FR-017 · SC-007〕

**Checkpoint**: US1 ~ US6 均可独立工作

---

## Phase 9: User Story 7 - 查询版本不会动我的东西 (Priority: P7)

**Goal**: `donkey version` 是**纯只读** —— 不创建 / 修改 / 删除任何文件，不读取工作区，不要求工作区存在。

**Independent Test**: 记录目标目录树的文件 / 目录 / 内容指纹，执行 `donkey version`，再次比对，断言**零变化**。

### Tests for User Story 7 (TDD) ⚠️

- [X] T030 [US7] 在 `tests/e2e/phase/verify_phase_f001_p4.py` 实现**场景 7**（US7 的 2 个验收场景）：① 在一个含若干文件的目录树里执行 `donkey version`，断言执行前后该目录树的**文件数 / 目录数 / 各文件内容指纹全部不变**（副作用数 = **0**）；② 工作区清单文件**未被创建、未被修改**。**补充**：命令 MUST 在**工作区不存在**（含 manifest 缺失或非法）与**只读文件系统**下同样成功（spec FR-022 / Edge Cases「只读性与作用域类」）　〔覆盖 US7 · spec FR-022 · SC-005〕
- [X] T031 [US7] 跑 US7 的独立验证（quickstart §2.7）：目标目录树的 `find` 输出 `diff` 为空、工作区清单 `manifest.json` 未被创建；确认 `tests/e2e/phase/verify_phase_f001_p4.py` 的 T030 转绿　〔覆盖 US7 · spec FR-022 · SC-005〕

**Checkpoint**: 全部 7 个用户故事均可独立验证

---

## Phase 10: 文案同步与 Polish —— 过期计数修正 + 全量验证

**Purpose**: 落地 spec FR-037 的**过期文案同步**（Maintainer 裁决纳入本 Phase 的范围，Clarifications Q5(b)）与全 Phase 的收尾验证。

- [X] T032 [P] 修正 `donkey/core/api.py` 的 `InitResult` docstring 中**3 处**过期计数：`templates_loaded` 的「P2 为 `46`」→ **`54`**；`files_created` 的「P2 全新创建为 `40`」→ **`48`**；`files_skipped` 的「P2 二次 init 为 `40`」→ **`48**`，并把"P2 为 / 为"的时代限定语改为当前口径 —— 权威源 = F001-P3 的 `contracts/cli-contract.md`「全新创建 / 二次 init / `--force`」三行计数表（spec FR-037 / SC-016）。**MUST 同步更新括注内的分解**：`files_created` 条目现写「文件型条目：37 文本 + 3 sqlite3」→ MUST 改为「**45 文本 + 3 sqlite3**」（清单 54 条 = 6 目录条目 + 48 文件型条目；48 = 45 文本 + 3 sqlite3 —— 已按 `donkey/core/workspace/templates/manifest.json` 核对）→ **否则 docstring 会出现「48 ≠ 45 + 3」的内部不自洽**。**MUST NOT** 改动 `InitResult` 的**字段名、字段顺序、类型与函数体**（spec FR-026 的口径只覆盖版本号，但本任务 MUST NOT 顺手动契约 —— 契约冻结在 F001-P1 FR-006）；**MUST NOT** 改动 `donkey/core/workspace/manifest.py` 的 `_DONKEY_VERSION`（F001-P2 FR-021 锁死 —— spec FR-026）　〔覆盖 spec FR-037 · SC-016〕
- [X] T033 修正 `donkey/cli/cli_client.py` 的 `init` 子解析器 **2 处**过期文案（`help` 与 `description` 各一处）：「生成模板骨架（**46** 个模板条目）+ 工作区清单。」→「生成模板骨架（**54** 个模板条目）+ 工作区清单。」（spec FR-037 / SC-016）。**依赖**：本任务与 **T015（US1）改的是同一个文件** → MUST 在 T015 之后**顺序提交**，MUST NOT 与其并行改写；**MUST NOT** 只改其中一处（两处字符串相同，漏改一处则 `--help` 与子解析器 usage 互相矛盾）；**MUST NOT** 改动 `init` 的参数面或行为　〔覆盖 spec FR-037 · SC-016〕
- [X] T034 执行**全量套件** `pytest tests/ -v` 并确认 **全部 PASS** —— 含三个既有 Phase 的 e2e（7 + 14 + 16 个断言）与全部单元 / 集成用例、以及本 Phase 的 7 个 e2e 断言与单元用例；逐条对照 T006 的**基线快照**确认既有断言**逐字未改**且仍全绿（spec FR-034 / SC-009）。**MUST NOT** 为了让本 Phase 变绿而改动任何既有测试文件（spec FR-034）　〔覆盖 spec FR-034 · SC-001 / SC-009〕
- [X] T035 执行静态检查 `ruff check donkey/ tests/` + `mypy donkey/ tests/`，确认**零 error**（spec FR-035 / SC-010）　〔覆盖 spec FR-035 · SC-010〕
- [X] T036 执行覆盖率 `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` —— 覆盖率 MUST 用**独立命令**度量，MUST NOT 写进 pytest 全局 `addopts`（否则 e2e 单独跑时覆盖率被拉到 0 而误报 —— 宪法 §4.6 / F001-P3 R-14）；确认 `donkey.core` 覆盖率 **≥ 80%**（新模块 `donkey/core/version.py` MUST 100% 被覆盖）　〔覆盖 spec FR-035 · SC-010〕
- [X] T037 执行**门禁冒烟**（quickstart §4）：① `grep -nE "import (langchain|langgraph|sqlite3|argparse)" donkey/core/version.py` MUST **0 命中**；② `grep -nE "import (langchain|langgraph|sqlite3)" donkey/cli/cli_client.py` MUST **0 命中**（**判据范围 = 本 Phase 新增 / 改动的这两个文件** —— spec SC-010；仓库中**既有**的 `donkey/core/workspace/sqlite3_templates.py` 对 `sqlite3` 的导入属 F001-P2 的冻结产物，**不计入**本条，MUST NOT 为此扩大本 Phase 范围）；③ `grep -rnE "langsmith|observability" donkey/` MUST **0 命中**（宪法 N-12）；④ `grep -rn "0\.1\.0" donkey/ --include=*.py` MUST **恰 2 处**命中（`donkey/__init__.py` = 回退源本身 + `donkey/core/workspace/manifest.py` = 工作区清单存储值，F001-P2 FR-021 锁死），且 `donkey/core/version.py` 与 `donkey/cli/cli_client.py` MUST **0 命中**（版本定义点唯一 —— spec FR-019）；⑤ `donkey/cli/cli_client.py` MUST **不含** `web` / `gui` 子解析器或任何**解析器占位**（spec FR-023）；⑥ MUST NOT 出现 `load` / `session` / `run` 相关实现（spec FR-025）　〔覆盖 spec FR-019 / FR-023 / FR-025 / FR-026 / FR-027 · SC-010〕
- [X] T038 执行**治理自检**（quickstart §5 + §6）：① 宪法**四处** grep（`元信息命令` / `核心功能的` / `元信息命令按 §4.2 豁免` / `[D-20]`）MUST **命中预期位置**（§4.2.1 / §4.3 第 253 行 / §4.3 第 269 行 / 第 5 章表尾），且 `git diff --stat harness/features/README.md` MUST **为空** —— **该组已在 T005 验证**，此处 MUST NOT 重复执行（MUST NOT 重复断言同一事实 —— spec FR-036 的自检以 T005 为准）；② `git diff --stat specs/001-donkey-init-workspace/phase-1-cli-validation/ specs/.../phase-2-template-skeleton/ specs/.../phase-3-builtin-tools/` MUST **为空**（三个既有 Phase 的 FR / SC 编号与断言逐字未改 —— spec FR-034）；③ `git diff --stat specs/.../phase-2-template-skeleton/contracts/` MUST **为空**（F001-P2 的三份**冻结快照** MUST NOT 被改 —— spec FR-037）；④ `python3 -m donkey init --help | grep -c "54 个模板条目"` MUST == 1 且 MUST NOT 出现「46 个模板条目」；⑤ `grep -nE "\b(46|40)\b" donkey/core/api.py` MUST **0 命中**　〔覆盖 spec FR-030 / FR-034 / FR-036 / FR-037 · SC-009 / SC-012 / SC-016〕
- [X] T039 执行**退出码零增量核对**（spec FR-029 / SC-008）：① `donkey/cli/cli_client.py` 的 `_EXCEPTION_TO_EXIT_CODE` MUST 仍**恰含 4 个条目**（`PathNotFoundError`→1 / `PathPermissionError`→2 / `TemplateGenerationError`→3 / `BuiltinToolGenerationError`→4）、值与键 MUST **逐项未变**；② `donkey/core/exceptions.py` MUST **未新增**任何异常类（仍恰 4 个具体类 + 2 个基类）；③ `donkey/core/exit_codes.py` MUST **未新增**任何 `EXIT_CODE_*` 常量、既有常量值与段位元组 MUST 逐项未变；④ 本 Phase 代码路径实际可返回的退出码集合 MUST **恰为 `{0, 1}`**（`version` 只经由 argparse 的既有错误路径落到 `1`，MUST NOT 使用默认失败码 `2`）　〔覆盖 spec FR-028 / FR-029 / FR-030 · SC-006 / SC-008〕
- [X] T040 **核对** quickstart.md §2 的 **7 组手动验证步骤**的**执行证据链齐备** —— 每组 MUST 已有对应任务的执行记录（§2.1 → T016 / §2.2 → T019 / §2.3 → T022 / §2.4 → T024 / §2.5 → T027 / §2.6 → T029 / §2.7 → T031），**MUST NOT 重复执行**这些步骤（同一事实 MUST NOT 被断言两次）；并确认 quickstart §8 的 **16 条**判据索引均有对应的落地证据 —— 其中 **SC-011（5 秒上限）** MUST 有 T013 要求的**逐场景耗时记录**为证（spec SC-001 ~ SC-016）　〔覆盖 spec SC-001 ~ SC-016〕

**Checkpoint**: 本 Phase 的退出条件（Exit Gate）全部达成 —— SC-001 ~ SC-016 全部达标 + 7 个 e2e 断言 100% PASS + 既有三套 verify 脚本全绿 + 静态检查零 error

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 —— 可立即开始。**T002 / T003 / T004 是「只读核对」任务**（宪法修订**已由 Maintainer 于 2026-10-30 前置落地**，MUST NOT 再改写该文件），但 MUST **先于**其余一切交付物完成核对 —— 以确认授权基础逐字未变（spec FR-036 / research.md R-19）
- **Foundational (Phase 2)**: 依赖 Phase 1 完成 —— **阻塞全部 7 个用户故事**
- **User Stories (Phase 3 ~ 9)**: 全部依赖 Phase 2 完成
  - 故事可**依次**推进（P1 → P2 → …）或并行推进（见下「受限（不可并行）」）
- **文案同步与 Polish (Phase 10)**: 依赖全部 7 个故事完成 —— T033 与 T015 **同文件**，MUST 在 T015 之后

### User Story Dependencies

- **User Story 1 (P1)**: 可在 Phase 2 完成后开始 —— **不依赖**其它故事（**MVP**）
- **User Story 2 (P2)**: 可在 Phase 2 完成后开始 —— 依赖 US1 的命令已注册，但不依赖 US2 ~ US7
- **User Story 3 (P3)**: 可在 Phase 2 完成后开始 —— 依赖 US1 的命令已注册
- **User Story 4 (P4)**: 可在 Phase 2 完成后开始 —— 依赖 US1 的命令已注册
- **User Story 5 (P5)**: 可在 Phase 2 完成后开始 —— 依赖 US1 的子命令已注册（否则误用会撞上"未知子命令"而非参数用法错误）
- **User Story 6 (P6)**: 可在 Phase 2 完成后开始 —— 依赖 Phase 2 的回退分支已实现
- **User Story 7 (P7)**: 可在 Phase 2 完成后开始 —— 依赖 US1 的命令已注册

### 用户故事 ↔ e2e 黑盒场景对照（spec 的 1:1 映射）

| User Story | 优先级 | e2e 场景函数 | 任务 | 关键判据 |
|---|---|---|---|---|
| US1 | P1 🎯 MVP | `test_scenario_1_version_command_outputs_one_line` | T014 | SC-002 / SC-015 |
| US2 | P2 | `test_scenario_2_single_version_value` | T018 | SC-002 / SC-003 |
| US3 | P3 | `test_scenario_3_deterministic_value_without_graph` | T021 | SC-003 |
| US4 | P4 | `test_scenario_4_both_entrypoints_equivalent` | T023 | SC-004 |
| US5 | P5 | `test_scenario_5_usage_errors_exit_1` | T026 | SC-006 / SC-013 / SC-014 |
| US6 | P6 | `test_scenario_6_version_without_distribution_metadata` | T028 | SC-007 |
| US7 | P7 | `test_scenario_7_read_only_no_side_effects` | T030 | SC-005 |
| （非故事） | —— | —— | —— | SC-001（7 个断言全绿）/ SC-008（退出码零增量 → T039）/ SC-009（既有套件全绿 → T034）/ SC-010（静态检查 → T035）/ SC-011（5 秒上限 → T013）/ SC-012（宪法修订 → T005 / T038）/ SC-016（过期计数 → T032 / T033） |

> **CI 交付检查类断言**：本 Phase **不新增** —— 「既有三套 verify 脚本保持全绿」属**强制退出条件**（FR-034 / SC-009），MUST NOT 被升格为 User Story（spec 的 User Scenarios 段前置说明）。

### Within Each User Story

- 测试 MUST 先写并确认**失败**，再补实现
- 核心层（Phase 2）→ CLI 层（US1）→ 行为硬化（US2 ~ US7）
- 故事完成 → 再进入下一个优先级

### Parallel Opportunities

- Phase 1 的 T001 / T006 与 T002 ~ T004（不同文件 / 不同关注点）可并行
- Phase 2 的 T007 与 T008 ~ T010（测试文件 vs 实现文件）可并行
- Phase 3 的 T012（单元测试文件）与 T013（e2e 骨架文件）可并行
- 各故事阶段的**单元测试任务**与**e2e 场景任务**分处两个文件，可并行
- 不同用户故事可由不同执行者并行推进（US2 ~ US7 均只依赖 US1 的命令已注册）

### 受限（不可并行）

| 冲突组 | 涉及任务 | 约束 |
|---|---|---|
| **T002 / T003 / T004** 全部指向同一个文件 `.specify/memory/constitution.md` | T002 · T003 · T004 | **串行**核对或分批提交（核对顺序即 §4.2.1 → §4.3 第 253 行括注 → §4.3 第 269 行 v1 baseline → 第 5 章 [D-20]）；三条均为**只读核对**任务（MUST NOT 改写该文件） |
| **T007 / T012 / T017 / T020 / T025** 全部写同一个文件 `tests/unit/test_cli_version.py` | T007 · T012 · T017 · T020 · T025 | **串行**或分批提交 |
| **T013 / T014 / T018 / T021 / T023 / T026 / T028 / T030** 全部写同一个文件 `tests/e2e/phase/verify_phase_f001_p4.py` | T013 · T014 · T018 · T021 · T023 · T026 · T028 · T030 | **串行**或分批提交 |
| **T015 / T033** 写同一个文件 `donkey/cli/cli_client.py` | T015 · T033 | **串行** —— T033 MUST 在 T015 之后 |
| **T009 / T010** 写同一个文件 `donkey/core/version.py` | T009 · T010 | **串行**（同文件的连续实现步骤） |

---

## Parallel Example: User Story 6

```bash
# 同一故事内的单元层与 e2e 层可并行（不同文件 → 分批提交）：
Task: "在 tests/unit/test_cli_version.py 写回退分支断言（T007 的 B-2 / B-3 用例）"
Task: "在 tests/e2e/phase/verify_phase_f001_p4.py 实现场景 6（副本法，T028）"

# 不同故事之间可并行（不同执行者）：
Task: "US2：T017 + T018（唯一版本值）"
Task: "US3：T020 + T021（恒定取值 + 无节点级信息）"
Task: "US5：T025 + T026（用法错误 → 1）"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup（宪法修订**核对** + 基线快照）
2. Complete Phase 2: Foundational（核心层版本解析模块）
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: 独立验证 `donkey version` → `v0.1.0`（**常规安装形态**下）
5. 交付 / 演示（若就绪）

### Incremental Delivery

1. Complete Setup + Foundational → 地基就位
2. Add US1 → 独立验证 → 交付（MVP：用户终于不必再用 `python -c` 绕路）
3. Add US2 → 独立验证 → 交付（版本值唯一 + 可比对清单）
4. Add US3 → 独立验证 → 交付（取值恒定、无节点级噪声）
5. Add US4 → 独立验证 → 交付（双入口等价）
6. Add US5 → 独立验证 → 交付（误用退出码一致）
7. Add US6 → 独立验证 → 交付（非标准安装下仍可用）
8. Add US7 → 独立验证 → 交付（只读保证）
9. Phase 10：文案同步 + 全量验证 + 治理自检 → 收尾

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together（T002 ~ T011）
2. Once Foundational is done:
   - Developer A: US2 + US3（T017 ~ T022）
   - Developer B: US4 + US5（T023 ~ T027）
   - Developer C: US6 + US7（T028 ~ T031）
3. Stories complete and integrate independently

---

## Notes

- [P] = 可**并行推进**（**无未完成任务的依赖**）；⚠️ 同一文件内的多个 `[P]` 任务 MUST **分批提交**（见「受限（不可并行）」表）
- [Story] 标签把任务映射到具体用户故事（US1 ~ US7），供追溯用
- 每个用户故事都应能**独立完成、独立测试**
- 提交前确认测试已转绿
- 每个任务或逻辑分组完成后提交一次
- 停在任意 Checkpoint 独立验证该故事
- 避免：含糊的任务、同一文件冲突、破坏故事独立性的跨故事依赖
- **实施者必读**：本 Phase 的**授权基础**是宪法修订（**已由 Maintainer 于 2026-10-30 前置落地，4 处**）—— T002 ~ T004 是**只读核对**任务，MUST NOT 再改写 `.specify/memory/constitution.md`；MUST NOT 在 T002 ~ T004 核对通过前实施任何其它交付物（spec FR-036 / Clarifications Q5(a)）
- **实施者必读**：本 Phase **不占用**任何 exit code 子段、**不新增** Error class、**不新增**依赖、**不改动**任何既有测试文件（spec FR-029 / FR-034 / plan Technical Context）
- **实施者必读**：`harness/features/README.md` MUST **逐字未改** —— F001-P4 在项目索引中的登记载体是宪法 [D-20] 的「影响面」条目（spec FR-030 / SC-012 / research.md R-13）

---

## Phase 11: Convergence —— 代码先于文档的追补（2026-10-30）

**背景**：本轮有两项变更**先于 spec / plan / tasks 落地**（宪法 [D-21] 工作区清单字段变更、
[D-22] `donkey init` 执行报告变更），偏离了宪法 §4.1 的「spec → plan → tasks → code」序。
本相位**只做文档追补**，MUST NOT 改动任何运行时代码、测试代码或既有 FR / SC 原文。

**追补的既定先例**（MUST 沿用，MUST NOT 自创机制）：

- **spec**：既有 FR / SC 的**编号与原文一律不动** —— 追加「**后续修订登记****」小节（指针 + 口径说明），
  与 F001-P2 spec 末尾已追加的同款段落、以及 F001-P3 spec FR-068 的「阶段边界断言的显式改写」段同构；
- **plan**：更新「Project Structure / 文件清单」「Scale / Scope 计数」「Constitution Check 门禁表」三处**事实性**描述；
- **tasks**：追加实施记录（**MUST NOT** 改写 / 重编号任何既有任务）；
- **断言改写登记**：MUST **逐条**登记，且**实施前 MUST 逐行核对**被改文件的实际内容 ——
  MUST NOT 以任何概括性计数（如"7 处"）为准（沿用 F001-P3 FR-068 的登记口径）；
- **不动的文档**：P1 的 `contracts/*.md`（自称「v1 冻结」）、P2 的三份 `contracts/*.md`（冻结快照）、
  P1 / P2 的 `quickstart.md`（历史快照 —— F001-P3 当年亦未回改 P2 的 quickstart）MUST **逐字不动**。

- [X] T041 在 `specs/001-donkey-init-workspace/phase-4-cli-version/spec.md` 追加「**后续修订登记**」小节，
      登记 **FR-026 的口径变更**：工作区清单的 `donkey_version` 由**硬编码** `"0.1.0"` 改为
      **动态取值**（`donkey.core.version.resolve_version()`）—— 授权来源 = 宪法 **[D-21]** +
      F001-P2 FR-021 **自身预留**的演进路径（"将来若改为动态获取，MUST 使用包元数据查询方式"）+
      Maintainer 裁决（2026-10-30）；同时说明该变更**修正**了 FR-026 原口径的
      "陈旧安装形态下迁移提示误判"隐患。FR-026 **原文 MUST NOT 改动**；
      Edge Cases「阶段边界类」中"本 Phase **不**触碰工作区清单的 `donkey_version` 硬编码值"一条
      MUST 在该登记段中被显式**追认**（而非删改原文） per FR-026 (contradicts)
- [X] T042 在 `specs/001-donkey-init-workspace/phase-4-cli-version/spec.md` 的「后续修订登记」小节内，
      **逐条**登记 [D-21] / [D-22] 导致的**既有测试断言改写**（分布在
      `tests/unit/test_cli_client.py`、`tests/unit/test_template_skeleton.py`、
      `tests/unit/test_builtin_tools.py`、`tests/e2e/phase/verify_phase_f001_p2.py`、
      `tests/e2e/phase/verify_phase_f001_p3.py` 五个文件）—— 每条 MUST 给出「位置 / 原断言 /
      新断言 / 改写理由」；**实施前 MUST 逐行核对这五个文件的实际内容**，MUST NOT 以任何概括性
      计数为准；FR-034 的"既有 FR / SC **编号** MUST 保持不变"一条 MUST 同时被确认未受影响 per FR-034 (partial)
- [X] T043 在 `specs/001-donkey-init-workspace/phase-4-cli-version/spec.md` 的 Phase 元信息
      「**授权基础**」行与「**H. 宪法修订文本**」段补登宪法 **[D-21]** 与 **[D-22]** 两条 ADR 的
      影响面（清单字段三字段化 / `donkey_version` 动态取值 / `InitResult` 契约 v2 / init 执行报告形态）；
      H 段 (a) / (b) / (b2) / (c) 的**登记文本 MUST 逐字不动**（宪法 §6.2 只增不删的先例） per Phase 元信息 / H 段 (partial)
- [X] T044 更新 `specs/001-donkey-init-workspace/phase-4-cli-version/plan.md` 的
      「Project Structure → Source Code」与「Scale / Scope」—— 补齐 [D-21] / [D-22] 实际触及的
      **全部**文件（含 `donkey/core/workspace/manifest.py` / `donkey/core/workspace/init.py` /
      `tests/unit/test_init_report.py` / 4 个既有测试文件 / 2 个既有 e2e 脚本 /
      `harness/features/README.md` / `harness/features/立项书.md` /
      `specs/.../phase-2-template-skeleton/spec.md` 等），并把「改动既有源文件 2 个」
      与「新增运行时代码模块 1 个」修正为**实际**口径；MUST NOT 顺手改写 plan 的其它决策段 per plan Project Structure / Scale-Scope (contradicts)
- [X] T045 在 `specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md` 追加「**后续修订登记**」
      小节，登记 **FR-006 的库 API 契约 v2**：`InitResult` 在 v1 六字段**之后追加**
      `files_overwritten` / `dirs_created` / `dirs_skipped` / `items` 四个字段（v1 字段**逐字保留、
      顺序不变**），并引入 `INIT_RESULT_CONTRACT_VERSION = 2` —— 满足 FR-006 的
      "字段语义不得在本阶段之后**无版本号**变更"；同时说明 `files_created` 的语义**归位**为
      FR-006 字面口径「本次**新建**文件数」（原先 `--force` 的**覆盖**被并入其中）per FR-006 (contradicts)
- [X] T046 更新 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md` 的 **FR-069** 末句 ——
      `--force`（契约库已存在）的计数口径由「`templates_loaded=54` / `files_created=47` /
      `files_skipped=1`」改为「`templates_loaded=54` / `files_created=0` /
      `files_overwritten=47` / `files_skipped=1`」（授权 = 宪法 [D-22]）；该 FR 的**其余文字 MUST NOT 改动** per FR-069 (contradicts)
- [X] T047 更新 `specs/001-donkey-init-workspace/phase-3-builtin-tools/contracts/cli-contract.md`
      的「§3.2 计数口径（契约的权威表）」—— 增列 `files_overwritten` / `dirs_created` / `dirs_skipped`
      三列、同步 `--force` 行与 `render_templates` 的调用示例（现返回逐项明细而非两个计数），
      并注明该表已被宪法 **[D-22]** 修订（该表被 F001-P4 的 tasks T032 引为**当前权威计数源**，
      故 MUST 与实现保持一致）；同文件内 P2 阶段的**历史**计数差异说明 MUST 保留 per P3 contracts §3.2 (contradicts)
- [X] T048 更新 `specs/001-donkey-init-workspace/phase-4-cli-version/plan.md` 的
      「Constitution Check」门禁表 —— G9（三端共用 `core.api` 库 API）/ G12（覆盖率）/
      G13（宪法修订）三门**补引**宪法 [D-21] / [D-22]（库 API 契约 v2 + init 执行报告形态
      + 清单字段三字段化），并复核 G2 / G4 / G6 三门在新形态下**仍为 PASS**（分层、测试三层、
      永不使用清单均未受影响）；MUST NOT 改写门禁的**判定结论**本身 per plan Constitution Check (partial)
- [X] T049 在 `specs/001-donkey-init-workspace/phase-2-template-skeleton/spec.md` 已有的
      「后续修订登记」小节内**补入 FR-017** 的登记：清单计数现按「对象 × 动作」分列 ——
      目录条目**不再**"不计入"，而是分列为 `dirs_created` / `dirs_skipped`（目录条目**永不**
      "覆盖"；其"新建/跳过"以**本次运行开始前**的存在状态判定）。FR-017 **原文 MUST NOT 改动** per FR-017 (contradicts)
- [X] T050 更新 `specs/001-donkey-init-workspace/phase-2-template-skeleton/plan.md` 与
      `tasks.md` T013 —— `render_templates` 的返回值由 `tuple[int, int]` 改为
      `list[InitItem]`（逐项明细：路径 / 对象 / 动作），各计数由明细**投影**而来
      （**单一真相源**）；tasks T013 的签名 MUST 逐字同步，MUST NOT 改写该任务的**其它**描述 per P2 plan 结构段 / tasks T013 (partial)
- [X] T051 更新 `specs/001-donkey-init-workspace/phase-1-cli-validation/plan.md` 与
      `tasks.md` T013 —— `InitResult` 的字段清单与契约版本号（v2：追加四字段 +
      `INIT_RESULT_CONTRACT_VERSION = 2`）；MUST NOT 改写该任务的**其它**描述 per P1 plan G9 / 结构段 / tasks T013 (partial)
- [X] T052 在 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md` 的
      「阶段边界断言的显式改写（实现要点 §3.5）」段与 `tasks.md` T095 的**登记表**内，
      **补记 [D-22] 的二次改写**（P3 e2e 3 处字面量 + P3 单测 1 处计数断言）——
      登记表 MUST 逐条给出「位置 / 原断言 / 新断言」；T095 登记的**既有**内容 MUST NOT 删改 per P3 FR-068 / tasks T095 (partial)
- [X] T053 更新 `specs/001-donkey-init-workspace/phase-3-builtin-tools/quickstart.md` 中
      `donkey init` 输出的**期望值**（九字段摘要 + 逐项明细形态 + `--force` 的
      `files_created=0` / `files_overwritten=47`）；该文件中对 P2 阶段**历史**断言的引用 MUST 保留 per P3 quickstart (partial)
- [X] T054 在 `specs/001-donkey-init-workspace/phase-4-cli-version/spec.md` 登记本次的
      **流程倒置**（[D-21] / [D-22] 两项变更**先于** spec / plan / tasks 落地）——
      **追认**其授权来源（宪法 [D-21] / [D-22] + Maintainer 裁决 2026-10-30），并写明后续变更
      MUST 恢复宪法 §4.1 的「spec → plan → tasks → code」序；本条 MUST NOT 削弱
      宪法 §4.1 的 TDD 四件套要求，也 MUST NOT 自设任何宪法例外 per Constitution §4.1 (missing)
- [X] T055 在 `specs/001-donkey-init-workspace/phase-4-cli-version/tasks.md` 追加「**实施记录**」小节，
      逐条列出 [D-21] / [D-22] 两项变更的实际落点（代码 / 测试 / 文档文件与对应的 FR / ADR），
      使本 tasks.md 与实现**可追溯对齐**；MUST NOT 改写 / 重编号 / 删除任何既有任务条目 per P4 tasks (missing)

---

## Phase 12: 实施记录 —— 宪法 [D-21] / [D-22] 两项变更

> 本节是 [D-21]（工作区清单字段变更）与 [D-22]（`donkey init` 执行报告变更）的**落点清单** ——
> 使本 tasks.md 与实现**可追溯对齐**。两项变更**先于** spec / plan / tasks 落地（流程倒置），
> 授权来源 = 宪法 [D-21] / [D-22] + Maintainer 裁决（2026-10-30）；追补见 spec.md 文末
> 「后续修订登记」段与本文件 Phase 11。

### [D-21] · 工作区清单字段变更

| 落点 | 内容 |
|---|---|
| `donkey/core/workspace/manifest.py` | 删 `_MANIFEST_VERSION` 常量与 `"version"` 字段；`donkey_version` 由硬编码 `"0.1.0"` 改为 `resolve_version()` **动态取值**（优先安装分发元数据 → 回退包内 `__version__`）；docstring 记录口径变更与存量兼容 |
| `tests/unit/test_template_skeleton.py` | 5 处清单字段断言改写（字段集合去 `version`；`donkey_version` 改为与运行时比对） |
| `tests/unit/test_cli_version.py` | 新增 FR-013 不变式用例（清单 `donkey_version` == `resolve_version()`；字段集 == 三项） |
| `.specify/memory/constitution.md` | 修订 **D-01**（四字段 → 三字段）与 **D-03**（"格式版本号" → "**donkey 版本号**" + 兜底条款）；追加 **[D-21]** ADR |
| `harness/features/立项书.md` | §1.3 目标 5 / Q-07 / §4.6.1 字段描述 / 附录 F D-03 摘要（5 处） |
| `harness/features/README.md` | §4.4 四处同步 + 新增 **§5.6「F002 必读备忘录」**（快照设计约束 S-1 ~ S-4） |
| `specs/.../phase-2-template-skeleton/spec.md` | 追加「后续修订登记」段（FR-019 / FR-021 / FR-017 的口径追认） |
| `docs/User_Guide/01_init_workspace.md` | M-D4 期望值改为三字段 |

### [D-22] · `donkey init` 执行报告变更

| 落点 | 内容 |
|---|---|
| `donkey/core/workspace/init.py` | `render_templates` 改返回**逐项明细** `list[InitItem]`（`path` / `kind` / `action`）；新增 `InitItem` 类型；文本 / sqlite3 / 目录渲染器改返回**动作**（`created` / `overwritten` / `skipped`）；目录的"新建/跳过"按**运行前**存在状态判定（避免清单顺序依赖） |
| `donkey/core/api.py` | `InitResult` 升为**契约 v2**（v1 六字段逐字保留、顺序不变 + 追加 `files_overwritten` / `dirs_created` / `dirs_skipped` / `items`）；新增 `INIT_RESULT_CONTRACT_VERSION = 2`；各计数由明细**投影**（单一真相源） |
| `donkey/cli/cli_client.py` | 摘要扩为**九个字段**（按「对象 × 动作」分解）；新增**逐项明细**（每条目一行，走 stdout）；`--force` 警告**置于明细之后** |
| `tests/unit/test_init_report.py` | **新增**（7 个用例：摘要分解 / 二次 init / `--force` 覆盖分列 / 明细逐条对应 / 三种标记 / 警告置尾 / 计数与 items 自洽） |
| `tests/unit/test_cli_client.py` | 1 处断言改写（六字段 → 九字段 + 行数口径） |
| `tests/unit/test_template_skeleton.py` | 9 处断言改写（8 处渲染计数 + 1 处 `InitResult` 字段清单） |
| `tests/unit/test_builtin_tools.py` | 1 处计数断言改写（三元组 → 六元组） |
| `tests/e2e/phase/verify_phase_f001_p2.py` | 2 处字面量改写 |
| `tests/e2e/phase/verify_phase_f001_p3.py` | 3 处字面量改写 |
| `.specify/memory/constitution.md` | 追加 **[D-22]** ADR |
| `harness/features/README.md` | §4.2 库 API 段同步 + 新增 **§4.8「`donkey init` 的执行报告」** |
| `harness/features/立项书.md` | §4.6.1 执行报告段 |
| `docs/User_Guide/01_init_workspace.md` | §0.3 计数口径、§0.4 输出格式、M-D1 / M-E1 / M-E2 / M-E3 / M-F1 / M-F4 |

### 验证结果

| 项 | 结果 |
|---|---|
| 全量套件 | **225 passed**（较基线 218 增 7 —— 新增 `test_init_report.py` 的 7 个用例） |
| `ruff check donkey/ tests/` | 0 error |
| `mypy donkey/ tests/` | 0 error（24 个文件） |
| 覆盖率 | `donkey.core` **93%**；`version.py` 100%、`api.py` 100% |
| 宪法 | ADR D-01 ~ D-22 连续、[D-22] 表尾；[D-20] 相关**四处**逐字**未动** |
| 冻结物 | P1 `contracts/*.md`、P2 三份 `contracts/*.md` —— `git diff` **均空**（逐字未改） |
