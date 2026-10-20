# F001-P2 `template_skeleton` —— `/speckit.specify` 开发提示词

> 本文件是 `donkey init` F001 第 2 个 Phase 的 **spec 输入**。把它整体作为参数传入 `/speckit.specify` 命令即可生成 `specs/001-donkey-init-workspace/phase-2-template-skeleton/spec.md`。
>
> **自包含契约**：本提示词包含完整的 Phase 范围、入口条件、退出条件、约束、实现要点；执行 `/speckit.specify` 时**无需**翻阅 `harness/features/` 内其他 F001 兄弟 Phase 提示词文件、也**无需**翻阅立项书 / README / 调研报告——所有必要信息均已内化在本文件内。本文件对其他 F001 Phase 的引用仅限于"Phase 标识符"层面（例如"由 F001-P1 提供"），**不**复制其 spec 内容——但会在本文件中以独立小节复述必要的接口契约（如 `validate_init_request` / `check_path` / `check_permission` / `load_template_manifest` 的函数行为），避免跨文件依赖。
>
> 本提示词**不**描述 `/speckit.plan` / `/speckit.tasks` / `/speckit.implement` / `/speckit.analyze` 的细节——那些命令是 spec 的下游延伸，由 Speckit 工作流按 `harness/prompt/speckit.md` 串行处理即可，本 Phase 不提前撰写。

---

## 0. Phase 元信息

| 字段 | 值 |
|---|---|
| **Feature 编号** | F001（`donkey init`） |
| **核心库 API** | `core.api.init_workspace(path, name=None, force=False) -> InitResult` |
| **Phase 编号** | F001-P2 |
| **Phase 英文名** | `template_skeleton` |
| **Phase 中文描述** | 幂等生成 workspace 模板骨架（六大必填目录 + 必填文件 + 支撑文件）+ workspace manifest 写入 |
| **段位** | F001 段位 1–10；本 Phase 占用 F001 子段 2（exit 3） |
| **已用 exit code** | 3（`TemplateGenerationError`） |
| **预留 exit code** | 5–10（留给 v1.x 试运行期新错误） |
| **本 Phase 不占用的 exit code** | 1 / 2（F001-P1 已用）、4（F001-P3 用）、5–10 |
| **对应验收脚本** | `tests/e2e/phase/verify_phase_f001_p2.py` |
| **闭环复杂度（断言数）** | 中（15 断言） |
| **准入条件** | F001-P1 退出条件全部满足 + F001-P1 抛出的 2 个异常类已通过单元测试 |

---

## 1. Phase 目标声明（一句话）

实现 `donkey init` 的模板骨架幂等生成：在 workspace 内落地六大必填目录（`tools/` / `mcp/` / `skills/` / `memory/`）+ 必填文件（`instruction.md` / `provider.toml` / `mcp/mcp.json` / `skills/example/SKILL.md`）+ 支撑文件（README 系列 / `.gitignore`）+ **三个 sqlite3 模板**（`memory/sessions.sqlite3` schema-built（SqliteSaver + sessions_metadata）/ `memory/store.sqlite3` 空文件占位（schema 推迟 v3 SqliteStore 实施）/ `memory/knowledge.sqlite3` 空文件占位（schema 推迟 RAG 引擎选型）；详见 §4.7.6 schema builder），并维护 workspace manifest。本 Phase **不**生成 3 个内置 `@tool` 文件（推迟到 F001-P3），**不**生成 Skills example 的 Level 2/3 内容（推迟到 F001-P3），**不**做"init 后跑 F002 静态检查"（F002 域）。

---

## 2. 背景与设计意图（实现者必须先理解）

### 2.1 项目身份

donkey 是一个**智能体材料层的可移植运行时引擎**——workspace 目录 = 智能体的全部材料层（人格、知识、手脚、大脑），用户可任意替换；Agent Loop、中间件挂载、客户端渲染、上下文治理等由引擎统一实现，不开放配置；改引擎层需 fork 仓库。

### 2.2 两层模型

- **材料层**（workspace 层）：Instructions / Model / Tools / Skills，由用户定义（一个目录），可移植性高；
- **引擎层**（harness / runtime 层）：Agent Loop、中间件链、客户端渲染、上下文治理，由 `donkey` 代码定义，**无任何配置项**。

### 2.3 workspace 原子性原则

- 一个 workspace 目录 = 一个 Agent，workspace 自带 manifest；
- 依赖与配置随 workspace 走；运行数据可选择性导出；
- workspace 有格式版本号，donkey 升级时提供迁移路径。

### 2.4 路径绝对化原则

workspace 内的所有相对路径引用**以 workspace 绝对路径为唯一根**；不依赖进程 cwd / HOME / 属主隐藏目录约定。

### 2.5 `donkey init` 的幂等性四场景（核心）

`donkey init` **必须幂等**（"无则增，有则跳过"）。下面是 4 种典型场景与对应行为：

| 场景 | 命令 | workspace 状态 | 行为 | exit |
|---|---|---|---|---|
| **1. 全新创建** | `donkey init /tmp/ws` | 目录不存在 | 新建全部目录 + 全部模板文件 | 0 |
| **2. 幂等补齐**（最常用） | `donkey init /tmp/ws` | 目录存在 | **遍历模板清单**：缺失的补齐；已存在的**完全不动**；用户内容（非模板）**完全不动** | 0 |
| **3. 模板重置** | `donkey init /tmp/ws --force` | 目录存在 | **遍历模板清单**：先 `delete` 每个模板文件（含子目录如 `skills/example/`），再 `create` 默认内容；用户内容**完全不动** | 0 |
| **4. 放弃重做** | （用户手动）`rm -rf /tmp/ws` + `donkey init /tmp/ws` | 目录被用户删除 | 同场景 1 | 0 |

**关键边界**：donkey 必须维护一份**模板文件清单**（位于 `donkey/core/workspace/templates/manifest.json`），列出 donkey 自动生成的所有文件路径。本 Phase 负责**驱动**该清单实现幂等渲染。

### 2.6 memory/ 模板边界（关键设计意图——`--force` 等于"恢复出厂设置"，sqlite3 是模板而非保留型运行数据）

- `memory/` 目录本身 + `memory/README.md` + **三个 sqlite3 文件**（`memory/sessions.sqlite3` / `memory/store.sqlite3` / `memory/knowledge.sqlite3`）**全部是 donkey 模板**，由 init 阶段统一预创建，纳入 `templates/manifest.json` 模板清单；
- **三个 sqlite3 模板的程序化构造**（不在包内携带二进制 sqlite3 文件，避免 schema 与代码漂移——参见 §4.7.6 schema builder）：
  - `memory/sessions.sqlite3`：init 阶段创建为带 schema 的空文件，承载 SqliteSaver 自有 `checkpoints` / `writes` 表 + donkey 自管 `sessions_metadata` 表（含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 索引）；
  - `memory/store.sqlite3`：**v1 仅占位空文件**——**不**建任何表 / 索引；schema 全部推迟到 v3 SqliteStore 实施时（Maintainer 修改 F001-P2 §4.7.6 添加 `store_items` 等建表 SQL + 同步 sessions_sqlite表结构一览.md §3 + 立项书 §4.10 TD-02 路线图）；
  - `memory/knowledge.sqlite3`：v3+ RAG / 向量库占位；当前仅创建空文件，schema 待向量引擎（sqlite-vec / faiss+sqlite）选型后正式化；
