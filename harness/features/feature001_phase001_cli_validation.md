# F001-P1 `cli_validation` —— `/speckit.specify` 开发提示词

> 本文件是 `donkey init` F001 第 1 个 Phase 的 **spec 输入**。把它整体作为参数传入 `/speckit.specify` 命令即可生成 `specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md`。
>
> **自包含契约**：本提示词包含完整的 Phase 范围、入口条件、退出条件、约束、实现要点；执行 `/speckit.specify` 时**无需**翻阅 `harness/features/` 内其他 F001 兄弟 Phase 提示词文件、也**无需**翻阅立项书 / README / 调研报告的对应章节——所有必要信息均已内化在本文件内。本文件对其他 F001 Phase 的引用仅限于"Phase 标识符"层面（例如"推迟到 F001-P2"），**不**复制其 spec 内容。
>
> 本提示词**不**描述 `/speckit.plan` / `/speckit.tasks` / `/speckit.implement` / `/speckit.analyze` 的细节——那些命令是 spec 的下游延伸，由 Speckit 工作流按 `harness/prompt/speckit.md` 串行处理即可，本 Phase 不提前撰写。

---

## 0. Phase 元信息

| 字段 | 值 |
|---|---|
| **Feature 编号** | F001（`donkey init`） |
| **核心库 API** | `core.api.init_workspace(path, name=None, force=False) -> InitResult` |
| **Phase 编号** | F001-P1 |
| **Phase 英文名** | `cli_validation` |
| **Phase 中文描述** | CLI 入口 + PATH 解析/权限校验 + workspace 根目录创建（**不加载模板清单**——推迟到 F001-P2） |
| **段位** | F001 段位 1–10；本 Phase 占用 F001 子段 1（exit 1–2） |
| **已用 exit code** | 1（`PathNotFoundError`）、2（`PathPermissionError`） |
| **预留 exit code** | 5–10（留给 v1.x 试运行期新错误） |
| **本 Phase 不占用的 exit code** | 3（`TemplateGenerationError`，推迟到 F001-P2）、4（`BuiltinToolGenerationError`，推迟到 F001-P3） |
| **对应验收脚本** | `tests/e2e/phase/verify_phase_f001_p1.py` |
| **闭环复杂度（断言数）** | 低（6 断言） |
| **准入条件** | 无前置（仓库初始化即可启动） |

---

## 1. Phase 目标声明（一句话）

实现 `donkey init` 的 CLI 入口、PATH 解析与权限校验、workspace 根目录创建。本 Phase **不**加载模板清单、**不**生成任何模板文件内容（清单加载 + 模板骨架内容、3 个内置 `@tool`、Skills example 三层均推迟到 F001-P2 / F001-P3）；本 Phase 结束时 `donkey init <PATH>` 在合法输入下 `exit 0`，且 PATH 校验 / 权限校验失败时分别抛 exit 1 / exit 2。

---

## 2. 背景与设计意图（实现者必须先理解）

### 2.1 项目身份（不可妥协的最高原则）

donkey 是一个**智能体材料层的可移植运行时引擎**。核心主张：

- **材料归用户**：workspace 目录 = 智能体的全部材料层（人格、知识、手脚、大脑），用户可任意替换；
- **运行归引擎**：Agent Loop、中间件挂载、客户端渲染、上下文治理等统一由引擎实现，不开放配置；
- **改引擎请 fork**：workspace 没有任何配置项能改变引擎层行为，需要 diff 审阅、路径权限交互、自定义图流程等能力的唯一官方路线是 fork donkey 本仓库二次开发。

### 2.2 两层模型

| 层 | 包含 | 定义方 | 可移植性 | 配置接口 |
|---|---|---|---|---|
| **材料层**（workspace 层） | Instructions / Model / Tools / Skills | 用户（一个目录） | 高 | workspace 内 4 类材料文件 |
| **引擎层**（harness / runtime 层） | Agent Loop 图流程、middleware 链、diff 审阅、路径权限交互、前端渲染、上下文治理 | `donkey` 代码 | 低 | **无任何配置项** |

### 2.3 workspace 原子性原则

- 一个 workspace 目录 = 一个 Agent；
- workspace 自带 manifest；
- 依赖与配置随 workspace 走；运行数据可选择性导出；
- workspace 有格式版本号。

### 2.4 路径绝对化原则

workspace 内的所有相对路径引用**以 workspace 绝对路径为唯一根**；不依赖进程 cwd / HOME / 属主隐藏目录约定。

