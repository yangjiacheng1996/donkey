# 数据模型 —— F001-P2 `template_skeleton`

**Phase**: F001-P2（`donkey init` 模板骨架幂等生成）
**上游**：[spec.md](spec.md)（FR-001 ~ FR-069 / SC-001 ~ SC-021）、[plan.md](plan.md)、[research.md](research.md)
**日期**: 2026-10-23

> 本文件描述**实体、字段、关系、状态流转与校验规则**。字段语义以 spec 为准；本文件补齐 spec 未展开的**状态机**与**口径推导**。

---

## 1. 实体总览

```text
安装包内                                   workspace 内
┌──────────────────────────────┐          ┌────────────────────────────┐
│ 模板清单 manifest.json        │          │ 工作区清单 manifest.json    │
│  version: int                 │          │  version: int = 1          │
│  entries: [模板清单条目 × 46] │────渲染──▶│  name: str                 │
└───────────┬──────────────────┘          │  created_at: str           │
            │ 1:1（仅文本类条目）             │  donkey_version: str       │
            ▼                               └────────────────────────────┘
   模板源文件 × 37                            ▲
   <entry.path>.txt                          │ 步骤⑤（独立于渲染）
                                            │
   sqlite3 结构构造器 × 3 ──────────────────▶│  memory/*.sqlite3 × 3
   （程序化建库，不带二进制模板）              │  sessions: 3 表 + 2 索引
                                            │  store / knowledge: 0 表
```

**关键关系**：

| 关系 | 基数 | 说明 |
|---|---|---|
| 模板清单 → 模板清单条目 | 1 : 46 | 清单的 `entries` 数组；条目顺序**无语义**（R-06） |
| 模板清单条目 → 模板源文件 | 1 : 0..1 | **仅**文本类条目（37 个）有源文件；目录条目（6）与 sqlite3 条目（3）**无**源文件 |
| 模板清单条目 → workspace 目标路径 | 1 : 1 | 目标路径 = `workspace_path / entry.path`（FR-005 / FR-007） |
| 工作区清单 → workspace 根 | 1 : 0..1 | 不在模板清单内；`--force` 时被覆盖（唯一的"清单外覆盖"路径，R-10） |
| sqlite3 条目 → 结构构造器 | 1 : 1 | 按条目路径末段分派到 3 个 builder 之一（FR-011 / FR-030） |

---

## 2. 模板清单条目（TemplateManifestEntry）

**归属**：安装包内 `donkey/core/workspace/templates/manifest.json`

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `path` | `str` | **必填**、非空、相对 workspace 根的 POSIX 风格路径 | 目标路径的相对部分；同时是模板源文件名的派生依据（`templates/<path>.txt`） |
| `format` | `str` | **可选**；缺省视为 `text`；取值 MUST ∈ 7 种受支持值 | 决定渲染分派方式 |

**`format` 的 7 种取值与分派语义**：

| `format` | 类别 | 渲染行为 | 源文件 | 计入 created/skipped |
|---|---|---|---|---|
| `markdown` | 文本类 | 复制 `templates/<path>.txt` → 占位符替换 → 写目标 | 有 | ✅ |
| `toml` | 文本类 | 同上 | 有 | ✅ |
| `json` | 文本类 | 同上 | 有 | ✅ |
| `text` | 文本类 | 同上 | 有 | ✅ |
| `python` | 文本类 | 同上 | 有 | ✅ |
| `directory` | 目录类 | `mkdir`（父目录一并确保） | **无** | ❌ |
| `sqlite3` | 数据库类 | 调对应结构构造器 | **无** | ✅ |

> **`python` 在 P2 无条目使用** —— 清单中不含任何 `format: "python"` 的条目；该值已支持，留给 F001-P3 的 3 个内置 `@tool`（N-01 门禁 G14 依赖此事实）。

**清单结构校验规则**（FR-002 / FR-003，违反即 `TemplateGenerationError` → exit 3）：

