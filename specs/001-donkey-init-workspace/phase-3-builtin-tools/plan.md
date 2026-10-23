# Implementation Plan: F001-P3 `builtin_tools` —— `donkey init` 内置工具与变更记录契约幂等生成

**Branch**: `main`（spec 目录名 `001-donkey-init-workspace/phase-3-builtin-tools` 与 git 分支相互独立，见 spec.md 头部说明） | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md`（105 条 FR / 24 条 SC / Clarifications 现有 **5 段 / 22 项决策** —— 以 spec.md 的 `## Clarifications` 段为准；最新一段为「`/speckit.analyze` 之后的定点修订轮 · 第二轮」，含 S1 / S2 / S3 / S5 **四项决策**（另含 S1b 的边界补充与 S4 的纯格式改动）：宪法例外引用 / 指纹 `null` 钉死 / SC-021 可判定化 / 表述收敛）

---

## Summary

**目标**：交付 `donkey init` 的**内置工具与变更记录契约幂等生成**（F001-P3 子段 3，退出码 `4`）—— 在 workspace 内落地 **3 个内置 `@tool`**（filesystem 7 个 / commandline 1 个 / webfetch 1 个）+ **1 个变更记录契约库**（`tools/changes.py`，全 workspace 唯一的变更记录产地）+ Skills example 三层 + `tools/` 支撑文件，并把全部 8 条新条目追加进模板清单（46 → **54** 条）。

**技术路线**：**产物即模板** —— 本 Phase 的绝大部分交付物是**渲染进用户工作区的 `.txt` 模板源**，而不是 donkey 自身的运行时代码。donkey 侧的改动被压缩到 **最小面**：

```text
donkey/core/workspace/templates/          ← 本 Phase 的主战场（新增 8 个 .txt + 覆盖 2 个 .txt + 清单追加 8 条）
donkey/core/exceptions.py                 ← 追加 1 个异常类（BuiltinToolGenerationError）
donkey/core/exit_codes.py                 ← 改 1 行文档串（常量 4 已由 P1 建档，见 R-10）
donkey/core/workspace/init.py             ← 仅 init_workspace_inner 步骤 ④ 加一条条目级豁免（R-07）
donkey/cli/cli_client.py                  ← 异常映射表追加 1 行
pyproject.toml                            ← dev 依赖追加 pytest-httpx
.github/workflows/ci.yml                  ← 新建（宪法 §6.3 临时例外 E-01 到期闭合）
```

**关键决策**（R-01 ~ R-20 详见 [research.md](research.md)）：

| # | 决策 | 落点 |
|---|---|---|
| R-01 | `@tool` + `from __future__ import annotations` 实测兼容（langchain-core 1.6.12）；docstring 原样成为工具描述 | 模板正文 |
| R-02 | **模板单元测试的加载策略**：渲染 → 工作区根入 `sys.path` → `importlib.import_module("tools.X")` → teardown 清 `sys.modules`；"顶层模块"形态由独立用例覆盖（`tools/` 入 path） | `tests/unit/test_builtin_tools.py` 夹具 |
| R-03 | 网络工具 MUST 改用 `httpx.Client` + `client.stream(...)`（`httpx.request()` 无法"读取中守上限"）—— 与源模板正文的**唯一**必须偏离；客户端 MUST 以 **`trust_env=False`** 构造（httpx 的 `trust_env` 默认为 `True`，会隐式读取 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `.netrc` —— 违反 spec FR-104「工具 MUST 不读任何环境变量」，且与 FR-089 的"MUST NOT 实现…代理"相悖） | `templates/tools/webfetch.py.txt` |
| R-04 | HTTP 拦截库 = `pytest-httpx>=0.35`（新增 **dev** 依赖；运行期依赖仍恰为 1 个） | `pyproject.toml` |
| R-05 | 行切分 MUST 用 `split("\n")`，MUST NOT 用 `splitlines()`（后者把 `\v` `\u2028` 等也当行界） | 全部模板 |
| R-06 | 原子写 = 同目录 `mkstemp` → `fsync` → `os.replace`；异常路径 MUST 清临时文件 | `templates/tools/changes.py.txt` |
| **R-07** | **契约库豁免于强制重置** ⇒ 只改 `init_workspace_inner` 步骤 ④（剔除条目 + 计入 skipped），`render_templates` **一字不改**；计数 47/1/54 | `core/workspace/init.py` |
| R-08 | 模板正文**零静态检查覆盖**（`.txt` 非 `.py`）⇒ 每个渲染出的 `.py` MUST `compile()` 成功 | 单元测试自检 |
| R-09 | `package-data` 已是 `"**/*.txt"` ⇒ MUST NOT 改动 | `pyproject.toml` |
| R-10 | 退出码常量 `4` **已由 P1 建档** ⇒ 本 Phase 只激活文档串 + 加异常类 + 映射 1 行 | `core/exit_codes.py` / `core/exceptions.py` / `cli/cli_client.py` |
| **R-11** | 读算法统一为**一条**分页代码路径（行数上限无条件生效）—— 与 OpenCode 的**第 4 处**有意偏离 | `templates/tools/filesystem.py.txt` |
| R-12 | `list_dir` 分页参数 = `offset`（**0 基**）+ `limit`（≤ 2000）；FR-097 只给语义，名字由 plan 定 | `templates/tools/filesystem.py.txt` |
| R-13 | `list_dir` 排序保持**源模板的代码点序**（非 OpenCode 的目录优先 + locale 序）—— **第 5 处**有意偏离 | `templates/tools/filesystem.py.txt` |
| R-14 | CI 工作流最小内容 + Python 3.11/3.12 矩阵；覆盖率 MUST 用独立命令（MUST NOT 写进 `addopts`） | `.github/workflows/ci.yml` |
| R-15 / R-16 | P2 的 e2e 场景 1 / 11 与单测侧的**阶段边界断言组** MUST 显式改写为 P3 口径（按 R-16 的断言组**逐条核对**，MUST NOT 以任何概括性计数为准）；P2 其余断言 MUST 原样保持绿 | `tests/unit/test_template_skeleton.py` / `tests/e2e/phase/verify_phase_f001_p2.py` |
| R-17 / R-18 | 命令输出以 stdout+stderr 合并文本计量；2000 行 / 50 KiB 两侧共用 + 单测守护一致 | 两个工具模板 |
| R-19 | 协议白名单（http/https）+ MIME 白名单 + 非 2xx 报错 + 超时上限 120s 事前校验；客户端 MUST 以 **`trust_env=False`** 构造（见 R-03 —— httpx 默认的 `trust_env=True` 会隐式读取代理 / 证书环境变量，违反 FR-104） | `templates/tools/webfetch.py.txt` |
| R-20 | e2e 的网络拦截 MUST 与导入同处**一个子进程**（子进程内打桩 `httpx.Client.send`）；子进程 MUST 用 `python -c`（`-c` 才把 cwd 放进 `sys.path`） | `tests/e2e/phase/verify_phase_f001_p3.py` |

