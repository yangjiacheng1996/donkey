# Phase 0 研究记录 —— F001-P2 `template_skeleton`

**Phase**: F001-P2（`donkey init` 模板骨架幂等生成）
**上游**：[spec.md](spec.md)（含澄清会话共 **27 项**决策：13 项 AI 推断 + 5 项 Maintainer 亲自裁决 + 6 项定向澄清修订裁决 + 3 项三文档交叉复核后定点修订）
**研究日期**: 2026-10-23
**方法**: 源码检视（wheel 解包）+ **可复现实验**（本机 `.venv` 实跑）+ 仓库内既有调研文档比对

> 本文件只回答"怎么做"（HOW）与"为什么这么做"，**不**回答"做什么"（WHAT）—— 后者由 spec 的 FR / SC 锁定。
> 所有实验均在本机 `/home/ctyun/workspace/github/donkey/.venv`（Python 3.12.3）实跑，命令与输出逐条留证。

---

## R-01 · 上游 saver 包的身份、导入路径与版本约束

**决策**：引入 `langgraph-checkpoint-sqlite` 作为 donkey **唯一**的运行期依赖；导入路径为 `langgraph.checkpoint.sqlite`（**不是** `langgraph_checkpoint_sqlite`）；版本约束 `>=3.1,<4`。

**依据（实验）**：

1. wheel 解包（`langgraph_checkpoint_sqlite-3.1.2-py3-none-any.whl`）显示包内实际模块路径为
   `langgraph/checkpoint/sqlite/__init__.py`，顶层导出类 `SqliteSaver`；
2. `SqliteSaver.__init__(self, conn: sqlite3.Connection, *, serde=None)` —— 接收一个**已建立的** `sqlite3.Connection`；
3. `setup()` 签名实测为 **`def setup(self) -> None`**（实例方法），内部走 `self.conn.executescript(...)`；
   → 与 `harness/report/sessions_sqlite表结构一览.md` §8 Q1 的结论一致：写成 `SqliteSaver.setup(conn)` 会把 `conn` 误绑到 `self` 上并抛 `AttributeError`；
4. 依赖链（读 wheel METADATA）：

   | 层级 | 包 | 约束 |
   |---|---|---|
   | 直接 | `langgraph-checkpoint-sqlite` | `>=3.1,<4`（实测 3.1.2） |
   | 传递 | `langgraph-checkpoint` | `>=4.3.0,<5.0.0`（实测 4.3.0） |
   | 传递 | `langchain-core` | `>=0.2.38`（实测 1.7.0） |
   | 传递 | `aiosqlite` | `>=0.20` |
   | 传递 | `sqlite-vec` | `>=0.1.6` |

**版本陷阱（实测）**：本机用户级 site-packages 里存在 `langgraph-checkpoint-sqlite 3.1.1` + `langgraph-checkpoint 4.2.0` 的组合，
二者**不兼容**——导入即抛 `ImportError: cannot import name 'writes_sort_key' from 'langgraph.checkpoint.base'`。
仓库 `.venv` 则是 `langgraph-checkpoint 4.3.0`（配套可用）。**故 `pyproject.toml` 的版本下界 MUST 取 `>=3.1`，且安装时 MUST 让 pip 解析出 `langgraph-checkpoint>=4.3.0`**。

**替代方案与否决理由**：

| 替代方案 | 否决理由 |
|---|---|
| 手写上游两张表的建表 SQL | 用户已裁决（spec 澄清决策 1）：donkey MUST NOT 承担结构漂移风险；上游改列名即 break |
| init 只建自管的 `sessions_metadata`，上游两表留给运行时 | 用户已裁决：违反"init 完就是结构完好的空库"目标（spec US14 / SC-006） |

---

## R-02 · N-12 门禁：导入上游 saver 会不会把 LangSmith 拖进进程

**决策**：**不构成违例**。donkey 引入 `langgraph-checkpoint-sqlite` 后，**任何**代码路径 MUST NOT import `langsmith` 或其子包；实测导入上游 saver **不会**把 langsmith 拉进进程。

**依据（实验）**：

```
$ .venv/bin/python -c "
import sys
before=set(sys.modules)
from langgraph.checkpoint.sqlite import SqliteSaver
after=set(sys.modules)
print(sorted(m for m in after-before if m.startswith('langsmith')))
print('langsmith' in sys.modules)"
→ []
→ False
```