- **`--force` 行为**（"恢复出厂设置"语义）：遍历模板清单 → 删 + 重建**全部模板文件**含三个 sqlite3；SqliteSaver 历史 + `sessions_metadata` 元数据**一并清空**；**用户必须在 `--force` 前手动备份**（参见 §4.7.5 `templates/memory/README.md.txt` 模板正文示例 `cp` 命令）；
- **"运行数据可选择性导出"**仍生效：sqlite3 文件虽属模板，导出 workspace zip 时仍可按需剔除（如客户端实现 `--include-memory` flag），"模板身份" ≠ "必须导出"；
- **退出码联动**：init 阶段 sqlite3 schema 必健康；用户后续手工破坏 sqlite3（如手动编辑 / 误删表）触发 F002-P2 `SqliteSchemaError` (exit 16) —— 这正是该 exit code 现在唯一可靠的触发场景；
- **v1 不提供**"只清 messages 不清 sessions_metadata" / "只清元数据不清 messages" 的细粒度工具——sqlite3 文件整体重建，二者原子消失。

### 2.7 用户内容（donkey 不动）

- 用户自定义的 `tools/*.py`（不在清单内）；
- 用户自定义的 `skills/*/`（不在清单内）；
- 用户任意创建的目录 / 文件（如 `media/` / `videos/` / `notes/`）；
- 用户在 `memory/` 下创建的非清单文件（如 `memory/notes.md`、`memory/legacy.sqlite3`，但 **不是** `memory/sessions.sqlite3` / `store.sqlite3` / `knowledge.sqlite3` 这三个模板文件本身——这三个是 donkey 自管）。

---

## 3. 入口条件（Entry Gate）

### 3.1 前置 Phase 已完成

前置 Phase = F001-P1（`cli_validation`，段位 exit 1-2，对应 `PathNotFoundError` / `PathPermissionError`）。F001-P1 的 7 个 verify 断言（场景 1 / 2 / 3 / 4 / 5 / 6 / 7）全部 PASS。F001-P1 抛出的 2 个异常类（`PathNotFoundError` / `PathPermissionError`）的单元测试（位于 `tests/unit/test_init_workspace.py`）全绿。

### 3.2 本 Phase 不重复实现的接口契约（来自 F001-P1，本 Phase 直接复用）

下列 4 个函数已在 `donkey/core/workspace/init.py` 内由 F001-P1 实现并通过单测；F001-P2 **不**修改它们，**只**追加 `render_templates` / `init_workspace_inner` 等新函数。F001-P2 调用契约如下：

| 函数 | F001-P2 调用方式 | 返回值 / 行为 |
|---|---|---|
| `check_path(path: str \| Path) -> Path` | `validate_init_request` 内部已调；F001-P2 间接通过 `validate_init_request` 调用 | 父目录不存在 / 路径解析失败 → raise `PathNotFoundError`（exit 1）；否则返回绝对路径 `Path` |
| `check_permission(path: Path) -> None` | 同上（间接通过 `validate_init_request` 调用） | 权限不足 → raise `PathPermissionError`（exit 2）；否则 `None` |
| `load_template_manifest(manifest_path: Optional[Path] = None) -> list[dict]` | `validate_init_request` 末尾调用；F001-P2 在 `init_workspace_inner` 内**再次调用**用于驱动渲染 | 返回 manifest 条目 `list[dict]`；损坏 / 缺失 → raise `PathNotFoundError`（exit 1，归类奥卡姆合并） |
| `validate_init_request(path, name, force) -> tuple[Path, str, bool]` | F001-P2 `init_workspace_inner` 入口首行调用 | 返回 `(abs_path, resolved_name, force)` 三元组；任一前置校验失败抛 `WorkspaceInitError` 子类 |

### 3.3 提前就绪的模块资产（Phase 启动时已存在）

| 资产 | 路径 | 内容约束 |
|---|---|---|
| **核心库 API** | `donkey/core/api.py` | `init_workspace(path, name=None, force=False) -> InitResult` 函数签名已定义；**P1 实现 = 校验 + 创建 workspace 根目录 + 加载模板清单**（不渲染模板）；`InitResult` dataclass 字段顺序与类型已锁定：`workspace_path: Path` / `name: str` / `force: bool` / `templates_loaded: int` / `files_created: int` / `files_skipped: int`。本 Phase 把函数体替换为「调 `init_workspace_inner` 完成模板渲染」。 |
| **核心逻辑骨架** | `donkey/core/workspace/init.py` | 上表 4 个函数已由 F001-P1 实现并测试通过；本 Phase **复用** `validate_init_request` 的 PATH + 权限校验结果，并在其后**追加**渲染逻辑（不修改 F001-P1 已实现的 4 个函数）。 |
| **CLI 入口** | `donkey/cli/cli_client.py` | argparse + 异常处理已就位。本 Phase **不**修改 CLI 代码；`init_workspace` 函数体补齐后 CLI 自动可调用，仅需在本文件 `_EXCEPTION_TO_EXIT_CODE` 字典**追加** 1 行（见 §4.4）。 |
| **exit code 常量** | `donkey/core/exit_codes.py` | 已定义 `EXIT_CODE_OK` / `EXIT_CODE_PATH_NOT_FOUND` / `EXIT_CODE_PATH_PERMISSION`（F001-P1 用）。本 Phase 在此文件**追加**定义 `EXIT_CODE_TEMPLATE_GENERATION = 3`。 |
| **异常类层次** | `donkey/core/exceptions.py` | 已定义 `DonkeyError` / `WorkspaceInitError` / `PathNotFoundError` / `PathPermissionError`（F001-P1 用）。本 Phase 在此文件**追加**定义 `TemplateGenerationError(WorkspaceInitError)` —— 对应 exit code 3。 |
| **CLI 异常映射表** | `donkey/cli/cli_client.py` | 已存在 `_EXCEPTION_TO_EXIT_CODE` 映射表。本 Phase 在表中**追加** `TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION`（仅 1 行）。 |
| **模板清单** | `donkey/core/workspace/templates/manifest.json` | 已定义 schema（version + entries，每 entry 含 `path` + 可选 `format`：`markdown` / `toml` / `json` / `python` / `text` / `directory` / `sqlite3` 共 7 种）。**P1 阶段已有 3 条**（`instruction.md` / `provider.toml` / `mcp/mcp.json`）；**本 Phase 追加 15 条 → 累计 18 条**（追加方式：在原 `entries` 数组末尾 push，**不**修改 P1 已有条目）。 |
| **模板源文件** | `donkey/core/workspace/templates/{entry['path']}.txt` | 已就位（P1 的 3 个 .txt 占位）+ 本 Phase 新增 15 个 .txt 源。**源文件路径规则**：`templates/{entry['path']}.txt`——与 manifest entry 的 `path` 一一对应（如 `templates/mcp/mcp.json.txt` / `templates/memory/README.md.txt`）。本 Phase 读取这些 .txt 内容并写入 workspace 对应位置；初始正文见 §4.7。 |
| **sqlite3 schema builders** | `donkey/core/workspace/sqlite3_templates.py` | **本 Phase 新建**模块。本 Phase 入口条件**不要求**该模块已存在——本 Phase 自身将其创建（`build_sessions_sqlite` / `build_store_sqlite` / `build_knowledge_sqlite` 三函数），并附 3 个单测。 |