---

## Technical Context

**Language/Version**: Python 3.11+（本机实测 3.12.3；依赖 `tomllib` 内置）

**Primary Dependencies**: **donkey 自身仍恰为 1 个直接运行期依赖** = `langgraph-checkpoint-sqlite>=3.1,<4`（**不变**，spec FR-080 / SC-015）；
本 Phase 新增 **1 个 dev 依赖** = `pytest-httpx>=0.35`（实测装入 0.36.2；R-04）；
**渲染进用户工作区的模板依赖**（**不计入** donkey 自身依赖）：HTTP 客户端（用户在自己的工作区里跑网络工具时才需要 —— spec FR-044(h) / FR-080）+ 智能体框架内置的工具装饰器（`langchain_core.tools`，随框架传递依赖而来）；
其余全部标准库（`pathlib` / `json` / `os` / `shutil` / `difflib` / `hashlib` / `tempfile` / `subprocess` / `shlex`）

**Storage**: 文件系统（workspace 根目录）+ sqlite3 文件（`memory/*.sqlite3`，**本 Phase 不触碰**，spec FR-085）

**Testing**: pytest —— `tests/unit/test_builtin_tools.py`（**≥15** 个用例）+ `tests/unit/test_template_skeleton.py`（P2 既有，**阶段边界断言组按 R-16 逐条核对改写**）+ `tests/integration/test_init_to_load.py`（**≥4** 个用例，**本 Phase 首次启用**）+ `tests/e2e/phase/verify_phase_f001_p3.py`（**16** 个黑盒断言）+ P1 / P2 的既有套件（**必须仍全绿**）

**Target Platform**: Linux / macOS（POSIX 权限与原子替换语义；Windows 不在本 Phase 实现范围，路径与文件操作按平台无关表述编写）

**Project Type**: single-package library + CLI（`donkey.core` 库 API + `donkey.cli` argparse 客户端；web / gui 维持空占位）

**Performance Goals**: 单次 `donkey init` 在 **10 秒**内返回（spec SC-019；纯本地文件系统操作，**无网络依赖** —— 本 Phase 不做导入预演，spec FR-072）

**Constraints**: 宪法 N-01（workspace 内禁智能体入口文件）/ N-02（禁 subagent）/ N-03（core 不依赖客户端）/ N-04（cli 不直接 import langchain·langgraph·sqlite3）/ N-05（core 不依赖 argparse·sys.argv）/ N-08（退出码段位不重叠）/ N-12（禁 LangSmith 任何形态，D-17 边界）/ N-11（三端对等，阶段性）；CLI 框架限标准库 `argparse`；**本 Phase 的工具装饰器与 HTTP 客户端导入 MUST 只出现在渲染产物中**（spec FR-077 / FR-078）；**工具 MUST NOT 读取任何环境变量**（spec FR-104）

**Scale/Scope**: 1 个子命令 / **1 个新错误类**（exit 4）/ **105 条 FR** / **24 条 SC** / **54 条清单条目**（45 个文本型 + 3 个 sqlite3 型 + 6 个目录型；文件型 **48**）/ **45 个模板源文件**（37 + 8）/ 磁盘落地 **49** 个文件 + **10** 个目录 / **9 个 `@tool` 函数**（7 + 1 + 1）+ **1 个契约库**（0 个 `@tool`）/ **16 个 e2e 黑盒断言** / **≥15 个单元测试用例** / **≥4 个集成测试用例** / **5 个新增或改造模块**（`templates/` 子树：8 个新源 + 2 处覆盖 + 清单 1 个 / `core/exceptions.py` / `core/exit_codes.py` / `core/workspace/init.py` / `cli/cli_client.py`）+ **3 个新增测试文件**（`tests/unit/test_builtin_tools.py` / `tests/e2e/phase/verify_phase_f001_p3.py` / `tests/integration/test_init_to_load.py`）+ **2 个改造测试文件**（P2 的单测与 e2e，R-15 / R-16）+ **1 个新建仓库文件**（`.github/workflows/ci.yml`）+ **1 个改造文件**（`pyproject.toml`，仅 dev 依赖）

