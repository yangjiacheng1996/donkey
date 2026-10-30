"""工作区清单的读写能力（F001-P2）。

工作区清单是 workspace **自带**的身份记录，落在 workspace 根目录，文件名
``manifest.json``（宪法 D-01 / §2.6）。它与安装包内的**模板清单**
（``donkey/core/workspace/templates/manifest.json``）是**两个不同的文件** ——
前者记录"这是谁的工作区"，后者记录"donkey 要往工作区里放哪些模板"。

本模块 MUST 与渲染逻辑分离（spec FR-018）—— 它被 F002 / F003 复用为工作区
身份读取能力，故独立成模块而非塞进 ``init.py``。

失败一律以 ``TemplateGenerationError`` 表达（退出码 ``3``）—— 清单内容不可
解析时，用户的修复动作是"重装 donkey / 修内容"，与路径类失败（建目录 / 换
路径）不同，二者 MUST NOT 复用同一码值（spec FR-038）。
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from donkey.core.exceptions import _NEXT_STEP_TEMPLATE, TemplateGenerationError
from donkey.core.version import resolve_version

#: 工作区清单的文件名（落在 workspace 根目录）。
WORKSPACE_MANIFEST_FILENAME = "manifest.json"


def _build_manifest(name: str) -> dict[str, object]:
    """构造一份工作区清单字典。

    字段**恰好且仅**为三项 —— 名字 / 创建时间 / donkey 版本号。

    > **口径变更登记（宪法 [D-21] · 2026-10-30 · Maintainer 裁决）**：
    > - **删除**原"版本号（整数 ``1``）"字段 —— 该字段**无人读取**（包内模板
    >   清单的同名 ``version`` 是另一个文件、另一个含义），且与
    >   ``donkey_version`` 并排时读作"两个打架的版本号"。
    > - ``donkey_version`` 改为**动态取值** —— 原 F001-P2 FR-021 的硬编码
    >   （``"0.1.0"``，理由"MUST NOT 通过导入内部版本符号获取（循环依赖风险）"）
    >   的代价是：版本 bump 后**新建**的工作区仍记旧版本号 → F002
    >   ``donkey load`` 的迁移提示**误判**工作区陈旧。该 FR 自身已预留演进
    >   路径（"将来若改为动态获取，MUST 使用包元数据查询方式"），本次即走该路径
    >   —— ``donkey.core.version`` 正是为此而建的核心层模块，且
    >   ``donkey/__init__.py`` **零 import** → 引用它**不成环**。
    >
    > **存量工作区兼容**：旧工作区的清单里可能仍带 ``"version": 1`` ——
    > 读取端原样返回字典、不解析该键，故**不影响任何读路径**；``--force``
    > 重写时该键被自然清除（归一到三字段形态）。
    """
    return {
        "name": name,
        "created_at": datetime.now(UTC).isoformat(),
        "donkey_version": resolve_version(),
    }


def _dump_manifest(manifest: dict[str, object]) -> str:
    """把清单序列化为人类可读形态：2 空格缩进、非 ASCII 保留原文（spec FR-022）。"""
    return json.dumps(manifest, indent=2, ensure_ascii=False)


def read_workspace_manifest(workspace_path: Path) -> dict[str, object] | None:
    """读取工作区清单。

    返回：清单字典；文件**不存在**时返回 ``None``（表示"无"，spec FR-018）。

    失败：清单内容不是合法 JSON → ``TemplateGenerationError``（退出码 ``3``）。
    """
    manifest_file = Path(workspace_path) / WORKSPACE_MANIFEST_FILENAME
    try:
        raw = manifest_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise TemplateGenerationError(
            f"读取工作区清单失败：{manifest_file}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise TemplateGenerationError(
            f"工作区清单内容不是合法 JSON：{manifest_file}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc

    if not isinstance(parsed, dict):
        raise TemplateGenerationError(
            f"工作区清单内容不是 JSON 对象：{manifest_file}。{_NEXT_STEP_TEMPLATE}"
        )
    return parsed


def write_workspace_manifest(workspace_path: Path, name: str, force: bool) -> dict[str, object]:
    """写入工作区清单。

    判定顺序（spec FR-020 / research.md R-10）：

    1. **带强制标志** → 直接覆盖（**MUST NOT 先读旧文件**），创建时间刷新为
       当前时刻；
    2. **不带强制标志且已存在** → 先读（解析失败 → ``TemplateGenerationError``
       退出码 ``3``）/ 不覆盖、返回既有内容（创建时间保留原值）；
    3. **不存在** → 无条件创建。

    返回：实际落地（或保留）的清单字典。

    写入形态：``json.dumps(indent=2, ensure_ascii=False)`` + UTF-8 无 BOM
    （spec FR-022）。
    """
    manifest_file = Path(workspace_path) / WORKSPACE_MANIFEST_FILENAME

    if not force:
        try:
            exists = manifest_file.exists()
        except OSError as exc:
            raise TemplateGenerationError(
                f"访问工作区清单失败：{manifest_file}（{exc}）。{_NEXT_STEP_TEMPLATE}"
            ) from exc
        if exists:
            existing = read_workspace_manifest(workspace_path)
            if existing is not None:
                return existing

    manifest = _build_manifest(name)
    payload = _dump_manifest(manifest)
    try:
        with open(manifest_file, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except OSError as exc:
        raise TemplateGenerationError(
            f"写入工作区清单失败：{manifest_file}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc
    return manifest


def ensure_workspace_manifest(
    workspace_path: Path, name: str, force: bool
) -> dict[str, object]:
    """确保工作区清单存在（"确保存在"便捷封装）。

    MUST 与 :func:`write_workspace_manifest` **严格等价** —— 委托同一实现、
    同一判定顺序（spec FR-023 / research.md R-10）：带强制标志时直接覆盖、
    MUST NOT 先读旧文件；不带强制标志时先读 —— 文件不存在则创建、已存在且
    解析成功则不覆盖并返回既有内容、已存在但解析失败则抛模板生成类错误
    （退出码 ``3``）。
    """
    return write_workspace_manifest(workspace_path, name, force)
