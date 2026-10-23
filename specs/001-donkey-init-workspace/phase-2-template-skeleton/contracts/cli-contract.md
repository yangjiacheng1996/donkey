# 契约：命令行接口（`donkey init`）

**版本**：v1.1（F001-P1 冻结的 v1.0 上追加 P2 的输出增强）
**所有者**：`donkey/cli/cli_client.py`
**上游**：[spec.md](../spec.md) FR-001 ~ FR-004、FR-036、FR-063、FR-068 ~ FR-069；[research.md](../research.md) R-11 / R-12

---

## 1. 命令面（P1 已冻结，本 Phase 不变）

```
donkey init <PATH> [--force]
```

| 参数 | 形态 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `<PATH>` | 位置参数 | 是 | — | workspace 目录路径；绝对或相对均可，相对路径以进程工作目录为解析基准 |
| `--force` | 布尔开关 | 否 | 假 | 强制重置已存在模板文件。**P2 起真正生效**：模板文件被删后重建、sqlite3 模板被删后重建并清空数据 |

**不存在其它参数**（spec FR-003）：v1 **不提供** `--name` 或任何等价的独立命名参数 —— workspace 名称恒取路径末段。

```
$ donkey init --help
usage: donkey init [-h] [--force] path
```

---

## 2. 退出码

| 退出码 | 触发条件 | 输出流向 |
|---|---|---|
| `0` | 成功（模板骨架 + 工作区清单已就位） | 结果摘要 → stdout |
| `1` | 路径 / 输入不合法（父目录不存在、非法字符、根路径、空路径、目标不是目录……）；**参数用法错误**（缺子命令、缺必填参数、未知参数） | 错误信息 → stderr |
| `2` | 权限不足（写位 / 执行位 / 读位缺失） | 错误信息 → stderr |
| `3` | **模板骨架生成失败**（清单损坏 / 结构非法 / 源模板缺失 / 写入失败含磁盘满与权限中途撤销 / sqlite3 结构构造失败 / 上游依赖不可用 / 目标是目录（仅文本类与 sqlite3 类条目）） | 错误信息 → stderr |
| `4` / `5-10` | 本 Phase **不触发** | — |

**语义唯一性**（按**阶段**切分，spec FR-038）：`1` = 输入 / 路径 / 参数用法不合法；`2` = 权限不足（发生在前置校验阶段与工作区根目录创建阶段）；`3` = 模板骨架生成失败（发生在模板骨架渲染阶段与工作区清单写入阶段，含渲染中途权限被撤销、磁盘满）。三者互不复用。

---

## 3. 输出契约

### 3.1 成功（stdout）

**P1 形态（1 行）** —— 本 Phase **不改格式**，仅数值随模板落地而变：

```
[donkey init] workspace=<绝对路径> name=<名称> force=<true|false> templates=<N> created=<N> skipped=<N>
```

| 字段 | P1 取值 | **P2 取值** |
|---|---|---|
| `workspace` | 绝对路径 | 同 |
| `name` | 末段名 | 同 |
| `force` | `true` / `false` | 同 |
| `templates` | `0` | **46**（清单条目总数，含目录条目、含重复条目） |
| `created` | `0` | **40**（文件型条目：37 文本 + 3 sqlite3） |
| `skipped` | `0` | **0**（全新创建）/ **40**（二次 init，无 `--force`） |

### 3.2 强制清空提示行（stdout）—— **P2 新增**

带 `--force` 时，结果摘要**之后**额外输出**一行**显式提示：

```
[donkey init] 警告：memory/ 下的会话历史与会话元数据已被清空（--force 恢复出厂设置）。如需保留请先备份。
```

| 约束 | 说明 | 出处 |
|---|---|---|
| C1 | MUST 与通用摘要**分行**输出 | spec FR-068 |
| C2 | MUST **不**挤占摘要中的路径 / 名称 / 强制标志 / 三个计数字段 | spec FR-068 |
| C3 | MUST 输出到 **stdout**（成功路径提示，非失败信息） | R-11 |
| C4 | MUST **恒定输出**（即使此前不存在 sqlite3 文件 —— 此时亦无数据可清空），故文案 MUST 同时涵盖"已清空 / 已重建"两种情形 | R-11 / Assumptions |
| C5 | **不带** `--force` 时 MUST **不**出现该行（**0 次**） | spec FR-068 / SC-019 |

