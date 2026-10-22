# F001-P3 `builtin_tools` —— `/speckit.specify` 开发提示词

> 本文件是 `donkey init` F001 第 3 个 Phase（也是 F001 的最后一个 Phase）的 **spec 输入**。把它整体作为参数传入 `/speckit.specify` 命令即可生成 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md`。`/speckit.specify` 完成后，本 Phase 闭包即代表 F001 (`donkey init`) 整体完成。
>
> **自包含契约**：本提示词包含完整的 Phase 范围、入口条件、退出条件、约束、实现要点；执行 `/speckit.specify` 时**无需**翻阅 `harness/features/` 内其他 F001 兄弟 Phase 提示词文件、也**无需**翻阅立项书 / README / 调研报告——所有必要信息均已内化在本文件内。本文件对其他 F001 Phase 的引用仅限于"Phase 标识符"层面（例如"由 F001-P1 提供" / "由 F001-P2 实现"），**不**复制其 spec 内容——但会在本文件中以独立小节复述必要的接口契约（如 `init_workspace_inner` 路径、manifest 条目追加方式、模板清单 schema），避免跨文件依赖。
>
> 本提示词**不**描述 `/speckit.plan` / `/speckit.tasks` / `/speckit.implement` / `/speckit.analyze` 的细节——那些命令是 spec 的下游延伸，由 Speckit 工作流按 `harness/prompt/speckit.md` 串行处理即可，本 Phase 不提前撰写。

---

## 0. Phase 元信息

| 字段 | 值 |
|---|---|
| **Feature 编号** | F001（`donkey init`） |
| **核心库 API** | `core.api.init_workspace(path, name=None, force=False) -> InitResult` |
| **Phase 编号** | F001-P3 |
| **Phase 英文名** | `builtin_tools` |
| **Phase 中文描述** | 幂等生成 3 个内置 `@tool`（filesystem / commandline / webfetch）+ Skills example 三层 + `tools/` 支撑文件 + 端到端集成预演 |
| **段位** | F001 段位 1–10；本 Phase 占用 F001 子段 3（exit 4） |
| **已用 exit code** | 4（`BuiltinToolGenerationError`） |
| **预留 exit code** | 5–10（留给 v1.x 试运行期新错误） |
| **本 Phase 不占用的 exit code** | 1 / 2（F001-P1）、3（F001-P2）、5–10 |
| **对应验收脚本** | `tests/e2e/phase/verify_phase_f001_p3.py` |
| **闭环复杂度（断言数）** | 中（11 断言） |
| **准入条件** | F001-P2 退出条件全部满足 + F001-P2 抛出的 `TemplateGenerationError` 已通过单元测试 |

---

## 1. Phase 目标声明（一句话）

实现 `donkey init` 的 3 个内置 `@tool` 文件生成（`tools/filesystem.py` 含 7 个工具函数 / `tools/commandline.py` 含 1 个工具函数 / `tools/webfetch.py` 含 1 个工具函数）+ Skills example 三层示例（Level 1 frontmatter + Level 2 主体 + Level 3 reference/scripts/templates 目录）+ `tools/` 支撑文件（`tools/__init__.py` / `tools/README.md`），并把上述条目追加到模板清单。本 Phase **不**引入任何 LangChain 中间件（F004 域），**不**做 F002 静态检查，**不**构造 sqlite3 schema（F001-P2 域），**不**调用 `init_chat_model`（F002 域）。

---

## 2. 背景与设计意图（实现者必须先理解）

### 2.1 项目身份

donkey 是一个**智能体材料层的可移植运行时引擎**——workspace 目录 = 智能体的全部材料层（人格、知识、手脚、大脑），用户可任意替换；Agent Loop、中间件挂载、客户端渲染、上下文治理等由引擎统一实现，不开放配置；改引擎层需 fork 仓库。

### 2.2 两层模型

- **材料层**（workspace 层）：Instructions / Model / Tools / Skills，由用户定义（一个目录），可移植性高；
- **引擎层**（harness / runtime 层）：Agent Loop、中间件链、客户端渲染、上下文治理，由 `donkey` 代码定义，**无任何配置项**。

### 2.3 workspace 原子性原则

- 一个 workspace 目录 = 一个 Agent；
- workspace 自带 manifest；
- 依赖与配置随 workspace 走；运行数据可选择性导出；
- workspace 有格式版本号。

### 2.4 Skills 三层渐进披露原则（核心）

每个 Skill 目录 `skills/<name>/SKILL.md` 按访问频度分为三级，**这是 donkey 的核心设计**：

| 级别 | 内容 | 加载方式 | 触发时机 |
|---|---|---|---|
| **Level 1** | `SKILL.md` frontmatter 必填两字段：`name` + `description` | `donkey.core` 扫描后**自动注册为独立 `@tool`**（工具名 `load_skill_<slugify(name)>`） | 工具列表常驻 |
| **Level 2** | `SKILL.md` frontmatter 下方的 Markdown 主体 | 通过 Level 1 工具调用返回（返回值含 Level 2 完整内容） | 模型判断相关时调用 |
| **Level 3** | Skill 目录内除 `SKILL.md` 之外的文件 | 由 workspace 内置 `@tool`（filesystem / commandline / webfetch）或 `FilesystemFileSearchMiddleware.glob_search/grep_search` 读取 | 模型需要深层细节 / 执行时调用 |

**Skills frontmatter schema 严格性**：

- 仅 `name` + `description` 两字段必填（与 MDA / Anthropic Agent Skills 协议对齐）；
- **不允许**自定义额外字段（`when_to_use` / `version` / `tags` 等）——donkey v1 不解析，避免 schema 漂移；
- 想加元信息写在 Markdown 主体（Level 2）即可。

### 2.5 内置 `@tool` 与中间件职责正交原则（核心）

| 工具来源 | 职责 | 调用场景 |
|---|---|---|
| `FilesystemFileSearchMiddleware`（引擎侧 LangChain 中间件） | `glob_search` + `grep_search`（ripgrep 后端） | "找文件"、"找内容" |
| `tools/filesystem.py`（workspace 内置 `@tool`，材料层） | 文件操作：read / write / copy / move / delete / list_dir / stat | "读这个文件"、"改那个文件" |
| `tools/commandline.py`（workspace 内置 `@tool`） | `run_shell` —— `subprocess.run([...], shell=False, timeout=...)`；**每次新建进程**，不走持久 shell | 命令执行 |
| `tools/webfetch.py`（workspace 内置 `@tool`） | `fetch_url` —— HTTP GET/POST + timeout；不持久化 cookies | HTTP 拉取 |

**职责正交不重叠**：内置 3 个 `@tool` + `FilesystemFileSearchMiddleware` 中间件共同构成 Skill Level 3 的完整访问通道，按场景选用。

### 2.6 `tools/filesystem.py` 不含 glob/grep 的原因

`glob_search` / `grep_search` 由 `FilesystemFileSearchMiddleware`（LangChain 中间件）接管——它是纯 LangChain（不依赖 deepagents）+ ripgrep 后端高效。`tools/filesystem.py` 仅做"读 / 写 / 复制 / 移动 / 删除 / 列目录 / stat"这些"对单一文件或目录的精确操作"。"找文件 / 找内容"属于中间件职责，**禁止**在 `tools/filesystem.py` 内实现。

### 2.7 `commandline.py` 不走持久 shell 的原因

`ShellToolMiddleware` 的持久 shell session 与未来 v2 HITL（interrupt）冲突——persistent shell 不支持 interrupt。本项目**禁用** `ShellToolMiddleware`，由 `tools/commandline.py` 用 `subprocess.run([...], shell=False, timeout=...)` 替代：每次新进程 + 显式 timeout 掐断 + 显式命令数组（不走 shell 字符串，从源头避免 shell injection + HITL 冲突）。

### 2.8 `donkey init` 幂等性

继续遵循 F001-P2 已确立的 4 场景幂等性：本 Phase 生成的 builtin tool + Skills example 模板条目均纳入 manifest 清单，遵循"无则增 / 已存在跳过 / --force 重置"三规则；用户自定义的 `tools/my_tool.py`（不在清单）**永远不动**。

---

## 3. 入口条件（Entry Gate）

### 3.1 前置 Phase 已完成

- **F001-P1 (`cli_validation`) 已完成**：7 个 verify 断言（场景 1 / 2 / 3 / 4 / 5 / 6 / 7）全部 PASS；`PathNotFoundError` / `PathPermissionError` 单测全绿。
- **F001-P2 (`template_skeleton`) 已完成**：14 个 verify 断言（场景 1 ~ 14）全部 PASS；`TemplateGenerationError` 单测全绿（`tests/unit/test_template_skeleton.py` 至少 14 个用例）。

### 3.2 本 Phase 不重复实现的接口契约（来自 F001-P1 / F001-P2，本 Phase 直接复用）

| 接口 | 来源 Phase | F001-P3 调用契约（**仅引用签名与行为，不复述实现**） |
|---|---|---|
| `validate_init_request(path, name, force) -> tuple[Path, str, bool]` | F001-P2 `core/workspace/init.py` | 由 `init_workspace_inner` 入口首行调用；返回 `(abs_path, resolved_name, force)` |
| `render_templates(workspace_path, name, force, manifest_entries)` | F001-P2 `core/workspace/init.py` | 由 `init_workspace_inner` 顺序调用；遍历 manifest 条目按 format 分派（text 类复制 .txt 源；sqlite3 类调对应 builder；directory 类 mkdir）；返回 `(files_created, files_skipped)` |
| `init_workspace_inner(path, name, force) -> tuple[Path, str, bool, int, int]` | F001-P2 `core/workspace/init.py` | 由 `init_workspace` 函数体首行调用；串行 `validate_init_request` → `load_template_manifest` → `render_templates` → `write_workspace_manifest` |
| `init_workspace(path, name=None, force=False) -> InitResult` | F001-P2 `core/api.py` | CLI 入口调用；函数体已由 F001-P2 补齐 |
| `_EXCEPTION_TO_EXIT_CODE` 异常映射表 | F001-P1 / F001-P2 `cli/cli_client.py` | 已映射 `PathNotFoundError` / `PathPermissionError` / `TemplateGenerationError`；本 Phase 在表**追加** 1 行：`BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION` |
| `templates/manifest.json` manifest 清单 | F001-P1 初始化 schema（3 条）+ F001-P2 已含 46 条目 | 本 Phase **追加** 7 条新 entry（`tools/__init__.py` + 3 个内置 tool + 3 个 Skills Level 3 示例）→ **累计 53 条**；追加方式是"在原 `entries` 数组末尾 push"，**不**修改 F001-P2 已有条目 |
| `templates/{entry['path']}.txt` 模板源 | F001-P2 已有 18 个 .txt 源 | 本 Phase **新增** 7 个 .txt（`tools/__init__.py.txt` + 3 个内置 tool + 3 个 Skills Level 3）+ **覆盖** 1 个已有 .txt（`skills/example/SKILL.md.txt` 补完整 Level 2 正文） |

### 3.3 提前就绪的模块资产（Phase 启动时已存在）

| 资产 | 路径 | 内容约束 |
|---|---|---|
| **核心库 API** | `donkey/core/api.py` | `init_workspace` 函数体已补齐（F001-P2）；本 Phase **不**修改 api.py。 |
| **核心逻辑骨架** | `donkey/core/workspace/init.py` | 已有 `validate_init_request` / `render_templates` / `init_workspace_inner`（F001-P2）；本 Phase **不**修改 init.py——复用 `render_templates` 即可。 |
| **CLI 入口** | `donkey/cli/cli_client.py` | argparse + 异常处理已就位；本 Phase **追加** 1 行异常映射：`BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION`。 |
| **exit code 常量** | `donkey/core/exit_codes.py` | 已定义 F001 已用码（0 / 1 / 2 / 3）；本 Phase **追加** `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4`。 |
| **异常类层次** | `donkey/core/exceptions.py` | 已定义 `DonkeyError` / `WorkspaceInitError` / `PathNotFoundError` / `PathPermissionError` / `TemplateGenerationError`；本 Phase **追加** `BuiltinToolGenerationError(WorkspaceInitError)` —— 对应 exit code 4。 |
| **workspace manifest** | `donkey/core/workspace/manifest.py` | 已实现 `write_workspace_manifest` / `read_workspace_manifest` / `ensure_workspace_manifest`（F001-P2）。本 Phase **不**修改。 |
| **模板清单** | `donkey/core/workspace/templates/manifest.json` | 已含 F001-P2 模板条目（instruction.md / `providers/`（default.toml + README.md + 26 个 stub）/ mcp/mcp.json / skills/example/SKILL.md / README 系列 / .gitignore）。本 Phase **追加** 7 个新条目（详见 §4.7）。 |
| **模板源文件** | `donkey/core/workspace/templates/{entry['path']}.txt` | 已含 F001-P2 的 18 个 .txt 源文件。**源文件路径规则**：`templates/{entry['path']}.txt`（与 manifest entry 的 `path` 一一对应）。本 Phase **新增** 7 个 .txt（`tools/__init__.py.txt` + 3 个内置 tool + 3 个 Skills Level 3）+ **覆盖** `skills/example/SKILL.md.txt`（补完整 Level 2 正文）。 |
| **Skills example Level 1 + 2** | `donkey/core/workspace/templates/skills/example/SKILL.md.txt` | F001-P2 已生成（frontmatter `name` + `description` + Level 2 占位）；本 Phase **覆盖**其 Level 2 正文为完整内容，并新增 Level 3 子目录文件（`reference/` / `scripts/` / `templates/`）。 |
| **三个 sqlite3 模板** | `memory/{sessions,store,knowledge}.sqlite3` | 已由 F001-P2 init 阶段预创建（schema-built sessions + 占位空文件 store/knowledge）；本 Phase **不**触碰。本 Phase 假设 sqlite3 schema 健康；若发现 schema 缺失，应让 `donkey init --force` 重建（属 F001-P2 / F002-P2 域，不属本 Phase）。 |

### 3.4 技术栈就绪

- Python 3.11+；
- `httpx`（用于 `webfetch.py.txt` 模板与测试；如选 `requests` 也可，但 spec 默认 httpx）；
- pytest + `pytest-httpx`（用于 webfetch 的 HTTP mock 测试）；
- `langchain_core.tools.tool` 装饰器（**纯 LangChain 内置**——`@tool` 装饰器从 `langchain_core.tools` import，**不**违反 N-04 / N-12；N-04 仅约束 cli/web/gui 客户端不直接 import langchain，`donkey.core` 允许使用 langchain 库 API）；
- ruff + mypy + GitHub Actions。

---

## 4. 实现要点（spec 必须覆盖的功能点）

### 4.1 `donkey/core/workspace/templates/filesystem.py.txt` —— 7 个 `@tool`（材料层）

**模板内容**（写入 workspace 后即为 `tools/filesystem.py`）：

```python
"""Filesystem operations @tool set for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user. When deleted, file
operations become unavailable, but Level 3 content can still be searched via
`FilesystemFileSearchMiddleware.glob_search` / `grep_search`.

NOTE: This module intentionally does NOT include `glob_search` / `grep_search`.
Those are provided by the engine-layer middleware `FilesystemFileSearchMiddleware`
(see donkey's constitution §2.5).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read the entire content of a file as a UTF-8 string.

    Args:
        path: Absolute or workspace-relative path.

    Returns:
        File content as UTF-8 string.

    Raises:
        FileNotFoundError: If `path` does not exist.
        IsADirectoryError: If `path` is a directory.
        PermissionError: If the file is not readable.
    """
    p = Path(path)
    return p.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Write `content` to `path`, creating parent directories if needed.

    Args:
        path: Absolute or workspace-relative path.
        content: Text content to write (UTF-8).

    Returns:
        JSON-encoded result with `path` and `bytes_written`.

    Raises:
        PermissionError: If the file or its parent directory is not writable.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return json.dumps({"path": str(p), "bytes_written": len(content.encode("utf-8"))})


