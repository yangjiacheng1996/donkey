# workspace sqlite 数据库文件 schema 一览

> 本文档集中记录 `<workspace>/memory/*.sqlite3` 三个文件中所有表 + 索引的结构、来源与状态，
> 协助 F002-P2 `SqliteSchemaError` (exit 16) 诊断 + F001-P2 schema builder 实施参考。
>
> **数据来源**：
> - F001-P2 §4.7.6 (`sessions.sqlite3` / `store.sqlite3` schema builder 实装计划) 与 §6.15 (`sessions_metadata` 列断言)
> - README §4.1.1 与立项书 §4.6.3 「memory/ 模板边界」（spec 顶层表述）
> - 立项书 §4.10 TD-02 路线图（`store_items` schema 蓝本 = `langgraph-checkpoint-postgres`）
> - `harness/LangGraph_doc/` 内 checkpointers / long-term-memory 等官方文档（SqliteSaver / Store 接口契约）

---

## §1. 文件与表归属总览

| 文件 | 引擎域 | 创建时机 | 现阶段状态 | v1 是否启用 |
|---|---|---|---|---|
| `memory/sessions.sqlite3` | 短期记忆 Saver（schema 构造 = F001-P2 / 运行时使用 = F004-P4） | F001-P2 schema builder | **schema 完成**：3 表（SqliteSaver `checkpoints` / `writes` + donkey `sessions_metadata`）+ 2 索引 | **启用**（SqliteSaver 写历史） |
| `memory/store.sqlite3` | 长期记忆 Store（v3+） | F001-P2 schema builder（占位） | **仅空文件**：**不**建任何表 / 索引——schema 全部推迟到 v3 SqliteStore 实施；届时由 Maintainer 修改 F001-P2 §4.7.6 添加 `store_items` 等建表 SQL | **占位**（v1 不挂 store；v3 启用时再决定 schema） |
| `memory/knowledge.sqlite3` | RAG 向量库（v3+ 候选） | F001-P2 schema builder（占位） | **仅空文件**：schema 推迟到 RAG 引擎（sqlite-vec / faiss+sqlite 等）选型后；届时由 Maintainer 修改 F001-P2 添加建表 SQL | **占位**（v1 无任何 RAG 集成） |

**两个关键事实**：
1. F001-P2 不是"不初始化表结构"——而是"按当前 spec 的明确范围初始化 sessions.sqlite3 schema（含 SqliteSaver 表 + donkey `sessions_metadata` + 2 索引）；store.sqlite3 / knowledge.sqlite3 留空文件（schema 推迟 v3 实施）"。
2. **SqliteSaver 的 `checkpoints` / `writes` 表 schema 由 `langgraph-checkpoint-sqlite` 包控制**，不在 donkey 维护范围内（详见 §2.1）。

---

## §2. `memory/sessions.sqlite3` —— v1 完整 schema

### §2.1 SqliteSaver 内部表（upstream-controlled）

由 `langgraph-checkpoint-sqlite` 包管理的两张表，donkey **不**修改、**不**追踪字段类型，仅做 SELECT / 通过 SqliteSaver 间接写：

| 表 | 来源 | donkey 可写？ |
|---|---|---|
| `checkpoints` | `langgraph-checkpoint-sqlite::SqliteSaver.setup()` | 否（仅 SqliteSaver 写；donkey 仅做**健康检查级别的元数据读**——`PRAGMA table_info` 等 F002-P2 用，**不**改写 `checkpoints` 记录，**不**追踪字段级 schema） |
| `writes` | 同上 | 否 |

**F002-P2 健康检查**（仅断言"表存在 + 列存在"，**不** pin 主键列名 / 列类型）：`PRAGMA table_info(checkpoints)` + `PRAGMA table_info(writes)` 字段存在即视为健康（exit 0）；字段缺失或类型不匹配触发 `SqliteSchemaError` (exit 16)。

> **上游 schema 实测**（`langgraph-checkpoint-sqlite` 3.x `SqliteSaver.setup()` 内联 DDL，donkey **不**复制、不维护）：
> - `checkpoints`：`thread_id` / `checkpoint_ns` / `checkpoint_id` / `parent_checkpoint_id` / `type` / `checkpoint`(BLOB) / `metadata`(BLOB)，主键 `(thread_id, checkpoint_ns, checkpoint_id)`；
> - `writes`：`thread_id` / `checkpoint_ns` / `checkpoint_id` / `task_id` / `task_path` / `idx` / `channel` / `type` / `value`(BLOB)，主键 `(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)`；
> - `setup()` 内含 `PRAGMA journal_mode=WAL` → 运行期会生成 `sessions.sqlite3-wal` / `sessions.sqlite3-shm` 侧车文件（已由 workspace `.gitignore` 模板忽略）。

