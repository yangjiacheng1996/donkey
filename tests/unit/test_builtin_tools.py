"""F001-P3 ``builtin_tools`` 的单元测试。

本文件承载 F001-P3 的全部单元测试用例（spec FR-058 的 23 个类别 + 4 个
补齐类别 + 边界护栏），逐条用例清单以 ``tasks.md`` 为准。

覆盖分组：

- 模板资产齐备性与内容契约（FR-052 ~ FR-057 / FR-076 / FR-079 / FR-104）；
- 9 个 ``@tool`` 的导入形态、说明文字与参数模式（FR-013 ~ FR-027）；
- 命令工具（FR-028 ~ FR-036）与网络工具（FR-037 ~ FR-042 / FR-089 / FR-090）；
- 文件工具的七个动作与读取侧双上限（FR-092 ~ FR-098）；
- 变更记录契约（FR-003 ~ FR-012 / FR-016 / FR-019 / FR-020）；
- 幂等、强制重置豁免与退出码 4 的映射（FR-069 ~ FR-075 / FR-087 / FR-105）。

**模块缓存陷阱**（验收假绿的来源）：``sys.modules`` 按**模块名**缓存 —— 在
同一个进程里先后导入两个工作区的同名模块，第二次拿到的是**第一个**工作区的
产物。故本文件的夹具在 teardown 时 MUST 把相关模块**全部**摘除（包形态与
顶层模块形态都要摘）。
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import httpx
import pytest
from pytest_httpx import HTTPXMock

from donkey.core.api import init_workspace
from donkey.core.exceptions import BuiltinToolGenerationError
from donkey.core.workspace.init import load_template_manifest

#: 变更记录的**基线字段**（12 个 —— 任何动作下全部存在）。
BASELINE_KEYS = frozenset(
    {
        "version",
        "action",
        "path",
        "rel_path",
        "previous_exists",
        "previous_size",
        "previous_hash",
        "new_size",
        "new_hash",
        "unified_diff",
        "diff_truncated",
        "applied",
    }
)

#: 契约库的公开函数（9 个 —— 只增不改的契约面）。
CONTRACT_FUNCTION_NAMES = (
    "workspace_root",
    "resolve_path",
    "relative_path",
    "sha256_bytes",
    "read_existing_bytes",
    "atomic_write_bytes",
    "build_unified_diff",
    "build_change_record",
    "check_expected_hash",
)

#: 内置工具模块与契约库在模块缓存里的全部键（包形态 + 顶层模块形态）。
_TOOL_MODULE_NAMES = (
    "tools",
    "tools.filesystem",
    "tools.commandline",
    "tools.webfetch",
    "tools.changes",
    "filesystem",
    "commandline",
    "webfetch",
    "changes",
)

#: 宪法 N-12：workspace 内容 MUST NOT 含任何智能体框架的可观测性后端形态。
#:
#: 该关键词 MUST 以**正则字符类**拼出 —— 仓库自身的静态 grep 自检 MUST NOT
#: 在源码里命中它，否则自检会把自己的断言当成违例。
_OBSERVABILITY_NEEDLE = re.compile(r"lang[_-]?smith", re.IGNORECASE)

#: 内置工具与契约库的落地路径（相对工作区根）。
_TOOLS_DIR_FILES = (
    "tools/__init__.py",
    "tools/changes.py",
    "tools/filesystem.py",
    "tools/commandline.py",
    "tools/webfetch.py",
    "tools/README.md",
)

#: 本 Phase 落地的 6 个 ``.py`` 文件（相对工作区根）。
_PYTHON_ARTIFACTS = (
    "tools/__init__.py",
    "tools/changes.py",
    "tools/filesystem.py",
    "tools/commandline.py",
    "tools/webfetch.py",
    "skills/example/scripts/example.py",
)


# --- 共享夹具 -------------------------------------------------------------------


def render_workspace(tmp_path: Path, name: str = "ws") -> Path:
    """把工作区渲染到临时目录并返回其路径（不改动已安装包）。"""
    workspace = tmp_path / name
    init_workspace(workspace)
    return workspace


def import_tool_module(workspace: Path, name: str) -> ModuleType:
    """把**工作区根**加入导入路径后，按包名导入工作区产物。"""
    root = str(workspace)
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module(f"tools.{name}")


def purge_tool_modules() -> None:
    """从模块缓存里摘除全部工作区产物模块（包形态与顶层形态都要摘）。"""
    for name in _TOOL_MODULE_NAMES:
        sys.modules.pop(name, None)


def assert_compiles(path: Path) -> None:
    """模板正文是 ``.txt`` → 零静态检查覆盖 —— 语法自检是它唯一的兜底。"""
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def strip_presentation(rendered: str) -> str:
    """去掉呈现文本的包装（页范围头 + 行号前缀），还原出正文。"""
    lines = rendered.split("\n")
    body: list[str] = []
    for line in lines[1:]:
        if line.startswith("["):
            break
        _, _, content = line.partition(": ")
        body.append(content)
    return "\n".join(body)


def count_tools(source: str) -> int:
    """统计源码里的 ``@tool`` 装饰器个数。"""
    return len(re.findall(r"^@tool\b", source, re.MULTILINE))


@pytest.fixture
def workspace(tmp_path: Path) -> Iterator[Path]:
    """渲染好的工作区；teardown 清模块缓存与导入路径。"""
    ws = render_workspace(tmp_path)
    root = str(ws)
    sys.path.insert(0, root)
    try:
        yield ws
    finally:
        if root in sys.path:
            sys.path.remove(root)
        purge_tool_modules()


@pytest.fixture
def tools_dir_on_path(workspace: Path) -> Iterator[Path]:
    """把 ``tools/`` 目录**本身**加入导入路径（顶层模块形态）。"""
    tools_dir = str(workspace / "tools")
    sys.path.insert(0, tools_dir)
    try:
        yield workspace
    finally:
        if tools_dir in sys.path:
            sys.path.remove(tools_dir)
        purge_tool_modules()


# --- US1：资产齐备性与内容契约（T019 / T106）--------------------------------------


def test_manifest_entries_and_rendered_assets_are_complete(workspace: Path) -> None:
    """清单 54 条 / 文件型 48 条 / 落地 49 文件 / 10 目录 / 6 个工具文件齐备。"""
    entries = load_template_manifest()
    file_type_entries = [
        entry for entry in entries if entry.get("format", "text") != "directory"
    ]
    assert len(entries) == 54
    assert len(file_type_entries) == 48

    files = [p for p in workspace.rglob("*") if p.is_file()]
    directories = [p for p in workspace.rglob("*") if p.is_dir()]
    # 49 个文件 = 48 个清单文件型条目 + 1 份工作区清单
    assert len(files) == 49
    # 10 个目录 = 根 + 6 个清单目录 + 3 个 Skill Level 3 子目录
    assert len(directories) + 1 == 10

    for relative in _TOOLS_DIR_FILES:
        assert (workspace / relative).is_file(), relative
    for relative in (
        "skills/example/reference/example.md",
        "skills/example/scripts/example.py",
        "skills/example/templates/example.md",
    ):
        assert (workspace / relative).is_file(), relative

    # 45 个文本型条目的源文件全部齐备（缺一个 → 安装后 init 报 exit 3）
    templates_root = Path(__file__).resolve().parents[2] / (
        "donkey/core/workspace/templates"
    )
    text_entries = [
        entry
        for entry in entries
        if entry.get("format", "text") in {"markdown", "toml", "json", "python", "text"}
    ]
    assert len(text_entries) == 45
    for entry in text_entries:
        source = templates_root / f"{entry['path']}.txt"
        assert source.is_file(), source


def test_rendered_artifacts_are_syntactically_valid_and_clean(workspace: Path) -> None:
    """6 个 ``.py`` 全部可编译；产物不含可观测性字样 / 环境变量读取 / 子智能体字段。"""
    for relative in _PYTHON_ARTIFACTS:
        assert_compiles(workspace / relative)

    assert count_tools((workspace / "tools" / "changes.py").read_text("utf-8")) == 0
    assert count_tools((workspace / "tools" / "__init__.py").read_text("utf-8")) == 0

    directories = {p.name.lower() for p in workspace.rglob("*") if p.is_dir()}
    assert not directories & {"agents", "subagent", "subagents"}

    for path in workspace.rglob("*"):
        if not path.is_file() or path.suffix == ".sqlite3":
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "subagent" not in lowered, path
        assert "agents/" not in lowered, path
        assert not _OBSERVABILITY_NEEDLE.search(lowered), path
        assert "os.environ" not in text, path
        assert "getenv" not in text, path

    # httpx 默认的 trust_env=True 会隐式读取代理 / 证书环境变量 —— 必须显式关闭。
    assert "trust_env=False" in (workspace / "tools" / "webfetch.py").read_text("utf-8")


def test_memory_database_files_are_never_touched(workspace: Path) -> None:
    """三个记忆库文件的内容与 mtime 在 init 前后完全不变。"""
    sentinels = {
        "sessions.sqlite3": b"sentinel-sessions",
        "store.sqlite3": b"sentinel-store",
        "knowledge.sqlite3": b"sentinel-knowledge",
    }
    memory_dir = workspace / "memory"
    before: dict[str, tuple[bytes, int]] = {}
    for name, payload in sentinels.items():
        target = memory_dir / name
        target.write_bytes(payload)
        before[name] = (target.read_bytes(), target.stat().st_mtime_ns)

    init_workspace(workspace)

    for name, (payload, mtime) in before.items():
        target = memory_dir / name
        assert target.read_bytes() == payload, name
        assert target.stat().st_mtime_ns == mtime, name


# --- US2：导入形态、说明文字与参数模式（T021 ~ T024）----------------------------


def test_every_tool_has_a_complete_docstring_and_args_schema(workspace: Path) -> None:
    """9 个工具的说明文字长度 > 20，参数模式含全部参数且默认值一致。"""
    filesystem = import_tool_module(workspace, "filesystem")
    commandline = import_tool_module(workspace, "commandline")
    webfetch = import_tool_module(workspace, "webfetch")

    expected_defaults = {
        ("read_file", "start_line"): 1,
        ("read_file", "num_lines"): None,
        ("write_file", "dry_run"): False,
        ("write_file", "include_previous"): False,
        ("write_file", "expected_hash"): None,
        ("copy_file", "dry_run"): False,
        ("move_file", "dry_run"): False,
        ("delete_file", "include_previous"): False,
        ("delete_file", "dry_run"): False,
        ("delete_file", "expected_hash"): None,
        ("list_dir", "include_hidden"): True,
        ("list_dir", "offset"): 0,
        ("list_dir", "limit"): None,
        ("stat", "with_hash"): False,
        ("run_shell", "timeout"): 60,
        ("run_shell", "cwd"): None,
        ("fetch_url", "method"): "GET",
        ("fetch_url", "headers"): None,
        ("fetch_url", "timeout"): 30,
    }

    tools = [
        *[
            getattr(filesystem, name)
            for name in (
                "read_file",
                "write_file",
                "copy_file",
                "move_file",
                "delete_file",
                "list_dir",
                "stat",
            )
        ],
        commandline.run_shell,
        webfetch.fetch_url,
    ]
    assert len(tools) == 9

    for tool in tools:
        assert len(tool.description) > 20, tool.name
        assert tool.name == tool.name.strip()
        for (tool_name, arg_name), default in expected_defaults.items():
            if tool_name != tool.name:
                continue
            schema = tool.args[arg_name]
            assert schema.get("default", default) == default, (tool.name, arg_name)


def test_relative_import_form_works(workspace: Path) -> None:
    """工作区根入导入路径 → ``tools.X`` 可导入，契约库的 9 个公开函数齐备。"""
    filesystem = import_tool_module(workspace, "filesystem")
    assert filesystem.read_file.name == "read_file"

    changes = import_tool_module(workspace, "changes")
    for name in CONTRACT_FUNCTION_NAMES:
        assert callable(getattr(changes, name)), name
    assert changes.CHANGE_RECORD_VERSION == 1


def test_top_level_module_import_form_works(tools_dir_on_path: Path) -> None:
    """``tools/`` 目录入导入路径 → 顶层模块形态可导入（走 ImportError 回退）。"""
    module = importlib.import_module("filesystem")
    assert module.read_file.name == "read_file"
    # 顶层模块形态下，模块来自工作区的 tools/ 目录本身。
    assert module.__file__ is not None
    assert Path(module.__file__).parent.name == "tools"


def test_tool_counts_and_contract_library_has_no_framework_import(
    workspace: Path,
) -> None:
    """3 个工具模块 7/1/1 个工具函数；契约库与包初始化各 0 个且零框架导入。"""
    import_tool_module(workspace, "filesystem")
    import_tool_module(workspace, "commandline")
    import_tool_module(workspace, "webfetch")
    changes = import_tool_module(workspace, "changes")
    package = import_tool_module(workspace, "__init__")

    assert count_tools((workspace / "tools" / "filesystem.py").read_text("utf-8")) == 7
    assert count_tools((workspace / "tools" / "commandline.py").read_text("utf-8")) == 1
    assert count_tools((workspace / "tools" / "webfetch.py").read_text("utf-8")) == 1
    assert count_tools((workspace / "tools" / "changes.py").read_text("utf-8")) == 0
    assert count_tools((workspace / "tools" / "__init__.py").read_text("utf-8")) == 0

    assert not [name for name in vars(changes) if name.startswith("_tool")]
    assert not [name for name in vars(package) if name.endswith("_tool")]
    assert callable(changes.build_change_record)

    # 契约库 MUST 零框架导入 —— 在独立子进程里只 import 契约库再验模块表。
    probe = (
        "import sys, tools.changes; "
        "print(sorted(m for m in sys.modules "
        "if m.split('.')[0] in {'langchain', 'langchain_core', 'langgraph'}))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "[]"


# --- US3：命令工具（T025 ~ T029 / T104）------------------------------------------


def test_run_shell_echo_returns_parsable_json(workspace: Path) -> None:
    """回显命令返回可解析 JSON，字段齐备且工作目录是工作区根。"""
    commandline = import_tool_module(workspace, "commandline")

    result = json.loads(commandline.run_shell.invoke({"command": "echo hello"}))

    assert result["stdout"] == "hello\n"
    assert result["stderr"] == ""
    assert result["returncode"] == 0
    assert result["timed_out"] is False
    assert result["truncated"] is False
    assert result["argv"] == ["echo", "hello"]
    assert result["cwd"] == str(workspace)


def test_run_shell_timeout_returns_marker_instead_of_raising(workspace: Path) -> None:
    """超时返回 ``timed_out`` 为真、返回码 ``-1`` 的 JSON —— MUST NOT 抛异常。"""
    commandline = import_tool_module(workspace, "commandline")

    result = json.loads(
        commandline.run_shell.invoke({"command": "sleep 5", "timeout": 1})
    )

    assert result["timed_out"] is True
    assert result["returncode"] == -1
    assert result["stderr"] == ""


def test_run_shell_cwd_defaults_to_workspace_root(workspace: Path) -> None:
    """工作目录默认是工作区根；相对 ``cwd`` 也以工作区根为基准。"""
    commandline = import_tool_module(workspace, "commandline")

    default = json.loads(commandline.run_shell.invoke({"command": "pwd"}))
    assert default["cwd"] == str(workspace)
    assert default["stdout"].strip() == str(workspace)

    relative = json.loads(
        commandline.run_shell.invoke({"command": "pwd", "cwd": "tools"})
    )
    assert relative["cwd"] == str(workspace / "tools")
    assert relative["stdout"].strip() == str(workspace / "tools")


def test_run_shell_output_is_truncated_and_never_written_to_disk(
    workspace: Path,
) -> None:
    """输出超限 → ``truncated`` 为真 + OpenCode 式标记；完整输出不落盘。"""
    commandline = import_tool_module(workspace, "commandline")

    result = json.loads(commandline.run_shell.invoke({"command": "seq 1 5000"}))

    assert result["truncated"] is True
    assert "[showing lines 1-2000 of 5000; full output not saved]" in result["stdout"]
    assert result["stdout"].rstrip().endswith(
        "[showing lines 1-2000 of 5000; full output not saved]"
    )
    # 完整输出 MUST NOT 落盘
    written = {p.name for p in workspace.rglob("*") if p.is_file()}
    assert not any("5000" in name or "output" in name.lower() for name in written)


def test_output_limit_constants_match_on_both_sides(workspace: Path) -> None:
    """读取侧与命令输出侧的 2000 行 / 50 KiB 上限数值一致。"""
    filesystem = import_tool_module(workspace, "filesystem")
    commandline = import_tool_module(workspace, "commandline")

    assert filesystem.MAX_READ_LINES == commandline.MAX_OUTPUT_LINES == 2000
    assert filesystem.MAX_READ_BYTES == commandline.MAX_OUTPUT_BYTES == 50 * 1024


def test_run_shell_timeout_has_no_upper_bound(workspace: Path) -> None:
    """命令工具的 ``timeout`` 不设上限 —— 999 秒 MUST 正常返回而不报错。"""
    commandline = import_tool_module(workspace, "commandline")

    result = json.loads(commandline.run_shell.invoke({"command": "echo x", "timeout": 999}))

    assert result["returncode"] == 0
    assert result["timed_out"] is False
    assert "x" in result["stdout"]


# --- US4：文件工具的七个动作（T030 ~ T035 / T108）--------------------------------


def test_write_then_read_round_trip(workspace: Path) -> None:
    """写后读：去掉呈现文本的包装后逐字一致。"""
    filesystem = import_tool_module(workspace, "filesystem")

    content = "hello world\nsecond line\n"
    filesystem.write_file.invoke({"path": "demo.txt", "content": content})

    rendered = filesystem.read_file.invoke({"path": "demo.txt"})

    assert strip_presentation(rendered) == content
    assert rendered.splitlines()[0] == "Read file demo.txt, lines 1-2"


def test_copy_move_delete_trio(workspace: Path) -> None:
    """复制 → 移动 → 删除三件套：内容一致、源消失、目录按目录粒度删除。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "src.txt", "content": "payload\n"})
    filesystem.copy_file.invoke({"src": "src.txt", "dst": "copy.txt"})
    assert (workspace / "copy.txt").read_text(encoding="utf-8") == "payload\n"

    filesystem.move_file.invoke({"src": "copy.txt", "dst": "moved.txt"})
    assert not (workspace / "copy.txt").exists()
    assert (workspace / "moved.txt").read_text(encoding="utf-8") == "payload\n"

    filesystem.delete_file.invoke({"path": "moved.txt"})
    assert not (workspace / "moved.txt").exists()

    (workspace / "tree").mkdir()
    (workspace / "tree" / "inner.txt").write_text("x", encoding="utf-8")
    result = json.loads(filesystem.delete_file.invoke({"path": "tree"}))
    assert result["type"] == "directory"
    assert not (workspace / "tree").exists()


