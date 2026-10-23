# 快速验证指南 —— F001-P2 `template_skeleton`

**Phase**: F001-P2（`donkey init` 模板骨架幂等生成）
**上游**：[spec.md](spec.md) / [plan.md](plan.md) / [research.md](research.md) / [data-model.md](data-model.md) / [contracts/](contracts/)
**日期**: 2026-10-23

> 本文件是**可复制执行的验证手册** —— 每条命令都给出**期望结果**，可直接用作验收 checklist。
> 不含实现代码；契约细节见 [contracts/](contracts/)，口径推导见 [data-model.md](data-model.md)。

---

## 0. 前置条件

| 项 | 要求 |
|---|---|
| Python | ≥ 3.11（`tomllib` 内置） |
| 工作目录 | 仓库根 `donkey/`（`pwd` 应显示 `.../donkey`） |
| 依赖 | §1 的环境自检**通过**后再继续 |

---

## 1. 环境自检（装依赖后立即跑）

> **为什么放在最前**：本 Phase 引入第一个运行期依赖，且本机存在 `langgraph-checkpoint-sqlite 3.1.1` + `langgraph-checkpoint 4.2.0` 的**不兼容组合**
> （导入即 `ImportError: cannot import name 'writes_sort_key'`）。先验证环境，避免把环境问题误判为实现缺陷。

```bash
cd /home/ctyun/workspace/github/donkey
.venv/bin/pip install -e .          # 或 pip install -e ".[dev]"
```

**① 依赖解析自检** —— 期望：`langgraph-checkpoint-sqlite` 与 `langgraph-checkpoint` 都在，且 checkpoint ≥ 4.3.0

```bash
.venv/bin/pip list 2>/dev/null | grep -iE "langgraph-checkpoint|langchain-core|aiosqlite|sqlite-vec"
```

**② 上游 saver 冒烟（导入 + 建表 + langsmith 零进入）** —— 期望：打印 `OK 3 tables`，且 `langsmith in sys.modules` 为 `False`

```bash
.venv/bin/python -c "
import sqlite3, sys, tempfile, pathlib
from langgraph.checkpoint.sqlite import SqliteSaver
p = pathlib.Path(tempfile.mkdtemp())/'x.sqlite3'
c = sqlite3.connect(str(p)); SqliteSaver(c).setup()
c.execute('CREATE TABLE IF NOT EXISTS sessions_metadata (thread_id TEXT PRIMARY KEY, title TEXT NOT NULL)')
c.commit()
tables = sorted(r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"))
c.close()
print('OK', len(tables), 'tables', tables)
print('langsmith in sys.modules:', 'langsmith' in sys.modules)
"
```

| 现象 | 含义 | 处置 |
|---|---|---|
| `ImportError: cannot import name 'writes_sort_key'` | 版本不兼容（checkpoint < 4.3.0） | `pip install -U "langgraph-checkpoint>=4.3.0" "langgraph-checkpoint-sqlite>=3.1,<4"` |
| `langsmith in sys.modules: True` | **门禁失败**（违反 N-12） | 停止实施；查清是哪条 import 链拉起 langsmith |
| `OK 3 tables` | 环境就绪 | 继续 §2 |

> 依据：[research.md](research.md) R-01 / R-02 —— 实测导入上游 saver 新增 471 个模块，langsmith 相关 **0** 个。

---

## 2. 手动冒烟（4 场景）

> 契约见 [contracts/cli-contract.md](contracts/cli-contract.md) §4。全部命令在**临时目录**执行，**MUST NOT** 在真实工作区上试。

```bash
WS=$(mktemp -d)/ws
```

### 场景 1 · 全新创建 → 期望 `exit 0` + `templates=46 created=40 skipped=0`

```bash
donkey init "$WS"; echo "exit=$?"
```

**期望**：输出含 `templates=46 created=40 skipped=0`；`$WS` 下出现 5 大目录 + 37 个文件 + 3 个 sqlite3 + 工作区清单。

```bash
find "$WS" -type f | wc -l          # 期望 41（37 文本 + 3 sqlite3 + 1 工作区清单）
find "$WS" -type d | wc -l          # 期望 7（根 + 5 必填 + skills/example）
```

