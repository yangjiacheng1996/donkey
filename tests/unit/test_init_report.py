"""``donkey init`` **执行报告**（摘要 + 逐项明细）的单元测试。

对应宪法 [D-22]：`donkey init` 的 stdout 由「**摘要行** + **逐项明细**」两部分
组成，计数按「**操作对象**（文件 / 目录）× **动作**（新建 / 覆盖 / 跳过）」分解。

本文件是 F001-P4 之后**新增**的独立测试文件 —— MUST NOT 改动 F001-P1 / P2 / P3
的既有测试文件（其相关断言的改写已按宪法 [D-22] 逐条登记在各自文件内）。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from donkey.cli import cli_client
from donkey.core.api import init_workspace

#: 摘要行里的 ``key=value`` 字段。
_SUMMARY_FIELD = re.compile(r"(\w+)=(\S+)")


def _summary_fields(stdout: str) -> dict[str, str]:
    """解析摘要行（首行）的 ``key=value`` 字段。"""
    first_line = stdout.splitlines()[0]
    return dict(_SUMMARY_FIELD.findall(first_line))


def _detail_lines(stdout: str) -> list[str]:
    """取出逐项明细行（第二行是图例，其后每行一条明细）。"""
    lines = stdout.splitlines()
    start = next(i for i, line in enumerate(lines) if "逐项明细" in line)
    return lines[start + 1 :]


def test_summary_decomposes_by_object_and_action(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """摘要 MUST 按「对象 × 动作」完整分解，且各数之和自洽。

    全新 init：文件新建 48、目录新建 6、覆盖 0、跳过 0；且
    ``templates == files_* 之和 + dirs_* 之和``。
    """
    assert cli_client.main(["init", str(tmp_path / "ws")]) == 0
    fields = _summary_fields(capsys.readouterr().out)

    assert fields["templates"] == "54"
    assert fields["files_created"] == "48"
    assert fields["files_overwritten"] == "0"
    assert fields["files_skipped"] == "0"
    assert fields["dirs_created"] == "6"
    assert fields["dirs_skipped"] == "0"

    # 算术自洽：清单条目总数 == 文件动作数之和 + 目录动作数之和。
    assert int(fields["templates"]) == (
        int(fields["files_created"])
        + int(fields["files_overwritten"])
        + int(fields["files_skipped"])
        + int(fields["dirs_created"])
        + int(fields["dirs_skipped"])
    )


def test_summary_on_second_init_is_all_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """二次 init：全部**跳过**（文件 48 + 目录 6），新建与覆盖皆为 0。"""
    workspace = tmp_path / "ws"

    assert cli_client.main(["init", str(workspace)]) == 0
    capsys.readouterr()

    assert cli_client.main(["init", str(workspace)]) == 0
    fields = _summary_fields(capsys.readouterr().out)

    assert fields["files_created"] == "0"
    assert fields["files_overwritten"] == "0"
    assert fields["files_skipped"] == "48"
    assert fields["dirs_created"] == "0"
    assert fields["dirs_skipped"] == "6"


def test_summary_on_force_separates_overwritten_from_created(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--force``：**覆盖**与**新建**分列 —— 覆盖 47、新建 0、跳过 1（契约库豁免）。"""
    workspace = tmp_path / "ws"

    assert cli_client.main(["init", str(workspace)]) == 0
    capsys.readouterr()

    assert cli_client.main(["init", str(workspace), "--force"]) == 0
    fields = _summary_fields(capsys.readouterr().out)

    assert fields["files_created"] == "0"
    assert fields["files_overwritten"] == "47"
    assert fields["files_skipped"] == "1"


def test_detail_lines_cover_every_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """逐项明细 MUST **每个清单条目一条**，且标记与动作一致。

    标记：``+`` 新建 / ``~`` 覆盖 / ``-`` 跳过；路径以 ``/`` 结尾者 = 目录条目。
    """
    assert cli_client.main(["init", str(tmp_path / "ws")]) == 0
    stdout = capsys.readouterr().out

    details = _detail_lines(stdout)
    assert len(details) == 54

    marks = {line[2] for line in details}
    assert marks == {"+"}

    # 目录条目以 "/" 结尾，且恰好 6 条。
    dirs = [line for line in details if line.strip().endswith("/")]
    assert len(dirs) == 6

    # 明细与库 API 的 items 逐条对应（同一相对路径、同一动作）。
    result = init_workspace(tmp_path / "other")
    by_path = {item.path: item for item in result.items}
    for line in details:
        mark, path = line.strip()[0], line.strip()[2:]
        item = by_path[path]
        expected = {"created": "+", "overwritten": "~", "skipped": "-"}[item.action]
        assert mark == expected, path


def test_detail_marks_distinguish_actions_on_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--force`` 的明细 MUST 用 ``~`` 标出**覆盖**、``-`` 标出**跳过**。"""
    workspace = tmp_path / "ws"

    assert cli_client.main(["init", str(workspace)]) == 0
    capsys.readouterr()

    assert cli_client.main(["init", str(workspace), "--force"]) == 0
    details = _detail_lines(capsys.readouterr().out)

    overwritten = [line for line in details if line.strip()[0] == "~"]
    skipped = [line for line in details if line.strip()[0] == "-"]
    assert len(overwritten) == 47
    # 跳过的 = 6 个目录条目（既有目录保留不变）+ 1 个契约库豁免项；
    # 3 个 sqlite3 与其余文本条目一样是**覆盖**（重建），不是跳过。
    assert len(skipped) == 7


def test_warning_is_the_last_line_on_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--force`` 的警告 MUST **置于明细之后**（否则会滚出终端视野）。"""
    workspace = tmp_path / "ws"

    assert cli_client.main(["init", str(workspace)]) == 0
    capsys.readouterr()

    assert cli_client.main(["init", str(workspace), "--force"]) == 0
    lines = capsys.readouterr().out.splitlines()

    assert "警告" in lines[-1]
    assert "逐项明细" in lines[1]


def test_init_result_items_is_the_single_source_of_truth(tmp_path: Path) -> None:
    """库 API 的五个计数 MUST 与 ``items`` 逐项明细**自洽**（单一真相源）。"""
    result = init_workspace(tmp_path / "ws")

    assert result.files_created == sum(
        1 for i in result.items if i.kind == "file" and i.action == "created"
    )
    assert result.files_overwritten == sum(
        1 for i in result.items if i.kind == "file" and i.action == "overwritten"
    )
    assert result.files_skipped == sum(
        1 for i in result.items if i.kind == "file" and i.action == "skipped"
    )
    assert result.dirs_created == sum(
        1 for i in result.items if i.kind == "dir" and i.action == "created"
    )
    assert result.dirs_skipped == sum(
        1 for i in result.items if i.kind == "dir" and i.action == "skipped"
    )
    assert len(result.items) == result.templates_loaded
