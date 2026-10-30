# 研究记录：F001-P4 `cli_version` —— `donkey version` 查询版本号

**Phase**: F001-P4 / `cli_version` | **日期**: 2026-10-30 | **Spec**: [spec.md](spec.md)

> 本文件是 `/speckit.plan` 的 Phase 0 产物 —— 记录本 Phase 的**技术决策**（R-01 ~ R-19）。
> **NEEDS CLARIFICATION 残留：0 项**（spec 的 38 条 FR / 16 条 SC / 9 项 Clarifications（2 段）已全部收敛，无待澄清项）。
> 每条决策给出：**决策 / 理由 / 被否决的备选**。凡 spec 已裁决的事项（Clarifications Q1 ~ Q9 + Maintainer 前置裁决 D-1 / D-2 / D-3）本文件**只引用、不重裁**。

---

## R-01 · 版本取值解析的落点 = 核心层新模块 `donkey/core/version.py`

**决策**：新增 `donkey/core/version.py`，承载版本取值的解析与展示形态拼接。

**理由**：
- spec FR-020 要求「版本取值的解析 MUST 落在**核心层**（`donkey/core/` 下），MUST NOT 落在客户端层（`donkey/cli/`）」—— 理由是 F004-P7 建图时改核心层即可，MUST NOT 迫使客户端层跟着改；
- 宪法 N-03（core 不 import client）/ N-05（core 不 import argparse / sys.argv）：新模块是纯 stdlib，无任何边界风险；
- 宪法 N-04（cli 不直接 import langchain / langgraph / sqlite3）：本 Phase **零新增**这三类导入。

**被否决的备选**：
- ❌ 放在 `donkey/cli/cli_client.py` → 违反 FR-020，F004-P7 将被迫改客户端；
- ❌ 放在 `donkey/core/api.py` → 违反 FR-020 末句「本命令 MUST NOT 因此新增 `donkey.core.api` 的库 API」（宪法 §4.2 修订后豁免条款的边界之一）；
- ❌ 放在 `donkey/__init__.py` → 该文件当前「不 import 任何模块」（仅 `__version__`），加 `importlib.metadata` 会改变它的导入语义，且 spec FR-026 禁止改动其 `__version__` 常量 —— 同文件改动易被误读为「改版本号」。

---

## R-02 · 核心层对外暴露两个函数；`v` 前缀逻辑单点收敛

**决策**：`donkey/core/version.py` 暴露两个公开函数：

| 函数 | 返回 | 语义 |
|---|---|---|
| `resolve_version() -> str` | `"0.1.0"` | **底层取值** —— 与 `pyproject.toml` 的 `version` / 包内 `__version__` / 工作区清单 `donkey_version` 字段**逐字节一致**（spec FR-013） |
| `version_string() -> str` | `"v0.1.0"` | **展示值** = `"v" + resolve_version()`（spec FR-013 的 `v` 显示前缀） |

客户端层只调 `version_string()` 并 `print()`。

**理由**：
- spec FR-019 要求「版本取值 MUST 只有一个**运行期来源**」—— 前缀拼接若散落在三端，将来 F005 / F006 各自加一次前缀就有漂移风险；单点收敛后三端复用同一函数；
- spec FR-007 的判据是「**去掉行终止符后**的正文」—— 客户端只负责输出与行终止符，取值语义归核心层，职责边界清晰；
- 两个函数都是**纯函数**（无 IO 副作用、无退出码、无打印）—— 符合宪法 N-05「核心层 MUST NOT 返回退出码 / 打印 / 退出进程」。

**被否决的备选**：
- ❌ 客户端层自己拼 `"v" + ...` → 前缀逻辑会随客户端数量增长而复制（当前 1 处，将来 3 处）；
- ❌ 只暴露一个函数返回带 `v` 的值 → 底层取值（要与工作区清单逐字节比对的那个）就无处可取，spec FR-013 的比对判据失去落点；
- ❌ 核心层返回 `("0.1.0", "v0.1.0")` 元组 → 过度设计，两个函数更直白。

---

## R-03 · 分发元数据查询 = `importlib.metadata.version("donkey")`

