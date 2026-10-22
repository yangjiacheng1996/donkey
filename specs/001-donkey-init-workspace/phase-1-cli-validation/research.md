# Phase 0 研究记录 —— F001-P1 `cli_validation`

**输入**：`specs/001-donkey-init-workspace/phase-1-cli-validation/spec.md`（含 2026-10-21 澄清会话的 **12 项**决策——截至 2026-10-22 已累积 12 条 Clarifications 记录）
**产出**：`plan.md` / `data-model.md` / `contracts/` / `quickstart.md`
**研究方式**：以本机可复现实验（Python 3.12.3 + POSIX）验证关键机制，不依赖外部资料；每条结论均附可复现的验证结果。

---

## R-01 · 参数用法错误的退出码改写（对应澄清决策 1）

**问题**：Python `argparse` 在"缺子命令 / 缺必填参数 / 未知参数"时默认 `sys.exit(2)`，而 `2` 在 F001 段位里已被 `PathPermissionError` 占用。

**验证**（`/tmp/opencode/argptest/t.py`）：子类化 `argparse.ArgumentParser` 并覆写 `error()`，把 `self.exit(2, ...)` 换成 `self.exit(1, ...)`：

| 场景 | 实测退出码 |
|---|---|
| `donkey`（缺子命令） | `1` |
| `donkey init`（缺必填位置参数） | `1` |
| `donkey init /tmp/x --name alice`（未知参数） | `1` |
| `python -m donkey init /tmp/x`（模块入口） | 退出码 `1`；但 usage 前缀为 `__main__.py`（与控制台脚本 `donkey` 不一致）→ 须显式设 `prog="donkey"` |

**关键发现**：`add_subparsers()` 的 `parser_class` 默认取 `type(self)`，实测子解析器类型为 `DonkeyParser` —— **覆写一次即覆盖顶层与所有子命令**，无需分别处理。

**决策**：定义 `DonkeyArgumentParser(argparse.ArgumentParser)`，覆写 `error()` → `self.exit(1, msg)`；用法提示与错误信息均写 `stderr`（`print_usage(sys.stderr)` + `self.exit(1, ...)` 的 message 参数默认写 stderr）。

解析器 MUST 显式设置 `prog="donkey"`——`argparse` 默认取 `sys.argv[0]` 的 basename，`python -m donkey` 下会得到 `__main__.py`，导致两条入口的 stderr usage 提示不一致，违反 spec FR-023「两种入口 MUST 产生完全相同的退出码与输出」。

**备选与否决理由**：
- 保留 argparse 默认 `2` → 否决：`2` 语义被稀释，与 N-08「段位语义严格」冲突（澄清决策 1 已定为 C）。
- 占用预留码 `10` → 否决：提前消耗 v1.x 预留位，违反"不预先造死错误类凑数"（立项书 §5.5.1）。
- 不设 `prog`（沿用 argparse 默认）→ 否决：两条入口的 usage 提示不一致，FR-023 不成立（实测见上表）。

---

## R-02 · 退出码从核心层到进程的传递链路

**问题**：`init_workspace` 以异常表达失败，退出码必须由 CLI 层产生；`donkey`（控制台脚本）与 `python -m donkey` 两条入口都要拿到同一个退出码。

**验证**（`/tmp/opencode/pkgtest/`，setuptools 68.1.2 + PEP 621 `pyproject.toml`）：

```
$ .venv/bin/mypkg          → console script exit = 7
$ .venv/bin/python -m mypkg → python -m exit  = 7
```

**结论**：
1. setuptools 生成的 console script 包装器为 `sys.exit(main())` → `main()` 返回的 `int` 原样成为进程退出码；
2. `donkey/__main__.py` 写 `sys.exit(main())` 即可得到同样行为；
3. 因此**入口点二选一即可满足验收脚本**，但为覆盖"未安装控制台脚本"的测试环境，`python -m donkey` 作为等价入口一并提供（spec FR-023 / FR-025）。

**决策**：`main(argv: list[str] | None = None) -> int` —— 返回退出码、由入口点 `sys.exit()` 落地；`main()` 内部**不**调用 `sys.exit`（保证可被测试直接断言返回值）。

---

## R-03 · 根路径的识别（对应澄清决策 6）

**问题**：`pathlib` 对根路径的末段名为空，而根路径的"父目录"是它自己且"存在"——现有的"父目录必须存在"校验对 `/` 完全放行。

**验证**（Python 3.12.3）：

| 输入 | `.name` | `.parent` | parent 存在？ |
|---|---|---|---|
| `/` | `''` | `/` | **是** |
| `//` | `''` | `//` | 是 |
| `/.` | `''` | `/` | 是 |
| `/tmp/` | `'tmp'` | `/` | 是 |
| `.`（相对） | 解析后 = 当前目录名 | — | — |

