# 契约：核心库 API（F001-P2）

**版本**：v1.1（F001-P1 冻结的 v1.0 上追加 P2 能力；**`InitResult` 契约不变**）
**所有者**：`donkey/core/api.py` + `donkey/core/workspace/{init,manifest,sqlite3_templates}.py`
**上游**：[spec.md](../spec.md) FR-001 ~ FR-034、FR-024 ~ FR-029；[research.md](../research.md) R-01 / R-04 / R-06 / R-08 / R-10

> **冻结声明**：`InitResult` 的字段集合 / 顺序 / 类型自 F001-P1 起**冻结** —— F002 / F003 / F004 / F005 / F006 共同依赖它，本 Phase MUST NOT 变更（spec FR-025）。

---

## 1. 门面 API（`donkey.core.api`）

```python
def init_workspace(path: str | Path,
                   name: str | None = None,
                   force: bool = False) -> InitResult: ...
```

**实现约束**：函数体 MUST 只做两件事 —— 调 `init_workspace_inner` + 构造 `InitResult`（spec FR-024）。MUST NOT 在门面层承载业务逻辑。

```python
from donkey.core.workspace.init import init_workspace_inner

def init_workspace(path, name=None, force=False):
    abs_path, resolved_name, resolved_force, created, skipped, loaded = init_workspace_inner(
        path=path, name=name, force=force,
    )
    # `loaded` = 模板清单的**原始**条目总数（含重复），MUST NOT 是去重后的长度
    return InitResult(
        workspace_path=abs_path,
        name=resolved_name,
        force=resolved_force,
        templates_loaded=loaded,
        files_created=created,
        files_skipped=skipped,
    )
```

| 参数 | 类型 | 语义（P1 已冻结，本 Phase 不变） |
|---|---|---|
| `path` | `str \| Path` | workspace 根目录路径；内部统一解析为绝对路径 |
| `name` | `str \| None` | 缺省 / 空串 → 名称取解析后路径的末段名；显式非空 → 以该值为准。**v1 的 CLI 通道永不传该参数** |
| `force` | `bool` | 是否请求强制重置 |

**失败**：抛出 `WorkspaceInitError` 的子类（`PathNotFoundError` / `PathPermissionError` / `TemplateGenerationError`）。
核心层 MUST NOT 返回退出码、MUST NOT 打印、MUST NOT 退出进程（宪法 N-05）。

---

## 2. `InitResult`

```python
@dataclass(frozen=True)
class InitResult:
    workspace_path: Path   # 绝对路径
    name: str              # 最终名称（CLI 通道恒 == workspace_path.name）
    force: bool            # 是否请求强制重置
    templates_loaded: int  # 清单条目总数（P2 = 46）
    files_created: int     # 本次新建的文件型条目数（P2 全新创建 = 40）
    files_skipped: int     # 已存在而跳过的文件型条目数（P2 二次 init = 40）
```

**不变量**：

| # | 不变量 |
|---|---|
| A1 | 不可变（`frozen=True`） |
| A2 | `workspace_path` 为绝对路径 |
| A3 | `templates_loaded` == 模板清单的**原始条目总数**（含目录条目、含重复条目）== `len(载入的原始条目列表)`；MUST NOT 用去重后的唯一路径数 |
| A4 | `files_created` + `files_skipped` == 本次**已存在或被创建**的**文件型条目**数（40 = 37 文本 + 3 sqlite3；目录条目不计入）；按**唯一路径**计一次 |
| A5 | 无 `--force` 且目标已存在 → `files_created` = 0，`files_skipped` = 40 |
| A6 | `name` 在未指定时 == `workspace_path.name`；显式指定时 == 该值 |

---

## 3. `donkey.core.workspace.init` —— P2 追加能力

> P1 已实现的 `check_path` / `check_permission` / `validate_init_request` **本 Phase MUST NOT 修改**（spec FR-029）。

### 3.1 `load_template_manifest`

```python
def load_template_manifest(manifest_path: Path | None = None) -> list[dict]: ...
```

