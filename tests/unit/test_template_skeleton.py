"""F001-P2 ``template_skeleton`` 的单元测试（core 层）。

本文件承载 F001-P2 的全部单元测试用例（spec FR-055 的 16 类 + 边界护栏 +
内容级断言），逐条用例清单以 ``tasks.md`` 为准。

覆盖分组：

- 工作区清单（``donkey.core.workspace.manifest``）—— FR-018 ~ FR-023；
- sqlite3 结构构造器（``donkey.core.workspace.sqlite3_templates``）—— FR-058；
- 模板清单加载与渲染内核（``donkey.core.workspace.init``）—— FR-001 ~ FR-017；
- 初始化流水线与核心库门面（``donkey.core.workspace.init`` /
  ``donkey.core.api``）—— FR-024 ~ FR-029；
- 模板资产内容契约 —— FR-043 / FR-050 / FR-051 / FR-052 / FR-053。
"""

import errno
import json
import re
import sqlite3
from dataclasses import fields
from pathlib import Path
from typing import NamedTuple

import pytest

from donkey.core.api import INIT_RESULT_CONTRACT_VERSION, init_workspace
from donkey.core.exceptions import PathPermissionError, TemplateGenerationError
from donkey.core.version import resolve_version
from donkey.core.workspace.init import (
    DEFAULT_TEMPLATES_ROOT,
    InitItem,
    load_template_manifest,
    render_templates,
)
from donkey.core.workspace.manifest import (
    WORKSPACE_MANIFEST_FILENAME,
    ensure_workspace_manifest,
    read_workspace_manifest,
    write_workspace_manifest,
)
from donkey.core.workspace.sqlite3_templates import (
    build_knowledge_sqlite,
    build_sessions_sqlite,
    build_store_sqlite,
)


def _make_templates_root(
    base: Path,
    entries: list[dict[str, object]],
    sources: dict[str, str],
) -> Path:
    """在临时目录里造一份"安装包内的模板根目录"。

    构造失败分支 MUST 以注入式方式产生，MUST NOT 破坏已安装包
    （spec FR-006 / FR-056）。
    """
    root = base / "templates"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"version": 1, "entries": entries}), encoding="utf-8"
    )
    for relative, content in sources.items():
        source_file = root / f"{relative}.txt"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(content, encoding="utf-8")
    return root


def _tables_and_indexes(db_path: Path) -> tuple[set[str], set[str], int]:
    """返回 ``(表名集合, sessions_metadata 的索引名集合, 会话元数据表记录数)``。"""
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='sessions_metadata'"
            )
        }
        count = conn.execute("SELECT COUNT(*) FROM sessions_metadata").fetchone()[0]
    finally:
        conn.close()
    return tables, indexes, count


# --- sqlite3 结构构造器（FR-058）------------------------------------------------


def test_build_sessions_sqlite_schema(tmp_path: Path) -> None:
    """FR-058 第一项：短期记忆库 —— 三表两索引齐备、记录数为 0。"""
    db_path = tmp_path / "sessions.sqlite3"

    build_sessions_sqlite(db_path)

    tables, indexes, count = _tables_and_indexes(db_path)
    assert {"checkpoints", "writes", "sessions_metadata"} <= tables
    # 索引断言 MUST 用 ``in`` / ``<=`` 判定 —— ``sqlite_autoindex_*`` 是
    # PRIMARY KEY 自动索引且其 ``tbl_name`` 亦为 ``sessions_metadata``
    # （research.md R-05）。
    assert "idx_sessions_metadata_title" in indexes
    assert "idx_sessions_metadata_updated_at" in indexes
    assert count == 0


def test_build_store_and_knowledge_are_empty(tmp_path: Path) -> None:
    """FR-058 第二项：两个占位文件 0 表 0 索引（宪法 D-11）。"""
    store_path = tmp_path / "store.sqlite3"
    knowledge_path = tmp_path / "knowledge.sqlite3"

    build_store_sqlite(store_path)
    build_knowledge_sqlite(knowledge_path)

    for db_path in (store_path, knowledge_path):
        conn = sqlite3.connect(str(db_path))
        try:
            table_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            index_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert table_count == 0
        assert index_count == 0


def test_build_sessions_sqlite_idempotent(tmp_path: Path) -> None:
    """FR-058 第三项：构造幂等 —— 既有表与索引 MUST NOT 被破坏。"""
    db_path = tmp_path / "sessions.sqlite3"
    build_sessions_sqlite(db_path)
    before_tables, before_indexes, _ = _tables_and_indexes(db_path)

    build_sessions_sqlite(db_path)

    after_tables, after_indexes, count = _tables_and_indexes(db_path)
    assert after_tables == before_tables
    assert after_indexes == before_indexes
    assert count == 0


# --- 工作区清单（FR-018 ~ FR-023）------------------------------------------------


def test_manifest_write_new(tmp_path: Path) -> None:
    """FR-055 第 12 项：工作区清单首次写入 → 落地 ``manifest.json``。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    written = write_workspace_manifest(workspace, "ws", False)

    manifest_file = workspace / WORKSPACE_MANIFEST_FILENAME
    assert manifest_file.is_file()
    assert written["name"] == "ws"
    assert json.loads(manifest_file.read_text(encoding="utf-8")) == written


def test_manifest_skip_existing_no_force(tmp_path: Path) -> None:
    """FR-055 第 13 项：不带强制标志且清单已存在 → 不覆盖、保留原创建时间。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    first = write_workspace_manifest(workspace, "ws", False)
    manifest_file = workspace / WORKSPACE_MANIFEST_FILENAME
    original = manifest_file.read_text(encoding="utf-8")

    second = write_workspace_manifest(workspace, "other", False)

    assert manifest_file.read_text(encoding="utf-8") == original
    assert second["created_at"] == first["created_at"]
    assert second["name"] == "ws"


def test_manifest_refresh_force(tmp_path: Path) -> None:
    """FR-055 第 14 项：带强制标志 → 覆盖并刷新创建时间。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    first = write_workspace_manifest(workspace, "ws", False)
    manifest_file = workspace / WORKSPACE_MANIFEST_FILENAME

    second = write_workspace_manifest(workspace, "ws", True)

    assert second["created_at"] != first["created_at"]
    assert json.loads(manifest_file.read_text(encoding="utf-8")) == second



class _Counts(NamedTuple):
    """逐项明细的计数投影（文件 / 目录 × 新建 / 覆盖 / 跳过）。"""

    files_created: int
    files_overwritten: int
    files_skipped: int
    dirs_created: int
    dirs_skipped: int


def _project(items: list[InitItem]) -> _Counts:
    """把 ``render_templates`` 的逐项明细投影成五个计数。

    > **断言改写登记（宪法 [D-22] · 2026-10-30 · Maintainer 裁决）**：
    > ``render_templates`` 原先返回 ``(files_created, files_skipped)`` 两个计数，
    > 且 ``--force`` 下的**覆盖**被并入 ``created`` —— "新建"与"覆盖"两个动作
    > **不可区分**。现返回逐项明细，断言一律按「对象 × 动作」投影。
    """
    return _Counts(
        files_created=sum(1 for i in items if i.kind == "file" and i.action == "created"),
        files_overwritten=sum(
            1 for i in items if i.kind == "file" and i.action == "overwritten"
        ),
        files_skipped=sum(1 for i in items if i.kind == "file" and i.action == "skipped"),
        dirs_created=sum(1 for i in items if i.kind == "dir" and i.action == "created"),
        dirs_skipped=sum(1 for i in items if i.kind == "dir" and i.action == "skipped"),
    )


def test_manifest_field_minimal(tmp_path: Path) -> None:
    """FR-055 第 15 项：清单字段恰为三项，且取值符合契约（FR-019 / FR-021）。

    > **断言改写登记（宪法 [D-21] · 2026-10-30 · Maintainer 裁决）**：
    > 原断言为「字段恰为**四**项」且含 ``version == 1``（整数）—— 该字段
    > **无人读取**且与 ``donkey_version`` 并排时读作"两个打架的版本号"，已
    > **删除**（F001-P2 FR-019 的"版本号"一项随之失效）。
    > 同时 ``donkey_version`` 由硬编码改为**动态取值**（F001-P2 FR-021
    > 预留的演进路径）—— 故此处 MUST NOT 断言字面量 ``"0.1.0"``，
    > 改为与**运行时**版本比对（否则版本 bump 后本断言会假失败）。
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()

    written = write_workspace_manifest(workspace, "ws", False)

    assert set(written.keys()) == {"name", "created_at", "donkey_version"}
    assert written["name"] == "ws"
    assert written["donkey_version"] == resolve_version()


