# 快速验证指南：F001-P4 `cli_version` —— `donkey version` 查询版本号

**Phase**: F001-P4 / `cli_version` | **日期**: 2026-10-30
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **契约**: [contracts/](contracts/)

> 本文件是**可执行的验证指南** —— 证明本 Phase 端到端可用。**不含**实现代码、**不含**完整测试套件。
> 判据的权威表述在 spec 的 FR / SC；本文件只给**可手验的步骤**。

---

## 1. 前置条件

| 项 | 要求 |
|---|---|
| Python | 3.11+（`tomllib` 内置，验收脚本用它读 `pyproject.toml`） |
| 依赖 | `pip install -e ".[dev]"`（运行期依赖仍恰为 1 个：`langgraph-checkpoint-sqlite`） |
| 前置 Phase | F001-P1 / P2 / P3 的退出条件全部满足（其三套 verify 脚本必须仍全绿） |
| 宪法修订 | **已由 Maintainer 于 2026-10-30 前置落地（4 处）** —— `§4.2.1` / `§4.3` 第 253 行括注 / `§4.3` 第 269 行 v1 baseline 限定语 / `[D-20]`（本 Phase **只核对、不改**；[contracts/constitution-amendment.md](contracts/constitution-amendment.md)） |

---

## 2. 手动验证（逐条对应 User Story）

### 2.1 一条命令看到版本号（US1 / SC-002 / SC-003）

```bash
cd <repo>
python3 -m donkey version
```

**期望**：stdout **恰好一行**、内容为 `resolve_version()` 的解析结果（**常规安装形态**下 = `v0.1.0`；陈旧安装形态下 = 分发元数据值）；stderr **为空**；退出码 `0`。

```bash
python3 -m donkey version | wc -l          # → 1
python3 -m donkey version | od -c | tail -3 # → 确认行终止符存在、正文前后无空白
echo $?                                     # → 0
```

**双比对的两个输入**（SC-003 的期望值取数口径 —— [research.md](../research.md) R-18）：

```bash
# ① 工作树声明值
python3 -c "import tomllib,pathlib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['version'])"
# ② 安装分发元数据值（标准库；MUST NOT import donkey.* 业务代码 —— FR-033）
python3 -c "import importlib.metadata as m; print(m.version('donkey'))"
```

**期望**：两个值**相等** → 输出底层取值 MUST == 二者；两个值**不等**（陈旧安装）→ 输出底层取值 MUST == **安装分发元数据值**（FR-018），且该不等情形 MUST **显式断言**、MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段（那会产生假失败）。

### 2.2 只有一个版本值（US2 / SC-002）

```bash
python3 -m donkey version | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | wc -l   # → 1
```

**期望**：恰好 **1** 个版本值（不得出现第二个版本值、客户端版本或节点级信息）。

### 2.3 图未建时也有确定答案（US3 / SC-003）

```bash
python3 -m donkey version
```

**期望**：`resolve_version()` 的解析结果（**常规安装形态**下 = `v0.1.0`）—— MUST NOT 是 `unknown` / `dev` / `v0.0.0` 一类的值；输出中**不含**节点清单或节点级版本号。

### 2.4 两条入口等价（US4 / SC-004）

```bash
# 有控制台脚本时
donkey version > /tmp/a.out 2>/tmp/a.err; echo "rc=$?"
python3 -m donkey version > /tmp/b.out 2>/tmp/b.err; echo "rc=$?"

diff /tmp/a.out /tmp/b.out && echo "stdout 一致"
diff /tmp/a.err /tmp/b.err && echo "stderr 一致"
```

**期望**：两条入口的 stdout **逐字节相同**、stderr 均为空、退出码相同。
> **环境注**：若本机未把 donkey 装进 site-packages（`pip show donkey` 报 not found），控制台脚本可能不存在 → 验收脚本会自动回落到 `python -m donkey` 并打印**一次显式告警**（沿用 P1 / P2 / P3 的既有约定）；该告警 MUST 出现在 verify 脚本的 **stderr** 中（**非静默跳过**），此时只断言模块入口一侧（spec SC-004 的降级条款）。

### 2.5 用错了报 exit 1（US5 / SC-006）

```bash
for arg in "--bogus" "web" "extra"; do
  python3 -m donkey version "$arg" >/tmp/o 2>/tmp/e; echo "$arg → rc=$?"
done
```

**期望**：三者退出码**均为 `1`**（**不是 `2`**）；stdout 为空；stderr 含用法提示。

```bash
python3 -m donkey version --help >/dev/null 2>&1; echo $?   # → 0（帮助请求不是用法错误）
python3 -m donkey --version >/dev/null 2>&1; echo $?         # → 1（顶层无 --version 标志）
```

### 2.6 装没装都给确定版本（US6 / SC-007）