Windows 侧（`PureWindowsPath`）：`D:\` → `name=''`、`parent='D:\'`；`\\server\share` → `name=''`；`C:`（盘符相对）→ 解析后落在该盘当前目录，末段名非空。

**决策**：
- 判据取 **"解析后末段名为空 ⇒ 路径非法"**（spec FR-012），一次覆盖所有根形态，不逐个枚举；
- 名称抽取 MUST 用路径对象的末段名属性，**MUST NOT 手写字符串切分**——`"D:\\".split("\\")[-1]` 会得到 `'D:'`（把盘符当名字）；
- Windows 平台本 Phase 不在实现范围（spec Assumptions），但规则按平台无关表述编写，避免将来移植时行为漂移。

**备选与否决理由**：
- 根目录放行 + 名称回落固定值（`workspace`）→ 否决：会在文件系统根铺开 `instruction.md` / `providers/` / `tools/`，属破坏性操作；且根目录"父目录存在"的表象会让校验形同虚设。
- 根目录放行 + 名称取根标签 → 否决：同上，且名称形态不可控。

---

## R-04 · 权限判定的可执行口径

**问题**：`os.access` 的实际行为，尤其是"只读父目录"这一 CI 模拟方式是否可靠。

**验证**（`os.access(dir, mode)`，本机 uid=1000）：

| 目录权限 | `R_OK` | `W_OK` | `X_OK` | 合并判定 |
|---|---|---|---|---|
| `0o555`（r-x） | True | **False** | True | 拒绝 |
| `0o333`（-wx） | **False** | True | True | 拒绝 |
| `0o700` | True | True | True | 通过 |

**结论**：
- 目标不存在 → 校验**父目录**的 `W_OK | X_OK`（能否在其中创建子项）；目标已存在 → 校验**目标自身**的 `R_OK | W_OK | X_OK`（读、写入、进入目录各需一位）；
- `0o555` 目录**没有写位**，因此按 POSIX 语义即使以 root 运行 `os.access(dir, W_OK)` 同样为 False → **CI 用 `chmod 0o555` 模拟权限不足是可靠的，不依赖特权账号**；
- 0o333 用于验证"缺读权限"分支（同样不依赖特权账号）。

**决策**：权限判定用 `os.access(path, mode)`；错误信息 MUST 同时给出"缺失的权限种类"与"对应路径"（spec FR-015）。

---

## R-05 · 非法字符（NUL）的异常来源

**问题**：`Path('\0')` 的失败方式决定了"非法字符"分支的捕获范围。

**验证**：`Path('/tmp/\x00x').resolve()` → **`ValueError: embedded null byte`**（不是 `OSError`）。

**决策**：`check_path` MUST 捕获 `ValueError`（非法字符 / 内嵌 NUL）与 `OSError`（解析失败）并统一转成 `PathNotFoundError`（exit 1），确保不产生未捕获异常堆栈（spec FR-013 / FR-030）。

**补充（2026-10-22，三件套一致性检查）**：「路径过长」**不能**依赖 `resolve()` 抛错来覆盖——实测 `Path(超长).resolve(strict=False)` **正常返回、不抛异常**；真正的抛点是其后的 stat 类调用：Python 3.11+ 的 `Path.exists()` / `Path.is_dir()` / `Path.stat()` 在超长路径上**抛出** `OSError(ENAMETOOLONG)`（`_IGNORED_ERRNOS` 仅含 ENOENT / ENOTDIR / EBADF / ELOOP），不返回 False。故 `check_path` 内的全部 stat 类调用 MUST 置于统一的 `try/except OSError → PathNotFoundError` 内（tasks T024 / T025）。

---

## R-06 · 模板源文件命名规则与提示词的一处不一致（**需注意**）

**问题**：Phase 提示词 §3.2 同时给出两条互相冲突的命名信息：
- 清单条目 `path` = `mcp/mcp.json`，但占位源文件被写作 **`mcp.json.txt`**；
- 而同节给出的规则是 **`templates/{entry['path']}.txt`**（例：`templates/tools/filesystem.py.txt`）。

**分析**：P2 的 `render_templates` 按规则从条目 `path` 推导源文件路径（"清单里的每一条都必须已有对应的模板源 .txt"，否则抛 `TemplateGenerationError` exit 3）。若 P1 按 `mcp.json.txt` 建源文件，P2 将按规则去找 `templates/mcp/mcp.json.txt` → 源缺失 → exit 3。

