"""F001-P4（``cli_version``）黑盒验收脚本 —— 7 个 e2e 场景。

**黑盒约束**：本脚本 MUST NOT import ``donkey.*`` 的业务代码，只以子进程方式
观察退出码、stdout / stderr 与文件系统副作用（spec FR-033）。允许使用**标准库**
``importlib.metadata``（取安装分发元数据值）与 ``tomllib``（读工作树
``pyproject.toml`` 的声明值）。

**被测命令的解析规则**（spec FR-033 / research.md R-16，沿用 F001-P1 / P2 / P3
已确立的口径）：

1. 优先使用 PATH 上的 ``donkey`` 控制台脚本；
2. 使用前 MUST 校验该命令解析到的 ``donkey`` 包安装位置**位于当前工作树内**，
   不匹配时 MUST 视为该命令不可用（避免测到已安装的其它版本或其它工作树）；
3. 不可用时回落到以当前解释器执行模块入口（``python -m donkey``），回落时
   MUST 以**仓库根**为工作目录，MUST 打印一次显式告警而 MUST NOT 静默回落；
4. 两条入口 MUST 产生完全相同的退出码与输出。

**期望值取数（双比对 · research.md R-18）**：本脚本同时读取**两个**来源 ——
① **工作树声明值**（``pyproject.toml`` 的 ``version``）与 ② **安装分发元数据值**
（``importlib.metadata.version("donkey")``）。两者相等（**常规安装形态**）→
期望值 = 二者；两者不等（**陈旧安装形态**）→ 期望值 = **安装分发元数据值**
（spec FR-018），且该不等情形 MUST **显式断言**、MUST NOT 被静默接受。

**时间上限**：单次 ``donkey version`` MUST 在 **5 秒**内返回（spec SC-011）——
每次子进程调用 MUST 计时并在超限时 FAIL，且实测耗时 MUST 被记录（供
quickstart §2 的执行证据链核对）。

**自包含**：本脚本自带一份命令解析辅助函数副本，MUST NOT 抽公共模块、
MUST NOT 改动三个既有 verify 脚本（research.md R-16）。
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

#: 仓库根（由本脚本自身位置向上推导）——回落时的工作目录。
REPO_ROOT = Path(__file__).resolve().parents[3]

#: 单次 ``donkey version`` 的耗时上限（秒）——spec SC-011 / research.md R-17。
_TIME_LIMIT_SECONDS = 5.0

#: 模块入口前缀。
_MODULE_ENTRY = [sys.executable, "-m", "donkey"]

#: 版本值的形态（宪法 §4.5 的 ``vx.y.z`` 记法）。
_VERSION_PATTERN = re.compile(r"v\d+\.\d+\.\d+")

#: 实测耗时记录 —— ``(场景标签, 秒)``，供 quickstart §2 的证据链核对。
ELAPSED_RECORDS: list[tuple[str, float]] = []

_fallback_warned = False


# --- 命令解析（黑盒侧辅助，自包含副本）-------------------------------------------


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
            "[verify_phase_f001_p4] 环境性未验证：控制台脚本不可用"
            "（不存在，或不属于当前工作树），已回落 `python -m donkey`。",
            file=sys.stderr,
        )
    return list(_MODULE_ENTRY), REPO_ROOT


def _run_donkey(
    argv: list[str], cwd: Path, label: str, *args: str
) -> subprocess.CompletedProcess[str]:
    """以子进程执行一次 ``donkey``，并断言耗时不超过 5 秒（spec SC-011）。"""
    started = time.monotonic()
    completed = subprocess.run(
        [*argv, *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=_TIME_LIMIT_SECONDS + 30,
    )
    elapsed = time.monotonic() - started
    ELAPSED_RECORDS.append((label, elapsed))
    assert elapsed <= _TIME_LIMIT_SECONDS, (
        f"donkey version 耗时 {elapsed:.3f}s，超过 {_TIME_LIMIT_SECONDS}s 上限（spec SC-011）"
    )
    return completed


# --- 期望值取数（双比对 · research.md R-18）----------------------------------------


def worktree_declared_version() -> str:
    """工作树声明值 = ``pyproject.toml`` 的 ``version``（标准库 ``tomllib``）。"""
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def installed_metadata_version() -> str:
    """安装分发元数据值 = ``importlib.metadata.version("donkey")``。"""
    return importlib.metadata.version("donkey")


def expected_version_value() -> str:
    """期望的版本展示值（双比对口径 —— spec SC-003 / research.md R-18）。

    - **常规安装形态**（工作树声明值 == 安装元数据值）→ 期望值 = 二者；
    - **陈旧安装形态**（两者不等）→ 期望值 = **安装分发元数据值**（spec FR-018），
      且该不等情形 MUST **显式断言**（此处以显式告警 + 分支断言承载），
      MUST NOT 断言输出 == 工作树声明值或清单 ``donkey_version`` 字段。
    """
    declared = worktree_declared_version()
    installed = installed_metadata_version()
    if declared != installed:
        print(
            "[verify_phase_f001_p4] 陈旧安装形态：工作树声明值 "
            f"{declared!r} != 安装分发元数据值 {installed!r}"
            " → 期望值以分发元数据值为准（spec FR-018）。",
            file=sys.stderr,
        )
        return "v" + installed
    return "v" + declared


# --- 场景 1（US1）-------------------------------------------------------------------


def test_scenario_1_version_command_outputs_one_line(tmp_path: Path) -> None:
    """场景 1 · ``donkey version`` 输出一行裸版本值（spec US1 场景 1 ~ 3）。

    ① 退出码 0、stdout 恰好一行、内容 == 期望值（双比对口径）、stderr 为空；
    ② 连续两次执行 stdout 逐字节相同（spec FR-011）；
    ③ 在**不存在 workspace** 的目录下执行同样成功（spec FR-022）。
    """
    argv, cwd = _resolve_donkey_command()

    # 工作树声明值当前 MUST 为 0.1.0 —— 该断言 MUST NOT 随安装形态漂移
    # （spec SC-003 / research.md R-09 保留半）。
    assert worktree_declared_version() == "0.1.0", (
        "工作树声明的版本（pyproject.toml 的 version）MUST 当前为 0.1.0"
        "（spec SC-003）"
    )

    expected = expected_version_value()

    completed = _run_donkey(argv, cwd, "scenario_1", "version")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    lines = completed.stdout.splitlines()
    assert len(lines) == 1, f"stdout MUST 恰好一行：{completed.stdout!r}"
    assert lines[0] == expected, (
        f"stdout 正文 {lines[0]!r} != 期望值 {expected!r}"
        "（常规安装形态下 = v0.1.0；陈旧安装形态下 = 安装分发元数据值）"
    )
    assert completed.stderr == "", f"成功路径 stderr MUST 为空：{completed.stderr!r}"

    # ② 连续两次执行 → stdout 逐字节相同（spec FR-011）。
    again = _run_donkey(argv, cwd, "scenario_1_repeat", "version")
    assert again.stdout.encode("utf-8") == completed.stdout.encode("utf-8")

    # ③ 当前目录**不存在 workspace** → 同样成功（spec FR-022）。
    in_empty_dir = _run_donkey(argv, tmp_path, "scenario_1_no_workspace", "version")
    assert in_empty_dir.returncode == 0, (
        f"stdout={in_empty_dir.stdout!r} stderr={in_empty_dir.stderr!r}"
    )
    assert in_empty_dir.stdout == completed.stdout


# --- 场景 2（US2）-------------------------------------------------------------------


def test_scenario_2_single_version_value(tmp_path: Path) -> None:
    """场景 2 · 输出里只有**一个**版本值，且与清单字段可逐字节比对。

    ① 版本值恰好出现 1 次、形如 ``^v\\d+\\.\\d+\\.\\d+$``（spec FR-008）；
    ② 去掉 ``v`` 前缀后的取值与**工作区清单**的 ``donkey_version`` 字段逐字节
    一致 —— 该比对的前提是「工作树声明值 == 清单字段」；不成立（**陈旧清单**
    形态）时 MUST **跳过**该比对，改以分发元数据 / 工作树声明值为准
    （spec SC-003 / US2 场景 2）；
    ③ **双比对断言**（spec SC-003 / research.md R-18）。
    """
    argv, cwd = _resolve_donkey_command()

    declared = worktree_declared_version()
    installed = installed_metadata_version()

    completed = _run_donkey(argv, cwd, "scenario_2", "version")
    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    stdout = completed.stdout

    # ① 版本值恰好出现 1 次，且形态合法。
    found = _VERSION_PATTERN.findall(stdout)
    assert len(found) == 1, f"版本值 MUST 恰好出现 1 次：{stdout!r}"
    value = found[0]
    assert re.fullmatch(r"v\d+\.\d+\.\d+", value), value

    # ③ 双比对：两者相等 → 输出底层取值 == 二者；不等（陈旧安装）→ 以元数据
    #    值为准，且该不等情形 MUST 被**显式断言**（spec FR-018 / SC-003）。
    underlying = value.removeprefix("v")
    if declared == installed:
        assert underlying == declared
        assert underlying == installed
    else:
        assert underlying == installed, (
            "陈旧安装形态下输出底层取值 MUST == 安装分发元数据值（spec FR-018）"
        )

    # ② 与工作区清单 ``donkey_version`` 字段的逐字节比对 —— **真黑盒路径**：
    #    子进程 ``donkey init`` 生成清单 → 读其 ``donkey_version`` 字段。
    #    MUST NOT import ``donkey.core.workspace.manifest``（违反 spec FR-033）。
    workspace = tmp_path / "ws"
    init_completed = _run_donkey(argv, cwd, "scenario_2_init", "init", str(workspace))
    assert init_completed.returncode == 0, (
        f"stdout={init_completed.stdout!r} stderr={init_completed.stderr!r}"
    )

    manifest_path = workspace / "manifest.json"
    assert manifest_path.is_file(), manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_version = str(manifest["donkey_version"])

    if declared == manifest_version:
        # 常规安装形态 → 逐字节一致（spec FR-013 / US2 场景 2）。
        assert underlying == manifest_version
    else:
        # 陈旧清单形态 → MUST 跳过该比对（否则是假失败）。
        print(
            "[verify_phase_f001_p4] 陈旧清单形态：工作树声明值 "
            f"{declared!r} != 清单 donkey_version {manifest_version!r}"
            " → 跳过「输出 vs 清单字段」比对（spec SC-003）。",
            file=sys.stderr,
        )
        assert underlying in {declared, installed}


# --- 场景 3（US3）-------------------------------------------------------------------


def test_scenario_3_deterministic_value_without_graph() -> None:
    """场景 3 · 图尚未构建时也给出**确定**的版本值（spec US3 场景 1 / 2）。

    ① 输出恒为 ``resolve_version()`` 的解析结果 —— MUST NOT 是 ``unknown`` /
    ``dev`` / ``v0.0.0`` 一类的值（陈旧安装形态下按 FR-018 以分发元数据为准）；
    ② 输出中**节点级版本信息的出现次数为 0**（spec FR-015 / FR-024）。
    """
    argv, cwd = _resolve_donkey_command()

    completed = _run_donkey(argv, cwd, "scenario_3", "version")
    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    stdout = completed.stdout

    value = stdout.strip()
    assert value == expected_version_value(), value
    assert value not in {"unknown", "dev", "v0.0.0", "0.0.0"}, value
    assert not value.endswith("dev"), value
    assert _VERSION_PATTERN.fullmatch(value), value

    # ② 节点级版本信息（节点 id 清单 / 逐节点版本号）的出现次数为 0 ——
    #    一个版本值 = 一个 ``vx.y.z``；MUST NOT 出现第二个。
    assert len(_VERSION_PATTERN.findall(stdout)) == 1, stdout
    assert len(stdout.splitlines()) == 1, stdout


# --- 场景 4（US4）-------------------------------------------------------------------


def test_scenario_4_both_entrypoints_equivalent() -> None:
    """场景 4 · 控制台脚本与模块入口**完全等价**（spec US4 场景 1 / 2）。

    ① 退出码相同、stdout 逐字节相同、stderr 均为空；
    ② 两条入口下的版本取值分别相等。

    控制台脚本不可用时（解析不到本工作树内的包）MUST **显式**跳过控制台脚本
    一侧并只断言模块入口一侧 —— MUST NOT 因此**假失败**；且 MUST 打印**一次
    显式告警**到 stderr（**非静默跳过**，spec SC-004 的降级条款）。
    """
    _argv, cwd = _resolve_donkey_command()
    console = _resolve_console_script()

    module_completed = _run_donkey(list(_MODULE_ENTRY), cwd, "scenario_4_module", "version")
    assert module_completed.returncode == 0, (
        f"stdout={module_completed.stdout!r} stderr={module_completed.stderr!r}"
    )
    assert module_completed.stderr == "", module_completed.stderr

    if console is None:
        print(
            "[verify_phase_f001_p4] 降级：控制台脚本不可用（不存在，或不属于"
            "当前工作树）→ 只断言模块入口一侧（spec SC-004）。",
            file=sys.stderr,
        )
        assert _VERSION_PATTERN.fullmatch(module_completed.stdout.strip())
        return

    console_completed = _run_donkey([str(console)], cwd, "scenario_4_console", "version")

    assert console_completed.returncode == module_completed.returncode, (
        f"控制台脚本 rc={console_completed.returncode} "
        f"模块入口 rc={module_completed.returncode}"
    )
    assert console_completed.stdout.encode("utf-8") == module_completed.stdout.encode("utf-8")
    assert console_completed.stderr == "", console_completed.stderr
    assert module_completed.stderr == "", module_completed.stderr
    # ② 两条入口下的版本取值分别相等。
    assert console_completed.stdout.strip() == module_completed.stdout.strip()


# --- 场景 5（US5）-------------------------------------------------------------------


def test_scenario_5_usage_errors_exit_1() -> None:
    """场景 5 · 用法错误一律以退出码 **1** 失败（spec US5 场景 1 ~ 4）。

    ① ``--bogus`` → 退出码 1（MUST NOT 为 2）、stdout 为空、stderr 含用法提示；
    ② ``web`` / ``extra`` → 退出码同为 1、stdout 为空；
    ③ ``--help`` → 退出码 0；
    ④ 顶层 ``--version`` → 退出码 1 且不输出任何版本号。

    断言 MUST NOT 依赖报错措辞（实测为「the following arguments are required:
    command」—— ``add_subparsers(dest="command", required=True)`` 的必填校验
    先于未识别参数检查触发，spec FR-038 / SC-014）。
    """
    argv, cwd = _resolve_donkey_command()

    for extra in ("--bogus", "web", "extra"):
        completed = _run_donkey(argv, cwd, f"scenario_5_{extra}", "version", extra)

        assert completed.returncode == 1, (
            f"{extra} → rc={completed.returncode}（MUST NOT 为 2）"
            f" stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
        assert completed.stdout == "", f"{extra} 的 stdout MUST 为空"
        assert not _VERSION_PATTERN.search(completed.stdout), extra
        assert completed.stderr != "", f"{extra} 的 stderr MUST 含用法提示"
        assert "usage:" in completed.stderr, completed.stderr

    # ③ 帮助请求不是用法错误 → 退出码 0。
    helped = _run_donkey(argv, cwd, "scenario_5_help", "version", "--help")
    assert helped.returncode == 0, (
        f"stdout={helped.stdout!r} stderr={helped.stderr!r}"
    )

    # ④ 顶层不提供 --version → 退出码 1，且不输出任何版本号。
    top_level = _run_donkey(argv, cwd, "scenario_5_top_level", "--version")
    assert top_level.returncode == 1, (
        f"stdout={top_level.stdout!r} stderr={top_level.stderr!r}"
    )
    assert top_level.stdout == ""
    assert not _VERSION_PATTERN.search(top_level.stdout)
    assert not _VERSION_PATTERN.search(top_level.stderr)

    # ⑤ 顶层 --help 的子命令列表 MUST 出现 version 条目（spec FR-003 / SC-013）。
    top_help = _run_donkey(argv, cwd, "scenario_5_top_help", "--help")
    assert top_help.returncode == 0, (
        f"stdout={top_help.stdout!r} stderr={top_help.stderr!r}"
    )
    assert "version" in top_help.stdout
    assert "init" in top_help.stdout


# --- 场景 6（US6）-------------------------------------------------------------------


def declared_package_version() -> str:
    """包内 ``__version__`` 常量（回退源）—— 从 ``donkey/__init__.py`` **文本**读取。

    只读文件、MUST NOT import ``donkey.*`` 业务代码（spec FR-033）。
    """
    text = (REPO_ROOT / "donkey" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match is not None, "donkey/__init__.py 中未找到 __version__ 常量"
    return match.group(1)


def test_scenario_6_version_without_distribution_metadata(tmp_path: Path) -> None:
    """场景 6 · 取不到安装分发元数据时仍给出**确定**的版本（spec US6 场景 1 / 2）。

    **真黑盒**复现"分发元数据不可得"：把工作树的 ``donkey/`` **包目录**复制到
    临时目录（副本**同级没有** ``*.egg-info``），在该副本根执行
    ``python -S -m donkey version``。

    ``-S``（屏蔽 site-packages）**不可省** —— 实测：已安装 donkey 的环境里
    site-packages 的 ``donkey-*.dist-info`` 仍会被 ``importlib.metadata`` 发现，
    仅靠"副本同级没有 ``*.egg-info``"不足以复现回退分支
    （research.md R-10 的修正记录）。

    MUST NOT 用 ``PYTHONPATH`` 指向仓库根（实测无效：仓库根的
    ``donkey.egg-info/`` 会随之被发现、元数据照样命中）；MUST NOT monkeypatch /
    import ``donkey.*`` 业务代码（spec FR-033）。
    """
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    shutil.copytree(
        REPO_ROOT / "donkey",
        isolated / "donkey",
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    # 先断言分发元数据**确实不可得** —— 否则本场景没有真正覆盖回退分支
    # （spec SC-007）。
    probe = subprocess.run(
        [sys.executable, "-S", "-c", "import importlib.metadata as md; md.version('donkey')"],
        capture_output=True,
        text=True,
        cwd=str(isolated),
        timeout=60,
    )
    assert probe.returncode != 0, f"副本内竟能取到分发元数据：{probe.stdout!r}"
    assert "PackageNotFoundError" in probe.stderr, probe.stderr

    # ① 退出码 0、stdout 仍是一个**确定可解析**的版本值。
    completed = _run_donkey(
        [sys.executable, "-S", "-m", "donkey"], isolated, "scenario_6", "version"
    )
    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    value = completed.stdout.strip()
    assert value != "", "回退路径 MUST NOT 输出空值"
    assert _VERSION_PATTERN.fullmatch(value), value

    # ② 版本取值**不依赖**安装形态 —— 取不到元数据时 MUST NOT 影响版本值：
    #    回退源是包自身的 ``__version__`` 常量（spec FR-017）。
    assert value == "v" + declared_package_version(), value


# --- 场景 7（US7）-------------------------------------------------------------------


def tree_snapshot(root: Path) -> dict[str, str]:
    """目录树指纹 —— 相对路径 → 类型 / 大小 / 内容摘要。

    用于断言 ``donkey version`` 的文件系统副作用数为 **0**（spec FR-022）。
    """
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[rel] = f"symlink:{os.readlink(path)}"
        elif path.is_dir():
            snapshot[rel] = "dir"
        else:
            payload = path.read_bytes()
            snapshot[rel] = f"file:{len(payload)}:{hashlib.sha256(payload).hexdigest()}"
    return snapshot


def test_scenario_7_read_only_no_side_effects(tmp_path: Path) -> None:
    """场景 7 · 查询版本**一个字节都不写**（spec US7 场景 1 / 2）。

    ① 含若干文件的目录树在执行前后，文件数 / 目录数 / 各文件内容指纹**全部
    不变**（副作用数 = 0）；
    ② 工作区清单文件**未被创建、未被修改**。

    补充（spec FR-022 / Edge Cases「只读性与作用域类」）：命令 MUST 在**工作区
    不存在**（含 manifest 缺失或非法）与**只读文件系统**下同样成功。
    """
    argv, _cwd = _resolve_donkey_command()

    tree = tmp_path / "tree"
    (tree / "sub").mkdir(parents=True)
    (tree / "a.txt").write_text("alpha\n", encoding="utf-8")
    (tree / "sub" / "b.txt").write_text("beta\n", encoding="utf-8")

    before = tree_snapshot(tree)
    completed = _run_donkey(argv, tree, "scenario_7", "version")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    after = tree_snapshot(tree)

    # ① 文件数 / 目录数 / 内容指纹全部不变。
    assert after == before, "目录树 MUST 零变化（文件数 / 目录数 / 内容指纹）"
    # ② 工作区清单文件未被创建、未被修改。
    assert not (tree / "manifest.json").exists()

    # 补充 · 工作区**损坏**（manifest 非法）→ 同样成功（MUST NOT 读取工作区）。
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "manifest.json").write_text("{ 不是合法 JSON", encoding="utf-8")
    broken_completed = _run_donkey(argv, broken, "scenario_7_broken", "version")
    assert broken_completed.returncode == 0, (
        f"stdout={broken_completed.stdout!r} stderr={broken_completed.stderr!r}"
    )

    # 补充 · 只读文件系统 → 同样成功（退出码 0，不因不可写而失败）。
    readonly = tmp_path / "readonly"
    readonly.mkdir()
    (readonly / "keep.txt").write_text("keep\n", encoding="utf-8")
    os.chmod(readonly, 0o555)
    try:
        readonly_completed = _run_donkey(argv, readonly, "scenario_7_readonly", "version")
        assert readonly_completed.returncode == 0, (
            f"stdout={readonly_completed.stdout!r} stderr={readonly_completed.stderr!r}"
        )
    finally:
        os.chmod(readonly, 0o755)
