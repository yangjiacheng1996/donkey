# 01 · `donkey init` —— 工作区初始化 人工测试手册

> **对应特性**：Feature 001（`donkey init`），含 P1 `cli_validation` / P2 `template_skeleton` / P3 `builtin_tools` / P4 `cli_version` 四个 Phase。
> **对应规格**：`specs/001-donkey-init-workspace/`。
> **本手册的用途**：在 TDD 自动化测试之外，用**人工操作**把 Feature 001 的每一条对外承诺走一遍，
> 找出"自动化测到了但用户能感知到的不合理之处"。
>
> **P4 补充说明**：`donkey version` 是**独立于 `donkey init` 的只读元信息命令** —— 它**不创建工作区、不读写任何文件、不要求工作区存在**，
> 只在 stdout 输出一行裸版本号。本手册在 **L 组** 覆盖它；A 组的 CLI 表面用例也因多了一个子命令而同步更新。
>
> **怎么用**：从第 1 章开始逐条执行。每条用例给出「目的 / 步骤 / 期望」。
> 执行时把**实际输出**记下来；与"期望"不一致 → 记一条缺陷（格式见第 14 章）。
> 第 13 章是**已知问题清单**（已确认存在的不合理点），执行前先读一遍，避免重复排查。

### 目录

| 章 | 内容 | 用例数 | 期望退出码 |
|---|---|---|---|
| 0 | 前置约定 · 计数口径 · 退出码速查 | — | — |
| 1 | A 组 · CLI 表面与用法错误 | 8 | 1（`--help` 为 0） |
| 2 | B 组 · 路径校验 | 8 | 1 |
| 3 | C 组 · 权限校验 | 3 | 2 |
| 4 | D 组 · 模板骨架落地与内容正确性 | 9 | 0 |
| 5 | E 组 · 幂等性 | 4 | 0 |
| 6 | F 组 · `--force` 恢复出厂设置 | 7 | 0 |
| 7 | G 组 · 内置工具功能 | 8 | — |
| 8 | H 组 · 变更记录契约 | 11 | — |
| 9 | I 组 · 示例 Skill 的三层结构 | 3 | — |
| 10 | J 组 · 工作区身份与可移植性 | 3 | — |
| 11 | L 组 · 版本查询（`donkey version`，只读元信息命令） | 9 | 0（用法错误为 1） |
| 12 | K 组 · 回归门禁 | — | 0 |
| 13 | 已知问题与待观察点（BUG 候选清单） | 13 条（1 条已修复） | — |
| 14 | 缺陷记录模板 | — | — |
| 15 | 人工测试完成后的检查清单 | — | — |

---

## 0. 前置约定

### 0.1 环境准备

```bash
cd <仓库根>                      # 即 donkey 仓库根目录
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"           # dev 依赖含 pytest / pytest-httpx / ruff / mypy
```

**自检**：

```bash
donkey --help          # 期望：打印 usage，退出码 0
donkey version         # 期望：v0.1.0（退出码 0，stdout 恰好一行）
```

> 📌 **查版本号用 `donkey version`**（P4 起）—— 不再需要 `python -c "import donkey; print(donkey.__version__)"` 这种绕路写法。
> 该命令**只读**：不创建 / 修改 / 删除任何文件，不读取工作区，也不要求当前目录存在工作区。
>
> ⚠️ **两个入口必须等价**：`donkey`（console script）与 `python -m donkey` 的 **stdout / stderr / 退出码必须逐字节相同**。
> 人工测试时两条入口各跑一遍同一组用例，比对输出。

### 0.2 贯穿全文的测试工作区

```bash
export WS=/tmp/dk_manual        # 测试工作区根（父目录必须已存在）
rm -rf "$WS"
```

> ⚠️ **相对路径以"进程当前目录"为基准**，`--force` 会**清空三个记忆库**。
> 人工测试请始终用**独立的一次性目录**，不要指向真实工作区。

### 0.3 关键计数口径（判定对错的基准）

| 口径 | 数值 | 说明 |
|---|---|---|
| 模板清单条目总数 `templates` | **54** | 45 个文本型 + 3 个 sqlite3 + 6 个目录型 |
| 文件型条目数 | **48** | 45 文本 + 3 sqlite3（= `files_created` + `files_overwritten` + `files_skipped`） |
| 目录型条目数 | **6** | `tools` / `mcp` / `skills` / `skills/example` / `memory` / `providers` |
| 磁盘上的文件总数 | **49** | 48 个模板文件 + 1 个工作区清单 `manifest.json` |
| 磁盘上的目录总数 | **10** | 根目录 + 6 个清单目录 + 3 个 Skill 第三层子目录 |
| 内置 `@tool` 函数总数 | **9** | 文件 7 + 命令 1 + 网络 1 |

**执行报告的计数**（按「对象 × 动作」分解 —— 2026-10-30 修订，宪法 [D-22]）：

| 场景 | `templates` | `files_created` | `files_overwritten` | `files_skipped` | `dirs_created` | `dirs_skipped` |
|---|---|---|---|---|---|---|
| 首次创建 | 54 | **48** | 0 | 0 | **6** | 0 |
| 再次 init（不加 `--force`） | 54 | 0 | 0 | **48** | 0 | **6** |
| `--force`（契约库已存在） | 54 | 0 | **47** | **1** | 0 | **6** |
| `--force`（契约库不存在） | 54 | 0 | **48** | 0 | 0 | **6** |
| 删掉 1 个文件后再 init | 54 | **1** | 0 | **47** | 0 | **6** |

> 📌 **`--force` 的 47 是"覆盖"不是"新建"** —— 它被重建（内容回到出厂态），但文件**原本就在**。
> `files_created` 严格是"本次**新建**"，故 `--force` 情形为 **0**。
>
> 📌 **算术自洽**：`templates` == `files_created` + `files_overwritten` + `files_skipped`
> + `dirs_created` + `dirs_skipped`（54 = 48 + 0 + 0 + 6 + 0）。

### 0.4 退出码速查

| 码 | 含义 | 触发条件 |
|---|---|---|
| **0** | 成功 | 工作区根已建、模板已渲染、工作区清单已写入 |
| **1** | 输入 / 路径 / 用法非法 | 父目录不存在 · 路径为空 · 根目录 · 悬空符号链接 · 目标已存在且不是目录 · 父目录是文件 · 路径含非法字符 · **argparse 用法错误** |
| **2** | 权限不足 | 父目录缺写 / 执行权限 · 目标缺读 / 写 / 执行权限 · 创建工作区根失败 |
| **3** | 模板生成失败 | 清单缺失 / 非法 JSON / 结构非法 · 模板源缺失 · 写入失败 · sqlite3 构造失败 · 目标路径是目录 |
| **4** | 内置工具生成失败 | 3 个内置工具文件写入失败 · 示例 Skill 三层写入失败（**当前实现下不可达，见第 13 章 K-6**） |