> **口径注**：「**5 个新增或改造模块**」是**模块组数**（`templates/` 子树算 1 组），与 spec 闭环复杂度里的「**6 个新增 `.py` 产物**」是**文件数**口径 —— 二者**不冲突**、MUST NOT 互相改写。

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 门 | 宪法条款 | 判定 | 依据 / 落地方式 |
|---|---|---|---|
| G1 | §3.1 Python 3.11+；§3.1 CLI 用 stdlib `argparse` | ✅ PASS | CLI 框架不变；本 Phase 的新增代码只落在**模板正文**（Python 3.11+ 语法：`X \| None`）与 `init_workspace_inner` 的豁免分支 |
| G2 | N-03 核心层不 import 客户端；N-04 cli 不直接 import langchain / langgraph / sqlite3；N-05 核心层不 import argparse / sys.argv | ✅ PASS | **工具装饰器与 HTTP 客户端的 import 只出现在渲染产物中**（`templates/tools/*.txt`）—— donkey 自身的 `core/` 与 `cli/` **零新增 import**（spec FR-077 / FR-078）；`cli/cli_client.py` 只加 1 行映射，不 import 任何框架 |
| G3 | N-08 退出码段位严格不重叠（§4.4） | ✅ PASS | 本 Phase 使用 `0/1/2/3/4`，落在 F001 段位 `1-10` 的子段 3；`5-10` 不触发（[contracts/exit-codes.md](contracts/exit-codes.md)） |
| G4 | §3.1 测试三层 `unit` / `integration` / `e2e/phase`；黑盒脚本只跑子进程、不 import 业务代码 | ✅ PASS（**本 Phase 改判**） | **`tests/integration/` 由空占位改为启用** —— P2 的理由是"无跨模块协作"，该理由在本 Phase **失效**：`donkey init`（core 层）产出的工作区产物被**独立进程**导入并调用，正是集成层的定义（spec FR-061）。黑盒脚本仍只跑子进程（R-20） |
| G5 | §4.1 CI：pytest + ruff + mypy；§4.1 TDD 四件套流程 | ✅ PASS（**本 Phase 由 Deferred 转 PASS**） | **临时例外 E-01 到期闭合** —— 本 Phase MUST 交付 `.github/workflows/ci.yml`（R-14；spec FR-065 / SC-001 的第 16 个断言）。**本 Phase 起不再有 E-01 的适用范围** |
| G6 | §3.2 永不使用清单（LangSmith / deepagents / ShellToolMiddleware / subagent） | ✅ PASS | 渲染产物 MUST NOT 含任何可观测性后端字样（spec FR-079）；**本 Phase 的模板正文不 import `langsmith` 任何形态**；`tools/changes.py` MUST **零框架 import**（spec FR-011，纯 stdlib）→ 未来的工具扫描器对其零歧义 |
| G7 | §2.2 路径绝对化原则 | ✅ PASS（**本 Phase 强化**） | 相对路径基准 = "存放 `tools/` 的那个目录"，由契约库自身位置推导；**MUST NOT 读环境变量**（spec FR-002 / FR-104）；命令工具的工作目录默认 = 工作区根（spec FR-032） |
| G8 | §2.3 / AC-3 workspace 原子性 + init 幂等；D-01 workspace 自带 manifest | ✅ PASS | 幂等三态沿用 P2；**唯一新增例外** = 契约库豁免于强制重置（R-07 / spec FR-105），且 MUST NOT 削弱其余条目的通则（FR-069） |
| G9 | §2.8 / D-08 三端共用 `core.api` 库 API | ✅ PASS | `init_workspace` 门面函数体**不动**（spec FR-070）；改动只在 `init_workspace_inner` 的步骤 ④ |
| G10 | N-03 入口点不得位于 `core/` | ✅ PASS | 入口点仍在 `cli/cli_client.py` + `__main__.py` + `[project.scripts]`，本 Phase 不动 |
| G11 | §3.4 / D-05 模板与 sqlite3 schema 属 P2 | ✅ PASS | 本 Phase **不触碰**三个记忆库文件（spec FR-085）；模板源文件的追加与覆盖沿用 P2 的 `<条目路径>.txt` 规则 |
| G12 | §4.6 技术指标：单元测试覆盖率 ≥ 80%（`donkey.core`） | ✅ PASS | spec SC-020；覆盖率 MUST 以**独立命令**度量（MUST NOT 写入 pytest 全局 `addopts`，否则 e2e 单独运行时不 import 业务代码会把覆盖率拉到 0 而误报 —— 同 P2 的 R-13）。**注**：模板正文是 `.txt`，**不在 `donkey.core` 的覆盖率口径内**（R-08） |
| G13 | §3.1 `tests/e2e/phase/verify_phase_<f>_<n>.py` 必须真正被 pytest 收集 | ✅ PASS | `python_files = ["test_*.py", "verify_phase_*.py"]` 已含该模式 → 新脚本 `verify_phase_f001_p3.py` 自动被收集 |
| G14 | N-01 workspace 内禁止出现 `agent.py` / `main.py` 或任何 Python 入口文件；D-10 同义 | ✅ PASS（**口径澄清**） | 本 Phase 落地 **6** 个 `.py`（`tools/` 下 5 + Skill 第三层脚本 1），其中**无**智能体入口。**Skill 第三层演示脚本的授权来源 = 宪法 §6.3 例外 E-02 + §5 章 [D-19]**（N-01 的边界澄清："Python 入口文件"指**智能体入口**）—— 宪法侧已由 Maintainer 正式登记；**spec FR-050 MUST 引用该例外，MUST NOT 自设豁免**（2026-10-23 定点修订轮已由"spec 自设豁免 + 强制登记口径"改写为引用口径）。**E-02 的三条范围边界 MUST 逐条落地**：MUST NOT 位于 `tools/` 目录 / MUST NOT 命名为 `agent.py` · `main.py` / MUST NOT 承担"创建智能体"职责（唯一官方入口仍是 `donkey.core.api.create_agent`）→ 门禁 MUST NOT 把该脚本判为违例 |
| G15 | N-11 / §2.8 三端对等（cli / web / gui 共用 `core.api`） | ✅ PASS（阶段性） | 本 Phase 仅交付 cli 通道，`web/` / `gui/` 维持空占位；三端对等由 F005 / F006 达成 |
| G16 | §2.6 workspace 目录必填项（`instruction.md` / `providers/`（含 `default.toml`）/ `tools/` / `mcp/mcp.json` / `skills/` / `memory/`）+ D-01 的 workspace `manifest.json` | ✅ PASS | P2 已落地 6 项必填；本 Phase 在其之上把 `tools/` 填成**真实可用的 5 个文件** + 契约库 |
| G17 | N-02 禁止 subagent / 子智能体任何目录或字段 | ✅ PASS | 54 条清单条目中无任何 subagent 相关路径；模板正文亦无该类字段（spec FR-076） |
| G18 | §3.5 数据安全分级（凭据高敏感 / 自动脱敏 / 不上传 workspace） | ✅ PASS（阶段性） | `donkey init` **不打印**任何凭据；本 Phase 的工具模板不含凭据字段。**已知遗留**：`providers/*.toml` 不被 `.gitignore` 忽略（P2 登记，v2 议题）—— 本 Phase 不擅自改动 |
| G19 | D-11 `store.sqlite3` / `knowledge.sqlite3` v1 仅占位空文件 | ✅ PASS | 本 Phase MUST NOT 触碰三个记忆库文件（spec FR-085） |
| G20 | §4.6 技术验收：所有 exit code 与 §4.4 完全一致 | ✅ PASS | 本 Phase 实际使用 `{0,1,2,3,4}`；`contracts/exit-codes.md` 给出完整映射表与 exit 4 的两类成因 |
| **G21** | **§4.3 Phase 切分规则** —— 本 Phase 是 F001 的**最后一个** Phase | ✅ PASS | 本 Phase 完成后 F001（`donkey init`）**整体完成**；其后的 `donkey load` / `session` / `run` / `web` / `gui` 均属其它 Feature。本 Phase 的产物是它们的前置（工作区就绪） |
| G22 | N-06 / N-07 / N-09 / N-10（`donkey load` 失败不改 workspace / `load` 不依赖 `init` / session 标题即对外标识 / session 首轮提示词摘要） | **不适用** | 四条均属 **`donkey load` / `donkey session` 域**（退出码段位 `11-20` / `21-30`），本 Phase 只做 `donkey init` 的模板生成 → **明确不适用**（未被覆盖 ≠ 已覆盖） |
| G23 | §2.1 两层模型（材料层 vs 引擎层 · 最高架构原则）/ §2.4 Skills 三层渐进披露 + D-07 frontmatter 严格性 / §2.5 内置 `@tool` 与中间件职责正交 / §2.7 中间件录用与禁用清单 | ✅ PASS | 材料层只提供能力、**不划边界** —— 路径白名单 / 权限交互 / diff 审阅均属引擎层，MUST NOT 在本 Phase 实现（spec FR-089 / FR-090 / FR-082 / **SC-021**，宪法 §2.1 / AC-5）；Skills 示例三层齐备且 frontmatter 恰含 `name` + `description` **两字段**（spec FR-047 ~ FR-051，D-07）；3 个内置工具 MUST NOT 含检索能力（spec FR-025 · SC-013）；MUST NOT 挂载任何中间件（spec FR-081 / FR-082） |