**决策**：以标准库 `importlib.metadata` 查询名为 `donkey` 的发行版版本。

**理由**：
- spec FR-016 明确要求「**安装分发元数据**查询（标准库的分发元数据接口，查询的发行版名为 `donkey`）」，并引用 F001-P2 FR-021「将来若改为动态获取，MUST 使用包元数据查询方式」—— 本 Phase 正是那个「将来」，故走包元数据；
- **实测**（本机 Python 3.12）：`importlib.metadata.version("donkey")` → `0.1.0`（仓库根的 `donkey.egg-info/` 被 `sys.path` 发现）；
- **实测**：发行版不存在时抛 `importlib.metadata.PackageNotFoundError`（`No package metadata was found for donkey`）—— 这正是 spec FR-017 的回退触发条件，异常类型明确、可精确捕获。

**被否决的备选**：
- ❌ 直接读 `pyproject.toml` → spec FR-016 明文禁止（构建期文件，运行期不可靠；且安装后的包里没有该文件）；
- ❌ `pkg_resources` → 已废弃（setuptools ≥ 81 起对未安装场景告警），非标准库主流路径；
- ❌ `importlib.metadata.distribution("donkey").version` → 与 `version()` 等价但多一步，异常类型相同，无收益。

---

## R-04 · 回退源 = 包自身的 `__version__` 常量（公开导出，零循环依赖）

**决策**：`resolve_version()` 捕获 `PackageNotFoundError` 后回退到 `from donkey import __version__`。

**理由**：
- spec FR-017 要求回退到「**包自身的 `__version__` 常量**」；
- **实测**：`donkey/__init__.py` **不 import 任何模块**（仅 `__version__ = "0.1.0"` + `__all__ = ["__version__"]`）→ `donkey.core.version` 里 `from donkey import __version__` **不会形成循环导入**（`donkey/__init__.py` 不回头 import `donkey.core.*`），且 import 成本几乎为零；
- `__version__` 是**公开导出**（在 `__all__` 里）→ 属包的公开面，读取它不是"import 内部符号"（F001-P2 FR-021 禁止的是 manifest 去 import 内部符号，此处不同）。

**被否决的备选**：
- ❌ 再读一次 `pyproject.toml` → FR-016 已禁止，且源码检出场景下该文件可能不在包内；
- ❌ 回退时抛错 / 返回空串 → 违反 FR-017「MUST NOT 抛异常 / MUST NOT 使命令失败 / MUST NOT 输出空值」。

---

## R-05 · 元数据与 `__version__` 不一致时以**元数据**为准

**决策**：不比较、不告警，直接返回元数据的结果。

**理由**：
- spec FR-018 明确「MUST 以**分发元数据**为准（它代表用户实际安装的那一份），MUST NOT 报错」；
- 语义正确性：用户跑的是**装上去的那一份**，不是仓库里的源码 —— 元数据描述的才是实际被 import 的发行版。

**被否决的备选**：
- ❌ 以 `__version__` 为准 → 与"实际安装的那一份"相反；
- ❌ 不一致时打印告警 → 会污染 stdout（spec FR-007 要求 stdout 恰好一行版本值、FR-009 要求成功路径 stderr 为空），告警要么破坏 FR-007、要么破坏 FR-009。

---

## R-06 · 子命令注册形态：无参数；argparse 自动提供 `-h/--help`

**决策**：`subparsers.add_parser("version", help=..., description=...)`，**不添加任何 `add_argument`**。

**实测**（用 `DonkeyArgumentParser` 的同款覆写复现）：

| 输入 | argparse 行为 | 进程退出码 |
|---|---|---|
| `version` | 解析成功 | `0` |
| `version --bogus` | `unrecognized arguments: --bogus` | **1** |
| `version web` | `unrecognized arguments: web` | **1** |
| `version extra` | `unrecognized arguments: extra` | **1** |
| `version --help` | 打印 usage + 描述 | **0** |

