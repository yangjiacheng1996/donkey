# Quickstart 验证指南（F001-P3 `builtin_tools`）

**用途**：本文件是**可执行的验证 / 运行指南** —— 逐条给出"怎么跑、期望看到什么"。**不含**完整实现代码、完整测试套件与迁移步骤（那些属 `tasks.md` 与实现阶段）。

**前置**：F001-P1 / F001-P2 已完成且其套件全绿；工作目录 = 仓库根。

---

## 0. 环境准备

```bash
cd <仓库根>
python -m venv .venv && . .venv/bin/activate     # 若尚未创建
pip install -e ".[dev]"                          # 含本 Phase 新增的 pytest-httpx
```

**期望**：`pip` 输出中 `pytest-httpx` 被装入；`python -c "import donkey; print(donkey.__file__)"` 指向本仓库。

---

## 1. 门禁冒烟（装依赖后**必跑**，P2 的 R-02 口径）

```bash
# ① donkey 自有代码路径 MUST NOT import 可观测性后端（N-12 / D-17）
python - <<'PY'
import subprocess, sys
code = "import sys, donkey.core.api, donkey.cli.cli_client; print('langsmith' in sys.modules)"
print("langsmith in donkey 导入链:", subprocess.run([sys.executable,"-c",code],capture_output=True,text=True).stdout.strip())
PY
# 期望输出：langsmith in donkey 导入链: False
```

> **口径**：该检查 MUST 限定为 **donkey 自有代码路径**（`donkey.core` / `donkey.cli`）的导入链 —— MUST NOT 拿"用户导入渲染产物"的语境去复核它（spec FR-078）。

---

## 2. 一次 `donkey init` 的完整冒烟

```bash
rm -rf /tmp/p3ws && donkey init /tmp/p3ws
echo "--- 工具目录 ---"; ls -1 /tmp/p3ws/tools
# 期望：README.md  __init__.py  changes.py  commandline.py  filesystem.py  webfetch.py
echo "--- 清单计数 ---"; donkey init /tmp/p3ws | tail -1
# 期望：templates=54 created=48 skipped=0   ← 二次 init 则是 templates=54 created=0 skipped=48
```

**要点**：首次 init 的计数是 `54 / 48 / 0`；**二次** init 是 `54 / 0 / 48`（幂等，MUST NOT 改动已存在文件）。

---

## 3. 逐个工具的手动验证

> 以下命令在**工作区目录内**执行（相对路径以工作区根为基准 —— spec FR-022 / FR-032）。

### 3.1 文件工具

```bash
cd /tmp/p3ws
python - <<'PY'
import json
from tools.filesystem import read_file, write_file, copy_file, move_file, delete_file, list_dir, stat

r = json.loads(write_file.invoke({"path": "demo.txt", "content": "hello\n"}))
print("write:", r["action"], r["applied"], r["change"]["version"], r["change"]["new_hash"][:16])
print("read :", read_file.invoke({"path": "demo.txt"}).splitlines()[:2])
print("list :", list_dir.invoke({"path": "."}))
print("stat :", stat.invoke({"path": "demo.txt", "with_hash": True})["is_file"])
PY
```
**期望**：`write` 的 `action` = `create`、`applied` = `true`、`change.version` = `1`；`read` 的首行是 `Read file demo.txt, lines 1-1`，次行是 `1: hello`。

### 3.2 变更记录的四条硬规则

```bash
cd /tmp/p3ws
python - <<'PY'
import json
from tools.filesystem import write_file

r1 = json.loads(write_file.invoke({"path": "demo.txt", "content": "a\nb\n"}))
prev = r1["change"]["previous_hash"]     # spec FR-004：不存在时为 null（Python 侧 None，MUST NOT 用空串）
print("基线字段数:", len(r1["change"]), "| previous_hash:", prev[:14] if prev else prev)
print("差异:", [l for l in r1["change"]["unified_diff"].splitlines() if l.startswith(("+","-"))])

r2 = json.loads(write_file.invoke({"path": "demo.txt", "content": "a\nc\n", "dry_run": True}))
print("预览 applied:", r2["applied"], "| 磁盘未变:", open("demo.txt").read() == "a\nb\n")
PY
```
**期望**：基线 12 字段；`previous_hash` 为 `None`（首次写入）或 `sha256:<hex>` 串（覆盖写入）—— **MUST NOT 是空串**；预览模式 `applied=false` 且磁盘内容不变；差异文本含 `-b` 与 `+c`。

### 3.3 乐观锁（期望指纹不匹配 → 拒绝）

```bash
cd /tmp/p3ws
python - <<'PY'
import json
from tools.filesystem import write_file
from tools.changes import FileChangedError
try:
    write_file.invoke({"path": "demo.txt", "content": "x\n", "expected_hash": "sha256:deadbeef"})
except FileChangedError as e:
    print("已拒绝:", str(e)[:60])
PY
```
**期望**：打印"已拒绝"，且 `demo.txt` 内容**未变**。

### 3.4 读取侧的双上限与续读指针

