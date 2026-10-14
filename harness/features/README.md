# harness/features 开发目录

> 本目录是 donkey 项目所有 `featurexxx_phasexxx_<phase name>.md` 提示词文件的**索引与开发目录**，由 Maintainer 人工评审维护。
>
> **唯一权威源**：
> - 立项书：`harness/features/立项书.md`（v1.0 全文，第 0~10 章 + 附录 A–G）—— F 编号 / Phase A·B 划分 / 段位空间 / 验收标准的**唯一定义源**
> - 宪法：`.specify/memory/constitution.md`（v0.1）—— N-01 ~ N-12 不可妥协条款 + §2 核心设计原则 + §3 不可妥协约束
>
> 本 README **不**重复立项书细节，**只**做：(1) 命名规范；(2) Phase 划分依据与编号映射；(3) 跨 F 开发顺序；(4) 每个 phase 文件大致内容；(5) 自检清单。

---

## 1. 命名规范

```
feature<FEAT>_phase<PHASE>_<phase name>.md
```

- `<FEAT>`：立项书 §3.2.1 / §5.2 定义的 F 编号，3 位补 0（**F001~F006**）
- `<PHASE>`：本 README §3 定义的 Phase 序号，3 位补 0；**跨 F 全局递增**（不按 F 重置）
- `<phase name>`：snake_case，**动词或名词短语**，禁止用中文

**示例**（用户已给出）：
- `feature001_phase001_builtin_tools.md` —— F001 第 1 个 phase，三大内置工具模板

---

## 2. Phase 划分依据

### 2.1 两层切分

立项书 §5.2 / 宪法 §4.3 已定义 F 内的 Phase A / Phase B 两阶段：

| 阶段 | 范围 | 包含内容 |
|---|---|---|
| **Phase A** | 最小可用骨架 / 契约占位 / 解析 / 错误脱敏 | 库 API 签名稳定 + 错误脱敏 + 占位实现（return 框架级 dummy result）+ exit code 段位对齐 + 单测骨架 |
| **Phase B** | 完整业务逻辑 / 联调 / 测试 / 文档同步 | 完整实现 + 与前序 F 的联调 + e2e + 文档同步 |

### 2.2 为什么 Phase A / Phase B 还要再细拆

立项书 §5.2 的 Phase A / Phase B 在粒度上仍偏粗（如 F001 Phase A 同时涵盖"三大内置工具模板 + API 签名 + 占位实现 + 单测骨架"，单一 `/speckit.specify` 写不完）。本目录将每个 Phase A / Phase B **再拆分为 1~3 个独立 phase 文件**，拆分依据：

1. **单一职责**：每个 phase 文件只描述**一个可独立交付的子能力**（如"filesystem 工具模板"vs"commandline 工具模板"vs"webfetch 工具模板"是三个独立 phase），便于 Speckit 单次会话闭环
2. **依赖序最小化**：phase N 不依赖 step M（M > N）的内容；只能依赖 step ≤ N
3. **验证可见**：每个 phase 文件可独立运行 `/speckit.specify → clarify → plan → tasks → implement → analyse` 五步并产出可验证产物（API 签名 / 工具模板 / 静态检查骨架 / 动态检查实现 等）
4. **Phase A 内拆分依据**：内置工具 3 件（filesystem / commandline / webfetch）+ API 签名 + 占位实现，按"3 工具独立成 phase + API 签名打包为另一 phase"分。**filesystem 独立成 phase 是因为它最重要、逻辑最复杂、test 用例最多；commandline / webfetch 可合为 phase001**
5. **Phase B 内拆分依据**：模板生成（写文件 / 建目录 / manifest）vs 幂等与错误脱敏（check + `--force` + N-06 自检）vs e2e 联调，三块按"写"→"校验"→"测"自然分

### 2.3 不细分到什么程度