def test_manifest_json_encoding(tmp_path: Path) -> None:
    """FR-055 第 15 项的补充：编码形态 —— 2 空格缩进、非 ASCII 保留原文、无 BOM。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    write_workspace_manifest(workspace, "我的 工作区 ✨", False)

    raw = (workspace / WORKSPACE_MANIFEST_FILENAME).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    assert "我的 工作区 ✨" in text
    assert "\\u" not in text
    assert '\n  "name"' in text


def test_manifest_read_invalid_json_raises(tmp_path: Path) -> None:
    """FR-055 第 16 项：清单内容非法 JSON → 读取抛模板生成类错误（退出码 3）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / WORKSPACE_MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")

    with pytest.raises(TemplateGenerationError) as excinfo:
        read_workspace_manifest(workspace)

    assert "下一步" in str(excinfo.value)


def test_manifest_force_overwrites_invalid_json(tmp_path: Path) -> None:
    """spec Edge Cases「其它边界」：坏 JSON + 强制标志 → 覆盖为合法内容。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    manifest_file = workspace / WORKSPACE_MANIFEST_FILENAME
    manifest_file.write_text("{not json", encoding="utf-8")

    written = write_workspace_manifest(workspace, "ws", True)

    assert set(written.keys()) == {"name", "created_at", "donkey_version"}
    assert json.loads(manifest_file.read_text(encoding="utf-8")) == written


def test_manifest_read_missing_returns_none(tmp_path: Path) -> None:
    """FR-018：清单文件不存在 → 读取返回"无"（``None``），MUST NOT 抛错。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    assert read_workspace_manifest(workspace) is None


