"""F001-P2（``template_skeleton``）黑盒验收脚本 —— 14 个 e2e 场景。

**黑盒约束**：本脚本 MUST NOT import ``donkey.*`` 的业务代码，只以子进程方式
观察退出码、stdout / stderr 与文件系统副作用（spec FR-060）。

**被测命令的解析规则**（spec FR-060，沿用 F001-P1 已确立的口径）：

1. 优先使用 PATH 上的 ``donkey`` 控制台脚本；
2. 使用前 MUST 校验该命令解析到的 ``donkey`` 包安装位置**位于当前工作树内**，
   不匹配时 MUST 视为该命令不可用（避免测到已安装的其它版本或其它工作树）；
3. 不可用时回落到以当前解释器执行模块入口（``python -m donkey``），回落时
   MUST 以**仓库根**为工作目录，MUST 打印一次显式告警而 MUST NOT 静默回落；
4. 两条入口 MUST 产生完全相同的退出码与文件系统副作用。

**时间上限**：单次 ``donkey init`` MUST 在 10 秒内返回（spec SC-012）。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
import tomllib
from pathlib import Path

#: 仓库根（由本脚本自身位置向上推导）——回落时的工作目录。
REPO_ROOT = Path(__file__).resolve().parents[3]

#: 单次 ``donkey init`` 的耗时上限（秒）——spec SC-012。
_TIME_LIMIT_SECONDS = 10.0

#: 模块入口前缀。
_MODULE_ENTRY = [sys.executable, "-m", "donkey"]

#: v1 白名单内的 26 家供应商 id（黑盒脚本 MUST NOT import 业务代码，故在此显式列出）。
PROVIDER_IDS = [
    "openai",
    "anthropic",
    "google",
    "ollama",
    "xai",
    "mistral",
    "qwen",
    "deepseek",
    "doubao",
    "kimi",
    "zhipu",
    "minimax",
    "tencent",
    "xiaomi",
    "stepfun",
    "openai-compatible",
    "meta",
    "bedrock",
    "groq",
    "fireworks",
    "together",
    "cohere",
    "perplexity",
    "databricks",
    "cerebras",
    "openrouter",
]

#: 五个必填目录 + 其子目录（spec §2.6）。
REQUIRED_DIRECTORIES = ("tools", "mcp", "skills", "memory", "providers")

#: 必填文件（spec US1 场景 1）。
REQUIRED_FILES = (
    "instruction.md",
    "README.md",
    ".gitignore",
    "providers/default.toml",
    "providers/README.md",
    "mcp/mcp.json",
    "mcp/README.md",
    "skills/README.md",
    "skills/example/SKILL.md",
    "memory/README.md",
    "tools/README.md",
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
            "[verify_phase_f001_p2] 环境性未验证：控制台脚本不可用"
            "（不存在，或不属于当前工作树），已回落 `python -m donkey`。",
            file=sys.stderr,
        )
    return list(_MODULE_ENTRY), REPO_ROOT


def _run_donkey(argv: list[str], cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """以子进程执行一次 ``donkey``，并断言耗时不超过 10 秒（spec SC-012）。"""
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
        f"donkey init 耗时 {elapsed:.3f}s，超过 {_TIME_LIMIT_SECONDS}s 上限（spec SC-012）"
    )
    return completed


def _init(
    argv: list[str], cwd: Path, target: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    """执行一次 ``donkey init <target>``。"""
    return _run_donkey(argv, cwd, "init", str(target), *extra)


def _sqlite_tables(db_path: Path) -> set[str]:
    """返回 sqlite3 文件中的表名集合。"""
    conn = sqlite3.connect(str(db_path))
    try:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def _sqlite_indexes(db_path: Path, table: str) -> set[str]:
    """返回 sqlite3 文件中指定表的索引名集合。"""
    conn = sqlite3.connect(str(db_path))
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?", (table,)
            )
        }
    finally:
        conn.close()


def _sqlite_count(db_path: Path, table: str) -> int:
    """返回 sqlite3 文件中指定表的记录数。"""
    conn = sqlite3.connect(str(db_path))
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


# --- 场景 1 ~ 5（US1 ~ US5）-------------------------------------------------------


def test_scenario_1_new_workspace_full_tree(tmp_path: Path) -> None:
    """场景 1 · 全新创建：exit 0 + 全部 46 条落地物就位 + 双入口逐字一致。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert (
        "templates=54 files_created=48 files_overwritten=0 files_skipped=0 "
        "dirs_created=6 dirs_skipped=0"
    ) in completed.stdout
    assert ws.is_dir()

    # 必填文件
    for relative in REQUIRED_FILES:
        assert (ws / relative).is_file(), relative
    # 五大必填目录 + skills/example/
    for name in REQUIRED_DIRECTORIES:
        assert (ws / name).is_dir(), name
    assert (ws / "skills" / "example").is_dir()
    # 26 份供应商配置 + 目录索引 + 全局默认
    for provider_id in PROVIDER_IDS:
        assert (ws / "providers" / f"{provider_id}.toml").is_file(), provider_id
    assert (ws / "providers" / "README.md").is_file()
    assert (ws / "providers" / "default.toml").is_file()
    # 三个记忆库模板 + 工作区清单
    for name in ("sessions.sqlite3", "store.sqlite3", "knowledge.sqlite3"):
        assert (ws / "memory" / name).is_file(), name
    assert (ws / "manifest.json").is_file()

    # 落地物计数（spec SC-003）：49 个文件 = 48 清单文件型条目 + 1 工作区清单
    files = [p for p in ws.rglob("*") if p.is_file()]
    directories = [p for p in ws.rglob("*") if p.is_dir()]
    assert len(files) == 49
    assert len(directories) + 1 == 10

    # 双入口一致性（spec FR-060，沿用 P1 的惯例并入场景 1，不新增第 15 个函数）
    console_script = _resolve_console_script()
    if console_script is None:
        print(
            "[verify_phase_f001_p2] 环境性未验证：控制台脚本不可用，"
            "跳过双入口对比断言（非静默跳过）。",
            file=sys.stderr,
        )
    else:
        console_argv = [str(console_script)]
        for suffix in ([], ["--force"]):
            via_console = _init(console_argv, cwd, ws, *suffix)
            via_module = _init(list(_MODULE_ENTRY), cwd, ws, *suffix)
            assert via_console.returncode == via_module.returncode
            assert via_console.stdout == via_module.stdout
            assert via_console.stderr == via_module.stderr

        # 参数用法错误 → 两条入口的 usage 提示逐字相同
        usage_console = _run_donkey(console_argv, cwd, "init")
        usage_module = _run_donkey(list(_MODULE_ENTRY), cwd, "init")
        assert usage_console.returncode == usage_module.returncode == 1
        assert usage_console.stderr == usage_module.stderr
        assert "usage:" in usage_console.stderr