**升级路径**：字段 schema 与 `langgraph-checkpoint-sqlite` 版本绑定，**由 LangChain 主线负责**。donkey 升级 sqlite3 时不会触碰这两张表的 schema——若这两张表出问题，根因在 `langgraph-checkpoint-sqlite` 升级，donkey 不背锅。

> **不破坏升级的触发路径**：`langgraph-checkpoint-sqlite` minor release → SqliteSaver.setup() 在新旧 sqlite3 上跑 `CREATE TABLE IF NOT EXISTS` 时**新增列 / 加索引不会重建**。若上游 release**改字段名 / 减列**，F002-P2 `PRAGMA table_info` 断言会 break——是上游契约变化，由 LangChain 负责公告与迁移脚本；donkey 不背锅，但 F002 检查只断言"字段名集合 + 至少 N 个核心列存在"，**不** pin 主键列名 / 列类型，以减小上游漂移影响面。

### §2.2 donkey 自管 `sessions_metadata` 表

```sql
CREATE TABLE IF NOT EXISTS sessions_metadata (
    thread_id      TEXT  PRIMARY KEY,  -- SqliteSaver thread_id（UUID v4）
    title          TEXT  NOT NULL,     -- 会话标题（≤ 20 字；默认 "无标题会话"）
    created_at     REAL  NOT NULL,     -- epoch 秒（float）
    updated_at     REAL  NOT NULL,     -- 排序主索引（按最近活动 DESC）
    donkey_version TEXT  NOT NULL,     -- 生成该记录的 donkey 版本号（迁移提示用）
    first_prompt   TEXT               -- 用户首轮 prompt 快照（nullable）
);

CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title
    ON sessions_metadata(title);

CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at
    ON sessions_metadata(updated_at);
```

**字段语义与写入路径**：

| 字段 | 写入方 | 写入时机 | 说明 |
|---|---|---|---|
| `thread_id` | `core.api.new_session` | INSERT | SqliteSaver 主键同步；UUID v4 形式 |
| `title` | `core.api.new_session`（N-10） | INSERT | 默认 "无标题会话"；用户传 `--title` / `--first-prompt` 时覆盖。**标题回退规则**：给了 `first_prompt` 时，LLM 总结失败 / 超时 → **取 `first_prompt` 前 20 字**（**绝不**回退成"无标题会话"）——详见 README §6.3 + 立项书 §5.5.4.5 |
| `created_at` | `core.api.new_session` | INSERT | `time.time()` 或 `datetime.now(timezone.utc).timestamp()` |
| `updated_at` | `core.api.new_session`（INSERT 时） | INSERT | 会话变更排序用；**v1 不做运行时刷新**（仅新建会话时写入一次） |
| `donkey_version` | `core.api.new_session` | INSERT | 当前 donkey 版本号（与 workspace manifest `donkey_version` 同源；建议硬编码 `'0.1.0'` 而非 `importlib.metadata.version()`，避开循环依赖）；`--force` 重建 sqlite3 后**旧记录的 `donkey_version` 不变**——donkey 不会因 schema 重建而改写用户数据 |
| `first_prompt` | `core.api.new_session` | INSERT | nullable（用户没传则 NULL）；**用途**：落库保存用户首轮 prompt 原文（与"标题总结用的 first_prompt"是同一份数据的两种角色：总结调用 LLM 后将原文落库）。**v1 无 `donkey session show` 命令**（F003 四命令 = list / new / remove / import），本列 v1 仅落库、暂不消费，为 v2+ "会话详情"能力预留 |

**F002-P2 健康检查**：`PRAGMA table_info(sessions_metadata)` 返回上述 6 列即视为字段健康；`idx_sessions_metadata_title` + `idx_sessions_metadata_updated_at` 索引名存在即视为索引健康。任一缺失触发 `SqliteSchemaError` (exit 16)。