> **`donkey version`（P4）的退出码集合 = `{0, 1}`**：成功 `0`；参数用法错误 `1`（**不是** argparse 默认的 `2`）——
> 与 `donkey init` 的用法错误**同源同码**（同一个解析器覆写）。该命令**不占用**任何新的退出码段位，
> 也**不会**触发 `2` / `3` / `4`。

**失败输出格式**（stderr，**第一行**）：

```
[donkey init] 失败：<异常类名>: <错误消息>
```

**成功输出格式**（stdout，**三段**）：

**① 摘要行**（第一行）—— 计数按「对象 × 动作」分解：

```
[donkey init] workspace=<绝对路径> name=<工作区名> force=<true|false> templates=<n> files_created=<n> files_overwritten=<n> files_skipped=<n> dirs_created=<n> dirs_skipped=<n>
```

**② 逐项明细**（第二行是图例，其后每个清单条目一行，**恒定 54 行**）：

```
[donkey init] 逐项明细（+ 新建 / ~ 覆盖 / - 跳过；路径以 / 结尾者 = 目录条目）：
  + instruction.md
  + providers/default.toml
  ...
  + tools/
```

**③ `--force` 警告行**（**仅 `--force` 时出现，且置于明细之后**）：

```
[donkey init] 警告：memory/ 下的三个记忆库文件已被清空并重建为出厂状态（会话历史与会话元数据一并清空，--force 恢复出厂设置）。如需保留请先备份。
```

> 📌 明细走 **stdout**，恒定输出（`init` 的参数面只有 `path` + `--force`，没有 `--quiet`）。
> 路径是**工作区相对**路径；目录条目以 `/` 结尾。

---

## 1. A 组 · CLI 表面与用法错误（期望退出码 1）

**目的**：确认 CLI 的参数面被**冻结**在 `<PATH>` + `--force` 两个参数上；用法错误**不得**复用 argparse 默认的退出码 2。

| 编号 | 操作 | 期望 |
|---|---|---|
| M-A1 | `donkey --help` | 退出码 **0**；打印 `usage: donkey [-h] {init,version} ...` 与 `donkey —— workspace 与 agent 运行框架。`；子命令列表**出现** `version`（P4 起） |
| M-A2 | `donkey init --help` | 退出码 **0**；打印 `usage: donkey init [-h] [--force] path`，含 `path` 与 `--force` 两条说明 |
| M-A3 | `donkey`（缺子命令） | 退出码 **1**；stderr：`donkey: error: the following arguments are required: command` |
| M-A4 | `donkey init`（缺 path） | 退出码 **1**；stderr：`donkey init: error: the following arguments are required: path` |
| M-A5 | `donkey foo`（未知子命令） | 退出码 **1**；stderr：`invalid choice: 'foo' (choose from 'init', 'version')` |
| M-A6 | `donkey init $WS --name abc` | 退出码 **1**；stderr：`unrecognized arguments: --name abc`（**不得**被静默忽略） |
| M-A7 | `donkey init $WS --unknown-flag` | 退出码 **1**；用法错误 |
| M-A8 | `python -m donkey init $WS` 与 `donkey init $WS` | 两者 stdout / stderr / 退出码**逐字节相同**（`prog` 必须都是 `donkey`，不得出现 `__main__.py`） |
> **A 组要点**：退出码 2 是"权限不足"的专属位，argparse 用法错误必须折叠成 **1**。

**M-A8 操作**（两个入口必须**各自对全新目录**跑，否则第二次是幂等重跑，计数本来就不同）：

```bash
rm -rf /tmp/dk_a8a /tmp/dk_a8b
donkey init /tmp/dk_a8a > /tmp/o1 2> /tmp/e1; a=$?
python -m donkey init /tmp/dk_a8b > /tmp/o2 2> /tmp/e2; b=$?
sed 's/dk_a8a/dk_a8X/g' /tmp/o1 > /tmp/o1n; sed 's/dk_a8b/dk_a8X/g' /tmp/o2 > /tmp/o2n
diff /tmp/o1n /tmp/o2n && diff /tmp/e1 /tmp/e2 && [ "$a" = "$b" ] && echo "两个入口完全等价"
```

---

## 2. B 组 · 路径校验（期望退出码 1）

**目的**：确认非法路径被**挡在写盘之前**，且失败信息可定位、下一步可执行。

| 编号 | 准备 | 操作 | 期望 stderr（首行） | 期望退出码 |
|---|---|---|---|---|
| M-B1 | — | `donkey init ""` | `PathNotFoundError: 路径不能为空：''。下一步：请先建目录，或换路径到父目录已存在的目标。` | 1 |
| M-B2 | — | `donkey init /` | `PathNotFoundError: 根目录不可作为 workspace 根：/。下一步：…` | 1 |
| M-B3 | — | `donkey init /tmp/nope/deep/ws` | `PathNotFoundError: 父目录不存在：/tmp/nope/deep。…` | 1 |
| M-B4 | `touch /tmp/afile` | `donkey init /tmp/afile` | `PathNotFoundError: 目标已存在且不是目录：/tmp/afile。…` | 1 |
| M-B5 | `touch /tmp/afile` | `donkey init /tmp/afile/sub` | `PathNotFoundError: 父目录不是目录：/tmp/afile。…` | 1 |
| M-B6 | `ln -s /tmp/does-not-exist /tmp/dangling` | `donkey init /tmp/dangling` | `PathNotFoundError: 路径是悬空符号链接（指向不存在的目标）：/tmp/dangling。…` | 1 |
| M-B7 | `cd /tmp && donkey init relws` | 相对路径 | —（成功路径无 stderr） | **0**；输出中 `workspace=/tmp/relws`（绝对路径） |
| M-B8 | `cd /tmp && donkey init ./a/b/ws` | 相对路径 + 父目录不存在 | `父目录不存在：/tmp/a/b` | **1** |

> **B 组要点**：
> - **M-B3 / M-B8 是重点** —— 父目录**不得**被自动创建（`mkdir(parents=True)` 被明令禁止）。用户没说要建目录，donkey 就替他建了目录树，后面会出诡异问题。
> - **M-B2** —— 根目录被拒时，**不得**在 `/` 下留下任何文件。
> - **M-B1** —— 空路径必须**单独识别**（`Path("")` 会被折叠成 `.`）。
> - 失败后**不得**在磁盘上留下任何半成品目录。

---

## 3. C 组 · 权限校验（期望退出码 2）