**门禁结论**：**无违例**。两处状态变化：G4 由"集成层留空"改为"**启用**"（P2 的理由已失效，spec FR-061 要求重新论证）；G5 由"Deferred（E-01 覆盖）"改为"**PASS（E-01 到期闭合）**"。G6 是本 Phase 风险最高的一条（模板正文要 import 框架官方装饰器）→ 由 FR-077 / FR-078 / FR-079 的**三向约束**（donkey 侧不 import / 渲染产物侧不含可观测性字样 / 门禁冒烟限定在 donkey 自有代码路径）闭合。G23 为本 Phase 补充登记的材料层职责边界门禁（§2.1 / §2.4 / §2.5 / §2.7）—— 判定依据落在 spec FR-025 / FR-047 ~ FR-051 / FR-081 / FR-082 / FR-089 / FR-090。

**Phase 0 research 放行**（R-01 ~ R-20 已落地，NEEDS CLARIFICATION 残留 **0** 项）。

### Phase 1 设计后复核（Re-check）

| 门 | 复核结论 | 复核要点 |
|---|---|---|
| G2（分层） | ✅ 维持 PASS | **零新增 import** 在 `core/` 与 `cli/`；工具装饰器与 HTTP 客户端的 import 只在 `templates/tools/*.txt` 内。quickstart §4 给出 4 条 grep 自检（`donkey/` 与 `cli/` 内 MUST NOT 出现工具装饰器 / HTTP 客户端 / langsmith） |
| G4（测试三层） | ✅ 维持 PASS（**已重新论证**） | 集成层启用的理由已写实（跨模块协作真实出现：core 层产物被独立进程导入并调用）；三层职责边界见 [data-model.md](data-model.md) §8 |
| G5（CI） | ✅ 维持 PASS（**新增证据**） | `.github/workflows/ci.yml` 的最小内容已由 R-14 定死；e2e 第 16 个断言会**实测**该文件存在且含四类关键命令（spec FR-065） |
| G6（永不使用清单） | ✅ 维持 PASS（**新增证据**） | `tools/changes.py` **零框架 import**（纯 stdlib）→ 未来的工具扫描器对其零歧义（FR-011 / FR-091 的风险登记）；quickstart §1 把它固化为门禁冒烟 |
| G7（路径绝对化） | ✅ 维持 PASS（**收紧**） | 环境变量开关已移除（spec FR-002 / FR-104）→ 工作区根**恒定**由契约库自身位置推导，无隐藏全局状态 |
| G8（幂等 + 原子性） | ✅ 维持 PASS（**新增一处受控例外**） | R-07 的条目级豁免只作用于契约库**一个**条目；P2 的通用通则**一字不改**（`render_templates` 不动），FR-069 的"MUST NOT 削弱其余条目"得到结构性保证 |
| G12（覆盖率） | ✅ 维持 PASS（**口径澄清**） | 模板正文是 `.txt` → 不在 `donkey.core` 覆盖率口径内；其质量由 R-08 的 `compile()` 自检 + ≥15 个单元用例兜底 |
| G14（N-01） | ✅ 维持 PASS（**口径澄清**） | 6 个 `.py` 中无智能体入口；Skill 第三层演示脚本的授权**已由宪法正式登记** —— 宪法 §6.3 **例外 E-02** + §5 章 **[D-19]**（N-01 的边界澄清："Python 入口"指智能体入口）；spec FR-050 MUST **引用**该例外而非自设豁免（2026-10-23 定点修订轮已把 FR-050 由"spec 自设豁免 + 强制登记口径"改写为引用口径，并补入 E-02 的两条边界：禁命名 `agent.py` / `main.py`、禁承担"创建智能体"职责） |
| G21（Phase 切分） | ✅ 维持 PASS | 本 Phase 完成后 F001 整体完成；后续 Feature 不得把 init 域的功能回灌 |