### 2.5 `donkey init` 的幂等性（核心）

`donkey init` **必须幂等**（"无则增，有则跳过"）。F001-P1（本 Phase）关心的是"PATH 解析 + 权限校验 + 创建 workspace 根目录"，**不**关心模板清单加载与模板内容生成（均推迟到 F001-P2 / F001-P3），但本 Phase 结束时必须保证以下四类输入与对应行为：

| # | 输入条件 | 本 Phase 行为 | exit |
|---|---|---|---|
| 1 | 新路径（父目录存在，workspace 不存在） | 校验通过；仅创建 workspace 根目录（具体内容由 F001-P2 写入） | 0 |
| 2 | 已存在 workspace（无 `--force`） | **不报错**——PATH + 权限校验通过即可，具体"已有文件保护"由 F001-P2 通过模板清单驱动实现 | 0 |
| 3 | 已存在 workspace + `--force` | 校验通过；`--force` 标志被记录但**不**在本 Phase 执行重置逻辑（由 F001-P2 通过 `render_templates` 实现） | 0 |
| 4 | PATH 父目录不存在 / 路径解析失败 | 抛 `PathNotFoundError` | 1 |
| 5 | PATH 权限不足（父目录或 workspace 缺失读 / 写 / 执行权限） | 抛 `PathPermissionError` | 2 |

**本 Phase 容忍场景**：init 出来的 workspace 可以是空目录或仅含占位空文件——具体模板内容推迟到 F001-P2。**禁止行为**：本 Phase **不**检查"workspace 已存在则报错"——幂等设计下已存在不是错误。

---

## 3. 入口条件（Entry Gate）

仓库初始化即可启动，**无前置 Phase 依赖**。Phase 启动时必须满足的前置资产：

### 3.1 目录骨架

`donkey/` 仓库根目录下已存在 4 个空目录（仅占位，不含任何文件）：

```
donkey/
├── core/    # 空目录占位即可
├── cli/     # 空目录占位即可
├── web/     # 空目录占位即可（不在本 Phase 使用）
└── gui/     # 空目录占位即可（不在本 Phase 使用）
```

> **注意**：本 Phase **不**创建 `donkey/tests/` 之外的任何文件骨架；`donkey/core/api.py` / `donkey/core/workspace/init.py` / `donkey/cli/cli_client.py` / `pyproject.toml` 等由本 Phase 的 spec.md 落地时按 §4 实现要点创建。`donkey/web/`、`donkey/gui/` 目录由后续 F005 / F006 实施，本 Phase 仅维持占位空目录状态。

### 3.2 提前就绪的模块资产（Phase 启动时已存在）

| 资产 | 路径 | 内容约束 |
|---|---|---|
| **exit code 段位常量** | `donkey/core/exit_codes.py` | 已定义 F001 段位常量（如 `EXIT_CODE_SEGMENT_INIT = (1, 10)`）；F002 / F003 / F004 / F005 / F006 段位常量也在此文件预留定义，但**不**在本 Phase 使用。 |
| **异常类层次** | `donkey/core/exceptions.py` | 已定义以下继承链：<br>• `DonkeyError(Exception)` —— donkey 总基类<br>• `WorkspaceInitError(DonkeyError)` —— F001 基类<br>• `PathNotFoundError(WorkspaceInitError)` —— 对应 exit code 1<br>• `PathPermissionError(WorkspaceInitError)` —— 对应 exit code 2<br>每个异常类有 docstring 标注 `exit code: N`（便于后续 CLI 退出码映射）。 |
| **模板清单 manifest schema 文件** | `donkey/core/workspace/templates/manifest.json` | 已定义的 JSON schema，列出 donkey init 阶段自动生成的所有文件路径。**schema 字段说明**：<br>• `version: int` —— manifest schema 版本（v1 填 `1`）<br>• `entries: list[dict]` —— 模板文件清单，每个 entry 含 `path: str`（相对 workspace 根的路径）与可选 `format: str`（`markdown` / `toml` / `json` / `text` / `python` / `directory` / `sqlite3` 共 7 种——用于 P2 渲染器分派；**本 Phase 不加载、不解析**（加载推迟到 F001-P2））<br>**P1 阶段的初始 manifest 内容**：**仅 3 条**——`instruction.md`（markdown）/ `providers/default.toml`（toml）/ `mcp/mcp.json`（json），与 P1 已就位的 3 个 .txt 占位一一对应。<br>**⚠️ 清单必须分阶段追加**（P1 3 条 → P2 +43 条 = 46 条 → P3 +7 条 = 53 条；P2 的 +43 含 `providers/README.md` + 26 个 provider stub）：**清单里的每一条都必须已有对应的模板源 .txt**，否则 P2 的 `render_templates` 会因源缺失抛 `TemplateGenerationError` (exit 3)。 |
| **模板源文件占位** | `donkey/core/workspace/templates/*.txt` | 已就位的占位文件，**至少**包含 3 个：<br>• `instruction.md.txt`（空文件或仅含 1 行注释即可）<br>• `providers/default.toml.txt`（**保留名**，装 `default_provider` + `default_model`）<br>• `mcp.json.txt`<br>本 Phase **不**解析这些 .txt 内容、**不**加载清单、**不**验证 .txt 是否存在——P2 才负责加载 + 渲染 + 校验（P2 的清单加载失败归 `TemplateGenerationError` exit 3）。<br>**源文件路径命名规则**：`donkey/core/workspace/templates/{entry['path']}.txt`（与 manifest entry 的 `path` 一一对应，如 `templates/tools/filesystem.py.txt`）。 |