- **不**把"写错误处理"`拆成"定义错误类型 + 实现错误脱敏"两 phase —— 同一份代码内聚
- **不**把"单测"拆成"写测试 + 跑测试"两 phase —— Speckit `/speckit.implement` 一步到位
- **不**为每个 python 文件单独建 phase —— F004 run 的中间件挂载 10 项**合为 1 phase**，由 phase 文件阶段**串行**处理（一次写完所有中间件的 import + 中间件列表 + 编译验证）

---

## 3. Phase 总览表（跨 F 全局编号）

> **关键路径（Phase 序串行）**（立项书 §5.2 关键路径 + §5.4 甘特图）：
> F001 Phase A → F001 Phase B + F002 Phase A → F002 Phase B + F003 Phase A → F003 Phase B + F004 Phase A → F004 Phase B + F005 Phase A → F005 Phase B + F006 Phase A → 三套模板 → Release

| Phase | 文件名 | F | Phase A/B | 阶段名 | 核心交付物 | 依赖 phase |
|---|---|---|---|---|---|---|
| 1 | `feature001_phase001_builtin_tools.md` | F001 | A | 三大内置工具模板 | `tools/filesystem.py` + `tools/commandline.py` + `tools/webfetch.py` 模板（§1.2.4 三层模型 Level 3 通道） | — |
| 2 | `feature001_phase002_init_api_skeleton.md` | F001 | A | init API 骨架与 exit code 段位 | `core.api.init_workspace(path, name, force)` 签名 + 占位实现 + exit code 1-10 段位预留 + 单测骨架 | phase 1 |
| 3 | `feature001_phase003_init_template_generation.md` | F001 | B | workspace 模板整生成 | workspace 目录创建 + 模板文件写入（instruction.md / provider.toml / mcp/mcp.json / skills/example/SKILL.md / memory/ / README.md / .gitignore / workspace manifest） | phase 2 |
| 4 | `feature001_phase004_init_idempotent.md` | F001 | B | 幂等 / --force / 错误脱敏 / e2e | 幂等校验 + `--force` 标志 + 宪法 N-06 自检（load 失败不改 workspace 反向印证）+ 错误脱敏 + e2e 联调 + 单测完善 | phase 3 |
| 5 | `feature002_phase005_load_static_check_skeleton.md` | F002 | A | 静态检查骨架 | provider.toml TOML 解析 + mcp/mcp.json JSON 解析 + skills/*/SKILL.md YAML frontmatter 解析 + instruction.md 存在性检查 + exit code 11-20 段位预留 + 单测骨架 | phase 4 |
| 7 | `feature002_phase006_load_dynamic_check_full.md` | F002 | B | 动态检查 9 项全实现 | 模型连通性 ping + sqlite3 schema 健康 + tools/*.py `@tool` 自动发现 + skills loader 可加载 + MCPAdapter 拉起 server + exit code 11-19 码值映射 + 多错误优先级规则 + warning 不计入失败 + e2e 联调 | phase 5 |
| 6 | `feature003_phase007_session_list_new.md` | F003 | A | session list/new 占位 | `core.api.list_sessions` + `core.api.new_session` 签名 + 占位（默认"无标题会话"）+ sqlite3 schema 健康检查 + exit code 21-30 段位预留 + 单测骨架 | phase 6 |
| 8 | `feature003_phase008_session_remove_import_title.md` | F003 | B | session 全套 + 标题总结 | `core.api.remove_session` + `core.api.import_session` 完整实现 + `core.api.new_session` 内部标题总结机制（宪法 N-10：图外 LLM 调用，不进 Agent Loop）+ 与 F002 load 联调 + e2e | phase 7 |
| 9 | `feature004_phase009_run_graph_skeleton.md` | F004 | A | LangGraph 主图骨架 | 主图 State + Edges + 10 项 v1 中间件挂载（§1.5.4 / 宪法 §2.7.1）+ SqliteSaver 接入 + Skills loader 集成 + MCP loader 集成 + Provider loader 集成 + exit code 31-100 段位预留 + 编译验证（10 节点） | phase 8 |
| 10 | `feature004_phase010_run_agent_loop.md` | F004 | B | Agent Loop 完整联调 | Skills 三层加载（per-skill `load_skill_<name>` 工具生成）+ MCP server 真实调用 + 24h 长稳测试 + 迁移验收用例（立项书 AC-2）+ e2e | phase 9 |
| 11 | `feature005_phase011_web_skeleton.md` | F005 | A | Web 客户端主体 | 前端框架选型 + UI 设计 + WebSocket/SSE 事件流 + Markdown/代码高亮 + 会话管理 UI + 调 `core.api` 全套接口 | phase 10 |
| 12 | `feature005_phase012_web_e2e.md` | F005 | B | Web e2e 联调 | Web e2e + CLI/Web 共享 pytest 主题（启动方式不同）+ 文档同步 | phase 11 |
| 13 | `feature006_phase013_gui_electron.md` | F006 | A | GUI = Electron 包壳 | Electron 主进程 + 渲染层 100% 复用 Web build + 原生胶水（菜单栏/文件对话框/通知/剪贴板）+ 三端打包脚本（macOS dmg / Windows nsis / Linux AppImage）+ GUI 启动验证 | phase 12 |

> **编号说明**：phase 编号 §3 表格"Phase"列**未严格按时间序排序**（phase 6=F002、7 行=F003 等），仅作 F 内局部递增。**跨 F 的开发顺序以"依赖 phase"列箭头串成 DAG**，实际执行按立项书 §5.2 关键路径串行推进（详见 §4）。

---

## 4. 跨 F 开发顺序（DAG）

```
phase 1 (F001 A: builtin_tools)
   │
   ▼
phase 2 (F001 A: init_api_skeleton)
   │
   ▼
phase 3 (F001 B: init_template_generation)
   │
   ▼
phase 4 (F001 B: init_idempotent)
   │
   ▼
phase 5 (F002 A: load_static_check_skeleton)
   │
   ▼