@tool
def copy_file(src: str, dst: str) -> str:
    """Copy a file from `src` to `dst`.

    Args:
        src: Source path.
        dst: Destination path (will be created if missing).

    Returns:
        JSON-encoded result with `src` and `dst`.

    Raises:
        FileNotFoundError: If `src` does not exist.
        shutil.SameFileError: If `src` and `dst` are the same.
    """
    shutil.copy2(src, dst)
    return json.dumps({"src": src, "dst": dst})


@tool
def move_file(src: str, dst: str) -> str:
    """Move a file from `src` to `dst`.

    Args:
        src: Source path.
        dst: Destination path.

    Returns:
        JSON-encoded result with `src` and `dst`.

    Raises:
        FileNotFoundError: If `src` does not exist.
    """
    shutil.move(src, dst)
    return json.dumps({"src": src, "dst": dst})


@tool
def delete_file(path: str) -> str:
    """Delete a file or a directory tree (be careful!).

    Args:
        path: Path to delete.

    Returns:
        JSON-encoded result with `path` and `type` ('file' | 'directory').

    Raises:
        FileNotFoundError: If `path` does not exist.
    """
    p = Path(path)
    if p.is_dir():
        shutil.rmtree(p)
        return json.dumps({"path": str(p), "type": "directory"})
    else:
        p.unlink()
        return json.dumps({"path": str(p), "type": "file"})