### 3.3 技术栈就绪

- Python 3.11+（依赖 `tomllib` 内置；本 Phase 仅使用 `pathlib` / `os` / `argparse` / `json` / `subprocess`，无第三方依赖）；
- 已安装 ruff + mypy + pytest（CI 标准）；
- 已配置 `.gitignore`（含 `__pycache__/`、`*.pyc`、`.venv/`、`memory/*.sqlite3`）。

---

## 4. 实现要点（spec 必须覆盖的功能点）

### 4.1 `donkey/core/api.py` —— 核心库 API

**目标**：定义 `init_workspace` 的稳定函数签名 + **P1 范围内的最小可用实现**（PATH 解析 / 权限校验 / **创建 workspace 根目录**）。**模板内容渲染推迟到 F001-P2**（由 `init_workspace_inner` + `render_templates` 实现）。**函数签名一旦确定，后续 F002 / F003 / F004 等均依赖之**——这是 v1 库 API 的"门面契约"。

```python
# donkey/core/api.py

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class InitResult:
    """donkey init 成功完成的返回结果。"""
    workspace_path: Path           # workspace 绝对路径
    name: str                      # workspace 名称（来自 --name 或 path.basename()）
    force: bool                    # 是否传了 --force
    templates_loaded: int          # 模板清单条目数（**P1 固定 0**——本 Phase 不加载清单；P2 起才填真实条目数）
    files_created: int             # 本次实际新建的文件数（本 Phase 固定 0——仅建根目录）
    files_skipped: int             # 已存在且跳过的文件数（本 Phase 固定 0）

def init_workspace(path: str | Path,
                   name: str | None = None,
                   force: bool = False) -> InitResult:
    """初始化一个 workspace 目录。

    库 API 契约（v1）：
    - path：workspace 绝对路径或相对路径（函数内部 resolve 为绝对路径）
    - name：可选 workspace 名称；为 None 时取 path.basename()
    - force：是否强制重置已存在模板文件（P2 才会真正使用；P1 仅记录）
    - 返回 InitResult dataclass，描述本次 init 的产出
    - 失败时 raise WorkspaceInitError 子类，由 CLI 层捕获并打印 exit code

    P1 行为（= 本 Phase 的实现范围）：
    1. validate_init_request(path, name, force) → (abs_path, resolved_name, force)
       （内部完成 check_path / check_permission）
    2. 创建 workspace 根目录（parents=True, exist_ok=True）
       —— 已存在不是错误（幂等设计）
    3. 返回 InitResult(files_created=0, files_skipped=0)
       （模板内容由 F001-P2 的 render_templates 写入）
    """
    abs_path, resolved_name, force = validate_init_request(
        path=path, name=name, force=force,
    )
    abs_path.mkdir(parents=True, exist_ok=True)
    return InitResult(
        workspace_path=abs_path,
        name=resolved_name,
        force=force,
        templates_loaded=0,          # P1 不加载模板清单（P2 起由 render_templates 填真实条目数）
        files_created=0,
        files_skipped=0,
    )
```

**spec 要求**：

