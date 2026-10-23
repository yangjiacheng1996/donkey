# 数据模型（F001-P3 `builtin_tools`）

**输入**：[spec.md](spec.md) FR-001 ~ FR-105 / SC-001 ~ SC-024
**决策依据**：[research.md](research.md) R-01 ~ R-20
**读者**：实现者（`/speckit.implement`）+ 评审者

> 本文件描述**实体、字段、关系、状态机与计数口径**。函数签名与返回形状见 [contracts/tool-contracts.md](contracts/tool-contracts.md)；变更记录的字段集见 [contracts/change-record-contract.md](contracts/change-record-contract.md)。

---

## 1. 实体总览

```text
┌─ 模板清单（安装包内 · 54 条）─────────────────────────────┐
│  entries[]: { path, format }                             │
│    └─ path → 源文件 templates/<path>.txt（45 个文本源）  │
└──────────────────────────┬───────────────────────────────┘
                           │ 渲染（init_workspace_inner 步骤 ④）
                           ▼
┌─ 工作区（用户可见 · 材料层）──────────────────────────────┐
│                                                            │
│  tools/                                                     │
│   ├── __init__.py      0 个 @tool                          │
│   ├── changes.py       0 个 @tool ★ 变更记录契约库         │
│   ├── filesystem.py    7 个 @tool                           │
│   ├── commandline.py   1 个 @tool                           │
│   ├── webfetch.py      1 个 @tool                           │
│   ├── README.md        规范文档                             │
│   └── (用户自写 *.py —— 清单外，--force 也不动)             │
│                                                            │
│  skills/example/                                           │
│   ├── SKILL.md         Level 1 frontmatter + Level 2 正文  │
│   ├── reference/example.md    Level 3                       │
│   ├── scripts/example.py      Level 3（含 __main__ 入口块） │
│   └── templates/example.md    Level 3                       │
└────────────────────────────────────────────────────────────┘
```

**★ 唯一的"共享状态"是 `tools/changes.py`** —— 它是全工作区唯一的变更记录产地（spec FR-012(c)）。
**Skill 第三层演示脚本的授权来源**：宪法 §6.3 **例外 E-02** + §5 章 **[D-19]**（N-01 的边界澄清："Python 入口文件"指**智能体入口**）—— 该脚本含 `__main__` 入口块，但**不属**"智能体入口"；spec FR-050 MUST **引用**该例外，MUST NOT 自设豁免（2026-10-23 定点修订轮已改写为引用口径）。

---

## 2. 变更记录（Change Record）

**契约版本**：`CHANGE_RECORD_VERSION = 1`（**冻结**；只在破坏性变更时递增 —— spec FR-003）

### 2.1 必现基线字段（12 个，任何动作下全部存在）

| 字段 | 类型 | 含义 | 取值约束 |
|---|---|---|---|
| `version` | int | 契约版本 | 恒为 `1` |
| `action` | str | 变更动作 | `create` / `update` / `delete` / `copy` / `move` |
| `path` | str | 变更目标的**绝对**路径 | — |
| `rel_path` | str | 相对工作区根的 POSIX 路径 | 工作区之外 → 回退为绝对路径（不抛异常） |
| `previous_exists` | bool | 变更前文件是否存在 | — |
| `previous_size` | int | 变更前字节数 | 不存在 = `0` |
| `previous_hash` | str \| None | 变更前内容指纹 | 格式 `sha256:<hex>`；不存在 = `None`（**MUST NOT 用空串** —— spec FR-004） |
| `new_size` | int | 变更后字节数 | 删除后 = `0` |
| `new_hash` | str \| None | 变更后内容指纹 | 格式 `sha256:<hex>`；删除后 = `None`（**MUST NOT 用空串** —— spec FR-004） |
| `unified_diff` | str | 标准统一差异文本 | 头为 `a/<rel_path>` / `b/<rel_path>`；超 64 KiB 截断 |
| `diff_truncated` | bool | 差异是否被截断 | — |
| `applied` | bool | 是否真的落盘 | 预览模式恒为 `false` |

### 2.2 条件字段（4 个）

| 字段 | 出现条件 | 语义 |
|---|---|---|
| `src` | `action ∈ {copy, move}` | 源路径（绝对） |
| `src_rel_path` | `action ∈ {copy, move}` | 源路径（工作区相对 POSIX） |
| `previous_content` | `include_previous=True` **且** 旧正文存在 **且** ≤ 256 KiB | 旧正文全文（回滚用） |
| `previous_content_truncated` | `include_previous=True` **且** 旧正文存在 **且** > 256 KiB | 旧正文被省略（此时**不**出现 `previous_content`） |

> **已知口径缺口**：删除**目录**时旧正文不存在 → `include_previous=True` 也不出现任何旧正文字段。改它会给基线 12 字段加第 13 个必现字段 → **违反只增不改**，故保持现状（spec Deferred 项）。

