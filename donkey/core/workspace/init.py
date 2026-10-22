"""workspace 路径解析、权限校验与综合校验入口。

分层约束（宪法 N-05 / N-03）：本模块 MUST NOT 依赖命令行参数解析或进程参数
读取（``argparse`` / ``click`` / ``typer`` 与进程参数属客户端层职责），MUST
NOT 反向依赖任何客户端层，MUST NOT 感知进程退出码——失败一律以异常表达。

三个校验能力 MUST 无副作用：不写文件、不建目录、不改任何状态（spec FR-016）。
"""

import os
from pathlib import Path

from donkey.core.exceptions import PathNotFoundError, PathPermissionError

#: 路径类失败统一的"下一步"提示（spec FR-019 / SC-012）。
_NEXT_STEP = "下一步：请先建目录，或换路径到父目录已存在的目标。"


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
