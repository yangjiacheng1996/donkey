"""``donkey.cli.cli_client`` 的单元测试（CLI 层）。

CLI 层共 3 个测试函数（缺子命令 / 缺必填参数 / 未登记异常子类兜底），
CLI 用法类失败的断言组内嵌在既有测试函数内，不新增测试函数。
"""

from pathlib import Path

import pytest

from donkey.cli import cli_client
from donkey.core.exceptions import WorkspaceInitError


def test_main_without_subcommand_exits_1() -> None:
    """缺子命令 → 退出码 1（不是 argparse 默认的 2）。"""
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main([])

    assert excinfo.value.code == 1


def test_main_missing_path_argument_exits_1() -> None:
    """缺必填位置参数 → 退出码 1，且 stderr 含用法提示。"""
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main(["init"])

    assert excinfo.value.code == 1

    # 追加断言组：误传命名类参数（--name）同样归退出码 1（spec FR-024）。
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main(["init", "some/path", "--name", "alice"])

    assert excinfo.value.code == 1


def test_main_unregistered_exception_falls_back_to_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """未登记进映射表的 ``WorkspaceInitError`` 子类 → 兜底退出码 1。"""

    class _UnregisteredError(WorkspaceInitError):
        """未在 ``_EXCEPTION_TO_EXIT_CODE`` 中登记的子类。"""

    def _fake_init_workspace(path: str, force: bool = False) -> None:
        raise _UnregisteredError("未登记的错误子类")

    # 打桩目标依赖 cli 侧固定的 ``import donkey.core.api as core_api`` 形态；
    # MUST NOT 打桩 ``donkey.core.api.init_workspace``——若 cli 侧是
    # ``from ... import`` 绑定，该打桩不生效、本用例会假绿。
    monkeypatch.setattr("donkey.cli.cli_client.core_api.init_workspace", _fake_init_workspace)

    exit_code = cli_client.main(["init", str(tmp_path / "ws")])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[donkey init] 失败：" in captured.err


def test_cli_force_warning_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """带 ``--force`` 时 stdout 末尾多一行强制清空提示；不带时**没有**该行。

    提示 MUST 与通用摘要**分行**、MUST NOT 挤占摘要的字段
    （spec FR-068 / SC-019），且 MUST 置于**逐项明细之后**（明细恒定 54 行，
    警告若在其之前会滚出终端视野 —— 宪法 [D-22]）。

    > **断言改写登记（宪法 [D-22] · 2026-10-30 · Maintainer 裁决）**：原断言
    > 为「不带 --force 时 stdout **恰好 1 行**」+「带 --force 时**恰好 2 行**」
    > + 摘要**六个字段**名 —— 现输出为「摘要 1 行 + 明细 1 行 + N 条明细
    > （+ --force 时的警告 1 行）」，摘要字段亦由六个扩为九个。
    """
    workspace = tmp_path / "ws"
    summary_fields = (
        "workspace=",
        "name=",
        "force=",
        "templates=",
        "files_created=",
        "files_overwritten=",
        "files_skipped=",
        "dirs_created=",
        "dirs_skipped=",
    )

    assert cli_client.main(["init", str(workspace)]) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    # 摘要 1 行 + 明细图例 1 行 + N 条明细
    assert lines[0].startswith("[donkey init] workspace=")
    assert "逐项明细" in lines[1]
    assert len(lines) > 2
    assert "清空" not in captured.out
    for field in summary_fields:
        assert field in lines[0], field

    assert cli_client.main(["init", str(workspace), "--force"]) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    warning = lines[-1]
    # 文案 MUST 同时涵盖"已清空 / 已重建"两种情形
    assert "清空" in warning
    assert "重建" in warning
    # 警告 MUST 置于明细之后
    assert "逐项明细" in lines[1]
    assert len(lines) > 3
    for field in summary_fields:
        assert field in lines[0], field