```bash
# 构造一个"取不到分发元数据"的环境：复制包目录（副本同级没有 *.egg-info）
# + 用 python -S 屏蔽 site-packages（否则已安装 donkey 的环境里仍会被发现）
rm -rf /tmp/iso && mkdir -p /tmp/iso
cp -r <repo>/donkey /tmp/iso/donkey
cd /tmp/iso
python3 -S -c "import importlib.metadata as md; md.version('donkey')" 2>&1 | tail -1
python3 -S -m donkey version; echo "rc=$?"
```

**期望**：第一行出现 `PackageNotFoundError`（证明分发元数据**确实不可得**）；第二段输出**仍是** `v0.1.0`、退出码 **`0`**。

> **关键 `-S` 不可省**：仅靠"副本同级没有 `*.egg-info`"**不足以**复现 —— **实测**：已安装 donkey 的环境（如 CI 的 `pip install -e ".[dev]"`）里 site-packages 的 `donkey-*.dist-info` 仍会被 `importlib.metadata` 发现（副本内照样返回 `0.1.0`）→ 回退分支**根本没被覆盖**。`-S`（屏蔽 site-packages）使"元数据不可得"**与环境无关**。
> **`-S` 不影响可用性**：实测 `-S` 下 `donkey` 的导入链**完整**（`langgraph` **不**进入 `sys.modules`，纯标准库）→ 无需任何第三方依赖。
> **反例（勿用）**：`PYTHONPATH=<repo>` **无效** —— 仓库根的 `donkey.egg-info/` 会随之被发现，元数据照样命中。

### 2.7 查询不动我的东西（US7 / SC-005）

```bash
mkdir -p /tmp/fs-before && cd /tmp/fs-before
find . | sort > /tmp/tree-before.txt
python3 -m donkey version >/dev/null
find . | sort > /tmp/tree-after.txt
diff /tmp/tree-before.txt /tmp/tree-after.txt && echo "目录树零变化"
```

**期望**：目录树**零变化**（文件数 / 目录数 / 内容全部不变）；在工作区**不存在**或**损坏**（manifest 缺失）的目录下同样成功。

---

## 3. 自动化验证（"Phase 完成" 的硬性证据）

```bash
# ① 前置套件（必须全绿 —— FR-034 / SC-009）
pytest tests/e2e/phase/verify_phase_f001_p1.py -v
pytest tests/e2e/phase/verify_phase_f001_p2.py -v
pytest tests/e2e/phase/verify_phase_f001_p3.py -v
pytest tests/unit/test_init_workspace.py -v
pytest tests/unit/test_template_skeleton.py -v
pytest tests/unit/test_builtin_tools.py -v
pytest tests/integration/test_init_to_load.py -v   # P3 既有 —— 必须仍全绿（与 tasks T006 的基线一致）

# ② 本 Phase 套件
pytest tests/unit/test_cli_version.py -v          # 版本解析三分支 + 输出形态
pytest tests/e2e/phase/verify_phase_f001_p4.py -v # 7 个断言 ↔ 7 个 User Story

# ③ 静态检查
ruff check donkey/ tests/
mypy donkey/ tests/

# ④ 覆盖率（独立命令，MUST NOT 写进 addopts）
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80

# ⑤ 完整套件
pytest tests/ -v
```

---

## 4. 门禁冒烟（分层与永不使用清单）

```bash
# 判据范围 = 本 Phase 新增 / 改动的两个文件（spec SC-010）
# —— 仓库中**既有**的 donkey/core/workspace/sqlite3_templates.py 对 sqlite3 的导入属 F001-P2 冻结产物，不计入本条
# 核心层新模块 MUST NOT 引入框架 / sqlite3 / argparse
grep -nE "import (langchain|langgraph|sqlite3|argparse)" donkey/core/version.py   # → 0 命中
grep -nE "import (langchain|langgraph|sqlite3)" donkey/cli/cli_client.py          # → 0 命中

# 全仓：donkey 自有代码路径 MUST NOT 出现可观测性后端
grep -rnE "langsmith|observability" donkey/                                        # → 0 命中

# 客户端层 MUST NOT 出现第二个版本定义点（FR-019）
# —— "版本定义点"指**供 version 命令解析用的**取值来源；仓库里另有两处
#    "0.1.0" 字面量属于**别的用途**，MUST NOT 被误判为违例：
#      donkey/__init__.py            → 回退源本身（FR-017 / FR-026）
#      donkey/core/workspace/manifest.py → 工作区清单的 donkey_version 存储值（F001-P2 FR-021 锁死）
grep -n "0\.1\.0" donkey/core/version.py        # → 0 命中（取值 MUST 来自动态解析，不得硬编码）
grep -n "0\.1\.0" donkey/cli/cli_client.py      # → 0 命中（客户端层 MUST NOT 复制版本值）
grep -rn "0\.1\.0" donkey/ --include=*.py       # → 恰 2 处命中（__init__.py + manifest.py），且仅此两处
```

---