**目的**：确认权限问题与"路径问题"被**区分开**（两个不同的退出码、两条不同的补救指引）。

| 编号 | 准备 | 操作 | 期望 | 退出码 |
|---|---|---|---|---|
| M-C1 | `mkdir /tmp/dk_ro && chmod 555 /tmp/dk_ro` | `donkey init /tmp/dk_ro/sub` | `PathPermissionError: 缺少写权限：/tmp/dk_ro。下一步：请调整权限（chmod）后再试。` | **2** |
| M-C2 | `mkdir /tmp/dk_ro2 && chmod 555 /tmp/dk_ro2` | `donkey init /tmp/dk_ro2`（目标已存在） | `PathPermissionError: 缺少写权限：/tmp/dk_ro2。…` | **2** |
| M-C3 | `mkdir /tmp/dk_ro3 && chmod 000 /tmp/dk_ro3` | `donkey init /tmp/dk_ro3` | 报错信息里含"读权限"或"执行权限"字样 | **2** |

> **C 组要点**：
> - 目标**不存在**时检查**父目录**的写 + 执行权限；目标**已存在**时检查**目标自身**的读 + 写 + 执行权限。
> - 报错信息必须**同时**包含「缺哪种权限」与「缺在哪条路径」—— 两者缺一不可。
> - `chmod 555` 的目录对 root 也应被拒（POSIX 语义），**不应**依赖特权账号才能复现。

---

## 4. D 组 · 模板骨架落地与内容正确性

### M-D1 · 首次 init 的产物计数

```bash
rm -rf "$WS"; donkey init "$WS"; echo "exit=$?"
```

**期望**（**首行**逐字比对；其后是图例 + 54 条逐项明细）：

```
[donkey init] workspace=/tmp/dk_manual name=dk_manual force=false templates=54 files_created=48 files_overwritten=0 files_skipped=0 dirs_created=6 dirs_skipped=0
[donkey init] 逐项明细（+ 新建 / ~ 覆盖 / - 跳过；路径以 / 结尾者 = 目录条目）：
  + instruction.md
  ...（共 54 条明细）
exit=0
```

> 📌 明细行数 MUST 恰为 **54**（= 清单条目总数）；其中 **48** 条是文件（标记 `+`）、
> **6** 条是目录（标记 `+` 且路径以 `/` 结尾）。

### M-D2 · 目录树

```bash
find "$WS" -type d | sort
```

**期望**：恰好 **10** 个目录 —— 根目录 + 下列 9 个：

```
<WS>            <WS>/memory      <WS>/providers    <WS>/skills
<WS>/mcp        <WS>/skills/example                   <WS>/skills/example/reference
<WS>/skills/example/scripts                            <WS>/skills/example/templates
<WS>/tools
```

### M-D3 · 文件总数

```bash
find "$WS" -type f | wc -l        # 期望：49
ls -1 "$WS"/tools                 # 期望：README.md  __init__.py  changes.py  commandline.py  filesystem.py  webfetch.py
ls -1 "$WS"/providers/*.toml | wc -l   # 期望：27（26 个供应商 + default.toml）
```

### M-D4 · 工作区清单 `manifest.json`

```bash
cat "$WS"/manifest.json
```

**期望**：**恰好 3 个字段**、2 空格缩进、非 ASCII 不转义：

```json
{
  "name": "dk_manual",
  "created_at": "2026-10-30T02:26:08.432853+00:00",
  "donkey_version": "0.1.0"
}
```

- `name` **必须等于路径末段**（`dk_manual`）—— CLI 没有任何命名参数。
- `created_at` 是带时区的 ISO 8601。
- `donkey_version` 记录**生成本工作区的那一份 donkey** 的版本（**动态取值** —— 优先读安装分发元数据，取不到时回退包内 `__version__`）。
- > 📌 **2026-10-30 变更（宪法 [D-21]）**：清单原有一个 `"version": 1` 字段（整数，清单**格式版本**），**已删除** ——
  > 它全仓无人读取，且与 `donkey_version` 并排时读作"两个打架的版本号"。**存量工作区**的清单里可能仍带该字段
  > （读取端不解析它，不影响任何读路径）；`donkey init --force` 重写后即归一到三字段形态。

### M-D5 · 工作区名注入三处一致

```bash
head -1 "$WS"/README.md
head -1 "$WS"/instruction.md
head -1 "$WS"/providers/default.toml
grep -rn '{{' "$WS" || echo "无占位符残留"
```

**期望**：三处的标题都含工作区名 `dk_manual`；**无任何 `{{ … }}` 残留**。
> 核对"三处一致"：工作区 README 正文 / 供应商全局默认正文 / 工作区清单 `name` 字段。

### M-D6 · 26 份供应商配置全部可解析

```bash
cd "$WS" && python - <<'PY'
import pathlib, tomllib
bad = []
for p in sorted(pathlib.Path("providers").glob("*.toml")):
    try: tomllib.loads(p.read_text())
    except Exception as e: bad.append((p.name, e))
print("解析失败:", bad or "无")
PY
```

**期望**：解析失败为空；每份配置的开关全部为关、凭据为空。

### M-D7 · `mcp/mcp.json` 是合法 JSON

```bash
python -c "import json;print(json.load(open('$WS/mcp/mcp.json')))"
```

**期望**：`{'mcpServers': {}}`。

### M-D8 · 三个记忆库文件

```bash
ls -l "$WS"/memory/*.sqlite3
cd "$WS" && python - <<'PY'
import sqlite3
for n in ("sessions", "store", "knowledge"):
    c = sqlite3.connect(f"memory/{n}.sqlite3")
    objs = c.execute("select type,name from sqlite_master order by type,name").fetchall()
    print(n, "→", objs or "空")
PY
```

**期望**：
- `sessions.sqlite3` → **3 张表**（`checkpoints` / `writes` / `sessions_metadata`）+ **2 个自建索引**
  （`idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at`）；
- `store.sqlite3` 与 `knowledge.sqlite3` → **完全空**（0 表 0 索引）。

### M-D9 · 记忆库历史在 `--force` 后被清空

```bash
cd "$WS" && python - <<'PY'
import sqlite3
c = sqlite3.connect("memory/sessions.sqlite3")
c.execute("insert into sessions_metadata(thread_id,title,created_at,updated_at,donkey_version)"
          " values('t1','标题',0,0,'0.1.0')")
c.commit()
print("插入后行数:", c.execute("select count(*) from sessions_metadata").fetchone()[0])
PY
donkey init "$WS" --force
cd "$WS" && python - <<'PY'
import sqlite3
c = sqlite3.connect("memory/sessions.sqlite3")
print("force 后行数:", c.execute("select count(*) from sessions_metadata").fetchone()[0])
PY
```