**复核结论**：**无违例**（唯一涉例外的 N-01 口径已由宪法 §6.3 **例外 E-02** + §5 章 **[D-19]** 正式登记，见 Complexity Tracking）。Phase 1 设计（[data-model.md](data-model.md) + [contracts/](contracts/) × 5 + [quickstart.md](quickstart.md)）未引入任何新的宪法冲突；两处状态变化（G4 启用集成层、G5 闭合 E-01）均已在 spec 侧有对应条款（FR-061 / FR-065）。

**Phase 1 设计放行** → 可进入 `/speckit.tasks`。

### 本轮 spec 定点修订轮（S1 ~ S5）的 plan 对齐登记（2026-10-23 · 第二轮）

> spec 已于 2026-10-23 完成第二轮定点修订（`## Clarifications` 新增第 5 段 / 4 项决策）—— **需求层语义逐条未变**（FR 仍 **105** 条、SC 仍 **24** 条，编号一字未动），全部属"**授权来源改引用 / 判据可判定化 / 表述钉死**"的原地改写。本 plan 与 Phase 1 设计产物据此对齐如下 —— **MUST NOT** 把本轮误读为"新增功能 / 新增宪法例外 / 新增计数口径"。

| spec 决策 | plan / 设计侧落点 | 性质 |
|---|---|---|
| **S1** FR-050 的授权来源由"spec 自设豁免 + 强制登记口径"改为**引用宪法例外 E-02 + §5 章 [D-19]** | plan G14（首轮）+ G14 复核（Phase 1）+ 复杂度与风险 §Complexity Tracking（E-02 行）+ 结构树 `scripts/example.py.txt` 注释；[research.md](research.md) R-16 的 (b) 行；[data-model.md](data-model.md) §1 实体树 + §10 术语表；[contracts/template-manifest.md](contracts/template-manifest.md) §3 第 7 条 + §5 B6 | **授权来源改引用** —— spec 侧 MUST NOT 自设宪法例外；plan / 设计侧 MUST NOT 再使用"spec 自设豁免 / 强制登记口径"措辞 |
| **S1b** E-02 的两条边界（MUST NOT 命名为 `agent.py` / `main.py`；MUST NOT 承担"创建智能体"职责） | plan G14 的"E-02 三条范围边界 MUST 逐条落地" | **边界落地**（宪法 E-02 早已列明，非 spec 新增） |
| **S2** FR-004 的指纹"为空"钉死为 `null`（Python 侧 `None`，MUST NOT 用空串） | [contracts/change-record-contract.md](contracts/change-record-contract.md) §1 第 7 / 9 行 + §3 动作矩阵；[data-model.md](data-model.md) §2.1 字段表；[quickstart.md](quickstart.md) §3.2（`previous_hash` 的 `None` 安全取值） | **表述钉死** —— 契约层本就按 `null` 落地，本轮只把 spec 的占位表述钉到与契约一致 |
| **S3** SC-021 由"出现次数各为 1"（不可判定）改写为**两类可判定判据**（行为层报错 + 静态层措辞 ≥ 1 次） | plan R-19 + G23 + 复杂度与风险新增"判据被过度收紧"一行；[quickstart.md](quickstart.md) §3.6 补齐**行为层**（四道边界各自报错 + 回环地址 MUST 被放行）与**静态层**（说明文字逐条措辞 ≥ 1 次）的可手验步骤 | **判据可判定化** —— 四项边界、5 MiB 数值、"不限制地址范围"的结论均未变 |
| **S4** FR-068(a) 的嵌套加粗修复（`**54 / 48 / 49 / **10****` → `**54 / 48 / 49 / 10**`） | 无 —— 纯 Markdown 格式 | **纯格式** |
| **S5** "read_file 返回值语义变更"收敛为 **FR-015** 单一权威表述，另两处改交叉引用 | [data-model.md](data-model.md) §10 术语表「呈现文本」条（已与 FR-015 口径一致，无需再展开） | **维护面收敛**（×3 → ×1），语义未变 |
| **分析轮**（2026-10-23 · `/speckit.analyze` 交叉核对） | spec：8 处悬挂引用（5 处指纹"为空" + 3 处"FR-050 的豁免条款"）全部对齐 + 新增 `## Clarifications` 第 6 段留痕；tasks：T012 补 FR-090 的 docstring 义务、T008 ~ T012 补 FR-076 / FR-079、T008 覆盖标签补 FR-005 / FR-012 / FR-091、头部 `[P]` 定义改写、T100 计数纠偏、Phase 18 子标题纠偏；contracts：`tool-contracts.md` §4 补 FR-090 静态契约、`template-manifest.md` 口径改为引用 E-02 / [D-19] | **表述对齐 + 落点补齐** —— FR 105 / SC 24 与任务 ID T001 ~ T108 一律未动 |