def test_ensure_manifest_equivalent_to_write(tmp_path: Path) -> None:
    """FR-023 / research.md R-10：``ensure`` 与 ``write`` 的判定顺序严格等价。"""
    # 组合一：坏 JSON + 强制标志 → 两者都覆盖为合法内容。
    for func in (write_workspace_manifest, ensure_workspace_manifest):
        workspace = tmp_path / f"force-{func.__name__}"
        workspace.mkdir()
        (workspace / WORKSPACE_MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")

        written = func(workspace, "ws", True)

        assert set(written.keys()) == {"name", "created_at", "donkey_version"}
        assert json.loads(
            (workspace / WORKSPACE_MANIFEST_FILENAME).read_text(encoding="utf-8")
        ) == written

    # 组合二：坏 JSON + 不带强制标志 → 两者都抛模板生成类错误且不覆盖原文件。
    for func in (write_workspace_manifest, ensure_workspace_manifest):
        workspace = tmp_path / f"noforce-{func.__name__}"
        workspace.mkdir()
        (workspace / WORKSPACE_MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")

        with pytest.raises(TemplateGenerationError):
            func(workspace, "ws", False)

        assert (workspace / WORKSPACE_MANIFEST_FILENAME).read_text(encoding="utf-8") == (
            "{not json"
        )


# --- 模板清单加载与渲染内核（FR-001 ~ FR-017）------------------------------------


def test_render_new_file(tmp_path: Path) -> None:
    """FR-055 第 1 项：目标不存在 → 写入默认内容，计入新建数。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()

    counts = _project(
        render_templates(
            workspace, "ws", False, load_template_manifest(root / "manifest.json"), root
        )
    )

    assert counts.files_created == 1
    assert counts.files_skipped == 0
    assert (workspace / "instruction.md").read_text(encoding="utf-8") == "出厂内容"


def test_render_skip_existing_no_force(tmp_path: Path) -> None:
    """FR-055 第 2 项：目标已存在且被用户改写 → 完全不动，计入跳过数。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = workspace / "instruction.md"
    target.write_text("用户改写的内容", encoding="utf-8")
    before_mtime = target.stat().st_mtime

    counts = _project(
        render_templates(
            workspace, "ws", False, load_template_manifest(root / "manifest.json"), root
        )
    )

    assert counts.files_created == 0
    assert counts.files_skipped == 1
    assert target.read_text(encoding="utf-8") == "用户改写的内容"
    assert target.stat().st_mtime == before_mtime


def test_render_force_overwrite(tmp_path: Path) -> None:
    """FR-055 第 3 项：带强制标志 → 删除后按默认内容重建。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = workspace / "instruction.md"
    target.write_text("用户改写的内容", encoding="utf-8")

    counts = _project(
        render_templates(
            workspace, "ws", True, load_template_manifest(root / "manifest.json"), root
        )
    )

    # **覆盖 ≠ 新建** —— 强制标志下的重建计入 ``files_overwritten``（[D-22]）。
    assert counts.files_created == 0
    assert counts.files_overwritten == 1
    assert counts.files_skipped == 0
    assert target.read_text(encoding="utf-8") == "出厂内容"


def test_render_force_directory(tmp_path: Path) -> None:
    """FR-055 第 4 项：强制标志下目录条目**不删除任何文件**。"""
    root = _make_templates_root(
        tmp_path,
        [
            {"path": "skills/example", "format": "directory"},
            {"path": "skills/example/SKILL.md", "format": "markdown"},
        ],
        {"skills/example/SKILL.md": "出厂 SKILL 正文"},
    )
    workspace = tmp_path / "ws"
    example_dir = workspace / "skills" / "example"
    example_dir.mkdir(parents=True)
    (example_dir / "SKILL.md").write_text("用户改写的 SKILL", encoding="utf-8")
    (example_dir / "my_notes.md").write_text("清单外用户文件", encoding="utf-8")

    counts = _project(
        render_templates(
            workspace, "ws", True, load_template_manifest(root / "manifest.json"), root
        )
    )

    # 目录本身不删、清单外文件不删
    assert example_dir.is_dir()
    assert (example_dir / "my_notes.md").read_text(encoding="utf-8") == "清单外用户文件"
    # 清单内文件由其自身的条目负责重建为出厂内容
    assert (example_dir / "SKILL.md").read_text(encoding="utf-8") == "出厂 SKILL 正文"
    # 清单内文件 = 覆盖；目录条目 = 跳过（既有目录**永不**"覆盖"，[D-22]）
    assert counts.files_overwritten == 1
    assert counts.files_created == 0
    assert counts.dirs_skipped == 1


def test_render_skip_user_content(tmp_path: Path) -> None:
    """FR-055 第 5 项：强制标志不动清单外的用户内容。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    (workspace / "media").mkdir(parents=True)
    (workspace / "media" / "video.mp4").write_text("fake", encoding="utf-8")
    (workspace / "tools").mkdir()
    (workspace / "tools" / "my_tool.py").write_text("# 用户自定义工具", encoding="utf-8")

    render_templates(workspace, "ws", True, load_template_manifest(root / "manifest.json"), root)

    assert (workspace / "media" / "video.mp4").read_text(encoding="utf-8") == "fake"
    assert (workspace / "tools" / "my_tool.py").read_text(encoding="utf-8") == "# 用户自定义工具"


def test_render_force_rebuilds_sqlite3(tmp_path: Path) -> None:
    """FR-055 第 6 项：强制标志重建 sqlite3 模板且数据清空（两侧同时断言）。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "memory/sessions.sqlite3", "format": "sqlite3"}],
        {},
    )
    workspace = tmp_path / "ws"
    (workspace / "memory").mkdir(parents=True)
    db_path = workspace / "memory" / "sessions.sqlite3"
    build_sessions_sqlite(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO sessions_metadata "
        "(thread_id, title, created_at, updated_at, donkey_version, first_prompt) "
        "VALUES ('t1', '标题', 1.0, 2.0, '0.1.0', '首轮')"
    )
    conn.commit()
    conn.close()
    (workspace / "media").mkdir()
    (workspace / "media" / "keep.txt").write_text("保留", encoding="utf-8")

    render_templates(workspace, "ws", True, load_template_manifest(root / "manifest.json"), root)

    # 侧一：sqlite3 数据已清空
    tables, _indexes, count = _tables_and_indexes(db_path)
    assert {"checkpoints", "writes", "sessions_metadata"} <= tables
    assert count == 0
    # 侧二：用户内容仍在
    assert (workspace / "media" / "keep.txt").read_text(encoding="utf-8") == "保留"


def test_render_placeholder_substitution(tmp_path: Path) -> None:
    """占位符：带空格与不带空格两种写法均被替换，未识别占位符原样保留。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "A={{ workspace_name }} B={{workspace_name}} C={{ unknown_token }}"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()

    entries = load_template_manifest(root / "manifest.json")
    render_templates(workspace, "my ws", False, entries, root)

    content = (workspace / "instruction.md").read_text(encoding="utf-8")
    assert content == "A=my ws B=my ws C={{ unknown_token }}"


def test_render_target_is_directory(tmp_path: Path) -> None:
    """目标路径已存在且是目录 → 模板生成类错误；目录内容原样保留。"""
    root = _make_templates_root(
        tmp_path,
        [
            {"path": "instruction.md", "format": "markdown"},
            {"path": "memory/sessions.sqlite3", "format": "sqlite3"},
            {"path": "tools", "format": "directory"},
        ],
        {"instruction.md": "出厂内容"},
    )
    entries = load_template_manifest(root / "manifest.json")

    # 文本类条目的目标是目录
    workspace = tmp_path / "ws-text"
    (workspace / "instruction.md").mkdir(parents=True)
    (workspace / "instruction.md" / "inner.txt").write_text("目录内容", encoding="utf-8")

    with pytest.raises(TemplateGenerationError):
        render_templates(workspace, "ws", False, entries, root)

    assert (workspace / "instruction.md" / "inner.txt").read_text(encoding="utf-8") == "目录内容"

    # sqlite3 类条目的目标是目录
    workspace2 = tmp_path / "ws-sqlite"
    (workspace2 / "memory" / "sessions.sqlite3").mkdir(parents=True)
    inner = workspace2 / "memory" / "sessions.sqlite3" / "inner.txt"
    inner.write_text("目录内容", encoding="utf-8")

    with pytest.raises(TemplateGenerationError):
        render_templates(workspace2, "ws", False, entries, root)

    assert (
        workspace2 / "memory" / "sessions.sqlite3" / "inner.txt"
    ).read_text(encoding="utf-8") == "目录内容"

    # 目录类条目已存在 → MUST NOT 报错
    workspace3 = tmp_path / "ws-dir"
    (workspace3 / "tools").mkdir(parents=True)
    (workspace3 / "tools" / "user_tool.py").write_text("# 用户工具", encoding="utf-8")

    render_templates(workspace3, "ws", False, entries, root)

    assert (workspace3 / "tools" / "user_tool.py").read_text(encoding="utf-8") == "# 用户工具"


def test_render_duplicate_manifest_entry(tmp_path: Path) -> None:
    """清单内同一路径出现两次 → 不报错，按唯一路径处理、后者胜出。"""
    root = _make_templates_root(
        tmp_path,
        [
            {"path": "doc.md", "format": "markdown"},
            {"path": "doc.md", "format": "text"},
            {"path": "thing", "format": "text"},
            {"path": "thing", "format": "directory"},
            {"path": "other.md", "format": "markdown"},
        ],
        {"doc.md": "doc 出厂内容", "thing": "thing 出厂内容", "other.md": "other 出厂内容"},
    )
    entries = load_template_manifest(root / "manifest.json")
    workspace = tmp_path / "ws"
    workspace.mkdir()

    counts = _project(render_templates(workspace, "ws", False, entries, root))

    unique_paths = {entry["path"] for entry in entries}
    unique_file_paths = {path for path in unique_paths if path not in {"thing"}}
    # loader 返回原始列表（长度 == templates_loaded 口径），大于唯一路径数
    assert len(entries) == 5
    assert len(unique_paths) == 3
    # 唯一文件型路径只计一次
    assert counts.files_created + counts.files_skipped == len(unique_file_paths)
    assert counts.files_created == 2
    assert counts.files_skipped == 0
    # 后者胜出 → "thing" 是目录（最后一条 format 为 directory）
    assert (workspace / "thing").is_dir()
    assert not (workspace / "thing").is_file()
    assert (workspace / "doc.md").read_text(encoding="utf-8") == "doc 出厂内容"
    assert (workspace / "other.md").read_text(encoding="utf-8") == "other 出厂内容"


def test_render_template_source_missing(tmp_path: Path) -> None:
    """FR-055 第 7 项：模板源缺失 → 模板生成类错误（MUST NOT 是路径类错误）。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "missing.md", "format": "markdown"}],
        {},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()

    with pytest.raises(TemplateGenerationError) as excinfo:
        entries = load_template_manifest(root / "manifest.json")
        render_templates(workspace, "ws", False, entries, root)

    assert "下一步" in str(excinfo.value)


def test_load_template_manifest_corrupted(tmp_path: Path) -> None:
    """FR-055 第 8 项：清单损坏 → 模板生成类错误。"""
    root = tmp_path / "templates"
    root.mkdir()
    (root / "manifest.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(TemplateGenerationError):
        load_template_manifest(root / "manifest.json")


def test_load_template_manifest_schema_invalid(tmp_path: Path) -> None:
    """FR-055 第 9 项：清单结构非法 → 模板生成类错误。"""
    invalid_payloads = [
        {"version": "1", "entries": []},
        {"version": 1, "entries": {}},
        {"version": 1, "entries": ["instruction.md"]},
        {"version": 1, "entries": [{"format": "markdown"}]},
        {"version": 1, "entries": [{"path": "", "format": "markdown"}]},
        {"version": 1, "entries": [{"path": "a.md", "format": "yaml"}]},
    ]

    for payload in invalid_payloads:
        root = tmp_path / f"templates-{len(json.dumps(payload))}-{abs(hash(str(payload)))}"
        root.mkdir()
        (root / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")

        with pytest.raises(TemplateGenerationError):
            load_template_manifest(root / "manifest.json")


def test_render_permission_denied_midway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-055 第 10 项：渲染中途权限失败 → 模板生成类错误。

    MUST 以**注入式**构造产生 —— 特权账号（root / ``CAP_DAC_OVERRIDE``）会绕过
    DAC 权限检查，其对只读目录的写入**仍成功**，chmod 方案在 root CI 容器中
    必然假失败（spec Assumptions「特权环境说明」/ plan R-18）。
    """
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    entries = load_template_manifest(root / "manifest.json")

    def _boom(self: Path, *args: object, **kwargs: object) -> int:
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(Path, "write_text", _boom)

    with pytest.raises(TemplateGenerationError) as excinfo:
        render_templates(workspace, "ws", False, entries, root)

    assert "下一步" in str(excinfo.value)


def test_load_template_manifest_format_omitted_defaults_to_text(tmp_path: Path) -> None:
    """补充 ①：条目省略 ``format`` → 按 ``text`` 处理（源路径 ``<path>.txt``）。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "plain.md"}],
        {"plain.md": "纯文本出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()

    entries = load_template_manifest(root / "manifest.json")

    assert entries == [{"path": "plain.md"}]
    counts = _project(render_templates(workspace, "ws", False, entries, root))

    assert counts.files_created == 1
    assert counts.files_skipped == 0
    assert (workspace / "plain.md").read_text(encoding="utf-8") == "纯文本出厂内容"


def test_load_template_manifest_duplicate_paths_no_error(tmp_path: Path) -> None:
    """补充 ②：清单内路径重复 → loader 不报错、返回原始列表（长度 == 2）。"""
    root = _make_templates_root(
        tmp_path,
        [
            {"path": "doc.md", "format": "markdown"},
            {"path": "doc.md", "format": "text"},
        ],
        {"doc.md": "doc 出厂内容"},
    )

    entries = load_template_manifest(root / "manifest.json")

    assert len(entries) == 2


def test_template_error_message_has_next_step(tmp_path: Path) -> None:
    """FR-055 第 11 项：模板类失败的错误信息 MUST 含可执行的下一步。"""
    root = tmp_path / "templates"
    root.mkdir()
    (root / "manifest.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(TemplateGenerationError) as excinfo:
        load_template_manifest(root / "manifest.json")

    message = str(excinfo.value)
    assert "下一步" in message
    assert any(
        keyword in message for keyword in ("重装 donkey", "权限", "重试 init")
    )
    assert "TemplateGenerationError" in type(excinfo.value).__name__


# --- 初始化流水线与核心库门面（FR-024 ~ FR-029、澄清 #26 / #27）------------------


def test_init_manifest_write_failure_keeps_rendered_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """澄清 #26 / plan R-16：步骤 ⑤ 失败 MUST NOT 回滚步骤 ④ 已落地的文件。"""
    workspace = tmp_path / "ws"

    def _boom(*args: object, **kwargs: object) -> None:
        raise TemplateGenerationError("注入的清单写入失败")

    monkeypatch.setattr("donkey.core.workspace.init.write_workspace_manifest", _boom)

    with pytest.raises(TemplateGenerationError):
        init_workspace(workspace)

    # 步骤 ④ 已落地的模板文件仍在，内容为出厂内容
    assert (workspace / "instruction.md").is_file()
    assert (workspace / "providers" / "default.toml").is_file()
    assert (workspace / "mcp" / "mcp.json").is_file()
    # 工作区清单未被写入
    assert not (workspace / WORKSPACE_MANIFEST_FILENAME).exists()


def test_root_dir_creation_failure_maps_to_exit_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-038：步骤 ③ 的一切失败（含磁盘满 ``ENOSPC``）一律归退出码 ``2``。"""
    workspace = tmp_path / "ws"

    def _boom(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(Path, "mkdir", _boom)

    with pytest.raises(PathPermissionError) as excinfo:
        init_workspace(workspace)

    assert not isinstance(excinfo.value, TemplateGenerationError)
    assert "下一步" in str(excinfo.value)
    assert "No space left on device" in str(excinfo.value)


def test_init_workspace_counts_and_manifest(tmp_path: Path) -> None:
    """FR-017 / FR-025 / FR-026：计数口径与结果契约字段。"""
    from donkey.core.api import InitResult

    workspace = tmp_path / "ws"
    entries = load_template_manifest()
    file_type_entries = {
        entry["path"] for entry in entries if entry.get("format", "text") != "directory"
    }

    result = init_workspace(workspace)

    assert result.templates_loaded == len(entries)
    assert result.files_created == len(file_type_entries)
    assert result.files_skipped == 0
    assert result.files_overwritten == 0
    assert result.dirs_created == 6
    assert result.dirs_skipped == 0
    assert len(result.items) == len(entries)
    assert (workspace / WORKSPACE_MANIFEST_FILENAME).is_file()
    manifest = read_workspace_manifest(workspace)
    assert manifest is not None
    assert manifest["name"] == workspace.name
    # **库 API 契约 v2**（宪法 [D-22]）—— v1 的六个字段**逐字保留、顺序不变**，
    # 新增四个计数 + 逐项明细；契约版本号 MUST 同步递增（FR-006 要求"不得
    # 在本阶段之后**无版本号**变更"）。
    assert [f.name for f in fields(InitResult)] == [
        "workspace_path",
        "name",
        "force",
        "templates_loaded",
        "files_created",
        "files_skipped",
        "files_overwritten",
        "dirs_created",
        "dirs_skipped",
        "items",
    ]
    assert INIT_RESULT_CONTRACT_VERSION == 2


#: 宪法 N-12：workspace 内容 MUST NOT 含任何智能体框架的可观测性后端形态。
#:
#: 该关键词 MUST 以**正则字符类**拼出 —— 仓库自身的静态 grep 自检
#: （quickstart §4）MUST NOT 在源码里命中它，否则自检会把自己的断言当成违例。
#: 模式大小写不敏感，覆盖该后端名的大小写变体与其 ``_`` 前缀环境变量形态。
_OBSERVABILITY_NEEDLE = re.compile(r"lang[_-]?smith", re.IGNORECASE)


# --- 模板资产与内容契约（FR-039 ~ FR-054）----------------------------------------


def test_template_assets_render_to_expected_tree(tmp_path: Path) -> None:
    """T018 / SC-003：以安装包内**真实资产**渲染 → 49 文件 / 10 目录 / 54·48·0。"""
    result = init_workspace(tmp_path)

    assert result.templates_loaded == 54
    assert result.files_created == 48
    assert result.files_skipped == 0

    files = [p for p in tmp_path.rglob("*") if p.is_file()]
    directories = [p for p in tmp_path.rglob("*") if p.is_dir()]
    # 49 个文件 = 48 个清单文件型条目 + 1 份工作区清单
    assert len(files) == 49
    # 10 个目录 = 根 + 6 个清单目录 + 3 个 Skill Level 3 子目录
    assert len(directories) + 1 == 10
    assert (tmp_path / "manifest.json").is_file()

    # 渲染结果中 MUST 无占位符残留（spec SC-014 / 契约 B12）
    for path in files:
        if path.suffix == ".sqlite3":
            continue
        assert "{{" not in path.read_text(encoding="utf-8"), path


def test_gitignore_template_content(tmp_path: Path) -> None:
    """T087 / FR-053：忽略规则恰为 9 条，渲染后内容一致且无占位符残留。"""
    source = DEFAULT_TEMPLATES_ROOT / ".gitignore.txt"
    content = source.read_text(encoding="utf-8")
    expected_lines = [
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.egg-info/",
        ".venv/",
        "venv/",
        "memory/*.sqlite3",
        "memory/*.sqlite3-wal",
        "memory/*.sqlite3-shm",
    ]
    for line in expected_lines:
        assert line in content, line

    init_workspace(tmp_path)

    rendered = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert rendered == content
    assert "{{" not in rendered


def test_instruction_template_title_and_sections(tmp_path: Path) -> None:
    """T088 / FR-043：标题用工作区名称 + 恰三个留白小节，无 Python 入口内容。"""
    content = (DEFAULT_TEMPLATES_ROOT / "instruction.md.txt").read_text(encoding="utf-8")

    first_line = content.splitlines()[0]
    assert first_line.startswith("# ")
    assert "{{ workspace_name }}" in first_line

    sections = [line.strip() for line in content.splitlines() if line.startswith("## ")]
    assert sections == ["## 角色", "## 风格", "## 限制"]

    # 宪法 N-01：MUST NOT 含任何 Python 入口文件
    assert ".py" not in content
    assert "agent.py" not in content
    assert "main.py" not in content


def test_workspace_readme_template_content(tmp_path: Path) -> None:
    """T089 / FR-050：含工作区名称占位符 + 概述六个目录职责，不承诺引擎层能力。"""
    content = (DEFAULT_TEMPLATES_ROOT / "README.md.txt").read_text(encoding="utf-8")

    assert "{{ workspace_name }}" in content
    for directory in ("instruction.md", "providers/", "tools/", "mcp/", "skills/", "memory/"):
        assert directory in content, directory

    # 宪法 AC-5 / §2.1：官方模板 MUST NOT 承诺引擎层能力
    assert "diff" not in content
    assert "路径权限" not in content
    assert "fork" not in content


def test_dir_readme_templates_content(tmp_path: Path) -> None:
    """T090 / FR-051：三份目录说明文档各自的内容契约。"""
    tools_doc = (DEFAULT_TEMPLATES_ROOT / "tools" / "README.md.txt").read_text(encoding="utf-8")
    for keyword in ("命名", "参数", "错误处理", "超时"):
        assert keyword in tools_doc, keyword
    # F001-P3 起该正文已被**覆盖**为完整的工具开发规范 —— 8 项必备要点齐备
    # （spec FR-044 (a) ~ (h)）。
    for keyword in (
        "langchain_core.tools",  # (a) 工具装饰器的官方导入位置
        "docstring",  # (b) 函数必须有说明文字
        "路径白名单",  # (c) 路径白名单由用户自管
        "60",  # (d) 推荐的超时配置（命令 60 秒 · 网络 30 秒）
        "错误处理",  # (e) 错误处理建议
        "工作区根",  # (f) 工作区根的推导方式
        "备份",  # (g) 契约库与用户自写工具是一套的
        "httpx",  # (h) 网络工具需自行安装 HTTP 客户端库
    ):
        assert keyword in tools_doc, keyword
    # 契约库**是契约库、不是工具**（spec FR-046）+ 变更记录契约小节（FR-045）
    assert "不是工具" in tools_doc
    assert "改文件的工具怎么写" in tools_doc

    mcp_doc = (DEFAULT_TEMPLATES_ROOT / "mcp" / "README.md.txt").read_text(encoding="utf-8")
    assert "mcpServers" in mcp_doc
    assert "用户自行填写" in mcp_doc

    skills_doc = (DEFAULT_TEMPLATES_ROOT / "skills" / "README.md.txt").read_text(encoding="utf-8")
    for keyword in ("name", "description", "Level 2", "Level 3"):
        assert keyword in skills_doc, keyword
    assert "不允许自定义额外字段" in skills_doc


# --- 供应商配置目录（FR-045 ~ FR-047）--------------------------------------------

#: v1 白名单内的 26 家供应商 id（与调研 §3.1 逐条一致）。
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

#: ``bedrock`` 的专属账号字段（出厂态全为空串，spec FR-047）。
BEDROCK_ACCOUNT_FIELDS = (
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_region",
    "aws_session_token",
)


def _parse_provider(provider_id: str) -> dict[str, object]:
    """解析一份供应商配置源（``<id>.toml.txt``）。"""
    import tomllib

    source = DEFAULT_TEMPLATES_ROOT / "providers" / f"{provider_id}.toml.txt"
    return tomllib.loads(source.read_text(encoding="utf-8"))


def test_providers_dir_parseable_and_disabled(tmp_path: Path) -> None:
    """T034 / FR-046 / FR-047：26 份逐份可解析、开关全关、凭据为空。"""
    import tomllib

    # 文件选择 MUST 显式排除 ``default.toml.txt``（保留名、非供应商配置）。
    for provider_id in PROVIDER_IDS:
        parsed = _parse_provider(provider_id)
        assert parsed["enabled"] is False, provider_id
        if provider_id == "bedrock":
            assert "api_key" not in parsed
            for field in BEDROCK_ACCOUNT_FIELDS:
                assert field in parsed, field
                assert parsed[field] == "", f"{provider_id}.{field}"
        else:
            assert parsed["api_key"] == "", provider_id

    default_doc = tomllib.loads(
        (DEFAULT_TEMPLATES_ROOT / "providers" / "default.toml.txt").read_text(encoding="utf-8")
    )
    assert default_doc["default_provider"] == ""
    assert default_doc["default_model"] == ""


def test_provider_models_count_is_51(tmp_path: Path) -> None:
    """T035 / SC-015：26 份配置中的 ``[models.*]`` 条目合计恰为 51 条。"""
    import re

    total = 0
    for provider_id in PROVIDER_IDS:
        source = DEFAULT_TEMPLATES_ROOT / "providers" / f"{provider_id}.toml.txt"
        total += len(re.findall(r"^\[models\.", source.read_text(encoding="utf-8"), re.M))

    assert total == 51


def test_providers_index_lists_all_26(tmp_path: Path) -> None:
    """T036 / FR-045：目录索引恰列出 26 个 provider id，且含三段说明。"""
    content = (DEFAULT_TEMPLATES_ROOT / "providers" / "README.md.txt").read_text(encoding="utf-8")
    listed = [line.strip() for line in content.splitlines() if line.strip() in set(PROVIDER_IDS)]

    assert len(listed) == 26
    assert set(listed) == set(PROVIDER_IDS)
    assert "..." not in content

    # 三段说明
    assert "文件名 stem == provider_id" in content
    assert "启用三步" in content
    assert "完全惰性" in content
    assert "不校验字段" in content
    assert "不参与连通性检查" in content


# --- US3 ~ US14 的行为硬化与内容契约 ---------------------------------------------


def test_mcp_json_parseable(tmp_path: Path) -> None:
    """T039 / US3 / FR-048：MCP 配置是合法 JSON，含空的服务器表。"""
    import json as _json

    content = (DEFAULT_TEMPLATES_ROOT / "mcp" / "mcp.json.txt").read_text(encoding="utf-8")
    parsed = _json.loads(content)

    assert "mcpServers" in parsed
    assert parsed["mcpServers"] == {}


def test_skill_frontmatter_exactly_two_fields(tmp_path: Path) -> None:
    """T041 / US4 / FR-049：示例 Skill 的 frontmatter 恰含 name + description。"""
    content = (DEFAULT_TEMPLATES_ROOT / "skills" / "example" / "SKILL.md.txt").read_text(
        encoding="utf-8"
    )
    assert content.startswith("---")
    frontmatter = content.split("---")[1]
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line and not line.strip().startswith("#")
    }

    assert keys == {"name", "description"}
    values = dict(
        line.split(":", 1)
        for line in frontmatter.splitlines()
        if ":" in line and not line.strip().startswith("#")
    )
    assert values["name"].strip() == "example"


def test_workspace_name_injected_three_places(tmp_path: Path) -> None:
    """T043 / US5 / SC-014：工作区名称在"一致性三处"逐字一致，且无占位符残留。"""
    for workspace_name in ("foo", "my ws ✨"):
        workspace = tmp_path / f"ws-{len(workspace_name)}"
        init_workspace(workspace, name=workspace_name)

        assert workspace_name in (workspace / "README.md").read_text(encoding="utf-8")
        assert workspace_name in (workspace / "providers" / "default.toml").read_text(
            encoding="utf-8"
        )
        manifest = read_workspace_manifest(workspace)
        assert manifest is not None
        assert manifest["name"] == workspace_name

        for path in workspace.rglob("*"):
            if path.is_file() and path.suffix != ".sqlite3":
                assert "{{" not in path.read_text(encoding="utf-8"), path


def test_render_skip_existing_keeps_mtime(tmp_path: Path) -> None:
    """T045 / US6 / SC-004：无强制标志时已存在文件的内容与 mtime 均不变。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = workspace / "instruction.md"
    target.write_text("用户改写的内容", encoding="utf-8")
    before_mtime = target.stat().st_mtime

    render_templates(workspace, "ws", False, load_template_manifest(root / "manifest.json"), root)

    assert target.read_text(encoding="utf-8") == "用户改写的内容"
    assert target.stat().st_mtime == before_mtime


def test_render_missing_file_is_recreated(tmp_path: Path) -> None:
    """T047 / US7 场景 1：清单内缺失的条目被补齐，内容为出厂内容。"""
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = workspace / "instruction.md"
    target.write_text("用户改写的内容", encoding="utf-8")
    target.unlink()

    counts = _project(
        render_templates(
            workspace, "ws", False, load_template_manifest(root / "manifest.json"), root
        )
    )

    assert counts.files_created == 1
    assert counts.files_skipped == 0
    assert target.read_text(encoding="utf-8") == "出厂内容"


def test_render_missing_file_does_not_touch_others(tmp_path: Path) -> None:
    """T047 / US7 场景 2：补齐不影响其它文件的内容与 mtime。"""
    root = _make_templates_root(
        tmp_path,
        [
            {"path": "instruction.md", "format": "markdown"},
            {"path": "other.md", "format": "markdown"},
        ],
        {"instruction.md": "出厂内容", "other.md": "另一份出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "instruction.md").write_text("用户改写的内容", encoding="utf-8")
    other = workspace / "other.md"
    other.write_text("用户的另一份内容", encoding="utf-8")
    other_before = other.stat().st_mtime
    (workspace / "instruction.md").unlink()

    render_templates(workspace, "ws", False, load_template_manifest(root / "manifest.json"), root)

    assert other.read_text(encoding="utf-8") == "用户的另一份内容"
    assert other.stat().st_mtime == other_before


def test_force_restores_factory_content_and_manifest_created_at(tmp_path: Path) -> None:
    """T049 / US8：强制标志恢复出厂内容，并覆盖工作区清单、刷新创建时间。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    (workspace / "instruction.md").write_text("我的自定义提示词", encoding="utf-8")
    manifest_before = read_workspace_manifest(workspace)
    assert manifest_before is not None

    init_workspace(workspace, force=True)

    assert "我的自定义提示词" not in (workspace / "instruction.md").read_text(encoding="utf-8")
    manifest_after = read_workspace_manifest(workspace)
    assert manifest_after is not None
    assert manifest_after["created_at"] != manifest_before["created_at"]


def test_force_preserves_user_content(tmp_path: Path) -> None:
    """T051 / US9：强制重置的作用域严格限定在模板清单条目内。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    (workspace / "media").mkdir()
    (workspace / "media" / "video.mp4").write_text("fake-video", encoding="utf-8")
    (workspace / "donkey.log").write_text("log line", encoding="utf-8")

    init_workspace(workspace, force=True)

    assert (workspace / "media" / "video.mp4").read_text(encoding="utf-8") == "fake-video"
    assert (workspace / "donkey.log").read_text(encoding="utf-8") == "log line"


def test_init_after_full_removal_equals_fresh(tmp_path: Path) -> None:
    """T053 / US10：整体删除后重新 init，结果与首次创建完全一致。"""
    import shutil

    workspace = tmp_path / "ws"
    init_workspace(workspace)
    first = sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*"))

    shutil.rmtree(workspace)
    init_workspace(workspace)

    second = sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*"))
    assert second == first


def test_builtin_tool_files_generated_without_agent_entry(tmp_path: Path) -> None:
    """T055 / US11 / SC-016：内置工具文件已就位，且不含智能体入口与子智能体内容。

    F001-P3 起这 4 个文件是**清单内条目**（spec FR-053）—— P2 阶段的
    "尚未生成"否定断言已按 spec FR-068(b) 改写。
    """
    workspace = tmp_path / "ws"
    init_workspace(workspace)

    for name in ("filesystem.py", "commandline.py", "webfetch.py", "__init__.py"):
        assert (workspace / "tools" / name).is_file(), name
    assert (workspace / "tools" / "README.md").is_file()

    # 除本 Phase 新增的 6 个 ``.py`` 文件外无其它 ``.py`` 文件
    python_files = {p.relative_to(workspace).as_posix() for p in workspace.rglob("*.py")}
    assert python_files == {
        "tools/__init__.py",
        "tools/changes.py",
        "tools/filesystem.py",
        "tools/commandline.py",
        "tools/webfetch.py",
        "skills/example/scripts/example.py",
    }

    # 持久不变量：工作区内无**智能体入口文件** —— Skill 第三层演示脚本获
    # 宪法 §6.3 例外 E-02 + §5 章 [D-19] 授权，**不计入**该不变量的违例
    # （spec FR-050 / FR-068(b)）。
    file_names = {p.name for p in workspace.rglob("*") if p.is_file()}
    assert "agent.py" not in file_names
    assert "main.py" not in file_names

    # MUST 无子智能体相关目录
    directories = {p.name.lower() for p in workspace.rglob("*") if p.is_dir()}
    assert not directories & {"agents", "subagent", "subagents"}

    # 文本内容 MUST 无子智能体相关字段名，且 MUST 无任何可观测性后端形态
    for path in workspace.rglob("*"):
        if not path.is_file() or path.suffix == ".sqlite3":
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert "subagent" not in text, path
        assert "agents/" not in text, path
        assert not _OBSERVABILITY_NEEDLE.search(text), path


def test_init_does_not_validate_provider_content(tmp_path: Path) -> None:
    """T057 / US12 / SC-011：init 阶段 0 次校验工作区内的配置内容。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    (workspace / "providers" / "default.toml").write_text(
        "这不是合法的 TOML {{{", encoding="utf-8"
    )

    result = init_workspace(workspace)

    assert result.templates_loaded == 54
    # 故意损坏的内容原样保留（init 不做内容判定）
    assert (workspace / "providers" / "default.toml").read_text(encoding="utf-8") == (
        "这不是合法的 TOML {{{"
    )


def test_force_rebuilds_sqlite_and_clears_metadata(tmp_path: Path) -> None:
    """T059 / US13：强制标志重建记忆库，会话元数据表记录数归 0。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    db_path = workspace / "memory" / "sessions.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO sessions_metadata "
        "(thread_id, title, created_at, updated_at, donkey_version, first_prompt) "
        "VALUES ('t1', '标题', 1.0, 2.0, '0.1.0', '首轮')"
    )
    conn.commit()
    conn.close()

    init_workspace(workspace, force=True)

    tables, _indexes, count = _tables_and_indexes(db_path)
    assert {"checkpoints", "writes", "sessions_metadata"} <= tables
    assert count == 0


def test_sessions_sqlite_full_schema_with_indexes(tmp_path: Path) -> None:
    """T063 / US14 / SC-006：短期记忆库三表两索引齐备、记录数为 0。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)

    tables, indexes, count = _tables_and_indexes(workspace / "memory" / "sessions.sqlite3")

    assert {"checkpoints", "writes", "sessions_metadata"} <= tables
    assert "idx_sessions_metadata_title" in indexes
    assert "idx_sessions_metadata_updated_at" in indexes
    assert count == 0


def test_memory_sqlite_templates_exist_and_placeholders_empty(tmp_path: Path) -> None:
    """T064 / US14 / SC-006：三个 sqlite3 文件就位，两个占位文件 0 表 0 索引。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)

    for name in ("sessions.sqlite3", "store.sqlite3", "knowledge.sqlite3"):
        assert (workspace / "memory" / name).is_file(), name

    for name in ("store.sqlite3", "knowledge.sqlite3"):
        conn = sqlite3.connect(str(workspace / "memory" / name))
        try:
            table_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            index_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert table_count == 0, name
        assert index_count == 0, name


def test_init_after_rename_keeps_old_name(tmp_path: Path) -> None:
    """T084 / 澄清 #27：工作区被重命名后，非强制 init 保留旧名且不报错。"""
    workspace = tmp_path / "old_name"
    init_workspace(workspace)
    renamed = tmp_path / "new_name"
    workspace.rename(renamed)

    result = init_workspace(renamed)

    # 命令成功（退出码 0 的等价物），MUST NOT 触发退出码 3
    assert result.name == "new_name"
    manifest = read_workspace_manifest(renamed)
    assert manifest is not None
    assert manifest["name"] == "old_name"
    assert "old_name" in (renamed / "README.md").read_text(encoding="utf-8")


def test_memory_readme_template_content(tmp_path: Path) -> None:
    """T091 / FR-052 / SC-018：记忆库说明文档含三库文件名、--force 与备份命令示例。"""
    content = (DEFAULT_TEMPLATES_ROOT / "memory" / "README.md.txt").read_text(encoding="utf-8")

    for name in ("sessions.sqlite3", "store.sqlite3", "knowledge.sqlite3"):
        assert name in content, name
    assert "--force" in content
    # 可执行的备份命令示例 MUST 覆盖三个库（MUST NOT 只给单文件）
    assert "cp memory/*.sqlite3" in content
    assert "仅占位空文件" in content
    assert "schema 推迟到后续版本" in content
    assert "运行数据可选择性导出" in content


def test_exit_code_set_is_exactly_0_to_4() -> None:
    """T074 / FR-037 / SC-010 / SC-021：本阶段使用的退出码集合恰为 {0, 1, 2, 3, 4}。"""
    import tomllib

    from donkey.cli import cli_client
    from donkey.core import exit_codes
    from donkey.core.exceptions import WorkspaceInitError

    module_vars = vars(exit_codes)
    int_constants = {
        name: value
        for name, value in module_vars.items()
        if name.startswith("EXIT_CODE_")
        and isinstance(value, int)
        and not isinstance(value, bool)
    }
    # 段位元组（值为 tuple）MUST NOT 计入本断言
    segment_constants = {
        name: value
        for name, value in module_vars.items()
        if name.startswith("EXIT_CODE_SEGMENT_")
    }
    assert segment_constants
    assert all(isinstance(value, tuple) for value in segment_constants.values())

    # ① 本阶段**实际使用**的退出码恰为 {0, 1, 2, 3, 4}
    used = {exit_codes.EXIT_CODE_OK} | set(cli_client._EXCEPTION_TO_EXIT_CODE.values())
    assert used == {0, 1, 2, 3, 4}
    assert set(int_constants) - {"EXIT_CODE_BUILTIN_TOOL_GENERATION"} == {
        "EXIT_CODE_OK",
        "EXIT_CODE_PATH_NOT_FOUND",
        "EXIT_CODE_PATH_PERMISSION",
        "EXIT_CODE_TEMPLATE_GENERATION",
    }

    # ② 映射表登记的码值集合恰为 {1, 2, 3, 4}；基类不登记（未登记子类兜底 1）
    assert set(cli_client._EXCEPTION_TO_EXIT_CODE.values()) == {1, 2, 3, 4}
    assert WorkspaceInitError not in cli_client._EXCEPTION_TO_EXIT_CODE

    # ③ 退出码 4 已在本阶段启用（内置工具生成失败）；5-10 未定义
    assert exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION == 4
    assert exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION in used
    assert not any(5 <= value <= 10 for value in int_constants.values())

    # ④ 运行期依赖恰为 1 个 —— 上游 saver 包
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    dependencies = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["dependencies"]
    assert len(dependencies) == 1
    assert dependencies[0].startswith("langgraph-checkpoint-sqlite")


# --- spec Edge Cases 段的边界断言（补齐"已实现但无断言落点"的 MUST）-------------


def test_missing_template_manifest_raises_template_error(tmp_path: Path) -> None:
    """Edge Case「注入的清单路径指向不存在的目录」→ exit 3（权威分类法 ①）。

    清单**缺失** MUST 与"JSON 非法"同归模板生成类错误 —— 用户修复动作是
    "重装 donkey"，与路径类错误（建目录 / 换路径）不同（spec FR-002 / FR-038）。
    """
    missing = tmp_path / "no-such-dir" / "manifest.json"

    with pytest.raises(TemplateGenerationError) as excinfo:
        load_template_manifest(missing)

    assert "下一步" in str(excinfo.value)
    assert "manifest.json" in str(excinfo.value)


def test_sqlite3_construction_failure_maps_to_exit_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge Case「sqlite3 结构构造失败」→ exit 3（权威分类法 ⑤）。

    构造失败 MUST 统一包成 ``TemplateGenerationError``，MUST NOT 以裸
    ``sqlite3.Error`` 逃逸（spec FR-033 / FR-014）。
    """
    import sqlite3 as _sqlite3

    def _boom(*args: object, **kwargs: object) -> object:
        raise _sqlite3.OperationalError("simulated sqlite3 failure")

    monkeypatch.setattr(_sqlite3, "connect", _boom)

    with pytest.raises(TemplateGenerationError) as excinfo:
        build_sessions_sqlite(tmp_path / "sessions.sqlite3")

    assert "下一步" in str(excinfo.value)


def test_upstream_saver_import_failure_maps_to_exit_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge Case「上游 saver 包缺失 / 导入失败」→ exit 3（权威分类法 ⑥）。

    上游 saver 缺失时 MUST NOT 静默跳过那两张表（否则 init 结束时结构不完整，
    用户拿到的是半成品空库）；MUST 表现为退出码 ``3``（spec FR-014 / FR-031）。
    """
    import sys

    # ``sys.modules[name] = None`` ⇒ 该模块的 import 抛 ImportError
    # （模拟"上游 saver 包未安装 / 不可导入"）。
    monkeypatch.setitem(sys.modules, "langgraph.checkpoint.sqlite", None)

    with pytest.raises(TemplateGenerationError) as excinfo:
        build_sessions_sqlite(tmp_path / "sessions.sqlite3")

    assert "下一步" in str(excinfo.value)


def test_force_delete_failure_maps_to_exit_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Edge Case「只读目标文件」→ force 下删除失败 MUST 归 exit 3。

    非 force 模式下只读文件 MUST 跳过、不报错（已由
    ``test_render_skip_existing_no_force`` 覆盖）；force 模式下删除失败 MUST
    抛模板生成类错误（spec Edge Cases「渲染与幂等类」）。
    """
    root = _make_templates_root(
        tmp_path,
        [{"path": "instruction.md", "format": "markdown"}],
        {"instruction.md": "出厂内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    target = workspace / "instruction.md"
    target.write_text("用户改写的内容", encoding="utf-8")
    entries = load_template_manifest(root / "manifest.json")

    original_unlink = Path.unlink

    def _boom(self: Path, *args: object, **kwargs: object) -> None:
        if self.name == "instruction.md":
            raise PermissionError(13, "Permission denied")
        original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "unlink", _boom)

    with pytest.raises(TemplateGenerationError) as excinfo:
        render_templates(workspace, "ws", True, entries, root)

    assert "下一步" in str(excinfo.value)


def test_manifest_order_does_not_affect_result(tmp_path: Path) -> None:
    """Edge Case「清单条目顺序被打乱」→ MUST NOT 影响结果（spec FR-012）。"""
    entries_spec: list[dict[str, object]] = [
        {"path": "providers/default.toml", "format": "toml"},
        {"path": "mcp/mcp.json", "format": "json"},
        {"path": "instruction.md", "format": "markdown"},
        {"path": "skills/example/SKILL.md", "format": "markdown"},
    ]
    sources = {
        "providers/default.toml": "默认配置",
        "mcp/mcp.json": "{}",
        "instruction.md": "提示词",
        "skills/example/SKILL.md": "技能",
    }

    # 顺序 A：文件条目排在目录条目之前（与"目录条目在前"相对）
    root_a = _make_templates_root(tmp_path / "a", entries_spec, sources)
    ws_a = tmp_path / "ws-a"
    ws_a.mkdir()
    render_templates(ws_a, "ws", False, load_template_manifest(root_a / "manifest.json"), root_a)

    # 顺序 B：条目顺序完全打乱
    shuffled = list(reversed(entries_spec))
    root_b = _make_templates_root(tmp_path / "b", shuffled, sources)
    ws_b = tmp_path / "ws-b"
    ws_b.mkdir()
    render_templates(ws_b, "ws", False, load_template_manifest(root_b / "manifest.json"), root_b)

    def _tree(ws: Path) -> dict[str, str]:
        return {
            str(p.relative_to(ws)): p.read_text(encoding="utf-8")
            for p in ws.rglob("*")
            if p.is_file()
        }

    assert _tree(ws_a) == _tree(ws_b)
    assert "instruction.md" in _tree(ws_a)


def test_force_removes_sqlite_sidecar_files(tmp_path: Path) -> None:
    """Edge Case「force 重建 sqlite3 时遗留的 -wal / -shm」→ MUST 连带删除。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    db_path = workspace / "memory" / "sessions.sqlite3"
    wal = Path(f"{db_path}-wal")
    shm = Path(f"{db_path}-shm")
    wal.write_bytes(b"stale-wal")
    shm.write_bytes(b"stale-shm")

    init_workspace(workspace, force=True)

    assert not wal.exists()
    assert not shm.exists()
    assert db_path.is_file()


def test_deleted_memory_template_is_recreated(tmp_path: Path) -> None:
    """Edge Case「用户手工把记忆库文件删了」→ 再次 init MUST 重建它。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    db_path = workspace / "memory" / "sessions.sqlite3"
    db_path.unlink()

    init_workspace(workspace)

    assert db_path.is_file()
    tables, _indexes, count = _tables_and_indexes(db_path)
    assert {"checkpoints", "writes", "sessions_metadata"} <= tables
    assert count == 0


def test_broken_memory_template_preserved_without_force(tmp_path: Path) -> None:
    """Edge Case「记忆库被改成非 sqlite3 文本」→ 非 force MUST 原样保留、不报错。

    init 阶段 MUST NOT 做 schema 健康检查 —— 那是配置检查阶段的职责（属另一
    码段，spec FR-063）。
    """
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    db_path = workspace / "memory" / "store.sqlite3"
    db_path.write_text("这不是 sqlite3 文件", encoding="utf-8")

    result = init_workspace(workspace)

    assert result.templates_loaded == 54
    assert db_path.read_text(encoding="utf-8") == "这不是 sqlite3 文件"


def test_memory_non_manifest_files_preserved_under_force(tmp_path: Path) -> None:
    """Edge Case「memory/ 下的非清单文件」→ 原样保留，force 也不得触碰。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    notes = workspace / "memory" / "notes.md"
    notes.write_text("用户的笔记", encoding="utf-8")
    old_db = workspace / "memory" / "old.sqlite3"
    old_db.write_text("旧库", encoding="utf-8")

    init_workspace(workspace, force=True)

    assert notes.read_text(encoding="utf-8") == "用户的笔记"
    assert old_db.read_text(encoding="utf-8") == "旧库"


def test_deleted_workspace_manifest_is_recreated(tmp_path: Path) -> None:
    """Edge Case「用户手工删掉工作区根的 manifest.json」→ 再次 init MUST 重建。"""
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    manifest_file = workspace / WORKSPACE_MANIFEST_FILENAME
    manifest_file.unlink()

    init_workspace(workspace)

    assert manifest_file.is_file()
    manifest = read_workspace_manifest(workspace)
    assert manifest is not None
    assert manifest["name"] == workspace.name


def test_manifest_top_level_not_object_raises(tmp_path: Path) -> None:
    """清单顶层不是对象 → 模板生成类错误（data-model §2 的 schema 校验）。"""
    root = tmp_path / "templates"
    root.mkdir()
    (root / "manifest.json").write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(TemplateGenerationError):
        load_template_manifest(root / "manifest.json")


def test_workspace_manifest_not_json_object_raises(tmp_path: Path) -> None:
    """工作区清单内容不是 JSON 对象 → 模板生成类错误（spec FR-018）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / WORKSPACE_MANIFEST_FILENAME).write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(TemplateGenerationError):
        read_workspace_manifest(workspace)


def test_unknown_format_entry_raises(tmp_path: Path) -> None:
    """FR-003：未登记的格式值 MUST 按模板生成类错误处理，MUST NOT 被静默忽略。

    ``render_templates`` 是**公开 API** —— 入参未必经 loader 校验，故渲染层
    MUST 自行兜住未知格式值。
    """
    root = _make_templates_root(
        tmp_path,
        [{"path": "doc.md", "format": "markdown"}],
        {"doc.md": "内容"},
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    # 绕过 loader —— 直接给渲染层一个未登记的格式值（loader 本身已拦一道）。
    entries = [{"path": "doc.md", "format": "yaml"}]

    with pytest.raises(TemplateGenerationError) as excinfo:
        render_templates(workspace, "ws", False, entries, root)

    assert "下一步" in str(excinfo.value)


def test_entry_without_path_raises(tmp_path: Path) -> None:
    """FR-002：条目缺 ``path`` → 模板生成类错误（渲染层兜底）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    with pytest.raises(TemplateGenerationError):
        render_templates(workspace, "ws", False, [{"format": "markdown"}], tmp_path)


def test_entry_path_escaping_workspace_root_raises(tmp_path: Path) -> None:
    """条目路径越出 workspace 根 → 模板生成类错误（父目录创建限定在根之下）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    entries = [{"path": "../outside.md", "format": "markdown"}]

    with pytest.raises(TemplateGenerationError):
        render_templates(workspace, "ws", False, entries, tmp_path)

    assert not (tmp_path / "outside.md").exists()


def test_unknown_sqlite3_entry_raises(tmp_path: Path) -> None:
    """未登记的 sqlite3 模板条目 → 模板生成类错误（无对应构造器）。"""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    entries = [{"path": "memory/unknown.sqlite3", "format": "sqlite3"}]

    with pytest.raises(TemplateGenerationError):
        render_templates(workspace, "ws", False, entries, tmp_path)