**期望**：行数由 1 回落到 **0**；同时 `--force` 的警告行出现在 stdout。

---

## 5. E 组 · 幂等性（Feature 001 的核心契约）

### M-E1 · 再次 init 不改动任何已有文件

```bash
find "$WS" -type f -exec stat -c '%n %Y %s' {} \; | sort > /tmp/before.txt
donkey init "$WS"
find "$WS" -type f -exec stat -c '%n %Y %s' {} \; | sort > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt && echo "完全未改动"
```

**期望**：
- 输出 `templates=54 files_created=0 files_skipped=48 dirs_skipped=6`；
- `diff` **无差异**（**内容与 mtime 都必须不变**）。

### M-E2 · 删掉的文件会被补回来

```bash
rm "$WS"/tools/filesystem.py
donkey init "$WS"
ls "$WS"/tools/filesystem.py
```

**期望**：文件重新出现；输出 `files_created=1 files_skipped=47`。

### M-E3 · 删掉 Skill 第三层的文件会被补回来

```bash
rm "$WS"/skills/example/reference/example.md
donkey init "$WS"
```

**期望**：文件重新出现（`files_created=1 files_skipped=47`）。

### M-E4 · 清单外的用户文件永不被触碰

```bash
echo "# 我自己的工具" > "$WS"/tools/my_tool.py
mkdir -p "$WS"/my_stuff && echo "x" > "$WS"/my_stuff/a.txt
donkey init "$WS"
donkey init "$WS" --force
cat "$WS"/tools/my_tool.py; cat "$WS"/my_stuff/a.txt
```

**期望**：两个文件**内容不变、仍在原处**。

---

## 6. F 组 · `--force` 恢复出厂设置

**目的**：确认 `--force` 的作用域**严格限定在清单条目内** —— 该恢复的恢复，不该动的绝不动。

| 编号 | 操作 | 期望 |
|---|---|---|
| M-F1 | `donkey init "$WS" --force`（契约库已存在） | 输出 `templates=54 files_created=0 files_overwritten=47 files_skipped=1`；**末行**是记忆库警告 |
| M-F2 | `echo "# 我改过的契约库" >> "$WS"/tools/changes.py` 后 `--force` | 契约库**保留用户追加行**（逐字节不变）—— 这条是 P3 唯一豁免项 |
| M-F3 | `echo "MODIFIED" > "$WS"/tools/filesystem.py` 后 `--force` | 文件**恢复成出厂内容**（`grep -c MODIFIED` = 0） |
| M-F4 | `rm -rf /tmp/dk_n && mkdir -p /tmp/dk_n && donkey init /tmp/dk_n --force` | 契约库**不存在** → 走正常创建：`files_created=48 files_overwritten=0 files_skipped=0` |
| M-F5 | `--force` 前后对比 `manifest.json` | `created_at` **被刷新**（`--force` 覆盖清单）；不加 `--force` 时 `created_at` **保持不变** |
| M-F6 | `touch "$WS"/memory/sessions.sqlite3-wal "$WS"/memory/sessions.sqlite3-shm` 后 `--force` | `-wal` / `-shm` 边车文件**被一并清理**（sqlite3 重建必须无残留） |
| M-F7 | 在 `skills/example/` 下放一个清单外的文件后 `--force` | 该文件**仍在**；同目录的清单内文件**恢复出厂内容** |

> **F 组要点**：
> - M-F2 是**最容易被回归**的行为 —— 契约库是用户自写工具的依赖，被覆盖等于单方面毁掉用户代码。
> - `--force` 的作用域**严格限定在清单条目内**；目录条目**既不删目录、也不删目录里的任何文件**。

---

## 7. G 组 · 内置工具功能

> **前置**：`cd "$WS"` 后执行。**必须**用 `python - <<'PY'`（stdin）或 `python -c`，
> **不要**写成脚本文件 —— 脚本文件的 `sys.path[0]` 是脚本所在目录，会找不到 `tools` 包。
> **不要**在同一个 Python 进程里先后导入两个不同工作区的 `tools.*`（`sys.modules` 按名缓存，会拿到上一个工作区的模块）。

### M-G1 · 9 个工具函数能被导入

```bash
cd "$WS" && python - <<'PY'
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
from tools.commandline import run_shell
from tools.webfetch import fetch_url
for f in (read_file, write_file, copy_file, move_file, delete_file, list_dir, stat, run_shell, fetch_url):
    print(f.__name__, len(f.description or f.__doc__ or ""), "字符说明")
PY
```

**期望**：9 个全部导入成功，每个说明文字长度 **> 20** 字符。

> ⚠️ **注意**：若报 `ModuleNotFoundError: No module named 'httpx'` —— 这是**预期行为**（`httpx` 是
> **渲染进工作区的模板依赖**，donkey 自身不携带）。在工作区里 `pip install httpx` 后重试。

### M-G2 · 契约库与包初始化文件含 0 个工具函数

```bash
cd "$WS" && grep -c "@tool" tools/changes.py tools/__init__.py   # 期望均为 0
grep -c "@tool" tools/filesystem.py tools/commandline.py tools/webfetch.py   # 期望 7 / 1 / 1
```

### M-G3 · 文件工具 7 个动作

```bash
cd "$WS" && python - <<'PY'
import json
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat

r = json.loads(write_file.invoke({"path": "demo.txt", "content": "hello\n"}))
print("write:", r["action"], r["applied"], r["change"]["version"], r["change"]["new_hash"][:20])
print("read :", read_file.invoke({"path": "demo.txt"}).splitlines()[:3])
print("list :", list_dir.invoke({"path": "."})[:5])
print("stat :", stat.invoke({"path": "demo.txt", "with_hash": True}))
print("copy :", json.loads(copy_file.invoke({"src":"demo.txt","dst":"demo2.txt"}))["action"])
print("move :", json.loads(move_file.invoke({"src":"demo2.txt","dst":"demo3.txt"}))["action"])
print("del  :", json.loads(delete_file.invoke({"path":"demo3.txt"}))["action"])
PY
```

**期望**：
- `write` → `action=create`、`applied=true`、`change.version=1`；
- `read` → 首行 `Read file demo.txt, lines 1-1`，次行 `1: hello`；
- `stat` → 返回**可取字段的映射**（不是 JSON 文本），含 `is_file` / `is_dir` / `size` / `mtime`；
- `list` → 返回**名称列表**（`list[str]`，不是 JSON）；
- `copy` / `move` / `del` → `action` 分别为 `copy` / `move` / `delete`。

