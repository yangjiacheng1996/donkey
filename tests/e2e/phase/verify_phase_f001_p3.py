"""F001-P3（``builtin_tools``）黑盒验收脚本 —— 16 个 e2e 场景。

**黑盒约束**：本脚本 MUST NOT import ``donkey.*`` 的业务代码，只以子进程方式
观察退出码、stdout / stderr 与文件系统副作用（spec FR-066）。

**被测命令的解析规则**（spec FR-064，沿用 F001-P1 / F001-P2 已确立的口径）：

1. 优先使用 PATH 上的 ``donkey`` 控制台脚本；
2. 使用前 MUST 校验该命令解析到的 ``donkey`` 包安装位置**位于当前工作树内**，
   不匹配时 MUST 视为该命令不可用（避免测到已安装的其它版本或其它工作树）；
3. 不可用时回落到以当前解释器执行模块入口（``python -m donkey``），回落时
   MUST 以**仓库根**为工作目录，MUST 打印一次显式告警而 MUST NOT 静默回落；
4. 两条入口 MUST 产生完全相同的退出码与文件系统副作用。

**时间上限**：单次 ``donkey init`` MUST 在 10 秒内返回（spec SC-019）。

**模块缓存陷阱**：凡需导入工作区产物的场景，MUST 用**独立子进程** ——
``sys.modules`` 按模块名缓存，在测试进程内导入会让后续场景测到**第一个**
工作区的产物（验收假绿）。子进程 MUST 用 ``python -c`` —— ``-c`` 才把当前
工作目录放进导入路径（research.md R-20）。
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

#: 仓库根（由本脚本自身位置向上推导）——回落时的工作目录。
REPO_ROOT = Path(__file__).resolve().parents[3]

#: 单次 ``donkey init`` 的耗时上限（秒）——spec SC-019。
_TIME_LIMIT_SECONDS = 10.0

#: 模块入口前缀。
_MODULE_ENTRY = [sys.executable, "-m", "donkey"]

#: ``tools/`` 下 MUST 齐备的 6 个文件（spec US1 场景 1）。
BUILTIN_TOOL_FILES = (
    "__init__.py",
    "changes.py",
    "commandline.py",
    "filesystem.py",
    "webfetch.py",
    "README.md",
)

_fallback_warned = False


def _is_within(child: Path, parent: Path) -> bool:
    """``child`` 是否位于 ``parent`` 之内（含相等）。"""
    return child == parent or parent in child.parents


def _console_script_package_dir(script: Path) -> Path | None:
    """解析控制台脚本所绑定的解释器，并定位它会 import 的 ``donkey`` 包目录。"""
    try:
        text = script.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    lines = text.splitlines()
    if not lines or not lines[0].startswith("#!"):
        return None

    parts = shlex.split(lines[0][2:].strip())
    if parts and os.path.basename(parts[0]) == "env":
        parts = parts[1:]
    if not parts:
        return None

    probe = "import donkey, pathlib;print(pathlib.Path(donkey.__file__).resolve().parent)"
    try:
        completed = subprocess.run(
            # ``-P``：不把工作目录前置到 sys.path —— 探测的必须是该解释器
            # 自身环境中的 donkey 安装位置，而不是当前目录下的同名目录。
            [parts[0], "-P", "-c", probe],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO_ROOT),
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if completed.returncode != 0:
        return None
    output = completed.stdout.strip()
    if not output:
        return None
    return Path(output)


def _console_script_candidates() -> list[Path]:
    """列出候选的 ``donkey`` 控制台脚本。"""
    candidates: list[Path] = []

    found = shutil.which("donkey")
    if found:
        candidates.append(Path(found))

    sibling = Path(sys.executable).with_name("donkey")
    if sibling.is_file() and sibling not in candidates:
        candidates.append(sibling)

    return candidates


def _resolve_console_script() -> Path | None:
    """返回属于当前工作树的 ``donkey`` 控制台脚本；不可用时返回 ``None``。"""
    for candidate in _console_script_candidates():
        package_dir = _console_script_package_dir(candidate)
        if package_dir is None:
            continue
        if _is_within(package_dir, REPO_ROOT):
            return candidate
    return None


def _resolve_donkey_command() -> tuple[list[str], Path]:
    """解析被测命令，返回 ``(命令前缀, 工作目录)``。"""
    global _fallback_warned

    script = _resolve_console_script()
    if script is not None:
        return [str(script)], REPO_ROOT

    if not _fallback_warned:
        _fallback_warned = True
        print(
            "[verify_phase_f001_p3] 环境性未验证：控制台脚本不可用"
            "（不存在，或不属于当前工作树），已回落 `python -m donkey`。",
            file=sys.stderr,
        )
    return list(_MODULE_ENTRY), REPO_ROOT


def _run_donkey(argv: list[str], cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """以子进程执行一次 ``donkey``，并断言耗时不超过 10 秒（spec SC-019）。"""
    started = time.monotonic()
    completed = subprocess.run(
        [*argv, *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=_TIME_LIMIT_SECONDS + 30,
    )
    elapsed = time.monotonic() - started
    assert elapsed <= _TIME_LIMIT_SECONDS, (
        f"donkey init 耗时 {elapsed:.3f}s，超过 {_TIME_LIMIT_SECONDS}s 上限（spec SC-019）"
    )
    return completed


def _init(
    argv: list[str], cwd: Path, target: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    """执行一次 ``donkey init <target>``。"""
    return _run_donkey(argv, cwd, "init", str(target), *extra)


def _run_in_workspace(
    workspace: Path, snippet: str
) -> subprocess.CompletedProcess[str]:
    """在工作区目录内以**独立子进程**执行一段 Python 代码。

    ``-c`` 使当前工作目录进入导入路径 —— 工作区的 ``tools`` 包因此可被导入。
    """
    return subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=120,
    )


# --- 场景 1 ~ 5（US1 ~ US5）-------------------------------------------------------


def test_scenario_1_builtin_tools_present(tmp_path: Path) -> None:
    """场景 1 · init 后 ``tools/`` 下 6 个文件齐备（spec US1 场景 1）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert "templates=54 created=48 skipped=0" in completed.stdout
    for name in BUILTIN_TOOL_FILES:
        assert (ws / "tools" / name).is_file(), name