### 2.3 字段与动作的关系矩阵

| 动作 | 旧字节 | 新字节 | 额外字段 |
|---|---|---|---|
| `create` | `None` | `bytes` | — |
| `update` | `bytes` | `bytes` | — |
| `delete`（文件） | `bytes` | `None` | 可选 `previous_content` |
| `delete`（目录） | `None` | `None` | —（目录粒度记录） |
| `copy` | 目标旧字节 | 源字节 | `src` / `src_rel_path` |
| `move` | 目标旧字节 | 源字节 | `src` / `src_rel_path` |

### 2.4 冻结常量

| 常量 | 值 | 作用 |
|---|---|---|
| `CHANGE_RECORD_VERSION` | `1` | 版本分派依据 |
| `MAX_DIFF_BYTES` | `64 KiB` | 单条差异文本上限 |
| `MAX_PREVIOUS_BYTES` | `256 KiB` | 可附带旧正文的上限 |

---

## 3. 统一输出上限（一组常量，两侧共用）

| 常量 | 值 | 读取侧 | 命令输出侧 |
|---|---|---|---|
| 行数上限 | **2000** | `read_file` 的单次返回行数 | `run_shell` 的单次返回行数 |
| 字节上限 | **50 KiB** | `read_file` 的单次返回字节 | `run_shell` 的单次返回字节 |
| 单行字符上限 | **2000** | `read_file` 的单行长度（仅读取侧） | — |

**二者先到者生效**（spec FR-092 / FR-099）。因 MUST NOT 新增清单条目（FR-052），两个工具模块**各自定义本地副本**，但**单元测试 MUST 断言两侧数值相等**（R-18 / FR-103）。

---

## 4. 工作区根的推导（无环境变量）

```text
契约库位置：<workspace>/tools/changes.py
   ↓ Path(__file__).resolve().parent.parent
工作区根：  <workspace>
```

**不变量**：
- `resolve_path(相对路径)` → `<workspace>/<相对路径>`（MUST NOT 依赖进程 cwd）
- `resolve_path(绝对路径)` → 原样返回（路径白名单由用户自管）
- `relative_path(工作区内路径)` → POSIX 相对路径；工作区外 → 绝对路径回退
- **MUST NOT** 读任何环境变量（spec FR-002 / FR-104）→ 智能体行为不受环境变量影响

---

## 5. 状态机：`donkey init` 对**单个清单条目**的作用

```text
                    ┌─────────────────────────┐
                    │  条目未出现在清单中      │  → 不动（清单外，--force 也不动）
                    └─────────────────────────┘

  目标不存在 ────────► [创建] ──► 计数 +1 (created)
       │                   │
       │                   └─ 写入失败 → TemplateGenerationError (exit 3)
       │
  目标存在 + 非强制 ──► [跳过] ──► 计数 +1 (skipped)，内容与 mtime 均不变
       │
  目标存在 + 强制 ──► [删除并重建] ──► 计数 +1 (created)
       │                   │
       │                   └─ 写入失败 → TemplateGenerationError (exit 3)
       │
       └─ ★ 契约库特例（FR-105 / R-07）：
            强制 + 契约库已存在 → [保留原样] ──► 计数 +1 (skipped)
            强制 + 契约库不存在   → [创建]     ──► 计数 +1 (created)
```

**持久不变量**（P2 沿用，本 Phase MUST NOT 削弱 —— spec FR-069）：
- **I1**：非强制模式下，已存在文件的内容**与 mtime** 均不变
- **I2**：强制模式下，清单内条目恢复出厂内容（**契约库除外** —— FR-105 的唯一例外）
- **I3**：目录条目在任何模式下都不删除目录本身、不删除目录内任何文件
- **I4**：清单外的任何路径永不被删除或改写

---

## 6. 计数口径（本 Phase 落地后的确切数值）

| 场景 | `templates_loaded` | `files_created` | `files_skipped` |
|---|---|---|---|
| 全新创建 | **54** | **48** | **0** |
| 二次 init（非强制） | 54 | **0** | **48** |
| `--force`（契约库已存在） | 54 | **47** | **1** |

**推导**（R-07）：
- 清单 54 条 = 45 个文本型 + 3 个 sqlite3 型 + 6 个目录型
- 文件型条目 = 54 − 6 = **48** → `files_created` / `files_skipped` 只统计文件型
- 磁盘落地 = 48 个清单文件 + 1 份工作区清单 = **49** 个文件
- 磁盘目录 = 根 + 6 个清单目录 + 3 个 Skill Level 3 子目录 = **10** 个
- `--force` 时契约库被豁免 → 计入 `files_skipped`（它确实没被创建）

**新增的 `.py` 文件数 = 6**（`tools/` 下 5 + Skill 第三层脚本 1）—— 源提示词 §3.5 写的"5 个"是笔误（spec 澄清 #1 的连带校正）。

