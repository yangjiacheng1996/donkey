# 契约：客户端与库 API 表面（F001-P3）

**版本**：v1（本 Phase 的改动面 = **3 处** + **1 处编排层豁免**）
**所有者**：`donkey/cli/cli_client.py` + `donkey/core/api.py` + `donkey/core/workspace/init.py`
**上游**：[spec.md](../spec.md) FR-070 / FR-073 / FR-087 / FR-088 / FR-105；[research.md](../research.md) R-07 / R-10

---

## 1. 本 Phase 的改动面总览

| # | 改动 | 文件 | 类型 |
|---|---|---|---|
| 1 | 异常映射表**追加一行**（`BuiltinToolGenerationError` → `4`） | `donkey/cli/cli_client.py` | 客户端 |
| 2 | 退出码常量 `4` 的文档串改为"本阶段启用"（常量**已由 P1 建档**） | `donkey/core/exit_codes.py` | 核心（仅文档串） |
| 3 | **新增异常类** `BuiltinToolGenerationError(WorkspaceInitError)`（**本 Phase 唯一新增的异常类** —— 见 §5） | `donkey/core/exceptions.py` | 核心（追加 1 个类） |
| 4 | `init_workspace_inner` 步骤 ④ 增加**一条**条目级强制重置豁免（契约库） | `donkey/core/workspace/init.py` | 核心（编排层，6 行） |

> **计数口径**：本 Phase 的真实改动 = **4 处**（本表 4 行）—— 前 3 处是**核心 / 客户端**的追加式改动，第 4 处是**唯一**的编排层豁免（唯一例外，spec FR-105 / FR-069）。

**MUST NOT 改动**（spec FR-070 / FR-088）：
- `donkey/core/api.py` 的 `init_workspace` 门面函数体；
- `donkey/core/workspace/init.py` 的 `render_templates` / `load_template_manifest` / `validate_init_request` / `check_path` / `check_permission`；
- `donkey/core/workspace/manifest.py` / `sqlite3_templates.py`；
- 客户端的**任何其它**行为（不新增输出 / 不改摘要 / 不改 `--help` 文案）。

---

## 2. 库 API（本 Phase 不动）

```python
# donkey/core/api.py —— F001-P2 已冻结，本 Phase 一字不改
def init_workspace(path: str | Path, name: str | None = None, force: bool = False) -> InitResult
```

`InitResult` 的字段集合、顺序与类型（`workspace_path` / `name` / `force` / `templates_loaded` / `files_created` / `files_skipped`）**冻结不动**（P2 的 FR-025）→ 三端（cli / web / gui）复用同一门面。

---

## 3. `init_workspace_inner` 的契约变化（**唯一**的编排层改动）

```python
def init_workspace_inner(path, name, force) -> tuple[Path, str, bool, list[InitItem], int]
    #  ① validate_init_request      （P1，不动）
    #  ② load_template_manifest     （P2，不动）→ 54 条
    #  ③ abs_path.mkdir             （P1，不动）
    #  ④ render_templates           （P2，不动）→ ★ 本 Phase 在此处加豁免
    #  ⑤ write_workspace_manifest   （P2，不动）
```

### 3.1 步骤 ④ 的豁免逻辑（R-07）

```text
若 force 且 契约库路径已存在于 workspace:
    entries_for_render = [e for e in manifest_entries if e["path"] != "tools/changes.py"]
    items = render_templates(abs_path, name, force, entries_for_render)
    items.append(InitItem(path="tools/changes.py", kind="file", action="skipped"))
                                        # 契约库被保留 → 计入 skipped（逐项明细）
否则:
    items = render_templates(abs_path, name, force, manifest_entries)
```

> **口径变更登记（宪法 [D-22] · 2026-10-30）**：`render_templates` 现返回**逐项明细**
> `list[InitItem]`（`path` / `kind` / `action`），各计数由明细**投影**而来（**单一真相源**）——
> 原先返回 `(files_created, files_skipped)` 两个计数。豁免逻辑本身（只豁免契约库**一个**条目）
> **未变**。

**约束**：
- MUST 只豁免**契约库一个**条目 —— P2 的通用通则对其余条目**原样成立**（spec FR-069）；
- `templates_loaded` MUST 仍为**原始条目总数 54**（豁免**不**改这个口径 —— 契约库条目仍在清单里）；
- 契约库**不存在**时 MUST 按出厂内容正常创建（与"无则增"通则一致）。

### 3.2 计数口径（契约的权威表）

> **口径变更登记（2026-10-30 · 宪法 [D-22] · Maintainer 裁决）**：计数改为按
> 「**操作对象**（文件 / 目录）× **动作**（新建 / 覆盖 / 跳过）」分解 —— 原表把
> `--force` 的**覆盖**并入 `files_created`，"新建"与"覆盖"不可区分；FR-006 的字面口径是
> 「本次**新建**文件数」，故此处**归位**，`files_created` 在 `--force` 情形为 **0**。
> 该表被 F001-P4 的 tasks T032 引为**当前权威计数源**，MUST 与实现保持一致。