| # | 规则 | 违规示例 |
|---|---|---|
| V1 | 顶层 `version` MUST 是整数 | `"1"`（字符串）、缺失 |
| V2 | 顶层 `entries` MUST 是列表 | `{}`（对象）、缺失 |
| V3 | 每个条目 MUST 是对象 | `"instruction.md"`（裸字符串） |
| V4 | 每个条目的 `path` MUST 是非空字符串 | 缺失、`""`、`123` |
| V5 | `format` 若存在 MUST ∈ 7 种受支持值 | `"yaml"`、`"sqlite"`（拼写错误） |
| V6 | 文件本身 MUST 是合法 JSON | 截断 / 尾逗号 |

**校验失败的统一语义**：一律 `TemplateGenerationError`（exit 3），**不**是 `PathNotFoundError`（exit 1）—— 用户修复动作不同（重装 donkey vs 建目录 / 换路径，FR-038）。

---

## 3. 模板源文件（TemplateSource）

**归属**：安装包内 `donkey/core/workspace/templates/<entry.path>.txt`

| 属性 | 值 |
|---|---|
| 命名规则 | 与清单条目的 `path` **逐字符**对应（`providers/openai.toml` → `templates/providers/openai.toml.txt`） |
| 数量 | **37** 个 = 46 条 − 6 目录条目 − 3 sqlite3 条目 |
| 编码 | UTF-8，无 BOM |
| 内容 | 占位符 + 出厂正文；**不含**任何待替换凭据占位符（`REPLACE_ME` 类一律禁止，FR-046） |

**占位符规范**（FR-015）：

| 占位符 | 替换为 | 说明 |
|---|---|---|
| `{{ workspace_name }}` | 工作区名称 | 主形态 |
| `{{workspace_name}}` | 工作区名称 | 无空格变体，同样 MUST 被识别 |
| 其它任意 `{{ ... }}` | **原样保留** | MUST NOT 报错、MUST NOT 替换为空串 |

**名称原样注入**：名称含空格 / Unicode / 特殊字符时 MUST 原样写入，MUST NOT 转义、MUST NOT 截断（Edge Cases「渲染与幂等类」）。

**37 个源文件的构成**：

| 组 | 数量 | 内容来源 |
|---|---|---|
| F001-P1 占位（**须覆盖**） | 3 | `instruction.md.txt` / `providers/default.toml.txt` / `mcp/mcp.json.txt`（R-07） |
| 新增文本模板 | 7 | `README.md` / `.gitignore` / `tools/README.md` / `mcp/README.md` / `skills/README.md` / `memory/README.md` / `skills/example/SKILL.md` |
| 新增 provider 索引 | 1 | `providers/README.md`（列全 26 家，FR-045） |
| 新增 provider 配置 | 26 | `providers/<id>.toml`（§8.3 逐字抄录，模型条目合计 51 条，R-09） |
| **合计** | **37** | — |

---

## 4. 工作区清单（WorkspaceManifest）

**归属**：workspace 根 `manifest.json`（**与安装包内的模板清单是两个不同的文件**，FR-004 / 宪法 §2.6）

| 字段 | 类型 | 约束 | 出厂值 |
|---|---|---|---|
| `version` | `int` | MUST 为整数，v1 = `1` | `1` |
| `name` | `str` | 工作区名称；CLI 通道恒等于解析后路径的末段名 | 路径末段名 |
| `created_at` | `str` | MUST 为**带时区**的 ISO 8601 时间戳（`datetime.now(timezone.utc).isoformat()`） | 生成时刻 |
| `donkey_version` | `str` | MUST 为 `0.1.0`（硬编码；MUST NOT import 内部 `__version__`） | `"0.1.0"` |

**硬约束**：

| # | 规则 | 出处 |
|---|---|---|
| M1 | 字段**恰好且仅**为这 4 项 —— MUST NOT 增字段 | FR-019 |
| M2 | 写入格式 `json.dumps(manifest, indent=2, ensure_ascii=False)` | FR-022 |
| M3 | 编码 UTF-8，MUST NOT 带 BOM | FR-022 |
| M4 | 无 `--force` 且已存在 → **不覆盖**，`created_at` 保留原值 | FR-020 |
| M5 | 有 `--force` → 覆盖并把 `created_at` 刷新为当前时刻 | FR-020 |
| M6 | 文件不存在 → 无条件创建（无论是否 `--force`） | FR-020 |
| M7 | 读取时 JSON 非法 → `TemplateGenerationError`（exit 3）；文件不存在 → 返回"无" | FR-018 |