def test_scenario_2_providers_dir_valid(tmp_path: Path) -> None:
    """场景 2 · 供应商目录可被标准 TOML 解析器逐份读取且出厂态关闭。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    providers_dir = ws / "providers"

    # 全局默认文件
    default_doc = tomllib.loads((providers_dir / "default.toml").read_text(encoding="utf-8"))
    assert default_doc["default_provider"] == ""
    assert default_doc["default_model"] == ""

    # 26 份逐份断言（MUST NOT 抽样）
    model_total = 0
    for provider_id in PROVIDER_IDS:
        source = providers_dir / f"{provider_id}.toml"
        parsed = tomllib.loads(source.read_text(encoding="utf-8"))
        assert parsed["enabled"] is False, provider_id
        if provider_id == "bedrock":
            assert "api_key" not in parsed
            for field in (
                "aws_access_key_id",
                "aws_secret_access_key",
                "aws_region",
                "aws_session_token",
            ):
                assert parsed[field] == "", f"{provider_id}.{field}"
        else:
            assert parsed["api_key"] == "", provider_id
        model_total += len(re.findall(r"^\[models\.", source.read_text(encoding="utf-8"), re.M))

    assert model_total == 51

    # 集合断言：以供应商 id 命名的 .toml 文件恰为 26 个
    provider_files = sorted(p.name for p in providers_dir.glob("*.toml"))
    assert len(provider_files) == 27  # 26 份供应商配置 + 1 份全局默认
    assert (providers_dir / "default.toml").is_file()
    assert (providers_dir / "README.md").is_file()

    # 目录索引恰含 26 个 provider id，无省略
    index_doc = (providers_dir / "README.md").read_text(encoding="utf-8")
    listed = [
        line.strip() for line in index_doc.splitlines() if line.strip() in set(PROVIDER_IDS)
    ]
    assert len(listed) == 26
    assert set(listed) == set(PROVIDER_IDS)
    assert "..." not in index_doc


def test_scenario_3_mcp_json_valid(tmp_path: Path) -> None:
    """场景 3 · MCP 配置可被标准 JSON 解析器读取。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    parsed = json.loads((ws / "mcp" / "mcp.json").read_text(encoding="utf-8"))

    assert "mcpServers" in parsed
    assert parsed["mcpServers"] == {}