- `InitResult` dataclass 字段顺序与类型严格按上表；P2 / P3 也会复用；
- `init_workspace` 接受 `str | Path`，内部统一 resolve 为 `Path`；
- **P1 必须真建 workspace 根目录**（否则 `donkey init <path>` 无法 exit 0，§6 场景 1 / 场景 6 断言不成立）——但**不加载模板清单、不写任何模板文件**（均属 P2 域）；
- 函数 docstring **必须**列出 v1 契约的全部行为（含 P1 的实现边界）；
- 本文件**禁止** import `argparse` / `sys.argv`（N-05）。

### 4.2 `donkey/core/workspace/init.py` —— 核心逻辑骨架

本模块实现 3 个独立函数 + 1 个综合校验函数（**模板清单加载 `load_template_manifest` 不在 P1 范围**——推迟到 F001-P2，因其失败应归 `TemplateGenerationError` (exit 3) 而非 exit 1）：

```python
# donkey/core/workspace/init.py
from pathlib import Path
from typing import Optional

from donkey.core.exceptions import PathNotFoundError, PathPermissionError


def check_path(path: str | Path) -> Path:
    """解析 path 为绝对路径，验证父目录存在。

    行为：
    1. 接受 str 或 Path；统一通过 Path(path).resolve() 返回绝对路径
    2. 验证 path.parent 是已存在的目录
       - path.parent 不存在 → raise PathNotFoundError
       - path 是相对路径但 cwd 解析后 parent 仍不存在 → raise PathNotFoundError
       - path 包含非法字符（如 NUL \\0）→ raise PathNotFoundError（合并到 path 错误）
    3. 不检查 path 是否已存在（幂等设计：已存在不是错误）
    4. 不检查权限（由 check_permission 单独负责）

    返回：绝对路径 Path 对象
    """


def check_permission(path: Path) -> None:
    """验证当前用户对 path（workspace 根目录）有完整权限。

    行为：
    1. 如果 path 不存在：检查 path.parent 的写权限 + 执行权限（搜身能否创建子项）
    2. 如果 path 已存在：检查 path 本身的读 + 写 + 执行权限（ls/cd/创建文件都依赖执行位）
    3. 任一权限不足 → raise PathPermissionError
    4. 错误信息必须含"哪个权限缺失"（read / write / execute）+ "对哪个路径缺失"

    返回：None
    """


def validate_init_request(path: str | Path,
                          name: str | None,
                          force: bool) -> tuple[Path, str, bool]:
    """综合校验入口。

    行为：
    1. 调 check_path → 拿到绝对路径 abs_path
    2. 调 check_permission(abs_path) → 校验权限
    3. 决定最终 name：name is None → abs_path.name（= basename）
    4. 不检查 "workspace 已存在"——幂等设计，已存在不是错误

    返回：(abs_path, name, force) 三元组
    """
```

**spec 要求**：

- 3 个函数必须**纯函数**（除 raise 外无副作用；不写文件、不调用 IO 库）；
- `check_path` 内部使用 `pathlib.Path.resolve(strict=False)` 解析相对路径；
- `check_permission` 在 Linux/macOS 上用 `os.access(path, mode)` 检查；mode = `os.R_OK | os.W_OK | os.X_OK`；
- **本 Phase 不实现 `load_template_manifest`**——模板清单加载推迟到 F001-P2（其失败归 `TemplateGenerationError` exit 3：修复动作是「重装 donkey」，与 exit 1 的「建目录 / 换路径」不同，按奥卡姆不能合并）；
- 本文件**禁止** import `argparse`（N-05）；**禁止** import `langchain` / `langgraph` / `sqlite3`（N-04）。

### 4.3 `donkey/cli/cli_client.py` —— argparse CLI 入口

**目标**：仅注册 `init` 子命令；P1 不实现其它子命令（load / session / run 推迟到后续 F）。

