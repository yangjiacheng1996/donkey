# 契约：退出码映射（F001-P3）

**版本**：v1（新增 `4`）
**所有者**：`donkey/core/exit_codes.py` + `donkey/core/exceptions.py` + `donkey/cli/cli_client.py`
**上游**：[spec.md](../spec.md) FR-071 ~ FR-075；[research.md](../research.md) R-07 / R-10

---

## 1. 段位（宪法 §4.4 · N-08）

```text
1-10    donkey init      ← 本 Phase 占用 1 / 2 / 3 / 4
11-20   donkey load
21-30   donkey session
31-100  donkey run
101-170 donkey web
171-200 donkey gui
```

**本阶段实际使用的退出码集合 = `{0, 1, 2, 3, 4}`**；`5-10` MUST NOT 被本阶段任何代码路径触发（spec FR-074）。

---

## 2. 异常 → 退出码映射表

| 异常类 | 退出码 | 常量 | 触发条件 | 修复动作 |
|---|---|---|---|---|
| —（成功） | `0` | `EXIT_CODE_OK` | 正常结束 | — |
| `PathNotFoundError` | `1` | `EXIT_CODE_PATH_NOT_FOUND` | 父目录不存在 / 路径非法 / 目标存在但不是目录 | 建目录 / 换路径 |
| `PathPermissionError` | `2` | `EXIT_CODE_PATH_PERMISSION` | 缺读 / 写 / 执行权限；创建 workspace 根失败 | 调整权限 |
| `TemplateGenerationError` | `3` | `EXIT_CODE_TEMPLATE_GENERATION` | 模板清单缺失 / 非法 / 源模板缺失 / 写入失败 / sqlite3 构造失败 / 目标路径是目录 | 重装 donkey / 检查权限 / 重试 init |
| **`BuiltinToolGenerationError`** | **`4`** | **`EXIT_CODE_BUILTIN_TOOL_GENERATION`** | **内置工具文件写入失败 / 示例 Skill 三层写入失败** | 重装 donkey / 检查权限 / 重试 init |

**映射表驱动**：客户端的异常 → 退出码映射 MUST 由**单一全局映射表**驱动（spec FR-073）；本 Phase 只**追加一行**。

---

## 3. exit 4 的两类成因（**权威分类法**）

| # | 成因 | 归类 |
|---|---|---|
| ① | 3 个内置工具文件写入失败（磁盘满 / 权限被撤销 / 其它 IO 错误） | 内置工具生成类 |
| ② | 示例 Skill 三层写入失败 | 内置工具生成类 |

**二者 MUST NOT 各占一个码值** —— 对用户的修复动作相同（重装 donkey / 检查权限 / 重试 init），按奥卡姆剃刀合并（spec FR-072）。

### 3.1 本 Phase **不**成立的第三类成因

源提示词 §5 的退出码表把"**集成预演导入失败**"列为 exit 4 的第三类成因 —— **本 Phase 不成立**（spec FR-072）：

- **工具导入验证是 `donkey load`（F002）的功能**，不在 `donkey init` 的职责内；
- 3 个内置工具是**稳定产物**，MUST NOT 为其每次 init 都付出一次导入预演的算力代价；
- **初始化阶段 MUST NOT 做"生成物导入预演"**。

**归属澄清（避免误报）**：

| 事项 | 归属 | 性质 |
|---|---|---|
| 生成物"确实能导入并调用"的**回归测试** | 本 Phase 的 `tests/integration/test_init_to_load.py` | **生成器自身的回归测试**（非产品能力） |
| "这个工作区的工具能不能被加载"的**用户可见验证** | **F002 `donkey load`** | 产品能力 |

二者 MUST NOT 混为一谈（spec FR-063）。

### 3.2 exit 4 **不**覆盖的情形

| 情形 | 归属的退出码 | 理由 |
|---|---|---|
| **模板源缺失**（如 `templates/tools/changes.py.txt` 不在安装包里） | **3**（`TemplateGenerationError`） | 是"模板源缺失"，不是"生成失败"—— 二者的排查路径不同（重装 vs 检查权限） |
| 清单条目 schema 非法 / 清单 JSON 非法 | **3** | 同上 |
| 工作区清单写入失败 | **3** | P2 的既定口径 |
| 记忆库结构问题 | **不适用** | 本 Phase MUST NOT 触碰三个记忆库文件（spec FR-085） |

---

## 4. 异常类层次

```text
Exception
└── DonkeyError                     # 总基类
    └── WorkspaceInitError          # donkey init 基类
        ├── PathNotFoundError       # exit 1
        ├── PathPermissionError     # exit 2
        ├── TemplateGenerationError # exit 3
        └── BuiltinToolGenerationError  # exit 4  ← 本 Phase 新增
```