def test_scenario_4_skill_frontmatter_valid(tmp_path: Path) -> None:
    """场景 4 · 示例 Skill 的 frontmatter 恰含 name + description。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    content = (ws / "skills" / "example" / "SKILL.md").read_text(encoding="utf-8")

    assert content.startswith("---")
    frontmatter = content.split("---")[1]
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line and not line.strip().startswith("#")
    }
    assert keys == {"name", "description"}
    assert "name: example" in frontmatter


def test_scenario_5_name_injection(tmp_path: Path) -> None:
    """场景 5 · 工作区名称在"一致性三处"逐字一致。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "foo"
    assert _init(argv, cwd, ws).returncode == 0

    assert "foo" in (ws / "README.md").read_text(encoding="utf-8")
    assert "foo" in (ws / "providers" / "default.toml").read_text(encoding="utf-8")
    manifest = json.loads((ws / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "foo"

    # 模板正文中 MUST NOT 残留名字占位符字面量（spec SC-014）
    for path in ws.rglob("*"):
        if path.is_file() and path.suffix != ".sqlite3":
            assert "{{" not in path.read_text(encoding="utf-8"), path


# --- 场景 6 ~ 10（US6 ~ US10）-----------------------------------------------------


def test_scenario_6_idempotent_no_force(tmp_path: Path) -> None:
    """场景 6 · 无强制标志：用户改写内容与 mtime 均不变，且无强制清空提示行。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    instruction = ws / "instruction.md"
    instruction.write_text("我的自定义提示词", encoding="utf-8")
    before_stat = instruction.stat()

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert instruction.read_text(encoding="utf-8") == "我的自定义提示词"
    after_stat = instruction.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    # 无 --force 时 MUST NOT 出现强制清空提示行（spec SC-019）
    assert "清空" not in completed.stdout

    # 追加子断言：工作区清单被改坏 → 退出码 3 + 可识别的错误标识 + 一条下一步
    (ws / "manifest.json").write_text("{not json", encoding="utf-8")
    failed = _init(argv, cwd, ws)

    assert failed.returncode == 3, (
        f"stdout={failed.stdout!r} stderr={failed.stderr!r}"
    )
    assert "TemplateGenerationError" in failed.stderr
    assert "下一步" in failed.stderr


def test_scenario_7_corruption_recovery(tmp_path: Path) -> None:
    """场景 7 · 缺失的模板文件被补齐。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "instruction.md").unlink()

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert (ws / "instruction.md").is_file()


def test_scenario_8_force_overwrites(tmp_path: Path) -> None:
    """场景 8 · --force 恢复出厂内容，且 stdout 含强制清空提示行。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "instruction.md").write_text("我的自定义提示词", encoding="utf-8")

    completed = _init(argv, cwd, ws, "--force")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert "我的自定义提示词" not in (ws / "instruction.md").read_text(encoding="utf-8")
    # 强制清空提示行 MUST 出现（spec FR-059 / SC-019）
    assert "清空" in completed.stdout
    # 通用摘要的六个字段仍完整可见
    for field in (
        "workspace=",
        "name=",
        "force=",
        "templates=",
        "files_created=",
        "files_overwritten=",
        "files_skipped=",
        "dirs_created=",
        "dirs_skipped=",
    ):
        assert field in completed.stdout, field


def test_scenario_9_force_preserves_user_content(tmp_path: Path) -> None:
    """场景 9 · --force 不动清单外的用户自建目录与文件。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "media").mkdir()
    (ws / "media" / "video.mp4").write_text("fake-video", encoding="utf-8")
    (ws / "donkey.log").write_text("log line", encoding="utf-8")

    completed = _init(argv, cwd, ws, "--force")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert (ws / "media" / "video.mp4").read_text(encoding="utf-8") == "fake-video"
    assert (ws / "donkey.log").read_text(encoding="utf-8") == "log line"


