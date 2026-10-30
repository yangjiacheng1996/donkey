# 契约：命令行接口（`donkey version`）

**版本**：v1（F001-P4 冻结）
**所有者**：`donkey/cli/cli_client.py`
**上游**：`spec.md` FR-001 ~ FR-011、FR-028 ~ FR-030、FR-038；Clarifications Q2 / Q4 / Q5

---

## 1. 命令面

```
donkey version
```

| 参数 | 形态 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| —— | —— | —— | —— | **无任何参数**：无位置参数、无可选开关 |

**不存在其它参数**（spec FR-001）：MUST NOT 提供 `--json` / `--short` / `--client` 等任何开关；MUST NOT 提供位置参数（`donkey version web` MUST 被拒绝而非被解释为"指定客户端"）。

`--help` / `-h` 由参数解析器自动提供（spec FR-004）—— 属**帮助请求**，**不**是用法错误 → 退出码 `0`。

**顶层解析器不提供 `--version`**（spec FR-038 / Clarifications Q4）：

```text
$ donkey --version
usage: donkey [-h] {init,version} ...
donkey: error: the following arguments are required: command
$ echo $?
1
```

> **实际报错为「the following arguments are required: command」** —— `add_subparsers(dest="command", required=True)` 的必填校验**先于**未识别参数检查触发（故报错措辞不是"unrecognized arguments"）。判据只取**退出码 == 1 且 stdout 不含任何版本号**，**MUST NOT 依赖具体报错措辞**（spec FR-038 / SC-014）。

版本查询的**唯一入口**是 `version` 子命令。

---

## 2. 退出码

| 退出码 | 触发条件 | 输出流向 |
|---|---|---|
| `0` | 成功（版本值已解析并输出） | 版本值 → stdout |
| `1` | **参数用法错误**（未知开关 / 多余位置参数 / 缺子命令） | 错误信息 + 用法提示 → stderr |
| `2-10` / `11+` | 本 Phase **不触发** | —— |

**语义唯一性**：本命令**不占用任何 exit code 子段**（spec FR-029 / D-3）—— 只使用宪法 §4.4 里**早已存在**的两个码值：`0`（"全子命令"共用段）与 `1`（F001 段位内、承载参数用法错误的既有口径，源自 F001-P1 FR-018）。**MUST NOT** 使用参数解析器的默认失败码 `2`（`2` 在 F001 段位里是"权限不足"）。

详见 [exit-codes.md](exit-codes.md)。

---

## 3. 输出契约

### 3.1 成功（stdout，恰好一行）

```text
v0.1.0
```

| 约束 | 判据 | 依据 |
|---|---|---|
| 行数 | **恰好 1 行** | FR-007 |
| 行内容 | **去掉行终止符后** = 展示值（当前 `v0.1.0`） | FR-007 |
| 前缀 / 字段名 | **无** —— MUST NOT 带 `[donkey version]` 一类前缀，MUST NOT 带 `key=value` 字段名 | FR-007 / FR-010 |
| 空白 | MUST NOT 有前导 / 尾随空白 | FR-007 |
| 版本值个数 | **恰好 1 个** —— MUST NOT 出现第二个版本值 | FR-008 |
| 确定性 | 同一条命令两次执行 → stdout **逐字节相同** | FR-011 |
| 一致性 | **常规安装形态**下底层取值与 `pyproject.toml` / `__version__` / 清单 `donkey_version` **逐字节一致**；**陈旧安装形态**下以**分发元数据**为准（FR-018），此时**不**逐字节一致（spec FR-013 / SC-003 已限定） | FR-013 / FR-018 / SC-003 |
| stderr | **为空** | FR-009 |

> **一致性口径**：上表「一致性」行是**规范性**口径 —— 「逐字节一致」MUST **仅在常规安装形态下**成立；陈旧安装形态下以**分发元数据**为准（FR-018）（[version-contract.md](version-contract.md) §1「一致性判据」行 / [research.md](../research.md) R-18）。

**形态说明**：本命令是**元信息命令**，其 stdout 是**裸版本值**，**有意不同**于 `donkey init` 的「单行 `key=value` 摘要」（spec FR-010）—— 目的是让 `V=$(donkey version)` 直接可用。