def test_list_dir_returns_names_with_pagination(workspace: Path) -> None:
    """``list_dir`` 返回名称列表（0 基 offset / limit 上限 2000 / 代码点序）。"""
    filesystem = import_tool_module(workspace, "filesystem")

    for name in ("b.txt", "a.txt", ".hidden"):
        (workspace / name).write_text("x", encoding="utf-8")

    names = filesystem.list_dir.invoke({"path": "."})
    assert isinstance(names, list)
    assert ".hidden" in names
    assert names == sorted(names)

    without_hidden = filesystem.list_dir.invoke({"path": ".", "include_hidden": False})
    assert ".hidden" not in without_hidden

    offset = filesystem.list_dir.invoke({"path": ".", "offset": 1})
    assert offset == names[1:]

    limited = filesystem.list_dir.invoke({"path": ".", "limit": 1})
    assert limited == names[:1]


def test_stat_returns_mapping_and_never_raises_for_missing_path(
    workspace: Path,
) -> None:
    """``stat`` 返回映射；``with_hash`` 追加带前缀的指纹；路径不存在不抛异常。"""
    filesystem = import_tool_module(workspace, "filesystem")

    (workspace / "demo.txt").write_text("hello", encoding="utf-8")

    info = filesystem.stat.invoke({"path": "demo.txt", "with_hash": True})
    assert isinstance(info, dict)
    assert info["size"] == 5
    assert info["is_file"] is True
    assert info["is_dir"] is False
    assert info["exists"] is True
    assert info["sha256"].startswith("sha256:")

    missing = filesystem.stat.invoke({"path": "no-such-file"})
    assert missing["exists"] is False
    assert missing["is_file"] is False
    assert missing["is_dir"] is False