**理由**：
- 三类误用全部落到**退出码 1**（spec SC-006）—— 因为 `DonkeyArgumentParser.error()` 已把 argparse 默认的 `2` 改写为 `1`，且该覆写**自动传播到子解析器**（`add_parser` 以 `type(self)` 作 `parser_class`，见 `cli_client.py` 的既有注释 + F001-P1 research.md R-01）；
- `version --help` 走 argparse 的 help action → `parser.exit(0)`，**不经过** `error()` → 退出码 `0`（spec FR-004 / SC-013）；
- 顶层 `add_subparsers(dest="command", required=True)` 保持不变 → `donkey`（无子命令）仍按 F001-P1 既有口径以退出码 `1` 失败。

**被否决的备选**：
- ❌ 给 `version` 加任何参数（如 `--json` / `--short`）→ spec FR-001「该子命令 MUST **无任何参数**」；
- ❌ 自定义 `parser_class` 覆盖子解析器 → 既有覆写已自动传播，无需额外动作。

---

## R-07 · 顶层**不**提供 `--version` 标志

**决策**：顶层解析器不新增 `--version`。

**实测**：`donkey --version` → argparse 报 `the following arguments are required: command` → 退出码 **1**（因 `--version` 未被识别为合法可选参数，且顶层又缺必填子命令）。

**理由**：spec FR-038 / SC-014 / Clarifications Q4 —— Q2 之后 donkey 只剩**一个**版本号，多一个入口没有信息增益，且顶层 `--version` 在工具生态里通常被默认为"包版本"，与本命令"唯一版本号"的语义打架。

**被否决的备选**：
- ❌ 加且与 `version` 等价 → 纯重复；
- ❌ 加且两者形态分工（`--version` 出 `0.1.0`）→ 同一值两种记法（spec Clarifications Q4 已否决）。

---

## R-08 · 输出用 `print()` —— 一行 + 一个行终止符

**决策**：`print(version_string())`。

**理由**：
- spec FR-007 要求「恰好一行 = 版本值 + **一个**行终止符，MUST NOT 有前导 / 尾随空白」→ `print()` 恰好写 `值 + "\n"`，不多不少；
- spec FR-007 的判据以「**去掉行终止符后**的正文」为准 → 跨平台 `\n` / `\r\n` 差异不构成命令差异，**验收断言 MUST NOT 直接比对原始字节**（否则 Windows 上假失败）；
- **不**用 `sys.stdout.write`（少了行终止符 → 某些终端的提示符会与版本值粘在一行）。

**被否决的备选**：
- ❌ `sys.stdout.write(value)` → 无行终止符，终端表现退化；
- ❌ `print(f"[donkey version] {value}")` → 违反 FR-007（MUST NOT 带前缀）与 FR-010（MUST NOT 套用 `key=value` 摘要形态）。

---

## R-09 · e2e 期望值取自**工作树声明**（`pyproject.toml` 的 `version`）

**决策**：验收脚本用 `tomllib`（Python 3.11+ 内置）读工作树 `pyproject.toml` 的 `version`，据此构造期望值 `"v" + version`；并**另行断言**该声明值当前为 `"0.1.0"`。

**理由**：
- spec SC-003 明确要求「验收脚本 MUST 以**工作树声明的版本**（`pyproject.toml` 的 `version`）为期望值来源，并 MUST 另行断言该声明值当前为 `0.1.0` —— MUST NOT 让断言随安装形态漂移（MUST NOT 因分发元数据陈旧而产生假失败）」；
- 与既有约定一致：F001-P3 的验收脚本已读取仓库文件（`.github/workflows/ci.yml`）做交付检查 → e2e 读仓库文件是本仓库的既定做法，不是破例；
- **实测**：本机 `donkey` **未**安装进 site-packages（`pip show donkey` → not found），版本元数据来自仓库根的 `donkey.egg-info/`（已被 `.gitignore` 的 `*.egg-info/` 规则忽略）→ 若某次安装陈旧，硬编码 `v0.1.0` 断言会假失败；按声明取值则恒成立。

**被否决的备选**：
- ❌ 硬编码 `v0.1.0` → 安装形态漂移时假失败（spec SC-003 明文禁止）；
- ❌ 只断言"输出形如 `vX.Y.Z`"（不比对具体值）→ 判据过弱，无法发现"打印了错误版本"这类真 bug。