---

## 4. 实现要点（spec 必须覆盖的功能点）

### 4.1 `donkey/core/workspace/init.py` —— 追加 `render_templates()` 函数

在 P1 已有的 4 个函数**之后**追加：

```python
# donkey/core/workspace/init.py（P2 追加段）

from donkey.core.exceptions import TemplateGenerationError
from donkey.core.workspace.manifest import write_workspace_manifest
from donkey.core.workspace.sqlite3_templates import (
    build_sessions_sqlite,
    build_store_sqlite,
    build_knowledge_sqlite,
)


def render_templates(workspace_path: Path,
                     name: str,
                     force: bool,
                     manifest_entries: list[dict]) -> tuple[int, int]:
    """根据 manifest 清单幂等生成模板骨架。

    行为：
    1. 遍历 manifest_entries（每个 entry 含 path + 可选 format）：
       a. 目标路径 = workspace_path / entry['path']
       b. **根据 format 分派处理**：
          - `markdown` / `toml` / `json` / `python` / `text`：源模板 = donkey/core/workspace/templates/{entry['path']}.txt
            - 不传 force：目标不存在则写入；已存在则**完全不动**
            - 传 force：unlink 后重写
          - `directory`：处理目录条目（mkdir / 递归清空内列出的文件）
          - **`sqlite3`**：调用对应 schema builder（见 §4.7.6）程序化构造 schema-built 空文件
            - 不传 force：目标不存在则构造；已存在则**完全不动**（保留用户历史）
            - 传 force：unlink 旧文件后重新构造
       c. 任一步骤 IO 失败（PermissionError / FileNotFoundError / OSError / sqlite3.OperationalError） →
          raise TemplateGenerationError（合并项：源缺失 + 渲染失败 + 文件写入失败 + **sqlite3 schema 构造失败**）
    2. 处理 manifest 中标记为目录的 entry（如 `skills/example/`）：
       - 不传 force：目录不存在则 mkdir(parents=True, exist_ok=True)
       - 传 force：目录不存在则创建；存在则**递归清空其内 manifest 列出的文件**（不删目录本身）
    3. **绝不触碰**任何不在 manifest 内的路径（用户的 `media/` / 自定义 `tools/my_tool.py` 等）——
       **注意**：sqlite3 模板（`memory/sessions.sqlite3` 等三个）**已经纳入 manifest**，所以会被 `--force` 重置；
       用户备份责任写入 `memory/README.md`（§4.7.5）。

    返回：(files_created, files_skipped) 两元组
    """


def init_workspace_inner(path: str | Path,
                          name: str | None,
                          force: bool) -> tuple[Path, str, bool, int, int, int]:
    """init_workspace 的内部实现（被 core.api.init_workspace 调用）。

    行为：
    1. 调 validate_init_request(path, name, force) → (abs_path, resolved_name, force)
    2. 调 load_template_manifest() → manifest_entries
    3. abs_path.mkdir(parents=True, exist_ok=True)   # 建根目录（P1 语义保留）
    4. 调 render_templates(abs_path, resolved_name, force, manifest_entries) → (created, skipped)
    5. 调 write_workspace_manifest(abs_path, resolved_name, force) → 写 workspace manifest
    6. 返回 (abs_path, resolved_name, force, created, skipped, len(manifest_entries))

    异常：任一步骤失败 → raise 对应 WorkspaceInitError 子类
    """
```

**spec 要求**：

- `render_templates` 与 `init_workspace_inner` 必须是新追加的函数，**不**修改 P1 已实现的 4 个函数；
- **`format` 字段分派表**：除 `markdown` / `toml` / `json` / `python` / `text` / `directory` 外，**新增** `sqlite3` —— 触发 schema builder（§4.7.6）而非文本复制；schema builder 内部抛错统一归到 `TemplateGenerationError`；
- 异常归类（合并四项）：**源 .txt 缺失**（如 `templates/instruction.md.txt` 被用户删除）+ **渲染失败**（如 .txt 内容不合法）+ **文件写入失败**（如磁盘满、权限中途撤销）+ **sqlite3 schema 构造失败**（如 SqliteSaver.setup() 抛错 / sessions_metadata 建表失败）→ 四者**统一**抛 `TemplateGenerationError`（合并报错，理由：用户修复动作相同——重装 donkey / 检查权限 / 重试 init；按奥卡姆剃刀合并到 1 个 exit code）；
- 目录处理：`manifest.json` 中 `skills/example/` 这种目录 entry 应被识别为"目录条目"（spec 应明确 schema 中如何标记——建议 `format: "directory"` 或单独的 `type: "directory"` 字段），`render_templates` 据此区分目录 vs 文件；
- **绝不允许** `--force` 触碰 manifest 外的路径（用户的 `media/` / 自定义 `tools/my_tool.py` 等）——单元测试必须验证这一点；**sqlite3 三模板已被 manifest 收纳，`--force` 重置它们是预期行为**（用户已在 `memory/README.md` §4.7.5 模板正文中被告知备份责任）。

### 4.2 `donkey/core/workspace/manifest.py` —— workspace manifest 写入与解析

新增模块（**不要**放到 `init.py` 内，独立模块便于 F002 / F003 复用）：

```python
# donkey/core/workspace/manifest.py

WORKSPACE_MANIFEST_FILENAME = "manifest.json"  # 位于 workspace 根


def write_workspace_manifest(workspace_path: Path,
                              name: str,
                              force: bool) -> dict:
    """写入 workspace manifest。

    行为：
    1. manifest 路径 = workspace_path / WORKSPACE_MANIFEST_FILENAME
    2. **不传 force**：manifest 已存在 → 不覆盖；返回当前 manifest 内容
       （设计意图：保留原 created_at，让用户看到 workspace "创建时间"不变）
    3. **传 force**：manifest 已存在 → 覆盖（refresh created_at 为当前时间）；不存在 → 创建
    4. 字段最少化：
       - version: int（v1 填 1）
       - name: str（workspace 名称）
       - created_at: str（ISO 8601 时间戳）
       - donkey_version: str（生成 manifest 的 donkey 版本号，**禁止** import 内部 __version__；spec 应明确"从 pyproject.toml 读版本"或"硬编码 '0.1.0'"——推荐硬编码以避免循环依赖）
    5. 写入格式：json.dumps(manifest, indent=2, ensure_ascii=False)

    返回：manifest 字典
    """


def read_workspace_manifest(workspace_path: Path) -> dict | None:
    """读取 workspace manifest；不存在返回 None。

    行为：json.loads 解析；解析失败 → raise TemplateGenerationError（合并到 exit 3）
    """


def ensure_workspace_manifest(workspace_path: Path,
                               name: str,
                               force: bool) -> dict:
    """write_workspace_manifest 的便捷封装：先 read，不存在或 force 时再 write。

    设计意图：init_workspace_inner 调用此函数一次完成"确保 manifest 存在"语义。
    """
```

**spec 要求**：

- manifest 字段最少化：仅 `version` / `name` / `created_at` / `donkey_version` 四项；
- `donkey_version` 推荐硬编码 `'0.1.0'`（v0.1.0 阶段）；如未来要从 `pyproject.toml` 读，需用 `importlib.metadata.version("donkey")` 而非 import 内部 `__version__`；
- `created_at` 格式：`datetime.now(timezone.utc).isoformat()`（带时区）；
- manifest 文件必须含 UTF-8 BOM 头？——**不**含；纯 UTF-8。