**测试落点**：e2e 黑盒场景 8 断言该行**存在**；场景 6 断言该行**不出现**（spec FR-059）。

### 3.3 失败（stderr，单行）

**P1 形态**（本 Phase 不改结构）：

```
[donkey init] 失败：<错误类别名>: <错误信息>
```

**错误信息 MUST 含**（spec FR-019 / FR-069）：

| 元素 | 要求 | 模板类失败的示例 |
|---|---|---|
| 可识别的错误标识 | 错误类别名 **或** 具体关键词 | `TemplateGenerationError` + "模板清单损坏" / "模板源缺失" 等 |
| 具体对象 | 涉及的路径 / 源路径 | `/path/to/templates/instruction.md.txt` |
| **一条**用户可执行的下一步 | MUST NOT 只报类别 | "下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。" |

**示例**：

```
[donkey init] 失败：TemplateGenerationError: 模板清单损坏（JSON 解析失败）：/…/templates/manifest.json。下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。
```

```
[donkey init] 失败：TemplateGenerationError: 模板源缺失：/…/templates/providers/openai.toml.txt。下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。
```

---

## 4. 四场景行为契约（AC-3 幂等）

| 场景 | 命令 | 前置状态 | 行为 | exit |
|---|---|---|---|---|
| **1. 全新创建** | `donkey init /tmp/ws` | 目录不存在 | 新建全部目录 + 全部模板文件 + 工作区清单；`created=40, skipped=0, templates=46` | `0` |
| **2. 幂等补齐** | `donkey init /tmp/ws` | 目录存在 | 遍历清单：缺失的补齐（`created` 部分）；已存在的**完全不动**（`skipped`）；用户内容（非清单）**完全不动** | `0` |
| **3. 模板重置** | `donkey init /tmp/ws --force` | 目录存在 | 遍历清单：先删每个模板文件（含 sqlite3 主库 + `-wal` / `-shm`；**目录条目不删任何文件**，其内清单文件由各自条目重建），再建默认内容；用户内容**完全不动**；**输出强制清空提示行** | `0` |
| **4. 放弃重做** | `rm -rf /tmp/ws` + `donkey init /tmp/ws` | 目录被用户删除 | 同场景 1 | `0` |

**场景 2 的"完全不动"含义**：内容的**字节**与**修改时间**均不变 —— 不是"重写了相同内容"。

**场景 3 的作用域**：严格限定在清单条目内。**唯一例外**是 sqlite3 的 `-wal` / `-shm` 附属文件（同一模板的附属产物，R-03）。

---

## 5. 客户端层改动清单（本 Phase）

| # | 改动 | 位置 | spec |
|---|---|---|---|
| 1 | 异常映射表**新增 1 行**：`TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION` | `_EXCEPTION_TO_EXIT_CODE` | FR-036 |
| 2 | 结果摘要**新增 1 行**（`--force` 时）：强制清空提示 | `_run_init` 的打印段 | FR-068 |
| 3 | **更新 `--help` 与子命令说明文案**，使其与 P2 的实际行为一致 —— P1 遗留的"不加载模板清单、不生成模板内容"与"本阶段仅记录并回显，不触发任何删除 / 重置"在 P2 落地后是**错误陈述**，MUST NOT 原样保留（属文案同步，不构成新的客户端行为） | `_build_parser`（init 子命令的 `help` / `description` 与 `--force` 的 `help`） | FR-064 ③ |

**MUST NOT**：引入其它客户端行为变更；直接 import `langchain` / `langgraph` / `sqlite3`（N-04）；感知 `sys.argv` 之外的进程细节。

---

## 6. 双入口一致性

`donkey init`（控制台脚本）与 `python -m donkey init`（模块入口）**MUST** 产生完全相同的退出码与文件系统副作用，
且 stdout / stderr 逐字一致（含 §3.2 的提示行）。解析器 `prog` 已显式设为 `"donkey"`（P1 R-01），保证 usage 提示一致。

---

## End of cli-contract.