**字段不存在时的处理**：`init` 阶段 schema builder 写入完整 schema；**`core.api.new_session` 不再 `CREATE TABLE IF NOT EXISTS`**——schema 缺失即视为"workspace 未 init / --force 后被外部破坏"，应**报 `SessionNewSqliteError` (exit 23) 让用户重跑 `donkey init`**，而不是用 `IF NOT EXISTS` 掩盖问题（README §6.3 F003-P2 step 1 + 立项书 §5.5.4.5 契约已锁定此行为）。

> **关于恢复路径的两种语义**：
> 1. **`donkey init --force`**（F001-P2 §4.7.6）：**先 `unlink` 旧 sqlite3 + 调 builder 重建**——能恢复 schema，但同时清空 SqliteSaver 历史 + sessions_metadata 元数据；用户必须先 `cp memory/*.sqlite3 /tmp/backup-*.sqlite3` 备份。
> 2. **`donkey init`（不带 `--force`）**：发现 sqlite3 已存在 → 不触碰（保留用户数据）→ schema 缺失时报错让用户用 `--force`。
> 不存在"只清 messages 不清元数据"的细粒度路径（F001-P2 §2.6 锁定此拒绝）。

### §2.3 schema builder 代码锚点（F001-P2 §4.7.6）

```python
# donkey/core/workspace/sqlite3_templates.py

def build_sessions_sqlite(path: Path) -> None:
    """构造 sessions.sqlite3 schema-built 空文件（F001-P2 §4.7.6）。

    失败归类：统一抛 TemplateGenerationError (exit 3)——
    模板清单损坏 / schema 非法 / 源缺失 / 渲染失败 / 文件写入失败 / sqlite3 schema 构造失败 / 上游 saver 不可用 / 目标路径是目录 —— 统一归退出码 3（奥卡姆合并；权威 **7 类**分类法见 F001-P2 spec『模板生成类失败的 7 类成因（权威分类法）』）。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        # 1. SqliteSaver 自有 checkpoints / writes 表（上游 DDL 见 §2.1，donkey 不复制）
        from langgraph.checkpoint.sqlite import SqliteSaver
        SqliteSaver(conn).setup()   # ← setup() 是【实例方法】：内部走 self.conn

        # 2. donkey 自管 sessions_metadata + 2 索引
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions_metadata (
                thread_id      TEXT  PRIMARY KEY,
                title          TEXT  NOT NULL,
                created_at     REAL  NOT NULL,
                updated_at     REAL  NOT NULL,
                donkey_version TEXT  NOT NULL,
                first_prompt   TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title "
            "ON sessions_metadata(title)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at "
            "ON sessions_metadata(updated_at)"
        )
        conn.commit()
    except Exception as e:
        raise TemplateGenerationError(
            f"sessions.sqlite3 schema construction failed: {e}"
        ) from e
    finally:
        conn.close()
```

> ⚠️ **API 注意**：`SqliteSaver.setup()` 是**实例方法**（`def setup(self) -> None`，内部用 `self.conn.executescript(...)`），**不是**接受 conn 的 classmethod / staticmethod——因此正确写法是 `SqliteSaver(conn).setup()`，**不是** `SqliteSaver.setup(conn)`（后者会因 `self` 绑定错误而抛 `AttributeError`）。`langgraph-checkpoint-sqlite` 3.x 源码实证。

**verify 锚点**：`tests/e2e/phase/verify_phase_f001_p2.py::test_scenario_14_sqlite3_templates_with_schema` 含完整 PRAGMA 断言（表存在性 + 字段名 + 索引名 + 空数据）。

---

## §3. `memory/store.sqlite3` —— v1 仅创建空文件（schema 全部推迟到 v3 SqliteStore 实施）

### §3.1 现状

| 阶段 | schema builder 行为 |
|---|---|
| F001-P2 init 阶段（v1 实施） | **仅创建空 sqlite3 文件**，**不**建任何表 / 索引 |
| v1 启用情况 | **不启用**：文件已就位但不调用——`create_agent(store=...)` 不传 store 参数；donkey 本体不读 store.sqlite3（F004-P5 v1 用 `InMemoryStore` 顶替） |
| **v3 SqliteStore 实施时**（Maintainer 修改 F001） | **`build_store_sqlite` 增加建表 SQL**（如 `CREATE TABLE store_items ...` + 索引）；同时本文件 §3 整个 schema 节补全；F002-P2 SqliteSchemaError 检查清单同步添加 `PRAGMA table_info(store_items)` |

