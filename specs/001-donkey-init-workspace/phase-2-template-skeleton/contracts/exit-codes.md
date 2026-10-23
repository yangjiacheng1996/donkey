# 契约：退出码与异常映射（F001-P2）

**版本**：v1.1（F001-P1 冻结的 v1.0 上启用码值 `3`）
**所有者**：`donkey/core/exit_codes.py`（常量）+ `donkey/core/exceptions.py`（异常类）+ `donkey/cli/cli_client.py`（映射表）
**上游**：[spec.md](../spec.md) FR-035 ~ FR-038、FR-063 ~ FR-069；宪法 §4.4 段位表

---

## 1. 段位总表（宪法 §4.4，全局不重叠）

| 段位 | 归属 | 本 Phase |
|---|---|---|
| `0` | 全子命令 | 使用 |
| `1-10` | `donkey init`（F001） | **本 Phase 占子段 1-2 = `1-3`** |
| `11-20` | `donkey load`（F002） | 不涉及 |
| `21-30` | `donkey session`（F003） | 不涉及 |
| `31-100` | `donkey run`（F004） | 不涉及 |
| `101-170` | `donkey web`（F005） | 不涉及 |
| `171-200` | `donkey gui`（F006） | 不涉及 |
| `201+` | v2 / v3 / v4+ | 预留 |

---

## 2. F001 段位内的码值分配

| 码值 | Error class | 触发条件 | 修复动作（"下一步"） | 状态 |
|---|---|---|---|---|
| `0` | — | 成功 | — | 本 Phase 使用 |
| `1` | `PathNotFoundError` | 父目录不存在 / 非法字符 / 末段名为空（根）/ 空路径 / 目标不是目录 / 父目录是文件 / 悬空链接 / 路径过长 / **参数用法错误** | 建目录 / 换路径 | P1 建立，本 Phase 不变 |
| `2` | `PathPermissionError` | 写位 / 执行位 / 读位缺失（**前置校验阶段与工作区根目录创建阶段**） | 调整权限 | P1 建立，本 Phase 不变 |
| `3` | `TemplateGenerationError` | 模板骨架生成失败（**7 类合并**，见 §4；发生在**模板骨架渲染阶段与工作区清单写入阶段**） | 重装 donkey / 检查权限 / 重试 init | **P2 启用** |
| `4` | `BuiltinToolGenerationError` | 内置工具生成失败 | 重装 donkey | P3 |
| `5-10` | — | v1.x 试运行期新发现 | — | 预留，本 Phase 不触发 |

**本阶段实际使用的退出码集合**：`{0, 1, 2, 3}`（spec SC-010）。

**语义唯一性**（按**阶段**切分，spec FR-038）：
- `1` = 输入 / 路径 / 参数用法不合法
- `2` = 权限不足（发生在前置校验阶段与工作区根目录创建阶段）
- `3` = 模板骨架生成失败（发生在模板骨架渲染阶段与工作区清单写入阶段，含渲染中途权限被撤销、磁盘满）

**`3` MUST NOT 复用 `1`**（spec FR-038）：二者的用户修复动作不同 —— `1` 是"建目录 / 换路径"，`3` 是"重装 donkey"。
故模板清单加载从 F001-P1 推迟到本 Phase（清单缺失 ≠ 路径缺失）。

---

## 3. 异常 → 退出码映射表

映射表是**全局唯一来源**，定义在 `donkey/cli/cli_client.py`：

```python
_EXCEPTION_TO_EXIT_CODE: dict[type[Exception], int] = {
    PathNotFoundError: EXIT_CODE_PATH_NOT_FOUND,          # 1
    PathPermissionError: EXIT_CODE_PATH_PERMISSION,        # 2
    TemplateGenerationError: EXIT_CODE_TEMPLATE_GENERATION,  # 3  ← P2 新增 1 行
}
```

**查找规则（沿用 P1，本 Phase 不变）**：沿继承链自近及远查找已登记的异常类；找不到则**兜底到 `1`**。
MUST NOT 使用宽泛的异常捕获吞掉未分类错误。

**常量**（`donkey/core/exit_codes.py`）：

```python
EXIT_CODE_OK = 0
EXIT_CODE_PATH_NOT_FOUND = 1
EXIT_CODE_PATH_PERMISSION = 2
EXIT_CODE_TEMPLATE_GENERATION = 3      # ← P2：从「建档」转为「启用」
EXIT_CODE_BUILTIN_TOOL_GENERATION = 4  # 仍为建档（P3 启用）
```

> P1 已把 `EXIT_CODE_TEMPLATE_GENERATION = 3` 与 `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` **建档**（常量存在但无代码路径使用）。
> 本 Phase MUST NOT 新增常量 —— 只把 `3` 接入映射表与错误路径。

---

## 4. 退出码 3 的 7 类成因 → 1 个错误类

> **本表是 spec『模板生成类失败的 7 类成因（权威分类法）』段的镜像**，冲突时以 spec 为准。

