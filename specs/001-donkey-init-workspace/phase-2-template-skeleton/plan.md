# Implementation Plan: F001-P2 `template_skeleton` —— `donkey init` workspace 模板骨架幂等生成

**Branch**: `main`（spec 目录名 `001-donkey-init-workspace/phase-2-template-skeleton` 与 git 分支相互独立，见 spec.md 头部说明） | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-donkey-init-workspace/phase-2-template-skeleton/spec.md`（含澄清会话共 **27 项**决策——13 项 AI 推断 + 5 项 Maintainer 亲自裁决 + 6 项定向澄清修订裁决 + **3 项三文档交叉复核后定点修订**（澄清 #25 ~ #27））

---

## Summary

**目标**：交付 `donkey init` 的**模板骨架幂等生成**（F001-P2 子段 2，退出码 `3`）——在 workspace 内落地 46 个模板条目（37 个文本模板 + 6 个目录 + 3 个 sqlite3 模板）+ 1 份工作区清单，并维护 `donkey init` 的四场景幂等契约（全新创建 / 幂等补齐 / 模板重置 / 放弃重做）。

**技术路线**：四层落地 —— `donkey/core/workspace/sqlite3_templates.py`（三个 sqlite3 结构构造器，程序化建库，不携带二进制模板）→ `donkey/core/workspace/manifest.py`（工作区清单读写，独立模块供 F002 / F003 复用）→ `donkey/core/workspace/init.py`（追加 `load_template_manifest` / `render_templates` / `init_workspace_inner`）→ `donkey/core/api.py`（门面函数体补齐）+ `donkey/cli/cli_client.py`（映射表 1 行 + 摘要 1 行提示）。

**关键决策**（R-01 ~ R-15 详见 [research.md](research.md)；**R-16 ~ R-18 为 `/speckit.analyze` 三文档交叉复核后的定点修订**，源自 spec 澄清 #26 / #27 与 FR-055 第 10 类的构造方式裁定 —— **已回填至 research.md 的「R-16 ~ R-18」节，两侧内容逐字一致**）：

| # | 决策 | 落点 |
|---|---|---|
| R-01 | 上游 saver 包 = `langgraph-checkpoint-sqlite`，导入路径 `langgraph.checkpoint.sqlite`（**非** `langgraph_checkpoint_sqlite`）；`setup()` 是**实例**方法 → `SqliteSaver(conn).setup()`；版本 `>=3.1,<4` | `core/workspace/sqlite3_templates.py` / `pyproject.toml` |
| R-02 | **N-12 门禁通过**：实测导入上游 saver 新增 471 个模块、langsmith 相关 **0** 个 → langsmith 仅作为 langchain-core 的传递依赖被**安装**，donkey **永不 import** | `pyproject.toml` / quickstart §4 grep 自检 |
| R-03 | 上游 `setup()` 首句即 `PRAGMA journal_mode=WAL` → 运行期产生 `-wal` / `-shm`；**正常关闭连接时 SQLite 自动清理**；陈旧 WAL 因盐值不匹配被**安全忽略** → 连带删除是**防御性**措施，注释 MUST NOT 声称"不删必然污染" | `core/workspace/init.py`（`--force` 分支） |
| R-04 | 上游 `setup()` 用 `CREATE TABLE IF NOT EXISTS` + 一条被容错的 `ALTER TABLE` 迁移 → 幂等安全；每次新建 saver 实例 MUST 调一次 | `core/workspace/sqlite3_templates.py` |
| R-05 | `sessions_metadata` 落地后 `sqlite_master` 含 `sqlite_autoindex_*`（PRIMARY KEY 自动索引）→ e2e 断言 MUST 用 `in` 判定，MUST NOT 用集合相等 | e2e 场景 14 |
| R-06 | 清单条目顺序 ≠ 依赖顺序（`providers/default.toml` 排在 `providers` 目录条目之前）→ 写文件前 MUST 确保父目录存在 | `core/workspace/init.py` |
| R-07 | MUST **覆盖** F001-P1 的 3 个占位源文件（`instruction.md.txt` / `providers/default.toml.txt` / `mcp/mcp.json.txt`）；`{{workspace_path}}` 占位符随之消失 | `core/workspace/templates/` |
| R-08 | 计数口径：`templates_loaded` = 模板清单的**原始条目总数**（46；含目录条目、含重复条目）；`files_created` / `files_skipped` = **文件型条目**数（40 = 37 文本 + 3 sqlite3；目录条目不计入），按**唯一路径**计一次 → 全新创建 = `40/0/46`，二次 init = `0/40/46` | `core/workspace/init.py` / `core/api.py` |
| R-09 | 26 份 provider stub 按调研 §8.3.3 ~ §8.3.28 **脚本抽取**（模型条目合计 **51** 条，与 SC-015 硬指标一致）MUST NOT 手工誊写 | `core/workspace/templates/providers/` |
| R-10 | 流程入口用 `write_workspace_manifest`，`ensure_workspace_manifest` 作为**严格等价**的便捷封装保留（委托同一判定顺序）：**force → 直接覆盖（不读旧文件）**；不带 force 且已存在 → 先读（解析失败 → exit 3）/ 不覆盖、返回既有内容；不存在 → 无条件创建 | `core/workspace/manifest.py` |
| R-11 | 强制清空提示行输出到 **stdout**、与摘要**分行**、带 `--force` 时**恒定输出**、不带时**不出现** | `cli/cli_client.py` |
| R-12 | 退出码 3 的错误信息沿用 F001-P1 的 `_NEXT_STEP` 模式，为模板类失败定义第二句固定文案；**文案常量 `_NEXT_STEP_TEMPLATE` 落 `donkey/core/exceptions.py`**（与错误类同源，MUST NOT 落 `init.py` —— 否则 `manifest.py` → `init.py` → `manifest.py` 循环 import） | `core/exceptions.py` / `core/workspace/{init,manifest,sqlite3_templates}.py` |
| R-13 | 覆盖率 MUST 以独立命令度量，MUST NOT 写入 pytest 全局 `addopts` | `pyproject.toml` / quickstart §6 |
| R-14 | 【范围外观察】上游包已自带 `langgraph/store/sqlite/` → 宪法 D-11 的"v3 自研 SqliteStore"路线待 Maintainer 评估；本 Phase MUST NOT 引用 | 登记项，不落代码 |
| R-15 | 清单条目路径重复 → **路径去重、后者定义胜出**，且**去重只发生在渲染层**：`load_template_manifest` 返回**未去重的原始条目列表**（长度 = `templates_loaded`，含重复条目 —— FR-001 的 `list[dict]` 内无位置携带原始总数，故 loader MUST NOT 去重）；`render_templates` MUST 在内部先按唯一路径去重（同一路径只处理一次，以重复项中**最后出现**的条目为准，其 `format` 与源模板生效），MUST NOT 对同一路径既计 `created` 又计 `skipped`；`files_created` / `files_skipped` 按唯一路径计一次（spec FR-002 / FR-026 / 澄清 #24） | `core/workspace/init.py`（`render_templates` 内去重）/ `contracts/library-api.md` §3.1·§3.2 |
| R-16 | **步骤 ⑤ 失败不回滚**（spec 澄清 #26）—— 初始化流程步骤 ⑤（写工作区清单）失败 MUST 抛模板生成类错误（退出码 `3`），而步骤 ④ 已落地 / 已重写的模板文件 MUST **保留**（不删除、不还原）；本 Phase **MUST NOT** 实现任何事务回滚机制（无补偿逻辑、无临时目录 + 原子替换、无"失败即清空"） | `core/workspace/init.py`（`init_workspace_inner` 步骤 ⑤）/ `tests/unit/test_template_skeleton.py` |
| R-17 | **工作区被重命名后保留旧名**（spec 澄清 #27）—— 用户把 workspace 目录重命名后再执行**非强制** `donkey init`：非强制模式下已存在文件 MUST 完全不动（FR-008 / FR-020），故工作区清单的 `name` 字段与模板正文**保留重命名前的名称**；命令行报告的名称（路径末段名）与模板正文内的名称**不一致** —— 该不一致 MUST NOT 触发退出码 `3`，亦 MUST NOT 以任何形式宣称二者一致。本 Phase 以**文档化口径**满足（spec Edge Cases「其它边界」已登记 + SC-014 适用边界已明确），**MUST NOT** 新增任何命令行输出（客户端改动仍限 FR-064 的三项） | `core/workspace/manifest.py`（"非强制 → 保留原 `name`"语义，无新增行为）/ `core/workspace/init.py` |
| R-18 | **权限失败 MUST 以注入式构造产生** —— 特权账号（root / `CAP_DAC_OVERRIDE`）**绕过 DAC 权限检查**，其对 `0o555` 目录的 `access(W_OK)` 与实际写入**均成功** → chmod 只读目录的方案在 root CI 容器中**失效**，FR-055 第 10 类（渲染中途权限失败）会假失败。故该用例 MUST 用 `monkeypatch` / mock 在写入边界注入 `OSError(EACCES)`，MUST NOT 依赖运行账号的特权状态（spec Assumptions「特权环境说明」已同步修订） | `tests/unit/test_template_skeleton.py`（`test_render_permission_denied_midway`） |

## Technical Context

**Language/Version**: Python 3.11+（本机实测 3.12.3；依赖 `tomllib` 内置）

**Primary Dependencies**: **1 个直接运行期依赖** = `langgraph-checkpoint-sqlite>=3.1,<4`（实测 3.1.2；传递依赖 `langgraph-checkpoint>=4.3.0,<5.0.0` / `langchain-core>=0.2.38` / `aiosqlite>=0.20` / `sqlite-vec>=0.1.6`）；
其余全部标准库（`pathlib` / `json` / `sqlite3` / `datetime` / `os` / `shutil` / `tomllib`）；dev 依赖 `pytest` / `pytest-cov` / `ruff` / `mypy`（**无新增**）

**Storage**: 文件系统（workspace 根目录）+ sqlite3 文件（`memory/*.sqlite3`，程序化建库，不随包分发二进制）

**Testing**: pytest —— `tests/unit/test_template_skeleton.py`（≥16 个用例）+ `tests/unit/test_cli_client.py`（P1 既有 3 个用例 + 本 Phase 新增的"强制清空提示行"结果摘要断言）+ `tests/e2e/phase/verify_phase_f001_p2.py`（14 个黑盒场景）

**Target Platform**: Linux / macOS（POSIX 权限语义；Windows 不在本 Phase 实现范围，但路径与文件操作按平台无关表述编写）

**Project Type**: single-package library + CLI（`donkey.core` 库 API + `donkey.cli` argparse 客户端；web / gui 维持空占位）

**Performance Goals**: 单次 `donkey init` 在 10 秒内返回（spec SC-012；纯本地文件系统操作，无网络依赖）

**Constraints**: 宪法 N-01（workspace 内禁 Python 入口文件）/ N-03（core 不依赖客户端）/ N-04（cli 不直接 import langchain·langgraph·sqlite3）/ N-05（core 不依赖 argparse·sys.argv）/ N-08（退出码段位不重叠）/ N-12（禁 LangSmith 任何形态，R-02 已实证）；CLI 框架限标准库 `argparse`；核心层 MUST 无副作用（校验能力）；MUST NOT 携带二进制 sqlite3 模板

**Scale/Scope**: 1 个子命令 / 1 个新错误类 / 69 条 FR / 21 条 SC / 46 条清单条目（`templates_loaded` = **原始条目总数**，含目录条目、含重复条目）/ 37 个模板源文件 / 6 个目录条目 / 3 个 sqlite3 模板（**文件型条目 40 = 37 文本 + 3 sqlite3**；`files_created` / `files_skipped` 按**唯一路径**计一次，目录条目不计入）/ 14 个 e2e 黑盒场景 / ≥16 个单元测试用例 / 3 个新增或改造模块（`workspace/manifest.py` 新增 · `workspace/sqlite3_templates.py` 新增 · `workspace/init.py` 追加）+ 4 个改造模块（`core/api.py` · `cli/cli_client.py` · `core/exceptions.py` · `core/exit_codes.py`）+ 1 个改造文件（`pyproject.toml`）**；另有测试层 —— 2 个新增文件（`tests/unit/test_template_skeleton.py` · `tests/e2e/phase/verify_phase_f001_p2.py`）+ 1 个改造文件（`tests/unit/test_cli_client.py`）**。客户端改动 = **3 项**（异常映射表 1 行 + 摘要强制清空提示 1 行 + `--help` / 子命令说明文案同步 1 处 —— FR-064 ③；P1 遗留文案在 P2 后是错误陈述）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 门 | 宪法条款 | 判定 | 依据 / 落地方式 |
|---|---|---|---|
| G1 | §3.1 Python 3.11+；§3.1 CLI 用 stdlib `argparse`（禁 typer / click） | ✅ PASS | CLI 框架不变；新增代码只用 `pathlib` / `json` / `sqlite3` / `datetime` / `os` / `shutil` |
| G2 | N-03 核心层不 import 客户端；N-04 cli 不直接 import langchain / langgraph / sqlite3；N-05 核心层不 import argparse / sys.argv | ✅ PASS | 上游 saver 的 import **只出现在** `core/workspace/sqlite3_templates.py`（core 层，N-04 允许）；`cli/cli_client.py` 仅新增 1 行映射 + 1 行打印，**不** import sqlite3 / langgraph（quickstart §4 有 grep 自检） |
| G3 | N-08 退出码段位严格不重叠（§4.4） | ✅ PASS | 本 Phase 使用 `0/1/2/3`，落在 F001 段位 `1-10` 的子段 1-2；`4/5-10` 不触发（`contracts/exit-codes.md`） |
| G4 | §3.1 测试三层 `unit` / `integration` / `e2e/phase`；黑盒脚本只跑子进程、不 import 业务代码 | ✅ PASS | 新增 `tests/unit/test_template_skeleton.py` + `tests/e2e/phase/verify_phase_f001_p2.py`（仅 `subprocess` + `shutil.which`）；**`tests/integration/` 仍为空占位** —— P2 虽新增 2 个 core 模块，但它们由**单一流水线**（`init_workspace_inner`）串联、无跨模块协作契约（模块间唯一接口是函数调用，已由单元测试覆盖），跨层边界由 e2e 黑盒场景（子进程 + 文件系统副作用）覆盖，故集成层继续留待首次出现真正的多模块协作时启用（同 P1 口径） |
| G5 | §4.1 CI：pytest + ruff + mypy；§4.1 TDD 四件套流程 | ⚠️ 部分 | 静态检查与测试命令已定义（`pyproject.toml` 配置 + quickstart §3 / §6）；**CI 工作流文件 Deferred**（仓库级资产，同 P1 R-08），不阻塞本 Phase；沿用 P1 已登记的临时例外 E-01 —— **例外范围经 Maintainer 批准扩展至 F001-P2**（E-01 原登记范围为「仅 F001-P1」；本次扩展**不改变**其过期时间「F001-P3 结束前」、**不改变**其替代保障清单、**不新增**任何豁免条款；**宪法 §6.3 E-01 的「范围」行已同步回写为「仅 F001-P1 与 F001-P2」** —— 保持单一权威来源，见 tasks T079） |
| G6 | §3.2 永不使用清单（LangSmith / deepagents / ShellToolMiddleware / subagent） | ✅ PASS | **本 Phase 风险最高的一条**（新增了依赖链）→ R-02 实测：导入上游 saver 新增 471 个模块、langsmith 相关 **0** 个；`langsmith` 仅作为 `langchain-core` 的硬传递依赖被**安装到磁盘**，donkey **永不 import** —— N-12 的约束对象是 **donkey 自有代码路径**的 import 与使用（边界澄清见宪法 ADR **D-17**）；quickstart §4 含 `langsmith` / `deepagents` grep 自检；SC-017 承载验收 |
| G7 | §2.2 路径绝对化原则 | ✅ PASS | workspace 内一切相对引用以 workspace 绝对路径为唯一根；模板源路径由条目 `path` 派生（`templates_root / f"{path}.txt"`），不依赖进程 cwd / HOME |
| G8 | §2.3 / AC-3 workspace 原子性 + init 幂等；D-01 workspace 自带 manifest | ✅ PASS | FR-005 ~ FR-017 幂等三态（新建 / 跳过 / 强制重建）；FR-018 ~ FR-023 工作区清单（4 字段）；FR-013 强制重置作用域严格限定在清单内 |
| G9 | §2.8 / D-08 三端共用 `core.api` 库 API | ✅ PASS | `init_workspace` 门面函数体补齐（FR-024 ~ FR-026）；`InitResult` 契约**冻结不动**（FR-025），web / gui 后续直接复用 |
| G10 | N-03 入口点不得位于 `core/` | ✅ PASS | 入口点仍在 `cli/cli_client.py` + `__main__.py` + `[project.scripts]`，本 Phase 不动 |
| G11 | §3.4 / D-05 模板与 sqlite3 schema 属 P2 | ✅ PASS | **本 Phase 即 D-05 的实现 Phase** —— `core/workspace/sqlite3_templates.py` 程序化建库（MUST NOT 携带二进制模板，FR-030）；上游 saver 的**实例** `setup()` 建 `checkpoints` / `writes`（R-01 / R-04）；donkey 自管 `sessions_metadata` + 2 索引（FR-031 / R-05） |
| G12 | §4.6 技术指标：单元测试覆盖率 ≥ 80%（`donkey.core`） | ✅ PASS | spec SC-013；以**独立命令** `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` 度量（MUST NOT 写入 pytest 全局 `addopts`，否则 e2e 单独运行时不 import 业务代码会把覆盖率拉到 0 而误报失败）；`pytest-cov` 已在 dev 依赖中 |
| G13 | §3.1 `tests/e2e/phase/verify_phase_<f>_<n>.py` 必须真正被 pytest 收集 | ✅ PASS | P1 已加 `python_files = ["test_*.py", "verify_phase_*.py"]` → 新脚本 `verify_phase_f001_p2.py` 自动被收齐；覆盖率度量仍只跑 `tests/unit/` |
| G14 | N-01 workspace 内禁止出现 `agent.py` / `main.py` 或任何 Python 入口文件；D-10 同义 | ✅ PASS | 本 Phase 生成的模板**只有** `.md` / `.toml` / `.json` / `.gitignore` —— 清单中**无** `format: "python"` 条目（该格式值已支持但 P2 无条目使用，留给 F001-P3 的 3 个内置 `@tool`）；e2e 场景 11 断言 `tools/` 下无 `.py` |
| G15 | N-11 / §2.8 三端对等（cli / web / gui 共用 `core.api`） | ✅ PASS（阶段性） | 本 Phase 仅交付 cli 通道，`web/` / `gui/` 维持空占位；三端对等由 F005 / F006 达成（同 P1 口径） |
| G16 | §2.6 workspace 目录必填项（`instruction.md` / `providers/`（含 `providers/default.toml`）/ `tools/` / `mcp/mcp.json` / `skills/` / `memory/`）+ D-01 的 workspace `manifest.json` | ✅ PASS | **本 Phase 即 §2.6 的实现 Phase** —— 6 项必填 + D-01 清单全部落地（FR-039 ~ FR-043）；e2e 场景 1 逐项断言 |
| G17 | N-02 禁止 subagent / 子智能体任何目录或字段 | ✅ PASS | 46 条清单条目中无任何 subagent 相关路径；模板正文亦无该类字段（FR-054） |
| G18 | §3.5 数据安全分级（凭据高敏感 / 自动脱敏 / 不上传 workspace） | ✅ PASS（阶段性） | provider stub 出厂态凭据为空串；`donkey init` **不打印**任何凭据（摘要只含路径 / 名称 / 标志 / 三个计数）；donkey 不上传 workspace 内容。**已知遗留**：`.gitignore` 模板不忽略 `providers/*.toml` → 用户提交 workspace 会连带提交明文密钥 —— 由提示词固定内容 + 宪法"凭据由用户自负"共同决定，**本 Phase 不擅自改动**（见「复杂度与风险」表中「`.gitignore` 不忽略 `providers/*.toml`」行） |
| G19 | D-11 `store.sqlite3` / `knowledge.sqlite3` v1 仅占位空文件 | ✅ PASS | FR-032：0 表 0 索引、MUST NOT 被任何运行时路径读取；R-14 登记的上游 SQLite Store 属 v3 议题，本 Phase MUST NOT 引用 |
| G20 | §4.6 技术验收：所有 exit code 与 §4.4 完全一致 | ✅ PASS | 本 Phase 实际使用 `{0,1,2,3}`；`contracts/exit-codes.md` 给出完整映射表与未登记子类的兜底口径 |

**门禁结论**：无违例。G5 为显式 Deferred（仓库级 CI 文件，非违例 —— 临时例外 E-01 的范围已登记扩展至 F001-P2，过期时间不变）；G6 是本 Phase 因新增依赖链而**必须重点验证**的一条 —— 已由 R-02 的实验实证闭合；G4 的集成层留空沿用 P1 口径并说明理由；G18 登记了一处「已知遗留但不属本 Phase 范围」。

**Phase 0 research 放行**（15 条决策已落地，NEEDS CLARIFICATION 残留 0 项）。

### Phase 1 设计后复核（Re-check）

| 门 | 复核结论 | 复核要点 |
|---|---|---|
| G2（分层） | ✅ 维持 PASS | 设计落点已明确：上游 saver 的 import **只**出现在 `core/workspace/sqlite3_templates.py`；`cli/cli_client.py` 的改动被 [contracts/cli-contract.md](contracts/cli-contract.md) §5 锁定为 **2 行代码改动**（异常映射表 1 行 + 摘要强制清空提示 1 行）**+ 1 处文案同步**（`--help` / 子命令说明，FR-064 ③）—— 客户端改动共 **3 项**；[quickstart.md](quickstart.md) §4 给出 4 条 grep 自检 |
| G4（测试三层） | ✅ 维持 PASS | 集成层留空的理由已写实：P2 的 2 个新 core 模块由**单一流水线**串联、无跨模块协作契约；跨层边界由 e2e 黑盒场景覆盖 |
| G6（永不使用清单） | ✅ 维持 PASS（**新增证据**） | R-02 的实验是**交付环境实测**而非纸面推断：471 个新模块中 langsmith 相关 0 个；quickstart §1 把该验证固化为**装依赖后必跑的门禁冒烟**；quickstart §4 有全仓 grep；SC-017 承载验收 |
| G8（幂等 + 原子性） | ✅ 维持 PASS | 幂等三态已落成 [data-model.md](data-model.md) §6 的**状态机**（含"已存在且只读""已存在但是目录"两条异常分支）；计数口径已推导到具体数值（`46 / 40 / 0`） |
| G11（D-05 sqlite3） | ✅ 维持 PASS | 三个 builder 的契约已写进 [contracts/library-api.md](contracts/library-api.md) §5（含上游 `setup()` 的**实例**调用形式与版本陷阱）；`templates/` 下 MUST NOT 出现二进制 sqlite3（契约 B11 自检） |
| G14（N-01 禁 Python 入口） | ✅ 维持 PASS | 清单 46 条中 `format: "python"` **零条目** —— 该事实现在是门禁依据（e2e 场景 11 断言 `tools/` 下无 `.py`） |
| G16（§2.6 必填项） | ✅ 维持 PASS | 6 项必填 + D-01 清单已逐项落到 [contracts/template-manifest.md](contracts/template-manifest.md) §2 的 46 条清单 |
| G18（数据安全） | ✅ 维持 PASS（**遗留已登记**） | `providers/*.toml` 的明文密钥不进 `.gitignore` —— 已在 [contracts/template-manifest.md](contracts/template-manifest.md) §5.10 与本计划「复杂度与风险」双处登记为 v2 议题；本 Phase 不擅自改动提示词固定的内容 |
| G19（D-11 占位空文件） | ✅ 维持 PASS | R-14 登记的上游自带 SQLite Store 属 v3 议题；本 Phase MUST NOT 引用（契约 §6 明列） |
| 其余各门 | ✅ 维持 PASS | 设计未引入新的越界面 |

**复核结论**：**无违例**。Phase 1 设计（`data-model.md` + `contracts/` × 4 + `quickstart.md`）未引入任何新的宪法冲突；
唯一需要重点看管的仍是 **G6**，已由「实验证据 + 交付期门禁冒烟 + 静态 grep + SC 验收」四重保险覆盖。

**Phase 1 设计放行** → 可进入 `/speckit.tasks`。

## Project Structure

### Documentation (this feature)

```text
specs/001-donkey-init-workspace/phase-2-template-skeleton/
├── plan.md              # 本文件（/speckit.plan 输出）
├── research.md          # Phase 0 输出（15 条决策 R-01 ~ R-15 + 实验证据）+ 回填的 R-16 ~ R-18（三文档交叉复核后定点修订）
├── data-model.md        # Phase 1 输出（实体 / 状态 / 计数口径 / 失败矩阵）
├── quickstart.md        # Phase 1 输出（可复制执行的验证指南）
├── contracts/           # Phase 1 输出
│   ├── library-api.md       # 核心库 API 契约（init_workspace / InitResult / 渲染与清单能力）
│   ├── exit-codes.md        # 退出码段位与异常映射表（新增码值 3）
│   ├── template-manifest.md # 模板清单 schema + 46 条条目 + 37 个源文件 + sqlite3 构造契约
│   └── cli-contract.md      # 命令行接口契约（参数 / 退出码 / 输出 / 强制清空提示行）
├── spec.md              # 需求来源（已冻结，含 27 项澄清决策）
├── checklists/
│   └── requirements.md  # 质量检查清单（16/16）
└── tasks.md             # Phase 2 输出（/speckit.tasks 生成，本命令不产出）
```

### Source Code (repository root)

```text
donkey/                              # 顶层 Python 包（仓库根即包根）
├── __init__.py                      # 包标识（版本号来源；MUST NOT 被工作区清单 import）
├── __main__.py                      # python -m donkey 入口 → sys.exit(main())
├── core/                            # 引擎层 / 库 API（零进程感知）
│   ├── __init__.py
│   ├── api.py                       # InitResult（契约冻结，不改）+ init_workspace 门面（补齐模板渲染）
│   ├── exit_codes.py                # 段位常量（新增启用 EXIT_CODE_TEMPLATE_GENERATION = 3）
│   ├── exceptions.py                # DonkeyError ← WorkspaceInitError ← {PathNotFound, PathPermission, TemplateGeneration}
│   └── workspace/
│       ├── __init__.py
│       ├── init.py                  # P1 三函数不动；P2 追加 load_template_manifest / render_templates / init_workspace_inner
│       ├── manifest.py              # 【新增】工作区清单读写（write / read / ensure_workspace_manifest）
│       ├── sqlite3_templates.py     # 【新增】三个 sqlite3 结构构造器（build_sessions / build_store / build_knowledge）
│       └── templates/               # 模板资产（安装包内）
│           ├── manifest.json        # 模板清单（46 条 = P1 的 3 条 + P2 追加 43 条）
│           ├── instruction.md.txt   # ← 覆盖 P1 占位
│           ├── README.md.txt        # 【新增】工作区总览（含 {{ workspace_name }}）
│           ├── .gitignore.txt        # 【新增】版本控制忽略规则
│           ├── providers/
│           │   ├── default.toml.txt  # ← 覆盖 P1 占位（两个字段出厂为空串）
│           │   ├── README.md.txt     # 【新增】26 家索引说明
│           │   └── <26 个>.toml.txt   # 【新增】openai / anthropic / google / … / openrouter（§8.3 逐字抄录）
│           ├── mcp/
│           │   ├── mcp.json.txt      # ← 覆盖 P1 占位（内容已一致，仍按 spec 覆盖）
│           │   └── README.md.txt      # 【新增】
│           ├── skills/
│           │   ├── README.md.txt      # 【新增】
│           │   └── example/
│           │       └── SKILL.md.txt   # 【新增】frontmatter 仅 name + description
│           ├── tools/
│           │   └── README.md.txt      # 【新增】（P3 才生成 3 个内置 @tool，本 Phase 不生成）
│           └── memory/
│               └── README.md.txt      # 【新增】三模板 + --force 备份指引
├── cli/                             # 客户端层
│   ├── __init__.py
│   └── cli_client.py                # argparse 入口 + 异常映射表（+1 行）+ 摘要（+1 行强制清空提示）
├── web/                             # 空占位（`.gitkeep`，F005 实施，本 Phase 不填内容）
└── gui/                             # 空占位（`.gitkeep`，F006 实施，本 Phase 不填内容）

tests/
├── unit/
│   ├── test_init_workspace.py       # P1 的 17 个用例（本 Phase MUST NOT 破坏）
│   ├── test_cli_client.py           # P1 的 3 个用例（本 Phase MUST NOT 破坏）
│   └── test_template_skeleton.py    # 【新增】≥16 个用例（逐条用例清单以 tasks.md 的 T006 / T008 / T010 / T011 / T014 / T015 为准）
├── integration/                     # 仍为空占位（见 G4）
└── e2e/
    └── phase/
        ├── verify_phase_f001_p1.py  # P1 的 7 个黑盒场景（本 Phase MUST NOT 破坏）
        └── verify_phase_f001_p2.py  # 【新增】14 个黑盒场景断言

pyproject.toml                       # 打包 + 工具配置（新增 1 个运行期依赖；**package-data MUST 显式列入 ".gitignore.txt"** —— setuptools 的 glob 会过滤 `.` 开头的文件名，漏列则 wheel 缺该源 → 安装后 donkey init 报源模板缺失 exit 3，见 quickstart §7.1 B2b；**B2b 前 MUST 清 build/** —— 残留的 build/ 会掩盖该缺陷；ruff / mypy / pytest 配置不变）
```

**Structure Decision**：沿用**单包 + 客户端分层**结构（仓库根即包根 `donkey/`），与 P1 结论一致 —— 宪法 §3.1 规定测试目录 `tests/` 与 `core/` / `cli/` / `web/` / `gui/` 同级；`harness/` 是研究资料（非可发布代码），不参与打包。
本 Phase 的 2 个**新增模块**（`workspace/manifest.py` / `workspace/sqlite3_templates.py`）放在 `core/workspace/` 下而非塞进 `init.py`：
前者被 F002 / F003 复用（工作区清单读取）、后者把"程序化建库"与"路径校验"两种关注点分开（`init.py` 已因 P1 而专注于校验）。

## 复杂度与风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| **`--force` 下目录条目删除文件 → 抹掉目录内的 34 个模板文件** | 清单顺序为「37 文本 → 6 目录 → 3 sqlite3」；6 个目录条目内共 **34** 个文件（**32** 个本轮新建 + **2** 个 P1 已有的 `mcp/mcp.json` / `providers/default.toml`）；若目录条目按旧口径（清空其内清单内文件）删除，已 unlink+重建的文件会被删掉且不再生成 → workspace 残缺、`files_created=40` 是假账、e2e 场景 13 失败 | **已裁决并修订 spec FR-010**：目录条目在 `--force` 下 MUST NOT 删除任何文件，其内清单文件由各自的文本 / sqlite3 条目负责 unlink+重建（净效果仍是"恢复出厂"）。FR-012 的顺序无关性随之成立（library-api §3.2 第 5 条 / data-model §6 状态机图 / I3 已同步）。**（现状：目录条目在 force 下 MUST NOT 删除任何文件，FR-010 已修订 —— 本行登记的是"若回退到旧口径会发生什么"的残余风险，不是当前行为。）** |
| **隐藏模板源不入 wheel** → 安装后 `donkey init` exit 3 | 模板清单条目 `.gitignore` 的源文件缺失 → FR-007 触发 → 整个 `donkey init` 不可用 | setuptools 的 `package_data` 用 `glob(recursive=True)`，会过滤**以 `.` 开头的文件名** → `templates/.gitignore.txt` 默认不入包（已用真实 wheel 干净构建实证：旧配置 → 缺失，新配置 → 在包内）。修法：`package-data` **显式列入 `".gitignore.txt"`**；并新增 B2b「按打包产物核对 37 个源文件」自检 —— 编辑安装（`pip install -e .`）下无感，**只有 wheel / sdist 安装才暴露**，且 `pathlib.rglob` 的 B2 自检查不出来（假阳性）。⚠️ B2b 前 MUST 清 `build/` —— setuptools 把源复制进 `build/lib/` 且不清隐藏文件，残留 `build/` 会**掩盖**该缺陷 |
| **N-12 的边界解释**（langsmith 被装到磁盘） | 触碰宪法 N-12 红线区 | 宪法 N-12 已补边界澄清（ADR **D-17**）：N-12 的约束对象是 **donkey 自有代码路径**（`donkey.core` / `cli` / `web` / `gui`）的 import 与使用；第三方库的传递依赖**被安装到磁盘**不构成"使用"，但 MUST 在 plan 中登记并由门禁验证。R-02 实测：导入上游 saver 新增 471 个模块、langsmith 相关 **0** 个 → donkey **永不 import** langsmith（`langsmith` 仅作为 `langchain-core` 的硬传递依赖被安装）；quickstart §4 grep 自检 + SC-017 验收 |
| **上游包版本不兼容**（本机用户级存在 `sqlite 3.1.1` + `checkpoint 4.2.0` 的坏组合，导入即 `ImportError: cannot import name 'writes_sort_key'`） | 环境性失败，且报错信息与本 Phase 无关，误导排查 | `pyproject.toml` 声明 `langgraph-checkpoint-sqlite>=3.1,<4`，让 pip 解析出 `langgraph-checkpoint>=4.3.0`；quickstart §1 给出**环境自检命令**（导入 + 建表冒烟），在装依赖后立即验证 |
| **`setup()` 被误写成非实例调用**（`SqliteSaver.setup(conn)`） | `AttributeError` 逃逸成裸异常 → 违反 FR-014（错误 MUST 归一为 `TemplateGenerationError`） | R-01 / R-04 实测确认签名；`sqlite3_templates.py` 的 builder MUST 用 `SqliteSaver(conn).setup()`；且 builder 内部 MUST 把任何异常（含 `AttributeError`）包成 `TemplateGenerationError` |
| **清单条目顺序 ≠ 依赖顺序**（`providers/default.toml` 排在 `providers` 目录条目之前） | 严格按序渲染必然 `FileNotFoundError` | R-06；渲染 MUST 在写文件前确保父目录存在（FR-012） |
| **模板源被拆成两段交付**（清单的 46 条是原子集合，源却分批就位） | 清单有条目而源缺失 → FR-007 触发 → **`donkey init` 直接 exit 3**、workspace 建不出来；且用户故事的"独立可测"承诺落空 | 实施顺序第 6 步已把 **37 个源 MUST 一次性全部就位**写为前提；构建期自检 B2 的「双向一一对应」在源未齐时会立即暴露（quickstart §7） |
| **P1 的 3 个占位源文件未覆盖** | `instruction.md` 残留 "待 F001-P2 填充"、`default.toml` 残留 `{{default_provider}}` 占位符 | R-07；FR-042 明确"覆盖"语义；e2e 场景 2 断言 `default.toml` 解析后不含占位符字面量、场景 5 断言名称已注入 |
| **26 份 provider stub 手工誊写必漏** | 漏模型条目 / 漏注释 → 违反 FR-046 与 SC-015 的 "51 条" 硬指标 | R-09； MUST 用**脚本抽取** §8.3 的 fenced code block，人工复核 diff 后提交；脚本不落仓库 |
| **陈旧 `-wal` 的危害被高估** → 实现者据此写出错误的注释或错误的实现 | 误导后续维护者 | R-03 实测：陈旧 WAL 因盐值不匹配被**安全忽略**（重建后行数 0）；连带删除仍按 spec 实现（行为确定可测），但注释 MUST NOT 声称"不删必然污染" |
| **e2e 场景 14 误用集合相等断言** | `sqlite_autoindex_sessions_metadata_1`（PRIMARY KEY 自动索引）导致假失败 | R-05；MUST 用 `in` 判定索引存在性（spec 给的断言形态即如此），契约中已登记提醒 |
| **`--force` 的 sqlite3 删除是破坏性动作，用户可能未备份** | 真实数据丢失 | 内存库目录说明模板 MUST 含备份命令示例（FR-052 / SC-018）；CLI 摘要 MUST 额外输出一行"记忆库数据已被清空"（FR-068 / R-11）；e2e 场景 13 断言"备份文件不受影响" |
| **`.gitignore` 不忽略 `providers/*.toml` → 明文密钥随 workspace 进版本库** | 凭据泄漏（宪法 §3.5 定为高敏感字段） | **本 Phase 不擅自改动**（提示词固定了 `.gitignore` 内容 + 宪法"凭据由用户自负"）；登记为 G18 的「已知遗留」，建议随 v2 的 workspace 打包 / 导出功能一并设计（届时统一决定哪些文件进包） |
| **覆盖率未达 80%** | SC-013 不达标，Phase 完成判据不成立 | R-13：独立命令度量；不足时优先补单测而非下调阈值 |
| **`langgraph-checkpoint-sqlite` 已自带 `langgraph/store/sqlite/`** | 宪法 D-11 的"v3 自研 SqliteStore"路线可能被上游现成实现替代 | R-14 登记为 Maintainer 决策项；本 Phase MUST NOT 引用（FR-032 / G19） |

## 实施顺序（任务拆解留给 `/speckit.tasks`）

> 本节只给**依赖顺序**（谁必须先存在），不规定逐条任务。

1. **依赖与门禁闭合**：在 `pyproject.toml` 声明 `langgraph-checkpoint-sqlite>=3.1,<4` → 装依赖 → 跑 quickstart §1 的**环境自检**（导入 + 建表冒烟 + langsmith grep），确认 R-01 / R-02 / R-04 三个实验结论在交付环境复现；
2. **异常与退出码**：`core/exceptions.py` 追加 `TemplateGenerationError` **与文案常量 `_NEXT_STEP_TEMPLATE`**（R-12 —— MUST 与错误类同模块，MUST NOT 落 `init.py`，否则 `manifest.py` → `init.py` → `manifest.py` 循环 import）+ `core/exit_codes.py` 把 `EXIT_CODE_TEMPLATE_GENERATION = 3` 从"建档"转为"启用"；
3. **sqlite3 结构构造器**：`core/workspace/sqlite3_templates.py`（3 个 builder + 统一错误包装）→ 其单测先行（结构完整 / 两占位 0 表 / 幂等，FR-058）；
4. **工作区清单**：`core/workspace/manifest.py`（write / read / ensure）→ 其单测先行（5 类别，FR-055 后 5 项；**另加两项补充断言** —— FR-018 的「读取时文件不存在 → 返回『无』」与 FR-023 的「`ensure_workspace_manifest` 与 `write_workspace_manifest` 严格等价，含『坏 JSON + force』与『坏 JSON + 不带 force』两个组合」）；另按 R-17 固化「工作区被重命名后 `name` 保留旧名」的语义（**不新增任何输出**）；
5. **清单加载与渲染**：`core/workspace/init.py` 追加 `load_template_manifest` / `render_templates` → 其单测先行（渲染类 + 失败分支类用例，FR-055 前 11 项；逐条以 tasks.md 为准）；其中**权限失败用例 MUST 以注入式构造产生**（`monkeypatch` 在写入边界抛 `OSError(EACCES)`），MUST NOT 依赖运行账号的特权状态（R-18 —— root 会绕过 DAC 权限检查，chmod 方案在 root CI 容器中失效）；
6. **模板资产（37 个源 MUST 一次性全部就位 —— 否则 `donkey init` 直接 exit 3）**：模板清单的 46 条是一个**原子集合**（spec FR-039 / FR-040 / FR-041），而 spec FR-007 规定「文本模板类条目的源文件缺失 MUST 抛 `TemplateGenerationError` → 退出码 `3`」→ 清单里有条目而源缺失时 workspace 建不出来。故 MUST NOT 把模板源拆成"先一部分、后一部分"的两段交付。**37 个源**的构成：① **脚本抽取 26 份**供应商配置源（调研 §8.3.3 ~ §8.3.28，含全部 **51** 条 `[models.*]` 模型条目，MUST NOT 手工誊写）；② **11 份文本模板源**——其中 **3 份覆盖** P1 的占位源（`instruction.md.txt` / `providers/default.toml.txt` / `mcp/mcp.json.txt`）、**8 份新增手写**（`README.md.txt` / `.gitignore.txt` / `tools/README.md.txt` / `mcp/README.md.txt` / `skills/README.md.txt` / `memory/README.md.txt` / `skills/example/SKILL.md.txt` / **`providers/README.md.txt`**）；③ 随后 `manifest.json` **末尾 push 追加 43 条**（MUST NOT 改 P1 已有 3 条）；④ 校验「**37 个源文件 ↔ 37 个文本条目**」**双向**一一对应 + 6 个目录条目与 3 个 sqlite3 条目**无**同名 `.txt` 源 + 安装包内**无**二进制 sqlite3 模板（宪法 D-05）；⑤ 校验**打包产物**内含全部 37 个源文件（含隐藏名 `.gitignore.txt` —— `pyproject.toml` 的 `package-data` MUST 显式列入，quickstart §7.1 B2b）。落地物计数口径：**41 个文件**（37 文本 + 3 sqlite3 + 1 工作区清单）+ **7 个目录**（根 + 5 必填 + `skills/example`）；
7. **内部流程**：`core/workspace/init.py` 追加 `init_workspace_inner`（五步流水线，FR-027）→ `core/api.py` 门面函数体替换（FR-024 ~ FR-026）；**R-16**：步骤 ⑤ 失败**不回滚** —— 步骤 ④ 已落地的文件 MUST 保留，本 Phase MUST NOT 实现任何事务回滚机制；
8. **客户端层**：`cli/cli_client.py` 追加映射表 1 行（FR-036）+ 摘要强制清空提示 1 行（FR-068 / R-11）+ **同步 `--help` / 子命令说明文案 1 处**（FR-064 ③ —— P1 遗留的"不加载模板清单、不生成模板内容"与"本阶段仅记录并回显，不触发任何删除 / 重置"在 P2 落地后均为错误陈述，MUST NOT 原样保留；**客户端改动共 3 项**）；
9. **黑盒验收层**：`tests/e2e/phase/verify_phase_f001_p2.py`（14 个场景）；
10. **回归验证**：`tests/e2e/phase/verify_phase_f001_p1.py` + `tests/unit/test_init_workspace.py` + `tests/unit/test_cli_client.py` 仍全绿（SC-002）；
11. **静态检查**：`ruff check donkey/ tests/` + `mypy donkey/ tests/` 零 error 零 warning（SC-009）；
12. **覆盖率验证**：`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` → `donkey.core` 行覆盖率 ≥ 80%（SC-013 / 宪法 §4.6；e2e 黑盒脚本不参与该度量，R-13）。

> **TDD 顺序**：第 3 ~ 5 步各自"先写测试并确认失败 → 再补实现"，MUST NOT 等全部实现完成后再补测（同 P1 口径）。

## 后续 Phase / 仓库级（不属本 Phase）

| 事项 | 归属 | 说明 |
|---|---|---|
| 3 个内置 `@tool`（`tools/filesystem.py` / `commandline.py` / `webfetch.py`）+ `tools/__init__.py` + 示例 Skill 的完整第二层正文与第三层资源（`reference/` / `scripts/` / `templates/`） | F001-P3 | 清单 `format: "python"` 已在本 Phase 支持但**无条目使用** —— P3 追加 8 条后清单累计 **54** 条（R-08 口径延续） |
| `donkey load` / `session` / `run` 子命令 | F002 / F003 / F004 | 复用 `core.api` 门面与 `core/workspace/manifest.py`（工作区清单读取） |
| `memory/sessions.sqlite3` 的结构健康检查（`SqliteSchemaError` exit 16，5 项断言） | F002-P2 | 判据以 `harness/report/sessions_sqlite表结构一览.md` §7 为准；本 Phase 已保证出厂态 5 项全部满足 |
| `store.sqlite3` 的 `store_items` 等建表 SQL | v3 SqliteStore（TD-02） | R-14：上游包已自带 `langgraph/store/sqlite/`，路线待 Maintainer 评估 |
| `.github/workflows/ci.yml` | 仓库级（Deferred） | 最小内容已备：`pytest tests/` + `pytest tests/unit/ --cov=donkey.core --cov-fail-under=80` + `ruff check donkey/ tests/` + `mypy donkey/ tests/`；骨架沿用 P1 R-08 |
| `.gitignore` 是否忽略 `providers/*.toml`（凭据明文） | v2（建议随 workspace 打包 / 导出功能一并设计） | G18 登记的已知遗留，本 Phase 不改动 |
| `donkey_version` 由硬编码改动态 | v1.x | 现为硬编码 `'0.1.0'`（FR-021）；将来 MUST 用包元数据查询而非内部符号。**注意双源风险**：`donkey/__init__.py` 的 `__version__` 与工作区清单的硬编码 `"0.1.0"` 是两处独立维护的值，且 FR-021 禁止 import 内部符号 → 版本漂移无告警。建议在 v1.x 的 CI 中加一条"两处版本号一致"的断言 |

## Complexity Tracking

**无违例**——Constitution Check 全部 PASS（G5 为显式 Deferred，非违例）。本表登记**超出本计划范围的复杂度增量 / 需豁免的偏离**；「复杂度与风险」表登记的是**已识别风险**，二者不重复。

| 复杂度增量 | 说明 |
|---|---|
| 运行期依赖从 0 个增至 1 个 | 用户已裁决（spec 澄清决策 1）：短期记忆库的上游两表 MUST 由上游 saver 的**实例** `setup()` 创建，donkey MUST NOT 手写 DDL（避免结构漂移）。代价：新增 1 个直接依赖 + 4 个传递依赖，且 `langchain-core` 会把 `langsmith` 拉进磁盘 —— 已由 R-02 实证「不进入进程」并在 G6 / SC-017 双重把关 |
| 客户端改动从 1 行扩到 3 项 | 用户已裁决（spec 澄清决策 4）：强制重置会清空记忆库数据，摘要 MUST 额外输出一行显式提示（FR-068）。**新增第 ③ 项**：`--help` / 子命令说明文案同步 —— P1 遗留文案（"不加载模板清单、不生成模板内容" / "本阶段仅记录并回显，不触发任何删除 / 重置"）在 P2 落地后是**错误陈述**，留着即是对用户说假话（FR-064 ③ / cli-contract §5 第 3 行）。原提示词"客户端只改 1 行映射表"以该裁决为准 |
| 单测类别从 14 增至 16 | 用户已裁决（spec 澄清决策 5）：退出码 3 的错误信息 MUST 含"下一步"，需独立断言落点（FR-055 第 11 项 / SC-020）；`/speckit.analyse` 复核后追加第 16 类"工作区清单内容非法 JSON → exit 3"（FR-055 / FR-018 的验证落点缺口）|
| 新增 2 个 core 模块 | `workspace/manifest.py`（F002 / F003 复用）+ `workspace/sqlite3_templates.py`（建库与校验解耦）；MUST NOT 塞进 `init.py` —— `init.py` 已因 P1 专注于校验，追加 2 个关注点会破坏其单一职责 |
| 新增 3 个「边界护栏」单测（**超出** FR-055 的 16 类） | `/speckit.analyze` 三文档交叉复核后补齐的 3 项边界 —— ① 步骤 ⑤ 失败**不回滚**（R-16 / tasks T083）；② 工作区被重命名后**保留旧名**且 MUST NOT 触发退出码 `3`（R-17 / tasks T084）；③ 步骤 ③ 的一切失败（含 `ENOSPC`）归退出码 `2`（R-16 同批 / tasks T085）。三者均为 FR-055 之外的**补充**类别，MUST NOT 被计入或替换 FR-055 的 16 类 —— FR-055 的 16 类与「不少于 16 个用例」的口径**保持不变** |