---

## 5. 渲染结果对象（InitResult）

**归属**：`donkey.core.api.InitResult` —— **F001-P1 已冻结，P2 MUST NOT 改字段集合 / 顺序 / 类型**（FR-025）

| 字段 | 类型 | P2 取值 | P1 取值 |
|---|---|---|---|
| `workspace_path` | `Path` | 绝对路径 | 绝对路径 |
| `name` | `str` | 最终名称 | 最终名称 |
| `force` | `bool` | 是否请求强制重置 | 同 |
| `templates_loaded` | `int` | **46** = loader 返回的**原始列表长度**（含目录条目、含重复条目 —— FR-026） | `0` |
| `files_created` | `int` | 本次新建的**文件型**条目数（40 = 37 文本 + 3 sqlite3；目录条目不计入），按**唯一路径**计一次 | `0` |
| `files_skipped` | `int` | 已存在而跳过的**文件型**条目数（同上口径） | `0` |

**计数口径推导**（R-08 / FR-017）：

```
可计数的文件型条目 = 37 个文本条目 + 3 个 sqlite3 条目 = 40
目录条目（6 个）不计入 created / skipped
templates_loaded = loader 返回的原始列表长度（46）—— 含目录条目、含重复条目；去重只发生在 render_templates 侧

场景                     templates_loaded  files_created  files_skipped
全新创建                 46                40             0
二次 init（无 --force）  46                0              40
二次 init（有 --force）  46                40             0
F001-P3 完成后（+8 条）  54                48             0
```

> 「二次 init（有 --force）」行成立的前提是 **FR-010**：目录条目在 `--force` 下**不删除任何文件** —— 其内清单文件由各自的文本 / sqlite3 条目 unlink + 重建，故 40 个文件型条目全部恢复出厂内容，且 `files_created` = 40 无虚账。若目录条目改为删除文件（FR-010 的旧口径），该行会失真（文件被删却仍计 created）。

> **`templates_loaded` 恒为清单的原始条目总数**（46；含目录条目、含重复条目），与"本次实际处理了多少"无关 —— 它是"清单有多大规模"的指标，不是"本次动作有多少"的指标（与 P1 冻结的语义一致）。

---

## 6. 目标路径状态机

**单条目视角**（`entry.path` 对应的 workspace 目标路径）：

```text
                    ┌──────────────────┐
                    │   不存在 (ABSENT) │
                    └────────┬─────────┘
                             │
              无 --force    │    有 --force
              ─────────────┼─────────────
                             ▼
                    ┌──────────────────┐
                    │  已存在 (PRESENT) │◀──── 无 --force 时命中即停
                    └────────┬─────────┘        （计数 +1 skipped，内容与 mtime 不变）
                             │
              有 --force    │
              ─────────────┤
                             ▼
              ┌────────────────────────────┐
              │  删除（文本：unlink 文件）      │
              │  删除（sqlite3：unlink 主库     │
              │        + unlink -wal/-shm）    │
              │  （目录：**不删除** —— 目录条目  │
              │        不删任何文件；其内清单文  │
              │        件由自己的条目负责重建）  │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  重建（文本：写正文            │
              │        sqlite3：调 builder）  │
              └────────────┬───────────────┘
                           ▼
                    ┌──────────────────┐
                    │ 已存在 (PRESENT)  │  计数 +1 created
                    └──────────────────┘
```

**状态迁移表**：

| 当前状态 | `force` | 动作 | 结果状态 | 计数 | 内容 | mtime |
|---|---|---|---|---|---|---|
| ABSENT | 否 | 写入 / 构造 | PRESENT | created +1 | 出厂 | 新 |
| ABSENT | 是 | 写入 / 构造 | PRESENT | created +1 | 出厂 | 新 |
| PRESENT | 否 | **不动** | PRESENT | skipped +1 | 用户内容 | **不变** |
| PRESENT | 是 | 删除 → 重建 | PRESENT | created +1 | 出厂 | 新 |
| PRESENT（**是目录**） | 任意 | 报错（**仅文本类与 sqlite3 类条目**；目录类条目已存在即保留不变，见 spec FR-010） | — | — | — | — |
| PRESENT（**只读**） | 否 | 跳过（不尝试写入） | PRESENT | skipped +1 | 用户内容 | 不变 |
| PRESENT（只读） | 是 | 删除失败 → 报错 | — | — | — | — |