导入共新增 **471** 个模块，其中 langsmith 相关 **0** 个；`langchain_core.runnables`（上游 saver 的唯一 langchain 触点）在 langchain-core 1.6+ 走 `_import_utils` 惰性导入，追踪器 / langsmith 机制**不在导入期加载**。

**但必须登记的事实**：`langchain-core` 把 `langsmith>=0.14.9,<1.0.0` 列为**硬依赖**（wheel METADATA 实测），
因此 `pip install donkey` 会把 langsmith **安装到磁盘**。N-12 的约束对象是"**使用** LangSmith 相关代码 / 直接 import langsmith.*"，
不是"磁盘上不存在 langsmith 包"—— 故不构成违例。**落地要求**：

- donkey 的任何 `.py` MUST NOT 出现 `import langsmith` / `from langsmith...` / `langsmith.`（quickstart §4 有 grep 自检）；
- donkey MUST NOT 设置任何 `LANGSMITH_*` 环境变量；
- 交付物中 MUST NOT 出现任何指向 LangSmith Cloud / Studio / Tracing 的配置项。

**替代方案与否决理由**：

| 替代方案 | 否决理由 |
|---|---|
| 强行剥离 langsmith（pip install --no-deps + 手工补依赖） | 会破坏 langchain-core 的导入契约，且升级即碎；且 N-12 约束的是"使用"而非"安装" |
| 回到手写建表 SQL | 用户已裁决（R-01） |

---

## R-03 · WAL 侧车文件：`-wal` / `-shm` 何时存在，`--force` 为何要连带删除

**决策**：`--force` 重建 sqlite3 模板时**连带删除**同名 `-wal` / `-shm`（spec FR-011 / 澄清决策 3）。

**依据（实验）**：

1. 上游 `setup()` 的 `executescript` **第一条语句就是 `PRAGMA journal_mode=WAL;`** → 库被置于 WAL 模式；
2. **连接存活期间**目录内容实测为 `['sessions.sqlite3', 'sessions.sqlite3-shm', 'sessions.sqlite3-wal']`；
3. **正常关闭连接后** SQLite 自动 checkpoint 并清理 → 目录只剩 `['sessions.sqlite3']`；
   → 故正常运行路径下 `donkey init` **不会**留下侧车；侧车只在 (a) 进程被强杀 / (b) 其它进程正持有该库时残留；
4. **陈旧 WAL 的实际危害（实验）**：构造一个陈旧 `-wal` 放在新建主库旁再重建，读取 `sessions_metadata` 得 **行数 0**（表结构完好）——
   SQLite 校验 WAL 头部盐值，与新库不匹配即**安全忽略**。

**结论（重要，避免实现者建立错误心智模型）**：残留 WAL **不会**把旧事务内容回放进新库。
连带删除 `-wal` / `-shm` 是**防御性**措施（消除极小概率的回放风险 + 不留垃圾文件），**不是**"不删就会坏"的必要条件。
实现 MUST 按 spec 删除（行为确定、可测试），但**注释与错误信息 MUST NOT 声称"不删必然导致数据污染"**。

**替代方案与否决理由**：

| 替代方案 | 否决理由 |
|---|---|
| 只删主库，留侧车 | 用户已裁决；且会留下孤儿文件，`.gitignore` 虽已覆盖，但用户手工清理仍困惑 |
| 非 `--force` 时也清理侧车 | 违反 FR-011「非强制模式 MUST NOT 触碰它们」——侧车是活跃库的一部分，误删会丢未 checkpoint 的事务 |

---

## R-04 · 上游 `setup()` 的幂等性与内建迁移

**决策**：直接调用 `SqliteSaver(conn).setup()`，donkey 不自写任何上游表的 DDL。

**依据（源码检视 + 实验）**：

1. `setup()` 内以 `CREATE TABLE IF NOT EXISTS` 建 `checkpoints` / `writes` → 重复调用安全；
2. `setup()` 额外执行一次 `ALTER TABLE writes ADD COLUMN task_path TEXT NOT NULL DEFAULT ''`（上游为旧库补列），
   捕获 `sqlite3.OperationalError`：**"duplicate column name" 吞掉**，"readonly database" 走 `_has_task_path = False` 降级分支，其余**重新抛出**；