### 4.3 `donkey/core/api.py` —— `init_workspace` 函数体补齐

把 P1 的「仅校验 + 建根目录」实现替换为（**模板渲染**部分）：

```python
def init_workspace(path: str | Path,
                   name: str | None = None,
                   force: bool = False) -> InitResult:
    abs_path, resolved_name, force, created, skipped, templates_loaded = init_workspace_inner(
        path=path, name=name, force=force,
    )
    return InitResult(
        workspace_path=abs_path,
        name=resolved_name,
        force=force,
        templates_loaded=templates_loaded,  # = manifest 条目数（P1 阶段为 3，P2 完成后 18，P3 完成后 25）
        files_created=created,
        files_skipped=skipped,
    )
```

**spec 要求**：

- 函数体**只**调用 `init_workspace_inner`，**不**在此处写业务逻辑（保持 api.py 极薄）；
- 返回 `InitResult` 字段顺序与类型严格按 P1 锁定值（P2 不能改 dataclass schema）；`templates_loaded` = 本次渲染的 manifest 条目数（P1 锁定语义，本 Phase 补齐实现）；
- `init_workspace_inner` 的 import 在 `api.py` 顶部（`from donkey.core.workspace.init import init_workspace_inner`）；
- `init_workspace_inner` 内部**先 `abs_path.mkdir(parents=True, exist_ok=True)`** 再渲染（保持 P1 的"建根目录"语义，避免只写子文件时的目录缺失）。

### 4.4 `donkey/cli/cli_client.py` —— 异常映射表追加 1 项

在 `_EXCEPTION_TO_EXIT_CODE` 字典中追加：

```python
TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION,  # 3
```

异常处理逻辑（main 函数中的 `try/except WorkspaceInitError`）**无需修改**——自动按 type(e) 查表。

### 4.5 `donkey/core/exit_codes.py` —— 追加 1 个常量

```python
EXIT_CODE_TEMPLATE_GENERATION = 3  # TemplateGenerationError
```

### 4.6 `donkey/core/exceptions.py` —— 追加 1 个异常类

```python
class TemplateGenerationError(WorkspaceInitError):
    """exit code: 3

    模板骨架生成失败（合并项）：
    - 源 .txt 模板缺失（如 templates/instruction.md.txt 被删除）
    - 渲染失败（如 .txt 内容格式损坏）
    - 文件写入失败（如磁盘满、权限中途撤销）

    用户修复动作相同：重装 donkey / 检查权限 / 重试 init；按奥卡姆剃刀合并到 1 个 exit code。
    """
```

### 4.7 模板源文件（`donkey/core/workspace/templates/{path}.txt`）的填充内容

P1 阶段 manifest（3 条）+ .txt 占位已就位；P2 阶段 spec **必须**列出每个 .txt 源文件的初始内容。

> **源文件路径规则**：`donkey/core/workspace/templates/{manifest entry 的 path}.txt`——与 manifest entry 一一对应。例：manifest entry `mcp/mcp.json` → 源文件 `donkey/core/workspace/templates/mcp/mcp.json.txt`。

#### 4.7.1 `instruction.md.txt`

```markdown
# {{ workspace_name }} 的系统提示词

> 本文件由 `donkey init` 生成；用户可自由编辑。

## 角色

<!-- 在此写 agent 的人格 / 行为约定 -->

## 风格

<!-- 回复语气、长度、格式偏好 -->

## 限制

<!-- 禁止行为、安全边界 -->
```

> **`{{ workspace_name }}` 占位符**：由 `render_templates` 在渲染时替换为 `--name`（缺省取 `path.basename()`）。F001-P2 §6.5 的"--name 注入"断言依赖此占位符。

#### 4.7.2 `provider.toml.txt`

```toml
# {{ workspace_name }} —— 模型配置
# 由 `donkey init` 生成；请把 REPLACE_ME 换成你真实的 API key。
# 字段契约见 harness/report/大模型toml参数设计.md §7-§8 与立项书 §4.6.2。

# 顶层：全局默认（必填）
default_provider = "openai"
default_model = "gpt-4o"

[openai]
api_key = "REPLACE_ME"   # 高敏感字段；TOML 明文，donkey 不读环境变量
api_host = ""            # 选填；自定义 OpenAI 兼容端点
temperature = 0.2
max_tokens = 128000

[openai.models.gpt-4o]
# 模型级参数覆盖 provider 默认
temperature = 0.2
```

> **占位符 `REPLACE_ME` 的理由（AC-1 静态口径，见立项书 §3.2.3）**：C 档云端 provider 的**空** `api_key` 在 F002 load 阶段是**硬错 exit 11**（调研 §9.2）——若出厂模板写 `api_key = ""`，则"刚 init 完的默认 workspace"连**静态检查**都过不了。用**非空占位符**则：① 静态检查（exit 11-14）100% 通过；② 用户替换成真实 key 后动态连通性检查（exit 15）才通过——未替换时 load 报 exit 15 并提示"请先把 provider.toml 中的 REPLACE_ME 换成真实 API key"。
>
> 完整 per-provider schema（含 26 家 provider 各自的专属字段）见 `harness/report/大模型toml参数设计.md` §7-§8 与立项书 §4.6.2。

#### 4.7.3 `mcp/mcp.json.txt`

```json
{
  "mcpServers": {}
}
```

#### 4.7.4 `skills/example/SKILL.md.txt`

```markdown
---
name: example
description: 示例 Skill —— 展示 Skills 三层模型（Level 1 frontmatter + Level 2 主体 + Level 3 reference/scripts/templates）。
---

# Example Skill（Level 2 占位）

> 本文件由 `donkey init` 自动生成，演示 Skills 三层模型。**完整正文 + Level 3 示例由 F001-P3 (`builtin_tools`) 覆盖写入**。

- **Level 1**（本文件顶部 frontmatter）：`name` + `description` 两字段必填。
- **Level 2**（frontmatter 下方的 Markdown 主体）：模型调用 `load_skill_example` 时返回的内容。
```

> **P2 只写"占位级" Level 2**：完整的 Skills 三层示例正文 + `reference/` / `scripts/` / `templates/` 三个 Level 3 示例文件由 **F001-P3** 追加（见 F001-P3 §4.6）。P3 的做法是**覆盖**本 .txt 源文件（同名覆盖）+ 新增 3 个 Level 3 的 .txt 源。

#### 4.7.5 其它 README + .gitignore 源文件

spec 必须列出每个文件的初始内容（建议长度 5–20 行）：

