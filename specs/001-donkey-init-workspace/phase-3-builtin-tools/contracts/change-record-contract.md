# 契约：变更记录 schema v1（F001-P3）

**版本**：`CHANGE_RECORD_VERSION = 1`（**冻结**）
**所有者**：`donkey/core/workspace/templates/tools/changes.py.txt` → 渲染后的 `<workspace>/tools/changes.py`
**上游**：[spec.md](../spec.md) FR-002 ~ FR-012；[research.md](../research.md) R-05 ~ R-07

> **本契约是"只增不改"的**（spec FR-012）：
> （a）**只增不改** —— 新字段可加，既有字段的名字与语义冻结，消费方 MUST 忽略不认识的字段；
> （b）**版本分派** —— 消费方 MUST 按 `version` 分派，MUST NOT"靠字段是否存在猜版本"；
> （c）**单一来源** —— 全工作区（内置工具 + 用户自写工具）MUST 复用本契约，MUST NOT 自造第二套指纹 / 差异逻辑。

---

## 1. 必现基线字段（12 个 —— 任何动作下全部存在）

| # | 字段 | 类型 | 语义 | 取值约束 |
|---|---|---|---|---|
| 1 | `version` | int | 契约版本 | 恒为 `1` |
| 2 | `action` | str | 变更动作 | `create` / `update` / `delete` / `copy` / `move` |
| 3 | `path` | str | 变更目标的**绝对**路径 | — |
| 4 | `rel_path` | str | 相对工作区根的 POSIX 路径 | 工作区**之外** → 回退为绝对路径（MUST NOT 抛异常） |
| 5 | `previous_exists` | bool | 变更前文件是否存在 | — |
| 6 | `previous_size` | int | 变更前字节数 | 不存在 = `0` |
| 7 | `previous_hash` | str \| None | 变更前内容指纹 | `sha256:<hex>`；不存在 = `null`（Python 侧 `None`，**MUST NOT 用空串** —— spec FR-004） |
| 8 | `new_size` | int | 变更后字节数 | 删除后 = `0` |
| 9 | `new_hash` | str \| None | 变更后内容指纹 | `sha256:<hex>`；删除后 = `null`（Python 侧 `None`，**MUST NOT 用空串** —— spec FR-004） |
| 10 | `unified_diff` | str | 标准统一差异文本 | 头 `--- a/<rel_path>` / `+++ b/<rel_path>` / `@@ … @@` |
| 11 | `diff_truncated` | bool | 差异文本是否被截断 | 超过 `MAX_DIFF_BYTES`（64 KiB）时为真 |
| 12 | `applied` | bool | 是否真的落盘 | 预览模式恒为 `false` |

**基线键集合（单测 MUST 按此断言，防字段漂移）**：

```python
BASELINE_KEYS = frozenset({
    "version", "action", "path", "rel_path",
    "previous_exists", "previous_size", "previous_hash",
    "new_size", "new_hash",
    "unified_diff", "diff_truncated", "applied",
})
```

---

## 2. 条件字段（4 个）

| # | 字段 | 类型 | 出现条件 | 语义 |
|---|---|---|---|---|
| 13 | `src` | str | `action ∈ {copy, move}` | 源路径（绝对） |
| 14 | `src_rel_path` | str | `action ∈ {copy, move}` | 源路径（工作区相对 POSIX） |
| 15 | `previous_content` | str | `include_previous=True` **且** 旧正文存在 **且** ≤ 256 KiB | 旧正文全文（回滚用） |
| 16 | `previous_content_truncated` | bool | `include_previous=True` **且** 旧正文存在 **且** > 256 KiB | 旧正文被省略（此时**不**出现 `previous_content`） |

---

## 3. 动作 × 字段矩阵

| 动作 | `previous_exists` | `previous_size` | `previous_hash` | `new_size` | `new_hash` | 条件字段 |
|---|---|---|---|---|---|---|
| `create` | `false` | `0` | `null` | 字节数 | 指纹 | — |
| `update` | `true` | 旧字节数 | 旧指纹 | 新字节数 | 新指纹 | — |
| `delete`（文件） | `true` | 旧字节数 | 旧指纹 | `0` | `null` | 可选 `previous_content` |
| `delete`（目录） | `false` | `0` | `null` | `0` | `null` | — |
| `copy` | 目标是否存在 | 目标旧字节数 | 目标旧指纹 | 源字节数 | 源指纹 | `src` / `src_rel_path` |
| `move` | 目标是否存在 | 目标旧字节数 | 目标旧指纹 | 源字节数 | 源指纹 | `src` / `src_rel_path` |