```python
# donkey/cli/cli_client.py

import argparse
import sys
from pathlib import Path

from donkey.core.api import init_workspace
from donkey.core.exit_codes import (
    EXIT_CODE_OK,
    EXIT_CODE_PATH_NOT_FOUND,       # = 1
    EXIT_CODE_PATH_PERMISSION,      # = 2
)
from donkey.core.exceptions import (
    DonkeyError,
    WorkspaceInitError,
    PathNotFoundError,
    PathPermissionError,
)


# 异常类 → exit code 的映射表（全局唯一来源）
_EXCEPTION_TO_EXIT_CODE: dict[type[DonkeyError], int] = {
    PathNotFoundError: EXIT_CODE_PATH_NOT_FOUND,        # 1
    PathPermissionError: EXIT_CODE_PATH_PERMISSION,     # 2
    # WorkspaceInitError 基类不在表中——基类应被子类细化；本 Phase 不引入新异常
}


def _build_parser() -> argparse.ArgumentParser:
    """构建 argparse 解析器；本 Phase 仅注册 `init` 子命令。"""
    parser = argparse.ArgumentParser(
        prog="donkey",
        description="donkey —— 智能体材料层可移植运行时引擎",
    )
    # v1 顶层只接子命令位置参数（不允许 `donkey init` 之外的"裸 donkey"形式）
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init 子命令
    init_parser = subparsers.add_parser(
        "init",
        help="初始化一个新的 workspace 目录",
    )
    init_parser.add_argument(
        "path",
        help="workspace 目录路径（绝对或相对均可）",
    )
    init_parser.add_argument(
        "--name",
        default=None,
        help="workspace 名称（缺省取 path.basename()）",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="强制重置已存在的模板文件（重置逻辑由 F001-P2 阶段的 render_templates 实现）",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 入口；返回 exit code。"""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        try:
            result = init_workspace(
                path=args.path,
                name=args.name,
                force=args.force,
            )
            print(f"[donkey init] workspace={result.workspace_path} "
                  f"name={result.name} force={result.force} "
                  f"templates={result.templates_loaded} "
                  f"created={result.files_created} skipped={result.files_skipped}")
            return EXIT_CODE_OK
        except WorkspaceInitError as e:
            # 1. 根据异常类型查 exit code
            exit_code = _EXCEPTION_TO_EXIT_CODE.get(
                type(e),
                EXIT_CODE_PATH_NOT_FOUND,  # 兜底：未注册的 WorkspaceInitError 子类归到 exit 1
            )
            # 2. 打印人类可读错误（stderr，不打密钥——本 Phase 无密钥路径）
            print(f"[donkey init] 失败：{e}", file=sys.stderr)
            return exit_code

    # 其它子命令未在本 Phase 注册；spec 不展开
    return EXIT_CODE_OK


if __name__ == "__main__":
    sys.exit(main())
```

**spec 要求**：

- argparse 用法严格按上例（`add_subparsers(required=True)` 强制必须传子命令）；
- `init` 子命令的 3 个参数（`path` 必填位置参数 / `--name` 可选 / `--force` flag）顺序与名字不能改；
- 异常处理统一捕获 `WorkspaceInitError`（F001 基类）；未注册的子类兜底归到 exit 1（**禁止**直接 `except Exception` 吞所有错误）；
- 错误消息必须打到 `stderr`；
- 本文件仅允许 `pathlib` 作为 IO 库；**禁止** import `langchain` / `langgraph` / `sqlite3`（N-04）。

### 4.4 `donkey/__main__.py` 或 `pyproject.toml` 的 entry point

**spec 必须包含**：

- `pyproject.toml` 中 `[project.scripts]` 段定义 `donkey = "donkey.cli.cli_client:main"`（或类似 entry point，使 `donkey init` 命令可执行）；
- 或 `donkey/__main__.py` 含 `from donkey.cli.cli_client import main; sys.exit(main())`（任选其一，spec 需明确说明选型）；
- entry point **必须**与 README §4.1.1 "分层架构：cli → core → LangChain / LangGraph / sqlite3" 一致；
- **禁止** entry point 写在 `donkey/core/` 下（N-03）。

### 4.5 单元测试（`tests/unit/test_init_workspace.py`）

**spec 必须列出**下列单测用例（**至少 9 个**，对应 §6 退出条件的每条都先在单测层验证一次）：

| 用例 | 输入 | 期望 |
|---|---|---|
| `test_check_path_absolute` | `/tmp/ws`（父目录存在） | 返回绝对 Path |
| `test_check_path_nonexistent_parent` | `/nonexistent/parent/ws` | raise `PathNotFoundError` |
| `test_check_path_resolve_relative` | `relative/ws`（cwd 下不存在） | raise `PathNotFoundError` |
| `test_check_permission_readonly_parent` | 只读父目录下的 ws | raise `PathPermissionError`（写权限缺失） |
| `test_check_permission_ok` | `/tmp/ws` | return None |
| `test_init_workspace_creates_root_dir` | 全新路径 | 目录被创建；`InitResult.files_created == 0` / `files_skipped == 0` |
| `test_init_workspace_existing_is_not_error` | 已存在目录 | exit 0 语义（不抛异常）；目录内容不变 |

