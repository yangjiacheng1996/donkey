"""workspace 路径解析、权限校验、综合校验入口与模板骨架渲染。

分层约束（宪法 N-05 / N-03）：本模块 MUST NOT 依赖命令行参数解析或进程参数
读取（``argparse`` / ``click`` / ``typer`` 与进程参数属客户端层职责），MUST
NOT 反向依赖任何客户端层，MUST NOT 感知进程退出码——失败一律以异常表达。

三个校验能力 MUST 无副作用：不写文件、不建目录、不改任何状态（spec FR-016）。

模板清单加载与渲染能力（F001-P2）MUST 与校验能力分离成独立函数：
``load_template_manifest`` 只读安装包内的清单，``render_templates`` 只往
workspace 内落地模板，二者均可通过路径入参注入 —— 使单元测试得以在**不破坏
已安装包**的前提下构造失败分支（spec FR-006 / FR-056）。
"""

import json
import os
from pathlib import Path
from typing import Any

from donkey.core.exceptions import (
    _NEXT_STEP_TEMPLATE,
    PathNotFoundError,
    PathPermissionError,
    TemplateGenerationError,
)
from donkey.core.workspace.manifest import write_workspace_manifest
from donkey.core.workspace.sqlite3_templates import (
    build_knowledge_sqlite,
    build_sessions_sqlite,
    build_store_sqlite,
)

#: 路径类失败统一的"下一步"提示（spec FR-019 / SC-012）。
_NEXT_STEP = "下一步：请先建目录，或换路径到父目录已存在的目标。"

#: 安装包内的模板根目录（与模板清单同目录）。
DEFAULT_TEMPLATES_ROOT = Path(__file__).parent / "templates"

#: 模板条目 ``format`` 的 7 种受支持取值（spec FR-003 / data-model.md §2）。
_TEMPLATE_FORMATS = frozenset(
    {"markdown", "toml", "json", "python", "text", "directory", "sqlite3"}
)

#: 文本模板类取值 —— 其源文件路径为 ``<条目路径>.txt``（spec FR-007）。
_TEXT_FORMATS = frozenset({"markdown", "toml", "json", "python", "text"})

#: sqlite3 条目 → 结构构造器的分派表（按目标文件名末段，spec FR-030 ~ FR-032）。
_SQLITE3_BUILDERS = {
    "sessions.sqlite3": build_sessions_sqlite,
    "store.sqlite3": build_store_sqlite,
    "knowledge.sqlite3": build_knowledge_sqlite,
}

#: **契约库**（变更记录契约）在强制重置下的条目级豁免（spec FR-105 / research.md R-07）。
#:
#: 契约库与用户的自写工具**是一套的** —— 它已是工作区的"活代码"，覆盖它等于
#: 单方面毁掉用户代码的依赖。故带强制标志时，一旦工作区里已存在契约库，
#: MUST 保留它原样。
#:
#: 该豁免只作用于**这一个**条目 —— P2 的通用通则（清单内文本条目带强制标志
#: 时先删后重建）对其余全部条目原样成立（spec FR-069）。
_FORCE_EXEMPT_ENTRY = "tools/changes.py"