3. `setup()` 有 `self.is_setup` 实例级短路；每个新实例的 `is_setup` 初值为 `False` → **每次新建 saver 实例都要调一次** `setup()`；
4. 实验：同一连接连调 `setup()` 两次，表集合不变（`checkpoints` / `sessions_metadata` / `writes`）。

**落地要求**：`build_sessions_sqlite` MUST 新建 `SqliteSaver` 实例并调**实例** `setup()`；MUST NOT 缓存 saver 实例跨连接复用。

---

## R-05 · `sessions_metadata` 的字段与索引落地形态

**决策**：donkey 自管的 `sessions_metadata` 表 + 2 个索引，按 `harness/report/sessions_sqlite表结构一览.md` §2.2 的 DDL 逐字建。

**依据（实验 + 文档）**：按 §2.2 的 6 字段 DDL + 2 个 `CREATE INDEX IF NOT EXISTS` 执行后，实测 `sqlite_master`：

```
表:   ['checkpoints', 'sessions_metadata', 'writes']
索引: ['idx_sessions_metadata_title', 'idx_sessions_metadata_updated_at',
       'sqlite_autoindex_checkpoints_1', 'sqlite_autoindex_sessions_metadata_1',
       'sqlite_autoindex_writes_1']
```

**测试注意**：`sqlite_autoindex_*` 是 PRIMARY KEY 自动索引，`tbl_name` 亦为 `sessions_metadata`。
spec e2e 场景 14 用的是 `in` 断言（非集合相等），故自动索引**不干扰**；但若后续有人把断言改成集合相等，会误判 —— 已在 `contracts/` 中登记该提醒。

**字段顺序不敏感**（§8 Q2）：SQLite 按列名匹配，`PRAGMA table_info` 顺序与 INSERT 不一致不影响存储；字段名 + 类型严格即可。

---

## R-06 · 渲染顺序无关性（清单条目顺序 ≠ 依赖顺序）

**决策**：写任何文件前 MUST 先确保其**父目录**存在（spec FR-012）；目录条目 MUST 显式创建但不计入 `files_created` / `files_skipped`（spec FR-017）。

**依据（事实核对）**：spec 的 46 条清单把 `providers/default.toml`（第 2 条）、`mcp/mcp.json`（第 3 条）、`skills/example/SKILL.md`（第 4 条）
排在对应目录条目（第 38 ~ 43 条）**之前**。若严格按序渲染，写第一个文件时 `providers/` 尚不存在 → 必然失败。
故渲染 MUST 对每条目标路径执行"含父目录"创建，且该创建 MUST 限定在 workspace 根之下。

**替代方案与否决理由**：

| 替代方案 | 否决理由 |
|---|---|
| 调整清单顺序（目录条目提前） | 用户已裁决"追加不得修改 P1 已有 3 条"；且顺序依赖是脆弱契约——未来追加条目仍可能踩坑 |
| 渲染前先扫一遍建所有目录 | 等价方案；实现上采"写文件时按需确保父目录"，更少一次遍历 |

---

## R-07 · 覆盖 F001-P1 的 3 个占位源文件

**决策**：F001-P2 MUST 覆盖 P1 建档的 3 个 `.txt` 源文件（spec FR-042）。

**依据（现状核对）**：P1 遗留内容与本 Phase 契约冲突 ——

| 源文件 | P1 占位现状 | 本 Phase 要求 |
|---|---|---|
| `templates/instruction.md.txt` | `# {{workspace_name}}` + `{{workspace_path}}` + "待 F001-P2 填充" | 按 spec §4.7.1 正文（角色 / 风格 / 限制三小节） |
| `templates/providers/default.toml.txt` | `default_provider = "{{default_provider}}"` / `default_model = "{{default_model}}"` | 按 spec §4.7.2.1（两个字段出厂为空串，**无**占位符） |
| `templates/mcp/mcp.json.txt` | 已与目标一致 | 不变（仍按 spec 覆盖以保证一致性） |

**占位符口径**：`{{ workspace_name }}`（带空格）与 `{{workspace_name}}`（无空格）两种写法都要识别；未识别占位符原样保留（spec FR-015）。
`{{workspace_path}}` 在 P2 的正文里**不再出现** —— P1 的占位源被整体覆盖，不做增量修补。

