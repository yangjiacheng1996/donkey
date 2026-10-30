# 契约：版本取值来源（`donkey version`）

**版本**：v1（F001-P4 冻结）
**所有者**：`donkey/core/version.py`（解析）+ `donkey/cli/cli_client.py`（呈现）
**上游**：`spec.md` FR-012 ~ FR-021；Clarifications Q2 / Q3；[research.md](../research.md) R-01 ~ R-05

---

## 1. 术语与两值口径

| 术语 | 定义 | 当前取值 | 形态 |
|---|---|---|---|
| **底层取值** | 不带前缀的版本号本体 | `0.1.0` | MUST 与 `pyproject.toml` 的 `version`、包内 `__version__`、工作区清单 `donkey_version` 字段**逐字节一致** |
| **展示值** | stdout 输出的那个字符串 | `v0.1.0` | = `"v" + 底层取值`（`v` 是**显示前缀**，不是版本号的一部分） |
| **软件功能版本** | donkey 的**唯一**版本号 | —— | **图版本 ≡ 软件版本 ≡ 包 / 发布版本**（三者 MUST 是同一个数） |
| **一致性判据** | 底层取值与 `pyproject.toml` / `__version__` / 清单 `donkey_version` 的比对口径 | —— | **常规安装形态**下**逐字节一致**；**陈旧安装形态**下以**分发元数据**为准（FR-018），此时**不**逐字节一致（spec FR-013 / SC-003 已限定） |

**两种记法的唯一合法用途**：用户拿 `donkey version` 的输出**去掉 `v` 前缀**后，可与工作区清单的 `donkey_version` 字段直接逐字节比对（迁移判定的依据，宪法 D-03）。

> **口径优先级**：本表的「**一致性判据**」行是**规范性**口径 —— 「逐字节一致」MUST **仅在常规安装形态下**成立（安装元数据值 == 工作树声明值）；陈旧安装形态下以**分发元数据**为准（FR-018），此时输出与工作树声明值 / 清单 `donkey_version` 字段**不**逐字节一致（spec FR-013 / SC-003 已限定；见 [research.md](../research.md) R-18）。

---

## 2. 取值来源与优先级（唯一解析序）

```text
① importlib.metadata.version("donkey")        ← 优先
      │  成功
      ├──▶ 返回元数据版本
      │
      │  抛 PackageNotFoundError
      ▼
② donkey.__version__                          ← 回退
```

| # | 来源 | 何时命中 | 优先级 | 依据 |
|---|---|---|---|---|
| ① | **安装分发元数据**（标准库 `importlib.metadata`，发行版名 `donkey`） | 发行版已安装（常规 `pip install` / `pip install -e .`） | **高** | FR-016（与 F001-P2 FR-021「将来若动态化 MUST 使用包元数据查询方式」同口径） |
| ② | **包自身的 `__version__` 常量** | 分发元数据**不可得**：包未安装 / 非标准安装 / 从源码检出直接运行 | **低**（仅在 ① 失败时） | FR-017 |

**MUST NOT** 读取 `pyproject.toml`（构建期文件，运行期不可靠）—— FR-016。

**MUST NOT** 读取任何环境变量来决定取值 —— FR-011（确定性）。

---

## 3. 三条分支的精确行为

| 分支 | 条件 | 行为 | MUST NOT | 依据 |
|---|---|---|---|---|
| **B-1 命中** | 元数据可读 | 取元数据版本 | —— | FR-016 |
| **B-2 不可得** | 抛 `importlib.metadata.PackageNotFoundError` | 回退到 `donkey.__version__` | MUST NOT 抛异常 / MUST NOT 使命令失败 / MUST NOT 输出空值 | FR-017 |
| **B-3 不一致** | 元数据版本 ≠ `donkey.__version__` | **以元数据为准**（它代表用户实际安装的那一份） | MUST NOT 报错 / MUST NOT 告警（告警会污染 stdout 或 stderr，违反 FR-007 / FR-009） | FR-018 |

> **异常捕获范围**：MUST **只**捕获 `importlib.metadata.PackageNotFoundError`；MUST NOT 用宽泛的 `except Exception` 吞掉未分类错误（沿用 F001-P1 契约 M-03 的口径）。

---

## 4. 公开函数面

核心层模块 `donkey/core/version.py` MUST 暴露**两个**纯函数：

| 函数 | 签名 | 返回 | 副作用 |
|---|---|---|---|
| `resolve_version()` | `() -> str` | **底层取值**（如 `"0.1.0"`） | **无**（纯查询，不打印、不退出、不写文件） |
| `version_string()` | `() -> str` | **展示值**（如 `"v0.1.0"`） = `"v" + resolve_version()` | **无** |