> **⚠️ 失效登记（2026-10-30 analyse 缺陷修复轮）**：本条的**「期望值来源」部分已被 R-18 取代** —— spec SC-003 已改为**双比对**口径（工作树声明值 + 安装分发元数据值；两者不等时以**分发元数据**为准，FR-018），故上述**理由**中对 SC-003 原文的逐字引用已失效。本条**保留**的部分 = 「另行断言工作树声明值当前为 `0.1.0`」（该断言仍 MUST 执行）；**被取代**的部分 = 「以工作树声明为唯一期望值来源」。实施口径见 **R-18**（spec FR-013 / SC-003 的「常规安装形态下」限定）。

---

## R-10 · e2e「分发元数据不可得」的**真黑盒**复现手法 = 复制 `donkey/` 包到临时目录 + **`python -S` 屏蔽 site-packages**

**决策**：验收脚本把工作树的 `donkey/` **包目录**复制到 `tmp_path` 下，在该副本的根目录执行 **`python -S -m donkey version`**（`-S` 屏蔽 site-packages）。

**⚠️ 修正记录（2026-10-30 · 分析轮实测）**：本条**原决策只说"副本同级没有 `*.egg-info`"**，并断言"在 CI（`pip install -e .` 已装）里同样成立" —— **该断言已被实测证伪**：CI 的 `pip install -e ".[dev]"` 会把 `donkey-0.1.0.dist-info` 装进 site-packages，而 `importlib.metadata` 搜索**全部** `sys.path` 条目 → 副本内**照样找得到**分发元数据 → 回退分支**根本没被覆盖**；而验收任务要求"先断言确实抛 `PackageNotFoundError`" → **正确实现在 CI 里也会把该场景判红**，退出条件 SC-007 永远无法达成。**修正**：MUST 追加 `-S`（屏蔽 site-packages），使"元数据不可得"在任何环境下都成立。

**实测（关键验证 · venv 模拟"donkey 已安装"）**：

```text
$ python3 -m venv --without-pip /tmp/venv          # 造一个"已安装 donkey"的环境
$ mkdir -p /tmp/venv/lib/python3.12/site-packages/donkey-0.1.0.dist-info
$ printf 'Metadata-Version: 2.1\nName: donkey\nVersion: 0.1.0\n' > .../donkey-0.1.0.dist-info/METADATA
$ mkdir -p /tmp/iso && cp -r <repo>/donkey /tmp/iso/donkey && cd /tmp/iso

# ❌ 只靠"副本同级没有 *.egg-info" —— 元数据仍可得，回退分支未覆盖
$ /tmp/venv/bin/python -c "import importlib.metadata as md; md.version('donkey')"
  → 0.1.0                              # ← 已安装的发行版被 site-packages 命中

# ✅ 追加 -S（屏蔽 site-packages）—— 元数据必然不可得
$ /tmp/venv/bin/python -S -c "import importlib.metadata as md; md.version('donkey')"
  → PackageNotFoundError: No package metadata was found for donkey

# ✅ -S 下 donkey 的导入链仍然完整（无任何第三方依赖）
$ /tmp/venv/bin/python -S -c "import sys, donkey.cli.cli_client; print(any(m.startswith('langgraph') for m in sys.modules))"
  → False                              # 实测：不加载 langgraph，纯 stdlib
```

**理由**：
- 副本的**同级没有 `*.egg-info`** + **`-S` 屏蔽 site-packages** → `importlib.metadata` **找不到任何 donkey 发行版** → 精确命中 spec FR-017 的回退分支，**且与环境无关**（装了、没装、editable 装都一样）；
- `-S` **不影响** `donkey` 的可用性：`donkey.cli.cli_client` 的导入链实测**纯标准库**（`langgraph` **不**进入 `sys.modules`，`sqlite3` 是标准库）→ 无需任何第三方依赖即可在 `-S` 下运行；
- 这条路径**真黑盒**：不 import `donkey.*` 业务代码、不打桩、不 monkeypatch（spec FR-033 硬约束）—— 优于 F001-P3 R-20 的"子进程内打桩"手法；
- 同时**顺带**验证 spec FR-020 的落点要求（副本里没有 `.specify/`、没有测试资产，命令仍能独立工作）。

