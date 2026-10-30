"""``donkey version`` 的单元测试（核心层版本解析 + CLI 层输出形态）。

本文件是 F001-P4 **新增**的独立单元测试文件 —— MUST NOT 改动 F001-P1 冻结的
``tests/unit/test_cli_client.py``（spec FR-034 / research.md R-11）。

测试落点分两层：

- **核心层**（``donkey.core.version``）—— 版本取值解析的三条分支
  （命中 / 不可得回退 / 不一致以元数据为准）；
- **CLI 层**（``donkey.cli.cli_client``）—— ``donkey version`` 的输出形态。

打桩口径（research.md R-09 的教训）：核心层 MUST 以
``import importlib.metadata`` + ``importlib.metadata.version("donkey")`` 的
形态调用 —— 本文件对 ``importlib.metadata.version`` 的 monkeypatch 方能生效；
若实现写成 ``from importlib.metadata import version``，打桩会**静默失效**、
用例假绿。
"""

from __future__ import annotations

import importlib.metadata
import re
import tomllib
from pathlib import Path

import pytest

from donkey.cli import cli_client
from donkey.core import version as core_version

#: 版本值的形态（宪法 §4.5 的 ``vx.y.z`` 记法）。
_VERSION_PATTERN = re.compile(r"v\d+\.\d+\.\d+")

#: 仓库根（由本文件自身位置向上推导）。
REPO_ROOT = Path(__file__).resolve().parents[2]