**行终止符**：判据一律以「**去掉行终止符后**的正文」为准 —— 跨平台的 `\n` / `\r\n` 差异不构成本命令的差异（FR-007）。

### 3.2 失败（stderr）

```text
usage: donkey version [-h]
donkey version: error: unrecognized arguments: --bogus
```

错误信息 MUST 写 stderr、含**用法提示**（契约 M-04 / M-05）；stdout MUST 为空。

---

## 4. 行为契约

| # | 规则 | 依据 |
|---|---|---|
| C-01 | 版本值 MUST 恒为**非空**且可被 `^v\d+\.\d+\.\d+$` 解析 | FR-013 / FR-014 |
| C-02 | 底层取值 MUST 与 `pyproject.toml` 的 `version`、包内 `__version__`、工作区清单 `donkey_version` 字段**逐字节一致** | FR-013 |
| C-03 | MUST **只读** —— 不创建 / 修改 / 删除任何文件，不读取任何工作区，不要求当前目录存在工作区 | FR-022 |
| C-04 | MUST NOT 接受任何**客户端参数**；客户端版本由 `donkey web version` / `donkey gui version` 各自暴露 | FR-005 |
| C-05 | MUST NOT 输出**节点清单**或任何节点的**独立**版本号 | FR-015 |
| C-06 | 两条入口（`donkey` / `python -m donkey`）MUST 产生**完全相同**的退出码与输出 | FR-006 |
| C-07 | MUST NOT 接受环境变量来决定输出（MUST NOT 受 `DONKEY_VERSION` 之类变量影响） | FR-011（确定性） |
| C-08 | MUST NOT 在 stdout / stderr 输出任何路径、主机名、进程号 | FR-008 / FR-011 |

---

## 5. 入口点

| 入口 | 形式 | 要求 |
|---|---|---|
| 控制台脚本 | `donkey version` | MUST 存在（`[project.scripts]`） |
| 模块入口 | `python -m donkey version` | MUST 存在，与控制台脚本行为**完全一致** |

两条入口 MUST 产生**完全相同的退出码与输出**（spec FR-006 / SC-004）。

> **验收注意**：控制台脚本解析到的工作树归属校验与「不可用时回落到 `python -m donkey`」的约定，沿用 F001-P1 / P2 / P3 三套验收脚本的既有实现（R-16）。

---

## 6. 调用示例

```bash
# 成功
$ donkey version
v0.1.0
$ echo $?
0

# 参数用法错误（退出码 1，不是 2）
$ donkey version --json
usage: donkey version [-h]
donkey version: error: unrecognized arguments: --json
$ echo $?
1

# 客户端参数不被接受
$ donkey version web
usage: donkey version [-h]
donkey version: error: unrecognized arguments: web
$ echo $?
1

# 顶层无 --version 标志
$ donkey --version
usage: donkey [-h] {init,version} ...
donkey: error: the following arguments are required: command
$ echo $?
1

# 帮助请求不是用法错误
$ donkey version --help
usage: donkey version [-h]

显示 donkey 版本号。

options:
  -h, --help  show this help message and exit
$ echo $?
0
```

---

## 7. 范围外登记（只登记、不实现）

| 事项 | 归属 | 本 Phase 的处置 |
|---|---|---|
| `donkey web version` | **F005** | **只登记** —— MUST NOT 实现任何代码或**解析器占位** |
| `donkey gui version` | **F006** | 同上 |
| 节点级版本号（逐节点的 `vx.y.z`） | **F004-P7** | **不实现、不展示** |
| 工作区清单 `donkey_version` 与当前运行时版本的对比 / 迁移提示 | **F002 `donkey load`** | **不做** |
| workspace 格式版本（整数 `1`） | —— | **不暴露** |

> **客户端三端对等（宪法 N-11 / §2.8）**：本 Phase 只在 cli 端提供版本入口；web / gui 端的版本入口由 F005 / F006 各自补齐 —— 属**已登记的前序缺口**，MUST NOT 被理解为"三端已对等"。