---

## R-08 · 计数口径（`templates_loaded` / `files_created` / `files_skipped`）

**决策**：`templates_loaded` = 模板清单的**原始条目总数**（46；含目录条目、含重复条目）；`files_created` / `files_skipped` = **文件型条目**数（40 = 37 文本 + 3 sqlite3；目录条目不计入），按**唯一路径**计一次（spec FR-017 / FR-026）。

**依据**：`InitResult` 的字段语义在 F001-P1 已冻结为"本次新建**文件**数 / 已存在而跳过的**文件**数"（P1 spec FR-006），目录不是文件。
F001-P3 追加 8 条后累计 54 条，其中同样含目录条目 → 口径跨 Phase 一致。

**倒推校验**：全新创建时 `files_created` = **40**、`files_skipped` = 0、`templates_loaded` = **46**；
二次 init（无 `--force`）时 `files_created` = 0、`files_skipped` = 40、`templates_loaded` = 46。

---

## R-09 · 26 份 provider stub 的机械抄录清单

**决策**：按 `harness/report/大模型toml参数设计.md` §8.3.3 ~ §8.3.28 逐字抄录（spec FR-046）。

**依据（脚本核对全文小节与模型条目数）**：§8.3 共 **29** 个编号小节（`####` 级 3 个 —— `providers/default.toml` / provider 文件模板总览 / 汇总速查表；`#####` 级 provider 子节 **26** 个，对应 §8.3.3 ~ §8.3.28），模型条目合计 **51** 条，与 spec SC-015 的 "51 条" 硬指标一致。

| provider | 模型数 | provider | 模型数 | provider | 模型数 |
|---|---|---|---|---|---|
| `openai` | 3 | `kimi` | 2 | `bedrock` | 2 |
| `anthropic` | 4 | `zhipu` | 2 | `groq` | 2 |
| `google` | 2 | `minimax` | 3 | `fireworks` | 1 |
| `ollama` | 2 | `tencent` | 1 | `together` | 1 |
| `xai` | 2 | `xiaomi` | 1 | `cohere` | 1 |
| `mistral` | 2 | `stepfun` | 2 | `perplexity` | 1 |
| `qwen` | 4 | `openai-compatible` | 1 | `databricks` | 1 |
| `deepseek` | 2 | `meta` | 2 | `cerebras` | 1 |
| `doubao` | 2 | `openrouter` | 4 | **合计** | **51** |

**抄录时的三条硬约束**：

1. `bedrock.toml` MUST NOT 含通用 `api_key` —— 改用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` / `aws_session_token` 四字段（§8.2 / spec FR-047）；
2. 全部 26 份 `enabled = false`；凭据字段出厂为空串；MUST NOT 出现 `REPLACE_ME` 类占位符（§8.3 前言 / spec FR-046）；
3. `providers/default.toml` 是**保留名**，MUST NOT 被当作 provider 名；其两个字段出厂为空串。

**机械抄录的落地方式**：由脚本从 §8.3 的 fenced code block 逐块抽取（含 `##### 8.3.x` 标题与 ```toml 围栏），写入 `templates/providers/<id>.toml.txt`；
MUST NOT 手工誊写（誊写必漏注释行与空行）。脚本本身属实现阶段产物（MUST NOT 进仓库），人工复核 diff 后再提交。

---

## R-10 · 工作区清单的写入入口

**决策**：初始化流程调用 `write_workspace_manifest(workspace_path, name, force)`（spec FR-027 步骤 ⑤）；`ensure_workspace_manifest` 作为等价便捷封装保留并实现同样的"存在即不覆盖"语义（spec FR-023）。

**依据**：提示词 §4.1 的伪码调用 `write_workspace_manifest`，§4.2 的设计意图段说 `ensure_workspace_manifest` —— 二者语义等价：
`write_workspace_manifest` 自身第 2 步就是"不传 force 且已存在 → 不覆盖、返回既有内容"。
故选 `write_workspace_manifest` 作为流程入口（少一层间接），便捷封装供 F002 / F003 复用。