def test_read_file_presentation_format(workspace: Path) -> None:
    """呈现格式：页范围头 + 行号前缀 + 空文件口径 + 单行截断标记。"""
    filesystem = import_tool_module(workspace, "filesystem")

    (workspace / "demo.txt").write_text("a\nb\n", encoding="utf-8")
    rendered = filesystem.read_file.invoke({"path": "demo.txt"})
    assert rendered.splitlines()[0] == "Read file demo.txt, lines 1-2"
    assert rendered.splitlines()[1] == "1: a"
    assert rendered.splitlines()[2] == "2: b"

    (workspace / "empty.txt").write_text("", encoding="utf-8")
    assert filesystem.read_file.invoke({"path": "empty.txt"}) == (
        "Read file empty.txt, 0 lines"
    )

    (workspace / "long.txt").write_text("x" * 5000, encoding="utf-8")
    long_rendered = filesystem.read_file.invoke({"path": "long.txt"})
    assert "... (line truncated to 2000 chars)" in long_rendered

    # 小文件走整份返回：全部行都在，且没有续读提示。
    small = filesystem.read_file.invoke({"path": "demo.txt"})
    assert "Output truncated" not in small
    assert small.splitlines()[-1] == "2: b"


def test_read_file_dual_limits(workspace: Path) -> None:
    """读取侧双上限：行数上限无条件生效；体积上限独立生效；越界 / 二进制报错。"""
    filesystem = import_tool_module(workspace, "filesystem")

    # ① 行数超 2000
    (workspace / "many.txt").write_text(
        "".join(f"line {i}\n" for i in range(3000)), encoding="utf-8"
    )
    many = filesystem.read_file.invoke({"path": "many.txt"})
    assert many.splitlines()[0] == "Read file many.txt, lines 1-2000"
    assert "[Output truncated. Continue reading with offset: 2001]" in many

    # ② 体积超 50 KiB（多行累加超限 —— 单行超长由单行字符上限负责）
    (workspace / "big.txt").write_text(
        "".join("y" * 99 + "\n" for _ in range(600)), encoding="utf-8"
    )
    big = filesystem.read_file.invoke({"path": "big.txt"})
    assert "[Output truncated. Continue reading with offset:" in big

    # ③ 区分样本：体积 ≤ 50 KiB 但行数 > 2000 —— 行数上限仍无条件生效
    (workspace / "many_short.txt").write_text(
        "".join("x\n" for _ in range(3000)), encoding="utf-8"
    )
    assert (workspace / "many_short.txt").stat().st_size <= 50 * 1024
    short = filesystem.read_file.invoke({"path": "many_short.txt"})
    assert "[Output truncated. Continue reading with offset: 2001]" in short

    # ④ 起始行越界报错
    (workspace / "demo.txt").write_text("a\nb\n", encoding="utf-8")
    with pytest.raises(ValueError):
        filesystem.read_file.invoke({"path": "demo.txt", "start_line": 99})

    # ⑤ 含 NUL 字节的文件报错
    (workspace / "binary.bin").write_bytes(b"abc\x00def")
    with pytest.raises(ValueError):
        filesystem.read_file.invoke({"path": "binary.bin"})

    # ⑥ 图片 / PDF 报错
    (workspace / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\nrest")
    with pytest.raises(ValueError):
        filesystem.read_file.invoke({"path": "pic.png"})
    (workspace / "doc.pdf").write_bytes(b"%PDF-1.7 rest")
    with pytest.raises(ValueError):
        filesystem.read_file.invoke({"path": "doc.pdf"})


def test_read_file_pagination_boundaries(workspace: Path) -> None:
    """读取侧分页边界：目录分支 / 请求行数超上限 / 列目录条目超上限。"""
    filesystem = import_tool_module(workspace, "filesystem")

    directory = filesystem.read_file.invoke({"path": "tools"})
    assert directory.splitlines()[0].startswith("Read directory tools, entries 1-")
    assert "__init__.py" in directory

    (workspace / "many.txt").write_text(
        "".join(f"line {i}\n" for i in range(3000)), encoding="utf-8"
    )
    requested = filesystem.read_file.invoke({"path": "many.txt", "num_lines": 9999})
    assert requested.splitlines()[0] == "Read file many.txt, lines 1-2000"

    for index in range(2100):
        (workspace / f"entry-{index:04d}.txt").write_text("x", encoding="utf-8")
    entries = filesystem.list_dir.invoke({"path": ".", "limit": 9999})
    assert len(entries) == 2000


# --- US5：网络工具（T036 ~ T042 / T107）------------------------------------------


def test_fetch_url_success_returns_frozen_shape(workspace: Path, httpx_mock: HTTPXMock) -> None:
    """成功路径返回可解析 JSON，四字段恰为状态码 / 正文 / 响应头 / 最终地址。"""
    httpx_mock.add_response(
        url="https://example.com", method="GET", status_code=200, text="mocked body"
    )
    webfetch = import_tool_module(workspace, "webfetch")

    result = json.loads(webfetch.fetch_url.invoke({"url": "https://example.com"}))

    assert result["status_code"] == 200
    assert "mocked body" in result["body"]
    assert set(result) == {"status_code", "body", "headers", "url"}
    assert "change" not in result


def test_fetch_url_timeout_is_propagated(workspace: Path, httpx_mock: HTTPXMock) -> None:
    """网络超时 MUST 抛出超时异常（与命令工具的"返回标记"有意不对称）。"""
    httpx_mock.add_exception(httpx.ReadTimeout("too slow"), url="https://slow.example")
    webfetch = import_tool_module(workspace, "webfetch")

    with pytest.raises(httpx.TimeoutException):
        webfetch.fetch_url.invoke({"url": "https://slow.example"})


def test_fetch_url_rejects_non_http_scheme(workspace: Path) -> None:
    """协议白名单：``ftp://`` / ``file://`` MUST 报错且不发起请求。"""
    webfetch = import_tool_module(workspace, "webfetch")

    for url in ("ftp://example.com/x", "file:///etc/passwd"):
        with pytest.raises(ValueError):
            webfetch.fetch_url.invoke({"url": url})


def test_fetch_url_rejects_non_text_mime(workspace: Path, httpx_mock: HTTPXMock) -> None:
    """非文本 MIME MUST 报错且不返回正文。"""
    httpx_mock.add_response(
        url="https://img.example",
        status_code=200,
        content=b"\x89PNG\r\n\x1a\n",
        headers={"content-type": "image/png"},
    )
    webfetch = import_tool_module(workspace, "webfetch")

    with pytest.raises(ValueError):
        webfetch.fetch_url.invoke({"url": "https://img.example"})


def test_fetch_url_rejects_non_2xx(workspace: Path, httpx_mock: HTTPXMock) -> None:
    """非 2xx MUST 报错且不返回正文。"""
    httpx_mock.add_response(
        url="https://err.example", status_code=500, text="boom"
    )
    webfetch = import_tool_module(workspace, "webfetch")

    with pytest.raises(httpx.HTTPStatusError):
        webfetch.fetch_url.invoke({"url": "https://err.example"})


def test_fetch_url_enforces_body_limit_while_streaming(
    workspace: Path, httpx_mock: HTTPXMock
) -> None:
    """无 ``Content-Length`` 的流式响应 MUST 在读取过程中触发 5 MiB 上限。"""

    class _ChunkedStream(httpx.SyncByteStream):
        """没有 ``Content-Length`` 的分块响应体。"""

        def __iter__(self) -> Iterator[bytes]:
            for _ in range(200):
                yield b"x" * 65536

    httpx_mock.add_response(url="https://big.example", stream=_ChunkedStream())
    webfetch = import_tool_module(workspace, "webfetch")

    with pytest.raises(ValueError):
        webfetch.fetch_url.invoke({"url": "https://big.example"})


def test_fetch_url_rejects_timeout_above_cap(workspace: Path) -> None:
    """超时值超过 120 秒 MUST 在发请求前报错。"""
    webfetch = import_tool_module(workspace, "webfetch")

    with pytest.raises(ValueError):
        webfetch.fetch_url.invoke({"url": "https://example.com", "timeout": 999})


def test_fetch_url_documents_boundaries_and_does_not_filter_addresses(
    workspace: Path, httpx_mock: HTTPXMock
) -> None:
    """静态层：说明文字逐条写出四道边界；行为层：回环地址 MUST 被放行。"""
    httpx_mock.add_response(
        url="http://127.0.0.1:8000/x", status_code=200, text="loopback"
    )
    webfetch = import_tool_module(workspace, "webfetch")

    source = (workspace / "tools" / "webfetch.py").read_text(encoding="utf-8")
    for needle in ("http", "https", "5 MiB", "MIME", "2xx"):
        assert needle in source, needle

    result = json.loads(webfetch.fetch_url.invoke({"url": "http://127.0.0.1:8000/x"}))
    assert result["status_code"] == 200
    assert "loopback" in result["body"]


# --- US6：示例 Skill 的三层结构（T043 ~ T046）------------------------------------


def test_skill_frontmatter_has_exactly_two_fields(workspace: Path) -> None:
    """frontmatter 恰含 ``name`` 与 ``description`` 两字段。"""
    content = (workspace / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")

    assert content.startswith("---\n")
    frontmatter = content.split("---")[1]
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line and not line.strip().startswith("#")
    }
    assert keys == {"name", "description"}
    assert "name: example" in frontmatter


def test_skill_three_layers_are_present(workspace: Path) -> None:
    """Level 2 正文非空；Level 3 的三个子目录各含 ≥ 1 个文件。"""
    skill = (workspace / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.strip()
    assert "Level 2" in skill

    for name in ("reference", "scripts", "templates"):
        directory = workspace / "skills" / "example" / name
        assert directory.is_dir(), name
        assert [p for p in directory.iterdir() if p.is_file()], name

    # 三个 Level 3 子目录 MUST NOT 作为清单条目新增
    entries = load_template_manifest()
    paths = {entry["path"] for entry in entries}
    assert "skills/example/reference" not in paths
    assert "skills/example/scripts" not in paths
    assert "skills/example/templates" not in paths
    assert len(entries) == 54


def test_skill_level2_paths_are_workspace_root_relative(workspace: Path) -> None:
    """Level 2 正文里的示例路径 MUST 以工作区根为基准。"""
    skill = (workspace / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")

    for relative in (
        "skills/example/reference/example.md",
        "skills/example/scripts/example.py",
        "skills/example/templates/example.md",
    ):
        assert relative in skill, relative
    assert "工作区根" in skill


def test_skill_script_keeps_entry_block_and_is_not_an_agent_entry(
    workspace: Path,
) -> None:
    """第三层脚本保留入口块；工作区内 MUST NOT 出现智能体入口文件。"""
    script = (workspace / "skills" / "example" / "scripts" / "example.py").read_text(
        encoding="utf-8"
    )
    assert 'if __name__ == "__main__":' in script
    assert "sys.exit(main())" in script

    # MUST NOT 命名为 agent.py / main.py
    names = {p.name for p in workspace.rglob("*") if p.is_file()}
    assert "agent.py" not in names
    assert "main.py" not in names

    # MUST NOT 承担"创建智能体"职责
    for path in workspace.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "create_agent" not in text, path
        assert "from donkey" not in text, path


# --- US7：职责正交（T047）--------------------------------------------------------


def test_builtin_tools_contain_no_search_capability(workspace: Path) -> None:
    """3 个内置工具文件 MUST NOT 含"按文件名找 / 按内容找"两个能力。"""
    for name in ("filesystem.py", "commandline.py", "webfetch.py"):
        text = (workspace / "tools" / name).read_text(encoding="utf-8")
        assert "glob_search" not in text, name
        assert "grep_search" not in text, name


# --- US8：幂等补齐（T048）--------------------------------------------------------


def test_deleted_manifest_entries_are_replenished(workspace: Path) -> None:
    """清单内条目被删后再次 init MUST 补齐；非强制模式下其它文件不被改动。"""
    filesystem = import_tool_module(workspace, "filesystem")

    (workspace / "tools" / "filesystem.py").unlink()
    (workspace / "skills" / "example" / "reference" / "example.md").unlink()
    (workspace / "instruction.md").write_text("用户改写的内容", encoding="utf-8")
    before = (workspace / "instruction.md").stat().st_mtime_ns

    result = init_workspace(workspace)

    assert result.templates_loaded == 54
    assert (workspace / "tools" / "filesystem.py").is_file()
    assert (workspace / "skills" / "example" / "reference" / "example.md").is_file()
    assert (workspace / "instruction.md").read_text(encoding="utf-8") == "用户改写的内容"
    assert (workspace / "instruction.md").stat().st_mtime_ns == before
    assert filesystem is not None


# --- US9：强制重置豁免（T050 ~ T053）---------------------------------------------


def test_force_preserves_the_contract_library_byte_for_byte(workspace: Path) -> None:
    """``--force`` 后已存在的契约库内容 MUST 逐字节未变。"""
    contract = workspace / "tools" / "changes.py"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\n# 用户追加的一行\n", encoding="utf-8"
    )
    before = contract.read_bytes()

    result = init_workspace(workspace, force=True)

    assert result.templates_loaded == 54
    assert result.files_skipped == 1
    assert contract.read_bytes() == before


def test_force_restores_every_other_entry_to_factory_content(
    workspace: Path,
) -> None:
    """契约库之外的清单内条目 MUST 100% 恢复出厂内容。"""
    (workspace / "tools" / "filesystem.py").write_text("# 改坏了\n", encoding="utf-8")
    (workspace / "tools" / "__init__.py").write_text("# 改坏了\n", encoding="utf-8")
    (workspace / "tools" / "README.md").write_text("# 改坏了\n", encoding="utf-8")
    (workspace / "skills" / "example" / "SKILL.md").write_text("# 改坏了\n", "utf-8")
    (workspace / "skills" / "example" / "reference" / "example.md").write_text(
        "# 改坏了\n", encoding="utf-8"
    )
    (workspace / "skills" / "example" / "scripts" / "example.py").write_text(
        "# 改坏了\n", encoding="utf-8"
    )
    (workspace / "skills" / "example" / "templates" / "example.md").write_text(
        "# 改坏了\n", encoding="utf-8"
    )

    init_workspace(workspace, force=True)

    for relative in (
        "tools/filesystem.py",
        "tools/__init__.py",
        "tools/README.md",
        "skills/example/SKILL.md",
        "skills/example/reference/example.md",
        "skills/example/scripts/example.py",
        "skills/example/templates/example.md",
    ):
        text = (workspace / relative).read_text(encoding="utf-8")
        assert "# 改坏了" not in text, relative


def test_counts_across_init_modes(workspace: Path, tmp_path: Path) -> None:
    """三种情形的计数（按「对象 × 动作」分解 —— 宪法 [D-22]）。

    - **全新**：文件新建 48、目录新建 6、其余为 0；
    - **二次**：文件跳过 48、目录跳过 6、其余为 0；
    - **强制**（契约库已存在）：文件**覆盖** 47、文件跳过 1（契约库豁免）、
      目录跳过 6。

    > **断言改写登记（宪法 [D-22] · 2026-10-30 · Maintainer 裁决）**：原断言
    > 为 ``(templates, created, skipped)`` 三元组，其中强制情形的 ``created=47``
    > 实为"**覆盖**"而非"新建"—— 两个动作被并入同一计数。本断言改为按
    > 「对象 × 动作」分解，并保留 v1 三元组的语义归位（``files_created``
    > 严格为"本次新建"）。
    """
    fresh = init_workspace(tmp_path / "fresh")
    assert (
        fresh.templates_loaded,
        fresh.files_created,
        fresh.files_overwritten,
        fresh.files_skipped,
        fresh.dirs_created,
        fresh.dirs_skipped,
    ) == (54, 48, 0, 0, 6, 0)

    second = init_workspace(tmp_path / "fresh")
    assert (
        second.templates_loaded,
        second.files_created,
        second.files_overwritten,
        second.files_skipped,
        second.dirs_created,
        second.dirs_skipped,
    ) == (54, 0, 0, 48, 0, 6)

    forced = init_workspace(workspace, force=True)
    assert (
        forced.templates_loaded,
        forced.files_created,
        forced.files_overwritten,
        forced.files_skipped,
        forced.dirs_created,
        forced.dirs_skipped,
    ) == (54, 0, 47, 1, 0, 6)


def test_force_keeps_user_authored_tools(workspace: Path) -> None:
    """清单外的用户自写工具在 ``--force`` 后 MUST 仍在。"""
    custom = workspace / "tools" / "my_custom_tool.py"
    custom.write_text("# 我自己的工具\n", encoding="utf-8")

    init_workspace(workspace, force=True)

    assert custom.is_file()
    assert custom.read_text(encoding="utf-8") == "# 我自己的工具\n"


# --- US11：init 不做配置检查（T059）----------------------------------------------


def test_init_does_not_validate_generated_tool_files(workspace: Path) -> None:
    """把内置工具文件改坏后再次 init 仍以成功状态结束，且不抛配置类异常。"""
    (workspace / "tools" / "filesystem.py").write_text(
        "这不是合法的 Python !!!", encoding="utf-8"
    )

    result = init_workspace(workspace)

    assert result.templates_loaded == 54
    assert (workspace / "tools" / "filesystem.py").read_text(encoding="utf-8") == (
        "这不是合法的 Python !!!"
    )


# --- US12：变更记录（T060 ~ T065）------------------------------------------------


def test_create_change_record_fields(workspace: Path) -> None:
    """首次写入返回 ``create`` 动作，旧指纹为 ``null``（Python 侧 ``None``）。"""
    filesystem = import_tool_module(workspace, "filesystem")

    result = json.loads(
        filesystem.write_file.invoke({"path": "demo.txt", "content": "hello\n"})
    )
    change = result["change"]

    assert result["action"] == "create"
    assert result["applied"] is True
    assert change["version"] == 1
    assert change["previous_exists"] is False
    assert change["previous_hash"] is None
    assert change["new_hash"] is not None
    assert change["new_hash"].startswith("sha256:")
    assert "+hello" in change["unified_diff"]


def test_update_change_record_carries_previous_hash_and_diff(
    workspace: Path,
) -> None:
    """二次写入返回 ``update`` 动作，旧指纹等于上次写入后的新指纹。"""
    filesystem = import_tool_module(workspace, "filesystem")

    first = json.loads(
        filesystem.write_file.invoke({"path": "demo.txt", "content": "a\nb\n"})
    )
    second = json.loads(
        filesystem.write_file.invoke({"path": "demo.txt", "content": "a\nc\n"})
    )
    change = second["change"]

    assert second["action"] == "update"
    assert change["previous_exists"] is True
    assert change["previous_hash"] == first["change"]["new_hash"]
    assert "-b" in change["unified_diff"]
    assert "+c" in change["unified_diff"]


def test_change_record_baseline_key_set_is_stable(workspace: Path) -> None:
    """变更记录的键集合恰为 12 个基线字段；不存在的指纹 MUST 为 ``None``。"""
    filesystem = import_tool_module(workspace, "filesystem")
    changes = import_tool_module(workspace, "changes")

    result = json.loads(
        filesystem.write_file.invoke({"path": "demo.txt", "content": "hello\n"})
    )
    assert set(result["change"]) == set(BASELINE_KEYS)

    record = changes.build_change_record(
        "create", workspace / "demo.txt", None, b"hello\n"
    )
    assert set(record) == set(BASELINE_KEYS)
    assert record["previous_hash"] is None
    assert record["new_hash"] is not None


def test_conditional_fields_of_change_record(workspace: Path) -> None:
    """``copy`` / ``move`` 追加两个源字段；旧正文按 256 KiB 阈值取舍。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "src.txt", "content": "payload\n"})
    copied = json.loads(
        filesystem.copy_file.invoke({"src": "src.txt", "dst": "copy.txt"})
    )
    assert copied["change"]["src"] == str(workspace / "src.txt")
    assert copied["change"]["src_rel_path"] == "src.txt"

    moved = json.loads(filesystem.move_file.invoke({"src": "copy.txt", "dst": "moved.txt"}))
    assert moved["change"]["src_rel_path"] == "copy.txt"

    small = json.loads(
        filesystem.write_file.invoke({"path": "small.txt", "content": "abc\n"})
    )
    assert "previous_content" not in small["change"]
    small = json.loads(
        filesystem.write_file.invoke(
            {"path": "small.txt", "content": "def\n", "include_previous": True}
        )
    )
    assert small["change"]["previous_content"] == "abc\n"
    assert "previous_content_truncated" not in small["change"]

    big_content = "z" * (300 * 1024)
    filesystem.write_file.invoke({"path": "big.txt", "content": big_content})
    big = json.loads(
        filesystem.write_file.invoke(
            {"path": "big.txt", "content": "y", "include_previous": True}
        )
    )
    assert big["change"]["previous_content_truncated"] is True
    assert "previous_content" not in big["change"]


def test_rel_path_and_diff_headers(workspace: Path, tmp_path: Path) -> None:
    """``rel_path`` 是工作区相对 POSIX 路径；越界路径回退为绝对路径。"""
    filesystem = import_tool_module(workspace, "filesystem")

    inside = json.loads(
        filesystem.write_file.invoke({"path": "demo.txt", "content": "hello\n"})
    )
    assert inside["change"]["rel_path"] == "demo.txt"
    assert inside["change"]["unified_diff"].startswith("--- a/demo.txt\n+++ b/demo.txt\n")

    outside_path = tmp_path / "outside.txt"
    outside = json.loads(
        filesystem.write_file.invoke(
            {"path": str(outside_path), "content": "hello\n"}
        )
    )
    assert outside["change"]["rel_path"] == str(outside_path)
    assert outside["change"]["unified_diff"].startswith(
        f"--- a/{outside_path}\n+++ b/{outside_path}\n"
    )


def test_diff_is_truncated_beyond_64_kib(workspace: Path) -> None:
    """差异超过 64 KiB 时 MUST 截断且 ``diff_truncated`` 为真。"""
    filesystem = import_tool_module(workspace, "filesystem")

    body = "".join(f"line {i:04d} " + "a" * 40 + "\n" for i in range(2000))
    filesystem.write_file.invoke({"path": "demo.txt", "content": body})
    result = json.loads(
        filesystem.write_file.invoke(
            {"path": "demo.txt", "content": "".join("b" * 50 + "\n" for _ in range(2000))}
        )
    )

    assert result["change"]["diff_truncated"] is True
    assert len(result["change"]["unified_diff"].encode("utf-8")) <= 64 * 1024


# --- US13：预览模式（T066 ~ T068）------------------------------------------------


def test_write_file_dry_run_leaves_disk_untouched(workspace: Path) -> None:
    """预览写入：磁盘逐字节未变、``applied`` 为假、差异非空、无临时文件残留。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "demo.txt", "content": "old\n"})
    before = (workspace / "demo.txt").read_bytes()

    result = json.loads(
        filesystem.write_file.invoke(
            {"path": "demo.txt", "content": "new\n", "dry_run": True}
        )
    )

    assert result["applied"] is False
    assert result["change"]["applied"] is False
    assert result["change"]["unified_diff"]
    assert (workspace / "demo.txt").read_bytes() == before
    assert not list(workspace.glob("*.donkey-tmp"))
    assert not list(workspace.glob(".*.donkey-tmp"))