| 项 | 契约 |
|---|---|
| 默认路径 | `DEFAULT_TEMPLATES_ROOT / "manifest.json"`（`DEFAULT_TEMPLATES_ROOT = Path(__file__).parent / "templates"`） |
| 返回 | 清单条目列表（`list[dict]`）；MUST NOT 就地修改 |
| 失败 | 清单缺失 / JSON 非法 / schema 非法（V1 ~ V6）→ `TemplateGenerationError`（exit 3）；**MUST NOT** 抛 `PathNotFoundError` |
| 注入点 | `manifest_path` 可注入 → 单元测试用临时目录构造失败分支，**MUST NOT** 破坏已安装包 |
| 重复路径 | 返回**未去重**的原始条目列表（长度 = `templates_loaded`，含目录条目、含重复条目）；去重由 `render_templates` 承担（见 §3.2 第 1 条）（spec FR-001 / FR-002 / FR-026 / 澄清 #24 / R-15）。loader **MUST NOT** 去重 —— `list[dict]` 内无位置可携带原始总数 |

**schema 校验**：见 [data-model.md](../data-model.md) §2 的 V1 ~ V6。

### 3.2 `render_templates`

```python
def render_templates(workspace_path: Path,
                     name: str,
                     force: bool,
                     manifest_entries: list[dict],
                     templates_root: Path | None = None) -> tuple[int, int]: ...
```

| 参数 | 语义 |
|---|---|
| `workspace_path` | workspace 绝对路径（根目录本身已存在） |
| `name` | 工作区名称 —— 占位符替换的值 |
| `force` | 是否强制重置 |
| `manifest_entries` | 清单条目列表 |
| `templates_root` | 模板源根目录；缺省 = `DEFAULT_TEMPLATES_ROOT`（**注入点**，spec FR-006） |
| **返回** | `(files_created, files_skipped)` —— 仅统计**文件型**条目（40 = 37 文本 + 3 sqlite3；目录条目不计入），按**唯一路径**计一次（spec FR-017） |

**行为契约**：

1. **先按唯一路径去重** —— `manifest_entries` 若含重复路径，MUST 按**唯一路径**处理（同一路径只处理一次，以重复项中**最后出现**的条目为准，其 `format` 与源模板生效），MUST NOT 对同一路径既计 created 又计 skipped（spec FR-002 / 澄清 #24 / R-15 —— `render_templates` 是公开 API，MUST NOT 假定入参已去重）；再遍历条目，按 `format` 分派（7 种取值，见 data-model §2）；
2. **MUST NOT 依赖条目顺序** —— 写任何文件前 MUST 先确保其父目录存在（父目录创建限定在 workspace 根之下）（spec FR-012 / R-06）；
3. 文本类：源 = `templates_root / f"{entry['path']}.txt"`；源缺失 → `TemplateGenerationError`；
4. 文本类幂等：目标不存在 → 写入；目标已存在且无 `--force` → **完全不动**（内容 + mtime 均不变）；有 `--force` → unlink 后重写（**MUST NOT** 用"打开覆盖写"，那会保留原权限位与 mtime 语义）；
5. 目录类：不存在 → `mkdir(parents=True, exist_ok=True)`；已存在（**无论是否带 `--force`**）→ **保留不变**，MUST NOT 删目录本身、MUST NOT 删除目录内的任何文件（清单内文件由第 3 / 4 / 6 条各自负责重置；目录条目若删除文件，会与第 2 条的顺序无关性冲突 —— 当前清单顺序为「37 文本 → 6 目录 → 3 sqlite3」，删除会抹掉刚重建的文件且不再生成）；
6. sqlite3 类：目标不存在 → 调结构构造器；已存在且无 `--force` → **完全不动**（MUST NOT 校验其结构）；有 `--force` → unlink 主库 **+ unlink `-wal` / `-shm`** 后重建（spec FR-011 / R-03）；
7. 任何 IO / sqlite 失败 → 统一 `TemplateGenerationError`，MUST NOT 逃逸裸 `OSError` / `sqlite3.Error`（spec FR-014）。