@tool
def list_dir(path: str) -> list[str]:
    """List immediate children of a directory (non-recursive).

    Args:
        path: Directory path.

    Returns:
        Sorted list of child names (basename only).

    Raises:
        FileNotFoundError: If `path` does not exist.
        NotADirectoryError: If `path` is not a directory.
    """
    return sorted(p.name for p in Path(path).iterdir())


@tool
def stat(path: str) -> dict[str, Any]:
    """Return file/directory metadata.

    Args:
        path: Path to inspect.

    Returns:
        Dict with keys: `size` (bytes), `mtime` (epoch seconds, float),
        `is_file` (bool), `is_dir` (bool), `exists` (bool).

    Raises:
        OSError: If `stat()` syscall fails (permission, etc.).
    """
    p = Path(path)
    try:
        st = p.stat()
        return {
            "size": st.st_size,
            "mtime": st.st_mtime,
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "exists": True,
        }
    except FileNotFoundError:
        return {"size": 0, "mtime": 0.0, "is_file": False, "is_dir": False, "exists": False}
```

**spec 要求**：

- 7 个 `@tool` 函数严格按上表签名（`read_file` / `write_file` / `copy_file` / `move_file` / `delete_file` / `list_dir` / `stat`）；
- 每个 `@tool` **必须**有完整 docstring（LangChain `@tool` 装饰器依赖 docstring 作为工具 description）；
- `@tool` 装饰器**必须**从 `langchain_core.tools` import（langchain 内置，**不**违反 N-04 / N-12 —— 因为 `donkey.core` 允许使用 langchain / langgraph 库 API；N-04 仅约束 `cli` / `web` / `gui` 客户端不直接 import）；
- **禁止**包含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管，§2.6）；
- 路径白名单由用户自管（donkey 不强制；`tools/filesystem.py` 不做路径校验 —— 用户自行负责越权访问风险）。

### 4.2 `donkey/core/workspace/templates/commandline.py.txt` —— 1 个 `@tool`

**模板内容**：

```python
"""Shell command execution @tool for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user.

IMPORTANT: This module intentionally does NOT use a persistent shell session
(ShellToolMiddleware). Persistent shells conflict with future v2 HITL
(interrupts). Each invocation spawns a new process via `subprocess.run`,
which is interrupt-safe and timeout-bounded.
"""
from __future__ import annotations

import json
import shlex
import subprocess

from langchain_core.tools import tool


@tool
def run_shell(command: str, timeout: int = 60) -> str:
    """Execute a shell command in a fresh subprocess and return its combined stdout/stderr.

    Each invocation creates a NEW subprocess (no persistent shell session).
    The command line is split into an argv array and executed via
    `subprocess.run` with `shell=False` to avoid shell injection. If the command
    runs longer than `timeout` seconds, it is killed (TimeoutExpired). Exit code 0
    is treated as success; non-zero is included in the returned JSON.

    Args:
        command: The shell command line to execute (e.g. "ls -la /tmp").
        timeout: Maximum execution time in seconds (default 60).

    Returns:
        JSON-encoded result with keys:
        - `stdout`: str (combined stdout+stderr)
        - `stderr`: str (typically empty; stdout already includes stderr)
        - `returncode`: int (0 on success)
        - `timed_out`: bool (True if killed by timeout)

    Raises:
        subprocess.TimeoutExpired: Re-raised after the JSON result is returned
            (caller should handle via `timed_out` field).
    """
    try:
        completed = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return json.dumps({
            "stdout": completed.stdout + completed.stderr,
            "stderr": "",
            "returncode": completed.returncode,
            "timed_out": False,
        })
    except subprocess.TimeoutExpired as e:
        return json.dumps({
            "stdout": (e.stdout or "") + (e.stderr or ""),
            "stderr": "",
            "returncode": -1,
            "timed_out": True,
        })