def test_copy_move_delete_dry_run_have_no_disk_side_effects(
    workspace: Path,
) -> None:
    """复制 / 移动 / 删除的预览 MUST 零磁盘副作用，但仍返回完整变更记录。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "src.txt", "content": "payload\n"})

    copied = json.loads(
        filesystem.copy_file.invoke(
            {"src": "src.txt", "dst": "copy.txt", "dry_run": True}
        )
    )
    assert copied["applied"] is False
    assert copied["change"]["applied"] is False
    assert copied["change"]["version"] == 1
    assert not (workspace / "copy.txt").exists()

    moved = json.loads(
        filesystem.move_file.invoke(
            {"src": "src.txt", "dst": "moved.txt", "dry_run": True}
        )
    )
    assert moved["applied"] is False
    assert (workspace / "src.txt").exists()
    assert not (workspace / "moved.txt").exists()

    deleted = json.loads(
        filesystem.delete_file.invoke({"path": "src.txt", "dry_run": True})
    )
    assert deleted["applied"] is False
    assert deleted["change"]["action"] == "delete"
    assert (workspace / "src.txt").exists()


def test_dry_run_does_not_create_parent_directory(workspace: Path) -> None:
    """对不存在的父目录做预览写入 MUST NOT 创建该父目录。"""
    filesystem = import_tool_module(workspace, "filesystem")

    result = json.loads(
        filesystem.write_file.invoke(
            {"path": "new-dir/demo.txt", "content": "x\n", "dry_run": True}
        )
    )

    assert result["applied"] is False
    assert not (workspace / "new-dir").exists()


# --- US14：写失败不毁旧内容（T069 ~ T072）----------------------------------------


def test_atomic_write_failure_leaves_old_content_and_no_residue(
    workspace: Path,
) -> None:
    """父路径是已存在的文件时写入抛异常，旧内容完好且无临时文件残留。"""
    filesystem = import_tool_module(workspace, "filesystem")

    blocker = workspace / "blocker"
    blocker.write_text("原内容", encoding="utf-8")

    with pytest.raises(OSError):
        filesystem.write_file.invoke({"path": "blocker/child.txt", "content": "x\n"})

    assert blocker.read_text(encoding="utf-8") == "原内容"
    assert not list(workspace.glob(".*.donkey-tmp"))


def test_write_creates_parent_and_rejects_directory_target(
    workspace: Path,
) -> None:
    """写向不存在的父目录 MUST 建目录并落盘；目标是目录 MUST 报错。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "deep/nested/demo.txt", "content": "x\n"})
    assert (workspace / "deep" / "nested" / "demo.txt").read_text("utf-8") == "x\n"

    (workspace / "adir").mkdir()
    (workspace / "adir" / "keep.txt").write_text("保留", encoding="utf-8")
    with pytest.raises(IsADirectoryError):
        filesystem.write_file.invoke({"path": "adir", "content": "x\n"})
    assert (workspace / "adir" / "keep.txt").read_text(encoding="utf-8") == "保留"