**决策**：**以规则为准**（源文件路径由条目 `path` 派生），P1 建立 3 个源文件：
- `templates/instruction.md.txt`（条目 `instruction.md`）
- `templates/providers/default.toml.txt`（条目 `providers/default.toml`）
- `templates/mcp/mcp.json.txt`（条目 `mcp/mcp.json`）

**影响**：F001-P2 提示词 §4.7 / P2 spec 必须按同一规则定位源文件；本决策已记入本 plan 与 `data-model.md`，供 `/speckit.analyze` 交叉核对。（2026-10-21 更新）上游提示词 `harness/features/feature001_phase001_cli_validation.md` §3.2 已按本决策修正为 `mcp/mcp.json.txt`。

---

## R-07 · 打包与工程化配置选型

**问题**：本仓库尚无 `pyproject.toml`，需新建以提供 `donkey` 控制台入口；且需选定构建后端与静态检查配置。

**验证**：R-02 的原型工程用 PEP 621 `pyproject.toml` + setuptools 68.1.2 构建成功，控制台入口与模块入口行为一致。

**决策**：
- **构建后端 = setuptools**（`requires = ["setuptools>=68"]`）：无新增运行时依赖、生态最通用；`package-data` 用 `**` 递归通配（setuptools ≥62.3 支持）以覆盖 P2/P3 将加入的深层模板源；
- **运行时依赖 = 空**（`dependencies = []`）：宪法 §3.1 + Phase 提示词 §9 —— 本 Phase 仅用标准库；
- **打包方式 = 可编辑安装**（`pip install -e .`）：验收脚本既可走 `donkey`（PATH），也可回落 `python -m donkey`；
- **pytest 配置**：`testpaths = ["tests"]` + `pythonpath = ["."]`（pytest ≥7 内置选项），使未安装包时也能直接 `pytest`；
- **pytest 收集范围**：`python_files = ["test_*.py", "verify_phase_*.py"]` —— 黑盒验收脚本按宪法 §3.1 固定命名为 `verify_phase_<f>_<n>.py`，不匹配 pytest 默认 `python_files`，若不显式声明则 `pytest tests/` 不会收集它（实测确认），7 个 e2e 场景将失去 CI 证据。
- **ruff**：`line-length = 100`、`target-version = "py311"`、`select = ["E", "F", "I", "UP"]`（含 import 排序与 pyupgrade，`I`/`UP` 是零成本的高价值规则）；
- **mypy**：`strict = true`（`donkey/` 全量严格）；`tests/` 通过 `[[tool.mypy.overrides]] module = "tests.*"` 放宽 7 项严格项（`disallow_untyped_defs` / `disallow_any_generics` / `disallow_untyped_calls` / `disallow_untyped_decorators` / `warn_return_any` / `warn_unused_ignores` / `no_implicit_reexport`）。**该 override 的命中依赖 `explicit_package_bases = true` + `mypy_path = "."`**——mypy 的模块名解析规则：目录下无 `__init__.py` 时模块名取文件名本身（`tests/unit/test_init_workspace.py` → `test_init_workspace`），只有开启 `explicit_package_bases` 并给出基准目录后模块名才成为 `tests.unit.test_init_workspace`，`tests.*` 才真正命中（否则 `strict` 全量作用于测试层，20 个无标注测试函数报 `no-untyped-def`）。满足 spec SC-009「零 error 零 warning」。

**备选与否决理由**：
- hatchling：更简洁，但需新增构建依赖且与仓库既有环境无关联，收益不足；
- ruff 全规则集（含 `SIM` / `B`）：本 Phase 代码量小，收益有限且易在实现期产生噪声；
- mypy 非严格模式：无法兑现「零 warning」口径，也削弱 v1 库 API 契约的类型保证。

---

## R-08 · CI 工作流文件的归属

**问题**：仓库当前无 `.github/`，宪法 §4.1 要求 CI 跑 `pytest tests/` + `ruff check` + `mypy`。

**分析**：spec 已将 CI 工作流文件归为 **Deferred**（属仓库级资产，不在 Phase 提示词 §4 的实现要点内）；本 Phase 的完成证据以本地命令清单（单测 / 验收脚本 / 静态检查）为准。

**决策**：P1 **不**交付 `.github/workflows/ci.yml`；但 plan 预留该文件的最小内容骨架与触发条件说明（`tests/` + `ruff` + `mypy` 三步），在仓库级 CI 落地时可直接取用，避免二次设计。

**例外登记**：本例外已按宪法 §6.3 登记为 **E-01**（范围 / 理由 / 过期时间见 `.specify/memory/constitution.md` §6.3；本条 R-08 的结论不变）。

---

## 未解事项

无。spec 的 **12 项**澄清决策已全部落地为具体机制，Technical Context 中不存在 `NEEDS CLARIFICATION`。
