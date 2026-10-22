"""``donkey.core.api.init_workspace`` 的单元测试（core 层）。

本文件被 7 个用户故事共用，每个故事在**同一个测试函数内**扩写断言组，
不新增测试函数——core 层的测试函数总数恒为 17（见 tasks.md 口径说明）。
"""

import os
from pathlib import Path

import pytest

from donkey.core.api import init_workspace
from donkey.core.exceptions import PathNotFoundError, PathPermissionError
from donkey.core.workspace.init import check_path, check_permission

#: 模板资产 MUST 由**仓库源树**定位——若以非 editable 方式安装，改名会落到
#: site-packages 上（污染环境或因只读而失败）。
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "donkey" / "core" / "workspace" / "templates"


def test_init_workspace_creates_root_dir(tmp_path: Path) -> None:
    """US1：全新路径 → 根目录被创建，三个计数恒为 0，路径为绝对路径。"""
    target = tmp_path / "ws"

    result = init_workspace(target)

    assert target.is_dir()
    assert result.workspace_path.is_absolute()
    assert result.workspace_path == target
    assert result.name == "ws"
    assert result.templates_loaded == 0
    assert result.files_created == 0
    assert result.files_skipped == 0

    # 追加断言组：path MUST 接受字符串与路径对象两种形态（spec FR-005），
    # 两者均成功且 workspace_path 均为绝对路径。
    target_from_str = tmp_path / "ws-str"

    result_from_str = init_workspace(str(target_from_str))

    assert target_from_str.is_dir()
    assert result_from_str.workspace_path.is_absolute()
    assert result_from_str.workspace_path == target_from_str
    assert result_from_str.name == "ws-str"


def test_check_path_nonexistent_parent(tmp_path: Path) -> None:
    """US2：父目录不存在 → 路径类错误，且缺失的父目录 MUST NOT 被创建。"""
    missing_parent = tmp_path / "missing"
    target = missing_parent / "ws"

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path(target)

    message = str(excinfo.value)
    assert "父目录不存在" in message
    assert str(missing_parent) in message
    # 追加断言组：抛错后该缺失父目录仍不存在（spec US2 场景 1 / SC-003）。
    assert not missing_parent.exists()
    assert not target.exists()