def test_hash_is_computed_over_raw_bytes(workspace: Path) -> None:
    """含 BOM 或非法 UTF-8 字节的文件，其指纹 MUST 与原始字节的指纹逐字相等。"""
    filesystem = import_tool_module(workspace, "filesystem")
    changes = import_tool_module(workspace, "changes")

    raw = b"\xef\xbb\xbfhello\xff\xfe"
    (workspace / "weird.bin").write_bytes(raw)

    info = filesystem.stat.invoke({"path": "weird.bin", "with_hash": True})
    assert info["sha256"] == changes.sha256_bytes(raw)


def test_successful_write_leaves_no_temp_file_residue(workspace: Path) -> None:
    """写入成功后目标目录 MUST NOT 残留任何 ``.donkey-tmp`` 文件。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "demo.txt", "content": "x\n"})

    assert not list(workspace.glob(".*.donkey-tmp"))
    assert not list((workspace / "tools").glob(".*.donkey-tmp"))


# --- US15：删除记录与契约版本冻结（T073 ~ T076）----------------------------------


def test_delete_change_record_fields(workspace: Path) -> None:
    """删除返回 ``delete`` 动作、类型 ``file``、旧指纹非空、新指纹为 ``null``。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "demo.txt", "content": "payload\n"})
    result = json.loads(filesystem.delete_file.invoke({"path": "demo.txt"}))
    change = result["change"]

    assert result["action"] == "delete"
    assert result["type"] == "file"
    assert change["previous_hash"] is not None
    assert change["new_hash"] is None
    assert change["new_size"] == 0
    assert not (workspace / "demo.txt").exists()