def test_scenario_2_tools_importable_with_docstrings(tmp_path: Path) -> None:
    """场景 2 · 9 个工具可 import，且每个 ``@tool`` 的说明文字长度 > 20。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
from tools.filesystem import (
    read_file, write_file, copy_file, move_file, delete_file, list_dir, stat,
)
from tools.commandline import run_shell
from tools.webfetch import fetch_url

tools = [
    read_file, write_file, copy_file, move_file, delete_file, list_dir, stat,
    run_shell, fetch_url,
]
print(len(tools), min(len(t.description) for t in tools))
""",
    )

    assert completed.returncode == 0, completed.stderr
    count, shortest = completed.stdout.split()
    assert int(count) == 9
    assert int(shortest) > 20


def test_scenario_3_run_shell_echo(tmp_path: Path) -> None:
    """场景 3 · ``run_shell("echo hello")`` 返回可解析 JSON（spec US3）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import json
from tools.commandline import run_shell
result = json.loads(run_shell.invoke({'command': 'echo hello'}))
print(json.dumps({
    'stdout': result['stdout'],
    'returncode': result['returncode'],
    'timed_out': result['timed_out'],
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert "hello" in result["stdout"]
    assert result["returncode"] == 0
    assert result["timed_out"] is False


def test_scenario_4_filesystem_seven_actions(tmp_path: Path) -> None:
    """场景 4 · 文件工具七动作的连续操作（spec US4）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import json
from tools.filesystem import (
    read_file, write_file, copy_file, move_file, delete_file, list_dir, stat,
)

write_file.invoke({'path': 'demo.txt', 'content': 'hello\n'})
read_back = read_file.invoke({'path': 'demo.txt'})
copy_file.invoke({'src': 'demo.txt', 'dst': 'copy.txt'})
names = list_dir.invoke({'path': '.'})
info = stat.invoke({'path': 'demo.txt', 'with_hash': True})
move_file.invoke({'src': 'copy.txt', 'dst': 'moved.txt'})
deleted = json.loads(delete_file.invoke({'path': 'moved.txt'}))