def test_check_path_resolve_relative(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """US2：相对路径在 cwd 下父目录不存在 → 路径类错误。"""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path("missing/ws")

    assert "父目录不存在" in str(excinfo.value)
    assert not (tmp_path / "missing").exists()


def test_check_path_root_path() -> None:
    """US2：文件系统根 → 末段名为空 → 路径类错误。"""
    with pytest.raises(PathNotFoundError) as excinfo:
        check_path("/")

    message = str(excinfo.value)
    assert "根目录" in message


def test_check_path_nul_character(tmp_path: Path) -> None:
    """US2：路径含 NUL 字节 → 路径类错误（``resolve()`` 抛的是 ``ValueError``）。"""
    target = tmp_path / "bad\x00name"

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path(str(target))

    message = str(excinfo.value)
    assert "非法字符" in message


def test_check_path_target_is_file_or_parent_is_file_or_empty_path(tmp_path: Path) -> None:
    """US2：目标为普通文件 / 父目录为文件 / 空路径 —— 由同一个用例一并覆盖。"""
    target_file = tmp_path / "target.txt"
    target_file.write_text("user content", encoding="utf-8")

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path(target_file)

    assert "不是目录" in str(excinfo.value)
    # MUST NOT 覆盖该文件。
    assert target_file.read_text(encoding="utf-8") == "user content"

    parent_file = tmp_path / "parent.txt"
    parent_file.write_text("user content", encoding="utf-8")

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path(parent_file / "ws")

    assert "父目录" in str(excinfo.value)
    assert parent_file.read_text(encoding="utf-8") == "user content"

    with pytest.raises(PathNotFoundError) as excinfo:
        check_path("")

    assert "不能为空" in str(excinfo.value)


def test_check_permission_readonly_parent(tmp_path: Path) -> None:
    """US3：只读父目录（0o555）→ 权限类错误，指明缺失的权限种类与对应路径。

    权限模拟 MUST NOT 依赖特权账号——``0o555`` 目录不含任何写位，按 POSIX
    语义即使以 root 运行 ``os.access(dir, W_OK)`` 亦为 False（research.md R-04）。
    """
    readonly_parent = tmp_path / "ro"
    readonly_parent.mkdir()
    target = readonly_parent / "ws"

    try:
        os.chmod(readonly_parent, 0o555)

        with pytest.raises(PathPermissionError) as excinfo:
            check_permission(target)

        message = str(excinfo.value)
        assert "写权限" in message
        assert str(readonly_parent) in message
        # 一条用户可执行的下一步（调整权限）。
        assert "调整权限" in message
    finally:
        os.chmod(readonly_parent, 0o755)


def test_check_permission_existing_missing_read(tmp_path: Path) -> None:
    """US3：已存在目录缺读位（0o333）→ 权限类错误。"""
    existing = tmp_path / "existing"
    existing.mkdir()

    try:
        os.chmod(existing, 0o333)

        with pytest.raises(PathPermissionError) as excinfo:
            check_permission(existing)

        message = str(excinfo.value)
        assert "读权限" in message
        assert str(existing) in message
        assert "调整权限" in message
    finally:
        os.chmod(existing, 0o755)


def test_check_permission_ok(tmp_path: Path) -> None:
    """US3：正常路径 → 权限校验通过（正常返回 ``None``，不抛异常）。"""
    target = tmp_path / "ws"

    # 契约的返回类型就是 ``None``（contracts/library-api.md §3）——权限充足时
    # "正常返回"，此处断言其返回值确为 ``None``。
    assert check_permission(target) is None  # type: ignore[func-returns-value]


def test_init_workspace_existing_is_not_error(tmp_path: Path) -> None:
    """US4：已存在的 workspace → 不是错误，且已有内容不被改动。"""
    existing = tmp_path / "ws"
    existing.mkdir()
    user_file = existing / "user.txt"
    user_file.write_text("user content", encoding="utf-8")
    before_stat = user_file.stat()

    result = init_workspace(existing)

    assert result.files_created == 0
    assert result.files_skipped == 0
    assert result.templates_loaded == 0
    assert result.workspace_path == existing
    assert user_file.read_text(encoding="utf-8") == "user content"
    after_stat = user_file.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert after_stat.st_size == before_stat.st_size


def test_init_workspace_force_recorded_not_applied(tmp_path: Path) -> None:
    """US5：``force=True`` → 被记录并回显，但本阶段不触发任何重置。"""
    existing = tmp_path / "ws"
    existing.mkdir()
    user_file = existing / "user.txt"
    user_file.write_text("user content", encoding="utf-8")
    before_stat = user_file.stat()

    result = init_workspace(existing, force=True)

    assert result.force is True
    assert result.workspace_path == existing
    # 目录内容不变（未发生重置）。
    assert user_file.read_text(encoding="utf-8") == "user content"
    assert user_file.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert sorted(p.name for p in existing.iterdir()) == ["user.txt"]


def test_init_workspace_does_not_load_manifest(tmp_path: Path) -> None:
    """US6：模板清单 / 模板源缺失 MUST NOT 导致失败，且目标目录内无任何文件。"""
    manifest = TEMPLATES_DIR / "manifest.json"
    manifest_backup = TEMPLATES_DIR / "manifest.json.bak"
    source = TEMPLATES_DIR / "instruction.md.txt"
    source_backup = TEMPLATES_DIR / "instruction.md.txt.bak"

    try:
        os.rename(manifest, manifest_backup)

        result = init_workspace(tmp_path / "ws-without-manifest")

        assert result.templates_loaded == 0
        assert result.files_created == 0
        assert result.files_skipped == 0
        assert list((tmp_path / "ws-without-manifest").iterdir()) == []

        # 追加覆盖：模板源占位缺失同样不导致失败。
        os.rename(source, source_backup)

        result_without_source = init_workspace(tmp_path / "ws-without-source")

        assert result_without_source.templates_loaded == 0
        assert result_without_source.files_created == 0
        assert result_without_source.files_skipped == 0
        assert list((tmp_path / "ws-without-source").iterdir()) == []
    finally:
        if manifest_backup.exists():
            os.rename(manifest_backup, manifest)
        if source_backup.exists():
            os.rename(source_backup, source)


def test_init_workspace_name_from_basename(tmp_path: Path) -> None:
    """US7：名称恒取解析后路径的末段名。"""
    target = tmp_path / "my-agent"

    result = init_workspace(target)

    assert result.name == "my-agent"
    assert result.name == result.workspace_path.name


def test_init_workspace_name_empty_falls_back_to_basename(tmp_path: Path) -> None:
    """US7：库 API 显式传空名 → 视为未指定，回落为末段名。"""
    target = tmp_path / "my-agent"

    result = init_workspace(target, name="")

    assert result.name == "my-agent"


def test_init_workspace_explicit_name_wins(tmp_path: Path) -> None:
    """US7：库 API 显式传非空名 → 以该值为准，但路径仍由 path 决定。"""
    target = tmp_path / "my-agent"

    result = init_workspace(target, name="alice")

    assert result.name == "alice"
    assert result.workspace_path == target


def test_init_workspace_rejects_root_path() -> None:
    """US7：文件系统根 → 末段名为空 → 路径类错误。"""
    with pytest.raises(PathNotFoundError):
        init_workspace("/")


def test_init_workspace_accepts_arbitrary_basename(tmp_path: Path) -> None:
    """US7：末段名含空格 / Unicode → 一律接受，名称原样保留。"""
    target = tmp_path / "我的 工作区"

    result = init_workspace(target)

    assert result.name == "我的 工作区"
    assert result.workspace_path == target

    # 追加断言组：末段名带尾部分隔符 → 名称仍等于末段名（与不带分隔符等价）。
    trailing = tmp_path / "ws-with-trailing-sep"

    result_trailing = init_workspace(f"{trailing}/")

    assert result_trailing.name == "ws-with-trailing-sep"
    assert result_trailing.workspace_path == trailing