def test_delete_can_include_previous_content(workspace: Path) -> None:
    """请求旧正文时文件给出旧正文；目录则不出现任何旧正文字段。"""
    filesystem = import_tool_module(workspace, "filesystem")

    filesystem.write_file.invoke({"path": "demo.txt", "content": "payload\n"})
    result = json.loads(
        filesystem.delete_file.invoke({"path": "demo.txt", "include_previous": True})
    )
    assert result["change"]["previous_content"] == "payload\n"

    (workspace / "tree").mkdir()
    directory = json.loads(
        filesystem.delete_file.invoke({"path": "tree", "include_previous": True})
    )
    assert "previous_content" not in directory["change"]
    assert "previous_content_truncated" not in directory["change"]


def test_contract_version_and_constants_are_frozen(workspace: Path) -> None:
    """契约版本恒为 ``1``；三个常量逐字冻结。"""
    changes = import_tool_module(workspace, "changes")

    assert changes.CHANGE_RECORD_VERSION == 1
    assert changes.MAX_DIFF_BYTES == 64 * 1024
    assert changes.MAX_PREVIOUS_BYTES == 256 * 1024

    record = changes.build_change_record("create", workspace / "demo.txt", None, b"x\n")
    assert set(record) == set(BASELINE_KEYS)
    assert record["version"] == 1