### 场景 2 · 幂等补齐 → 期望 `created=0 skipped=40` 且用户内容零改动

```bash
echo "我的自定义提示词" > "$WS/instruction.md"
BEFORE=$(stat -c %Y "$WS/instruction.md")
donkey init "$WS"; echo "exit=$?"
AFTER=$(stat -c %Y "$WS/instruction.md")
[ "$BEFORE" = "$AFTER" ] && echo "OK mtime 未变" || echo "FAIL mtime 被改写"
cat "$WS/instruction.md"             # 期望仍是"我的自定义提示词"
```

### 场景 3 · 模板重置 → 期望内容恢复出厂 + **多出强制清空提示行**

```bash
donkey init "$WS" --force; echo "exit=$?"
cat "$WS/instruction.md"             # 期望：出厂内容，无"我的自定义提示词"
```

**期望输出**含**两行**：摘要行 + 一行显式提示（记忆库数据已清空）。

```bash
donkey init "$WS" --force 2>&1 | grep -c "清空"     # 期望 ≥ 1
donkey init "$WS" 2>&1 | grep -c "清空"             # 期望 0（无 --force 时不出现）
```

### 场景 4 · 放弃重做 → 期望与场景 1 等价

```bash
rm -rf "$WS"
donkey init "$WS"; echo "exit=$?"
```

### 附加 · 用户内容在 `--force` 下零改动

```bash
mkdir -p "$WS/media"; echo fake > "$WS/media/video.mp4"; echo log > "$WS/donkey.log"
donkey init "$WS" --force >/dev/null
[ -f "$WS/media/video.mp4" ] && [ "$(cat "$WS/donkey.log")" = "log" ] && echo "OK 用户内容未被触碰" || echo "FAIL 用户内容被破坏"
```

---

## 3. 静态检查

```bash
.venv/bin/ruff check donkey/ tests/
.venv/bin/mypy donkey/ tests/
```

**期望**：两条命令均**零 error 零 warning**（spec SC-009）。

---

## 4. 分层边界自检（宪法 N-03 / N-04 / N-05 / N-12）

> 全部**期望无输出**（即 grep 无命中）。

```bash
# N-03：核心层不得 import 客户端
grep -rnE "^\s*(from|import)\s+donkey\.(cli|web|gui)" donkey/core/ || echo "OK"

# N-05：核心层不得依赖命令行框架 / 进程参数
grep -rnE "^\s*(from|import)\s+(argparse|click|typer)|sys\.argv" donkey/core/ || echo "OK"

# N-04：客户端层不得直接 import langchain / langgraph / sqlite3
grep -rnE "^\s*(from|import)\s+(langchain|langgraph|sqlite3)" donkey/cli/ || echo "OK"

# N-12：全仓不得出现 LangSmith 任何形态 / deepagents / ShellToolMiddleware
grep -rniE "langsmith|LANGCHAIN_TRACING|LANGSMITH_|deepagents|ShellToolMiddleware" donkey/ tests/ || echo "OK"
```

**注意**：`langsmith` 作为 `langchain-core` 的**传递依赖**会被安装到磁盘（无法也不必避免）——
本检查针对的是**代码中出现**，不是磁盘上存在包（[research.md](research.md) R-02）。

---

## 5. 验收脚本与回归

```bash
# 本 Phase（14 个黑盒场景）
.venv/bin/pytest tests/e2e/phase/verify_phase_f001_p2.py -v

# 前置 Phase 回归（必须仍全绿 —— spec SC-002）
.venv/bin/pytest tests/e2e/phase/verify_phase_f001_p1.py -v
.venv/bin/pytest tests/unit/test_init_workspace.py tests/unit/test_cli_client.py -v

# 本 Phase 单元测试（≥16 个用例 —— spec SC-008）
.venv/bin/pytest tests/unit/test_template_skeleton.py -v

# 全量
.venv/bin/pytest tests/ -v
```

**期望**：全部 PASS；其它 Phase 的测试允许 FAIL。

---

