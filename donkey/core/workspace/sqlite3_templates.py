"""三个 sqlite3 记忆库模板的**程序化**结构构造器（F001-P2）。

宪法 D-05：sqlite3 的结构定义**属代码**，不属模板资产 —— 安装包 MUST NOT 携带
任何二进制 sqlite3 模板文件（spec FR-030），否则结构定义与代码会各自漂移。
故本模块用代码把三个库"造"出来。

三者的分工（data-model.md §7）：

- ``build_sessions_sqlite`` —— 短期记忆库：**三表两索引**。其中 ``checkpoints``
  与 ``writes`` 两张表由**上游 saver 包**维护（donkey MUST NOT 手写其建表
  语句，MUST NOT 承担结构漂移风险，spec FR-031）；``sessions_metadata`` 由
  donkey 自管（结构以项目既有结构文档为准，spec FR-034）。
- ``build_store_sqlite`` / ``build_knowledge_sqlite`` —— 长期记忆库占位 /
  知识库占位：**仅创建空的 sqlite3 文件**（0 表 0 索引），schema 推迟到后续
  版本（宪法 D-11 / spec FR-032）。

构造 MUST 幂等（``CREATE TABLE IF NOT EXISTS`` / ``CREATE INDEX IF NOT
EXISTS``），已存在的表与索引 MUST NOT 被破坏（spec FR-033）。任何失败 MUST
统一包成 ``TemplateGenerationError``（退出码 ``3``），MUST NOT 以裸异常逃逸
（spec FR-014）。
"""

import sqlite3
from pathlib import Path

from donkey.core.exceptions import _NEXT_STEP_TEMPLATE, TemplateGenerationError

#: ``sessions_metadata`` 的建表语句（6 字段 + 会话 id 主键）。
#:
#: 字段顺序不影响存储 —— SQLite 按列名匹配（structure doc §8 Q2）。
_SESSIONS_METADATA_DDL = """
CREATE TABLE IF NOT EXISTS sessions_metadata (
    thread_id      TEXT  PRIMARY KEY,
    title          TEXT  NOT NULL,
    created_at     REAL  NOT NULL,
    updated_at     REAL  NOT NULL,
    donkey_version TEXT  NOT NULL,
    first_prompt   TEXT
)
"""

#: 两个索引：标题索引与更新时间索引。
_SESSIONS_METADATA_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_sessions_metadata_title "
    "ON sessions_metadata(title)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_metadata_updated_at "
    "ON sessions_metadata(updated_at)",
)


def build_sessions_sqlite(path: Path) -> None:
    """构造短期记忆库（``memory/sessions.sqlite3``）。

    产出：三张表（上游 saver 的 ``checkpoints`` / ``writes`` + donkey 自管的
    ``sessions_metadata``）与两个索引（标题 / 更新时间）；``sessions_metadata``
    的出厂态记录数为 ``0``。

    失败：``TemplateGenerationError``（退出码 ``3``）—— 含上游 saver 包缺失 /
    版本不兼容 / 导入失败（spec 权威分类法 ⑥）、sqlite3 构造失败（⑤）。
    """
    db_path = Path(path)
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(db_path))
        # 上游 saver 的导入 MUST 放在函数体内 —— 包缺失 / 版本不兼容时，模块
        # 级的 import 会让异常在**导入 donkey 自身时**逃逸，无法归一为退出码
        # ``3``（spec 权威分类法 ⑥）。
        #
        # 导入路径是 ``langgraph.checkpoint.sqlite``（**不是**分发包名
        # ``langgraph_checkpoint_sqlite``，research.md R-01）。
        from langgraph.checkpoint.sqlite import SqliteSaver

        # ``setup()`` 是**实例方法** —— 写成 ``SqliteSaver.setup(conn)`` 会把
        # ``conn`` 误绑到 ``self`` 上并抛 ``AttributeError``
        #（research.md R-01 / R-04）。
        saver = SqliteSaver(conn)
        saver.setup()

        conn.execute(_SESSIONS_METADATA_DDL)
        for ddl in _SESSIONS_METADATA_INDEXES:
            conn.execute(ddl)
        conn.commit()
    except (sqlite3.Error, OSError, ImportError, AttributeError) as exc:
        raise TemplateGenerationError(
            f"构造短期记忆库失败：{db_path}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc
    finally:
        if conn is not None:
            conn.close()


def _build_empty_sqlite(path: Path, label: str) -> None:
    """创建一个**空的** sqlite3 文件（0 表 0 索引）。

    connect 之后 MUST NOT 执行任何 DDL / DML —— 连 ``CREATE TABLE`` 都不许，
    否则表数不为 ``0``（spec FR-032 / 宪法 D-11）。
    """
    db_path = Path(path)
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(db_path))
    except (sqlite3.Error, OSError) as exc:
        raise TemplateGenerationError(
            f"构造{label}失败：{db_path}（{exc}）。{_NEXT_STEP_TEMPLATE}"
        ) from exc
    finally:
        if conn is not None:
            conn.close()


def build_store_sqlite(path: Path) -> None:
    """构造长期记忆库占位文件（``memory/store.sqlite3``）。

    产出：**空的** sqlite3 文件（0 表 0 索引）。schema 推迟到 v3
    ``SqliteStore`` 实施时落点（宪法 D-11）；MUST NOT 被 donkey 本体的任何
    运行时路径读取。

    失败：``TemplateGenerationError``（退出码 ``3``）。
    """
    _build_empty_sqlite(path, "长期记忆库占位文件")


def build_knowledge_sqlite(path: Path) -> None:
    """构造知识库占位文件（``memory/knowledge.sqlite3``）。

    产出：**空的** sqlite3 文件（0 表 0 索引）。schema 待引擎（sqlite-vec /
    faiss+sqlite）选型后正式化。

    失败：``TemplateGenerationError``（退出码 ``3``）。
    """
    _build_empty_sqlite(path, "知识库占位文件")