---

## 4. 指纹与差异的计算口径

| 项 | 口径 | 依据 |
|---|---|---|
| 指纹 | `"sha256:" + hashlib.sha256(data).hexdigest()` | spec FR-004 |
| 指纹的输入 | **原始字节** —— MUST NOT 先解码再编码（含 BOM / 非法字节的文件会因此改变指纹） | spec FR-006 |
| 体积 | `len(data)`（原始字节数） | spec FR-004 |
| 差异的输入 | 字节以 UTF-8 **容错**解码（`errors="replace"`）后按 `\n` 切行（**MUST NOT** 用 `splitlines()` —— R-05） | R-05 |
| 差异头 | `a/<rel_path>` / `b/<rel_path>` —— **工作区相对**，保证可移植 | spec FR-007 |
| 差异截断 | 字节数 > `MAX_DIFF_BYTES`（64 KiB）→ 截断 + `diff_truncated=true` | spec FR-003 |
| 旧正文省略 | 字节数 > `MAX_PREVIOUS_BYTES`（256 KiB）→ 只置 `previous_content_truncated=true`，MUST NOT 附带正文 | spec FR-005 |

---

## 5. `applied` 与工具顶层字段的关系

四个改文件工具的返回 JSON 顶层各有一个 `applied` 字段，**与 `change.applied` 恒等**：

| 场景 | 顶层 `applied` | `change.applied` |
|---|---|---|
| 正常落盘 | `true` | `true` |
| 预览模式（`dry_run=True`） | `false` | `false` |

**期望指纹不匹配时** → 抛 `tools.changes.FileChangedError`，**不返回任何 JSON**，**无任何磁盘副作用**（spec FR-019）。

---

## 6. 期望指纹（乐观锁）的检查口径

```text
check_expected_hash(path, expected_hash):
    expected_hash 为空（None / ""） → 直接返回（检查关闭）
    当前内容的指纹（文件不存在 → None）≠ expected_hash → 抛 FileChangedError
```

- 文件**已不存在**时（当前指纹 = `None`）→ 视为不匹配 → 抛异常（spec FR-010）
- 期望指纹是**入参守卫**，MUST NOT 出现在变更记录里（spec FR-019）
- 覆盖范围：**写 / 复制 / 移动 / 删除**四个工具**均**支持（spec FR-013 / FR-019）

---

## 7. 消费方指引（给未来的引擎层）

```text
1. 按 record["version"] 分派（MUST NOT 靠字段是否存在猜版本）
2. 忽略不认识的字段（只增不改）
3. 渲染差异时用 record["unified_diff"]（已带 a/ b/ 的工作区相对头）
4. 回滚时用 record["previous_content"]（若存在）；若 previous_content_truncated 为真 → 旧正文不可得 → 需靠快照
5. 判断"是否在审阅范围内"用 record["rel_path"]（工作区外的记录 rel_path 是绝对路径 → 单独标注）
```

**已知缺口**（v1 不补，由引擎层兜底）：

| 缺口 | 后果 | 引擎层的兜底 |
|---|---|---|
| 命令工具造成的文件副作用**不进**变更记录 | 引擎层看到的"已记录变更"少于"实际变更" | 审阅前做一次工作区快照（指纹扫描）并对账 |
| 目录删除按**目录粒度**记录 | 删目录时只得到一条目录级记录 | 同上（快照对账可还原被删文件清单） |
| 越过工作区根的绝对路径写入 | `path` 指向工作区之外 | 按 `rel_path` 判定审阅范围，越界记录单独标注 |

---

## 8. 未来演进（只加不改的示例形态）

```python
# 破坏性变更 → version 升到 2，消费方按 version 分派
# 非破坏性变更 → 直接加字段，version 不变
record["duration_ms"] = 12          # 允许：消费方 MUST 忽略不认识的字段
```

**禁止**：修改既有字段的名字或语义；把条件字段改成必现；把 `applied` 的语义从"是否落盘"改成别的。