> **注意**：`read_file` 的返回值是**呈现文本**（页范围头 + `<行号>: ` 前缀），**不是纯正文**。
> 程序化调用方要正文必须自己读文件 —— 这是 v1 明确登记的已知缺口。

### M-G4 · 命令工具

```bash
cd "$WS" && python - <<'PY'
import json
from tools.commandline import run_shell
r = json.loads(run_shell.invoke({"command": "echo hello"}))
print("stdout:", repr(r["stdout"]), "| rc:", r["returncode"], "| truncated:", r["truncated"], "| timed_out:", r["timed_out"])
t = json.loads(run_shell.invoke({"command": "sleep 5", "timeout": 1}))
print("timeout:", t["timed_out"], "| rc:", t["returncode"])
PY
```

**期望**：`stdout` 含 `hello`、`returncode=0`、`truncated=false`、`timed_out=false`；
超时时 **`timed_out=true`、`returncode=-1`，且不抛异常**（超时以**返回值里的结构化标记**表达）。

### M-G5 · 命令输出超限被截断

```bash
cd "$WS" && python - <<'PY'
import json
from tools.commandline import run_shell
r = json.loads(run_shell.invoke({"command": "seq 1 5000"}))
print("truncated:", r["truncated"])
print("末行:", r["stdout"].splitlines()[-1])
PY
ls "$WS"   # 期望：**没有**多出任何输出落盘文件
```

**期望**：`truncated=true`；末行形如 `[showing lines 1-2000 of 5000; full output not saved]`；
工作区里**不出现**完整输出文件（完整输出**不落盘**）。

### M-G6 · 网络工具的四道边界

```bash
cd "$WS" && python - <<'PY'
from tools.webfetch import fetch_url
for url in ("ftp://example.com/x", "file:///etc/passwd"):
    try:
        fetch_url.invoke({"url": url}); print("!! 未拒绝", url)
    except Exception as e:
        print("协议白名单 已拒绝:", type(e).__name__)
try:
    fetch_url.invoke({"url": "https://example.com", "timeout": 999}); print("!! 未拒绝 超时上限")
except Exception as e:
    print("超时上限 已拒绝:", type(e).__name__)
PY
```

**期望**：三项全部被拒绝（协议白名单 ×2、超时上限 ×1，> 120 秒不允许）。

### M-G7 · 地址范围**不被**限制

```bash
cd "$WS" && python - <<'PY'
from tools.webfetch import fetch_url
try:
    fetch_url.invoke({"url": "http://127.0.0.1:9/ping"})
    print("回环地址 被放行")
except Exception as e:
    print("!! 回环地址被拦 —— 违反规格:", type(e).__name__)
PY
```

**期望**：打印"被放行"，**不得**出现"被拦"。
> 这一条是**有意设计**：协议与体积有限制，**地址范围不设限**（黑名单 / 白名单 / 代理 / 沙箱一律不实现）。
> 地址白名单由**用户自管**，与"路径白名单由用户自管"同构。

### M-G8 · 网络工具的说明文字逐条写明四道边界

```bash
for w in "http" "https" "5 MiB" "MIME" "2xx"; do
  printf "%-8s %s\n" "$w" "$(grep -oF "$w" "$WS"/tools/webfetch.py | wc -l)"
done
grep -n "trust_env" "$WS"/tools/webfetch.py
```

**期望**：五个计数**均 ≥ 1**；`trust_env=False` 存在（客户端**不得**隐式读取代理 / 证书环境变量）。

---

## 8. H 组 · 变更记录契约

### M-H1 · 变更记录 12 个基线字段

```bash
cd "$WS" && python - <<'PY'
import json
from tools.filesystem import write_file
r = json.loads(write_file.invoke({"path": "c.txt", "content": "a\nb\n"}))
ch = r["change"]
print("字段:", sorted(ch.keys()))
print("version:", ch["version"], "| previous_hash:", ch["previous_hash"], "| new_hash:", ch["new_hash"][:16])
PY
```

**期望**：基线字段恰好 **12** 个：
`version` / `action` / `path` / `rel_path` / `previous_exists` / `previous_size` / `previous_hash` / `new_size` / `new_hash` / `unified_diff` / `diff_truncated` / `applied`。
首次写入时 `previous_hash` 为 **`null`（Python 侧 `None`，不是空串）**。

### M-H2 · 二次写入的指纹接力

```bash
cd "$WS" && python - <<'PY'
import json
from tools.filesystem import write_file
r1 = json.loads(write_file.invoke({"path": "c.txt", "content": "a\nb\n"}))
r2 = json.loads(write_file.invoke({"path": "c.txt", "content": "a\nc\n"}))
print("上次 new_hash == 本次 previous_hash:", r1["change"]["new_hash"] == r2["change"]["previous_hash"])
print("差异行:", [l for l in r2["change"]["unified_diff"].splitlines() if l.startswith(("+","-"))])
PY
```

**期望**：接力成立（`r1.new_hash == r2.previous_hash`）；差异文本含 `-b` 与 `+c`
（另有两行差异头 `--- a/c.txt` / `+++ b/c.txt`，头里的路径是**工作区相对路径**）。

### M-H3 · 预览模式（只算不写）

```bash
cd "$WS" && python - <<'PY'
import json
from tools.filesystem import write_file
before = open("c.txt").read()
r = json.loads(write_file.invoke({"path": "c.txt", "content": "zzz\n", "dry_run": True}))
print("applied:", r["applied"], "| change.applied:", r["change"]["applied"])
print("磁盘未变:", open("c.txt").read() == before)
print("差异非空:", len(r["change"]["unified_diff"]) > 0)
PY
ls -a "$WS" | grep -F ".donkey-tmp" || echo "无临时文件残留"
```

**期望**：`applied=false`；**磁盘逐字节未变**；差异文本**非空**；
**无临时文件残留**（原子写的临时文件后缀是 `.donkey-tmp`、名字以点开头）。

### M-H4 · 乐观锁（期望指纹不匹配 → 拒绝）

```bash
cd "$WS" && python - <<'PY'
from tools.filesystem import write_file
from tools.changes import FileChangedError
before = open("c.txt").read()
try:
    write_file.invoke({"path": "c.txt", "content": "x\n", "expected_hash": "sha256:deadbeef"})
    print("!! 未被拒绝")
except FileChangedError as e:
    print("已拒绝:", type(e).__name__)
print("磁盘未变:", open("c.txt").read() == before)
PY
```

**期望**：抛 `FileChangedError`；**磁盘未变**（写入被完全拒绝，不留半成品）。

### M-H5 · 复制 / 移动 / 删除也带乐观锁与预览