> **tasks.md 的对齐已于分析轮完成**：`tasks.md` 的 T016 / T046 / T094 的授权措辞已改为"引用宪法 §6.3 例外 E-02 + §5 章 [D-19]"（见上表「分析轮」行）；**MUST NOT** 再以"spec 自设豁免"措辞回流。

---

## Project Structure

### Documentation (this feature)

```text
specs/001-donkey-init-workspace/phase-3-builtin-tools/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output（决策 R-01 ~ R-20 + 待回填 spec 清单，**已于 2026-10-23 闭合**）
├── data-model.md        # Phase 1 output（实体 / 状态机 / 计数口径）
├── quickstart.md        # Phase 1 output（可执行的验证指南）
├── contracts/           # Phase 1 output
│   ├── tool-contracts.md          # 9 个 @tool 的签名 + 返回形状（材料层公开契约）
│   ├── change-record-contract.md  # 变更记录 schema v1（12 基线 + 4 条件字段）
│   ├── template-manifest.md       # 54 条清单 + 45 个源文件 + 8 条新源的内容契约
│   ├── cli-contract.md            # exit 4 的异常映射 + 渲染层豁免 + 计数口径
│   └── exit-codes.md              # 退出码映射表（本 Phase 新增 exit 4）
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
donkey/
├── core/
│   ├── api.py                          # 门面 —— 本 Phase 不动（FR-070）
│   ├── exceptions.py                   # 追加 1 个异常类 BuiltinToolGenerationError
│   ├── exit_codes.py                   # 仅改 EXIT_CODE_BUILTIN_TOOL_GENERATION 的文档串（R-10）
│   └── workspace/
│       ├── init.py                     # 仅 init_workspace_inner 步骤 ④ 加条目级豁免（R-07）
│       ├── manifest.py                 # 不动
│       ├── sqlite3_templates.py        # 不动
│       └── templates/                  # ← 本 Phase 主战场
│           ├── manifest.json           # 追加 8 条（46 → 54）
│           ├── tools/
│           │   ├── __init__.py.txt          # 新增
│           │   ├── changes.py.txt            # 新增（契约库，0 个 @tool）
│           │   ├── filesystem.py.txt         # 新增（7 个 @tool）
│           │   ├── commandline.py.txt        # 新增（1 个 @tool）
│           │   └── README.md.txt             # 覆盖（P2 占位正文 → 完整规范）
│           ├── skills/example/
│           │   ├── SKILL.md.txt              # 覆盖（补完整 Level 2 正文）
│           │   ├── reference/example.md.txt  # 新增
│           │   ├── scripts/example.py.txt    # 新增（含 __main__ 入口块 · 宪法 E-02 + D-19 授权）
│           │   └── templates/example.md.txt  # 新增
│           └── …（P1 / P2 的既有源文件，一律不动）
├── cli/cli_client.py                   # 异常映射表追加 1 行

tests/
├── unit/
│   ├── test_builtin_tools.py           # 新增（≥15 个用例）
│   ├── test_template_skeleton.py       # P2 既有 —— 阶段边界断言组逐条核对改写（R-16）
│   ├── test_init_workspace.py           # P1 既有 —— 不动
│   └── test_cli_client.py               # P1/P2 既有 —— 不动
├── integration/
│   └── test_init_to_load.py            # 新增（≥4 个用例；本 Phase 首次启用该层）
└── e2e/phase/
    ├── verify_phase_f001_p1.py         # P1 既有 —— 不动（必须仍全绿）
    ├── verify_phase_f001_p2.py         # P2 既有 —— 改写场景 1 与场景 11（R-15 / R-16）
    └── verify_phase_f001_p3.py         # 新增（16 个黑盒断言）

.github/workflows/ci.yml                # 新建（E-01 到期闭合，R-14）
pyproject.toml                          # dev 依赖追加 pytest-httpx（R-04）
```

