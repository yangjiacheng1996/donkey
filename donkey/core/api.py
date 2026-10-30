"""donkey 核心库门面 API —— 客户端三端（cli / web / gui）共用的唯一业务入口
（宪法 N-08 / D-08）。

本模块 MUST NOT 感知进程退出码、 MUST NOT 打印、 MUST NOT 退出进程
（宪法 N-05 / N-03）。
"""

from dataclasses import dataclass
from pathlib import Path

from donkey.core.workspace.init import InitItem, init_workspace_inner

__all__ = ["InitItem", "InitResult", "init_workspace"]

#: ``InitResult`` 的**契约版本号**（宪法 [D-22]）。
#:
#: F001-P1 FR-006 冻结了 v1 的字段与顺序，并要求"字段语义不得在本阶段之后
#: **无版本号**变更" —— 故 v2 的每一次契约变更 MUST 递增本常量。
#:
#: - **v1**（F001-P1）：``workspace_path`` / ``name`` / ``force`` /
#:   ``templates_loaded`` / ``files_created`` / ``files_skipped``；
#: - **v2**（[D-22]）：新增逐项明细与其投影计数；``files_created`` 的语义
#:   **归位**为 FR-006 字面口径「本次新建文件数」（原先 ``--force`` 的**覆盖**
#:   被并入其中）。
INIT_RESULT_CONTRACT_VERSION = 2


@dataclass(frozen=True)
class InitResult:
    """``init_workspace`` 的返回契约对象（不可变）。

    字段与顺序由 spec FR-006 冻结，后续阶段（F002 / F003 / F004）依赖此契约；
    v2 的增量见 :data:`INIT_RESULT_CONTRACT_VERSION` 与宪法 [D-22]。

    **计数口径**：按「**操作对象**（文件 / 目录）× **动作**（新建 / 覆盖 /
    跳过）」建模 —— 五个计数皆由 ``items`` 逐项明细**投影**而来（单一真相源）。

    - ``workspace_path``：workspace 的绝对路径；
    - ``name``：workspace 名称——未指定时为路径末段名，库 API 显式传入非空
      名称时以其为准；
    - ``force``：本次是否请求强制重置；
    - ``templates_loaded``：已加载的模板清单条目数——当前清单的**原始**条目
      总数（含目录条目、含重复条目）为 ``54``（spec FR-026）；
    - ``files_created``：本次**新建**的文件数——全新创建为 ``48``（文件型
      条目：45 文本 + 3 sqlite3；目录条目不计入，spec FR-017）；
    - ``files_skipped``：已存在而跳过的文件数——二次 init 为 ``48``；
    - ``files_overwritten``：本次**覆盖**的文件数（已存在 + ``--force`` →
      删除后重建）——``--force`` 二次 init 为 ``47``（另有 1 个契约库豁免项
      计入 ``files_skipped``）；
    - ``dirs_created``：本次**新建**的目录条目数——全新创建为 ``6``；
    - ``dirs_skipped``：已存在而**保留不变**的目录条目数——二次 init 为 ``6``
      （目录条目**永不**"覆盖"：既有目录一律保留不动，spec FR-010）；
    - ``items``：**逐项明细** —— 每个清单条目一条 ``InitItem``，含相对路径、
      对象类别与本次动作。
    """

    workspace_path: Path
    name: str
    force: bool
    templates_loaded: int
    files_created: int
    files_skipped: int
    files_overwritten: int
    dirs_created: int
    dirs_skipped: int
    items: tuple[InitItem, ...]


def init_workspace(
    path: str | Path,
    name: str | None = None,
    force: bool = False,
) -> InitResult:
    """创建 workspace 并落地模板骨架，返回结果契约对象。

    ``path`` 接受字符串与路径对象两种形态，内部统一解析为绝对路径；``name``
    缺省为 ``None``——此时名称取解析后路径的末段名，显式传入非空字符串时以
    该值为准，传入空字符串视为未指定（spec FR-005）；``force`` 缺省为假值。

    本函数体 MUST 只做两件事 —— 调内部初始化流程 + 构造结果对象，MUST NOT
    在门面层承载业务逻辑（spec FR-024）。

    失败：抛出 ``WorkspaceInitError`` 的子类（``PathNotFoundError`` /
    ``PathPermissionError`` / ``TemplateGenerationError``）——本层 MUST NOT
    返回退出码。
    """
    abs_path, resolved_name, resolved_force, items, loaded = init_workspace_inner(
        path=path,
        name=name,
        force=force,
    )
    return InitResult(
        workspace_path=abs_path,
        name=resolved_name,
        force=resolved_force,
        templates_loaded=loaded,
        files_created=sum(1 for i in items if i.kind == "file" and i.action == "created"),
        files_skipped=sum(1 for i in items if i.kind == "file" and i.action == "skipped"),
        files_overwritten=sum(
            1 for i in items if i.kind == "file" and i.action == "overwritten"
        ),
        dirs_created=sum(1 for i in items if i.kind == "dir" and i.action == "created"),
        dirs_skipped=sum(1 for i in items if i.kind == "dir" and i.action == "skipped"),
        items=tuple(items),
    )
