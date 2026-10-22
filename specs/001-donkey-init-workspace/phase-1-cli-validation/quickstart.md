# Quickstart —— F001-P1 `cli_validation` 验证指南

**目标**：在实现完成后，用一组可复制执行的命令证明 `donkey init` 满足 spec 的全部退出条件。
**前提**：`spec.md` 已冻结；`contracts/` 定义了行为契约；本文件只讲**怎么跑**、**期望看到什么**。

---

## 0. 环境准备

```bash
cd /home/ctyun/workspace/github/donkey

# 依赖（dev only；运行时零第三方依赖）
python3 -m venv .venv          # 仓库已存在 .venv 时本命令为幂等复用，不会清空已有环境
.venv/bin/pip install -U pip
.venv/bin/pip install -e ".[dev]"        # 可编辑安装 + pytest / pytest-cov / ruff / mypy

# 确认入口可用（两条入口都必须存在）
.venv/bin/donkey --help
.venv/bin/python -m donkey --help

# 确认两条入口的 usage 提示逐字相同（spec FR-023 / research.md R-01：prog 必须显式为 "donkey"）
.venv/bin/donkey init 2>&1 | head -1
.venv/bin/python -m donkey init 2>&1 | head -1
# 期望：上面两行输出完全相同（形如 "usage: donkey init [-h] [--force] path"）
```

> 验收脚本**不依赖**安装：找不到 PATH 上的 `donkey` 时自动回落 `python -m donkey`（spec FR-025）。但本地开发建议完成上面的可编辑安装。

## 1. 单元测试层（20 个用例全绿：core 层 17 + CLI 层 3）

```bash
.venv/bin/pytest tests/unit/ -v
```

**期望**：全部 PASS。覆盖类别 —— 绝对路径解析 / 父目录不存在 / 相对路径解析失败 / 根路径（末段名为空）/ 非法字符 / 只读父目录权限 / 正常权限 / 创建根目录且计数为 0 / 已存在目录不报错 / 含空格或 Unicode 等特殊字符的末段名一律接受且名称原样保留 / 目标为普通文件 / 父目录为文件 / 空路径 → 均按路径类错误处理（退出码 1）。CLI 层 3 个用例：缺子命令 / 缺必填参数 / 未登记异常子类兜底 → 均退出码 `1`（`test_main_missing_path_argument_exits_1` 内另含 FR-024「未知参数 → 退出码 1」断言组）。

## 2. e2e/phase 验收层（7 个场景全绿）

```bash
.venv/bin/pytest tests/e2e/phase/verify_phase_f001_p1.py -v
```

**期望**：7 个 `test_scenario_*` 全部 PASS。

| 场景 | 断言要点 |
|---|---|
| 1 全新创建 | 退出码 `0` + 目录已创建；**双入口对比**：两者退出码相同 + stdout 摘要逐字相同 + stderr usage 提示逐字相同（FR-023） |
| 2 路径类失败 | 父目录不存在 → 退出码 `1`；根目录 → 退出码 `1`；stderr 含错误标识 |
| 3 权限类失败 | 只读父目录 → 退出码 `2`；stderr 含权限标识 |
| 4 幂等 | 已存在 workspace 无 `--force` → 退出码 `0`，内容不变 |
| 5 强制标志 | 已存在 workspace + `--force` → 退出码 `0`，P1 不重置 |
| 6 范围边界 | 目录已建但**不要求**含任何模板文件 |
| 7 名称派生 | 名称 = 路径末段；摘要回显绝对路径与名称；误传 `--name` → 退出码 `1` |

## 3. 静态检查（零 error / 零 warning）

```bash
.venv/bin/ruff check donkey/ tests/
.venv/bin/mypy donkey/ tests/
```

**期望**：ruff `All checks passed!`；mypy `Success: no issues found in N source files`。

## 4. 手动冒烟（对照 contracts/cli-contract.md §6）