```bash
cd "$WS" && python - <<'PY'
import json, os
from tools.filesystem import copy_file, move_file, delete_file
from tools.changes import FileChangedError
for fn, args in ((copy_file, {"src":"c.txt","dst":"x.txt"}),
                 (move_file, {"src":"c.txt","dst":"y.txt"}),
                 (delete_file, {"path":"c.txt"})):
    try:
        fn.invoke({**args, "expected_hash": "sha256:deadbeef"})
        print("!! 未被拒绝:", fn.name)
    except FileChangedError:
        print("已拒绝:", fn.name)
print("x/y 存在:", os.path.exists("x.txt"), os.path.exists("y.txt"), "| c.txt 仍在:", os.path.exists("c.txt"))
PY
```

**期望**：三者**全部**拒绝；**零磁盘副作用**。

### M-H6 · 删除的变更记录

```bash
cd "$WS" && python - <<'PY'
import json, os
from tools.filesystem import delete_file
r = json.loads(delete_file.invoke({"path": "c.txt"}))
print("action:", r["action"], "| previous_hash:", r["change"]["previous_hash"][:16], "| new_hash:", r["change"]["new_hash"])
print("文件已删:", not os.path.exists("c.txt"))
PY
```

**期望**：`action=delete`；`previous_hash` 非空；`new_hash` 为 **`null`**；文件确实消失。

### M-H7 · 契约版本冻结

```bash
cd "$WS" && python -c "from tools.changes import CHANGE_RECORD_VERSION; print(CHANGE_RECORD_VERSION)"
```

**期望**：`1`（消费方按版本分派，字段只增不改）。

### M-H8 · 读取侧双上限与续读指针

```bash
cd "$WS" && python - <<'PY'
from tools.filesystem import write_file, read_file
# ① 行数超限
write_file.invoke({"path": "big_lines.txt", "content": "".join(f"line {i}\n" for i in range(3000))})
# ② 体积超限
write_file.invoke({"path": "big_bytes.txt", "content": "x" * 60000 + "\n"})
for f in ("big_lines.txt", "big_bytes.txt"):
    ls = read_file.invoke({"path": f}).splitlines()
    print(f, "| 首行:", ls[0], "| 末行:", ls[-1])
PY
```

**期望**：两者都被截断；末行为 `[Output truncated. Continue reading with offset: N]`（N 为下一段起始行号）。

### M-H9 · 区分样本：体积 ≤ 50 KiB 但行数 > 2000

```bash
cd "$WS" && python - <<'PY'
from tools.filesystem import write_file, read_file
write_file.invoke({"path": "many_lines.txt", "content": "".join(f"{i}\n" for i in range(2500))})
import os; print("体积 KiB:", round(os.path.getsize("many_lines.txt")/1024, 1))
ls = read_file.invoke({"path": "many_lines.txt"}).splitlines()
print("首行:", ls[0]); print("末行:", ls[-1])
PY
```

**期望**：体积远小于 50 KiB，但**行数上限无条件生效** → 仍被截断，且带续读指针。

### M-H10 · 二进制文件读取报错

```bash
cd "$WS" && python - <<'PY'
open("bin.dat","wb").write(b"abc\x00def")
from tools.filesystem import read_file
try:
    read_file.invoke({"path": "bin.dat"}); print("!! 未报错")
except Exception as e:
    print("已报错:", type(e).__name__, str(e)[:60])
PY
```

**期望**：明确报错，**不得**把乱码当正文返回。

### M-H11 · 相对路径以**工作区根**为基准（与进程 CWD 无关）

```bash
cd /tmp && python - <<PY
import sys; sys.path.insert(0, "$WS")
from tools.filesystem import write_file, list_dir
write_file.invoke({"path": "cwd_test.txt", "content": "x\n"})
print("文件落在工作区根:", __import__("os").path.exists("$WS/cwd_test.txt"))
print("文件落在 /tmp:", __import__("os").path.exists("/tmp/cwd_test.txt"))
PY
```

**期望**：文件落在**工作区根**，**不得**落在 `/tmp`（进程 CWD）。

---

## 9. I 组 · 示例 Skill 的三层结构

**目的**：确认示例 Skill **照抄就能用** —— 三层齐备、占位符规范、入口块合规。

```bash
cat "$WS"/skills/example/SKILL.md
ls -R "$WS"/skills/example
```

**期望**：
- **第一层**：文件以 `---` 分隔符开头，元信息**恰好 2 个字段**（`name` + `description`）；
- **第二层**：正文非空，且讲清了"三层渐进披露"模型，示例路径**相对于工作区根**；
- **第三层**：至少 1 个文件，且**三种形态齐备** —— 参考文档（`reference/`）、脚本（`scripts/`）、模板（`templates/`）；
- 第三层文件**不得**含 `{{ … }}` 占位符（用 `<<title>>` / `<title>`），否则会破坏"渲染后无占位符残留"这条持久不变量。

> **注意**：`skills/example/scripts/example.py` 带 `if __name__ == "__main__":` 入口块 ——
> 这是**宪法已登记的例外**（§6.3 例外 E-02 + §5 章 [D-19]），**不得**被判为"工作区禁止 Python 入口"违例。

---

## 10. J 组 · 工作区身份与可移植性

**目的**：确认工作区**可以打包带走**、**不绑死在生成它的那台机器上**。

| 编号 | 操作 | 期望 |
|---|---|---|
| M-J1 | 把工作区整个拷到别处再导入工具 | 全部导入成功、全部可调用（工作区**可携带**） |
| M-J2 | 把 `tools/` 整个移走后再调用相对路径工具 | 相对路径基准**随 `tools/` 一起移动**；**不得**回落到环境变量或进程 CWD |
| M-J3 | `grep -rn "getenv\|environ" "$WS"/tools/` | **零命中** —— 工具的行为**不得**被环境变量改变 |

**M-J1 操作**：

```bash
rm -rf /tmp/dk_copy && cp -r "$WS" /tmp/dk_copy
cd /tmp/dk_copy && python - <<'PY'
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat
from tools.commandline import run_shell
from tools.webfetch import fetch_url
print("9 个工具全部可调用")
PY
```

**M-J2 操作**：

```bash
mv "$WS"/tools /tmp/dk_moved_tools
python - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location("changes", "/tmp/dk_moved_tools/changes.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("workspace_root:", m.workspace_root())   # 期望：/tmp/dk_moved_tools 的父目录
PY
mv /tmp/dk_moved_tools "$WS"/tools
```

**期望**：工作区根由**契约库自身的位置**推导 —— `tools/` 移到哪，基准就跟到哪。

---

## 11. L 组 · 版本查询 `donkey version`（P4 · 只读元信息命令）