def _stub_metadata_version(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """把 ``importlib.metadata.version`` 打桩为一个固定返回值。"""

    def _fake_version(distribution_name: str) -> str:
        assert distribution_name == "donkey", distribution_name
        return value

    monkeypatch.setattr(importlib.metadata, "version", _fake_version)


def _stub_metadata_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """把 ``importlib.metadata.version`` 打桩为"发行版不存在"。"""

    def _fake_version(distribution_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(importlib.metadata, "version", _fake_version)


# --- 核心层：版本取值解析（US2 / US3 / US6 共用地基）-----------------------------


def test_resolve_version_prefers_distribution_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B-1 命中：分发元数据可读 → 取该值（spec FR-016）。"""
    _stub_metadata_version(monkeypatch, "9.9.9")

    assert core_version.resolve_version() == "9.9.9"


def test_resolve_version_falls_back_to_package_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B-2 不可得：元数据查询抛 ``PackageNotFoundError`` → 回退 ``__version__``。

    MUST NOT 抛异常、MUST NOT 返回空串、MUST NOT 使命令失败（spec FR-017）。
    """
    from donkey import __version__

    _stub_metadata_missing(monkeypatch)

    resolved = core_version.resolve_version()

    assert resolved == __version__
    assert resolved != ""


def test_resolve_version_metadata_wins_on_mismatch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """B-3 不一致：元数据值 ≠ ``__version__`` → **以元数据为准**（spec FR-018）。

    MUST NOT 报错、MUST NOT 告警 —— 告警会污染 stdout / stderr
    （spec FR-007 / FR-009）。
    """
    from donkey import __version__

    _stub_metadata_version(monkeypatch, "0.0.1")
    assert "0.0.1" != __version__

    assert core_version.resolve_version() == "0.0.1"

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_version_string_is_prefixed_resolved_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """展示值 = ``"v" + resolve_version()``（spec FR-013）。

    ``v`` 是**显示前缀**，不是版本号的一部分；前缀逻辑 MUST 单点收敛在核心层
    （research.md R-02）。
    """
    _stub_metadata_version(monkeypatch, "1.2.3")

    assert core_version.version_string() == "v1.2.3"
    assert core_version.version_string() == "v" + core_version.resolve_version()


def test_resolve_version_does_not_swallow_other_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MUST **只**捕获 ``PackageNotFoundError`` —— 其它异常 MUST NOT 被吞掉。

    沿用 F001-P1 契约 M-03 的"不得宽泛捕获"口径。
    """

    def _boom(distribution_name: str) -> str:
        raise RuntimeError(f"unexpected failure for {distribution_name}")

    monkeypatch.setattr(importlib.metadata, "version", _boom)

    with pytest.raises(RuntimeError):
        core_version.resolve_version()


def test_version_module_exports_only_public_functions() -> None:
    """模块 MUST 只导出 ``resolve_version`` / ``version_string`` 两个函数。

    实现层 MUST NOT 存在节点级版本号的枚举入口（spec FR-024）。
    """
    assert core_version.__all__ == ["resolve_version", "version_string"]


# --- CLI 层：输出形态（US1）--------------------------------------------------------


def test_version_command_prints_single_bare_version_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``donkey version`` → 退出码 0，stdout 恰好一行**裸版本值**。

    判据（spec FR-007 ~ FR-010）：无 ``[donkey version]`` 前缀、无
    ``version=`` 字段名、无前导 / 尾随空白、stderr 为空、版本值恰好出现 1 次。

    输出值 == ``"v" + resolve_version()``（**元数据优先**的解析结果 —— spec
    FR-016 ~ FR-018）；若安装元数据与 ``donkey.__version__`` 不一致，本断言
    MUST NOT 断言输出 == ``donkey.__version__``（那会产生假失败）。
    """
    exit_code = cli_client.main(["version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    lines = captured.out.splitlines()
    assert len(lines) == 1, f"stdout MUST 恰好一行：{captured.out!r}"
    line = lines[0]
    assert line == "v" + core_version.resolve_version()
    assert line == line.strip(), "MUST NOT 有前导 / 尾随空白"
    assert "[donkey version]" not in line, "MUST NOT 带前缀"
    assert "version=" not in line, "MUST NOT 带 key=value 字段名"
    assert len(_VERSION_PATTERN.findall(captured.out)) == 1, "版本值 MUST 恰好出现 1 次"
    assert captured.err == "", f"成功路径 stderr MUST 为空：{captured.err!r}"


def test_version_command_output_matches_declared_version_in_normal_install(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """**常规安装形态**下输出 MUST 等于 ``v0.1.0``（spec FR-014 / SC-003）。

    判定谓词 = 安装分发元数据值 == ``donkey.__version__``；不成立（**陈旧安装
    形态**）时 MUST NOT 断言该值（spec FR-018）。
    """
    from donkey import __version__

    assert cli_client.main(["version"]) == 0
    captured = capsys.readouterr()

    if importlib.metadata.version("donkey") == __version__:
        assert captured.out.strip() == "v0.1.0"
    else:
        assert captured.out.strip() == "v" + importlib.metadata.version("donkey")


def test_version_command_output_is_deterministic(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """连续两次调用 → stdout **逐字节相同**（spec FR-011）。

    输出 MUST NOT 含时间戳 / 主机名 / 路径 / 进程号一类的非确定性内容。
    """
    assert cli_client.main(["version"]) == 0
    first = capsys.readouterr().out

    assert cli_client.main(["version"]) == 0
    second = capsys.readouterr().out

    assert first.encode("utf-8") == second.encode("utf-8")


# --- 唯一版本值（US2）--------------------------------------------------------------


def test_version_string_contains_exactly_one_version_value() -> None:
    """版本值里只有**一个**版本值（spec FR-008）。

    MUST NOT 出现第二个版本值、客户端版本、节点级版本信息、workspace 格式
    版本（整数 ``1``）或工作区路径（spec FR-008 / FR-021）。
    """
    value = core_version.version_string()

    assert len(_VERSION_PATTERN.findall(value)) == 1, value
    assert value == "v" + core_version.resolve_version()
    # workspace 格式版本是整数 1 —— MUST NOT 被取作版本值（spec FR-021）。
    assert core_version.resolve_version() != "1"
    assert value != "1"


def test_version_string_matches_installed_metadata_version() -> None:
    """底层取值 MUST 与安装分发元数据值**逐字节一致**（spec FR-016）。

    取值来源唯一（spec FR-019）—— MUST NOT 出现第二个版本定义点。
    """
    assert core_version.resolve_version() == importlib.metadata.version("donkey")


def test_version_string_falls_back_without_distribution_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """取不到分发元数据时取值 MUST **仍确定**（spec FR-017 / US6 场景 2）。

    回退值 MUST 是包内 ``__version__``（非空、可解析）—— 取不到元数据时
    MUST NOT 影响版本值。**陈旧安装形态**下二者可以不等（spec FR-018）。
    """
    from donkey import __version__

    _stub_metadata_missing(monkeypatch)

    assert core_version.resolve_version() == __version__
    assert core_version.resolve_version() != ""
    assert core_version.version_string() == "v" + __version__


def test_version_string_matches_declared_sources_in_normal_install() -> None:
    """**常规安装形态**下底层取值与各处声明**逐字节一致**（spec FR-013）。

    常规安装形态的判定谓词 = 安装分发元数据值 == 包内 ``__version__``；不成立
    （**陈旧安装形态**）时 MUST NOT 断言该口径（spec FR-018）。

    注：清单 ``donkey_version`` 字段的比对由 **e2e 场景 2** 以真黑盒路径
    承载（子进程 ``donkey init`` → 读 ``manifest.json``），此处 MUST NOT
    重复断言同一事实。
    """
    from donkey import __version__

    installed = importlib.metadata.version("donkey")
    if installed != __version__:
        # 陈旧安装形态 → 以分发元数据为准，MUST NOT 断言 == __version__。
        assert core_version.resolve_version() == installed
        return

    declared = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]

    assert core_version.resolve_version() == __version__
    assert core_version.resolve_version() == declared


def test_workspace_manifest_donkey_version_tracks_runtime_version(tmp_path: Path) -> None:
    """工作区清单的 ``donkey_version`` MUST 记录**运行时**版本（spec FR-013）。

    MUST NOT 硬编码字面量 —— 否则版本 bump 后**新建**的工作区仍记旧版本号，
    会让 F002 ``donkey load`` 的迁移提示**误判**工作区陈旧
    （spec Assumptions「版本号 bump 的跨 Phase 联动」）。
    """
    from donkey.core.workspace.manifest import write_workspace_manifest

    workspace = tmp_path / "ws"
    workspace.mkdir()

    written = write_workspace_manifest(workspace, "ws", False)

    assert written["donkey_version"] == core_version.resolve_version()
    # 清单的**字段集**为三项 —— 名字 / 创建时间 / donkey 版本号；原先的
    # "版本号（整数 1）"字段**无人读取**且与 ``donkey_version`` 读作两个打架
    # 的版本号，已删除（宪法 [D-21]）。
    assert set(written.keys()) == {"name", "created_at", "donkey_version"}


# --- 图未建时的确定取值（US3）------------------------------------------------------
def test_version_value_is_deterministic_without_graph(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """展示值 MUST 恒为 ``"v" + 底层取值``，恒不为占位串（spec FR-014）。

    主图尚未构建（F004-P7 之前）时，版本值 MUST 仍是确定的解析结果 ——
    MUST NOT 是 ``unknown`` / ``dev`` 一类的占位或后缀串，MUST NOT 是
    ``v0.0.0`` 一类"图版本 0"的取值。
    """
    assert cli_client.main(["version"]) == 0
    captured = capsys.readouterr()

    value = captured.out.strip()
    assert value == "v" + core_version.resolve_version()
    assert value not in {"unknown", "dev", "v0.0.0", "0.0.0"}
    assert not value.endswith("dev")
    assert _VERSION_PATTERN.fullmatch(value), value


def test_version_output_has_no_node_level_information(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """输出 MUST **不含**节点清单 / 任何节点的独立版本号（spec FR-015 / FR-024）。

    节点级版本号（``vx.y.z`` 的 ``y`` / ``z``）属 F004-P7 —— 本 Phase 不实现、
    不展示。
    """
    assert cli_client.main(["version"]) == 0
    captured = capsys.readouterr()

    lines = captured.out.splitlines()
    assert len(lines) == 1, f"MUST NOT 输出节点清单等多行内容：{captured.out!r}"
    # 一个版本值 = 一个 ``vx.y.z`` —— 节点级版本号 MUST NOT 出现第二个。
    assert len(_VERSION_PATTERN.findall(captured.out)) == 1
    # workspace 格式版本（整数 1）MUST NOT 被暴露（spec FR-021）。
    assert core_version.resolve_version() != "1"


# --- 用法错误（US5）----------------------------------------------------------------


def test_version_usage_errors_exit_1(capsys: pytest.CaptureFixture[str]) -> None:
    """三类误用 → 退出码 **1**（MUST NOT 为 argparse 默认的 ``2``）。

    误用形态（spec FR-002 / FR-005）：未知长选项 / 客户端参数 / 多余位置参数。
    子解析器 MUST 自动继承 ``DonkeyArgumentParser`` 的 ``error()`` 覆写
    （F001-P1 research.md R-01）。

    断言 MUST NOT 依赖 argparse 的**具体报错措辞**（实测为「the following
    arguments are required: command」—— ``add_subparsers(dest="command",
    required=True)`` 的必填校验先于未识别参数检查触发）。
    """
    for argv in (["version", "--bogus"], ["version", "web"], ["version", "extra"]):
        with pytest.raises(SystemExit) as excinfo:
            cli_client.main(argv)

        assert excinfo.value.code == 1, argv
        captured = capsys.readouterr()
        assert captured.out == "", f"{argv} 的 stdout MUST 为空"
        assert not _VERSION_PATTERN.search(captured.out), argv
        assert captured.err != "", f"{argv} 的 stderr MUST 含用法提示"


def test_version_help_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    """``donkey version --help`` → 退出码 **0**（帮助请求**不**是用法错误）。"""
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main(["version", "--help"])

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert not _VERSION_PATTERN.search(captured.out), captured.out


def test_top_level_version_flag_is_not_supported(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """顶层 MUST **不**提供 ``--version`` 标志 → 以退出码 ``1`` 失败。

    版本查询的**唯一入口**是 ``version`` 子命令（spec FR-038 / Clarifications
    Q4）。断言以「退出码 == 1 且 stdout 不含任何版本号」为准，MUST NOT 依赖
    具体报错措辞。
    """
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main(["--version"])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert not _VERSION_PATTERN.search(captured.out)


def test_top_level_help_lists_version_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``donkey --help`` 的子命令列表 MUST 出现 ``version`` 条目（spec FR-003）。"""
    with pytest.raises(SystemExit) as excinfo:
        cli_client.main(["--help"])

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "version" in captured.out
