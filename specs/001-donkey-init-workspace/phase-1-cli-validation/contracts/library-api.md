# 契约：核心库 API（`core.api.init_workspace`）

**版本**：v1（F001-P1 冻结；F002 / F003 / F004 依赖此契约）
**所有者**：`donkey/core/api.py` + `donkey/core/workspace/init.py`
**上游**：`spec.md` FR-005 ~ FR-017、FR-025 ~ FR-027；澄清决策 2 / 6

---

## 1. 门面 API

```python
def init_workspace(path: str | Path,
                   name: str | None = None,
                   force: bool = False) -> InitResult: ...
```

| 参数 | 类型 | 语义 |
|---|---|---|
| `path` | `str \| Path` | workspace 根目录路径；绝对或相对均可；内部统一解析为绝对路径 |
| `name` | `str \| None` | 缺省 `None` → 名称取解析后路径的末段名。显式传入**非空字符串** → 以该值为准；传入空字符串视为未指定 → 回落解析后路径的末段名。**v1 的 CLI 通道永不传该参数**（spec FR-003 / FR-005），故命令行名称恒由路径派生；形参保留仅为维持立项书 D-1 的稳定签名 |
| `force` | `bool` | 是否请求强制重置；P1 仅记录 |

**返回**：`InitResult`（见下）。

**失败**：抛出 `WorkspaceInitError` 的子类（`PathNotFoundError` / `PathPermissionError`）。核心层 MUST NOT 返回退出码、MUST NOT 打印、MUST NOT 退出进程（宪法 N-05）。

## 2. `InitResult`

```python
@dataclass(frozen=True)
class InitResult:
    workspace_path: Path   # 绝对路径
    name: str              # workspace 名称（未指定时为路径末段派生值；库 API 显式传入时以其为准）
    force: bool            # 是否请求强制重置
    templates_loaded: int  # P1 = 0
    files_created: int     # P1 = 0
    files_skipped: int      # P1 = 0
```

**不变量**：不可变；`workspace_path` 为绝对路径；P1 阶段后三个计数恒为 `0`；`name` 在**未指定**（`None` / 空串）时 == `workspace_path.name`，显式指定非空值时 == 该值（spec FR-005 / FR-017）；CLI 通道恒 == `workspace_path.name`。

## 3. 校验能力（`core.workspace.init`）

| 函数 | 签名 | 返回 | 失败 |
|---|---|---|---|
| `check_path` | `(path: str \| Path) -> Path` | 解析后的绝对路径 | `PathNotFoundError` |
| `check_permission` | `(path: Path) -> None` | `None`（正常返回）/ 抛 `PathPermissionError` | `PathPermissionError` |
| `validate_init_request` | `(path: str \| Path, name: str \| None, force: bool) -> tuple[Path, str, bool]` | `(绝对路径, 名称, force)` | 上述两类 |

### 3.1 `check_path` 契约

1. 接受 `str` 或 `Path`，统一解析为绝对路径（相对路径以进程工作目录为基准）；
2. 父目录不存在 → `PathNotFoundError`；
3. 路径含非法字符（NUL）→ `PathNotFoundError`（`resolve()` 抛 `ValueError`，MUST 捕获转换）；
4. **解析后末段名为空**（文件系统根 / 盘符根 / UNC 共享根）→ `PathNotFoundError`；
5. 不检查"目标是否已存在"（幂等：已存在不是错误）；
6. 不检查权限（由 `check_permission` 负责）；
7. MUST 无副作用（不写文件、不建目录）；
8. 全部 stat 类调用（`exists()` / `is_dir()` / `stat()`）MUST 置于 `try/except OSError → PathNotFoundError` 内——Python 3.11+ 的 `Path.exists()` 在超长路径上**抛出** `OSError(ENAMETOOLONG)`（不返回 False）；「路径过长」MUST NOT 依赖 `resolve()` 抛错来覆盖（`Path.resolve(strict=False)` 不抛错），否则该分支永不可达且会漏出未捕获异常堆栈（spec FR-030 / 契约 C-06）。

### 3.2 `check_permission` 契约

1. 目标**不存在** → 校验**父目录**的写权限 + 执行权限（能否在其中创建子项）；
2. 目标**已存在** → 校验**目标自身**的读 + 写 + 执行权限；
3. 任一不足 → `PathPermissionError`；
4. 错误信息 MUST 含"缺失哪种权限"（读 / 写 / 执行）+ "对哪个路径缺失"，**且 MUST 含一条用户可执行的下一步（"调整权限"）**（spec FR-019 / SC-012 扩写后版本）；
5. 判定使用 `os.access(path, mode)`；`0o555` 目录（无写位）即被拒——**CI 以此方式模拟，不依赖特权账号**（`research.md` R-04）；
6. MUST 无副作用。

### 3.3 `validate_init_request` 契约

串联"路径解析 → 权限校验 → 名称定夺"；名称定夺规则为 —— `name` 为 `None` 或空串时 MUST 取解析后路径的末段名，`name` 为非空串时 MUST 采用该值（spec FR-005 / FR-017）；CLI 入口 MUST NOT 提供任何命名输入通道（命令行场景下名称恒由路径末段派生）；MUST NOT 把"目标已存在"当错误。

## 4. 边界行为

| 输入 | 行为 | 退出码（经 CLI） |
|---|---|---|
| 新路径（父目录存在） | 创建根目录 | `0` |
| 已存在 workspace | 不报错、不改动 | `0` |
| 已存在 workspace + `--force` | 同上（P1 不重置） | `0` |
| 父目录不存在 | `PathNotFoundError` | `1` |
| 根路径 / 盘符根 / UNC 共享根 | `PathNotFoundError`（末段名为空） | `1` |
| 空字符串路径 | `PathNotFoundError` | `1` |
| 目标存在但不是目录 | `PathNotFoundError` | `1` |
| 父目录只读（`0o555`） | `PathPermissionError` | `2` |
| 目标已存在但缺读 / 写 / 执行位 | `PathPermissionError` | `2` |
| 模板清单 / 模板源缺失 | **不失败**（P1 不加载清单） | `0` |

## 5. 分层约束（宪法）

- `donkey.core` MUST NOT import `argparse` / `sys.argv` / `click` / `typer`（N-05）；
- `donkey.core` MUST NOT import 任何客户端层（cli / web / gui）（N-03）；
- `donkey.cli` MUST NOT 直接 import `langchain` / `langgraph` / `sqlite3`（N-04）；
- 客户端层 MUST 只通过本门面 API 触达文件系统行为（三端共用，N-11 / D-08）。