**被否决的备选**：
- ❌ 子进程内 monkeypatch `importlib.metadata.version` → 需 import `donkey.cli.cli_client`（违背 FR-033 的黑盒意图）；
- ❌ 依赖"当前环境恰好没装 donkey" → 脆弱，且 CI 里 `pip install -e .` 必然装了 → **必须**用可构造的副本法；
- ❌ 用 `PYTHONPATH` 指向仓库根 → **实测无效**：仓库根的 `donkey.egg-info/` 会随之被发现，元数据照样命中（这条实测直接排除了该方案）；
- ❌ **只靠"副本同级没有 `*.egg-info`"** → **实测无效**（已安装的发行版在 site-packages 里仍会被发现）→ 故 MUST 追加 `-S`。

---

## R-11 · 单元测试落点 = 新建 `tests/unit/test_cli_version.py`

**决策**：新增独立单元测试文件，覆盖版本解析的三条分支。

**理由**：
- spec SC-007 明文要求「该回退路径 MUST 有单元测试覆盖」—— 回退分支在 e2e 里可构造（R-10），但**单元层是本 Phase 的主覆盖点**（可直接 monkeypatch 抛 `PackageNotFoundError`，并断言"元数据优先于 `__version__"的不一致分支）；
- 独立文件而非塞进 `tests/unit/test_cli_client.py`：后者是 F001-P1 的既有文件，其 docstring 明确「CLI 层共 3 个测试函数」—— 本 Phase **不动**既有文件（spec FR-034「既有断言逐字未改」的同源要求），新增独立文件零侵入。

**被否决的备选**：
- ❌ 往 `test_cli_client.py` 追加用例 → 改动 F001-P1 的冻结测试文件，与 FR-034 的"既有断言逐字未改"口径相悖；
- ❌ 只靠 e2e 覆盖回退分支 → spec SC-007 明文要求单元覆盖。

---

## R-12 · 宪法修订的**四处**落点（**已落地** · 核对锚点行号）

**决策**（载体：`.specify/memory/constitution.md`）：宪法修订共 **四处**，**已由 Maintainer 于 2026-10-30 前置落地**（宪法 §6.2 第 2 条）；实施期本 Phase 只**核对、不改**（R-19）。下表行号为**修订后**的实际行号（核对锚点）：

| 修订 | 落点 | 核对锚点（修订后行号） |
|---|---|---|
| (a) §4.2.1 新增「元信息命令豁免」小节 | 在 §4.2 的 F 编号表之后、"任何 spec / plan / tasks / 代码 / 文档中出现 F 编号引用必须与上表**字面对齐**。"之后、§4.3 标题之前 | §4.2 的 F 编号表止于**第 241 行**；插入点 = **第 243 行之后**（小节标题在**第 245 行**，正文在**第 247 / 249 行**） |
| (b) §4.3 加括注限定语 | §4.3 首段"**核心原则**"行内的「（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）」 | §4.3 起于**第 251 行**；该句在**第 253 行** |
| (b2) §4.3 的 v1 baseline 句加限定语 | §4.3 的「**v1 baseline**」句末的「**（元信息命令按 §4.2 豁免）**」 | 该句在**第 269 行** |
| (c) 第 5 章新增 [D-20] | ADR 表**末尾**追加一行（编号只增不删，当前最大为 D-19） | 第 5 章起于**第 352 行**；[D-19] 行在**第 376 行**；[D-20] 行在**第 377 行**（表尾） |

**理由**：
- spec FR-036 + H 段要求**逐字落地**（Maintainer 已批准，宪法 §6.2 第 2 条）—— **已由 Maintainer 于 2026-10-30 前置落地**，实施期只核对，MUST NOT 改写措辞；
- ADR 编号**只增不删** → [D-20] 必须是表内**最后一行**（插在中间会破坏"只增"的顺序惯例）；
- **本轮 analyse 修正了原 R-12 的锚点行号错误**（原表把 §4.2 的 F 编号表止点写成"第 243 行"，且整表遗漏了 §4.3 的 v1 baseline 限定语这一处）—— 现行锚点已与仓库实际逐行核对（`grep -n`）。