print(json.dumps({
    'read': read_back,
    'has_copy': 'copy.txt' in names,
    'is_file': info['is_file'],
    'has_hash': info['sha256'].startswith('sha256:'),
    'action': deleted['action'],
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert "hello" in result["read"]
    assert result["has_copy"] is True
    assert result["is_file"] is True
    assert result["has_hash"] is True
    assert result["action"] == "delete"
    assert not (ws / "moved.txt").exists()


def test_scenario_5_webfetch_with_mock(tmp_path: Path) -> None:
    """场景 5 · 网络工具 HTTP mock —— mock 与 import 同处一个子进程。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import httpx


def fake_send(self, request, **kwargs):
    return httpx.Response(200, text='mocked body', request=request)


httpx.Client.send = fake_send

import json
from tools.webfetch import fetch_url

result = json.loads(fetch_url.invoke({'url': 'https://example.com'}))
print(json.dumps({
    'status_code': result['status_code'],
    'body': result['body'],
    'keys': sorted(result),
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert result["status_code"] == 200
    assert "mocked body" in result["body"]
    assert result["keys"] == ["body", "headers", "status_code", "url"]


# --- 场景 6 ~ 10（US6 ~ US10）-----------------------------------------------------


def test_scenario_6_skill_three_layers(tmp_path: Path) -> None:
    """场景 6 · 示例 Skill 三层齐备（spec US6）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    skill = (ws / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\n")
    frontmatter = skill.split("---")[1]
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line and not line.strip().startswith("#")
    }
    assert keys == {"name", "description"}
    assert skill.split("---", 2)[2].strip()

    for name in ("reference", "scripts", "templates"):
        directory = ws / "skills" / "example" / name
        assert directory.is_dir(), name
        assert [p for p in directory.iterdir() if p.is_file()], name


def test_scenario_7_no_search_capability_in_builtin_tools(tmp_path: Path) -> None:
    """场景 7 · 3 个内置工具文件 MUST NOT 含"按名找 / 按内容找"（spec US7）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    for name in ("filesystem.py", "commandline.py", "webfetch.py"):
        text = (ws / "tools" / name).read_text(encoding="utf-8")
        assert "glob_search" not in text, name
        assert "grep_search" not in text, name


def test_scenario_8_removed_file_is_replenished(tmp_path: Path) -> None:
    """场景 8 · ``rm tools/filesystem.py`` 后 init 补齐（spec US8）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "tools" / "filesystem.py").unlink()
    assert not (ws / "tools" / "filesystem.py").exists()

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert (ws / "tools" / "filesystem.py").is_file()
    assert "templates=54 created=1 skipped=47" in completed.stdout


def test_scenario_9_force_preserves_user_tools(tmp_path: Path) -> None:
    """场景 9 · ``--force`` 不动用户自写工具，且内置工具恢复出厂（spec US9）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    custom = ws / "tools" / "my_custom_tool.py"
    custom.write_text("# 我自己的工具\n", encoding="utf-8")
    (ws / "tools" / "filesystem.py").write_text("# 改坏了\n", encoding="utf-8")

    completed = _init(argv, cwd, ws, "--force")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert custom.is_file()
    assert custom.read_text(encoding="utf-8") == "# 我自己的工具\n"
    assert "# 改坏了" not in (ws / "tools" / "filesystem.py").read_text(encoding="utf-8")
    assert "templates=54 created=47 skipped=1" in completed.stdout


def test_scenario_10_all_tools_callable_in_subprocess(tmp_path: Path) -> None:
    """场景 10 · 9 个工具函数在独立子进程中全部可调用（spec US10）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import httpx


def fake_send(self, request, **kwargs):
    return httpx.Response(200, text='mocked body', request=request)


httpx.Client.send = fake_send

from tools.filesystem import (
    read_file, write_file, copy_file, move_file, delete_file, list_dir, stat,
)
from tools.commandline import run_shell
from tools.webfetch import fetch_url

results = []
results.append(read_file.invoke({'path': 'instruction.md'}))
results.append(write_file.invoke({'path': 'probe.txt', 'content': 'x\n'}))
results.append(copy_file.invoke({'src': 'probe.txt', 'dst': 'probe-copy.txt'}))
results.append(move_file.invoke({'src': 'probe-copy.txt', 'dst': 'probe-moved.txt'}))
results.append(list_dir.invoke({'path': '.'}))
results.append(stat.invoke({'path': 'probe.txt'}))
results.append(delete_file.invoke({'path': 'probe-moved.txt'}))
results.append(run_shell.invoke({'command': 'echo e2e'}))
results.append(fetch_url.invoke({'url': 'https://example.com'}))
print('CALLABLE', len(results))
""",
    )

    assert completed.returncode == 0, completed.stderr
    assert "CALLABLE 9" in completed.stdout


# --- 场景 11 ~ 15（US11 ~ US15）---------------------------------------------------


def test_scenario_11_init_does_no_static_check(tmp_path: Path) -> None:
    """场景 11 · init 不做 F002 静态检查（spec US11）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "tools" / "filesystem.py").write_text("这不是合法的 Python !!!", encoding="utf-8")

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )


