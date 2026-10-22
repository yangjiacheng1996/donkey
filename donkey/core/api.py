"""donkey 核心库门面 API —— 客户端三端（cli / web / gui）共用的唯一业务入口
（宪法 N-08 / D-08）。

本模块 MUST NOT 感知进程退出码、 MUST NOT 打印、 MUST NOT 退出进程
（宪法 N-05 / N-03）。
"""

from dataclasses import dataclass
from pathlib import Path

from donkey.core.workspace.init import validate_init_request


@dataclass(frozen=True)
class InitResult:
    """``init_workspace`` 的返回契约对象（不可变）。

    字段与顺序由 spec FR-006 冻结，后续阶段（F002 / F003 / F004）依赖此契约。

    - ``workspace_path``：workspace 的绝对路径；
    - ``name``：workspace 名称——未指定时为路径末段名，库 API 显式传入非空
      名称时以其为准；
    - ``force``：本次是否请求强制重置；
    - ``templates_loaded``：已加载的模板清单条目数——P1 恒为 ``0``；
    - ``files_created``：本次实际新建的文件数——P1 恒为 ``0``；
    - ``files_skipped``：已存在而跳过的文件数——P1 恒为 ``0``。
    """

    workspace_path: Path
    name: str
    force: bool
    templates_loaded: int
    files_created: int
    files_skipped: int


def init_workspace(
    path: str | Path,
    name: str | None = None,
    force: bool = False,
) -> InitResult:
    """创建 workspace 根目录并返回结果契约对象。

    ``path`` 接受字符串与路径对象两种形态，内部统一解析为绝对路径；``name``
    缺省为 ``None``——此时名称取解析后路径的末段名，显式传入非空字符串时以
    该值为准，传入空字符串视为未指定（spec FR-005）；``force`` 缺省为假值。

    失败：抛出 ``WorkspaceInitError`` 的子类（``PathNotFoundError`` /
    ``PathPermissionError``）——本层 MUST NOT 返回退出码。
    """
    abs_path, resolved_name, resolved_force = validate_init_request(path, name, force)
    abs_path.mkdir(exist_ok=True)
    return InitResult(
        workspace_path=abs_path,
        name=resolved_name,
        force=resolved_force,
        templates_loaded=0,
        files_created=0,
        files_skipped=0,
    )