```bash
# 统一用 .venv/bin/donkey（已 source .venv/bin/activate 时可直接写 donkey）

# 成功（退出码 0）
.venv/bin/donkey init /tmp/test-ws; echo "exit=$?"

# 路径类失败（退出码 1）
.venv/bin/donkey init /nonexistent/parent/ws; echo "exit=$?"

# 权限类失败（退出码 2）
mkdir -p /tmp/ro && chmod 555 /tmp/ro
.venv/bin/donkey init /tmp/ro/ws; echo "exit=$?"
chmod 755 /tmp/ro

# 根目录被拒（退出码 1，不是 0）
.venv/bin/donkey init /; echo "exit=$?"

# 幂等（退出码 0，内容不变）
.venv/bin/donkey init /tmp/test-ws; echo "exit=$?"

# 用法错误（退出码 1，不是 argparse 默认的 2）
.venv/bin/donkey init; echo "exit=$?"
```

**期望输出形态**

```text
[donkey init] workspace=/tmp/test-ws name=test-ws force=false templates=0 created=0 skipped=0
```

## 5. 分层边界自检（宪法 N-03 / N-04 / N-05）

```bash
# 核心层不得出现命令行解析 / 进程参数
grep -rnE "import (argparse|click|typer)|sys\.argv" donkey/core/ && echo "VIOLATION"

# 客户端层不得直接依赖智能体框架 / 图运行时 / 数据库驱动
grep -rnE "^\s*(import|from) (langchain|langgraph|sqlite3)" donkey/cli/ && echo "VIOLATION"

# 永不使用清单：任何形态的 LangSmith
grep -rnE "langsmith" donkey/ && echo "VIOLATION"
```

**期望**：三条命令均无输出（无 `VIOLATION`）。

## 6. Phase 完成判据（全部满足才算完成）

```bash
.venv/bin/pytest tests/unit/ -v                                     # 20 用例全绿（core 17 + CLI 3）
.venv/bin/pytest tests/ -v                                          # unit + e2e 三层一次收齐（plan G13 / research.md R-07）
.venv/bin/pytest tests/e2e/phase/verify_phase_f001_p1.py -v          # 7 场景全绿
.venv/bin/pytest tests/unit/ --cov=donkey.core --cov-fail-under=80  # donkey.core 行覆盖率 ≥ 80%（SC-016）
.venv/bin/ruff check donkey/ tests/                                  # 零 error
.venv/bin/mypy donkey/ tests/                                        # 零 error
```

对照 spec 退出条件：

- [x] SC-001 ~ SC-016 全部达成（可量化判据见 `spec.md`「Success Criteria」）
- [x] 退出码实测通过：`0` / `1` / `2`，集合恰为 `{0,1,2}`
- [x] 双入口一致：`donkey` 与 `python -m donkey` 的退出码、stdout 摘要、stderr usage 提示逐字相同（spec FR-023 / research.md R-01）
- [x] 幂等：不破坏已存在内容（`--force` 在 P1 亦不重置）
- [x] 分层边界与永不使用清单自检无违例
- [x] 后续 Phase（F001-P2）的入口条件未被破坏：模板清单 3 条 + 3 个同名 `.txt` 源就位
- [x] `donkey.core` 单元测试行覆盖率 ≥ 80%（spec SC-016）
- [x] pytest 全量收集：`pytest tests/` 一次收齐 unit + e2e 三层（7 个 e2e 场景被真正收集，plan G13）

## 7. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `donkey: command not found` | 未做可编辑安装 | 走 `python -m donkey`，或执行 §0 的 `pip install -e ".[dev]"` |
| 权限场景在 root 下"没报错" | 权限位判定基于实际权限位 | 用 `chmod 0o555`（无写位）模拟，root 下同样被拒 |
| `mypy` 报 `unused-ignore` / `no-untyped-def` | 严格模式配置 | `tests/` 已在 `pyproject.toml` 的 `[[tool.mypy.overrides]] module = "tests.*"` 放宽 7 项严格项（该 override 依赖 `explicit_package_bases = true` + `mypy_path = "."` 才命中，缺任一项则模块名不落在 `tests.*` 下）；源码需完整标注 |
| 模板源缺失导致 P2 exit 3 | 源文件路径 MUST 由条目 `path` 派生 | 见 `data-model.md` §5 与 `research.md` R-06 |