**判定顺序（唯一实现，二者共用）**：`write_workspace_manifest` 的判定顺序是 ——
**带 force → 直接覆盖（不读旧文件）**；不带 force 且已存在 → 先读，解析失败 → exit 3，不覆盖、返回既有内容；不存在 → 无条件创建。
`ensure_workspace_manifest` MUST 委托同一判定顺序（MUST NOT 先于 force 判定去读旧文件），二者语义因此**严格等价** ——
包括"坏 JSON + force → 覆盖为合法内容"与"坏 JSON + 不带 force → exit 3"两个组合。
（关键点：**force 分支不读旧文件** —— 若 `ensure` 按字面"先读"，则"坏 JSON + force"会读失败抛 exit 3，与 `write` 的覆盖成功行为不一致。）

**边界澄清**（spec Assumptions 已登记）：工作区清单**不在** 46 条清单内，却是 `--force` 唯一会覆盖的"清单外"路径 ——
FR-013 约束的是**渲染**（`render_templates`），工作区清单写入是独立步骤，二者不冲突。

---

## R-11 · 强制清空提示行的输出形态

**决策**：提示行输出到 **stdout**，与通用摘要**分行**；带 `--force` 时**恒定输出**（即使此前不存在 sqlite3 文件）；不带 `--force` 时**不出现**（spec FR-068 / SC-019）。

**依据**：该提示属**成功路径**提示（不是失败信息）→ stdout；F001-P1 已确立"失败信息 → stderr / 成功摘要 → stdout"的口径。
文案 MUST 同时涵盖"已清空 / 已重建"两种情形，否则在"工作区本来就没有记忆库文件"的情形下会输出误导性文案。

**测试形态**：e2e 黑盒场景 8 断言提示行**存在**、场景 6 断言提示行**不出现**（spec FR-059）。

---

## R-12 · 退出码 3 的错误信息「下一步」统一文案

**决策**：模板类失败的错误信息 MUST 含可识别的错误标识 + 一条用户可执行的下一步（spec FR-069 / SC-020）。

**依据**：F001-P1 的 `check_path` / `check_permission` 已用 `_NEXT_STEP` 常量固化该模式（"下一步：请先建目录，或换路径到父目录已存在的目标。"）。
本 Phase MUST 沿用同一模式，为模板类失败定义第二句固定文案，例如：

```
下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。
```

**落地要求**：错误信息 MUST 同时含 (a) 失败的具体环节（清单损坏 / 源缺失 / 写入失败 / sqlite3 构造失败）与 (b) 上述下一步；
MUST NOT 只报异常类别名。

**文案常量落点**：`_NEXT_STEP_TEMPLATE` MUST 放在 `donkey/core/exceptions.py`（与 `TemplateGenerationError` 同模块）。**不得**放在 `donkey/core/workspace/init.py` —— `init.py` 需 import `manifest.py`，而 `manifest.py` / `sqlite3_templates.py` 也需要该文案，常量若在 `init.py` 会形成 `manifest.py → init.py → manifest.py` 的循环 import。
P1 已有的 `_NEXT_STEP`（路径类，位于 `donkey/core/workspace/init.py`）**保持不动** —— 二者语义不同（路径类 vs 模板类），并列而非替换（spec FR-029 禁止改动 P1 已有代码）。

---

## R-13 · 覆盖率度量命令（沿用 F001-P1）

**决策**：覆盖率 MUST 以**独立命令**度量，MUST NOT 写入 pytest 全局 `addopts`。

**依据**：F001-P1 已确立该口径（其 plan G12 / G13）：e2e 黑盒脚本不 import 业务代码，若把 `--cov` 写进全局 `addopts`，
单独跑 e2e 时会把覆盖率拉到 0 而误报失败。

```
pytest tests/unit/ --cov=donkey.core --cov-fail-under=80
```

`pytest-cov` 已在 dev 依赖中（`pyproject.toml` `[project.optional-dependencies].dev`），本 Phase 无需新增。

---

## R-14 · 【范围外观察】上游已自带 SQLite Store —— 影响宪法 D-11 的 v3 路线

**决策**：**不在本 Phase 处理**，仅登记为 Maintainer 决策项。

**事实**：`langgraph-checkpoint-sqlite 3.1.2` 的 wheel 内除 `langgraph/checkpoint/sqlite/` 外，
还含 **`langgraph/store/sqlite/`**（`base.py` + `aio.py` + `__init__.py`）—— 上游已提供 SQLite 版的 Store 实现。