### §3.2 现状：F001-P2 `build_store_sqlite` 实现（**v1**）

```python
def build_store_sqlite(path: Path) -> None:
    """构造 store.sqlite3 空文件占位（F001-P2 §4.7.6）。

    v1 仅触发 sqlite3 文件创建；schema 全部推迟到 v3 SqliteStore 实施。
    实施时除本文档 §3.3 待敲定项外，**Maintainer 必读立项书 §4.10 TD-02 路线图 步骤 1-5**，
    看懂 `langgraph-checkpoint-postgres` 的 PostgresStore 表结构后再补 SQL。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.close()  # 仅触发文件创建；schema 待 v3
```

### §3.3 v3 SqliteStore 实施时的待敲定项（**v3 启动期讨论，本 Phase 不介入**）

| # | 待定 | Maintainer 决策锚点 |
|---|---|---|
| 0 | **schema 蓝本** | **`LangGraph_doc/stores.md:339-346`**（Postgres 端 `store_items` 推荐 schema），SQLite 端口需做**数组语法 / JSONB→TEXT / GIN→FTS5** 三处适配 |
| 1 | 表名（`store_items` / 其他） | 与 langgraph-checkpoint-postgres 的 PostgresStore 对齐 |
| 2 | `prefix` / `key` 主键结构 | 与 LangGraph `BaseStore.aput(namespace: tuple[str, ...], key: str)` 接口契约对齐（`LangGraph_doc/stores.md:332-336`） |
| 3 | `value` **与 `namespace`** 序列化 | 两者均 Postgres JSONB / TEXT[] → SQLite **TEXT（JSON 字符串）** + `json_extract` / `json_each` 适配；`namespace` 以 JSON 数组字符串形式存储（如 `'["alice","memories"]'`，参考 `LangGraph_doc/stores.md:73`） |
| 4 | namespace 索引方案 | Postgres 端 `USING gin(namespace)`（`stores.md:349`），SQLite **无 GIN / GIST**——可用：①`json_each` 展开为虚拟表 + B-Tree 索引；②FTS5；③自定义 LIKE 前缀函数（`LIKE '["alice",%'`）；④触发器。需 v3 启动期实测对比 |
| 5 | DeltaChannel 反序列化兼容 | v3 实施时跟 LangChain 1.x 主线跑兼容性测试 |
| 6 | 同步接口（`put` / `get` / `search` 等） | v3 路线图步骤 3 |
| 7 | 实施工作量 | ~5 人周（立项书 §4.10 TD-02 已预算） |

### §3.4 F002-P2 健康检查

**当前**（v1）：F002-P2 SqliteSchemaError (exit 16) **不**涉及 `store.sqlite3`——空文件 `PRAGMA table_info` 返回空集即视为健康（与 integrity_check 行为一致）。

**v3 实施时**：F002-P2 检查清单追加 `PRAGMA table_info(store_items)` + namespace 索引存在性 + `PRAGMA integrity_check`；SqliteSchemaError 触发场景对应调整。

---

## §4. `memory/knowledge.sqlite3` —— v1 仅空文件（schema 留白）

### §4.1 现状

| 阶段 | 行为 |
|---|---|
| F001-P2 init 阶段 | **仅创建空 sqlite3 文件**，**不**建任何表 / 索引（schema 完全留白） |
| v1 启用 | 不启用；`create_agent()` 不传入 knowledge 参数 |
| v3+ RAG 引擎选型后 | 由对应 RAG 引擎 schema 补全 |

### §4.2 为什么 v1 选"完全留白"而非"占位骨架"

knowledge.sqlite3 的 schema 取决于**选哪个 RAG 引擎**——不同引擎的表结构差异巨大：

| 引擎 | 主要 schema 形态 | donkey 涉及工作 |
|---|---|---|
| **sqlite-vec** | `vec_items` 虚拟表 + rowid-based 向量检索 + metadata 列；sqlite extension 加载 | 中（需 prebuilt sqlite-vec .so / .dylib） |
| **faiss + sqlite hybrid** | `faiss_index_meta`（索引 ID + sqlite 数据）+ faiss 索引落地单独文件 | 高（双持） |
| **外部向量 DB**（Qdrant / Milvus） | 0 张 sqlite 表（外部服务进程） | **不推荐**（违反 §1.2.2 P2 打包即走） |