**约束**：
- 两者 MUST 是**纯函数**（无 IO 写入、无打印、无退出）—— 宪法 N-05（核心层 MUST NOT 感知退出码 / 打印 / 退出进程）；
- 两者 MUST NOT 读取环境变量；
- `version_string()` MUST NOT 被实现为在客户端层拼接 —— 前缀逻辑**单点收敛**，三端将来复用同一函数（否则同一值会出现 `0.1.0` 与 `v0.1.0` 两种记法）；
- 本模块 MUST **NOT** 是 `donkey.core.api` 的对外库 API（spec FR-020 末句 / 宪法 §4.2 修订后豁免条款的边界之一）。

---

## 5. 唯一来源约束

| 约束 | 判据 | 依据 |
|---|---|---|
| 运行期来源数 = **1** | MUST NOT 存在第二个**供 `version` 命令解析用的**版本定义点（尤其 MUST NOT 另立一个"图版本"常量）。**注**：仓库里另有两处 `0.1.0` 字面量属**别的用途**，**不**是版本定义点 —— `donkey/__init__.py` 的 `__version__`（**就是**回退源本身，FR-017）与 `donkey/core/workspace/manifest.py` 的 `_DONKEY_VERSION`（工作区清单的**存储值**，F001-P2 FR-021 锁死、MUST NOT 改动，FR-026） | FR-019 |
| 解析落点 = **核心层** | MUST NOT 落在客户端层（`donkey/cli/`）—— 否则 F004-P7 建图时将被迫改客户端 | FR-020 |
| `donkey/__init__.py` **不改动** | 其 `__version__ = "0.1.0"` 是**回退源**，MUST NOT 被改动 | FR-026 |
| `pyproject.toml` 的版本号**不改动** | —— | FR-026 |
| 工作区清单的 `donkey_version` 硬编码值**不改动** | F001-P2 FR-021 锁死 | FR-026 |

> **未来一致性（登记约定 · 当前不是 MUST）**：主图建成（F004-P7）后，图结构变化触发宪法 §4.5 的 `x+1` 时，**宜**伴随软件版本同步递增 —— 因为二者是**同一个数**（FR-012），不存在两处各自维护的定义点。该联动**当前不是 MUST**：它 MUST 由 **F004-P7 在其 spec 中显式登记并取得 Maintainer 批准**后才成立；本 Phase MUST NOT 把它写成对后续 Phase 的强制约束（spec Edge Cases「版本取值与来源类」）。

---

## 6. §4.5 三分量读法（Clarifications Q3）

展示值 `v0.1.0` 的三个分量 MUST **严格按宪法 §4.5 的字面定义**读，MUST NOT 另作解释：

| 分量 | §4.5 定义 | 本 Phase 读值 | 是否暴露节点级信息 |
|---|---|---|---|
| `x` | 后端 LangGraph 图版本 | `0` | —— |
| `y` | 该图版本内各节点与中间件的 id | `1` | **否** |
| `z` | 该节点的修改次数 | `0` | **否** |

本命令 MUST **不输出节点清单**、MUST NOT 输出任何节点的**独立**版本号（FR-015 / FR-024）—— 节点要到 F004-P7 才存在。

---

## 7. 验收要点（对应 SC）

| 判据 | 测法 | 依据 |
|---|---|---|
| 展示值形态 | 匹配 `^v\d+\.\d+\.\d+$` | SC-003 |
| 底层取值与清单字段一致 | 去掉 `v` 后与工作区清单 `donkey_version` 字段逐字节相等 | SC-003 |
| 当前值 | `v0.1.0`，且工作树声明值（`pyproject.toml` 的 `version`）= `0.1.0` | SC-003 |
| 回退路径 | 把 `donkey/` **包目录**复制到临时目录（副本同级无 `*.egg-info`）**并以 `python -S` 屏蔽 site-packages** → `importlib.metadata` 抛 `PackageNotFoundError` → 输出仍为 `v0.1.0`、退出码 `0`。**`-S` 不可省**：已安装 donkey 的环境里 site-packages 的 `dist-info` 仍会被发现（实测），仅靠"副本同级无 `*.egg-info`" 覆盖不到回退分支 | SC-007 / FR-017 |
| 回退路径的单元覆盖 | 单元层 MUST 有用例覆盖"元数据不可得"与"两者不一致"两条分支 | SC-007 |
| 期望值取数 | **双比对**口径：验收脚本 MUST 读取**两个**来源并分别断言 —— ① **工作树声明值** = `pyproject.toml` 的 `version`（MUST 另行断言其当前为 `0.1.0`）；② **安装分发元数据值** = `importlib.metadata.version("donkey")`（**允许**使用标准库 `importlib.metadata`，MUST NOT import `donkey.*` 业务代码 —— FR-033）。**两者相等** → 输出底层取值 MUST == 二者；**两者不等**（陈旧安装）→ 输出底层取值 MUST == **安装分发元数据值**（FR-018），且 MUST **显式断言**该不等情形、MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段（那会产生假失败）。MUST NOT 因安装形态漂移而产生**假失败** | SC-003（[research.md](../research.md) R-18） |