```bash
cd /tmp/p3ws
python - <<'PY'
from tools.filesystem import write_file, read_file
write_file.invoke({"path": "big.txt", "content": "".join(f"line {i}\n" for i in range(3000))})
out = read_file.invoke({"path": "big.txt"})
lines = out.splitlines()
print("首行:", lines[0])
print("末行:", lines[-1])
PY
```
**期望**：首行形如 `Read file big.txt, lines 1-2000`；末行是 `[Output truncated. Continue reading with offset: 2001]`。

### 3.5 命令工具

```bash
cd /tmp/p3ws
python - <<'PY'
import json
from tools.commandline import run_shell
r = json.loads(run_shell.invoke({"command": "echo hello"}))
print("stdout:", repr(r["stdout"]), "| returncode:", r["returncode"], "| truncated:", r["truncated"])
t = json.loads(run_shell.invoke({"command": "sleep 5", "timeout": 1}))
print("超时:", t["timed_out"], "| returncode:", t["returncode"])
PY
```
**期望**：`stdout` 含 `hello`；超时时 `timed_out=True`、`returncode=-1`（**不抛异常** —— spec FR-031）。

### 3.6 网络工具（**四道边界** + **不限制地址范围**）

> **判据来源**：spec SC-021 的**两类可判定判据** ——（a）**行为层**：四道边界各自 MUST 报错、**地址范围 MUST NOT 被限制**；（b）**静态层**：渲染产物的**说明文字** MUST **逐条出现**四项边界的措辞。

#### (a) 行为层 · 四道边界各自报错

```bash
cd /tmp/p3ws
python - <<'PY'
from tools.webfetch import fetch_url

# ① 协议白名单（仅 http/https）
for url in ("ftp://example.com/x", "file:///etc/passwd"):
    try:
        fetch_url.invoke({"url": url}); print("!! 未拒绝", url)
    except Exception as e:
        print("协议白名单 已拒绝:", type(e).__name__)

# ② 超时上限（120 秒）
try:
    fetch_url.invoke({"url": "https://example.com", "timeout": 999}); print("!! 未拒绝 超时上限")
except Exception as e:
    print("超时上限 已拒绝:", type(e).__name__)
PY
```
**期望**：三项全部被拒绝（协议白名单 ×2、超时上限 ×1）。

> **响应体上限（5 MiB）/ 非文本 MIME 拒绝 / 非 2xx 报错** 三项 MUST 在单元层用 HTTP 拦截库构造对应响应实测（见 `tests/unit/test_builtin_tools.py` 的 SC-021 行为层用例）—— 本节只演示可直接手验的两项。

#### (a′) 地址范围 MUST NOT 被限制

```bash
cd /tmp/p3ws
python - <<'PY'
from tools.webfetch import fetch_url
try:
    fetch_url.invoke({"url": "http://127.0.0.1:9/ping"})
    print("回环地址 被放行（无地址黑名单 / 白名单 / 代理 / 沙箱）")
except Exception as e:
    print("!! 回环地址被拦 —— 违反 SC-021(a)：", type(e).__name__)
PY
```
**期望**：打印"回环地址 被放行"（**不得**出现"被拦"）—— SC-021(a) 明确要求"**地址范围**限制 MUST NOT 被实现"，回环 / 私有网段 / 云主机元数据地址一律放行。

#### (b) 静态层 · 说明文字逐条出现四项措辞

```bash
for w in "http" "https" "5 MiB" "MIME" "2xx"; do
  printf "%-8s %s\n" "$w" "$(grep -oF "$w" /tmp/p3ws/tools/webfetch.py | wc -l)"
done
```
**期望**：五个计数均 **≥ 1**（SC-021(b) / FR-090）—— "http" 与 "https"（协议白名单）/ "5 MiB"（响应体上限）/ "MIME"（非文本拒绝）/ "2xx"（非 2xx 报错）逐条出现。

**附：客户端 MUST 以 `trust_env=False` 构造**（R-03 / R-19）—— httpx 默认的 `trust_env=True` 会隐式读取 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `.netrc`，违反 spec FR-104（工具 MUST 不读取任何环境变量）。自检：

```bash
grep -n "trust_env" /tmp/p3ws/tools/webfetch.py   # 期望含 trust_env=False
```

---

## 4. 三层测试的跑法

```bash
# 前置套件（必须全绿 —— 前两 Phase 的退出条件未被破坏）
pytest tests/e2e/phase/verify_phase_f001_p1.py -v
pytest tests/e2e/phase/verify_phase_f001_p2.py -v
pytest tests/unit/test_init_workspace.py -v
pytest tests/unit/test_template_skeleton.py -v

# 本 Phase 套件
pytest tests/unit/test_builtin_tools.py -v          # ≥15 个用例
pytest tests/integration/test_init_to_load.py -v    # ≥4 个用例
pytest tests/e2e/phase/verify_phase_f001_p3.py -v   # 16 个断言
```

**期望**：全部 PASS，零失败。

---

## 5. 静态检查与覆盖率