def test_scenario_10_rm_then_init(tmp_path: Path) -> None:
    """场景 10 · 手动整体删除后重新 init 等价于全新创建。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    shutil.rmtree(ws)

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert (ws / "instruction.md").is_file()
    assert (ws / "manifest.json").is_file()


# --- 场景 11 ~ 14（US11 ~ US14）---------------------------------------------------


def test_scenario_11_builtin_tools_present(tmp_path: Path) -> None:
    """场景 11 · tools/ 下内置工具文件与包初始化文件已就位。

    F001-P3 起这 4 个文件是清单内条目 —— P2 阶段的"尚未生成"否定断言已按
    spec FR-068(e) 改写为 P3 口径（``tools/README.md`` 仍在）。
    """
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    for name in ("filesystem.py", "commandline.py", "webfetch.py", "__init__.py"):
        assert (ws / "tools" / name).is_file(), name
    assert (ws / "tools" / "README.md").is_file()


def test_scenario_12_no_f002_static_check(tmp_path: Path) -> None:
    """场景 12 · init 不对工作区内的配置内容做合法性判定。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    (ws / "providers" / "default.toml").write_text("这不是合法的 TOML {{{", encoding="utf-8")

    completed = _init(argv, cwd, ws)

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )


def test_scenario_13_force_rebuilds_sqlite3_templates(tmp_path: Path) -> None:
    """场景 13 · --force 重建三个记忆库模板且数据清空，备份不受影响。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    db_path = ws / "memory" / "sessions.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO sessions_metadata "
        "(thread_id, title, created_at, updated_at, donkey_version, first_prompt) "
        "VALUES ('t1', '标题', 1.0, 2.0, '0.1.0', '首轮')"
    )
    conn.commit()
    conn.close()
    backup = tmp_path / "backup-sessions.sqlite3"
    shutil.copyfile(db_path, backup)
    assert backup.stat().st_size > 0

    completed = _init(argv, cwd, ws, "--force")

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert {"checkpoints", "writes", "sessions_metadata"} <= _sqlite_tables(db_path)
    assert _sqlite_count(db_path, "sessions_metadata") == 0
    # 用户自行备份的文件依然存在且非空
    assert backup.is_file()
    assert backup.stat().st_size > 0

    # 记忆库目录说明文档（MUST 同时含三个库名、--force 与可执行的备份命令示例）
    memory_doc = (ws / "memory" / "README.md").read_text(encoding="utf-8")
    for name in ("sessions.sqlite3", "store.sqlite3", "knowledge.sqlite3"):
        assert name in memory_doc, name
    assert "--force" in memory_doc
    assert "cp memory/*.sqlite3" in memory_doc


def test_scenario_14_sqlite3_templates_with_schema(tmp_path: Path) -> None:
    """场景 14 · 三个记忆库文件就位，短期记忆库结构完整。"""
    argv, cwd = _resolve_donkey_command()
    ws = tmp_path / "ws"
    assert _init(argv, cwd, ws).returncode == 0

    for name in ("sessions.sqlite3", "store.sqlite3", "knowledge.sqlite3"):
        assert (ws / "memory" / name).is_file(), name

    sessions_db = ws / "memory" / "sessions.sqlite3"
    assert {"checkpoints", "writes", "sessions_metadata"} <= _sqlite_tables(sessions_db)
    indexes = _sqlite_indexes(sessions_db, "sessions_metadata")
    assert "idx_sessions_metadata_title" in indexes
    assert "idx_sessions_metadata_updated_at" in indexes
    assert _sqlite_count(sessions_db, "sessions_metadata") == 0

    for name in ("store.sqlite3", "knowledge.sqlite3"):
        assert _sqlite_tables(ws / "memory" / name) == set(), name