## 5. 宪法修订交付自检（FR-036 / SC-012）

```bash
grep -n "元信息命令" .specify/memory/constitution.md            # §4.2.1 豁免小节 / §4.3 括注 / §4.3 v1 baseline
grep -n "核心功能的" .specify/memory/constitution.md             # §4.3 第 253 行括注
grep -n "元信息命令按 §4.2 豁免" .specify/memory/constitution.md # §4.3 第 269 行 v1 baseline 限定语
grep -n "\[D-20\]" .specify/memory/constitution.md               # 第 5 章 [D-20]

git diff --stat harness/features/README.md                      # MUST 为空（逐字未改）

# 宪法修订的四处变更：以**基线 commit**（实施开始前记录的 HEAD）为基准
# —— MUST NOT 用裸 `git diff`（若修订已被单独提交，裸 diff 会为空而误判）
git diff --stat <基线commit> -- .specify/memory/constitution.md  # MUST 只有四处变更（已前置落地，本 Phase 只核对）
```

> **四处措辞 MUST 与 spec H 段 (a) / (b) / (b2) / (c) 登记的文本逐字一致**（一字不差）—— 逐条比对见 [contracts/constitution-amendment.md](contracts/constitution-amendment.md) §4 的检查清单第 8 项。
> **比对基准（(b) 处）**：H 段 (b) 登记的是该括注的**内层文本**；宪法第 253 行的**外层圆括号**属句子的一部分 → MUST NOT 因外层圆括号判 FAIL（完整句见 contracts/constitution-amendment.md §2）。

补丁级文本见 [contracts/constitution-amendment.md](contracts/constitution-amendment.md)。

---

## 6. 过期计数修正自检（FR-037 / SC-016）

```bash
python3 -m donkey init --help | grep -c "54 个模板条目"    # → 1（且 MUST NOT 出现 "46 个模板条目"）
grep -nE "\b(46|40)\b" donkey/core/api.py                   # → 0 命中（InitResult docstring 已同步为 54 / 48 / 48）
```

> **不改** F001-P2 的三份冻结 `contracts/*.md` —— 它们是该 Phase 的历史快照（差额已由 F001-P3 的契约文档登记为当前口径）。

---

## 7. 排查表

| 症状 | 可能原因 | 处理 |
|---|---|---|
| `donkey version` 报 "invalid choice: 'version'" | 子命令未注册 | 检查 `cli_client.py` 是否 `add_parser("version", ...)` |
| 输出带 `[donkey version] ` 前缀或 `version=` 字段 | 误用了 `donkey init` 的摘要形态 | FR-007 / FR-010：MUST 是**裸版本值** |
| 误用退出码是 `2` | 子解析器未继承 `DonkeyArgumentParser` | `add_parser` 以 `type(self)` 作 `parser_class` → 覆写自动传播（P1 research R-01） |
| 版本值取到旧版本号 | 安装的发行版陈旧 | FR-018：元数据优先即"实际安装的那一份"；验收脚本按**双比对**取期望值（工作树声明值 + `importlib.metadata.version("donkey")`）—— 不等时以**元数据值**为期望值并显式断言该情形（SC-003） |
| `python3 -m donkey version` 报 `No module named donkey` | 未安装 / 不在仓库根 | `pip install -e .` 或 `cd <repo>`；**验收脚本**用工作树内的控制台脚本或回落到模块入口 |
| 2.6 的副本法没触发 `PackageNotFoundError` | 副本同级仍有 `*.egg-info` | 副本 MUST 只含 `donkey/` 包目录本身 |
| 既有 verify 脚本变红 | 本 Phase 动了既有文件 | FR-034：既有测试文件**一律不动**；R-15 已核对无断言依赖过期文案 |

---

## 8. 判据索引

| 判据 | 验证步骤 |
|---|---|
| SC-001（7 个断言全绿） | §3 ② |
| SC-002 / SC-003（输出形态与取值；SC-003 含**双比对**口径） | §2.1 / §2.2 / §2.3 |
| SC-004（双入口等价） | §2.4 |
| SC-005（零副作用） | §2.7 |
| SC-006（用法错误 → 1） | §2.5 |
| SC-007（回退路径） | §2.6 + §3 ② 的单元层 |
| SC-008（退出码零增量） | §4 门禁 + [contracts/exit-codes.md](contracts/exit-codes.md) §2 |
| SC-009（既有套件全绿） | §3 ① |
| SC-010（静态检查零 error / 零框架导入） | §3 ③ + §4 |
| SC-011（≤ 5 秒） | 验收脚本逐场景计时 |
| SC-012（宪法**四处** + README 未改） | §5 |
| SC-013（`--help` 可发现） | `python3 -m donkey --help`（子命令列表含 `version`） |
| SC-014（顶层无 `--version`） | §2.5 |
| SC-015（确定性） | §2.1 的两次执行比对 |
| SC-016（过期计数） | §6 |