## 6. 覆盖率（spec SC-013 / 宪法 §4.6）

```bash
.venv/bin/pytest tests/unit/ --cov=donkey.core --cov-fail-under=80
```

**期望**：`donkey.core` 行覆盖率 **≥ 80%**。

> **MUST NOT** 把 `--cov` 写进 `pyproject.toml` 的 pytest 全局 `addopts` —— e2e 黑盒脚本不 import 业务代码，
> 单独运行 e2e 时会把覆盖率拉到 0 而误报失败（[research.md](research.md) R-13）。
> e2e 黑盒脚本**不计入**该覆盖率。

---

## 7. 构建期自检（模板资产 —— 契约 B1 ~ B12）

> 完整清单见 [contracts/template-manifest.md](contracts/template-manifest.md) §7。
> 本节命令块覆盖契约定义的 **B1 ~ B12 共 12 项**（B2b 是 §7.1 的**扩展项**，不占契约编号）。

```bash
T=donkey/core/workspace/templates

# B1：清单条目总数 = 46
python3 -c "import json;print(len(json.load(open('$T/manifest.json'))['entries']))"   # 期望 46

# B2：文本条目 ↔ 源文件一一对应（各 37）
python3 -c "
import json,pathlib
T=pathlib.Path('$T'); e=json.load(open(T/'manifest.json'))['entries']
text={x['path'] for x in e if x['format'] not in ('directory','sqlite3')}
nosrc={x['path'] for x in e if x['format'] in ('directory','sqlite3')}
have={str(p.relative_to(T))[:-4] for p in T.rglob('*.txt')}
print('文本条目',len(text),'源文件',len(have),'孤儿源',sorted(have-text),'缺源',sorted(text-have))
print('非文本条目误带源',sorted(nosrc & have))
"

# B5/B6/B7：26 份 provider 可解析 + 开关全关 + 模型条目合计 51
python3 -c "
import tomllib,pathlib,re
P=pathlib.Path('$T/providers'); ids=[p.stem for p in P.glob('*.toml.txt')]
n=0
for i in sorted(ids):
    d=tomllib.loads((P/f'{i}.toml.txt').read_text(encoding='utf-8'))
    assert d['enabled'] is False, i
    n+=len(re.findall(r'^\[models\.', (P/f'{i}.toml.txt').read_text(encoding='utf-8'), re.M))
print('provider 份数',len(ids),'模型条目合计',n)   # 期望 26 份 / 51 条
"

# B11：安装包不得携带二进制 sqlite3 模板
find "$T" -name "*.sqlite3" -o -name "*.db" | grep . && echo "FAIL" || echo "OK 无二进制模板"

# B3/B4：目录条目与 sqlite3 条目 MUST NOT 配备同名 .txt 源
python3 -c "
import json,pathlib
T=pathlib.Path('$T'); e=json.load(open(T/'manifest.json'))['entries']
bad=[x['path'] for x in e if x['format'] in ('directory','sqlite3') and (T/(x['path']+'.txt')).exists()]
print('非文本条目误带源',bad); assert not bad
"

# B8/B9/B10：default.toml 可解析且两字段为空串 / mcp.json 可解析且含 mcpServers / SKILL.md frontmatter 恰 2 字段
python3 -c "
import tomllib,json,pathlib
T=pathlib.Path('$T')
d=tomllib.loads((T/'providers/default.toml.txt').read_text(encoding='utf-8'))
assert d['default_provider']=='' and d['default_model']=='', d
m=json.loads((T/'mcp/mcp.json.txt').read_text(encoding='utf-8'))
assert 'mcpServers' in m and m['mcpServers']=={}, m
fm=(T/'skills/example/SKILL.md.txt').read_text(encoding='utf-8')
assert fm.startswith('---'), 'frontmatter 未以 --- 开头'
body=fm.split('---')[1]
keys=[l.split(':',1)[0].strip() for l in body.splitlines() if ':' in l and not l.strip().startswith('#')]
assert set(keys)=={'name','description'}, keys
print('OK B8/B9/B10')
"

# B12：渲染后无 {{ 占位符残留
python3 - <<'EOF'
import pathlib, tempfile
from donkey.core.workspace.init import load_template_manifest, render_templates
T = pathlib.Path("donkey/core/workspace/templates")
entries = load_template_manifest(T / "manifest.json")
with tempfile.TemporaryDirectory() as d:
    render_templates(pathlib.Path(d), "b12 ws", False, entries, T)
    bad = [str(p.relative_to(d)) for p in pathlib.Path(d).rglob("*")
           if p.is_file() and p.suffix != ".sqlite3"
           and "{{" in p.read_text(encoding="utf-8", errors="ignore")]
    assert not bad, bad
print("OK 渲染后无 {{ 占位符残留")
EOF
```