```bash
ruff check donkey/ tests/
mypy donkey/ tests/

# 覆盖率 MUST 用独立命令（MUST NOT 写进 pytest 全局 addopts）
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80
```
**期望**：ruff / mypy 零 error；覆盖率 ≥ 80%。

> **口径提示**：模板正文是 `.txt` → **不在** `donkey.core` 的覆盖率口径内；其质量由单元测试的 `compile()` 自检 + ≥15 个用例兜底（R-08）。

---

## 6. 全量与 CI 交付自检

```bash
pytest tests/ -v

test -f .github/workflows/ci.yml && echo "OK ci.yml 已交付" || echo "FAIL E-01 已到期，ci.yml 缺失"
grep -cE "pytest tests/|--cov=donkey.core|--cov-fail-under=80|ruff check|mypy" .github/workflows/ci.yml
```
**期望**：文件存在；**四类**关键命令全部命中（`pytest tests/` / `--cov=donkey.core` / `--cov-fail-under=80` / `ruff check` / `mypy` 五个模式落在 **4 行** `- run:` 上 → `grep -cE` 计数 **≥ 4**；若把覆盖率命令拆成两行 `- run:`，则为 5 行、计数 ≥ 5 —— **MUST NOT** 以"计数 ≥ 5"作为通过条件）；`pytest tests/` 全绿。

---

## 7. 幂等与 `--force` 的手工验证

```bash
rm -rf /tmp/p3ws2 && donkey init /tmp/p3ws2
echo "# 我的工具" > /tmp/p3ws2/tools/my_tool.py          # 清单外
echo "# 改过的契约库" >> /tmp/p3ws2/tools/changes.py    # 已存在的契约库

donkey init /tmp/p3ws2 --force
echo "--- 契约库（必须保留用户改动）---"; tail -1 /tmp/p3ws2/tools/changes.py
echo "--- 用户自写工具（必须仍在）---"; cat /tmp/p3ws2/tools/my_tool.py
echo "--- 计数（契约库被豁免 → skipped=1）---"
```
**期望**：契约库保留用户的追加行；`my_tool.py` 仍在；`--force` 的计数为 `created=47 skipped=1`。

> **这一条是本 Phase 最容易回归的行为** —— 它由 R-07 的编排层豁免实现，且 MUST NOT 削弱 P2 通则对其余条目的作用。

---

## 8. 跨工作区的模块缓存陷阱（验收假绿的来源）

**现象**：在**同一个进程**里先后导入两个不同工作区的 `tools.filesystem` → 第二次拿到的是**第一个**工作区的模块（`sys.modules` 按名缓存）。

**规避**（三层各自的既定做法）：

| 层 | 做法 |
|---|---|
| 单元 | 渲染到 tmp → 工作区根入 `sys.path` → `importlib.import_module("tools.X")` → **teardown 清 `sys.modules`**（R-02） |
| 集成 | **独立子进程**（FR-062） |
| e2e | **独立子进程**，且 MUST 用 `python -c`（`-c` 才把 cwd 放进 `sys.path`；用脚本文件会因 `sys.path[0]` 是脚本目录而找不到 `tools` 包 —— R-20） |

---

## 9. 排查指引

| 症状 | 首查 |
|---|---|
| `donkey init` 报"模板源缺失"（exit 3） | 安装包内缺 `templates/tools/*.txt` 或 `templates/skills/example/**` 的 8 个源 → R-09 的打包核对（B3） |
| `donkey init` 报 exit 4 | 内置工具 / Skills 三层写入失败 → 目标目录写权限 / 磁盘空间 |
| 工作区里 `import tools.filesystem` 失败 | `tools/` 是否在工作区根下；是否用了 `python -c`（§8） |
| 网络工具导入失败 | 用户工作区未装 HTTP 客户端库 —— `tools/README.md` 已写明（FR-044(h)） |
| 网络工具把**回环地址 / 私有网段**也拦了 | **违反 SC-021(a)** —— "地址范围"限制 MUST NOT 被实现（无地址黑名单 / 白名单 / 代理 / 沙箱）；查 `tools/webfetch.py` 是否实现了地址过滤（§3.6 a′） |
| 变更记录里 `previous_hash` 打印报 `TypeError` | 契约库按 spec FR-004 返回 `null`（Python 侧 `None`），**MUST NOT 用空串** → 取值前 MUST 先判空（§3.2） |
| 读大文件只拿到部分内容 | **预期行为** —— 双上限生效，末尾有续读指针（§3.4） |
| `--force` 后契约库被覆盖了 | 豁免分支未生效 —— 查 `init_workspace_inner` 步骤 ④（R-07） |
| CI 覆盖率莫名为 0 | 覆盖率被写进了 pytest 的 `addopts` —— MUST 用独立命令（§5） |
| 门禁把 Skill 第三层演示脚本判成"智能体入口"违例 | 口径按 **宪法 §6.3 例外 E-02 + §5 章 [D-19]**（N-01 的边界澄清："Python 入口文件"指**智能体入口**）—— 该脚本**获宪法授权**，MUST NOT 被判为违例（spec FR-050） |