**关键不变量**：

| # | 不变量 | 出处 |
|---|---|---|
| I1 | 无 `--force` 时，已存在文件的**内容与 mtime 均不变**（"完全不动"，非"重写相同内容"） | FR-008 / SC-004 |
| I2 | 强制重置的作用域 **⊆ 模板清单条目**（含 sqlite3 附属文件这一**唯一**例外，R-03） | FR-013 |
| I3 | 目录条目在 `--force` 下 MUST NOT 删除目录本身，MUST NOT 删除目录内的**任何**文件（清单内外一律不动）；其内清单文件的重置由各自条目负责 | FR-010 |
| I4 | 渲染 MUST NOT 依赖条目顺序 —— 写文件前确保父目录存在 | FR-012 / R-06 |
| I5 | 渲染阶段（FR-027 步骤 ④）的一切失败 MUST 归一为 `TemplateGenerationError`（exit 3），MUST NOT 逃逸裸异常；阶段 ① / ③ 的权限不足归 exit 2（spec FR-038） | FR-014 / FR-038 |

---

## 7. sqlite3 模板三件套

### 7.1 `memory/sessions.sqlite3` —— 短期记忆库

| 表 | 归属 | 结构来源 | 列数 |
|---|---|---|---|
| `checkpoints` | **上游 saver** | 上游 `setup()` 的 DDL（donkey MUST NOT 维护） | 7 |
| `writes` | **上游 saver** | 同上 | 9 |
| `sessions_metadata` | **donkey 自管** | `harness/report/sessions_sqlite表结构一览.md` §2.2 | 6 |

**`sessions_metadata` 的 6 字段**：

| 字段 | 类型 | 约束 | 语义 |
|---|---|---|---|
| `thread_id` | `TEXT` | **PRIMARY KEY** | 会话 id（SqliteSaver 的 thread_id） |
| `title` | `TEXT` | `NOT NULL` | 会话标题（≤ 20 字） |
| `created_at` | `REAL` | `NOT NULL` | epoch 秒 |
| `updated_at` | `REAL` | `NOT NULL` | epoch 秒（排序主索引） |
| `donkey_version` | `TEXT` | `NOT NULL` | 生成该记录的 donkey 版本（迁移提示） |
| `first_prompt` | `TEXT` | nullable | 用户首轮 prompt 快照 |

**2 个索引**：`idx_sessions_metadata_title`（title）、`idx_sessions_metadata_updated_at`（updated_at）。

**建库流程**（R-01 / R-04）：

```
sqlite3.connect(path)
  → SqliteSaver(conn)          # 实例；注意 import 路径是 langgraph.checkpoint.sqlite
  → saver.setup()               # 实例方法；建 checkpoints / writes；幂等
  → CREATE TABLE IF NOT EXISTS sessions_metadata (...)
  → CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title ...
  → CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at ...
  → commit()
  → close()
```

**实测落地形态**（R-05）：

```
表:   ['checkpoints', 'sessions_metadata', 'writes']
索引: ['idx_sessions_metadata_title', 'idx_sessions_metadata_updated_at',
       'sqlite_autoindex_checkpoints_1', 'sqlite_autoindex_sessions_metadata_1',
       'sqlite_autoindex_writes_1']
```

> ⚠️ `sqlite_autoindex_*` 是 PRIMARY KEY 自动索引，`tbl_name` 亦为对应表名。
> **测试断言 MUST 用 `in` 判定，MUST NOT 用集合相等**（spec e2e 场景 14 给出的形态即 `in`）。

**出厂态**：三张表存在 + 2 个索引存在 + `sessions_metadata` **记录数 = 0**。