**被否决的备选**：
- ❌ 在 §4.2 的 F 编号表里加一行"元信息命令" → 那会把"元信息命令"混入"核心功能"表，恰恰是 [D-20] 动机里要避免的语义污染；
- ❌ 把 [D-20] 插在 [D-19] 之前 → 破坏 ADR 表的时序；
- ❌ 实施期再编辑一次宪法（哪怕措辞相同）→ 修订已前置落地，编辑会让 4 处修订变成额外的 diff，且违背 spec FR-036 的「保持其逐字不变」（R-19）。

---

## R-13 · `harness/features/README.md` **逐字未改**；F001-P4 的登记载体 = [D-20] 的影响面条目

**决策**：本 Phase **不**改动 `harness/features/README.md`（§1.5 的"Phase ↔ 子段 1:1"惯例表述、§3 一览总表、§4 详细设计、§12.2 提示词映射表**一律不动**）。

**理由**：
- spec FR-030 / SC-012 / Clarifications Q5：Maintainer 已决定不修订该 README（其非强制），本 Phase 打破该惯例属**有意的例外**，MUST 在 spec 中显式登记（已登记）；
- spec H 段的「登记说明」：[D-20] 的**影响面**条目已指名 `specs/001-donkey-init-workspace/phase-4-cli-version/` → F001-P4 在项目索引中的登记载体即该条；
- 若在 README 里新增 F001-P4 行，就必须同时动 §1.5 的 1:1 表述与 §3.1 的"3 子段"计数 → **构成对被豁免的索引表的修订**，与 D-3 相悖。

**被否决的备选**：
- ❌ 在 README §3.1 加一行 → 触发"3 子段 → 4 Phase / 3 子段"的连锁改写，直接违反 D-3；
- ❌ 新开 README §4.6 章节 → 该章节同样要填"子段"列（无处可填，因本 Phase 无子段）。

---

## R-14 · 过期计数修正的**两处**落点 + 明确不改 P2 冻结快照

**决策**：

| # | 文件 | 现状 | 改为 |
|---|---|---|---|
| 1 | `donkey/cli/cli_client.py` | `init` 子解析器的 `help` 与 `description` **两处**均写「生成模板骨架（**46** 个模板条目）+ 工作区清单。」 | 「生成模板骨架（**54** 个模板条目）+ 工作区清单。」 |
| 2 | `donkey/core/api.py` | `InitResult` docstring 三处计数：`templates_loaded` 写「P2 为 `46`」、`files_created` 写「P2 全新创建为 `40`」、`files_skipped` 写「P2 二次 init 为 `40`」 | 分别改为「`54`」「`48`」「`48`」，并把「P2 为/为」的时代限定语改为当前口径（spec SC-016 要求 MUST NOT 再出现 46 / 40） |

**权威口径来源**：F001-P3 的 `contracts/cli-contract.md`「全新创建 / 二次 init / `--force`」三行计数表（`54 / 48 / 0`、`54 / 0 / 48`、`54 / 47 / 1`）+「与 P2 的差异：P2 是 46/40/0（全新）；P3 的 54 = 46 + 8，文件型 48 = 40 + 8」。

**明确不改**：F001-P2 的三份 `contracts/*.md`（`cli-contract.md` / `library-api.md` / `template-manifest.md`）—— 它们是**该 Phase 的冻结快照**，差额已由 P3 的契约文档显式登记为当前口径；spec FR-037 明文「MUST NOT 改动那三份文档」。

**被否决的备选**：
- ❌ 一并把 P2 的 `contracts/*.md` 改成 54 → 那是回改**已完成 Phase 的冻结交付物**，且 P2 契约文档里「P2 = 46」本就是**历史事实**（P2 当时确实交付 46 条）；
- ❌ 只改 `--help` 不改 docstring → spec FR-037 / SC-016 要求两处同步；
- ❌ 只改一处 `--help`（`help` 或 `description` 二选一）→ 两处字符串相同，漏改一处则 `--help` 与子解析器 usage 互相矛盾。

---

## R-15 · 既有断言兼容性核对（结论：**无需**登记阶段边界改写）