> 权限测试在 CI 上需要 root 权限或 chmod 模拟；spec 应明确"在 CI 上通过临时 chmod 模拟"。

### 4.6 verify 脚本（`tests/e2e/phase/verify_phase_f001_p1.py`）

**黑盒测试**（N-04 / §立项书 4.1.1）：**禁止** import `donkey.*` 业务代码；只跑 `subprocess.run(["donkey", ...])` 验证 exit code + 文件系统副作用。7 个断言对应 §6 退出条件。

---

## 5. 异常退出码表（Phase 全量 Error class 映射）

| Error class（`donkey.core.exceptions`） | exit code | 触发条件 | 报错概率 |
|---|---|---|---|
| `PathNotFoundError` | **1** | PATH 父目录不存在 / 路径解析失败（相对路径解析失败、非法字符） | 高 |
| `PathPermissionError` | **2** | PATH 权限不足（父目录缺失写 / 执行权限；workspace 已存在但缺失读 / 写 / 执行权限） | 高 |
| （本 Phase 不占用）| 3 | `TemplateGenerationError` —— 推迟到 F001-P2 | — |
| （本 Phase 不占用）| 4 | `BuiltinToolGenerationError` —— 推迟到 F001-P3 | — |
| （预留）| 5–10 | 留给 v1.x 试运行期发现的新错误 | — |

**奥卡姆剃刀原则**：本 Phase 仅占 2 个码值（1 + 2），均属"用户大概率会遇到"的高频错误；罕见错误（路径含 NUL 字节、磁盘满等）合并到 `PathNotFoundError` / `PathPermissionError`，不单独分配码值。

---

## 6. 退出条件（Exit Gate）

**`tests/e2e/phase/verify_phase_f001_p1.py` 必须跑通以下 7 个断言**（顺序固定，每条独立可测）：

### 6.1 场景 1：全新创建 → exit 0

```python
def test_scenario_1_new_workspace(tmp_path):
    """场景 1：全新创建 workspace → exit 0"""
    result = subprocess.run(
        ["donkey", "init", str(tmp_path / "ws")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert (tmp_path / "ws").exists()  # 目录已创建
```

### 6.2 场景 2：PATH 父目录不存在 → exit 1

```python
def test_scenario_2_path_not_found(tmp_path):
    """PATH 父目录不存在 → exit 1 (PathNotFoundError)"""
    result = subprocess.run(
        ["donkey", "init", str(tmp_path / "nonexistent" / "ws")],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "PathNotFoundError" in result.stderr or "父目录不存在" in result.stderr
```

### 6.3 场景 3：PATH 权限不足 → exit 2

```python
def test_scenario_3_permission_denied(tmp_path):
    """PATH 权限不足 → exit 2 (PathPermissionError)"""
    # 模拟：父目录只读
    readonly_parent = tmp_path / "ro"
    readonly_parent.mkdir()
    os.chmod(readonly_parent, 0o555)
    try:
        result = subprocess.run(
            ["donkey", "init", str(readonly_parent / "ws")],
            capture_output=True, text=True,
        )
        assert result.returncode == 2
        assert "PathPermissionError" in result.stderr or "权限" in result.stderr
    finally:
        os.chmod(readonly_parent, 0o755)  # 清理
```

### 6.4 场景 4：已存在 workspace + 无 `--force` → exit 0（幂等）

```python
def test_scenario_4_idempotent_no_force(tmp_path):
    """场景 2 子操作：已存在 workspace，无 --force → exit 0 (幂等)"""
    ws = tmp_path / "ws"
    ws.mkdir()  # 已存在
    result = subprocess.run(
        ["donkey", "init", str(ws)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # 不报错：幂等设计，已存在不是错误
```

### 6.5 场景 5：已存在 workspace + `--force` → exit 0（P1 不真正重置）

```python
def test_scenario_5_force_no_reset_yet(tmp_path):
    """场景 3 子操作：已存在 workspace，传 --force → exit 0 (P1 不真正重置)"""
    ws = tmp_path / "ws"
    ws.mkdir()
    result = subprocess.run(
        ["donkey", "init", str(ws), "--force"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # F001-P1：--force 参数被记录但不执行重置（重置逻辑在 F001-P2 由 render_templates 实现）
```

### 6.6 场景 6：P1 不检查模板渲染 → init 出来的目录允许是空的