def test_scenario_12_write_file_returns_change_record(tmp_path: Path) -> None:
    """场景 12 · 写文件带回统一变更记录（spec US12）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import json
from tools.filesystem import write_file

first = json.loads(write_file.invoke({'path': 'demo.txt', 'content': 'a\nb\n'}))
second = json.loads(write_file.invoke({'path': 'demo.txt', 'content': 'a\nc\n'}))
print(json.dumps({
    'first_action': first['action'],
    'second_action': second['action'],
    'previous_hash': second['change']['previous_hash'],
    'first_new_hash': first['change']['new_hash'],
    'diff': second['change']['unified_diff'],
    'version': second['change']['version'],
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert result["first_action"] == "create"
    assert result["second_action"] == "update"
    assert result["previous_hash"] == result["first_new_hash"]
    assert "-b" in result["diff"]
    assert "+c" in result["diff"]
    assert result["version"] == 1


def test_scenario_13_dry_run_has_no_disk_side_effect(tmp_path: Path) -> None:
    """场景 13 · 预览模式零磁盘副作用（spec US13）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "demo.txt").write_text("old\n", encoding="utf-8")

    completed = _run_in_workspace(
        ws,
        r"""
import json
from tools.filesystem import write_file

result = json.loads(
    write_file.invoke({'path': 'demo.txt', 'content': 'new\n', 'dry_run': True})
)
print(json.dumps({
    'applied': result['applied'],
    'change_applied': result['change']['applied'],
    'diff': result['change']['unified_diff'],
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert result["applied"] is False
    assert result["change_applied"] is False
    assert "-old" in result["diff"]
    assert (ws / "demo.txt").read_text(encoding="utf-8") == "old\n"
    assert not list(ws.glob(".*.donkey-tmp"))


def test_scenario_14_failed_write_keeps_old_content(tmp_path: Path) -> None:
    """场景 14 · 写失败时旧内容完好且无临时文件残留（spec US14）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "blocker").write_text("原内容", encoding="utf-8")

    completed = _run_in_workspace(
        ws,
        r"""
from tools.filesystem import write_file

try:
    write_file.invoke({'path': 'blocker/child.txt', 'content': 'x\n'})
    print('NO_ERROR')
except Exception as exc:
    print('ERROR', type(exc).__name__)
""",
    )

    assert completed.returncode == 0, completed.stderr
    assert "ERROR" in completed.stdout
    assert (ws / "blocker").read_text(encoding="utf-8") == "原内容"
    assert not list(ws.glob(".*.donkey-tmp"))


def test_scenario_15_delete_returns_change_record(tmp_path: Path) -> None:
    """场景 15 · 删除带回变更记录，契约版本冻结为 1（spec US15）。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    completed = _run_in_workspace(
        ws,
        r"""
import json
from tools.filesystem import write_file, delete_file
from tools.changes import CHANGE_RECORD_VERSION

write_file.invoke({'path': 'demo.txt', 'content': 'payload\n'})
result = json.loads(delete_file.invoke({'path': 'demo.txt'}))
print(json.dumps({
    'action': result['action'],
    'type': result['type'],
    'previous_hash': result['change']['previous_hash'],
    'new_hash': result['change']['new_hash'],
    'version': CHANGE_RECORD_VERSION,
}))
""",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert result["action"] == "delete"
    assert result["type"] == "file"
    assert result["previous_hash"]
    assert result["new_hash"] is None
    assert result["version"] == 1
    assert not (ws / "demo.txt").exists()


# --- 场景 16（CI 交付检查 —— 非 User Story）----------------------------------------


def test_scenario_16_ci_workflow_delivered() -> None:
    """场景 16 · CI 工作流文件已交付且含四类关键命令（spec FR-065）。

    宪法 §6.3 临时例外 E-01 的到期时间是"F001-P3 结束前" —— 本断言即其闭合点。
    """
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"

    assert ci_file.is_file(), "CI 工作流文件缺失（宪法 §6.3 例外 E-01 已到期）"
    content = ci_file.read_text(encoding="utf-8")

    for command in (
        "pytest tests/",
        "--cov=donkey.core",
        "--cov-fail-under=80",
        "ruff check",
        "mypy",
    ):
        assert command in content, command