**决策**：本 Phase **不改动** F001-P1 / P2 / P3 的任何测试文件与断言。

**核对证据（实测 grep）**：

| 检索对象 | 结果 |
|---|---|
| `tests/` 下的「46 个模板条目」 | **0 命中** |
| `tests/` 下的 `templates=46` | **0 命中**（P2 / P3 的 e2e 已在 P3 轮改为 `templates=54 created=48 skipped=0`） |
| `tests/` 下对 `--help` / `usage:` 的断言 | 仅 `"usage:" in stderr` 三处（P1 e2e 2 处 + P2 e2e 1 处）—— **不涉及子命令列表** |
| `tests/` 下对子命令列表的断言 | **0 命中**（无断言依赖 `{init}` 的精确形态） |

**理由**：spec FR-034 / SC-009 要求既有三套 verify 脚本保持全绿且断言逐字未改 —— 核对结果表明 R-14 的文案修正**不会使任何既有断言失效**，故**无需**在 spec 中登记阶段边界改写（与 F001-P3 FR-068 的"必须显式改写"形成对照：本 Phase 没有要改的东西）。

**被否决的备选**：
- ❌ 顺手把 P2 / P3 e2e 里的 `templates=54` 改成"从 `pyproject.toml` 读" → 那是 F001-P1 / P2 / P3 的冻结断言，spec FR-034 禁止。

---

## R-16 · e2e 脚本**自包含**（不抽公共模块）

**决策**：`tests/e2e/phase/verify_phase_f001_p4.py` 自带一份 `_resolve_donkey_command()` / `_console_script_package_dir()` 等辅助函数副本。

**理由**：
- **实测**：三套既有脚本（P1 / P2 / P3）**各自**持有一份同名辅助函数，**互不 import** —— 保持"每个 Phase 的验收脚本可独立运行、独立删改"的既有惯例；
- 本 Phase 的解析需求与 P1 / P2 / P3 **完全一致**（控制台脚本优先 + 校验归属当前工作树 + 不可用时回落到 `python -m donkey` + 打印一次显式告警）。

**被否决的备选**：
- ❌ 抽 `tests/e2e/phase/_common.py` → 引入三个既有脚本的**改动**（违反 FR-034 的"既有断言逐字未改"与最小侵入原则），且会让已冻结 Phase 的脚本互相耦合。

---

## R-17 · 性能基线

**决策**：单次 `donkey version` 的耗时上限取 **5 秒**（spec SC-011）。

**理由**：本命令无网络、无文件写入、无工作区读取 —— 实测耗时在**毫秒级**；5 秒是给 CI 冷启动 / 解释器启动留的极宽松余量（P3 的 `donkey init` 因为要落 49 个文件才需要 10 秒）。

**被否决的备选**：
- ❌ 沿用 P3 的 10 秒 → 对一个纯内存命令过松，判据失去意义；
- ❌ 取 1 秒 → 在极慢的 CI 机器上可能假失败，余量不足。

---

## R-18 · 版本一致性判据 = **双比对**（工作树声明值 + 安装分发元数据值）

**决策**：验收脚本 MUST 读取**两个**来源并分别断言 —— ① **工作树声明值** = `pyproject.toml` 的 `version`（MUST 另行断言其当前为 `0.1.0`）；② **安装分发元数据值** = `importlib.metadata.version("donkey")`（**允许**使用标准库 `importlib.metadata`，MUST NOT import `donkey.*` 业务代码 —— FR-033）。**断言规则**：两者相等 → 输出底层取值 MUST == 二者；两者不等（陈旧安装）→ 输出底层取值 MUST == **安装分发元数据值**（FR-018），且 MUST **显式断言**该不等情形、MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段（那会产生假失败）。**清单字段比对的额外前提（陈旧清单形态）**：工作区清单 `donkey_version` 被 F001-P2 FR-021 **锁死**为**当时的**版本，故「输出 vs 清单字段」的比对 MUST 以「**工作树声明值 == 清单字段**」为前提 —— 不成立时 MUST **跳过**该比对（改以分发元数据 / 工作树声明值为准），MUST NOT 断言输出 == 清单字段（假失败）；见 spec Key Entities「常规安装形态 / 陈旧安装形态（判定谓词）」与 Assumptions「版本号 bump 的跨 Phase 联动」。