| 场景 | `templates_loaded` | `files_created` | `files_overwritten` | `files_skipped` | `dirs_created` | `dirs_skipped` |
|---|---|---|---|---|---|---|
| 全新创建 | **54** | **48** | 0 | **0** | **6** | 0 |
| 二次 init（非强制） | 54 | **0** | 0 | **48** | 0 | **6** |
| `--force`（契约库已存在） | 54 | **0** | **47** | **1** | 0 | **6** |

> **算术自洽**：`templates_loaded` == 五类计数之和（54 = 48 + 0 + 0 + 6 + 0）。
>
> **目录条目**：**永不**"覆盖"（既有目录一律保留不动）；其"新建 / 跳过"以**本次运行开始前**的
> 存在状态判定（否则目录会被其**子条目**的父目录创建提前建出 → 结果依赖清单顺序）。
>
> **与 P2 的差异**：P2 是 `46 / 40 / 0`（全新）；P3 的 54 = 46 + 8 条追加，文件型 48 = 40 + 8
> （**历史**口径，P2 阶段的 `46 / 40` 保持不动）。

---

## 4. 客户端的异常映射

```python
# donkey/cli/cli_client.py —— 本 Phase 只追加一行
_EXCEPTION_TO_EXIT_CODE = {
    ...既有...,
    BuiltinToolGenerationError: EXIT_CODE_BUILTIN_TOOL_GENERATION,   # ← 新增（exit 4）
}
```

**约束**：
- MUST 由**单一全局映射表**驱动（按类型查表自动生效），MUST NOT 新增分支逻辑（spec FR-073）；
- MUST NOT 因本 Phase 引入任何智能体框架的导入（宪法 N-04）—— 客户端**零新增 import**；
- 映射表的取值 MUST 来自 `donkey/core/exit_codes.py` 的常量，MUST NOT 内联字面量 `4`。

---

## 5. 新增异常类的契约

```python
# donkey/core/exceptions.py
class BuiltinToolGenerationError(WorkspaceInitError):
    """内置工具生成失败。

    退出码：``4``（``EXIT_CODE_BUILTIN_TOOL_GENERATION``）。

    失败成因的**权威分类法**见
    [contracts/exit-codes.md](...) §3 的两类成因表。本类 MUST NOT 自行复述该表。
    """
```

**约束**：
- MUST 归属 `WorkspaceInitError` 之下（spec FR-071）；
- MUST 标注退出码 `4`；
- MUST **引用**权威分类法，MUST NOT 自造第 2 份副本；
- MUST NOT 自行返回退出码 / 打印 / 退出进程（宪法 N-05）。

**配套常量**（同模块，避免循环 import —— P2 的 R-12 教训）：

```python
_NEXT_STEP_BUILTIN = "下一步：请重装 donkey，或检查目标目录的写权限后重试 init。"
```

---

## 6. 退出码常量的激活

```python
# donkey/core/exit_codes.py —— 常量已由 P1 建档，本 Phase 只改文档串
EXIT_CODE_BUILTIN_TOOL_GENERATION = 4   # ← 值不动，文档串由"属 F001-P3，本阶段不触发"
                                         #    改为"本阶段启用（F001-P3）"
```

**MUST NOT** 重复定义该常量（避免第 2 份真相源，R-10）。

---

## 7. CI 工作流文件（客户端之外的仓库级交付物）

**路径**：`.github/workflows/ci.yml`（**新建** —— 宪法 §6.3 临时例外 E-01 到期闭合）

**MUST 含的四类命令**（spec FR-065，e2e 第 16 个断言会实测）：

```yaml
- run: pytest tests/                                              # 全量
- run: pytest tests/unit/ --cov=donkey.core --cov-fail-under=80  # 覆盖率
- run: ruff check donkey/ tests/                                   # 代码规范
- run: mypy donkey/ tests/                                         # 类型检查
```

**约束**：
- 覆盖率 MUST 用**独立命令**度量，MUST NOT 写入 pytest 全局 `addopts`（否则 e2e 单独跑时不 import 业务代码会把覆盖率拉到 0 而误报 —— P2 的 R-13）；
- Python 版本矩阵 MUST 覆盖 **3.11 与 3.12**（`requires-python = ">=3.11"`）；
- MUST 在装包**之后**跑门禁冒烟（quickstart §1）。

---

## 8. 依赖变更

```toml
# pyproject.toml —— 本 Phase 唯一的依赖改动
[project.optional-dependencies]
dev = ["pytest>=7", "pytest-cov", "ruff", "mypy", "pytest-httpx>=0.35"]
```

**约束**：
- `pytest-httpx` MUST **NOT** 进 `[project].dependencies` —— donkey 自身的运行期依赖 MUST 仍恰为 **1** 个（spec FR-080 / SC-015）；
- `[tool.setuptools.package-data]` MUST NOT 改动（R-09）；
- 其余配置（ruff / mypy / pytest）MUST NOT 改动 —— 本 Phase 的模板正文是 `.txt`，**不在** ruff / mypy 的检查口径内（R-08），故静态检查配置无需调整。