### 7.1 B2b：按打包产物核对 37 个源文件（含隐藏名 `.gitignore.txt`）

> ⚠️ **B2 的 `pathlib.rglob('*.txt')` 会包含隐藏文件 → 隐藏源漏进 wheel 时 B2 仍会通过（假阳性）**。
> 故 MUST 再按**打包产物**核对一次（setuptools 的 `package_data` 用 `glob(recursive=True)`，会过滤**以 `.` 开头的文件名**）。

```bash
# B2b：wheel 内 MUST 含全部 37 个 .txt 源，且 MUST 含隐藏名 .gitignore.txt
# ⚠️ MUST 先清 build/ 与 *.egg-info —— setuptools 会把源文件复制进 build/lib/ 且不清除
#    隐藏文件，**残留的 build/ 会让旧配置的缺陷被掩盖**（假阴性）。
rm -rf build *.egg-info /tmp/f001p2-wheel
python3 -m pip wheel . --no-deps --no-build-isolation -w /tmp/f001p2-wheel >/dev/null
python3 - <<'EOF'
import glob, zipfile
w = glob.glob('/tmp/f001p2-wheel/*.whl')[0]
names = zipfile.ZipFile(w).namelist()
prefix = 'donkey/core/workspace/templates/'
srcs = [n for n in names if n.startswith(prefix) and n.endswith('.txt')]
assert len(srcs) == 37, f'期望 37 个 .txt 源，实际 {len(srcs)}：{sorted(srcs)}'
assert prefix + '.gitignore.txt' in names, '隐藏源 .gitignore.txt 未进 wheel —— 检查 pyproject.toml 的 package-data'
print('OK 37 个源文件全部在 wheel 内（含 .gitignore.txt）')
EOF
```

---

## 8. sqlite3 结构自检

```bash
WS=$(mktemp -d)/ws
donkey init "$WS" >/dev/null

python3 -c "
import sqlite3
c=sqlite3.connect('$WS/memory/sessions.sqlite3')
t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}
i={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='sessions_metadata'\")}
n=c.execute('SELECT COUNT(*) FROM sessions_metadata').fetchone()[0]
print('表',sorted(t)); print('索引',sorted(i)); print('记录数',n)
assert {'checkpoints','writes','sessions_metadata'} <= t
assert {'idx_sessions_metadata_title','idx_sessions_metadata_updated_at'} <= i
assert n == 0
print('OK sessions.sqlite3 结构完好')
for f in ('store','knowledge'):
    c2=sqlite3.connect(f'$WS/memory/{f}.sqlite3')
    k=c2.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\").fetchone()[0]
    print(f'{f}.sqlite3 表数',k); assert k==0
c.close()
"
```

**期望**：`sessions.sqlite3` 三表两索引齐备、记录数 0；两个占位文件表数各为 0。

> ⚠️ 索引断言 MUST 用 `in` / `<=` 判定，MUST NOT 用集合相等 —— `sqlite_autoindex_*` 是 PRIMARY KEY 自动索引，
> 其 `tbl_name` 亦为 `sessions_metadata`（[research.md](research.md) R-05）。

---

## 9. 常见失败排查