**Structure Decision**：沿用**单包 + 三层测试**结构（**Option 1**，与 F001-P1 / P2 完全一致）—— 不引入新包、不引入新分层。本 Phase 的产物**不是** donkey 运行时代码的新模块，而是**渲染进用户工作区的模板源**；故结构树的关键变化集中在 `donkey/core/workspace/templates/` 子树与三处追加式改动。

---

## 复杂度与风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| **模板正文零静态检查覆盖**（R-08） | 模板里的真实算法逻辑若语法错误，用户的 workspace 直接不可用，且 ruff / mypy 抓不到 | 每个渲染出的 `.py` MUST `compile()` 成功（单元测试自检）；≥15 个单元用例覆盖每个工具的每条分支 |
| **模块按名缓存导致验收假绿**（R-02） | 单元层第二个用例可能拿到第一个工作区的产物 | 夹具 teardown MUST 清 `sys.modules`；集成层与 e2e 层一律用**独立子进程**（FR-062 / FR-066） |
| **spec FR-070 与 FR-105 的张力** | 二者字面冲突 | R-07 的最小侵入解法（只改编排层，不动通用渲染器）；**已于 2026-10-23 在 spec FR-070 内定点闭合**（research.md 待回填清单第 1 项） |
| **与 OpenCode 的 5 处有意偏离** | "完全照搬"的表述与实际实现有落差 | 全部登记在 spec FR-098 的"五处有意偏离"（**已于 2026-10-23 闭合** —— research.md 待回填清单第 2/3 项）；每处都有"为什么偏离"的理由 |
| **`httpx.request()` 一次性读爆内存** | 违反 FR-089(b) | R-03 强制流式；单元用例用 chunked 响应实测触发上限（R-04） |
| **httpx 默认 `trust_env=True` 隐式读取代理 / 证书环境变量** | 违反 FR-104（"工具 MUST 不读任何环境变量"），且与 FR-089 的"MUST NOT 实现…代理"相悖 | R-03 / R-19 钉死 `httpx.Client(trust_env=False, ...)`；T019 的静态断言虽只查 `os.environ` / `getenv` 字样，但实现侧 MUST 显式关闭 |
| **SC-021 两类判据被"过度收紧"**（2026-10-23 定点修订轮新增登记） | 实现侧把"四道边界 MUST 报错"误扩成"地址范围也拦" → 违反 FR-089 / SC-021(a) 的"**地址范围限制 MUST NOT 被实现**"，且与宪法 §2.1"材料层只提供能力、不划边界"相悖 | 判据逐项对照 SC-021(a) —— **四道边界报错** 与 **回环地址 / 私有网段 / 云主机元数据地址被放行** 是**两条方向相反**的 MUST，单元层 MUST 同时覆盖两者；quickstart §3.6 给出可手验的两侧步骤 |
| **子进程用脚本文件而非 `python -c`** | `sys.path[0]` 是脚本目录 → 找不到工作区的 `tools` 包（R-20 实测） | e2e 的子进程 MUST 用 `-c`（与 P1 / P2 的既有写法一致） |
| **P2 既有套件被改红** | 违反 FR-069 | 只改**阶段边界**断言组（R-15 / R-16 —— 按其逐条核对口径，MUST NOT 以概括性计数为准），P2 的其余 **12** 个 e2e 场景与全部持久不变量 MUST 原样保持绿；SC-002 承载 |
| **CI 覆盖率口径误报** | e2e 单独跑时覆盖率被拉到 0 → CI 红 | 覆盖率 MUST 用**独立命令**度量，MUST NOT 写进 pytest 全局 `addopts`（R-14） |

---

## 实施顺序（任务拆解留给 `/speckit.tasks`）

```text
① 契约库骨架      tools/changes.py.txt（0 个 @tool、纯 stdlib、9 个公开函数 + 1 异常类 + 3 常量）
② 文件工具        tools/filesystem.py.txt（7 个 @tool；读取侧统一分页路径 R-11 + 目录分支）
③ 命令工具        tools/commandline.py.txt（1 个 @tool；输出截断 R-17）
④ 网络工具        tools/webfetch.py.txt（1 个 @tool；流式 + 四道边界 R-03 / R-19）
⑤ 支撑文件        tools/__init__.py.txt + 覆盖 tools/README.md.txt
⑥ Skills 三层     覆盖 skills/example/SKILL.md.txt + 新增 3 个 Level 3 源
⑦ 清单与源文件    manifest.json 追加 8 条（46 → 54）+ 核对 45 个源文件齐备
⑧ 核心与客户端    exceptions.py（+1 类）/ exit_codes.py（改文档串）/ cli_client.py（+1 行）/ init.py（豁免分支 R-07）
⑨ 单元测试        tests/unit/test_builtin_tools.py（≥15 用例；含模板自检与常量一致性断言）
⑩ 集成测试        tests/integration/test_init_to_load.py（≥4 用例；独立子进程）
⑪ 黑盒验收        tests/e2e/phase/verify_phase_f001_p3.py（16 断言）
⑫ 改写 P2 边界    test_template_skeleton.py（按 R-16 的断言组逐条核对改写）+ verify_phase_f001_p2.py（场景 1 / 11）
                **实际随 Phase 3 的资产落地同步执行（tasks 的 T094 / T095 落在 Phase 3 末尾）** —— 清单一变（T014），
                P2 的阶段边界断言即失效，改写 MUST 紧随其后，P2 套件才尽早恢复绿（见 tasks 的「P2 套件的中间态」段）
⑬ CI 与依赖      .github/workflows/ci.yml + pyproject.toml dev 依赖（**实际落在 Phase 1** —— 依赖与 CI 都是
                前置就位项，不是收尾项；tasks 的 T001 ~ T003 已按此排）
                **编号 ≠ 相位** —— T094 / T095 落在 Phase 3 末尾、T001~T003 落在 Phase 1，均以 tasks.md 为准
⑭ 全量验证        跑 §"可执行测试命令列表" 全量 + 静态检查 + 门禁冒烟
```