```

**spec 要求**：

- 1 个 `@tool` 函数：`run_shell(command, timeout=60)`；
- **每次新建进程**（`subprocess.run(shlex.split(command), shell=False, timeout=...)`）——显式命令数组不走 shell 字符串，从源头避免 shell injection；与"v1 不走持久 shell"约束一致（每次都是新进程）。管道 / 重定向不支持（需用户自行拆分或改用脚本）；
- 显式 `timeout` 掐断；
- 返回值必须含 `timed_out` 字段，模型据此决定重试 / 放弃；
- **不**依赖 LangChain `ShellToolMiddleware`（被 v1 永久禁用）；
- docstring 完整。

### 4.3 `donkey/core/workspace/templates/webfetch.py.txt` —— 1 个 `@tool`

**模板内容**：

```python
"""HTTP fetch @tool for the donkey agent.

This module is part of the **material layer** (workspace). It is generated by
`donkey init` and can be edited / deleted by the user.

Uses httpx (synchronous). Does NOT persist cookies between calls.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool


@tool
def fetch_url(url: str,
              method: str = "GET",
              headers: dict[str, str] | None = None,
              timeout: int = 30) -> str:
    """Make an HTTP request to `url` and return the response body as a string.

    Args:
        url: Target URL (must include scheme, e.g. https://example.com).
        method: HTTP method (default "GET"). Supports "GET" / "POST" / "PUT"
                / "DELETE" / "PATCH" / "HEAD".
        headers: Optional dict of HTTP headers.
        timeout: Request timeout in seconds (default 30).

    Returns:
        JSON-encoded result with keys:
        - `status_code`: int (HTTP status, e.g. 200)
        - `body`: str (response body decoded as UTF-8)
        - `headers`: dict[str, str] (response headers)
        - `url`: str (final URL after redirects)

    Raises:
        httpx.HTTPError: On network / protocol errors.
        httpx.TimeoutException: On timeout (after `timeout` seconds).
    """
    response = httpx.request(
        method=method.upper(),
        url=url,
        headers=headers or {},
        timeout=timeout,
        follow_redirects=True,
    )
    return json.dumps({
        "status_code": response.status_code,
        "body": response.text,
        "headers": dict(response.headers),
        "url": str(response.url),
    })
```

**spec 要求**：

- 1 个 `@tool` 函数：`fetch_url(url, method="GET", headers=None, timeout=30)`；
- 使用 `httpx` 同步调用（不持久化 cookies；每次新连接）；
- 显式 `timeout`；
- 不引入 LangChain 任何 webfetch 中间件（v1 不存在）。

### 4.4 `donkey/core/workspace/templates/tools/__init__.py.txt` —— `tools/__init__.py` 占位

**模板内容**：

```python
"""donkey workspace tools package.

This package is auto-generated by `donkey init`. The 3 builtin @tool modules
(filesystem / commandline / webfetch) live here. Users may add additional
@tool modules of their own.
"""
```

**spec 要求**：最小占位即可（仅 docstring）。

### 4.5 `donkey/core/workspace/templates/tools/README.md.txt` —— `tools/README.md` 工具开发规范

> **注意**：`tools/README.md` 的 **manifest entry 与目标文件由 F001-P2 创建**（P2 已把它列入 46 条清单 + 生成占位 .txt）；本 Phase **不新增 entry**，只**覆盖** `templates/tools/README.md.txt` 源文件，把占位正文替换为完整规范（`--force` 时按出厂内容重写）。

spec 必须列出 `tools/README.md` 的初始内容（建议长度 15–25 行），包含：

- `@tool` 装饰器从 `langchain_core.tools` 导入；
- 函数必须有 docstring（作为工具 description）；
- 路径白名单由用户自管，donkey 不强制；
- 推荐 timeout 配置（`commandline` 默认 60s / `webfetch` 默认 30s）；
- 错误处理建议（raise 具体异常类型 / 返回 JSON 含 `error` 字段）。

### 4.6 Skills example 三层示例

#### 4.6.1 Level 1 + Level 2（`donkey/core/workspace/templates/skills/example/SKILL.md.txt`——**覆盖** F001-P2 的同名源）

```markdown
---
name: example
description: 示例 Skill —— 展示 Skills 三层模型（Level 1 frontmatter + Level 2 主体 + Level 3 reference/scripts/templates）。
---

# Example Skill（Level 2）

本文件由 `donkey init` 自动生成，演示 Skills 三层模型：

- **Level 1**（本文件顶部 frontmatter）：`name` + `description` 两字段必填；donkey 自动注册为独立 `@tool` `load_skill_example`。
- **Level 2**（frontmatter 下方的 Markdown 主体）：模型调用 `load_skill_example` 时返回的内容。
- **Level 3**（同目录下除 SKILL.md 之外的文件）：放在 `reference/` / `scripts/` / `templates/` 等子目录；由内置 `@tool`（filesystem / commandline / webfetch）或 `FilesystemFileSearchMiddleware` 读取。

## 使用示例

模型判断相关时调用 `load_skill_example`，获得本文件全部内容，然后：

- 如需看 `reference/` 子目录的细节 → 调 `filesystem.list_dir` 或 `grep_search`
- 如需运行 `scripts/example.py` → 调 `commandline.run_shell`
- 如需渲染 `templates/example.md` 模板 → 调 `filesystem.read_file`

## 注意事项

- 修改本 Skill 时请保留 frontmatter 的 `name` + `description` 字段；
- 其它字段（如 `when_to_use` / `tags` / `version`）**不**被 donkey 解析，会被忽略。
```

#### 4.6.2 Level 3：reference / scripts / templates

`donkey/core/workspace/templates/skills/example/reference/example.md.txt`：

```markdown
# Example Reference（Level 3 示例）

本文件演示 Skill 的 Level 3 内容——模型用内置 `@tool`（filesystem / commandline / webfetch）按需读取。

## 内容

此处填写 Skill 的深层参考文档（API 手册 / 术语表 / 长篇背景知识）。

- 模型**不**会主动加载本文件；
- 模型调用 `load_skill_example` 获得 Level 2 主体后，如需更深内容才会触发 `filesystem.read_file("skills/example/reference/example.md")`。
```

`donkey/core/workspace/templates/skills/example/scripts/example.py.txt`：

```python
"""Example Script（Level 3 示例）。

本文件演示 Skill 的 Level 3 内容——可由模型通过 `commandline.run_shell` 调用。
"""
import sys


def main() -> int:
    print("Hello from skills/example/scripts/example.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`donkey/core/workspace/templates/skills/example/templates/example.md.txt`：

```markdown
# Example Template（Level 3 示例）

本文件演示 Skill 的 Level 3 内容——模板文件（如 Jinja2 模板 / Markdown 模板）。

模型调用 `filesystem.read_file("skills/example/templates/example.md")` 后再渲染。

---

**Title**: {{ title }}
**Date**: {{ date }}

## Body

{{ body }}
```

### 4.7 模板清单追加条目（P3：+7 条 → 累计 53 条）

`donkey/core/workspace/templates/manifest.json` 在 P2 已有 46 条基础上**追加**如下 7 条（追加操作 = "在原 entries 数组末尾 push"，**不**修改 P2 已有条目）。下表是 **P3 完成后的最终形态（53 条）**：

```json
{
  "version": 1,
  "entries": [
    {"path": "instruction.md", "format": "markdown"},
    {"path": "providers/default.toml", "format": "toml"},
    {"path": "mcp/mcp.json", "format": "json"},
    {"path": "skills/example/SKILL.md", "format": "markdown"},
    {"path": "README.md", "format": "markdown"},
    {"path": "tools/README.md", "format": "markdown"},
    {"path": "mcp/README.md", "format": "markdown"},
    {"path": "skills/README.md", "format": "markdown"},
    {"path": "memory/README.md", "format": "markdown"},
    {"path": ".gitignore", "format": "text"},
    {"path": "providers/README.md", "format": "markdown"},
    {"path": "providers/openai.toml", "format": "toml"},
    {"path": "providers/anthropic.toml", "format": "toml"},
    {"path": "providers/google.toml", "format": "toml"},
    {"path": "providers/ollama.toml", "format": "toml"},
    {"path": "providers/xai.toml", "format": "toml"},
    {"path": "providers/mistral.toml", "format": "toml"},
    {"path": "providers/qwen.toml", "format": "toml"},
    {"path": "providers/deepseek.toml", "format": "toml"},
    {"path": "providers/doubao.toml", "format": "toml"},
    {"path": "providers/kimi.toml", "format": "toml"},
    {"path": "providers/zhipu.toml", "format": "toml"},
    {"path": "providers/minimax.toml", "format": "toml"},
    {"path": "providers/tencent.toml", "format": "toml"},
    {"path": "providers/xiaomi.toml", "format": "toml"},
    {"path": "providers/stepfun.toml", "format": "toml"},
    {"path": "providers/openai-compatible.toml", "format": "toml"},
    {"path": "providers/meta.toml", "format": "toml"},
    {"path": "providers/bedrock.toml", "format": "toml"},
    {"path": "providers/groq.toml", "format": "toml"},
    {"path": "providers/fireworks.toml", "format": "toml"},
    {"path": "providers/together.toml", "format": "toml"},
    {"path": "providers/cohere.toml", "format": "toml"},
    {"path": "providers/perplexity.toml", "format": "toml"},
    {"path": "providers/databricks.toml", "format": "toml"},
    {"path": "providers/cerebras.toml", "format": "toml"},
    {"path": "providers/openrouter.toml", "format": "toml"},
    {"path": "tools", "format": "directory"},
    {"path": "mcp", "format": "directory"},
    {"path": "skills", "format": "directory"},
    {"path": "skills/example", "format": "directory"},
    {"path": "memory", "format": "directory"},
    {"path": "providers", "format": "directory"},
    {"path": "memory/sessions.sqlite3", "format": "sqlite3"},
    {"path": "memory/store.sqlite3", "format": "sqlite3"},
    {"path": "memory/knowledge.sqlite3", "format": "sqlite3"},
    {"path": "tools/__init__.py", "format": "python"},
    {"path": "tools/filesystem.py", "format": "python"},
    {"path": "tools/commandline.py", "format": "python"},
    {"path": "tools/webfetch.py", "format": "python"},
    {"path": "skills/example/reference/example.md", "format": "markdown"},
    {"path": "skills/example/scripts/example.py", "format": "python"},
    {"path": "skills/example/templates/example.md", "format": "markdown"}
  ]
}
```

**spec 要求**：

- `format` 字段取值：`markdown` / `toml` / `json` / `python` / `text` / `directory` / `sqlite3`；
- P3 追加的 `tools/__init__.py` + 3 个内置 tool + 3 个 Skills Level 3 示例 共 **7** 条新 entry（叠加 P1 的 3 条 + P2 的 43 条 → 累计 **46** 条 → **本 Phase 结束后累计 53 条**，即 v1 baseline）；
- `load_template_manifest()` 由 **F001-P2** 实现并已做 schema 校验（F001-P1 只**建档**清单、**不加载不解析**，spec FR-029）；本 Phase 不修改 manifest 加载逻辑——P2 的 `render_templates` 已能驱动新条目。

### 4.8 单元测试（`tests/unit/test_builtin_tools.py`）

**spec 必须列出**下列单测用例（**至少 8 个**）：

| 用例 | 输入 | 期望 |
|---|---|---|
| `test_filesystem_read_write` | write_file → read_file | 内容一致 |
| `test_filesystem_copy_move_delete` | copy / move / delete 三件套 | 操作符合预期 |
| `test_filesystem_list_dir_stat` | list_dir / stat | 返回结构正确 |
| `test_commandline_run_shell_echo` | `run_shell("echo hello")` | 返回 `"hello\n"`，`timed_out=False` |
| `test_commandline_run_shell_timeout` | `run_shell("sleep 5", timeout=1)` | 返回 `timed_out=True` |
| `test_webfetch_get_mock` | 用 pytest-httpx mock 一个 GET 200 | 返回 JSON 含 `status_code=200`, `body="..."` |
| `test_webfetch_timeout` | 用 pytest-httpx mock 延迟 5s + timeout=1 | **抛 `httpx.TimeoutException`**（模板的 `fetch_url` **不**捕获超时——异常透传给调用方，由 `ToolTimeoutError`（exit 33）在 F004 run 域统一映射） |
| `test_tools_init_importable` | `from tools import filesystem, commandline, webfetch` | 无异常；每个模块至少 1 个 `@tool` 函数 |

### 4.9 集成测试（`tests/integration/test_init_to_load.py`）

**spec 必须列出**以下集成测试（**端到端集成预演**——**仅做 import 路径 + 函数签名测试，不做 F002 静态格式检查**）：

| 用例 | 验证内容 |
|---|---|
| `test_init_then_import_filesystem` | `donkey init` 后 `from tools.filesystem import read_file` 等 import 语句无异常 |
| `test_init_then_import_commandline` | `from tools.commandline import run_shell` + 调一次 `run_shell("echo integration")` |
| `test_init_then_import_webfetch` | `from tools.webfetch import fetch_url` + 调一次（用 pytest-httpx mock） |

### 4.10 verify 脚本（`tests/e2e/phase/verify_phase_f001_p3.py`）

**黑盒测试**（禁止 import `donkey.*` 业务代码；只跑 `subprocess.run(["donkey", ...])`），11 个断言对应 §6 退出条件。

---

## 5. 异常退出码表（Phase 全量 Error class 映射）

| Error class（`donkey.core.exceptions`） | exit code | 触发条件 | 报错概率 |
|---|---|---|---|
| `BuiltinToolGenerationError` | **4** | 内置 `@tool` + Skills example 生成失败（**合并三项**：filesystem/commandline/webfetch 写入失败、SKILL.md 三层写入失败、集成预演 import 失败）。用户修复动作相同：重装 donkey / 检查权限 / 重试 init；按奥卡姆剃刀合并到 1 个码值 | 低 |
| exit 5–10 | （预留） | 留给 v1.x 试运行期新错误 | — |

**奥卡姆剃刀原则**：本 Phase 仅占 1 个码值（4）。原本可能拆分为 `BuiltinToolWriteError`（写入失败）/ `SkillsExampleWriteError`（Skills 三层失败）/ `EndToEndVerifyError`（集成预演失败）三个，对用户而言修复动作相同（重装 / 检查权限 / 重试），合并为单一 `BuiltinToolGenerationError` —— 若分开分配会浪费 2 个码值给稀有错误。

---

## 6. 退出条件（Exit Gate）

**`tests/e2e/phase/verify_phase_f001_p3.py` 必须跑通以下 11 个断言**（顺序固定，每条独立可测）：

### 6.1 生成的 workspace 含 3 个 builtin tool + tools/__init__.py + tools/README.md

```python
def test_scenario_1_builtin_tools_present(tmp_path):
    """场景 1：init 后含 3 个 builtin tool + __init__.py + README.md"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    assert (ws / "tools" / "__init__.py").exists()
    assert (ws / "tools" / "filesystem.py").exists()
    assert (ws / "tools" / "commandline.py").exists()
    assert (ws / "tools" / "webfetch.py").exists()
    assert (ws / "tools" / "README.md").exists()
```

### 6.2 三个 builtin tool 文件均可 import，每个 `@tool` 函数有完整 docstring

```python
def test_scenario_2_tools_importable_with_docstrings(tmp_path):
    """场景 2：3 个 builtin tool 可 import，每个 @tool 有 docstring"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sys.path.insert(0, str(ws))
    try:
        from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
        for fn in [read_file, write_file, copy_file, move_file, delete_file, list_dir, stat]:
            assert fn.__doc__ is not None and len(fn.__doc__) > 20
        from tools.commandline import run_shell
        assert run_shell.__doc__ is not None and len(run_shell.__doc__) > 20
        from tools.webfetch import fetch_url
        assert fetch_url.__doc__ is not None and len(fetch_url.__doc__) > 20
    finally:
        sys.path.remove(str(ws))
```

### 6.3 `commandline.run_shell("echo hello")` 返回 `"hello\n"`

```python
def test_scenario_3_commandline_run_shell_echo(tmp_path):
    """场景 3：run_shell("echo hello") 集成测试"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sys.path.insert(0, str(ws))
    try:
        from tools.commandline import run_shell
        result = run_shell.invoke({"command": "echo hello"})
        result_dict = json.loads(result)
        assert "hello" in result_dict["stdout"]
        assert result_dict["returncode"] == 0
    finally:
        sys.path.remove(str(ws))
```

### 6.4 `filesystem.py` 7 个 `@tool` 单元测试全绿

```python
def test_scenario_4_filesystem_seven_tools(tmp_path):
    """场景 4：filesystem.py 7 个 @tool 单元测试"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sys.path.insert(0, str(ws))
    try:
        from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
        # write + read
        write_file.invoke({"path": str(ws / "test.txt"), "content": "hi"})
        assert "hi" in read_file.invoke({"path": str(ws / "test.txt")})
        # copy + move
        copy_file.invoke({"src": str(ws / "test.txt"), "dst": str(ws / "test_copy.txt")})
        assert (ws / "test_copy.txt").exists()
        # list_dir
        names = list_dir.invoke({"path": str(ws)})
        assert "test.txt" in names
        # stat —— 返回 dict（不是 JSON 字符串），直接取字段
        s = stat.invoke({"path": str(ws / "test.txt")})
        assert s["is_file"] is True
        assert s["size"] > 0
        # delete
        delete_file.invoke({"path": str(ws / "test_copy.txt")})
        assert not (ws / "test_copy.txt").exists()
    finally:
        sys.path.remove(str(ws))
```

### 6.5 `webfetch.py` HTTP mock 测试通过

```python
def test_scenario_5_webfetch_http_mock(tmp_path, httpx_mock):
    """场景 5：webfetch HTTP mock 测试（pytest-httpx 的 httpx_mock fixture）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sys.path.insert(0, str(ws))
    try:
        from tools.webfetch import fetch_url
        httpx_mock.add_response(
            url="https://example.com",
            method="GET",
            status_code=200,
            text="mocked body",
        )
        result = fetch_url.invoke({"url": "https://example.com"})
        result_dict = json.loads(result)
        assert result_dict["status_code"] == 200
        assert "mocked body" in result_dict["body"]
    finally:
        sys.path.remove(str(ws))
```

### 6.6 Skills example 三层完整

```python
def test_scenario_6_skills_three_levels(tmp_path):
    """场景 6：SKILL.md frontmatter 合法 + Level 2 非空 + Level 3 含至少 1 个文件"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    skill_path = ws / "skills" / "example" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    # Level 1: frontmatter
    assert text.startswith("---\n")
    assert "name: example" in text
    assert "description:" in text
    # Level 2: markdown body 非空
    assert "Level 2" in text
    # Level 3: 至少 1 个文件（reference 或 scripts 或 templates）
    level3_count = 0
    for sub in ["reference", "scripts", "templates"]:
        sub_dir = ws / "skills" / "example" / sub
        if sub_dir.is_dir():
            level3_count += sum(1 for _ in sub_dir.iterdir())
    assert level3_count >= 1
```

### 6.7 `tools/` 子目录内的 3 个内置工具**不**含 `glob_search` / `grep_search`

```python
def test_scenario_7_no_glob_grep_in_builtin(tmp_path):
    """场景 7：3 个 builtin tool 文件不含 glob_search / grep_search"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    for tool_file in [ws / "tools" / "filesystem.py",
                      ws / "tools" / "commandline.py",
                      ws / "tools" / "webfetch.py"]:
        text = tool_file.read_text(encoding="utf-8")
        assert "glob_search" not in text
        assert "grep_search" not in text