### 7.2 `memory/store.sqlite3` —— 长期记忆库（v1 占位）

| 属性 | 值 |
|---|---|
| 表数量 | **0** |
| 索引数量 | **0** |
| 用途 | v3 `SqliteStore` 实施时的落点；v1 ~ v2 用 `InMemoryStore` 顶替 |
| 约束 | MUST NOT 被 donkey 本体的任何运行时路径读取（FR-032 / D-11） |

### 7.3 `memory/knowledge.sqlite3` —— 知识库（v1 占位）

| 属性 | 值 |
|---|---|
| 表数量 | **0** |
| 索引数量 | **0** |
| 用途 | v3+ RAG / 向量库落点；schema 待引擎（sqlite-vec / faiss+sqlite）选型后正式化 |
| 约束 | 同上 |

### 7.4 附属文件（WAL / SHM）

| 文件 | 何时存在 | `--force` 行为 | 非 `--force` 行为 |
|---|---|---|---|
| `<name>-wal` | 连接存活期间 / 非正常关闭后 | **连带删除** | 不动 |
| `<name>-shm` | 同上 | **连带删除** | 不动 |

**实测结论（R-03）**：正常关闭连接时 SQLite 自动 checkpoint 并清理侧车 → 正常运行路径下 `donkey init` **不会**留下侧车；
陈旧 WAL 因头部盐值不匹配被**安全忽略**（重建后读取得 0 行）→ 连带删除是**防御性**措施，非必要条件。

---

## 8. 异常层次与失败矩阵

```
Exception
└── DonkeyError                       # donkey 总基类
    └── WorkspaceInitError            # F001 基类
        ├── PathNotFoundError         # exit 1：路径 / 输入不合法
        ├── PathPermissionError       # exit 2：权限不足
        └── TemplateGenerationError   # exit 3：模板骨架生成失败【P2 新增】
```

### 8.1 模板类失败的 7 类成因 → 1 个错误类（FR-014）

> **本表是 spec『模板生成类失败的 7 类成因（权威分类法）』段的镜像**，冲突时以 spec 为准。

| # | 成因 | 触发点 | 错误信息 MUST 含 |
|---|---|---|---|
| 1 | 模板清单缺失 / JSON 非法 / schema 非法 | `load_template_manifest` | 失败环节 + 下一步 |
| 2 | 模板源文件缺失 | `render_templates` | 缺失的源路径 + 下一步 |
| 3 | 渲染失败（正文不可解析） | `render_templates` | 失败环节 + 下一步 |
| 4 | 文件写入失败（磁盘满 / 权限在渲染中途被撤销） | `render_templates` | 目标路径 + 下一步 |
| 5 | sqlite3 结构构造失败 | `build_*_sqlite` | 失败环节 + 下一步 |
| 6 | 上游 saver 包缺失 / 版本不兼容 / 导入失败 | `build_sessions_sqlite` | "运行期依赖缺失或不可用" + 下一步 |
| 7 | 目标路径已存在但**是目录**（**且该条目为文本类或 sqlite3 类**） | `render_templates` | 目标路径 + 下一步 |

**合并理由（奥卡姆剃刀）**：7 类的用户修复动作相同（重装 donkey / 检查权限 / 重试 init）→ 合并到 1 个码值 `3`，
不浪费码值给稀有错误。**与 exit 1 的边界**：修复动作不同（建目录/换路径 vs 重装 donkey）→ MUST NOT 合并（FR-038）。

### 8.2 失败矩阵（阶段 × 失败面）

> **退出码语义按阶段切分（spec FR-038）**：阶段 ① / ③ 的权限不足 → `2`；阶段 ④ / ⑤ 的一切失败 → `3`。
> **阶段 ③ 的一切失败一律归 `2`** —— 含磁盘满（`ENOSPC`）在内，`mkdir` 抛出的任何 `OSError` MUST 包装为 `PathPermissionError`；该阶段的失败根因由**错误信息**承载（指出磁盘空间 / 权限），"下一步"固定句沿用 P1 的 `_NEXT_STEP`（MUST NOT 改动 P1 已有文案）。`3` 侧的"磁盘满"仅指**阶段 ④**的写入失败。