```python
def test_scenario_6_p1_no_template_rendering(tmp_path):
    """P1 阶段 init 出来的 workspace 不要求含模板文件（属于 P2 / P3）"""
    ws = tmp_path / "ws"
    result = subprocess.run(
        ["donkey", "init", str(ws)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # P1 实现范围：仅创建目录（不加载模板清单、不写模板文件）
    # workspace 可以是空目录或仅含占位文件——具体内容推迟到 P2 / P3
    assert ws.is_dir()  # 至少是目录
    # 不强制要求含 instruction.md / providers/default.toml 等
```

### 6.8 退出条件总览

verify_phase_f001_p1.py 的 6 个 `test_*` 函数全部 PASS → F001-P1 完成。

---

## 7. 可执行测试命令列表（"Phase 完成" 的硬性证据）

按以下顺序执行，全部 PASS 即视为 Phase 完成：

1. **单测层**：
   ```bash
   pytest tests/unit/test_init_workspace.py -v
   ```
   必须 9 个用例全绿。

2. **e2e/phase 层**：
   ```bash
   pytest tests/e2e/phase/verify_phase_f001_p1.py -v
   ```
   必须 7 个 `test_scenario_*` 全绿。

3. **静态检查**：
   ```bash
   ruff check donkey/ tests/
   mypy donkey/ tests/
   ```
   必须零 error / 零 warning。

4. **CLI 手动冒烟**（可选）：
   ```bash
   donkey init /tmp/test-ws               # 应 exit 0
   donkey init /nonexistent/parent/ws     # 应 exit 1
   chmod 555 /tmp/test-ws && donkey init /tmp/test-ws/sub  # 应 exit 2
   ```
   退出码必须与预期一致。

5. **完整 CI 套件（不影响 Phase 验收，但建议跑一遍）**：
   ```bash
   pytest tests/ -v
   ```
   本 Phase 的所有测试必须 PASS；其它 Phase 的测试允许 FAIL（因后续 Phase 未实现）。

---

## 8. 绝对不做清单（推迟到后续 Phase / Feature）

| 不做的内容 | 推迟到 |
|---|---|
| 模板骨架文件实际写入（`instruction.md` / `providers/default.toml` / `providers/<id>.toml` × 26 / `mcp/mcp.json` 等） | F001-P2 |
| `render_templates(path, name, force)` 函数实现 | F001-P2 |
| workspace manifest（`donkey/manifest.json`）的写入与解析 | F001-P2 |
| `--name` 注入到 `providers/default.toml` 注释 / `README.md` 标题 | F001-P2 |
| 3 个内置 `@tool` 文件（`tools/filesystem.py` / `tools/commandline.py` / `tools/webfetch.py`）生成 | F001-P3 |
| Skills example 三层示例（`skills/example/SKILL.md` Level 1/2/3） | F001-P3 |
| `tools/__init__.py` / `tools/README.md` 等支撑文件 | F001-P3 |
| `donkey load` / `donkey session` / `donkey run` 等其它子命令 | F002 / F003 / F004 |
| 任何 LangChain 中间件挂载（`FilesystemFileSearchMiddleware` 等） | F004 |
| 任何 `init_chat_model` / 模型连通性测试 | F002 |
| 任何 sqlite3 数据库文件 schema 构造（SqliteSaver / sessions_metadata / SqliteStore） | F001-P2（init 作为模板预创建 schema；本 P1 不写任何文件） |
| 解析 `providers/` 目录字段 / 验证 `mcp/mcp.json` 字段 | F002 |
| "init 后跑 F002 静态检查" | F002 域 |
| 创建 `tests/` 目录（`tests/unit/`、`tests/integration/`、`tests/e2e/phase/`）之外的额外测试目录 | 任何阶段都不引入 |

---

## 9. 技术栈与依赖硬约束

- **Python 3.11+**（`tomllib` 内置；本 Phase 仅使用 `pathlib` / `os` / `argparse` / `json` / `subprocess`，无第三方依赖）；
- **CLI 框架**：标准库 `argparse`（**禁止** typer / click / rich-argparse 等第三方 CLI 框架）；
- **测试**：pytest；
- **静态检查**：ruff + mypy；
- **CI**：GitHub Actions（`pytest tests/` + `ruff check` + `mypy`）。

### 9.1 永不使用清单