| 现象 | 最可能原因 | 处置 |
|---|---|---|
| `ImportError: cannot import name 'writes_sort_key'` | `langgraph-checkpoint` < 4.3.0 | §1 的处置列 |
| `TemplateGenerationError: 模板清单损坏` | `manifest.json` 不是合法 JSON | 校验清单文件（契约 §1） |
| `TemplateGenerationError: 模板源缺失: …/openai.toml.txt` | 26 份 stub 未抽取到位 | 跑 §7 的 B2 |
| `FileNotFoundError: …/providers/default.toml` | 渲染未先确保父目录（顺序依赖） | 检查 FR-012 的实现 |
| `TemplateGenerationError: 模板源缺失: …/.gitignore.txt`（仅在 **wheel / sdist 安装**后出现） | `package-data` 漏列隐藏名 —— setuptools 的 glob 会过滤 `.` 开头的文件名 | 在 `pyproject.toml` 的 `package-data` 显式列入 `".gitignore.txt"`（§7.1 B2b） |
| `templates=3 created=0` | 清单仍是 P1 的 3 条 | 追加 43 条（契约 §2） |
| `created` 计数偏小 | 把目录条目计入了 created | 检查 FR-017 的计数口径 |
| e2e 场景 14 断言失败但表都在 | 用了集合相等断言（含 `sqlite_autoindex_*`） | 改用 `in` 判定 |
| `--force` 后旧会话仍在 | 只删了主库、漏删 `-wal` / `-shm` | 检查 FR-011 的连带删除 |
| 覆盖率 < 80% | 新增分支未覆盖 | 补单测，**不要**下调阈值 |

---

## 10. 验收对照表（spec SC → 验证动作）

| SC | 验证动作 | 本文小节 |
|---|---|---|
| SC-001 | 14 个 e2e 场景全绿 | §5 |
| SC-002 | P1 的 7 个 e2e + 单测仍全绿 | §5 |
| SC-003 | 46 条落地物齐全 | §2 场景 1 + §7 B1 / B2 |
| SC-004 | 幂等：内容与 mtime 均不变 | §2 场景 2 |
| SC-005 | `--force` 恢复出厂 + 用户内容零改动 | §2 场景 3 + 附加 |
| SC-006 | sqlite3 三件套结构 | §8 |
| SC-007 | `--force` 后记录数 0 + 备份不受影响 | §8 + §2 场景 3 |
| SC-008 | ≥16 个单测全绿 | §5 |
| SC-009 | ruff + mypy 零 error 零 warning | §3 |
| SC-010 | 退出码集合 {0,1,2,3} | §2 各场景的 `exit=` + [contracts/exit-codes.md](contracts/exit-codes.md) |
| SC-011 | init 不做配置内容检查 | §2 场景 1（出厂态仍 exit 0） |
| SC-012 | 单次 < 10 秒 | §5（pytest 逐场景计时断言） |
| SC-013 | 覆盖率 ≥ 80% | §6 |
| SC-014 | 名称三处一致 | §2 场景 2 + §7 B12 |
| SC-015 | 26 份可解析 + 51 条模型 | §7 B5 / B6 / B7（源文件）+ e2e 场景 2（**渲染后 workspace 产物，26/26 逐份断言，MUST NOT 抽样**） |
| SC-016 | 无内置工具文件 | `find "$WS/tools" -name "*.py"` → 无结果 |
| SC-017 | 全仓无 LangSmith | §4 |
| SC-018 | `memory/README.md` 含备份指引 | `grep -c "cp memory/" "$WS/memory/README.md"` → ≥ 1 |
| SC-019 | 强制清空提示行 | §2 场景 3（`grep -c "清空"`） |
| SC-020 | 退出码 3 带下一步 | 单测类别（FR-055 第 11 项） |
| SC-021 | 运行期依赖恰为 1 个 | §1 的 `pip list` + `pyproject.toml` 核对 |

### 10.1 打包完整性（附加门禁）

| 项 | 验证动作 | 本文小节 |
|---|---|---|
| 安装包 MUST 含全部 37 个模板源（含 `.gitignore.txt` 隐藏名） | 构建 wheel 并解包比对 | §7.1（B2b） |
| 隐藏源漏列 → 安装后 `donkey init` exit 3（源模板缺失） | `pyproject.toml` 的 `package-data` MUST 显式列入 `".gitignore.txt"` | §7.1 / §9 |

---

## End of quickstart.