def test_expected_hash_guard_rejects_mismatching_writes(workspace: Path) -> None:
    """四个改文件工具传入不匹配的期望指纹时 MUST 拒绝执行且无磁盘副作用。"""
    filesystem = import_tool_module(workspace, "filesystem")
    changes = import_tool_module(workspace, "changes")

    filesystem.write_file.invoke({"path": "demo.txt", "content": "payload\n"})
    (workspace / "other.txt").write_text("other", encoding="utf-8")
    before = (workspace / "demo.txt").read_bytes()

    with pytest.raises(changes.FileChangedError):
        filesystem.write_file.invoke(
            {"path": "demo.txt", "content": "x\n", "expected_hash": "sha256:deadbeef"}
        )
    assert (workspace / "demo.txt").read_bytes() == before

    with pytest.raises(changes.FileChangedError):
        filesystem.copy_file.invoke(
            {"src": "other.txt", "dst": "demo.txt", "expected_hash": "sha256:deadbeef"}
        )
    assert (workspace / "demo.txt").read_bytes() == before

    with pytest.raises(changes.FileChangedError):
        filesystem.move_file.invoke(
            {"src": "other.txt", "dst": "demo.txt", "expected_hash": "sha256:deadbeef"}
        )
    assert (workspace / "other.txt").exists()

    with pytest.raises(changes.FileChangedError):
        filesystem.delete_file.invoke(
            {"path": "demo.txt", "expected_hash": "sha256:deadbeef"}
        )
    assert (workspace / "demo.txt").exists()

    # 不传期望指纹时行为与旧调用方式一致
    plain = json.loads(filesystem.write_file.invoke({"path": "demo.txt", "content": "y\n"}))
    assert plain["applied"] is True
    assert plain["change"]["applied"] is True