| 阶段 | 路径类（1） | 权限类（2） | 模板类（3） |
|---|---|---|---|
| ① 前置校验（`validate_init_request`） | ✅ 父目录缺失 / 末段名为空 / 非法字符 / 目标非目录 | ✅ 读 / 写 / 执行位缺失 | — |
| ② 加载清单（`load_template_manifest`） | — | — | ✅ 缺失 / JSON 非法 / schema 非法 |
| ③ 建根目录（`mkdir(exist_ok=True)`） | — | ✅ 任何 `OSError`（权限不足 / 磁盘满 `ENOSPC`）→ 包装为 `PathPermissionError` | — |
| ④ 渲染（`render_templates`） | — | — | ✅ 源缺失 / 写入失败（磁盘满 / 权限中途撤销）/ sqlite3 构造失败 / 目标是目录（文本类与 sqlite3 类条目） |
| ⑤ 写工作区清单（`write_workspace_manifest`） | — | — | ✅ JSON 解析失败 / 写入失败 |

> **步骤 ⑤ 失败不回滚（spec 澄清 #26 / plan R-16）**：步骤 ⑤ 失败 MUST 抛模板生成类错误（退出码 `3`），而**步骤 ④ 已落地的文件 MUST 保留**（不删除、不还原）；本 Phase **MUST NOT** 实现任何事务回滚机制。

> **错误信息统一模板**（R-12，沿用 P1 的 `_NEXT_STEP` 模式）：
> `[失败环节] + [具体对象] + [固定的下一步句]`。
> 模板类失败的下一步句固定为：**"下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。"**
> 文案常量 `_NEXT_STEP_TEMPLATE` 落 `donkey/core/exceptions.py`（与错误类同源，避免 core/workspace 内模块循环 import —— R-12）。

---

## 9. 校验规则汇总

| 组 | 规则 | 违反后果 | 落点 |
|---|---|---|---|
| 清单结构 | V1 ~ V6（§2） | `TemplateGenerationError` → exit 3 | `load_template_manifest` |
| 重复路径 | 清单条目路径重复 MUST NOT 报错；**去重发生在 `render_templates`（renderer）侧** —— 同一路径只处理一次，以重复项中**最后出现**的条目为准（其 `format` 与源模板生效）；`files_created` / `files_skipped` 按**唯一路径**计一次；`templates_loaded` = loader 返回的**原始列表长度**（含目录条目、含重复条目）。loader 返回**未去重**的原始条目列表（spec FR-001 / FR-002 / FR-026） | 不报错（口径约束） | `render_templates`（去重）|
| 目标路径 | 目标必须是文件或不存在；存在且是目录 → 拒绝（**仅文本类与 sqlite3 类条目**；目录类条目已存在即保留不变，见 spec FR-010） | `TemplateGenerationError` → exit 3 | `render_templates` |
| 源文件 | 文本类条目的源 MUST 存在 | `TemplateGenerationError` → exit 3 | `render_templates` |
| 占位符 | 已知占位符 MUST 被替换；未知占位符 MUST 原样保留；名称含空格 / Unicode / 特殊字符时 MUST 原样注入（MUST NOT 转义 / 截断） | 不报错 | `render_templates` |
| 工作区清单 | M1 ~ M7（§4） | `TemplateGenerationError` → exit 3 | `workspace/manifest.py` |
| 计数 | `files_created` / `files_skipped` = **文件型条目**数（40 = 37 文本 + 3 sqlite3；目录条目不计入），按**唯一路径**计一次；`templates_loaded` = loader 返回的**原始列表长度**（46；含目录条目、含重复条目） | 不报错（口径约束） | `render_templates` |
| 结构完整性 | 37 文本条目 ↔ 37 源文件 **一一对应**；46 = 37 + 6 + 3 | 构建期自检失败 → exit 3 | `load_template_manifest` |
| provider 配置 | 26 份可被 `tomllib` 解析；`enabled` 全为 `false`；凭据为空；模型条目合计 **51** 条 | 构建期自检失败 → exit 3 | 构建期校验 |

---

## End of data-model.