---

## 7. 工具的输入 → 输出关系（9 个 `@tool`）

```text
read_file(path, start_line=1, num_lines=None) ──► str（呈现文本：页范围头 + 行号前缀 + 续读提示）
write_file(path, content, dry_run, include_previous, expected_hash) ──► str（JSON）
copy_file(src, dst, dry_run, expected_hash) ──► str（JSON）
move_file(src, dst, dry_run, expected_hash) ──► str（JSON）
delete_file(path, include_previous, dry_run, expected_hash) ──► str（JSON）
list_dir(path, include_hidden, offset, limit) ──► list[str]
stat(path, with_hash) ──► dict[str, Any]
run_shell(command, timeout, cwd) ──► str（JSON）
fetch_url(url, method, headers, timeout) ──► str（JSON）
```

**四个改文件工具**（写 / 复制 / 移动 / 删除）的共同形状：

```text
输入守卫 ──► 期望指纹不匹配？ ──是─► 抛 FileChangedError（无任何磁盘副作用）
                    │否
                    ▼
              读旧字节（目标已存在时）
                    ▼
              build_change_record(action, path, old, new, ...)
                    ▼
              dry_run？ ──是─► 返回 JSON（applied=false），不落盘
                    │否
                    ▼
              原子写 / 移动 / 删除 ──► 返回 JSON（applied=true）
```

**不变式**：
- 期望指纹是**入参守卫**，MUST NOT 出现在变更记录里（spec FR-019）
- 预览模式下**零磁盘副作用**（不建父目录 / 不写 / 不移 / 不删 / 不留临时文件）
- 所有改文件的工具**必须**经契约库生成变更记录，MUST NOT 自造指纹 / 差异逻辑（spec FR-012(c) / FR-016）

---

## 8. 测试三层的职责边界

| 层 | 目录 | 能否 import 工作区产物 | 能否 import donkey 业务代码 | 本 Phase 的用例数 |
|---|---|---|---|---|
| 单元 | `tests/unit/` | **可以**（渲染到 tmp 后按包名导入 + teardown 清 `sys.modules`，R-02） | 可以 | ≥15（新建） |
| 集成 | `tests/integration/` | **只能独立子进程**（FR-062） | 可以 | ≥4（**本 Phase 首次启用**） |
| e2e / phase | `tests/e2e/phase/` | **只能独立子进程**（FR-066） | **不可以**（黑盒） | 16（新建） |

**"集成层为何启用"**（spec FR-061 要求重新论证）：P2 的理由是"本 Phase 的 2 个新 core 模块由单一流水线串联、无跨模块协作契约" —— 该理由在 P3 **失效**：P3 出现**真正的跨模块协作** —— `donkey init`（core 层）产出的工作区产物（渲染层）被**独立进程**导入并调用（用户侧），这正是集成层的定义。

---

## 9. 退出码与异常的映射（本 Phase 新增部分）

```text
DonkeyError
└── WorkspaceInitError
    ├── PathNotFoundError        exit 1
    ├── PathPermissionError      exit 2
    ├── TemplateGenerationError  exit 3
    └── BuiltinToolGenerationError  exit 4   ← 本 Phase 新增
```

**exit 4 的两类成因**（spec FR-072，**不含**"导入预演失败" —— 本 Phase 不做导入预演）：

| 成因 | 归类 | 用户修复动作 |
|---|---|---|
| 3 个内置工具文件写入失败 | 内置工具生成类 | 重装 donkey / 检查权限 / 重试 init |
| 示例 Skill 三层写入失败 | 内置工具生成类 | 同上 |

（模板源缺失 → 归 exit 3 的"模板生成类"，**不是** exit 4 —— 见 [contracts/exit-codes.md](contracts/exit-codes.md) §3。）

---

## 10. 术语表

| 术语 | 定义 |
|---|---|
| **材料层** | workspace 目录内的一切（用户可任意替换） |
| **引擎层** | donkey 代码（Agent Loop / 中间件 / 渲染 / 上下文治理），**无配置项** |
| **契约库** | `tools/changes.py` —— 变更记录的唯一产地，**0 个 `@tool`** |
| **变更记录** | 一次文件变更的"原材料"（12 基线 + 4 条件字段） |
| **呈现文本** | `read_file` 返回的带页范围头 + 行号前缀的文本（**非**纯正文） |
| **续读指针** | 截断时给出的"下一段起始行号" |
| **条目级豁免** | 契约库在 `--force` 下不被重置（FR-105 / R-07） |
| **智能体入口文件** | `agent.py` / `main.py` 这类（宪法 N-01 禁止）；Skill 第三层演示脚本**不属**此类（FR-050 引用的宪法 §6.3 例外 E-02 + §5 章 [D-19] 授权） |