def check_path(path: str | Path) -> Path:
    """把输入路径解析为绝对路径，并校验其作为 workspace 根的合法性。

    接受 ``str`` 或 ``Path`` 两种形态，相对路径以进程工作目录为解析基准。

    返回：解析后的绝对路径。

    失败：``PathNotFoundError``（退出码 1）——父目录不存在、路径含非法字符
    （NUL）、解析后末段名为空（文件系统根 / 盘符根 / UNC 共享根）、空字符串
    路径、目标存在但不是目录、父目录是文件、悬空符号链接、路径过长。

    本函数 MUST 无副作用（spec FR-016），返回的绝对路径可被调用方直接使用。
    """
    raw = path if isinstance(path, str) else str(path)

    # 空字符串路径 MUST 在 resolve() 之前判空——``Path("")`` 会被 pathlib 折叠
    # 为 ``"."``，若先 resolve 再判末段名，空路径会被误判为合法（spec FR-030）。
    # 「空」只认长度为 0 的空串；纯空白串按普通路径处理。
    if isinstance(path, str) and len(raw) == 0:
        raise PathNotFoundError(f"路径不能为空：{raw!r}。{_NEXT_STEP}")

    # 悬空符号链接 MUST 在 resolve() 之前对**原始输入路径**判定——resolve 会把
    # 悬空链接静默解析成目标路径，谓词恒为假，该分支永不可达（spec FR-030）。
    if os.path.islink(raw) and not os.path.exists(raw):
        raise PathNotFoundError(f"路径是悬空符号链接（指向不存在的目标）：{raw}。{_NEXT_STEP}")

    try:
        abs_path = Path(raw).resolve(strict=False)
    except ValueError as exc:
        # 非法字符（如内嵌 NUL）——``resolve()`` 抛的是 ValueError 而非 OSError。
        raise PathNotFoundError(f"路径含非法字符：{raw!r}。{_NEXT_STEP}") from exc
    except OSError as exc:
        raise PathNotFoundError(f"路径解析失败：{raw!r}。{_NEXT_STEP}") from exc

    # 解析后末段名为空 ⇒ 路径非法——一次覆盖文件系统根 / 盘符根 / UNC 共享根
    # 等一切根形态（spec FR-012 / research.md R-03）。
    if not abs_path.name:
        raise PathNotFoundError(f"根目录不可作为 workspace 根：{abs_path}。{_NEXT_STEP}")

    parent = abs_path.parent
    try:
        # 全部 stat 类调用 MUST 置于统一的 try/except OSError 内——超长路径上
        # ``Path.exists()`` 会**抛出** OSError(ENAMETOOLONG) 而非返回 False
        # （research.md R-05 / spec FR-030）。
        parent_exists = parent.exists()
        parent_is_dir = parent.is_dir() if parent_exists else False
        target_exists = abs_path.exists()
        target_is_dir = abs_path.is_dir() if target_exists else False
    except OSError as exc:
        raise PathNotFoundError(f"路径不可访问（可能超出长度限制）：{raw!r}。{_NEXT_STEP}") from exc

    if not parent_exists:
        raise PathNotFoundError(f"父目录不存在：{parent}。{_NEXT_STEP}")
    if not parent_is_dir:
        raise PathNotFoundError(f"父目录不是目录：{parent}。{_NEXT_STEP}")
    if target_exists and not target_is_dir:
        raise PathNotFoundError(f"目标已存在且不是目录：{abs_path}。{_NEXT_STEP}")

    return abs_path


def check_permission(path: Path) -> None:
    """校验当前用户对 ``path`` 的访问权限。

    目标**不存在** → 校验父目录的写权限 + 执行权限（能否在其中创建子项）；
    目标**已存在** → 校验目标自身的读 + 写 + 执行权限。

    返回：``None``（权限充足）。

    失败：``PathPermissionError``（退出码 2）——错误信息同时含缺失的权限
    种类与对应路径，并附一条用户可执行的下一步（spec FR-015 / FR-019）。

    判定使用 ``os.access(path, mode)``：``0o555`` 目录（无写位）即被拒——按
    POSIX 语义即使以 root 运行 ``os.access(dir, W_OK)`` 亦为 False，故该模拟
    **不依赖特权账号**（research.md R-04）。

    本函数 MUST 无副作用（spec FR-016）。
    """
    target_exists = path.exists()

    required: tuple[tuple[int, str], ...]
    if target_exists:
        checked_path = path
        required = (
            (os.R_OK, "读权限"),
            (os.W_OK, "写权限"),
            (os.X_OK, "执行权限"),
        )
    else:
        checked_path = path.parent
        required = (
            (os.W_OK, "写权限"),
            (os.X_OK, "执行权限"),
        )

    for mode, kind in required:
        if not os.access(checked_path, mode):
            raise PathPermissionError(
                f"缺少{kind}：{checked_path}。下一步：请调整权限（chmod）后再试。"
            )


