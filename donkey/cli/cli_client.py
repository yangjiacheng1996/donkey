"""donkey 命令行客户端入口。

分层约束（宪法 N-04 / N-08）：

- MUST NOT 直接 import ``langchain`` / ``langgraph`` / ``sqlite3``；
- 触达文件系统行为 MUST 只通过 ``donkey.core.api`` 门面；
- 退出码只在客户端层产生（核心层不感知退出码，宪法 N-05）。
"""

import argparse
import sys
from typing import NoReturn

import donkey.core.api as core_api
from donkey.core.exceptions import (
    BuiltinToolGenerationError,
    PathNotFoundError,
    PathPermissionError,
    TemplateGenerationError,
    WorkspaceInitError,
)
from donkey.core.exit_codes import (
    EXIT_CODE_BUILTIN_TOOL_GENERATION,
    EXIT_CODE_OK,
    EXIT_CODE_PATH_NOT_FOUND,
    EXIT_CODE_PATH_PERMISSION,
    EXIT_CODE_TEMPLATE_GENERATION,
)

#: 异常 → 退出码的**全局唯一映射表**（contracts/exit-codes.md §3）。
#:
#: 基类 ``WorkspaceInitError`` 不登记（M-01）；未登记的子类兜底到路径类退出码
#: ``1``（M-02）。MUST NOT 使用宽泛捕获吞掉未分类错误（M-03）。
_EXCEPTION_TO_EXIT_CODE: dict[type[Exception], int] = {
    PathNotFoundError: EXIT_CODE_PATH_NOT_FOUND,
    PathPermissionError: EXIT_CODE_PATH_PERMISSION,
    TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION,
    BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION,
}


class DonkeyArgumentParser(argparse.ArgumentParser):
    """把参数用法错误的失败码从 argparse 默认的 ``2`` 改写为 ``1``。

    退出码 ``2`` 在 ``donkey init`` 的段位里已被 ``PathPermissionError`` 占用，
    参数用法错误必须归入 ``1``（"输入 / 路径不合法"同族，见 spec FR-018）。

    ``argparse`` 的子解析器类型默认取 ``type(self)``，故本覆写自动传播到
    所有子命令，无需分别处理（research.md R-01）。
    """

    def error(self, message: str) -> NoReturn:
        """把用法错误写 stderr 并以退出码 ``1`` 终止。"""
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _build_parser() -> DonkeyArgumentParser:
    """构造顶层解析器并注册子命令。

    ``prog`` MUST 显式设为 ``"donkey"``——``argparse`` 默认取 ``sys.argv[0]``
    的 basename，``python -m donkey`` 下会得到 ``__main__.py``，导致两条入口的
    stderr usage 提示不一致，违反 spec FR-023（research.md R-01）。

    ``init`` 的参数面 MUST 仅含必填位置参数 ``path`` 与布尔开关 ``--force``；
    MUST NOT 提供 ``--name`` 或任何等价的独立命名参数（spec FR-003）。
    """
    parser = DonkeyArgumentParser(
        prog="donkey",
        description="donkey —— workspace 与 agent 运行框架。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="创建 workspace：生成模板骨架（46 个模板条目）+ 工作区清单。",
        description="创建 workspace：生成模板骨架（46 个模板条目）+ 工作区清单。",
    )
    init_parser.add_argument(
        "path",
        help="workspace 目录路径；绝对或相对均可，相对路径以进程工作目录为解析基准。",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="恢复出厂设置：模板文件与三个记忆库模板被删后重建，记忆库历史与元数据一并清空。",
    )
    return parser


def _exit_code_for(exc: WorkspaceInitError) -> int:
    """按映射表把异常折成退出码。

    沿继承链自近及远查找已登记的异常类；找不到则兜底到路径类退出码 ``1``
    （contracts/exit-codes.md M-02）。
    """
    for exc_type in type(exc).__mro__:
        mapped = _EXCEPTION_TO_EXIT_CODE.get(exc_type)
        if mapped is not None:
            return mapped
    return EXIT_CODE_PATH_NOT_FOUND


def _run_init(path: str, force: bool) -> int:
    """执行 ``donkey init``：经核心库门面创建 workspace 根目录。"""
    try:
        result = core_api.init_workspace(path, force=force)
    except WorkspaceInitError as exc:
        print(f"[donkey init] 失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return _exit_code_for(exc)

    print(
        f"[donkey init] workspace={result.workspace_path} name={result.name} "
        f"force={str(result.force).lower()} templates={result.templates_loaded} "
        f"created={result.files_created} skipped={result.files_skipped}"
    )
    if result.force:
        # 强制重置会删掉重建三个记忆库模板 —— MUST 显式提示用户历史与元数据
        # 一并清空（spec FR-068 / SC-019）。该提示属**成功路径**信息，故走
        # stdout；MUST 与通用摘要**分行**、MUST NOT 挤占摘要的六个字段。
        #
        # 文案 MUST 同时涵盖"已清空 / 已重建"两种情形 —— 带 --force 时该提示
        # **恒定输出**（即使工作区此前不存在 sqlite3 文件，此时亦无数据可清空，
        # 属"已被重建"的形态）。
        print(
            "[donkey init] 警告：memory/ 下的三个记忆库文件已被清空并重建为出厂状态"
            "（会话历史与会话元数据一并清空，--force 恢复出厂设置）。"
            "如需保留请先备份。"
        )
    return EXIT_CODE_OK


def main(argv: list[str] | None = None) -> int:
    """命令行入口；返回进程退出码，由入口点 ``sys.exit()`` 落地。"""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return _run_init(path=str(args.path), force=bool(args.force))
    parser.error(f"未知子命令：{args.command}")