**理由**：
- spec SC-003 的「期望值的取数口径（双比对）」是本条的权威来源；**R-09 的结论仍然成立**（读工作树声明 + 另行断言其为 `0.1.0`），本条补上的是「输出该等于谁」的那一半 —— 两者互补、不冲突；
- 语义正确性：陈旧安装时用户实际跑的是**装上去的那一份** → 分发元数据才是权威（FR-018）；若仍以工作树声明为唯一期望值就会**假失败**；
- spec FR-013 / SC-003 的「逐字节一致」口径**已限定在常规安装形态下**（安装元数据值 == 工作树声明值）—— 本条给出该限定之外（陈旧安装）的确定行为，消除 MUST 级冲突。

**被否决的备选**：
- ❌ 只断言工作树声明值（单一来源）→ 陈旧安装时假失败（spec SC-003 明文禁止「MUST NOT 因安装形态漂移而产生假失败」）；
- ❌ 两者不等时以工作树声明为准 → 与 FR-018 相反（用户跑的是装上去的那一份）；
- ❌ 两者不等时打印告警 → 污染 stdout / stderr（FR-007 / FR-009）；
- ❌ 静默接受不等情形 → 违反 spec FR-013「该不一致情形 MUST 由验收脚本**显式断言**……MUST NOT 被静默接受」。

---

## R-19 · 宪法修订**前置落地** → 实施期只核对、不改

**决策**：宪法修订（4 处，R-12）**已由 Maintainer 于 2026-10-30 前置落地**；本 Phase 的 **T002 ~ T004** 由『**编辑宪法**』任务改为『**核对 + 自检**』任务 —— 实施期 MUST **保持四处措辞逐字不变**、MUST NOT 再改动 `.specify/memory/constitution.md`。

**理由**：
- spec FR-036（已改为「**已由 Maintainer 于 2026-10-30 前置落地**（4 处）→ 本 Phase MUST **保持其逐字不变**、实施期 MUST NOT 再改动」）+ Clarifications **Session 2026-10-30（analyse 缺陷修复轮）** 的 Q6 / Q8；
- 授权基础必须在实施开始**之前**已成立 —— 否则实现处于"无授权"状态；前置落地直接消除了这一窗口；
- spec MUST NOT 自设宪法例外（FR-031）—— 本 Phase 只**引用**该修订；SC-012 的「四处措辞 MUST 与 spec H 段 (a)/(b)/(b2)/(c) 登记的文本**逐字一致**」核对仍必须执行。

**被否决的备选**：
- ❌ 实施期再编辑一次（哪怕措辞完全相同）→ 会让宪法产生 4 处之外的额外 diff，且违背 FR-036 的「保持其逐字不变」；
- ❌ 把 T002 ~ T004 直接删掉 → **核对 + 自检**（四处措辞逐字一致 / README 逐字未改 / ADR 编号只增不删）仍必须执行（SC-012）。

---

## Phase 0 收尾核对

| 项 | 结论 |
|---|---|
| NEEDS CLARIFICATION 残留 | **0 项** |
| 新增依赖 | **0 个**（运行期仍恰为 1 个 `langgraph-checkpoint-sqlite`；dev 依赖不变） |
| 新增 exit code / Error class | **0 个**（spec FR-029） |
| 既有测试文件改动 | **0 个**（R-15 核对结论） |
| 宪法修订 | **4 处**（R-12），内容逐字取自 spec H 段 (a) / (b) / (b2) / (c)；**已由 Maintainer 于 2026-10-30 前置落地**，实施期只核对（R-19） |
| 落地新增文件 | 2 个（`donkey/core/version.py`、`tests/unit/test_cli_version.py`）+ 1 个验收脚本（`tests/e2e/phase/verify_phase_f001_p4.py`） |
| 实施期改动既有源文件 | **2** 个（`donkey/cli/cli_client.py`、`donkey/core/api.py`）；`.specify/memory/constitution.md` 已在前置修订中落地（R-19） |