```

### 6.8 幂等场景 2：用户 `rm filesystem.py` 后 init 补齐

```python
def test_scenario_8_idempotent_replenish(tmp_path):
    """场景 2 子操作：rm filesystem.py 后 init 补齐"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    (ws / "tools" / "filesystem.py").unlink()
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (ws / "tools" / "filesystem.py").exists()
```

### 6.9 `--force` 场景 3：用户自建 `tools/my_custom_tool.py`（不在清单内）后 `--force` 不删

```python
def test_scenario_9_force_preserves_user_tool(tmp_path):
    """场景 3：--force 不动用户的 tools/my_custom_tool.py（不在 manifest）"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    user_tool = ws / "tools" / "my_custom_tool.py"
    user_tool.write_text("# 用户自定义工具\n", encoding="utf-8")

    result = subprocess.run(["donkey", "init", str(ws), "--force"], capture_output=True, text=True)
    assert result.returncode == 0
    assert user_tool.exists()  # 用户自定义 tool 不动
    # filesystem.py 被恢复出厂
    fs_content = (ws / "tools" / "filesystem.py").read_text(encoding="utf-8")
    assert "用户自定义工具" not in fs_content
```

### 6.10 集成预演：`from tools.filesystem import read_file` 等 import 语句无异常

```python
def test_scenario_10_integration_imports(tmp_path):
    """场景 10：集成预演——所有 builtin tool 可正常 import"""
    ws = tmp_path / "ws"
    subprocess.run(["donkey", "init", str(ws)], check=True, capture_output=True)
    sys.path.insert(0, str(ws))
    try:
        from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
        from tools.commandline import run_shell
        from tools.webfetch import fetch_url
        # 每个 @tool 函数存在且可调用
        for fn in [read_file, write_file, copy_file, move_file, delete_file, list_dir, stat, run_shell, fetch_url]:
            assert callable(fn)
    finally:
        sys.path.remove(str(ws))