# --- 退出码 4 的映射与错误信息（T105）--------------------------------------------


def test_exit_code_4_mapping_and_error_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """退出码 4 已进映射表；端到端触发时返回码为 4 且错误信息含下一步。"""
    from donkey.cli import cli_client
    from donkey.core import exit_codes
    from donkey.core.workspace import init as init_module

    assert exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION == 4
    assert (
        cli_client._EXCEPTION_TO_EXIT_CODE[BuiltinToolGenerationError]
        == exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION
    )
    others = {
        code
        for exc_type, code in cli_client._EXCEPTION_TO_EXIT_CODE.items()
        if exc_type is not BuiltinToolGenerationError
    }
    assert 4 not in others

    def _boom(*args: object, **kwargs: object) -> tuple[int, int]:
        raise BuiltinToolGenerationError("内置工具文件写入失败：模拟磁盘故障")

    monkeypatch.setattr(init_module, "render_templates", _boom)

    code = cli_client.main(["init", str(tmp_path / "ws")])
    captured = capsys.readouterr()

    assert code == 4
    assert "BuiltinToolGenerationError" in captured.err
    assert "下一步" in captured.err
    assert (
        "重装 donkey" in captured.err
        or "重试 init" in captured.err
        or "权限" in captured.err
    )