- `README.md.txt`：workspace 总览模板（含 workspace name 占位符）
- `tools/README.md.txt`：工具开发规范（命名 / 参数 / 错误处理 / timeout 建议）
- `mcp/README.md.txt`：MCP 配置说明
- `skills/README.md.txt`：Skills 开发规范（含三层模型说明）
- `memory/README.md.txt`（**内容详见下框**，关键设计意图：sqlite3 三模板由 `donkey init` 预创建 + `--force` 会清空 + 用户备份责任）：

  ```markdown
  # memory/

  本目录与目录内三个 sqlite3 文件**全部是 donkey 模板**——`donkey init` 阶段统一预创建，并纳入 `templates/manifest.json` 模板清单。

  - `sessions.sqlite3`（短期记忆 + 会话元数据）由 `donkey init` 阶段预创建为**带 schema 的空文件**：
    - **SqliteSaver 自有表**（`checkpoints` / `writes`）—— message 历史；schema 由 `langgraph-checkpoint-sqlite` 包管理；
    - **`sessions_metadata` 表**（donkey 自管）—— `thread_id` ↔ `title` 映射 + `created_at` / `updated_at` / `donkey_version` / `first_prompt`，含 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` 索引。`donkey session list` / `remove --title` 走此表。
  - `store.sqlite3`（长期记忆，v3 SqliteStore）：`donkey init` 阶段**仅创建空文件**——schema 全部推迟到 v3 SqliteStore 实施时（届时 Maintainer 修改 F001-P2 §4.7.6 添加 `store_items` 等建表 SQL + 同步 `harness/report/sessions_sqlite表结构一览.md` §3）。
  - `knowledge.sqlite3`（向量库，v3+ 候选）由 `donkey init` 阶段预创建空文件；schema 待向量引擎（sqlite-vec / faiss+sqlite）选型后正式化。

  **`donkey init --force` 行为**（"恢复出厂设置"语义）：上述三个 sqlite3 文件会**删 + 重建**——SqliteSaver 历史与 `sessions_metadata` 元数据**一并清空**。需要保留历史的用户在 `--force` 前手动备份即可：

  ```bash
  cp memory/sessions.sqlite3   /tmp/backup-sessions.sqlite3
  cp memory/store.sqlite3      /tmp/backup-store.sqlite3      # v3 启用后才有意义
  cp memory/knowledge.sqlite3  /tmp/backup-knowledge.sqlite3  # 向量库启用后才有意义
  donkey init /path/to/ws --force
  ```

  **"运行数据可选择性导出"**仍生效：sqlite3 文件虽属模板，导出 workspace zip 时仍可按需剔除（如客户端实现 `--include-memory` flag）。

  本目录由 `donkey init` 自动生成的 `.gitignore` 标记为忽略（`memory/*.sqlite3` + `memory/*.sqlite3-wal` + `memory/*.sqlite3-shm`）——sqlite3 文件（含 WAL / SHM 侧车）不入版本控制。
  ```
- `.gitignore.txt`：

  ```
  __pycache__/
  *.pyc
  *.pyo
  *.egg-info/
  .venv/
  venv/
  memory/*.sqlite3
  memory/*.sqlite3-wal
  memory/*.sqlite3-shm
  ```

#### 4.7.6 sqlite3 schema builders（程序化构造，不带二进制模板）

**新增模块** `donkey/core/workspace/sqlite3_templates.py`：

- **设计原则**：不在 donkey 安装包内携带任何二进制 sqlite3 文件——所有 sqlite3 schema 在 init 阶段由代码程序化构造（避免 schema 与上游 `langgraph-checkpoint-sqlite` 漂移）；
- **三个 builder 函数**（每个返回成功 / 抛 `TemplateGenerationError`）：
  - `build_sessions_sqlite(path: Path) -> None`：连接 sqlite3 → 构造 `SqliteSaver(conn)` 并调 **`saver.setup()`**（**实例方法**——`langgraph-checkpoint-sqlite` 3.x 的 `setup()` 是 `def setup(self)`，内部走 `self.conn.executescript(...)`；**不能**写成 `SqliteSaver.setup(conn)`）创建 SqliteSaver 自有 `checkpoints` / `writes` 表 → 执行 `CREATE TABLE IF NOT EXISTS sessions_metadata(...)` + 2 个索引 → commit → close。失败统一抛 `TemplateGenerationError`；
  - `build_store_sqlite(path: Path) -> None`：**仅触发空 sqlite3 文件创建，不建任何表 / 索引**——schema 全部推迟到 v3 SqliteStore 实施时（届时 Maintainer 修改本函数添加建表 SQL + 同步更新 sessions_sqlite表结构一览.md §3 + 立项书 §4.10 TD-02 路线图）；v1 该文件仅作占位（保持 workspace 模板结构稳定），不被任何运行时调用；
  - `build_knowledge_sqlite(path: Path) -> None`：连接 sqlite3 → 创建空文件，**不**预设 schema（v1 阶段 RAG 引擎选型未决）；
- **集成点**：`render_templates`（§4.1）遍历 manifest 时遇到 `format: "sqlite3"` 的 entry → 调对应 builder 函数；error class 上抛归到 `TemplateGenerationError`（exit 3）；
- **幂等性**：builder 内部用 `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` 模式，已存在的表 + 索引不会被破坏；
- **`--force` 行为**：`render_templates` 先 `unlink` 旧文件再调 builder——确保 schema 干净（不接受"保留 schema 只清数据"的污染路径）；
- **上游 schema 不由 donkey 维护**：`checkpoints` / `writes` 的列定义由 `langgraph-checkpoint-sqlite` 决定（详见 `harness/report/sessions_sqlite表结构一览.md` §2.1），donkey 只做"表存在 + 列存在"级别的健康检查。

#### 4.7.7 模板清单追加条目（P2：+15 条 → 累计 18 条）

`donkey/core/workspace/templates/manifest.json` 在 P1 已有 3 条基础上**追加**如下 15 条（追加操作 = "在原 `entries` 数组末尾 push"，**不**修改 P1 已有条目）：

```json
{
  "version": 1,
  "entries": [
    {"path": "instruction.md", "format": "markdown"},
    {"path": "provider.toml", "format": "toml"},
    {"path": "mcp/mcp.json", "format": "json"},
    {"path": "skills/example/SKILL.md", "format": "markdown"},
    {"path": "README.md", "format": "markdown"},
    {"path": "tools/README.md", "format": "markdown"},
    {"path": "mcp/README.md", "format": "markdown"},
    {"path": "skills/README.md", "format": "markdown"},
    {"path": "memory/README.md", "format": "markdown"},
    {"path": ".gitignore", "format": "text"},
    {"path": "tools", "format": "directory"},
    {"path": "mcp", "format": "directory"},
    {"path": "skills", "format": "directory"},
    {"path": "skills/example", "format": "directory"},
    {"path": "memory", "format": "directory"},
    {"path": "memory/sessions.sqlite3", "format": "sqlite3"},
    {"path": "memory/store.sqlite3", "format": "sqlite3"},
    {"path": "memory/knowledge.sqlite3", "format": "sqlite3"}
  ]
}
```

> **追加条数核对**：P2 追加 **15** 条 = 7 个文本模板（`skills/example/SKILL.md` / `README.md` / `tools/README.md` / `mcp/README.md` / `skills/README.md` / `memory/README.md` / `.gitignore`）+ 5 个目录条目（`tools` / `mcp` / `skills` / `skills/example` / `memory`）+ 3 个 sqlite3 模板；叠加 P1 的 3 条 = **累计 18 条**。F001-P3 追加 7 条后累计 **25 条**（见 F001-P3 §4.7）。


### 4.9 单元测试（`tests/unit/test_template_skeleton.py`）

**spec 必须列出**下列单测用例（**至少 12 个**）：

| 用例 | 输入 | 期望 |
|---|---|---|
| `test_render_new_file` | workspace 不存在，target file 不存在 | 创建文件；files_created=1, files_skipped=0 |
| `test_render_skip_existing_no_force` | workspace 存在，target file 已存在（用户编辑过） | 不动文件；files_created=0, files_skipped=1 |
| `test_render_force_overwrite` | force=True，target file 已存在 | 删除 + 重写 |
| `test_render_force_directory` | force=True，`skills/example/` 存在且含子文件 | 递归删除子文件后重建 |
| `test_render_skip_user_content` | workspace 含 `media/`、`tools/my_tool.py`（不在 manifest） | `--force` 不删这些 |
| `test_render_force_rebuilds_sqlite3` | workspace 含 `memory/sessions.sqlite3`（写入假数据）+ `media/` | `--force` 重建 sqlite3（含 schema 重建，数据清空）+ media/ 不动 |
| `test_render_template_source_missing` | 手动删除 `templates/instruction.md.txt` + force | raise `TemplateGenerationError` |
| `test_render_permission_denied_midway` | workspace 在写到一半时权限被撤销 | raise `TemplateGenerationError`（合并项） |
| `test_manifest_write_new` | 新 workspace | 写入 manifest.json |
| `test_manifest_skip_existing_no_force` | manifest 已存在，无 force | 不覆盖；保留 created_at |
| `test_manifest_refresh_force` | manifest 已存在，force=True | 覆盖；created_at 更新 |
| `test_manifest_field_minimal` | manifest 内容 | 仅含 version / name / created_at / donkey_version 4 字段 |

### 4.10 verify 脚本（`tests/e2e/phase/verify_phase_f001_p2.py`）

**黑盒测试**（禁止 import `donkey.*` 业务代码；只跑 `subprocess.run(["donkey", ...])`），15 个断言对应 §6 退出条件。

---

## 5. 异常退出码表（Phase 全量 Error class 映射）

| Error class（`donkey.core.exceptions`） | exit code | 触发条件 | 报错概率 |
|---|---|---|---|
| `TemplateGenerationError` | **3** | 模板骨架生成失败（**合并四项**：源 .txt 缺失 + 渲染失败 + 文件写入失败 + **sqlite3 schema 构造失败**）。用户修复动作相同：重装 donkey / 检查权限 / 重试 init；按奥卡姆剃刀合并到 1 个码值 | 低（init 阶段罕见） |
| exit 4 | （预留） | `BuiltinToolGenerationError` —— 段位 1-10 子段 3，由下游 F001-P3 (`builtin_tools`) 分配 | — |
| exit 5–10 | （预留） | 留给 v1.x 试运行期新错误 | — |

**奥卡姆剃刀原则**：本 Phase 仅占 1 个码值（3）。源缺失 / 渲染失败 / 写入失败 / **sqlite3 schema 构造失败**四者对用户而言都是"重装 donkey / 检查权限 / 重试 init"，合并为单一 `TemplateGenerationError` —— 若分开分配会浪费 3 个码值给稀有错误。

---

## 6. 退出条件（Exit Gate）

**`tests/e2e/phase/verify_phase_f001_p2.py` 必须跑通以下 15 个断言**（顺序固定，每条独立可测）：

### 6.1 场景 1：全新创建 → exit 0 + 目录树一致 + 三个 sqlite3 模板就位

```python
def test_scenario_1_new_workspace_full_tree(tmp_path):
    """场景 1：全新创建 → exit 0；目录树与设计一致；三个 sqlite3 schema-built 模板就位"""
    ws = tmp_path / "ws"
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    # 必填文件
    assert (ws / "instruction.md").exists()
    assert (ws / "provider.toml").exists()
    assert (ws / "README.md").exists()
    assert (ws / ".gitignore").exists()
    # 必填目录
    assert (ws / "tools").is_dir()
    assert (ws / "mcp").is_dir()
    assert (ws / "skills").is_dir()
    assert (ws / "memory").is_dir()
    # 子文件
    assert (ws / "mcp" / "mcp.json").exists()
    assert (ws / "skills" / "example" / "SKILL.md").exists()
    assert (ws / "memory" / "README.md").exists()
    # 支撑文件
    assert (ws / "tools" / "README.md").exists()
    assert (ws / "mcp" / "README.md").exists()
    assert (ws / "skills" / "README.md").exists()
    # 三个 sqlite3 模板（schema-built 空文件）必须存在
    assert (ws / "memory" / "sessions.sqlite3").exists()
    assert (ws / "memory" / "store.sqlite3").exists()
    assert (ws / "memory" / "knowledge.sqlite3").exists()
    # manifest
    assert (ws / "manifest.json").exists()
```

### 6.2 provider.toml 用 tomllib 解析无异常

```python
def test_scenario_2_provider_toml_valid(tmp_path):
    """生成的 provider.toml 可被 tomllib 解析，且顶层含 default_provider / default_model"""
    import tomllib
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    data = tomllib.loads((ws / "provider.toml").read_text(encoding="utf-8"))
    # 顶层两个全局字段（立项书 §4.6.2 / 调研 §7.2）
    assert "default_provider" in data
    assert "default_model" in data
    # per-provider 独立节
    assert data["default_provider"] in data
    assert "api_key" in data[data["default_provider"]]
```

### 6.3 mcp/mcp.json 用 json.loads 解析无异常

```python
def test_scenario_3_mcp_json_valid(tmp_path):
    """生成的 mcp/mcp.json 可被 json.loads 解析"""
    import json
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    data = json.loads((ws / "mcp" / "mcp.json").read_text(encoding="utf-8"))
    assert "mcpServers" in data
```

### 6.4 SKILL.md frontmatter 合法

```python
def test_scenario_4_skill_frontmatter_valid(tmp_path):
    """生成的 skills/example/SKILL.md frontmatter 含 name + description"""
    # spec 推荐用 python-frontmatter 解析；若无依赖可用纯文本解析
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    text = (ws / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: example" in text
    assert "description:" in text
```

### 6.5 `--name=foo` 注入

```python
def test_scenario_5_name_injection(tmp_path):
    """--name=foo 注入后，README 标题与 provider.toml 注释含 'foo'"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws), "--name", "foo"], check=True, capture_output=True)
    readme = (ws / "README.md").read_text(encoding="utf-8")
    assert "foo" in readme
    provider = (ws / "provider.toml").read_text(encoding="utf-8")
    assert "foo" in provider  # 注释中含 workspace name（{{ workspace_name }} 占位符已被替换）
    manifest = json.loads((ws / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "foo"
```

### 6.6 场景 2 幂等：用户编辑过的 instruction.md 不被覆盖

```python
def test_scenario_6_idempotent_no_force(tmp_path):
    """场景 2：已存在 ws，用户编辑过 instruction.md，init 后内容不变"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    custom_content = "# 用户自定义 instruction\n我的 agent"
    (ws / "instruction.md").write_text(custom_content, encoding="utf-8")
    mtime_before = (ws / "instruction.md").stat().st_mtime

    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "instruction.md").read_text(encoding="utf-8") == custom_content
    assert (ws / "instruction.md").stat().st_mtime == mtime_before  # mtime 也不变
```

### 6.7 场景 2 子操作：损坏恢复（用户删除文件后 init 补齐）

```python
def test_scenario_7_corruption_recovery(tmp_path):
    """场景 2 子操作：rm instruction.md 后 init 补齐"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    (ws / "instruction.md").unlink()

    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "instruction.md").exists()  # 已补齐
```

### 6.8 场景 3 模板重置：--force 覆盖用户编辑过的文件

```python
def test_scenario_8_force_overwrites(tmp_path):
    """场景 3：--force 恢复 instruction.md 出厂内容"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    (ws / "instruction.md").write_text("用户自定义", encoding="utf-8")

    result = subprocess.run(["donkey", "init", str(ws), "--force"], capture_output=True, text=True)
    assert result.returncode == 0
    content = (ws / "instruction.md").read_text(encoding="utf-8")
    assert "用户自定义" not in content  # 已恢复出厂
```

### 6.9 场景 3 完整验证：用户自建目录与文件不动

```python
def test_scenario_9_force_preserves_user_content(tmp_path):
    """场景 3：--force 不动用户的 media/ 与 donkey.log"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    (ws / "media").mkdir()
    (ws / "media" / "video.mp4").write_bytes(b"fake")
    (ws / "donkey.log").write_text("user log", encoding="utf-8")

    result = subprocess.run(["donkey", "init", str(ws), "--force"], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "media").exists()
    assert (ws / "media" / "video.mp4").exists()
    assert (ws / "donkey.log").read_text(encoding="utf-8") == "user log"
```

### 6.10 场景 4：手动 rm -rf 后 init 同场景 1

```python
def test_scenario_10_rm_then_init(tmp_path):
    """场景 4：rm -rf ws 后 init → exit 0，同场景 1"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    import shutil
    shutil.rmtree(ws)

    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "instruction.md").exists()
```

### 6.11 源 .txt 缺失 → exit 3

```python
def test_scenario_11_template_source_missing(tmp_path, monkeypatch):
    """删除 templates/instruction.md.txt 后 --force → exit 3"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    # 用 monkeypatch 把模板源文件路径指向不存在的路径
    # 或直接在 donkey 安装目录删 templates/instruction.md.txt（更脆弱，但更真实）
    src = Path("donkey/core/workspace/templates/instruction.md.txt")
    src_backup = src.read_bytes()
    try:
        src.unlink()
        result = subprocess.run(["donkey", "init", str(ws), "--force"], capture_output=True, text=True)
        assert result.returncode == 3
        assert "TemplateGenerationError" in result.stderr or "模板" in result.stderr
    finally:
        src.write_bytes(src_backup)
```

### 6.12 不生成内置 @tool 文件

```python
def test_scenario_12_no_builtin_tools_yet(tmp_path):
    """P2 不生成 tools/filesystem.py 等内置 @tool（属于 P3）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    # P2 阶段：tools/ 目录存在但不含 builtin 工具文件（推迟到 P3）
    # 或：tools/ 目录存在且含 tools/README.md（支撑文件 P2 已生成）
    assert not (ws / "tools" / "filesystem.py").exists()
    assert not (ws / "tools" / "commandline.py").exists()
    assert not (ws / "tools" / "webfetch.py").exists()
    assert not (ws / "tools" / "__init__.py").exists()
```

### 6.13 不做 F002 静态检查

```python
def test_scenario_13_no_f002_static_check(tmp_path):
    """P2 init 完成后不跑 F002 静态检查（属 F002 域）"""
    ws = tmp_path / "ws"
    # 即使故意写错 provider.toml 也不应在 init 阶段报错（init 只生成模板，不校验内容）
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0  # init 不校验 provider.toml 内容
    # F002 才会校验
```

### 6.14 memory/ 模板边界：`--force` 等于"恢复出厂设置"——sqlite3 三模板被重建

```python
def test_scenario_14_force_rebuilds_sqlite3_templates(tmp_path):
    """用户首次 init → 含 sqlite3 三模板；用户备份后 --force → 三模板被重建（schema 重建，数据清空）"""
    import shutil
    import sqlite3
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sessions_file = ws / "memory" / "sessions.sqlite3"
    assert sessions_file.exists()  # 模板已就位

    # 用户手工模拟"用户在 sqlite3 写入数据"：插一条 sessions_metadata 记录
    conn = sqlite3.connect(str(sessions_file))
    try:
        conn.execute(
            "INSERT INTO sessions_metadata"
            "(thread_id, title, created_at, updated_at, donkey_version, first_prompt) "
            "VALUES ('t1', '用户会话', 0, 0, '0.1.0', 'hello')"
        )
        conn.commit()
    finally:
        conn.close()

    # 用户先备份，再 --force
    backup = tmp_path / "sessions.backup.sqlite3"
    shutil.copy2(sessions_file, backup)

    result = subprocess.run(
        ["donkey", "init", str(ws), "--force"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert sessions_file.exists()  # 文件仍存在（被重建）

    # 重建后：schema 完好（重建成功）且数据已清空（--force = 恢复出厂设置）
    conn = sqlite3.connect(str(sessions_file))
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "checkpoints" in tables
        assert "writes" in tables
        assert "sessions_metadata" in tables
        count = conn.execute("SELECT COUNT(*) FROM sessions_metadata").fetchone()[0]
        assert count == 0, "--force 重建后 sessions_metadata 应为空"
    finally:
        conn.close()

    # 备份文件不受影响（用户数据安全）
    assert backup.exists() and backup.stat().st_size > 0

    # memory/README.md 应被恢复出厂内容
    readme = (ws / "memory" / "README.md").read_text(encoding="utf-8")
    assert "sessions.sqlite3" in readme
    assert "--force" in readme  # 模板正文中提到 --force 备份要点
```

### 6.15 init 后三个 sqlite3 模板存在 + sessions.sqlite3 带正确 schema

```python
def test_scenario_15_sqlite3_templates_with_schema(tmp_path):
    """init 后 memory/ 三个 sqlite3 文件全部存在；sessions.sqlite3 schema 检查（含 SqliteSaver 表 + sessions_metadata + 索引）"""
    import sqlite3
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)

    # 三个 sqlite3 模板全部存在
    assert (ws / "memory").is_dir()
    assert (ws / "memory" / "README.md").exists()
    assert (ws / "memory" / "sessions.sqlite3").exists()
    assert (ws / "memory" / "store.sqlite3").exists()
    assert (ws / "memory" / "knowledge.sqlite3").exists()

    # sessions.sqlite3 schema 检查
    conn = sqlite3.connect(str(ws / "memory" / "sessions.sqlite3"))
    try:
        # SqliteSaver 自有表
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert "checkpoints" in tables, "SqliteSaver.checkpoints 表缺失"
        assert "writes" in tables, "SqliteSaver.writes 表缺失"
        # donkey 自管 sessions_metadata 表
        assert "sessions_metadata" in tables, "donkey.sessions_metadata 表缺失"
        # sessions_metadata 索引
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sessions_metadata'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_sessions_metadata_title" in indexes, "title 索引缺失"
        assert "idx_sessions_metadata_updated_at" in indexes, "updated_at 索引缺失"
        # sessions_metadata 表为空
        count = conn.execute("SELECT COUNT(*) FROM sessions_metadata").fetchone()[0]
        assert count == 0, "init 阶段 sessions_metadata 应为空"
    finally:
        conn.close()
```

### 6.16 退出条件总览

verify_phase_f001_p2.py 的 15 个 `test_*` 函数全部 PASS → F001-P2 完成。F001-P2 完成时，`--force` 等于"恢复出厂设置"语义 + 三个 sqlite3 模板（含 sessions.sqlite3 完整 schema + store/knowledge 占位空文件）已落地；为下一 Phase（F001-P3 = `builtin_tools`）的入口条件做好铺垫。

---

## 7. 可执行测试命令列表（"Phase 完成" 的硬性证据）

按以下顺序执行，全部 PASS 即视为 Phase 完成：

1. **前置 Phase 套件（F001-P1）**：
   ```bash
   pytest tests/e2e/phase/verify_phase_f001_p1.py -v
   pytest tests/unit/test_init_workspace.py -v
   ```
   必须全绿（验证 F001-P1 退出条件未被破坏）。

2. **本 Phase 套件**：
   ```bash
   pytest tests/unit/test_template_skeleton.py -v    # 至少 12 个
   pytest tests/e2e/phase/verify_phase_f001_p2.py -v  # 15 个
   ```

3. **静态检查**：
   ```bash
   ruff check donkey/ tests/
   mypy donkey/ tests/
   ```

4. **CLI 手动冒烟（可选）**：
   ```bash
   donkey init /tmp/test-ws
   cat /tmp/test-ws/manifest.json  # 含 name + created_at
   rm /tmp/test-ws/instruction.md && donkey init /tmp/test-ws  # 应补齐
   donkey init /tmp/test-ws --force  # 应恢复出厂
   ```

5. **完整 CI 套件**：
   ```bash
   pytest tests/ -v
   ```
   F001-P1 + F001-P2 全部测试 PASS；其它 Phase 的测试允许 FAIL。

---

## 8. 绝对不做清单（推迟到后续 Phase / Feature）

| 不做的内容 | 推迟到 |
|---|---|
| 3 个内置 `@tool` 文件（`tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py`）生成 | F001-P3 (`builtin_tools`) |
| `tools/__init__.py` | F001-P3 (`builtin_tools`) |
| Skills example 的 Level 3 内容（`skills/example/reference/` / `scripts/` / `templates/`） | F001-P3 (`builtin_tools`) |
| Skills example Level 2 完整正文（仅占位 `name` + `description` 即可） | F001-P3 (`builtin_tools`) |
| 端到端集成预演（`from tools.filesystem import read_file` 等 import 验证） | F001-P3 (`builtin_tools`) |
| `donkey load` / `donkey session` / `donkey run` 等其它子命令 | F002 / F003 / F004 |
| 任何 LangChain 中间件挂载（`FilesystemFileSearchMiddleware` 等） | F004 (`donkey run`) |
| 任何 `init_chat_model` / 模型连通性测试 | F002 (`donkey load`) |
| 解析 / 校验 `provider.toml` 内容 | F002 (`donkey load`) |
| 解析 / 校验 `mcp/mcp.json` 内容 | F002 (`donkey load`) |
| 解析 / 校验 `skills/*/SKILL.md` 内容（除本 Phase 验证 frontmatter 存在性外） | F002 (`donkey load`) |
| "init 后跑 F002 静态检查" | F002 域 |
| workspace 路径 basename 命名校验（v1 不引入） | v2+ |
| `donkey load` / `donkey run` 集成测试 | F002 / F004 |

---

## 9. 技术栈与依赖硬约束

- **Python 3.11+**（`tomllib` 内置；本 Phase 使用 `pathlib` / `json` / `shutil` / `datetime` / 标准库；**不**引入第三方依赖——tomllib 与 json 由标准库提供）；
- **测试**：pytest；建议增加 `python-frontmatter` 用于 SKILL.md frontmatter 解析测试（如不引入，可用纯文本 split 解析）；
- **静态检查**：ruff + mypy；
- **CI**：GitHub Actions。

### 9.1 永不使用清单

- ❌ LangSmith 任何形态（详见 N-12）；
- ❌ deepagents 包；
- ❌ ShellToolMiddleware；
- ❌ subagent / 子智能体任何目录或字段。

### 9.2 分层架构硬约束（N-01 ~ N-12）

| 编号 | 条款 | 本 Phase 落地 |
|---|---|---|
| **N-01** | workspace 内禁止 `agent.py` / `main.py` | ✓ 本 Phase 生成的全部模板不含这些 |
| **N-03** | `donkey.core` 禁止 import `cli` / `web` / `gui` | ✓ `core/workspace/init.py` / `manifest.py` / `api.py` 仅 import 标准库 + 内部模块 |
| **N-04** | `cli` 禁止直接 import `langchain` / `langgraph` / `sqlite3` | ✓ 本 Phase 不修改 `cli/cli_client.py` 业务逻辑（仅追加异常映射 1 行） |
| **N-05** | `donkey.core` 禁止 import `argparse` / `sys.argv` / `click` / `typer` | ✓ |
| **N-08** | exit code 段位不重叠 | ✓ 本 Phase 占 exit 3，落在 F001 段位 1–10 内 |
| **N-12** | 禁止 LangSmith | ✓ |

---

## 10. 验收标准（business AC）

| 验收项 | 说明 |
|---|---|
| **AC-3（init 幂等）** | 重复执行 `donkey init <已存在 ws>` 不破坏已存在文件（除非 `--force`）。本 Phase 通过 render_templates 的"已存在跳过 / --force 覆盖"逻辑落地。 |
| **技术验收** | F001 段位 1–10 中 exit 3（`TemplateGenerationError`）实测通过；P1 的 exit 1 / 2 不被破坏；exit 4 / 5–10 在本 Phase 不触发。 |
| **workspace 原子性** | 一个 workspace = 一个 Agent；manifest 含 4 字段；sqlite3 三模板**已被 manifest 收纳**，`--force` 会清空 + 重建（含 schema），用户备份责任由 `memory/README.md` 模板正文告知。 |

---

## 11. Spec 输出格式要求（给 `/speckit.specify` 的提示）

执行 `/speckit.specify` 后生成的 `specs/001-donkey-init-workspace/phase-2-template-skeleton/spec.md` **必须**包含：

1. **User Stories**：按优先级 P1 → P15 列出 15 个核心场景（对应 §6 的 15 个 verify 断言）；
2. **Functional Requirements (FR-001 ~ FR-NNN)**：覆盖 §4 的 10 个子节（4.1 ~ 4.10）；FR 中如需引用 F001-P1 已实现的函数（`check_path` / `check_permission` / `load_template_manifest` / `validate_init_request`），仅引用**函数签名与行为契约**，不复述其实现细节（详见 §3.2 函数契约小节）；
3. **Edge Cases**：本 Phase 边界条件（用户编辑过模板 / 用户删除模板 / 用户删除源 .txt / 用户手动 rm -rf / sqlite3 文件被 touch 等）；
4. **Success Criteria (SC-001 ~ SC-NNN)**：可量化的退出条件（"15 个 verify 断言全部 PASS"、"F001-P1 7 个断言仍全绿"、"ruff + mypy 零 error"等）；
5. **Key Entities**：`TemplateGenerationError` 异常类、`workspace manifest` 字典结构、模板清单 `manifest.json` schema；
6. **Assumptions**：F001-P1 (`cli_validation`) 已完成；`donkey/core/workspace/templates/*.txt` 已就位（占位 / 实际内容均可）；F002 / F003 / F004 域不存在。

**Spec 禁止**包含的内容（留给 `/speckit.plan` 处理）：

- 具体实现步骤（如"先实现 render_templates 再实现 manifest.py"）—— plan 才规定顺序；
- 测试用例的具体代码（除 §6 / §4.8 中已作为参考示例给出的）；
- 依赖包版本号。

---

**End of F001-P2 spec input.** 将本文件整体作为参数传入 `/speckit.specify` 即可。