v1 不预设任何候选——写占位骨架会**事后改 schema**，比留空代价更大。F001-P2 选择"创建空文件占位"是**最小承诺 + 最大可逆**：workspace zip 备份结构稳定，RAG 选型后**新增**表即可，无需破坏现有 sqlite3。

### §4.3 schema builder（v1 当前实现 = 仅创建文件）

```python
def build_knowledge_sqlite(path: Path) -> None:
    """构造 knowledge.sqlite3 空文件占位（F001-P2 §4.7.6）。

    v1 仅触发 sqlite3 文件创建；schema 待 RAG 引擎选型后补。

    该占位行为同时也在 `LangChain_doc/retrieval.md` 的 RAG 集成表中
    对所有 sqlite-based 向量引擎预留接口——v3 选型时按本文档 §4.2 表格去匹配。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.close()  # 仅触发文件创建
```

### §4.4 F002-P2 健康检查

**当前**：F002-P2 SqliteSchemaError (exit 16) **不**涉及 `knowledge.sqlite3`——空文件 PRAGMA 全 OK。

**未来**：RAG 引擎选型后，F002-P2 检查清单追加 `PRAGMA table_info(<RAG 表>)` + `PRAGMA integrity_check`。

---

## §5. donkey 不控制 / 不追踪的表（schema 来源属于上游）

| 表 / 文件 | 来源 | donkey 角色 | 升级路径 |
|---|---|---|---|
| `sessions.sqlite3.checkpoints` | `langgraph.checkpoint.sqlite` v0.1.x+ | 仅 SELECT（SqliteSaver 写） | langchain-ai/langgraph-checkpoint-sqlite 主线 |
| `sessions.sqlite3.writes` | 同上 | 同上 | 同上 |
| `sessions.sqlite3.sessions_metadata` | **donkey 自管**（§2.2） | INSERT / DELETE（**v1 不 UPDATE**——`updated_at` 仅新建时写一次） | donkey 版本号字段 `donkey_version` + 后续版本写 schema migration |
| `store.sqlite3.*` | v3 SqliteStore 实施时由 donkey 自管（v1 不存在） | v3 启用后由 SqliteStore 写 | donkey `donkey.core.memory.store` + schema migration |
| `knowledge.sqlite3.*` | v3+ RAG 引擎候选（v1 不存在） | v3+ 由 RAG 引擎写 | 同上 |

**含义**：F002-P2 SqliteSchemaError 涉及**唯一**一套 donkey 自家 schema（§2.2 sessions_metadata）；另外两张表（v3 才有）后续视实施情况追加。v1 阶段 donkey 维护工作量**仅** §2.2 sessions_metadata 一处 SqliteSaver 内部表由上游 `langgraph-checkpoint-sqlite` 维护，donkey 跟随升级。

---

## §6. 优先级 roadmap

| Schema | 完善时机 | 触发条件 | 工作量 |
|---|---|---|---|
| `sessions.sqlite3.sessions_metadata` 列调整 | donkey 升级 + new column 需求 | donkey minor release | ~0.5 人周 |
| **`sessions_metadata.donkey_version` 列迁移路径** | donkey minor 升级触发 schema migration 时 | 按 `donkey_version` 列筛选需迁移的旧 session；`--force` 只清数据不修改字段值；F002-P2 留 `MIN(donkey_version) < current_version` 触发钩子 | ~0.5 人周 |
| `store.sqlite3.*`（v1 不存在，v3 实施时新增） | **v3 SqliteStore 实施启动期**（Maintainer 修改 F001-P2 §4.7.6 + 本文件 §3） | F003 长期记忆启用 | **~5 人周** |
| `store.sqlite3.*` namespace 索引方案 | 同上 | 同上 | 嵌入上面工作量 |
| `knowledge.sqlite3.*`（v1 不存在，v3+ 实施时新增） | **v3+ RAG 引擎选型**（Maintainer 修改 F001-P2 §4.7.6 + 本文件 §4） | 用户启用 `donkey ingest` 类命令 | 待评估（建议先评估 sqlite-vec） |
| SqliteSaver `checkpoints` / `writes` | n/a（upstream-controlled） | 跟随 `langgraph-checkpoint-sqlite` 升级 | n/a |

---

## §7. F002-P2 SqliteSchemaError 退出条件（与本文档对齐）