**合并理由（奥卡姆剃刀）**：7 类对用户的修复动作相同（重装 donkey / 检查权限 / 重试 init）→ 合并为一个码值，
不浪费 4 个码值给稀有错误。

| # | 成因 | 触发点 | 错误信息 MUST 含 |
|---|---|---|---|
| 1 | 模板清单缺失 / JSON 非法 / schema 非法 | `load_template_manifest` | 失败环节 + 下一步 |
| 2 | 模板源文件缺失 | `render_templates` | 缺失的源路径 + 下一步 |
| 3 | 渲染失败（正文不可解析） | `render_templates` | 失败环节 + 下一步 |
| 4 | 文件写入失败（磁盘满 / 权限在渲染中途被撤销） | `render_templates` | 目标路径 + 下一步 |
| 5 | sqlite3 结构构造失败 | `build_*_sqlite` | 失败环节 + 下一步 |
| 6 | 上游 saver 包缺失 / 版本不兼容 / 导入失败 | `build_sessions_sqlite` | "运行期依赖缺失或不可用" + 下一步 |
| 7 | 目标路径已存在但**是目录**（**且该条目为文本类或 sqlite3 类**） | `render_templates` | 目标路径 + 下一步 |

---

## 5. 错误信息契约（"下一步"指引）

**统一模板**（沿用 F001-P1 的 `_NEXT_STEP` 模式）：

```
[失败环节] + [具体对象] + [固定的下一步句]
```

| 退出码 | 下一步句（建议固定文案） |
|---|---|
| `1` | "下一步：请先建目录，或换路径到父目录已存在的目标。"（P1 已实现） |
| `2` | "下一步：请调整权限（chmod）后再试。"（P1 已实现） |
| `3` | **"下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。"**（P2 新增） |

**文案常量的落点**：

| 退出码 | 常量 | 落点模块 |
|---|---|---|
| `1` | `_NEXT_STEP` | `donkey/core/workspace/init.py`（P1 已实现，MUST NOT 改动） |
| `3` | `_NEXT_STEP_TEMPLATE` | **`donkey/core/exceptions.py`**（与 `TemplateGenerationError` 同模块）—— MUST NOT 放在 `init.py`：`init.py` 需 import `manifest.py`，而 `manifest.py` / `sqlite3_templates.py` 也需该文案，常量若在 `init.py` 会形成 `manifest.py → init.py → manifest.py` 的循环 import（research.md R-12） |

**硬约束**：

| # | 约束 | 出处 |
|---|---|---|
| E1 | 失败信息 MUST 写入 **stderr** | P1 FR-019 |
| E2 | MUST 含可识别的错误标识（错误类别名，或具体关键词） | P1 FR-019 |
| E3 | MUST 含**一条**用户可执行的下一步 | P1 FR-019 + **P2 FR-069**（模板类失败亦适用） |
| E4 | MUST NOT 产生未捕获的异常堆栈 | P1 FR-030 |
| E5 | 模板类失败 MUST NOT 只报异常类别而不给下一步 | P2 FR-069 / SC-020 |

---

## 6. 退出码与阶段的对照

> **退出码语义按阶段切分（spec FR-038）**：阶段 ① / ③ 的权限不足 → `2`；阶段 ④ / ⑤ 的一切失败 → `3`。
> 阶段切分保证 `2` 与 `3` 各自仍是**单一含义**：权限不足只在"尚未开始落地模板骨架"时归 `2`；一旦进入模板骨架落地阶段，任何失败（含权限撤销）都归 `3`。

| 阶段 | 失败面 | 退出码 |
|---|---|---|
| ① 前置校验（路径 / 权限 / 名称） | 路径类 | `1` |
| ① 前置校验 | 权限类 | `2` |
| ② 加载模板清单 | 模板类 | `3` |
| ③ 创建 workspace 根目录 | 权限类（`mkdir` 抛 `OSError` —— 含 `PermissionError` / 磁盘满 `ENOSPC` —— → MUST 包装为 `PathPermissionError`；**步骤 ③ 的一切失败一律归 `2`**，spec FR-038） | `2` |
| ④ 渲染模板骨架 | 模板类（源缺失 / 写入失败含磁盘满与权限中途撤销 / sqlite3 构造失败 / 目标是目录） | `3` |
| ⑤ 写工作区清单 | 模板类（JSON 非法 / 写入失败） | `3` |

---

## 7. 段位不重叠的自检（N-08）

本 Phase 的退出码全部落在 `1-10`（`donkey init` 段位）；`donkey load` 从 `11` 起、`session` 从 `21` 起、`run` 从 `31` 起 —— 无交集。

**F001 段位内的分配轨迹**：

```
子段 1（P1）：1  2
子段 2（P2）：3          ← 本 Phase
子段 3（P3）：4
预留     ：5 - 10
```

---

## End of exit-codes contract.