| 类别 | 具体禁用项 |
|---|---|
| **LangSmith** | 任何形态——`langsmith` 包、LangSmith Cloud、Studio UI、Tracing、Deployment、Hub、`langchain[langsmith]` extras、`LANGSMITH_TRACING` 等环境变量；**禁止**在 `donkey.core` / `cli` / `web` / `gui` 任何代码路径中 `import langsmith` 或 `import langchain.langsmith` / `langchain_community.langsmith` / `langgraph.langsmith` 等任何 langsmith.* 子包（包括为了"诊断智能体"或"打印运行轨迹"等用途） |
| **deepagents** | `create_deep_agent` / FilesystemMiddleware / SubAgentMiddleware / RubricMiddleware / SkillsMiddleware / MemoryMiddleware |
| **ShellToolMiddleware** | 由 `tools/commandline.py` 替代（推迟到 F001-P3 阶段，本 Phase 不引入） |
| **subagent / 子智能体** | workspace 内禁止任何 `agent.py` / `main.py`；禁止任何 subagent 字段 |

### 9.2 分层架构硬约束（N-01 ~ N-12）

| 编号 | 条款 | 本 Phase 落地 |
|---|---|---|
| **N-01** | workspace 内禁止出现 `agent.py` / `main.py` 或任何 Python 入口文件 | 本 Phase 不创建 workspace；约束传递给后续 Phase |
| **N-03** | `donkey.core` 禁止 import `cli` / `web` / `gui` | ✓ 已落地（`core/api.py` 与 `core/workspace/init.py` 仅 import 标准库 + `core.exceptions`） |
| **N-04** | `cli` 禁止直接 import `langchain` / `langgraph` / `sqlite3` | ✓ 已落地（`cli/cli_client.py` 仅 import `argparse` / `sys` / `core.api` / `core.exit_codes` / `core.exceptions`） |
| **N-05** | `donkey.core` 禁止 import `argparse` / `sys.argv` / `click` / `typer` | ✓ 已落地 |
| **N-08** | exit code 段位空间严格不重叠 | ✓ 已落地（仅用 exit 1 / 2，落在 F001 段位 1–10 内） |
| **N-12** | 禁止 LangSmith 任何形态 | ✓ 已落地（本 Phase 无 LangChain 调用，自然不涉及） |

---

## 10. 验收标准（business AC）

| 验收项 | 说明 |
|---|---|
| **AC-3（init 幂等）** | 重复执行 `donkey init <已存在 ws>` 不破坏已存在文件（除非 `--force`）。本 Phase 仅保证"不报错 + exit 0"；具体"不破坏文件"由 F001-P2 通过模板清单驱动实现。 |
| **技术验收** | F001 段位 1–10 中 exit 1（`PathNotFoundError`）、exit 2（`PathPermissionError`）实测通过；预留码 3 / 4 / 5–10 在本 Phase 不触发。 |
| **分层验收** | `donkey.core` / `donkey.cli` 边界严格：core 不含 argparse / sys.argv；cli 不含 langchain / langgraph / sqlite3；exit code 段位不重叠。 |

---

## 11. Spec 输出格式要求（给 `/speckit.specify` 的提示）

执行 `/speckit.specify` 后生成的 `specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md` **必须**包含：

1. **User Stories**：按优先级 P1 → P7 列出 7 个核心场景（对应 §6 的 7 个 verify 断言）；
2. **Functional Requirements (FR-001 ~ FR-NNN)**：覆盖 §4 的 6 个子节（4.1 ~ 4.6）；
3. **Edge Cases**：列出本 Phase 的边界条件（路径含 NUL、相对路径解析、权限缺失、已存在 workspace 的 4 种场景）——**不含模板清单损坏**（P1 不加载清单，该场景属 P2 / exit 3）；
4. **Success Criteria (SC-001 ~ SC-NNN)**：可量化的退出条件（"7 个 verify 断言全部 PASS"、"ruff + mypy 零 error"等）；
5. **Key Entities**：`InitResult` dataclass 字段定义；`DonkeyError` / `WorkspaceInitError` / `PathNotFoundError` / `PathPermissionError` 异常类继承链；
6. **Assumptions**：仓库已初始化、`donkey/core/` 等目录已存在；manifest.json / .txt 模板源已就位（这些是**P2** 的入口条件，P1 不加载、不校验、不实现）。

**Spec 禁止**包含的内容（留给 `/speckit.plan` 处理）：

- 具体实现步骤（如"先写 check_path 再写 check_permission"）—— plan 才规定顺序；
- 测试用例的具体代码 —— plan / tasks 才展开；
- 依赖包的版本号 —— plan 才锁定。

---

**End of F001-P1 spec input.** 将本文件整体作为参数传入 `/speckit.specify` 即可。