---

## 后续 Phase / 仓库级（不属本 Phase）

| 事项 | 归属 |
|---|---|
| 工具的**用户可见导入验证**能力（"这个工作区的工具能不能被加载"） | **F002 `donkey load`**（spec FR-072 的明确边界） |
| 工作区工具的**自动扫描与注册**（`tools/*.py` → `@tool` 集合）、"无 `@tool` 的辅助模块"容忍 | F002（spec FR-091 的风险登记项） |
| Skills Level 1 扫描 + Level 2 读取 + Level 3 集成（`core/skills/loader.py`） | F004-P2 |
| 引擎层差异审阅 / 人工审批 / 回滚（消费本 Phase 的变更记录契约） | 引擎层 v4 或 fork（AC-5） |
| 引擎层路径权限交互（消费本 Phase 的"路径白名单由用户自管"） | 引擎层 v4 / fork |
| 中间件挂载（10 项录用清单） | F004 |
| 多模态附件交付（图片 / PDF 直接给模型） | 引擎层（spec FR-096 的已知缺口） |

---

## Complexity Tracking

> **本 Phase 涉及宪法临时例外 1 条（宪法 §6.3 E-02，已由 Maintainer 批准）**：宪法 §6.3 临时例外 **E-01**（"F001-P1 与 F001-P2 均不交付 `ci.yml`"）在本 Phase **到期闭合**（本 Phase 交付该文件）；同时本 Phase **引用宪法已登记的例外 E-02**（宪法侧登记已完成 —— Maintainer 2026-10-23 批准；本 plan 的职责是**登记与引用**，MUST NOT 自设任何宪法例外）—— F001-P3 的示例 Skill **第三层附属资源目录**下的**普通演示脚本**（`skills/example/scripts/example.py`，含 `__main__` 入口块）**不属** N-01 / D-10 / §2.6 / §3.2 所禁的"Python 入口文件"（边界澄清见 §5 章 [D-19]）。E-02 的**范围 / 理由 / 替代保障 / 过期时间**以宪法 §6.3 的登记条目为准（过期时间 = F001-P3 结束前 —— 最迟转为正式纳入宪法，或移除该脚本的入口块）。**除 E-02 外，本 Phase 不引入任何其它宪法例外、不新增临时豁免、不新增退出码段位。**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **E-02**（宪法 §6.3，已登记） | F001-P3 的示例 Skill 需以"第三层可执行脚本"展示"模型如何按需调用附属资源"，该脚本 MUST 保留 `if __name__ == "__main__": sys.exit(main())` 入口块（与源提示词模板逐字一致；**spec FR-050 MUST 引用 E-02 / [D-19]，MUST NOT 自设豁免**） | ❌ 删掉入口块 → 偏离源提示词模板正文，且无法演示"被调用"语义；❌ 把脚本移出工作区 → 第三层"可执行脚本"这一形态无法交付；❌ 在 spec 内**自设**一条豁免 → 与宪法 §6.1 / §6.3 冲突（例外须在宪法登记册登记），且与 plan 的 Complexity Tracking 互斥 |
| （无其它） | —— | —— |

---

## 可执行测试命令列表（"Phase 完成" 的硬性证据）

```bash
# ① 前置套件（必须全绿）
pytest tests/e2e/phase/verify_phase_f001_p1.py -v
pytest tests/e2e/phase/verify_phase_f001_p2.py -v
pytest tests/unit/test_init_workspace.py -v
pytest tests/unit/test_template_skeleton.py -v

# ② 本 Phase 套件
pytest tests/unit/test_builtin_tools.py -v          # ≥15 个用例
pytest tests/integration/test_init_to_load.py -v    # ≥4 个用例
pytest tests/e2e/phase/verify_phase_f001_p3.py -v   # 16 个断言

# ③ 静态检查
ruff check donkey/ tests/
mypy donkey/ tests/

# ④ 覆盖率（独立命令，MUST NOT 写进 addopts）
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80

# ⑤ 完整套件
pytest tests/ -v

# ⑥ CI 交付自检（E-01 到期）
test -f .github/workflows/ci.yml && echo "OK ci.yml 已交付" || echo "FAIL E-01 已到期，ci.yml 缺失"
grep -cE "pytest tests/|--cov=donkey.core|--cov-fail-under=80|ruff check|mypy" .github/workflows/ci.yml
```

**详细逐条验证步骤见 [quickstart.md](quickstart.md)。**
