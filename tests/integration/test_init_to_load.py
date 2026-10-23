"""F001-P3 ``builtin_tools`` 的集成测试 —— 初始化产物被**独立进程**导入并调用。

**集成层为何启用**（spec FR-061）：F001-P2 把 ``tests/integration/`` 留空的
理由是"本 Phase 的 2 个新 core 模块由单一流水线串联、无跨模块协作契约" ——
该理由在 F001-P3 **失效**：本 Phase 出现**真正的跨模块协作** ——
``donkey init``（核心层）产出的工作区产物（渲染层）被**独立进程**导入并
调用（用户侧），这正是集成层的定义。

**为何必须用独立子进程**（spec FR-062）：``sys.modules`` 按**模块名**缓存 ——
在测试进程内把工作区路径塞进导入路径后直接导入，第二个场景会拿到**第一个**
工作区的产物 → 验收假绿。故本文件一律用
``subprocess.run([sys.executable, "-c", snippet], cwd=workspace)``：

- 子进程 MUST 用 ``-c`` —— ``-c`` 才把**当前工作目录**放进导入路径，用脚本
  文件则因 ``sys.path[0]`` 是脚本目录而找不到 ``tools`` 包（research.md R-20）；
- 网络拦截 MUST 与导入位于**同一个子进程**内 —— 拦截能力只对当前进程生效
  （spec FR-067 / research.md R-20）。

本层只做"导入路径 + 函数签名 + 一次调用"的预演，MUST NOT 做配置静态格式
检查（那属另一个阶段的职责 —— spec FR-063）。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from donkey.core.api import init_workspace


def _run_in_workspace(workspace: Path, snippet: str) -> subprocess.CompletedProcess[str]:
    """在**工作区目录内**以独立子进程执行一段代码。

    ``-c`` 使当前工作目录进入导入路径 —— 工作区的 ``tools`` 包因此可被导入。
    """
    return subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=120,
    )


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """初始化后的工作区 —— 被测对象。"""
    ws = tmp_path / "ws"
    init_workspace(ws)
    return ws


def test_init_then_import_filesystem_tools(workspace: Path) -> None:
    """``donkey init`` 后 7 个文件工具的 import 语句无异常。"""
    completed = _run_in_workspace(
        workspace,
        "from tools.filesystem import (read_file, write_file, copy_file, "
        "move_file, delete_file, list_dir, stat); print('ok')",
    )

    assert completed.returncode == 0, completed.stderr
    assert "ok" in completed.stdout


def test_init_then_import_commandline_tool_and_call_it(workspace: Path) -> None:
    """``run_shell`` 可导入且调一次 —— 输出含回显内容。"""
    completed = _run_in_workspace(
        workspace,
        "import json\n"
        "from tools.commandline import run_shell\n"
        "result = json.loads(run_shell.invoke({'command': 'echo integration'}))\n"
        "print(result['stdout'])\n",
    )

    assert completed.returncode == 0, completed.stderr
    assert "integration" in completed.stdout


def test_init_then_import_webfetch_tool_and_call_it(workspace: Path) -> None:
    """``fetch_url`` 可导入且调一次 —— 拦截 MUST 与导入同处一个子进程。"""
    completed = _run_in_workspace(
        workspace,
        "import httpx\n"
        "def fake_send(self, request, **kwargs):\n"
        "    return httpx.Response(200, text='mocked body', request=request)\n"
        "httpx.Client.send = fake_send\n"
        "import json\n"
        "from tools.webfetch import fetch_url\n"
        "result = json.loads(fetch_url.invoke({'url': 'https://example.com'}))\n"
        "print(result['status_code'], result['body'])\n",
    )

    assert completed.returncode == 0, completed.stderr
    assert "200" in completed.stdout
    assert "mocked body" in completed.stdout


def test_init_then_import_change_contract(workspace: Path) -> None:
    """契约库可导入、版本为 ``1``，且与文件工具**同批存在**。"""
    completed = _run_in_workspace(
        workspace,
        "from tools.changes import (CHANGE_RECORD_VERSION, atomic_write_bytes, "
        "build_change_record); print(CHANGE_RECORD_VERSION)",
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "1"

    # 同批存在 —— MUST NOT 出现"工具在、契约库不在"的半残工作区。
    assert (workspace / "tools" / "changes.py").is_file()
    assert (workspace / "tools" / "filesystem.py").is_file()
    assert (workspace / "tools" / "commandline.py").is_file()
    assert (workspace / "tools" / "webfetch.py").is_file()
    assert (workspace / "tools" / "__init__.py").is_file()
