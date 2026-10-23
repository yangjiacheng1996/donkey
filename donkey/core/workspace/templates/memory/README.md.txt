# memory/ —— 记忆库目录说明

`memory/` 目录与其中的三个 sqlite3 文件**全部是模板**，由 `donkey init` 阶段**预创建**。

## 三个记忆库文件

- `sessions.sqlite3` —— 短期记忆库：含上游 saver 的 `checkpoints`（历史表）与 `writes`（写入表），以及工作区自管的 `sessions_metadata`（6 个字段 + 2 个索引：标题索引与更新时间索引）。
- `store.sqlite3` —— 长期记忆库：当前版本**仅占位空文件**（0 表 0 索引），schema 推迟到后续版本。
- `knowledge.sqlite3` —— 知识库：当前版本**仅占位空文件**（0 表 0 索引），schema 推迟到后续版本。

## `--force` 会清空记忆库

`--force` 恢复出厂设置时，会**删掉重建**这三个文件（连同同名的 `-wal` / `-shm` 附属文件），历史会话与会话元数据**一并清空**。

**执行前请手动备份**，例如一次备份三个库：

```bash
cp memory/*.sqlite3 /tmp/backup-*.sqlite3
```

也可只备份其中一个库：

```bash
cp memory/sessions.sqlite3 /tmp/backup-sessions.sqlite3
```

## 运行数据

运行数据可选择性导出 —— 模板身份不等于必须导出。