F002 跑 9 项检查（README §3.2 + 立项书 §5.5.3 "动态检查"）时，**第 6 项** `memory/sessions.sqlite3 可读 + schema 健康` 触发的 `SqliteSchemaError` (exit 16) 当前**仅**涉及 `sessions.sqlite3`（与 §2 / §3.4 / §4.4 对齐）：

| # | 检查 | 文件 | 命令 | 失败后果 |
|---|---|---|---|---|
| 1 | SqliteSaver `checkpoints` 表存在 | `sessions.sqlite3` | `PRAGMA table_info(checkpoints)` | `SqliteSchemaError` → exit 16 |
| 2 | SqliteSaver `writes` 表存在 | `sessions.sqlite3` | `PRAGMA table_info(writes)` | `SqliteSchemaError` → exit 16 |
| 3 | donkey `sessions_metadata` 表存在 + 6 字段匹配 | `sessions.sqlite3` | `PRAGMA table_info(sessions_metadata)` | `SqliteSchemaError` → exit 16 |
| 4 | donkey `sessions_metadata` 的 2 个索引存在 | `sessions.sqlite3` | `sqlite_master` 查询 `idx_sessions_metadata_title` / `idx_sessions_metadata_updated_at` | `SqliteSchemaError` → exit 16 |
| 5 | sqlite 文件无损坏 | `sessions.sqlite3` | `PRAGMA integrity_check` | `SqliteSchemaError` → exit 16 |

**任一失败即抛 `SqliteSchemaError` → exit 16**。

**`store.sqlite3` / `knowledge.sqlite3` 当前不参与 SqliteSchemaError**（§3.4 / §4.4）——v1 阶段两文件为空文件无 schema；v3 实施时按本文档 §3.4 / §4.4 追加。

---

## §8. 实施侧 FAQ（给 F001-P2 schema builder 实装者）

**Q1：`SqliteSaver.setup(conn)` 真的能直接调用吗？**  
A：**不能**——`langgraph-checkpoint-sqlite` 3.x 的 `SqliteSaver.setup()` 是**实例方法**（`def setup(self) -> None`，内部走 `self.conn.executescript(...)`），正确写法是 **`SqliteSaver(conn).setup()`**；写成 `SqliteSaver.setup(conn)` 会把 conn 误绑到 `self` 上而抛 `AttributeError`（上游 schema 见 §2.1）。其字段名 / 索引 / PRIMARY KEY 的具体 schema **不在 donkey 维护范围内**，donkey 仅依赖 SqliteSaver 自己健康。具体列结构与 `langgraph-checkpoint-sqlite` 版本绑定，跟随上游升级——donkey F002 健康检查只断言"表存在 + 列存在"，不 pin 列类型 / 主键约束（详见 §2.1 + §3 + §7）。

**Q2：sessions_metadata 字段顺序重要吗？**  
A：PRAGMA 字段顺序与 INSERT 不一致时 SQLite 自动按列名匹配，**不**影响存储；字段名 + 类型严格即可（基线断言见 §2.3 锚点）。

**Q3：`build_store_sqlite` 现在为什么只创建空文件、不建表？**  
A：设计决策——v3 SqliteStore 实施时再决定 `store_items` 等表的列结构（详见立项书 §4.10 TD-02 路线图）。**原因**：v1~v2 用 `InMemoryStore` 顶替（立项书 §4.10 TD-02 路线图），donkey 本体不读 store.sqlite3——若 v1 就建占位表，**实际无人写**反而误导读者以为"功能已可用"。留空文件 + manifest 收纳表示"db schema 待定"，是更诚实的契约；同时避免"`--force` 后用占位列跑了 v3 migration"的债务。

**Q4：knowledge.sqlite3 空文件会被 `git status` 忽略吗？**  
A：会，`.gitignore` 模板含 `memory/*.sqlite3` + `memory/*.sqlite3-wal` + `memory/*.sqlite3-shm`（README §4.4 P2 init 模板 + F001-P2 §4.7.5 + workspace/memory/README.md 已写入）。git 只看到 memory/ 目录本身 + README.md，**不**看到三个 sqlite3 文件及其 WAL / SHM 侧车。

**Q5：F002-P2 跑 SqliteSchemaError 时，三个 sqlite3 都查吗？**  
A：当前 `SqliteSchemaError` (exit 16) **仅** `sessions.sqlite3`（§7 三件套）；`store.sqlite3` / `knowledge.sqlite3` 不参与。v3 实施时按 §3.4 / §4.4 追加。

---

**End of sqlite 表结构一览.**