**影响**：宪法 D-11 与 §3.3 记载的"v3 自研 `SqliteStore`（仿照 PostgresStore）"路线，可能被上游现成实现部分或全部替代。
这关系到 v3 的工作量与"自研 vs 复用"的技术选型，属**仓库级 / v3 范围**决策。

**边界**：本 Phase MUST NOT 引入、引用或试验该模块（spec FR-032 明确 `store.sqlite3` v1 仅占位空文件、donkey 本体不读）。
登记于此供 Maintainer 在 v3 启动时评估。

---

## R-15 · 清单条目路径重复的去重口径与计数归属

**决策**：**去重只发生在渲染层**。`load_template_manifest` 返回**未去重的原始条目列表**（`list[dict]`，长度即 FR-026 的 `templates_loaded`）；`render_templates` 作为公开 API，MUST 在内部先按唯一路径去重（同一路径只处理一次，以重复项中**最后出现**的条目为准，其 `format` 与源模板生效），MUST NOT 对同一路径既计 `created` 又计 `skipped`；`files_created` / `files_skipped` 按唯一路径计一次。

**落点（一层）**：只由 `render_templates` 承担去重。`load_template_manifest` **不做**归一化 —— spec FR-001 把其返回类型固定为 `list[dict]`，该类型内没有任何位置能携带"原始（未去重）条目总数"，而 FR-026 要求 `templates_loaded` = 本次**加载**的条目总数（含重复）。**因此 loader MUST NOT 去重**（否则 `templates_loaded` 只能取去重后的长度，与 FR-026 冲突）；去重下沉到 `render_templates` 内部，loader 保持"原始列表"这一单一职责。

**计数归属**：`files_created` / `files_skipped` 按**唯一路径**计一次（MUST NOT 对同一路径既计 created 又计 skipped）；`templates_loaded` = loader 返回的**原始列表长度**（含重复条目）—— 与 R-08 的计数口径一致，两者口径不同但各自有明确依据。
故 `init_workspace_inner` MUST 返回 `manifest_total = len(load_template_manifest())`（原始列表长度），MUST NOT 用去重后列表的长度 —— 与 spec FR-002 / FR-026 同一口径。

**依据**：spec FR-001（返回类型 `list[dict]`）/ FR-002（**渲染** MUST 按唯一路径处理）/ FR-026（`templates_loaded` = 加载的条目总数，含重复）/ 澄清 #24。`format` 省略时 MUST 按 `text` 处理（spec FR-002 / data-model.md §2 "缺省视为 text"），对重复项同样适用（以最后出现者的 `format` 为准）。

---

## R-16 ~ R-18 · 三文档交叉复核后的定点修订

> **来源说明**：以下 3 条**不属于 Phase 0 research 原始产出** —— 它们由 `/speckit.analyze` 对 spec / plan / tasks 三文档做交叉复核后追加（对应 spec 澄清 **#25 ~ #27**，即"三文档交叉复核后修订轮"的 3 条定点修订）。
> 本节为**回填**，内容与 [plan.md](plan.md) 的 R-16 ~ R-18 决策表**逐字一致**（plan 侧为决策落点的权威表述，本节为 research 侧的决策记录）。

### R-16 · 步骤 ⑤ 失败不回滚（spec 澄清 #26）

**决策**：初始化流程步骤 ⑤（写工作区清单）失败 MUST 抛模板生成类错误（退出码 `3`），而步骤 ④ 已落地 / 已重写的模板文件 MUST **保留**（不删除、不还原）；本 Phase **MUST NOT** 实现任何事务回滚机制（无补偿逻辑、无临时目录 + 原子替换、无"失败即清空"）。

**落点**：`core/workspace/init.py`（`init_workspace_inner` 步骤 ⑤）/ `tests/unit/test_template_skeleton.py`（T083 护栏单测）。

### R-17 · 工作区被重命名后保留旧名（spec 澄清 #27）

**决策**：用户把 workspace 目录重命名后再执行**非强制** `donkey init`：非强制模式下已存在文件 MUST 完全不动（FR-008 / FR-020），故工作区清单的 `name` 字段与模板正文**保留重命名前的名称**；命令行报告的名称（路径末段名）与模板正文内的名称**不一致** —— 该不一致 MUST NOT 触发退出码 `3`，亦 MUST NOT 以任何形式宣称二者一致。