phase 6 (F002 B: load_dynamic_check_full)
   │
   ├──────────────────────────┐
   ▼                          ▼
phase 7 (F003 A: session_list_new)
   │
   ▼
phase 8 (F003 B: session_remove_import_title)
   │
   ▼
phase 9 (F004 A: run_graph_skeleton)
   │
   ▼
phase 10 (F004 B: run_agent_loop)
   │
   ▼
phase 11 (F005 A: web_skeleton)
   │
   ▼
phase 12 (F005 B: web_e2e)
   │
   ▼
phase 13 (F006 A: gui_electron)
```

> **串行依据**（立项书 §5.2）：
> - F001 Phase A 必须**先**完成三大内置工具模板（phase 1），否则 F001 init 模板无法生成 tools/ 内容
> - F001 Phase B 必须**先**有 API 签名（phase 2），再做模板生成（phase 3）
> - F002 必须**先**有 F001 Phase B 完整 init（phase 3-4），否则 load 不知道 init 产物长啥样
> - F003 必须**先**有 F002 完整 load（phase 5-6），否则 session 无法在已校验 workspace 上操作
> - F004 必须**先**有 F003 完整 session（phase 7-8），否则 run 无 session 可激活
> - F005 Web 必须**先**有 F004 完整 run（phase 9-10），否则 Web 无 Agent Loop 事件可消费
> - F006 GUI **必须**等 Web 完成后才启动**（宪法 N-11 + 立项书 §5.5.6：GUI = Electron 包壳，100% 复用 Web 渲染层）**

---

## 5. F001 各 phase 文件详细内容

> F001 = `donkey init <PATH>` 子命令；core API = `init_workspace(path, name, force)`。
> 立项书依据：§5.5.1（Phase A）+ §5.5.2（Phase B）+ §4.6.1（workspace 目录结构）+ §1.2.4（三层模型 Level 3 通道）+ §2.1.5（不录用中间件清单，builtin tools 不走中间件）。

### phase 1 — `feature001_phase001_builtin_tools.md`（F001 Phase A）

**目标**：交付 F001 init 模板所需的 3 个内置 `@tool` 模板，作为 Skill Level 3 的标准访问通道（立项书 §1.2.4）。

**大致内容**：

| 文件 | 暴露的 `@tool` 函数 | 关键约束 |
|---|---|---|
| `core/workspace/templates/tools/filesystem.py` | `read_file` / `write_file` / `copy_file` / `move_file` / `delete_file` / `list_dir` / `stat`（共 7 个） | 文件操作类工具；**不**含 `glob_search` / `grep_search`（由 `FilesystemFileSearchMiddleware` 接管，§1.2.4 职责正交） |
| `core/workspace/templates/tools/commandline.py` | `run_shell(command: str, timeout: int = 60) -> str`（1 个） | `subprocess.run([...], shell=False, timeout=...)`；**每次新建进程** + 显式 timeout；**不**走持久 shell session（避免 HITL 冲突，§1.5.5） |
| `core/workspace/templates/tools/webfetch.py` | `fetch_url(url: str, method: str = "GET", headers: dict \| None = None, timeout: int = 30) -> str`（1 个） | `httpx` 或 `requests` 同步调用；显式 timeout；**不**持久化 cookies |

**宪法 / 立项书自检**：

- §N-04：内置工具模板只是普通 Python `@tool` 函数，最终被 F004 run 时扫描 `tools/*.py` 自动发现（不引入 LangChain 中间件路径）
- §N-01：模板是放在 `core/workspace/templates/tools/`（**引擎侧模板**），不属于 workspace 内
- §N-05：core 不 import argparse
- §1.2.4 三层模型容错分析：filesystem / commandline / webfetch 三件套缺一不可（用户可删除/重写，但 init 必须默认生成）
- §1.5.5 显式排除：`ShellToolMiddleware` 不使用，`FilesystemMiddleware`（deepagents）不使用

**Speckit 闭环**：每个工具 `@tool` 装饰 + docstring + 关键实现约束 + 单测骨架（仅验证骨架可 import + 函数签名正确，**不**测边界）。

---

### phase 2 — `feature001_phase002_init_api_skeleton.md`（F001 Phase A）

**目标**：交付 F001 的核心库 API 签名 + exit code 段位预留 + 占位实现 + 单测骨架。

**大致内容**：

| 项 | 内容 |
|---|---|
| API 签名 | `def init_workspace(path: Path, name: str \| None = None, force: bool = False) -> InitResult` |
| 返回类型 | `InitResult(path, created_dirs: list[str], created_files: list[str], skipped_files: list[str], warnings: list[str])` |
| 占位实现 | 仅创建根目录 + 返回 `InitResult(... created_files=[], skipped_files=[], ...)`（**不**写模板，phase 3 写） |
| 异常类型 | `WorkspaceAlreadyExistsError` / `PermissionError` / `InvalidPathError`（仅声明，phase 3-4 实现） |
| Exit code 段位预留 | `1-10` 段位表（§5.5.2 + 宪法 §4.4），定义常量 `INIT_EXIT_OK=0` / `INIT_EXIT_PATH_INVALID=10` 等 |
| 单测骨架 | `tests/test_init_workspace.py`：仅验证 (a) API 可 import；(b) 占位实现返回 `InitResult`；(c) exit code 段位枚举完整 |
| 文档 | `core/api.py` 模块 docstring（含约束 N-06 / §N-07 不依赖 / §1.2.4 三层模型） |

**宪法 / 立项书自检**：

- §N-05：core 不 import argparse
- §N-03：core 不 import client
- §N-06：load 失败不改 workspace（init 反向印证：init 失败也不应留下半成品——phase 4 完整自检）
- §N-07：load 不依赖 init（init API 设计时不假设 load 存在）
- §3.5：`secret_key` 视为高敏感——phase 4 错误脱敏
- §4.6.1：workspace 目录结构已知，phase 3 落地

**Speckit 闭环**：API 签名稳定是后续 phase 3 / 4 / F002 load 联调的前提。

---

### phase 3 — `feature001_phase003_init_template_generation.md`（F001 Phase B）

**目标**：交付 workspace 模板文件的**完整写入**——让 `donkey init` 能产出 §4.6.1 定义的标准 workspace 目录。

**大致内容**：

| 文件 / 目录 | 内容来源 | 必填 |
|---|---|---|
| `instruction.md` | 模板字符串（含"你是 donkey 智能体..."默认提示词；含宪法 §1 / §2 引用注释） | ✅ |
| `provider.toml` | 模板字符串（含 `[provider].protocol` / `model_name` / `secret_key` / `temperature` / `max_tokens` 占位；§4.6.2） | ✅ |
| `tools/__init__.py` | 空文件 + docstring | ✅ |
| `tools/filesystem.py` | 从 `core/workspace/templates/tools/filesystem.py` 复制（phase 1 产物） | ✅ |
| `tools/commandline.py` | 从 `core/workspace/templates/tools/commandline.py` 复制（phase 1 产物） | ✅ |
| `tools/webfetch.py` | 从 `core/workspace/templates/tools/webfetch.py` 复制（phase 1 产物） | ✅ |
| `tools/README.md` | 工具开发规范说明（用户面向此区） | ✅ |
| `mcp/mcp.json` | `{"mcpServers": {}}` 空模板 | ✅ |
| `mcp/README.md` | MCP 配置说明 | ✅ |
| `skills/README.md` | Skills 使用说明 | ✅ |
| `skills/example/SKILL.md` | 三层模型示例 Skill（含 Level 2 Markdown 主体 + 可选 Level 3 `reference/` / `scripts/` 占位） | ✅ |
| `memory/README.md` | memory 区说明（短期/长期记忆落盘位置） | ✅ |
| `memory/.gitkeep` | 占位 | ✅ |
| `README.md` | workspace 总览（用户面向此区；引用宪法 / 立项书两层模型） | ✅ |
| `.gitignore` | `__pycache__/` / `*.pyc` 等 | ✅ |
| **workspace manifest**（[D-01]） | `donkey_workspace.toml` 或 `.donkey/manifest.json` 含 schema 版本号（[D-03]） | ✅ |

**宪法 / 立项书自检**：

- §N-01：**不**生成 `agent.py` / `main.py` / 任何 Python 入口
- §2.6：workspace 目录必填项齐全；显式排除（`middleware/` / `connectors/` / `sandbox/` 等）**不**出现
- §2.2 路径绝对化：所有相对路径引用以 workspace 绝对路径为唯一根
- §N-05：core 不 import argparse（但**可** import `shutil` / `pathlib` / `tomllib` 等 stdlib）
- §N-12：**不** import langsmith / 不使用 LangSmith 任何形态
- §1.5.5：init 模板不引入 `ShellToolMiddleware` / `FilesystemMiddleware` / `SubAgentMiddleware` / `RubricMiddleware` / `SkillsMiddleware` / `MemoryMiddleware`（任何 deepagents 包）
- §4.6.2：`secret_key` 占位标识为"高敏感"

**Speckit 闭环**：写完后能跑 `python -m core.cli init /tmp/test-ws`，产生完整 workspace 目录树。

---

### phase 4 — `feature001_phase004_init_idempotent.md`（F001 Phase B）

**目标**：交付 `donkey init` 的幂等性 / `--force` / 错误脱敏 / e2e 联调。**F001 收尾**。

**大致内容**：

| 功能 | 行为 |
|---|---|
| 幂等校验 | 重复 `donkey init <已存在>` 不报错；返回 `InitResult(skipped_files=[...])`，已存在文件被跳过 |
| `--force` 标志 | `--force` 时覆盖已存在文件 + workspace manifest schema 版本号升级时**强制迁移**（[D-03]） |
| 错误脱敏 | `PermissionError` / `InvalidPathError` 抛出时**不**打印 `provider.toml.secret_key` 明文；异常消息走脱敏通道 |
| N-06 自检 | init 失败时**不**留下半成品 workspace（事务回滚：失败时清理已写入文件）；N-06 镜像条款——load 失败不改 workspace，init 失败不留半成品 |
| N-07 自检 | 跳过 init 直接跑 load（用户场景）：init API 不假设存在，phase 4 与 F002 load 联调验证 |
| e2e 联调 | (a) `donkey init /tmp/test-ws` + 验证目录树完整；(c) `family/main --force` 验证幂等；(b) init 后 `donkey load` 通过（phase 5-6 留 stub） |
| 单测完善 | 边界用例：路径权限拒绝 / 路径不存在 / workspace 已存在 / `--force` / schema 版本不匹配 |
| 文档 | README 更新（init 子命令说明）；CLI 子命令清单（§附录 D-5） |

**宪法 / 立项书自检**：

- §N-06：init 失败不留半成品（事务回滚）
- §3.5 数据安全分级：异常脱敏；`secret_key` 不外泄
- §4.6 验收 AC-3：`donkey init` 幂等——重复执行不破坏已存在文件（除非 `--force`）
- §4.6 验收 AC-4：换 workspace 后模型/工具/Skills/提示词随之切换——init 模板必须确保 4 类材料齐全
- §5.5.2 段位表：donkey init 段位 `1-10` 11 码值映射在 phase 4 完成（具体码值在 phase 4 spec 内详细讨论，**不**在 README 展开）
- §N-12：error message 不触发 LangSmith tracing

**Speckit 闭环**：F001 v0.1.0-alpha 完成；进入 F002 `donkey load`（phase 5）。

---

## 6. F002 各 phase 文件详细内容（占位骨架，待 F001 完成后细化）

> F002 = `donkey load <PATH>` 子命令；core API = `load_workspace(path) -> LoadResult`。
> 立项书依据：§5.5.3（9 项检查清单）+ §3.1.2（业务流程图）+ §5.5.2（exit code 段位表 11-20）。
> **当前为占位骨架**——F001 完成后由 Maintainer 手动细化每个 phase 的"大致内容"表格。

### phase 5 — `feature002_phase005_load_static_check_skeleton.md`（F002 Phase A）

**目标**：交付静态检查 4 项 + exit code 11-20 段位预留 + 单测骨架。

**大致内容**（占位）：

- 检查项 1-4（立项书 §5.5.3）：`provider.toml` TOML 语法 + `mcp/mcp.json` JSON 语法 + `skills/*/SKILL.md` YAML frontmatter + `instruction.md` 存在性
- API 签名：`load_workspace(path) -> LoadResult`
- `LoadResult(status: Literal["ok", "warning", "error"], errors: list[LoadError], warnings: list[LoadWarning], exit_code: int)`
- Exit code 段位预留：11-20（§5.5.2 + 宪法 §4.4）
- 单测骨架：仅验证 API 可 import + 段位枚举完整

**宪法自检**：§N-06 load 失败不改 workspace；§N-07 load 不依赖 init；§N-08 段位 11-20 严格不与 init（1-10）重叠。

### phase 7 — `feature002_phase006_load_dynamic_check_full.md`（F002 Phase B）

**目标**：交付动态检查 5 项 + 9 项 hard error 全实现 + 多错误优先级 + warning 处理。

**大致内容**（占位）：

- 检查项 5-9（§5.5.3）：模型连通性 ping + sqlite3 schema 健康 + tools/*.py `@tool` 自动发现 + skills loader 可加载 + MCPAdapter 拉起 server
- Exit code 段位 11-19 码值映射（9 项 hard error 各占 1 码值，20 余留冗余）
- 多错误优先级规则：按 §5.5.3 检查清单顺序逐项执行，遇到第一个 hard error 立即返回，**不**累积多错误码
- warning 不计入失败：`provider.toml.secret_key` 缺失但 `LLM_API_KEY` 已设 → warning 不触发 non-zero exit
- e2e 联调：与 F001 init（phase 4）联调——init → load 全绿

**宪法自检**：§N-06 load 失败不改 workspace；§3.5 数据安全分级——异常脱敏（`secret_key` 入 stdout 时遮蔽）。

---

## 8. F003 各 phase 文件详细内容（占位骨架）

> F003 = `donkey session <PATH>` 子命令；core API = `list_sessions` / `new_session` / `remove_session` / `import_session`。
> 立项书依据：§5.5.4 + §5.5.4.1（标题总结机制）+ 宪法 N-09 / N-10。

### phase 6 — `feature003_phase007_session_list_new.md`（F003 Phase A）

**目标**：交付 `list_sessions` + `new_session` 占位 + sqlite3 schema 健康 + exit code 21-30 段位预留。

**大致内容**（占位）：

- API 签名：`list_sessions(path) -> list[SessionMeta]` + `new_session(path, first_prompt: str | None = None, title: str \| None = None) -> SessionMeta`
- `SessionMeta(thread_id, title)`——thread_id 内部引用；title 默认"无标题会话"
- Exit code 段位预留：21-30（§5.5.2 + 宪法 §4.4）
- 单测骨架

**宪法自检**：§N-09 session 对外标识是 title，thread_id 不外露；§N-05 core 不 import argparse。

### phase 8 — `feature003_phase008_session_remove_import_title.md`（F003 Phase B）

**目标**：交付 `remove_session` + `import_session` + `core.api.new_session` 内部标题总结机制。

**大致内容**（占位）：

- `remove_session(path, title_or_id)`：按 title 定位 thread_id，物理删除 `checkpoint.sqlite3` 中该 thread 全部 checkpoint（不可恢复）
- `import_session(path, from_sqlite_path)`：从外部 sqlite 文件导入历史会话（v1 留接口；§5.5.4 落地列入 v1.x）
- **`new_session` 内部标题总结**（§5.5.4.1 + 宪法 N-10）：
  - 用户显式传 `title` → 用 title（≤ 20 字截断）
  - 用户传 `first_prompt` → 调 `init_chat_model` 总结 ≤ 20 字
  - 失败 / 超时 / 空返回 → 回写"无标题会话"
  - 都不传 → 默认"无标题会话"
  - **必须**在 `core.api.new_session` 内部实现，**严禁** `before_agent` 中间件，**不**进 LangGraph 图，**不**新增节点，**不**触发 §1.5.2 的 `x+1`
- e2e 联调：F001 init → F002 load → F003 session list/new/remove 全跑通

**宪法自检**：§N-10 严守"图外实现"——`new_session` 标题总结**严禁**进 Agent Loop 图；§N-12 不触发 LangSmith。

---

## 9. F004 各 phase 文件详细内容（占位骨架）

> F004 = `donkey run <PATH>` 子命令；core API = `run_session(path, session_id)`。
> 立项书依据：§4.3（模块划分）+ §4.4.1（Agent Loop 状态机）+ §4.4.2（v1 主图节点清单 10 个）+ 宪法 §2.7（中间件录用清单 10 项 / 禁用清单 11 项）。

### phase 9 — `feature004_phase009_run_graph_skeleton.md`（F004 Phase A）

**目标**：交付 LangGraph 主图骨架 + 10 项 v1 中间件挂载 + SqliteSaver 接入 + 各 loader 集成。

**大致内容**（占位）：

- 主图 State schema（§4.4.1）+ Edges + 4 基线节点（`__start__` / `model` / `tools` / `__end__`）
- 10 项 v1 中间件挂载（宪法 §2.7.1）：
  - wrap-style（0 节点）：ToolError / ToolRetry / ModelRetry / LLMToolSelector / ContextEditing
  - node-style（6 节点）：Summarization(1) + ModelCallLimit(2) + PII(2) + TodoList(1)
  - 无 hook（仅工具）：FilesystemFileSearchMiddleware
- SqliteSaver 接入：`memory/checkpoint.sqlite3`
- 编译验证：`create_agent(...).get_graph().nodes.keys()` 含 10 节点（§4.4.2 清单）
- 集成 provider loader / tools loader / mcp loader / skills loader
- Exit code 段位预留：31-100（§5.5.2 + 宪法 §4.4，7 个子段位：tools / Skills / mcp / Saver / Store / middleware / Agent Loop）

**宪法自检**：§N-12 不挂 LangSmith；§1.5.5 显式排除 11 项中间件（FilesystemMiddleware / SubAgentMiddleware / RubricMiddleware / SkillsMiddleware / MemoryMiddleware 等）绝不挂载；§N-02 不挂 subagent。

### phase 10 — `feature004_phase010_run_agent_loop.md`（F004 Phase B）

**目标**：交付 Skills 三层加载完整集成 + MCP 真实调用 + Agent Loop 完整联调 + 24h 长稳测试。

**大致内容**（占位）：

- Skills loader 三层模型集成（§1.2.4）：
  - Level 1：`loader.py` 扫描 `skills/*/SKILL.md` frontmatter → 自动注册 `load_skill_<name>` `@tool`
  - Level 2：`load_skill_<name>` 工具返回 SKILL.md 主体 Markdown + Level 3 路径清单
  - Level 3：模型用 `tools/filesystem.py` / `FilesystemFileSearchMiddleware` / `tools/commandline.py` / `tools/webfetch.py` 读取
- per-skill tool 命名规则：`load_skill_<slugify(name)>`（§2.4 + §3.4）
- MCP server 真实调用：stdin/stdout / http 两种 transport（§2.1）
- 24h 长稳测试：核心 LangGraph 图 24h 持续运行无未捕获异常（§4.6 验收 + §9.3）
- 迁移验收用例：workspace zip → 解压 → 任意路径 → `donkey run` 无路径相关错误（§AC-2）

**宪法自检**：§2.4 Skills 三层渐进披露；§2.5 工具与中间件职责正交；§N-12 不触发 LangSmith。

---

## 10. F005 各 phase 文件详细内容（占位骨架）

> F005 = `donkey web` 客户端；复用 F001-F004 核心 API；v1 主战场 ~200 人时。
> 立项书依据：§5.5.6（客户端开发顺序）+ 宪法 N-6（N-11）+ §2.8（客户端三端对等原则）。

### phase 11 — `feature005_phase011_web_skeleton.md`（F005 Phase A）

**目标**：交付 Web 客户端主体——前端框架 + UI + 事件流 + Markdown 高亮 + 会话管理。

**大致内容**（占位）：

- 前端框架选型（React / Vue / Svelte 中选 1；选型记录在 ADR）
- UI 设计：会话列表 + 当前会话 + 输入框 + 工具调用可视化 + Skill 加载可视化
- WebSocket / SSE 事件流：实时推送 Agent Loop 节点执行 + 工具调用 + 模型流式输出
- Markdown / 代码高亮：模型输出 / 工具结果 / Skill 主体渲染
- 会话管理 UI：list / new / remove 按钮 + 标题展示（§N-09）
- 调 `core.api` 全套接口：`init_workspace` / `load_workspace` / `list_sessions` / `new_session` / `remove_session` / `import_session` / `run_session`
- 全部组件完成度 ≥ 80%；主路径 e2e 通过（§5.4）

**宪法自检**：§N-04 web 不直接 import langchain / langgraph / sqlite3（必须通过 `core.api` 库 API）；§N-11 三端对等；§N-12 不触发 LangSmith。

### phase 12 — `feature005_phase012_web_e2e.md`（F005 Phase B）

**目标**：交付 Web e2e 联调 + 三端通用 pytest 主题。

**大致内容**（占位）：

- Web e2e 套件：playwright / pytest
- CLI / Web 共享 pytest 主题（启动方式不同）：`tests/e2e/test_*.py` 既支持 CLI 跑又支持 Web 跑
- 文档同步：README + Web 用户手册

**宪法自检**：§N-11 三端对等——每个 e2e 用例三端都跑通；§N-12 不触发 LangSmith。

---

## 11. F006 各 phase 文件详细内容（占位骨架）

> F006 = `donkey gui` 客户端；GUI = Electron 包壳（100% 复用 Web 渲染层）；~40 人时。
> 立项书依据：§5.5.6 GUI 选型决策 + 宪法 N-6（N-11）+ §2.8。

### phase 13 — `feature006_phase013_gui_electron.md`（F006 Phase A）

**目标**：交付 Electron 主进程 + 渲染层 100% 复用 Web build + 三端打包脚本。

**大致内容**（占位）：

- Electron 主进程：窗口管理 + IPC 桥接 + 原生 API 暴露（菜单栏 / 文件对话框 / 通知 / 剪贴板）
- 渲染层：100% 复用 Web build（package.json + Web build pipeline 共用）
- 三端打包脚本：macOS dmg / Windows nsis / Linux AppImage
- GUI 启动验证：Electron 壳启动 + 渲染层与 Web 一致（§5.5.6 测试策略）
- GUI 不重复业务测试——靠 Web 测试覆盖

**宪法自检**：§N-04 GUI Electron 主进程**不** import 业务库——只做窗口管理 / IPC 桥接 / 原生 API 暴露；§N-11 三端对等；§N-12 不触发 LangSmith；§5.5.6 GUI 必须等 Web 完成才启动。

---

## 12. 约束自检清单（每个 phase 文件每步都对照）

每个 phase 文件在 `/speckit.specify` 起草前 + `/speckit.analyse` 后都必须自检：

| 编号 | 自检项 | 来源 |
|---|---|---|
| §N-01 | workspace 内**不**出现 `agent.py` / `main.py` / Python 入口 | 宪法 §1.2 + 立项书 §3.4 |
| §N-02 | **不**引入 subagent / 子智能体相关目录或字段 | 宪法 §1.2 + 立项书 §1.2.3 |
| §N-03 | `core` 不 import 任何 client（cli / web / gui） | 宪法 §1.2 + 立项书 §4.1.1 |
| §N-04 | `cli` / `web` / `gui` 不直接 import `langchain` / `langgraph` / `sqlite3` | 宪法 §1.2 + 立项书 §5.5.6 |
| §N-05 | `core` 不 import `argparse` / `sys.argv` / `click` / `typer` | 宪法 §1.2 + 立项书 §4.1.1 |
| §N-06 | `donkey load` 失败**不**改 workspace（init 失败不留半成品为镜像条款） | 宪法 §1.2 + 立项书附录 F |
| §N-07 | `donkey load` 不依赖 init（用户可跳过 init 直接跑 load） | 宪法 §1.2 + 立项书附录 F |
| §N-08 | exit code 段位严格不重叠（init 1-10 / load 11-20 / session 21-30 / run 31-100） | 宪法 §4.4 + 立项书 §5.5.2 |
| §N-09 | session 对外标识是 title，thread_id 仅内部引用 | 宪法 §1.2 + 立项书 §5.5.4 |
| §N-10 | `new_session` 标题总结**严**禁 `before_agent` 中间件（必须在 core.api 内） | 宪法 §1.2 + 立项书 §5.5.4.1 |
| §N-11 | v1 必须同时交付 cli / web / gui 三种客户端 | 宪法 §1.2 + 立项书 §1.5.3 |
| §N-12 | **不**使用 LangSmith 任何形态（包 / Cloud / Studio / extras / 环境变量 / import 路径） | 宪法 §1.2 + 立项书 §1.5.5 + §2.1 |
| §2.1 | 两层模型：材料层 vs 引擎层边界 | 宪法 §2.1 + 立项书 §1.2.3 |
| §2.2 | 路径绝对化原则：workspace 相对路径以 workspace 绝对路径为唯一根 | 宪法 §2.2 + 立项书 §1.2.2 |
| §2.3 | workspace 原子性：一个 workspace = 一个 Agent | 宪法 §2.3 + [D-01] |
| §2.4 | Skills 三层渐进披露：Level 1 自动注册 per-skill `@tool` | 宪法 §2.4 + 立项书 §1.2.4 |
| §2.5 | 内置 `@tool` 与中间件职责正交（filesystem / commandline / webfetch 三件套 vs FilesystemFileSearchMiddleware） | 宪法 §2.5 + 立项书 §1.2.4 |
| §2.6 | workspace 目录必填项齐全 + 显式排除项不出现 | 宪法 §2.6 + 立项书 §4.6.1 |
| §2.7 | 中间件录用 10 项 / 禁用 11 项严格不挂载 | 宪法 §2.7 + 立项书 §1.5.4 + §1.5.5 |
| §2.8 | 客户端三端对等（cli / web / gui 都覆盖同组子命令集） | 宪法 §2.8 + 立项书 §5.5.6 |
| §2.9 | Skills 自研 + 禁止 deepagents 依赖 | 宪法 §2.9 + 立项书 §1.2.4 |
| §3.1 | 技术栈与依赖硬约束（Python 3.11+ / LangChain 1.x / LangGraph / TOML / pytest 等） | 宪法 §3.1 + 立项书 §4.2.1 |
| §3.2 | 永不使用清单（LangSmith / deepagents / ShellToolMiddleware / subagent / Python 入口） | 宪法 §3.2 |
| §3.3 | 长期记忆硬约束（v1-v2 InMemoryStore / v3 自研 SqliteStore） | 宪法 §3.3 + 立项书 §4.10 TD-02 |
| §3.4 | Skills 三层加载硬约束（per-skill tool 命名 / init 自动生成三件套） | 宪法 §3.4 + 立项书 §1.2.4 |
| §3.5 | 数据安全分级（`secret_key` 脱敏 / 不上传 workspace） | 宪法 §3.5 + 立项书 §4.8 |
| §4.5 | 版本号规则（`x+1` 仅 LangGraph State / Edge / 节点数变化时） | 宪法 §4.5 + 立项书 §1.5.2 |
| §4.6 | 验收标准（AC-1 ~ AC-5 + load 9 项检查覆盖率 + 中间件录用率 + 24h 长稳） | 宪法 §4.6 + 立项书 §3.2.3 + §3.5 + §9.3 |

> **约束自检来源**：立项书附录 F + 宪法 §1.2 N-01 ~ N-12 + §2 核心设计原则 + §3 不可妥协约束 + §4 开发流程。
> **任意一条违例 = spec 缺陷 / plan 缺陷 / code 缺陷**——必须修订后才能进入下一阶段。

---

## 13. 当前进度

| Phase | 文件名 | 状态 | 备注 |
|---|---|---|---|
| phase 1 | `feature001_phase001_builtin_tools.md` | ⏳ 待编写 | F001 Phase A 第 1 个 phase，三大内置工具模板 |
| phase 2 | `feature001_phase002_init_api_skeleton.md` | ⏳ 待编写 | F001 Phase A 第 2 个 phase，API 签名 + 占位 |
| phase 3 | `feature001_phase003_init_template_generation.md` | ⏳ 待编写 | F001 Phase B 第 1 个 phase，模板生成 |
| phase 4 | `feature001_phase004_init_idempotent.md` | ⏳ 待编写 | F001 Phase B 第 2 个 phase，幂等 + --force + 错误脱敏 |
| phase 5~13 | (F002~F006 占位骨架) | ⏳ 待 F001 完成后细化 | 当前 README 仅占位 |

---

**Version**: v0.1 草稿 | **Last Amended**: 2026-10-14 | **Maintainer**: yangjiacheng