**新增类的要求**（spec FR-071）：
- MUST 归属 `donkey init` 的错误基类之下；
- MUST 在其说明中标注对应退出码 `4`；
- MUST **引用**本契约 §3 的权威分类法，**MUST NOT 自行复述**该清单（避免出现第 2 份副本而漂移）；
- MUST NOT 自行映射退出码（MUST NOT 返回退出码 / 打印 / 退出进程 —— 宪法 N-05）。

---

## 5. 错误信息的形态

**exit 4 的错误信息 MUST 同时含**：

1. **可识别的失败标识**（哪一类生成失败）；
2. **一条用户可执行的下一步**（"重装 donkey" / "检查权限" / "重试 init" 三者之一）—— 与 exit 1 / 2 / 3 的指引口径一致（spec FR-075）。

**固定文案常量 MUST 落在 `donkey/core/exceptions.py`**（与错误类同源）—— **MUST NOT** 落在 `core/workspace/init.py`，否则形成 `manifest.py → init.py → manifest.py` 的循环 import（**P2 的 R-12 教训**）。

```text
_NEXT_STEP_TEMPLATE    （既有，exit 3 用）
_NEXT_STEP_BUILTIN     （新增，exit 4 用）
```

---

## 6. 改动清单（本 Phase 的**全部**改动 = 4 处）

| # | 改动 | 文件 | 依据 |
|---|---|---|---|
| 1 | 异常映射表**追加一行**（`BuiltinToolGenerationError` → `4`） | `donkey/cli/cli_client.py` | spec FR-073 / FR-088 |
| 2 | 退出码常量 `4` 的文档串从"属 F001-P3，本阶段不触发"改为"**本阶段启用**"（常量本身**已由 P1 建档**，MUST NOT 重复定义） | `donkey/core/exit_codes.py` | R-10 |
| 3 | 新增异常类 `BuiltinToolGenerationError(WorkspaceInitError)`（**本 Phase 唯一新增的异常类**） | `donkey/core/exceptions.py` | spec FR-071 / FR-075 |
| 4 | **渲染层的条目级豁免**（`init_workspace_inner` 步骤 ④ 剔除契约库条目并计入 `files_skipped`）—— **详见本文 §7**；`render_templates` **一字不改** | `donkey/core/workspace/init.py` | spec FR-105 / FR-069 · R-07 |

**MUST NOT**：引入任何其它客户端行为变更（不新增命令行输出 / 不改摘要格式 / 不改 `--help` 文案 —— 与 P2 的 FR-064 三项不同，本 Phase **无**文案同步项）。**注**：第 4 行是**渲染层**的行为变更，不属客户端文案变更，故不受该约束覆盖。

> **口径核对（2026-10-23 定点修订）**：P2 的 FR-064 把客户端改动限定为**三项**（异常映射 +1 行 / 结果摘要 +1 行强制清空提示 / `--help` 与子命令说明文案同步）—— 本 Phase 的客户端改动**仅**其中的第 ① 项（异常映射 +1 行），**不**做结果摘要改动、**不**做 `--help` 文案同步（spec FR-088：除"异常映射表追加一行"外 MUST NOT 有任何客户端行为变更）→ 上句"本 Phase **无**文案同步项"**仍然成立**。

---

## 7. 渲染层的条目级豁免（exit 4 之外的唯一本 Phase 行为变更）

**豁免对象**：`tools/changes.py`（契约库）—— `--force` 时 MUST 保留其原样（spec FR-105）。

**实现落点**：`init_workspace_inner` 步骤 ④ —— 把已存在的契约库条目**从传给 `render_templates` 的列表中剔除**并计入 `files_skipped`；`render_templates` **一字不改**（R-07）。

**计数影响**：

| 场景 | `templates_loaded` | `files_created` | `files_skipped` |
|---|---|---|---|
| 全新创建 | 54 | **48** | 0 |
| 二次 init（非强制） | 54 | 0 | **48** |
| `--force`（契约库已存在） | 54 | **47** | **1** |

**边界**：该豁免**只**作用于契约库**一个**条目 —— MUST NOT 削弱 P2 通则"清单内文本条目带强制标志时先删后重建"对其余全部条目的成立（spec FR-069）。

> **已回填 spec（2026-10-23 `/speckit.analyze` 闭合）**：FR-070 已定点修订为"允许在 `init_workspace_inner` 步骤 ④ 增加**一条**条目级强制重置豁免"（research.md 待回填清单第 1 项）。