**落点**：`core/workspace/manifest.py`（"非强制 → 保留原 `name`"语义，无新增行为）/ `core/workspace/init.py`。本 Phase 以**文档化口径**满足（spec Edge Cases「其它边界」已登记 + SC-014 适用边界已明确），**MUST NOT** 新增任何命令行输出（客户端改动仍限 FR-064 的三项）。

### R-18 · 权限失败 MUST 以注入式构造产生（FR-055 第 10 类的构造方式裁定）

**决策**：特权账号（root / `CAP_DAC_OVERRIDE`）**绕过 DAC 权限检查**，其对 `0o555` 目录的 `access(W_OK)` 与实际写入**均成功** → chmod 只读目录的方案在 root CI 容器中**失效**，FR-055 第 10 类（渲染中途权限失败）会假失败。故该用例 MUST 用 `monkeypatch` / mock 在写入边界注入 `OSError(EACCES)`，MUST NOT 依赖运行账号的特权状态。

**落点**：`tests/unit/test_template_skeleton.py`（`test_render_permission_denied_midway`）。spec Assumptions「特权环境说明」已同步修订。

---

## 研究结论汇总

| # | 决策 | 类别 | 是否有实验证据 |
|---|---|---|---|
| R-01 | 上游包身份 / 导入路径 / 版本约束 | 依赖选型 | ✅ wheel 检视 + 导入实验 |
| R-02 | N-12 门禁：导入上游 saver 不引入 langsmith 模块 | 宪法合规 | ✅ 471 模块逐一核对 |
| R-03 | WAL 侧车：何时存在 / 陈旧 WAL 被安全忽略 | 边界行为 | ✅ 目录快照 + 陈旧 WAL 实验 |
| R-04 | 上游 `setup()` 幂等性与内建迁移 | 实现要点 | ✅ 源码 + 重复调用实验 |
| R-05 | `sessions_metadata` 落地形态与 `sqlite_autoindex` 提醒 | 数据模型 | ✅ sqlite_master 实测 |
| R-06 | 渲染顺序无关性 | 实现要点 | ✅ 清单条目顺序核对 |
| R-07 | 覆盖 P1 的 3 个占位源文件 | 实现要点 | ✅ 现状内容核对 |
| R-08 | 计数口径与倒推校验值 | 数据模型 | ✅ 清单条目分类计数 |
| R-09 | 26 份 stub 的抄录清单与模型条目数 | 机械抄录 | ✅ 脚本核对全文（51 条） |
| R-10 | 工作区清单写入入口 | 实现要点 | ✅ 语义等价性分析 |
| R-11 | 强制清空提示的输出形态 | 交互 | ✅ 与 P1 输出口径对齐 |
| R-12 | 退出码 3 的下一步文案模式 | 交互 | ✅ 与 P1 `_NEXT_STEP` 模式对齐 |
| R-13 | 覆盖率度量命令 | 质量门禁 | ✅ 沿用 P1 已验证口径 |
| R-14 | 上游自带 SQLite Store → v3 路线待评估 | 范围外观察 | ✅ wheel 目录清单 |
| R-15 | 清单路径重复的去重口径与计数归属 | 实现要点 | ✅ spec 澄清 #24 裁决（去重只在 renderer：loader 返回原始列表） |
| R-16 | 步骤 ⑤ 失败**不回滚**（无事务回滚机制） | 边界行为 | ✅ spec 澄清 #26 裁决（三文档交叉复核后定点修订） |
| R-17 | 工作区被重命名后**保留旧名**（非强制模式） | 边界行为 | ✅ spec 澄清 #27 裁决（三文档交叉复核后定点修订） |
| R-18 | 权限失败 MUST 以**注入式构造**产生（root 绕过 DAC 检查） | 测试构造 | ✅ root 环境 DAC 权限实测（三文档交叉复核后定点修订） |

**NEEDS CLARIFICATION 残留**：**0 项** —— spec 的 27 项澄清决策已覆盖全部可预见的歧义，本 Phase 无需向用户追加提问。

---

## End of Phase 0 research.
