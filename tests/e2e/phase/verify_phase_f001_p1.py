"""F001-P1（``cli_validation``）黑盒验收脚本 —— 7 个 e2e 场景。

**黑盒约束**：本脚本 MUST NOT import ``donkey.*`` 的业务代码，只以子进程方式
观察退出码、stdout / stderr 与文件系统副作用（spec FR-025）。

**被测命令的解析规则**（spec FR-025）：

1. 优先使用 PATH 上的 ``donkey`` 控制台脚本；
2. 使用前 MUST 校验该命令解析到的 ``donkey`` 包安装位置**位于当前工作树内**，
   不匹配时 MUST 视为该命令不可用（避免测到已安装的其它版本或其它工作树）；
3. 不可用时回落到以当前解释器执行模块入口（``python -m donkey``），回落时
   MUST 以**仓库根**为工作目录，MUST 打印一次显式告警而 MUST NOT 静默回落；
4. 两条入口 MUST 产生完全相同的退出码与文件系统副作用。
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

#: 仓库根（由本脚本自身位置向上推导）——回落时的工作目录。
REPO_ROOT = Path(__file__).resolve().parents[3]

#: 单次 ``donkey init`` 的耗时上限（秒）——spec SC-013。
_TIME_LIMIT_SECONDS = 10.0

#: 模块入口前缀。
_MODULE_ENTRY = [sys.executable, "-m", "donkey"]

_fallback_warned = False


def _is_within(child: Path, parent: Path) -> bool:
    """``child`` 是否位于 ``parent`` 之内（含相等）。"""
    return child == parent or parent in child.parents


def _console_script_package_dir(script: Path) -> Path | None:
    """解析控制台脚本所绑定的解释器，并定位它会 import 的 ``donkey`` 包目录。

    返回包目录（``donkey/__init__.py`` 所在目录），无法解析时返回 ``None``。
    """
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

    probe = (
        "import donkey, pathlib;"
        "print(pathlib.Path(donkey.__file__).resolve().parent)"
    )
    try:
        completed = subprocess.run(
            # ``-P``：不把工作目录前置到 sys.path——探测的必须是该解释器
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
    """列出候选的 ``donkey`` 控制台脚本。

    先取 PATH 上的 ``donkey``；PATH 上没有时，再取当前解释器同目录下的
    ``donkey``（pip 把控制台脚本装在解释器旁边）——两者都 MUST 通过
    "当前工作树归属"校验才会被采用。
    """
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
            "[verify_phase_f001_p1] 环境性未验证：控制台脚本不可用"
            "（不存在，或不属于当前工作树），已回落 `python -m donkey`。",
            file=sys.stderr,
        )
    return list(_MODULE_ENTRY), REPO_ROOT


def _run_donkey(argv: list[str], cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """以子进程执行一次 ``donkey``，并断言耗时不超过 10 秒（spec SC-013）。"""
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
        f"donkey init 耗时 {elapsed:.3f}s，超过 {_TIME_LIMIT_SECONDS}s 上限（spec SC-013）"
    )
    return completed


def test_scenario_1_new_workspace(tmp_path: Path) -> None:
    """场景 1：全新创建 —— 退出码 0 + 目录已创建 + 双入口逐字一致。"""
    ws = tmp_path / "ws"
    argv, cwd = _resolve_donkey_command()

    completed = _run_donkey(argv, cwd, "init", str(ws))

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert ws.is_dir()
    assert f"workspace={ws.resolve()}" in completed.stdout
    assert "name=ws" in completed.stdout

    # 双入口对比：控制台脚本 vs 模块入口（spec FR-023）。
    console_script = _resolve_console_script()
    if console_script is None:
        print(
            "[verify_phase_f001_p1] 环境性未验证：控制台脚本不可用，"
            "跳过双入口对比断言（非静默跳过）。",
            file=sys.stderr,
        )
    else:
        console_argv = [str(console_script)]
        via_console = _run_donkey(console_argv, cwd, "init", str(ws))
        via_module = _run_donkey(list(_MODULE_ENTRY), cwd, "init", str(ws))

        assert via_console.returncode == via_module.returncode
        assert via_console.stdout == via_module.stdout

        # stderr usage 提示逐字相同（两条入口的 prog 均须为 "donkey"）。
        usage_console = _run_donkey(console_argv, cwd, "init")
        usage_module = _run_donkey(list(_MODULE_ENTRY), cwd, "init")

        assert usage_console.returncode == 1
        assert usage_module.returncode == 1
        assert usage_console.stderr == usage_module.stderr
        assert "usage:" in usage_console.stderr


def test_scenario_2_path_not_found(tmp_path: Path) -> None:
    """场景 2：路径类失败 —— 退出码 1 + 错误标识 + 下一步 + 不建任何目录。"""
    argv, cwd = _resolve_donkey_command()

    missing_parent = tmp_path / "missing"
    target = missing_parent / "ws"

    completed = _run_donkey(argv, cwd, "init", str(target))

    assert completed.returncode == 1, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    stderr = completed.stderr
    assert "PathNotFoundError" in stderr or "父目录不存在" in stderr
    # 一条用户可执行的下一步（建目录 / 换路径）。
    assert "建目录" in stderr or "换路径" in stderr
    # stderr 首行 MUST 以 "[donkey init] 失败：" 开头。
    assert stderr.splitlines()[0].startswith("[donkey init] 失败：")
    # 不产生任何新建目录（含缺失的父目录）。
    assert not missing_parent.exists()
    assert not target.exists()

    # 根目录不是合法 workspace 根 → 退出码 1，且根目录下不出现任何新建内容。
    root_entries_before = set(os.listdir("/"))
    root_completed = _run_donkey(argv, cwd, "init", "/")

    assert root_completed.returncode == 1
    assert set(os.listdir("/")) == root_entries_before


def test_scenario_3_permission_denied(tmp_path: Path) -> None:
    """场景 3：权限类失败 —— 退出码 2 + 权限标识 + 种类/路径 + 下一步。"""
    argv, cwd = _resolve_donkey_command()

    readonly_parent = tmp_path / "ro"
    readonly_parent.mkdir()
    target = readonly_parent / "ws"

    try:
        os.chmod(readonly_parent, 0o555)

        completed = _run_donkey(argv, cwd, "init", str(target))

        assert completed.returncode == 2, (
            f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
        stderr = completed.stderr
        assert "PathPermissionError" in stderr or "权限" in stderr
        # 缺失的权限种类 + 对应路径。
        assert "写权限" in stderr
        assert str(readonly_parent) in stderr
        # 一条用户可执行的下一步（调整权限）。
        assert "调整权限" in stderr
        assert stderr.splitlines()[0].startswith("[donkey init] 失败：")
        # 不创建任何目录。
        assert not target.exists()
    finally:
        os.chmod(readonly_parent, 0o755)


def test_scenario_4_idempotent_no_force(tmp_path: Path) -> None:
    """场景 4：幂等 —— 已存在 workspace 重复执行不报错、不破坏内容。"""
    argv, cwd = _resolve_donkey_command()

    ws = tmp_path / "ws"
    ws.mkdir()
    user_file = ws / "user.txt"
    user_file.write_text("user content", encoding="utf-8")
    before_stat = user_file.stat()

    first = _run_donkey(argv, cwd, "init", str(ws))
    second = _run_donkey(argv, cwd, "init", str(ws))

    assert first.returncode == 0
    assert second.returncode == 0
    # MUST NOT 出现"已存在"类错误。
    assert "已存在" not in first.stderr
    assert "已存在" not in second.stderr
    # 已有用户文件的内容与 mtime 在两次执行之间保持不变（spec SC-005）。
    assert user_file.read_text(encoding="utf-8") == "user content"
    after_stat = user_file.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_scenario_5_force_no_reset_yet(tmp_path: Path) -> None:
    """场景 5：``--force`` 被记录并回显，但本阶段不重置、不删除任何内容。"""
    argv, cwd = _resolve_donkey_command()

    ws = tmp_path / "ws"
    ws.mkdir()
    user_file = ws / "user.txt"
    user_file.write_text("user content", encoding="utf-8")
    before_stat = user_file.stat()

    completed = _run_donkey(argv, cwd, "init", str(ws), "--force")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert "force=true" in completed.stdout
    # 已有内容未被删除或覆盖。
    assert user_file.read_text(encoding="utf-8") == "user content"
    assert user_file.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert sorted(p.name for p in ws.iterdir()) == ["user.txt"]


def test_scenario_6_p1_no_template_rendering(tmp_path: Path) -> None:
    """场景 6：范围边界 —— 只建根目录，不加载清单、不生成任何模板内容。"""
    argv, cwd = _resolve_donkey_command()

    ws = tmp_path / "ws"

    completed = _run_donkey(argv, cwd, "init", str(ws))

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert ws.is_dir()
    # 模板相关计数明确为 0（spec FR-020 / US6 场景 3）。
    assert "templates=0 created=0 skipped=0" in completed.stdout
    # 目标目录内 MUST 无任何文件（宪法 N-01：workspace 内不出现 Python 入口文件）。
    assert list(ws.iterdir()) == []


def test_scenario_7_name_derived_from_path(tmp_path: Path) -> None:
    """场景 7：名称派生 —— 名称 = 路径末段；命令行不接受独立命名参数。"""
    argv, cwd = _resolve_donkey_command()

    ws = tmp_path / "my-agent"

    completed = _run_donkey(argv, cwd, "init", str(ws))

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert "name=my-agent" in completed.stdout
    assert f"workspace={ws.resolve()}" in completed.stdout

    # 误传命名类参数 → 退出码 1（不是 argparse 默认的 2），stderr 含用法提示。
    misuse = _run_donkey(argv, cwd, "init", str(ws), "--name", "alice")

    assert misuse.returncode == 1
    assert "usage:" in misuse.stderr

    # 末段名含空格 / Unicode → 退出码 0，名称原样保留。
    unicode_ws = tmp_path / "我的 工作区"

    unicode_completed = _run_donkey(argv, cwd, "init", str(unicode_ws))

    assert unicode_completed.returncode == 0, (
        f"stdout={unicode_completed.stdout!r} stderr={unicode_completed.stderr!r}"
    )
    assert "name=我的 工作区" in unicode_completed.stdout