```

### 6.11 不做 F002 静态检查

```python
def test_scenario_11_no_f002_static_check(tmp_path):
    """场景 11：P3 init 后不跑 F002 静态检查（属 F002 域）"""
    ws = tmp_path / "ws"
    result = subprocess.run(["donkey", "init", str(ws)], capture_output=True, text=True)
    assert result.returncode == 0
    # 即便 builtin tool 文件有问题（人为改坏），init 阶段也不应跑 F002 检查
    # F002 才会校验
```

### 6.12 退出条件总览

verify_phase_f001_p3.py 的 11 个 `test_*` 函数全部 PASS → F001-P3 完成。**F001 整体完成**。

---

## 7. 可执行测试命令列表（"Phase 完成" 的硬性证据）

按以下顺序执行，全部 PASS 即视为 Phase 完成（**Phase 完成 = F001 `donkey init` 整体完成**）：

1. **前置 Phase 套件（F001-P1 + F001-P2）**：
   ```bash
   pytest tests/e2e/phase/verify_phase_f001_p1.py -v
   pytest tests/e2e/phase/verify_phase_f001_p2.py -v
   pytest tests/unit/test_init_workspace.py -v
   pytest tests/unit/test_template_skeleton.py -v
   ```
   必须全绿（验证 F001-P1 / F001-P2 退出条件未被破坏）。

2. **本 Phase 套件**：
   ```bash
   pytest tests/unit/test_builtin_tools.py -v                    # 至少 8 个
   pytest tests/integration/test_init_to_load.py -v              # 至少 3 个
   pytest tests/e2e/phase/verify_phase_f001_p3.py -v             # 11 个
   ```

3. **静态检查**：
   ```bash
   ruff check donkey/ tests/
   mypy donkey/ tests/
   ```

4. **CLI 手动冒烟（可选）**：
   ```bash
   donkey init /tmp/test-ws
   ls /tmp/test-ws/tools  # 应含 filesystem.py / commandline.py / webfetch.py / __init__.py / README.md
   python -c "import sys; sys.path.insert(0, '/tmp/test-ws'); from tools.commandline import run_shell; print(run_shell.invoke({'command': 'echo hi'}))"
   ```

5. **完整 CI 套件**：
   ```bash
   pytest tests/ -v
   ```
   F001-P1 / P2 / P3 全部测试 PASS；其它 Phase（F002 ~ F006）的测试允许 FAIL。

---

## 8. 绝对不做清单（推迟到后续 Phase / Feature）

| 不做的内容 | 推迟到 |
|---|---|
| 任何 LangChain 中间件挂载（`ToolErrorMiddleware` / `ToolRetryMiddleware` / `ModelRetryMiddleware` / `SummarizationMiddleware` / `ModelCallLimitMiddleware` / `PIIMiddleware` / `TodoListMiddleware` / `LLMToolSelectorMiddleware` / `ContextEditingMiddleware` / `FilesystemFileSearchMiddleware`） | F004 (`donkey run`) |
| `init_chat_model` / 模型连通性测试（`providers/` 目录解析 + ping） | F002 (`donkey load`) |
| sqlite3 数据库文件 schema 构造（含 `memory/sessions.sqlite3` 的 SqliteSaver 表 + `sessions_metadata` + 索引） | F001-P2（`template_skeleton` 已实现 schema builder；详见 F001-P2 sqlite3_templates 模块） |
| 任何 `donkey load` 静态检查（`providers/` 字段 / mcp/mcp.json 字段 / SKILL.md 字段） | F002 (`donkey load`) |
| Skills 自研 loader 实现（Level 1 扫描 + Level 2 读取 + Level 3 工具集成 = `core/skills/loader.py`） | F004-P2 (`donkey run` → Skills 加载) |
| `donkey session list` / `new` / `remove` / `import` 等子命令 | F003 (`donkey session`) |
| `donkey run` Agent Loop / LangGraph 图编译 / 10 个 v1 中间件挂载 | F004 (`donkey run`) |
| `donkey web` 前端 | F005 |
| `donkey gui` Electron 包壳 | F006 |
| 引入 `ShellToolMiddleware` / `FilesystemMiddleware`（deepagents）/ `SubAgentMiddleware` / `SkillsMiddleware`（deepagents）等任何禁用中间件 | 永不使用（N-02 / N-12 / 宪法 §2.7.2） |
| workspace 路径 basename 命名校验（v1 不引入） | v2+ |
| 修改 F001-P1 / F001-P2 已实现的代码（仅允许**追加**——F001-P1 的 4 个 init 函数 / F001-P2 的 `render_templates` / `manifest.py` / `sqlite3_templates.py` 一律不动） | — |
| 引入 langsmith 任何形态 | 永不使用（N-12 / §3.2 永不使用清单） |
| 引入 deepagents 包 | 永不使用（宪法 §3.2） |
| 在 `tools/filesystem.py` 内实现 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 在 F004 中间件域接管） | —（永不在 `tools/filesystem.py` 内实现） |

---

## 9. 技术栈与依赖硬约束

- **Python 3.11+**；
- **HTTP 客户端**：`httpx`（用于 `tools/webfetch.py` 模板与测试）；`pytest-httpx` 用于 mock；
- **LangChain 内置工具装饰器**：`from langchain_core.tools import tool` —— `@tool` 是 LangChain 内置功能，**不**违反 N-04 / N-12；N-04 仅约束 `cli` / `web` / `gui` 客户端不直接 import langchain，**`donkey.core` 允许使用 langchain 库 API**；
- **测试**：pytest + pytest-httpx；
- **静态检查**：ruff + mypy；
- **CI**：GitHub Actions。

### 9.1 永不使用清单

- ❌ LangSmith 任何形态（详见 N-12）；
- ❌ deepagents 包（`create_deep_agent` / FilesystemMiddleware / SubAgentMiddleware / RubricMiddleware / SkillsMiddleware / MemoryMiddleware）；
- ❌ `ShellToolMiddleware`（持久 shell + HITL 冲突，由 `tools/commandline.py` 替代）；
- ❌ subagent / 子智能体任何目录或字段；
- ❌ `tools/filesystem.py` 内含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管）；
- ❌ `import langsmith` 或 `langchain.langsmith` / `langchain_community.langsmith` / `langgraph.langsmith` 等任何 langsmith.* 子包。

### 9.2 分层架构硬约束（N-01 ~ N-12）

| 编号 | 条款 | 本 Phase 落地 |
|---|---|---|
| **N-01** | workspace 内禁止 `agent.py` / `main.py` | ✓ 生成的 3 个 builtin tool 文件均不含 `if __name__ == "__main__": sys.exit(...)` 形式入口（Skills example 的 `scripts/example.py` 是 Level 3 演示脚本，**允许**含 `__main__` 块，但**不是** workspace 入口） |
| **N-02** | 禁止 subagent / 子智能体相关目录或字段 | ✓ 生成的 3 个 builtin tool 无任何 subagent 字段；Skills example 不涉及 subagent |
| **N-03** | `donkey.core` 禁止 import `cli` / `web` / `gui` | ✓ 本 Phase 不修改 `core/` 下任何已有模块；只追加 .txt 模板源 |
| **N-04** | `cli` 禁止直接 import `langchain` / `langgraph` / `sqlite3` | ✓ 本 Phase 仅修改 `cli/cli_client.py` 1 行（追加异常映射）；无 langchain import |
| **N-05** | `donkey.core` 禁止 import `argparse` / `sys.argv` / `click` / `typer` | ✓ |
| **N-08** | exit code 段位不重叠 | ✓ 本 Phase 占 exit 4，落在 F001 段位 1–10 内 |
| **N-11** | v1 必须同时交付 cli / web / gui 三种客户端 | 本 Phase 不涉及客户端（仅 init 业务）；cli 端 F001-P1 已落地；web / gui 推迟到 F005 / F006 |
| **N-12** | 禁止 LangSmith | ✓ |

---

## 10. 验收标准（business AC）

| 验收项 | 说明 |
|---|---|
| **AC-1（workspace 加载通过率 100%）** | 本 Phase 仅保证"生成模板"；AC-1 的通过口径是"**配置完成后** 100% 通过"——出厂态（26 个 stub 全 `enabled = false` + `api_key = ""`）在 F002 **静态检查**阶段即报 exit 11（零 enabled provider + 三步配置指引），属**预期行为**（详见立项书 §3.2.3 AC-1 ③ + 宪法 §4.6 AC-1 出厂态豁免）；本 Phase 不承担 F002 的 9 项检查 |
| **AC-2（路径无关）** | init 后 workspace 移到任意路径，import 路径仍能正确发现 `@tool` 函数（本 Phase 通过 `tools/__init__.py` + 集成测试落地） |
| **AC-3（init 幂等）** | 重复执行 `donkey init <已存在 ws>` 不破坏用户内容；`--force` 仅重置 manifest 内模板，不动 manifest 外（用户内容） |
| **AC-4（换 workspace 切换模型 / 工具 / Skills / 提示词）** | workspace 模板含 `instruction.md` / `providers/` / `tools/` / `skills/`，未来 F004 run 时模型 / 工具 / Skills / 提示词均从 workspace 加载——本 Phase 完成"workspace 模板就绪"前置条件 |
| **AC-5（v1 模板不承诺 diff 审阅）** | workspace 内不含 `agent.py` / `main.py` 等 diff 审阅入口 |

**技术验收**：F001 段位 1–10 中 4 个码值（1 / 2 / 3 / 4）全部实测通过；预留码 5–10 不触发；F001 整体完成。

---

## 11. Spec 输出格式要求（给 `/speckit.specify` 的提示）

执行 `/speckit.specify` 后生成的 `specs/001-donkey-init-workspace/phase-3-builtin-tools/spec.md` **必须**包含：

1. **User Stories**：按优先级 P1 → P11 列出 11 个核心场景（对应 §6 的 11 个 verify 断言）；
2. **Functional Requirements (FR-001 ~ FR-NNN)**：覆盖 §4 的 10 个子节（4.1 ~ 4.10），含 9 个 `@tool` 函数签名、Skills 三层文件清单、manifest 追加条目；FR 中如需引用 F001-P1 / F001-P2 已实现的函数（`validate_init_request` / `render_templates` / `init_workspace_inner` 等），仅引用**函数签名与行为契约**，不复述其实现细节（详见 §3.2 函数契约小节）；
3. **Edge Cases**：本 Phase 边界条件（用户自定义 `tools/*.py` 不被 `--force` 删 / 用户 rm builtin tool 后 init 补齐 / Skills Level 3 目录被 `--force` 递归清空 / 等）；
4. **Success Criteria (SC-001 ~ SC-NNN)**：可量化的退出条件（"11 个 verify 断言全部 PASS"、"F001-P1 7 个 + F001-P2 14 个断言仍全绿"、"单测 8 个 + 集成测试 3 个 + verify 11 个全绿"、"ruff + mypy 零 error"等）；
5. **Key Entities**：`BuiltinToolGenerationError` 异常类；`filesystem.read_file` / `write_file` / `copy_file` / `move_file` / `delete_file` / `list_dir` / `stat` / `commandline.run_shell` / `webfetch.fetch_url` 共 9 个 `@tool` 工具函数；Skills Level 1/2/3 三层模型；
6. **Assumptions**：F001-P1 (`cli_validation`) + F001-P2 (`template_skeleton`) 均已完成并退出；`langchain_core.tools.tool` 装饰器可用；`httpx` 与 `pytest-httpx` 已安装。

**Spec 禁止**包含的内容（留给 `/speckit.plan` 处理）：

- 具体实现步骤（如"先写 filesystem.py 再写 commandline.py 再写 webfetch.py"）—— plan 才规定顺序；
- 测试用例的具体代码（除 §6 / §4.8 / §4.9 中已作为参考示例给出的）；
- 依赖包版本号。

---

**End of F001-P3 spec input. F001 `donkey init` 整体完成的最后 Phase.** 将本文件整体作为参数传入 `/speckit.specify` 即可。