def validate_init_request(
    path: str | Path,
    name: str | None,
    force: bool,
) -> tuple[Path, str, bool]:
    """串联"路径解析 → 权限校验 → 名称定夺"，交付综合校验三元组。

    名称定夺规则：``name`` 为 ``None`` 或空串时取解析后路径的末段名；为非空串
    时采用该值（spec FR-005 / FR-017）。CLI 通道永不传该参数，故命令行名称
    恒由路径派生。

    返回：``(绝对路径, 最终名称, 强制标志)``。

    失败：``PathNotFoundError`` / ``PathPermissionError``。MUST NOT 把"目标
    已存在"当错误（幂等设计，spec FR-008）。
    """
    abs_path = check_path(path)
    check_permission(abs_path)
    resolved_name = name if name else abs_path.name
    return abs_path, resolved_name, force


# --- F001-P2：模板清单加载与模板骨架渲染 ---------------------------------------


def load_template_manifest(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    """加载安装包内的模板清单。

    默认路径：``DEFAULT_TEMPLATES_ROOT / "manifest.json"``（模板清单 MUST 位于
    安装包内、与模板源文件同目录，spec FR-004）。它与 workspace 根的工作区
    清单是**两个不同的文件**（宪法 §2.6）。

    schema 校验覆盖 data-model.md §2 的 V1 ~ V6：``version`` 为整数 /
    ``entries`` 为列表 / 每条目为对象 / 每条目含非空字符串 ``path`` /
    ``format`` 若存在则 ∈ 7 种受支持值（省略时按 ``text`` 处理）/ 文件本身
    为合法 JSON。

    返回：**未去重的原始条目列表**（长度即 ``templates_loaded`` 口径 —— 含
    目录条目、含重复条目）。去重由 :func:`render_templates` 承担
    （spec FR-002 / FR-026 / research.md R-15）。本函数 MUST NOT 就地修改
    条目。

    失败：清单缺失 / JSON 非法 / schema 非法 → ``TemplateGenerationError``
    （退出码 ``3``），MUST NOT 抛 ``PathNotFoundError`` —— 二者的用户修复动作
    不同（"重装 donkey" vs "建目录 / 换路径"，spec FR-038）。
    """
    path = (
        Path(manifest_path)
        if manifest_path is not None
        else DEFAULT_TEMPLATES_ROOT / "manifest.json"
    )
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TemplateGenerationError(
            f"模板清单缺失：{path}。{_NEXT_STEP_TEMPLATE}"
        ) from exc
    except OSError as exc:
        raise TemplateGenerationError(
            f"读取模板清单失败：{path}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TemplateGenerationError(
            f"模板清单不是合法 JSON：{path}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc

    if not isinstance(parsed, dict):
        raise TemplateGenerationError(
            f"模板清单结构非法（顶层不是对象）：{path}。{_NEXT_STEP_TEMPLATE}"
        )
    version = parsed.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise TemplateGenerationError(
            f"模板清单结构非法（version 不是整数）：{path}。{_NEXT_STEP_TEMPLATE}"
        )
    entries = parsed.get("entries")
    if not isinstance(entries, list):
        raise TemplateGenerationError(
            f"模板清单结构非法（entries 不是列表）：{path}。{_NEXT_STEP_TEMPLATE}"
        )

    validated: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise TemplateGenerationError(
                f"模板清单结构非法（条目不是对象）：{path}。{_NEXT_STEP_TEMPLATE}"
            )
        entry_path = entry.get("path")
        if not isinstance(entry_path, str) or not entry_path:
            raise TemplateGenerationError(
                f"模板清单结构非法（条目缺 path 或 path 为空）：{path}。{_NEXT_STEP_TEMPLATE}"
            )
        entry_format = entry.get("format", "text")
        if entry_format not in _TEMPLATE_FORMATS:
            raise TemplateGenerationError(
                f"模板清单结构非法（未知 format：{entry_format!r}）：{path}。"
                f"{_NEXT_STEP_TEMPLATE}"
            )
        validated.append(dict(entry))
    return validated


def _resolve_target(workspace_path: Path, relative: str) -> Path:
    """把条目的相对路径解析为 workspace 内的目标路径。

    目标 MUST 落在 workspace 根**之下** —— 父目录的递归创建仅限 workspace
    根之下（spec FR-012 / library-api §3.2 第 2 条）。
    """
    target = Path(os.path.normpath(Path(workspace_path) / relative))
    if not target.is_relative_to(Path(workspace_path)):
        raise TemplateGenerationError(
            f"模板条目路径越出 workspace 根：{relative}。{_NEXT_STEP_TEMPLATE}"
        )
    return target


def _ensure_parent(target: Path) -> None:
    """确保目标文件的父目录存在（渲染 MUST NOT 依赖条目顺序，spec FR-012）。"""
    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise TemplateGenerationError(
            f"创建模板父目录失败：{parent}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc


def _substitute_placeholders(content: str, name: str) -> str:
    """替换模板正文中的名字占位符。

    同时识别 ``{{ workspace_name }}`` 与 ``{{workspace_name}}`` 两种写法；其它
    ``{{ ... }}`` 原样保留 —— MUST NOT 报错、MUST NOT 替换为空串
    （spec FR-015）。名称含空格 / Unicode / 特殊字符时原样注入，不转义、
    不截断。
    """
    return content.replace("{{ workspace_name }}", name).replace("{{workspace_name}}", name)


def _render_text_template(
    templates_root: Path,
    target: Path,
    relative: str,
    name: str,
    force: bool,
) -> bool:
    """渲染一个文本模板类条目。

    返回：``True`` = 本次新建（计入 ``files_created``）；``False`` = 已存在
    而跳过（计入 ``files_skipped``）。
    """
    source = templates_root / f"{relative}.txt"
    if not source.exists():
        raise TemplateGenerationError(
            f"模板源缺失：{source}。{_NEXT_STEP_TEMPLATE}"
        )
    try:
        content = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateGenerationError(
            f"读取模板源失败：{source}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc

    if target.exists():
        if target.is_dir():
            raise TemplateGenerationError(
                f"目标路径已存在且是目录：{target}。{_NEXT_STEP_TEMPLATE}"
            )
        if not force:
            # "完全不动" —— 内容与 mtime 均不变（spec FR-008 / 不变量 I1）。
            return False
        try:
            target.unlink()
        except OSError as exc:
            raise TemplateGenerationError(
                f"删除目标文件失败：{target}（{exc}）。{_NEXT_STEP_TEMPLATE}"
            ) from exc

    _ensure_parent(target)
    payload = _substitute_placeholders(content, name)
    try:
        target.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise TemplateGenerationError(
            f"写入模板文件失败：{target}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc
    return True


def _render_directory_template(target: Path) -> None:
    """渲染一个目录类条目。

    已存在（无论是否带强制标志）→ **保留不变**：MUST NOT 删除目录本身、
    MUST NOT 删除目录内的**任何**文件（清单内外一律不动）；其内清单内文件
    的重置由各自的文本 / sqlite3 条目负责（spec FR-010 / 不变量 I3）。
    目录条目 MUST NOT 报错（spec Edge Cases「渲染与幂等类」）。
    """
    if target.exists():
        return
    _ensure_parent(target)
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise TemplateGenerationError(
            f"创建模板目录失败：{target}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc


def _render_sqlite3_template(target: Path, force: bool) -> bool:
    """渲染一个 sqlite3 条目（走结构构造器，spec FR-011 / FR-030）。

    返回：``True`` = 本次新建；``False`` = 已存在而跳过。
    """
    if target.exists():
        if target.is_dir():
            raise TemplateGenerationError(
                f"目标路径已存在且是目录：{target}。{_NEXT_STEP_TEMPLATE}"
            )
        if not force:
            # 完全不动 —— MUST NOT 校验其结构（schema 健康检查属 F002-P2）。
            return False
        # 连带删除同名 -wal / -shm 附属文件（防御性措施；实测陈旧 WAL 因盐值
        # 不匹配被安全忽略，MUST NOT 声称"不删必然导致旧数据回放"，
        # research.md R-03）。
        for suffix in ("", "-wal", "-shm"):
            sidecar = Path(f"{target}{suffix}")
            if sidecar.exists():
                try:
                    sidecar.unlink()
                except OSError as exc:
                    raise TemplateGenerationError(
                        f"删除记忆库文件失败：{sidecar}（{exc}）。{_NEXT_STEP_TEMPLATE}"
                    ) from exc

    builder = _SQLITE3_BUILDERS.get(target.name)
    if builder is None:
        raise TemplateGenerationError(
            f"未登记的 sqlite3 模板条目：{target.name}。{_NEXT_STEP_TEMPLATE}"
        )
    _ensure_parent(target)
    builder(target)
    return True


def render_templates(
    workspace_path: Path,
    name: str,
    force: bool,
    manifest_entries: list[dict[str, Any]],
    templates_root: Path | None = None,
) -> tuple[int, int]:
    """把模板清单渲染进 workspace。

    行为要点：

    - **先按唯一路径去重** —— 同一路径只处理一次，以重复项中**最后出现**的
      条目为准（其 ``format`` 与源模板生效）；MUST NOT 对同一路径既计 created
      又计 skipped（spec FR-002 / research.md R-15）。``render_templates`` 是
      公开 API，MUST NOT 假定入参已去重。
    - **MUST NOT 依赖条目顺序** —— 写任何文件前先确保其父目录存在
      （spec FR-012）。
    - 文本类条目的源路径为 ``templates_root / f"{条目路径}.txt"``
      （spec FR-007）；源缺失 → ``TemplateGenerationError``。
    - 目录类条目一律"不存在则创建、已存在则保留不变"（spec FR-010）。
    - sqlite3 类条目走结构构造器；带强制标志时先删主库 **+ 同名 ``-wal`` /
      ``-shm``** 再重建（spec FR-011）。
    - 任何 IO / sqlite 失败一律归一为 ``TemplateGenerationError``，MUST NOT
      逃逸裸异常（spec FR-014）。

    返回：``(files_created, files_skipped)`` —— 仅统计**文件型**条目（文本 +
    sqlite3），目录条目不计入，按唯一路径计一次（spec FR-017）。
    """
    workspace = Path(workspace_path)
    root = Path(templates_root) if templates_root is not None else DEFAULT_TEMPLATES_ROOT

    unique: dict[str, dict[str, Any]] = {}
    for entry in manifest_entries:
        entry_path = entry.get("path")
        if not isinstance(entry_path, str) or not entry_path:
            raise TemplateGenerationError(
                f"模板清单条目缺 path 或 path 为空。{_NEXT_STEP_TEMPLATE}"
            )
        # 后者覆盖前者 —— 重复项中最后出现的条目生效。
        unique[entry_path] = entry

    created = 0
    skipped = 0
    for relative, entry in unique.items():
        entry_format = entry.get("format", "text")
        target = _resolve_target(workspace, relative)

        if entry_format == "directory":
            _render_directory_template(target)
            continue
        if entry_format == "sqlite3":
            is_created = _render_sqlite3_template(target, force)
        elif entry_format in _TEXT_FORMATS:
            is_created = _render_text_template(root, target, relative, name, force)
        else:
            raise TemplateGenerationError(
                f"未登记的模板条目 format：{entry_format!r}（路径 {relative}）。"
                f"{_NEXT_STEP_TEMPLATE}"
            )

        if is_created:
            created += 1
        else:
            skipped += 1
    return created, skipped


def _entries_for_render(
    workspace_path: Path,
    manifest_entries: list[dict[str, Any]],
    force: bool,
) -> tuple[list[dict[str, Any]], int]:
    """算出传给渲染器的条目列表，以及被豁免而计入"跳过"的条目数。

    **条目级强制重置豁免**（spec FR-105 / research.md R-07）：带强制标志且
    工作区里**已存在**契约库时，把契约库条目从渲染列表中剔除 —— 契约库
    保留原样，不被覆盖。

    约束：

    - MUST 过滤进**一个新列表变量** —— MUST NOT 就地改写 ``manifest_entries``
      （``templates_loaded`` 取的是原始列表长度，就地过滤会让它变成 53）；
    - MUST 只豁免契约库**一个**条目 —— P2 的通用通则对其余条目原样成立
      （spec FR-069）；
    - ``render_templates`` 本身**一字不改**（通用渲染器 MUST NOT 被污染）；
    - 契约库**不存在**时 MUST 按出厂内容正常创建（与"无则增"通则一致）。

    返回：``(渲染用条目列表, 计入 skipped 的条目数)``。
    """
    if not force:
        return manifest_entries, 0

    exempt_target = Path(workspace_path) / _FORCE_EXEMPT_ENTRY
    if not exempt_target.exists():
        return manifest_entries, 0

    filtered = [
        entry
        for entry in manifest_entries
        if entry.get("path") != _FORCE_EXEMPT_ENTRY
    ]
    return filtered, 1


def init_workspace_inner(
    path: str | Path,
    name: str | None,
    force: bool,
) -> tuple[Path, str, bool, int, int, int]:
    """``donkey init`` 的内部初始化流程（五步流水线）。

    顺序固定（spec FR-027）：

    1. 前置校验（复用 P1 的 :func:`validate_init_request`）；
    2. 加载模板清单；
    3. 创建 workspace 根目录；
    4. 渲染模板骨架；
    5. 写入工作区清单。

    返回：``(绝对路径, 最终名称, 强制标志, 新建文件数, 跳过文件数, 清单条目总数)``。

    退出码按**阶段**切分（spec FR-038）：步骤 ③ 的一切失败（含磁盘满
    ``ENOSPC``）归 ``PathPermissionError``（退出码 ``2``）；步骤 ④ / ⑤ 的一切
    失败归 ``TemplateGenerationError``（退出码 ``3``）。

    步骤 ⑤ 失败 MUST **NOT** 回滚步骤 ④ —— 已落地的模板文件保留（不删除、
    不还原）；本 Phase MUST NOT 实现任何事务回滚机制（spec 澄清 #26 /
    plan R-16）。
    """
    abs_path, resolved_name, resolved_force = validate_init_request(path, name, force)

    manifest_entries = load_template_manifest()

    try:
        # MUST 只用 ``mkdir(exist_ok=True)`` —— 父目录缺失已在步骤 ① 判为路径
        # 类错误并拒绝，MUST NOT 用 ``parents=True`` 补建（spec FR-028）。
        abs_path.mkdir(exist_ok=True)
    except OSError as exc:
        raise PathPermissionError(
            f"创建 workspace 根目录失败：{abs_path}（{exc}）。{_NEXT_STEP}"
        ) from exc

    entries_for_render, exempt_skipped = _entries_for_render(
        abs_path, manifest_entries, resolved_force
    )
    created, skipped = render_templates(
        abs_path, resolved_name, resolved_force, entries_for_render
    )
    # 被豁免而保留的契约库计入"跳过" —— 它确实没有被创建。
    skipped += exempt_skipped

    write_workspace_manifest(abs_path, resolved_name, resolved_force)

    # ``manifest_total`` = 步骤 ② 已在手的**原始列表长度**（含重复条目）；
    # MUST NOT 为此二次调用 ``load_template_manifest()`` —— 会带来重复 IO 与
    # 第二个失败点，且与步骤 ② 的结果可能不自洽（spec FR-002 / FR-026）。
    return abs_path, resolved_name, resolved_force, created, skipped, len(manifest_entries)