**目的**：确认这条**纯只读**的元信息命令行为可预期 —— 输出一行**裸版本值**、**不碰**文件系统、
**用错**时报错方式与 `donkey init` 一致、**装没装**都给得出确定的版本。

> 📌 **它是什么**：donkey 只有**一个**版本号（软件功能版本 ≡ 图版本 ≡ 包版本）。
> `v` 是**显示前缀**（宪法 §4.5 的 `vx.y.z` 记法），不是版本号的一部分 —— 底层取值 `0.1.0` 与
> `pyproject.toml`、包内 `__version__`、工作区清单 `manifest.json` 的 `donkey_version` 字段**逐字节一致**。
>
> 📌 **取值的来源**：优先读**安装分发元数据**；取不到时回退包自身的 `__version__` —— 两者不一致时**以元数据为准**
> （它代表用户实际装上的那一份）。**取值不依赖**当前目录有没有工作区。

| 编号 | 操作 | 期望 |
|---|---|---|
| M-L1 | `donkey version` | 退出码 **0**；stdout **恰好一行** `v0.1.0` —— **裸版本值**：无 `[donkey version]` 前缀、无 `version=` 字段名、无首尾空白；stderr **为空** |
| M-L2 | `donkey version \| wc -l` | **1**（不是 0，也不是 2） |
| M-L3 | 连续两次 `donkey version`，逐字节比对 stdout | **完全相同** —— 输出不得含时间戳 / 主机名 / 路径 / 进程号 |
| M-L4 | `donkey version \| grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+'` | **恰好 1** 个版本值 —— 不得出现第二个版本值、客户端版本或节点级信息 |
| M-L5 | 在**不存在工作区**的目录里执行 `donkey version` | 退出码 **0**；**目录树零变化**（`find` 前后 `diff` 为空）；**不得**创建 `manifest.json` 或任何文件 |
| M-L6 | `donkey version` 与 `python -m donkey version` | 退出码相同、stdout **逐字节相同**、stderr 均为空 |
| M-L7 | `donkey version --bogus` / `donkey version web` / `donkey version extra` | 三者退出码**均为 1**（**不是 2**）；stdout **为空**；stderr 含用法提示 |
| M-L8 | `donkey version --help` / `donkey --version` | 前者退出码 **0**；后者退出码 **1** 且**不输出任何版本号**（顶层**不提供** `--version` 标志） |
| M-L9 | 取不到安装分发元数据的环境（见下方操作） | 退出码 **0**；stdout 仍是 `v0.1.0` —— **不得**抛异常、**不得**输出空值 |

**M-L5 操作**（确认"一个字节都不写"）：

```bash
mkdir -p /tmp/dk_v && cd /tmp/dk_v
find . | sort > /tmp/v_before.txt
donkey version
find . | sort > /tmp/v_after.txt
diff /tmp/v_before.txt /tmp/v_after.txt && echo "目录树零变化"
ls -a | grep -F manifest.json || echo "工作区清单未被创建"
```

**M-L9 操作**（复现"没装 donkey"的环境 —— `-S` 屏蔽 site-packages，**不可省**）：

```bash
rm -rf /tmp/dk_iso && mkdir -p /tmp/dk_iso
cp -r <仓库根>/donkey /tmp/dk_iso/donkey          # 副本同级没有 *.egg-info
cd /tmp/dk_iso
python -S -c "import importlib.metadata as md; md.version('donkey')" 2>&1 | tail -1
# 期望：PackageNotFoundError: No package metadata was found for donkey
python -S -m donkey version; echo "rc=$?"
# 期望：v0.1.0 / rc=0
```

> **L 组要点**：
> - 这条命令**只读** —— 它是"查"，不是"做"。任何写盘行为都是缺陷。
> - 它的 stdout 是**裸版本值**，**有意不同**于 `donkey init` 的「单行 `key=value` 摘要」——
>   目的是让 `V=$(donkey version)` 能直接取用。
> - 用法错误**必须**折叠成 `1`（与 `donkey init` 同码）；`2` 在 `init` 段位里是"权限不足"，混用会让脚本误判。
> - **顶层没有 `--version`** —— 版本查询的**唯一入口**是 `donkey version` 子命令。
> - `donkey version web` / `donkey version extra` **必须**被拒绝，**不得**被静默忽略。

---

## 12. K 组 · 回归门禁（人工测试结束前跑一遍）

```bash
pytest tests/e2e/phase/verify_phase_f001_p1.py -v
pytest tests/e2e/phase/verify_phase_f001_p2.py -v
pytest tests/e2e/phase/verify_phase_f001_p3.py -v
pytest tests/e2e/phase/verify_phase_f001_p4.py -v
pytest tests/unit/ -v
pytest tests/integration/ -v

ruff check donkey/ tests/
mypy donkey/ tests/
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80
```

**期望**：全部通过，ruff / mypy 零告警，覆盖率 ≥ 80%。
（`verify_phase_f001_p4.py` 是 P4 的验收脚本 —— **7 个** `test_scenario_*` 断言，与 L 组逐条对应。）

**另外自检**：

```bash
test -f .github/workflows/ci.yml && echo "OK ci.yml 已交付" || echo "FAIL ci.yml 缺失"
grep -cE "pytest tests/|--cov=donkey.core|--cov-fail-under=80|ruff check|mypy" .github/workflows/ci.yml
```

**期望**：文件存在；四类关键命令全部命中。

---

## 13. 已知问题与待观察点（BUG 候选清单）

> 以下均为**已在当前实现中确认存在**的现象。人工测试时重点复核它们的影响面，
> 并确认是否值得开单。**不要求本轮全部修完**，但 MUST NOT 在已知的情况下发版。
>
> **已修复项保留编号**（便于与历史记录 / 缺陷单对照），并在"状态"列注明关闭依据。