**占位符替换**：`{{ workspace_name }}` 与 `{{workspace_name}}` → `name`；其它 `{{ ... }}` 原样保留（MUST NOT 报错、MUST NOT 替换为空串）（spec FR-015）。

### 3.3 `init_workspace_inner`

```python
def init_workspace_inner(path: str | Path,
                          name: str | None,
                          force: bool) -> tuple[Path, str, bool, int, int, int]: ...
```

**五步流水线**（顺序固定，spec FR-027）：

| 步 | 动作 | 产出 | 失败 |
|---|---|---|---|
| ① | `validate_init_request(path, name, force)` | `(abs_path, resolved_name, force)` | `PathNotFoundError`（1）/ `PathPermissionError`（2） |
| ② | `load_template_manifest()` | `manifest_entries` | `TemplateGenerationError`（3） |
| ③ | `abs_path.mkdir(exist_ok=True)` | 根目录 | 权限类（2）—— `mkdir` 抛 `OSError` MUST 包装为 `PathPermissionError` |
| ④ | `render_templates(abs_path, resolved_name, force, manifest_entries)` | `(created, skipped)` | `TemplateGenerationError`（3）—— 含渲染中途权限被撤销 |
| ⑤ | `write_workspace_manifest(abs_path, resolved_name, force)` | 工作区清单 | `TemplateGenerationError`（3） |

**返回**：`(abs_path, resolved_name, force, created, skipped, manifest_total)` —— 其中 `manifest_total` = `len(manifest_entries)`（步骤 ② 已在手的**原始列表长度**，含重复条目）——因 loader 已不负责去重，此处无额外机制；**MUST NOT 为此二次调用 `load_template_manifest()`**（重复 IO + 第二个失败点，且与步骤 ② 的结果可能不自洽）（spec FR-002 / FR-026 / R-15）。

**关键约束**：

- ③ MUST 用 `mkdir(exist_ok=True)` —— **MUST NOT** 用 `parents=True`（父目录缺失已在 ① 判为路径类错误，spec FR-028）；
- ③ 的权限失败 MUST 包装为 `PathPermissionError`（exit 2）；④ / ⑤ 的一切失败 MUST 归 `TemplateGenerationError`（exit 3）—— 退出码按**阶段**切分（spec FR-038）；
- ④ 内部为条目创建父目录时 MAY 用 `parents=True`，但 MUST 限定在 workspace 根之下；
- ① MUST 复用 P1 已实现的三函数，MUST NOT 重新实现路径 / 权限逻辑（spec FR-029）。

---

## 4. `donkey.core.workspace.manifest` —— 工作区清单（P2 新增模块）

```python
WORKSPACE_MANIFEST_FILENAME = "manifest.json"   # 位于 workspace 根

def write_workspace_manifest(workspace_path: Path, name: str, force: bool) -> dict: ...
def read_workspace_manifest(workspace_path: Path) -> dict | None: ...
def ensure_workspace_manifest(workspace_path: Path, name: str, force: bool) -> dict: ...
```

| 能力 | 契约 |
|---|---|
| `write_workspace_manifest` | 写入 4 字段清单；**判定顺序**：带 `--force` → **直接覆盖（不读旧文件）**并刷新 `created_at`；不带 `--force` 且已存在 → 先读（解析失败 → `TemplateGenerationError` exit 3）/ 不覆盖、返回既有内容（`created_at` 保留）；不存在 → 无条件创建；写入格式 `indent=2, ensure_ascii=False`，UTF-8 无 BOM |
| `read_workspace_manifest` | 文件不存在 → 返回 `None`；JSON 非法 → `TemplateGenerationError`（exit 3） |
| `ensure_workspace_manifest` | 与 `write_workspace_manifest` **严格等价**（委托同一实现）：force → 覆盖（**不读旧文件**）；不带 force 且已存在 → 读（解析失败 → `TemplateGenerationError` exit 3）/ 不覆盖；不存在 → 创建（R-10） |

**流程入口**：初始化流程调用 `write_workspace_manifest`（spec FR-027 步骤 ⑤ / R-10）；`ensure_workspace_manifest` 供 F002 / F003 复用。