| 编号 | 现象 | 影响 | 建议 | 状态 |
|---|---|---|---|---|
| **K-1** | ~~`donkey init --help` 与 `donkey --help` 仍写 **"生成模板骨架（46 个模板条目）"**，而实际清单已增到 **54** 条~~ | 用户按帮助文档核对数量会对不上；`donkey/core/api.py` 的 `InitResult` docstring 同样停留在 46 / 40 | 同步帮助文案与 docstring 到 54 / 48 | ✅ **已修复（F001-P4）** —— `donkey init --help` 两处文案改为 **54**；`InitResult` docstring 三处改为 **54 / 48 / 48**（含 "45 文本 + 3 sqlite3" 的分解）。**K-9 仍开放** |
| **K-2** | **`run_shell` 遇到管道 / 重定向 / `&&` 时不报错**。`echo hello \| grep hello` 被 `shlex.split` 拆成参数数组，管道符号成为 `echo` 的普通参数 → 输出 `hello \| grep hello`、`returncode=0`；且工具 docstring **未明写"不支持管道"** | **最危险的一条**：模型会以为管道跑通了并据此推理，实际什么都没做；规格要求"如实报告失败" | 检测 shell 元字符（`\|` `&&` `\|\|` `;` `>` `>>` `$()`）→ 明确报错或至少在返回值里标记；docstring 补一句"不支持管道 / 重定向" | 开放 |
| **K-3** | `run_shell` 的 `cwd` 指向不存在的目录时，`subprocess` 的 `FileNotFoundError` **带完整堆栈**抛出 | 堆栈里夹带内部帧，对模型不友好（规格只要求抛具体异常类型） | 预先校验 `cwd` 存在性，抛带工作区路径的自定义错误 | 开放 |
| **K-4** | `read_file` 的返回值是**呈现文本**（页范围头 + 行号前缀），不是纯正文 | 程序化调用方无法直接拿到正文 | 已在规格登记为 v1 已知缺口；**需在 `tools/README.md` 里再加一句醒目提示** | 开放 |
| **K-5** | `list_dir` 返回 `list[str]`（不是 JSON），条目超上限时分页指引只能靠说明文字承载 | 目录型返回缺少结构化分页信息 | 规格已冻结该返回类型，暂不改；可在 docstring 里补分页说明 | 开放 |
| **K-6** | 退出码 **4**（`BuiltinToolGenerationError`）**当前不可达** —— 内置工具是"清单条目"实现的，写失败会被归入退出码 3 | 规格 P3 声称的退出码 4 实际从不触发；错误归类与规格不一致 | 要么在渲染内置工具条目时把失败改判为 4，要么修订规格承认 4 号不可达 | 开放 |
| **K-7** | `tools/webfetch.py` 在**模块层** `import httpx` | 未装 httpx 的工作区里，**该模块导入即失败**；若工具扫描器逐个导入全部 `tools/*.py`，会连带影响其它工具的加载 | 规格已要求 `tools/README.md` 写明；建议同时评估"延迟导入"或"扫描器容错" | 开放 |
| **K-8** | `--force` 的警告行**恒定打印**，哪怕三个记忆库原本就不存在（首次 init 就带 `--force`） | 提示语"已被清空"与事实不符 | 改为按实际清理情况决定是否打印，或调整措辞为"将被重建" | 开放 |
| **K-9** | 阶段 2 的合同文档（`phase-2-template-skeleton/contracts/*.md`）仍引用旧计数（46 条目 / 40 文件）与旧警告措辞 | 文档与实现不一致，人工核对时会被误导 | **本轮有意不改** —— 该目录是 F001-P2 的**冻结快照**，差额已由 F001-P3 的契约文档登记为当前口径（54 = 46 + 8）；回改它等于篡改已交付 Phase 的历史记录 | 开放 |
| **K-10** | `tools/README.md` 第一节写"工具文件名用小写下划线（如 `web_fetch`）"，但内置工具实际叫 `webfetch.py` | 示例与实物不一致 | 统一措辞 | 开放 |
| **K-11** | `donkey web version` / `donkey gui version` **未实现** —— 客户端侧没有版本入口 | 版本查询目前**只有 cli 一端**；宪法 N-11 要求 v1 三端对等（cli / web / gui 缺一不可） | 归 **F005 / F006** 各自落地；本轮**只登记、不实现**，且**不得**写解析器占位（占位会让未交付的能力被报成已交付） | 开放 |
| **K-12** | 节点级版本号（`vx.y.z` 中的 `y` = 节点 id / `z` = 节点修改次数）**未暴露** | 用户看到的是**一个**整体版本号，看不到逐节点版本 | 归 **F004-P7 `agent_loop`**（图建成后才存在节点）；本轮**不实现、不展示** | 开放 |
| **K-13** | `tests/e2e/phase/verify_phase_f001_p2.py` 场景 1 的 docstring 仍写「全部 **46** 条落地物就位」 | 人工核对时会与实现对不上 | **本轮有意不改** —— 该文件是 F001-P2 的**冻结快照**（受 FR-034 保护）；口径差异已由 F001-P3 的契约文档登记为当前权威口径 | 开放 |

---

## 14. 缺陷记录模板

每发现一个问题，复制一份以下模板记录：

```markdown
### [BUG-nnn] 一句话标题

- **严重级别**：阻塞 / 严重 / 一般 / 轻微
- **发现用例**：M-xxx
- **复现步骤**：
  1.
  2.
  3.
- **期望结果**：
- **实际结果**：
- **实际输出（粘贴原始 stdout / stderr）**：
  ```
  ```
- **判定依据**：spec FR-xxx / SC-xxx / 用户手册第 x 章
- **是否需要改规格**：是（涉及 FR / SC 变更）/ 否（纯实现缺陷）
```

---

## 15. 人工测试完成后的检查清单

- [ ] A 组 8 条全过（CLI 面冻结、两个入口等价、子命令列表含 `version`）
- [ ] B 组 8 条全过（路径校验，且**不产生半成品目录**）
- [ ] C 组 3 条全过（权限错误与路径错误**分得开**）
- [ ] D 组 9 条全过（计数 / 目录树 / 文件总数 / 清单 / 名称注入 / 26 份 TOML / mcp.json / 三个记忆库 / `--force` 清空历史）
- [ ] E 组 4 条全过（幂等：内容与 mtime 均不变；缺文件补回；清单外内容不动）
- [ ] F 组 7 条全过（`--force` 作用域；**契约库豁免**；边车文件清理）
- [ ] G 组 8 条全过（9 工具可导入 / 7 动作 / 命令工具 / 截断不落盘 / 网络四道边界 / 地址不设限 / 说明文字）
- [ ] H 组 11 条全过（12 字段 / 指纹接力 / 预览 / 乐观锁 / 删除记录 / 版本冻结 / 双上限 / 区分样本 / 二进制 / 路径基准）
- [ ] I 组 3 条全过（Skill 三层齐备、无占位符残留）
- [ ] J 组 3 条全过（可移植 / 基准随目录移动 / 不读环境变量）
- [ ] L 组 9 条全过（一行裸版本值 / 行数为 1 / 确定性 / 唯一版本值 / **零副作用** / 双入口等价 / 用法错误为 1 / `--help` 与顶层 `--version` / 无元数据回退）
- [ ] K 组回归门禁全绿
- [ ] 第 13 章的 13 条已知问题已逐条复核，并决定各自的处置（修复 / 登记为已知 / 修订规格）
- [ ] 缺陷清单已汇总，阻塞级问题为零