**边界**：工作区清单**不在** 46 条模板清单内，却是 `--force` 唯一会覆盖的"清单外"路径 —— FR-013 约束的是**渲染**，二者不冲突。

---

## 5. `donkey.core.workspace.sqlite3_templates` —— 结构构造器（P2 新增模块）

```python
def build_sessions_sqlite(path: Path) -> None: ...
def build_store_sqlite(path: Path) -> None: ...
def build_knowledge_sqlite(path: Path) -> None: ...
```

| 能力 | 契约 |
|---|---|
| `build_sessions_sqlite` | `sqlite3.connect(path)` → `SqliteSaver(conn)` → **`saver.setup()`（实例方法）** → 建 `sessions_metadata`（6 字段）+ 2 索引 → commit → close |
| `build_store_sqlite` | **仅**创建空的 sqlite3 文件（0 表 0 索引）；MUST NOT 建占位表 |
| `build_knowledge_sqlite` | 同上 |
| 通用 | 幂等（`CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`）；任何失败 → `TemplateGenerationError`（exit 3）；MUST NOT 以裸异常逃逸 |

### 5.1 上游 saver 的使用契约（R-01 / R-04）

```python
from langgraph.checkpoint.sqlite import SqliteSaver    # 注意：不是 langgraph_checkpoint_sqlite

conn = sqlite3.connect(str(path))
try:
    saver = SqliteSaver(conn)
    saver.setup()          # 实例方法；写成 SqliteSaver.setup(conn) 会抛 AttributeError
    conn.execute("""CREATE TABLE IF NOT EXISTS sessions_metadata (...)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title ON sessions_metadata(title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at ON sessions_metadata(updated_at)")
    conn.commit()
finally:
    conn.close()
```

**上游依赖声明**：`pyproject.toml` 的 `dependencies = ["langgraph-checkpoint-sqlite>=3.1,<4"]`
（传递依赖：`langgraph-checkpoint>=4.3.0,<5.0.0` / `langchain-core>=0.2.38` / `aiosqlite>=0.20` / `sqlite-vec>=0.1.6`）。

> ⚠️ **版本陷阱**：本机用户级 site-packages 存在 `sqlite 3.1.1` + `checkpoint 4.2.0` 的**不兼容组合**，导入即
> `ImportError: cannot import name 'writes_sort_key'`。故版本下界 MUST 取 `>=3.1`，且安装后 MUST 立即跑冒烟验证（quickstart §1）。

### 5.2 `sessions_metadata` 的 DDL（逐字取自 `harness/report/sessions_sqlite表结构一览.md` §2.2）

```sql
CREATE TABLE IF NOT EXISTS sessions_metadata (
    thread_id      TEXT  PRIMARY KEY,
    title          TEXT  NOT NULL,
    created_at     REAL  NOT NULL,
    updated_at     REAL  NOT NULL,
    donkey_version TEXT  NOT NULL,
    first_prompt   TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title    ON sessions_metadata(title);
CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at ON sessions_metadata(updated_at);
```

### 5.3 安装包 MUST NOT 携带二进制 sqlite3 模板

`donkey/core/workspace/templates/` 下 MUST NOT 存在任何 `.sqlite3` / `.db` 二进制文件（spec FR-030 / 宪法 D-05）。
所有 schema 由上述 builder 程序化构造。

---

## 6. 分层边界（本 Phase MUST 保持）

| 层 | MAY import | MUST NOT import |
|---|---|---|
| `donkey/core/**` | 标准库、`langgraph.checkpoint.sqlite`（**仅** `sqlite3_templates.py`）、`donkey.core.*` | `donkey.cli` / `donkey.web` / `donkey.gui`、`argparse` / `sys.argv` / `click` / `typer`、`langsmith`（任何形态） |
| `donkey/cli/**` | 标准库、`donkey.core.*` | `langchain` / `langgraph` / `sqlite3`（N-04）、`langsmith` |

**MUST NOT import 清单**（宪法 N-12 / §3.2）：`langsmith`（及其任何子包）、`langsmith.*`、`deepagents`、`ShellToolMiddleware`、任何 subagent 相关模块。

---

## End of library-api contract.
