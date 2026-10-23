# 契约：模板清单与模板源文件（F001-P2）

**版本**：v1（F001-P1 建档 3 条 → 本 Phase 追加 43 条，累计 **46** 条）
**所有者**：`donkey/core/workspace/templates/manifest.json` + `donkey/core/workspace/templates/**.txt`
**上游**：[spec.md](../spec.md) FR-039 ~ FR-054；[research.md](../research.md) R-06 / R-07 / R-09

> **追加纪律**：P1 已有的 3 条（`instruction.md` / `providers/default.toml` / `mcp/mcp.json`）**MUST NOT 修改**路径与格式值；
> 本 Phase 只在 `entries` 数组**末尾追加** 43 条（spec FR-039）。

---

## 1. 清单文件

**路径**：`donkey/core/workspace/templates/manifest.json`
**编码**：UTF-8，无 BOM
**打包**：`pyproject.toml` 的 `[tool.setuptools.package-data]` MUST 显式列入 `"donkey.core.workspace.templates" = ["**/*.txt", "**/*.json", ".gitignore.txt"]` —— setuptools 以 `glob(recursive=True)` 解析 `package_data`，会**过滤以 `.` 开头的文件名**，故隐藏源 `templates/.gitignore.txt` MUST 单独显式列入，否则 wheel / sdist 缺该源 → 安装后 `donkey init` 报"模板源缺失"（退出码 `3`）。**仅 wheel / sdist 安装暴露**（editable 安装无感）→ 交付前 MUST 跑 §7.1 的 B2b 按打包产物核对。

---

## 2. 完整清单（46 条）

```json
{
  "version": 1,
  "entries": [
    { "path": "instruction.md", "format": "markdown" },
    { "path": "providers/default.toml", "format": "toml" },
    { "path": "mcp/mcp.json", "format": "json" },
    { "path": "skills/example/SKILL.md", "format": "markdown" },
    { "path": "README.md", "format": "markdown" },
    { "path": "tools/README.md", "format": "markdown" },
    { "path": "mcp/README.md", "format": "markdown" },
    { "path": "skills/README.md", "format": "markdown" },
    { "path": "memory/README.md", "format": "markdown" },
    { "path": ".gitignore", "format": "text" },
    { "path": "providers/README.md", "format": "markdown" },
    { "path": "providers/openai.toml", "format": "toml" },
    { "path": "providers/anthropic.toml", "format": "toml" },
    { "path": "providers/google.toml", "format": "toml" },
    { "path": "providers/ollama.toml", "format": "toml" },
    { "path": "providers/xai.toml", "format": "toml" },
    { "path": "providers/mistral.toml", "format": "toml" },
    { "path": "providers/qwen.toml", "format": "toml" },
    { "path": "providers/deepseek.toml", "format": "toml" },
    { "path": "providers/doubao.toml", "format": "toml" },
    { "path": "providers/kimi.toml", "format": "toml" },
    { "path": "providers/zhipu.toml", "format": "toml" },
    { "path": "providers/minimax.toml", "format": "toml" },
    { "path": "providers/tencent.toml", "format": "toml" },
    { "path": "providers/xiaomi.toml", "format": "toml" },
    { "path": "providers/stepfun.toml", "format": "toml" },
    { "path": "providers/openai-compatible.toml", "format": "toml" },
    { "path": "providers/meta.toml", "format": "toml" },
    { "path": "providers/bedrock.toml", "format": "toml" },
    { "path": "providers/groq.toml", "format": "toml" },
    { "path": "providers/fireworks.toml", "format": "toml" },
    { "path": "providers/together.toml", "format": "toml" },
    { "path": "providers/cohere.toml", "format": "toml" },
    { "path": "providers/perplexity.toml", "format": "toml" },
    { "path": "providers/databricks.toml", "format": "toml" },
    { "path": "providers/cerebras.toml", "format": "toml" },
    { "path": "providers/openrouter.toml", "format": "toml" },
    { "path": "tools", "format": "directory" },
    { "path": "mcp", "format": "directory" },
    { "path": "skills", "format": "directory" },
    { "path": "skills/example", "format": "directory" },
    { "path": "memory", "format": "directory" },
    { "path": "providers", "format": "directory" },
    { "path": "memory/sessions.sqlite3", "format": "sqlite3" },
    { "path": "memory/store.sqlite3", "format": "sqlite3" },
    { "path": "memory/knowledge.sqlite3", "format": "sqlite3" }
  ]
}
```

### 2.1 条数核对

| 组 | 条数 | 构成 |
|---|---|---|
| P1 已建档 | **3** | `instruction.md` / `providers/default.toml` / `mcp/mcp.json` |
| P2 追加 · 文本模板 | 7 | `skills/example/SKILL.md` / `README.md` / `tools/README.md` / `mcp/README.md` / `skills/README.md` / `memory/README.md` / `.gitignore` |
| P2 追加 · provider | 27 | `providers/README.md` + 26 个 `<id>.toml` |
| P2 追加 · 目录 | 6 | `tools` / `mcp` / `skills` / `skills/example` / `memory` / `providers` |
| P2 追加 · sqlite3 | 3 | `sessions` / `store` / `knowledge` |
| **累计** | **46** | 文本 37 + 目录 6 + sqlite3 3 |

### 2.2 条目顺序无语义

清单把 `providers/default.toml`（第 2 条）排在 `providers`（目录，第 **43** 条）之前 —— **渲染 MUST NOT 依赖顺序**：
写任何文件前 MUST 先确保其父目录存在（spec FR-012 / R-06）。未来追加条目同样 MUST NOT 引入顺序依赖。

> **序号口径（实测，勿漂移）**：文本条目占**第 1 ~ 37** 条、目录条目占**第 38 ~ 43** 条、sqlite3 条目占**第 44 ~ 46** 条。

### 2.3 `format: "python"` 在本 Phase 无条目

清单的 `format` 取值支持 `python`，但 46 条中**无**任何 `python` 条目 —— 内置 `@tool` 属 F001-P3。
这同时是宪法 N-01 门禁（G14）的依据：workspace 内 MUST NOT 出现 Python 入口文件。

---

## 3. 模板源文件（37 个）

**路径规则**：`donkey/core/workspace/templates/<entry.path>.txt` —— 与清单条目的 `path` **逐字符**对应。

| 组 | 数量 | 文件 |
|---|---|---|
| **覆盖** P1 占位 | 3 | `instruction.md.txt` / `providers/default.toml.txt` / `mcp/mcp.json.txt` |
| 新增 · 文本模板 | 7 | `README.md.txt` / `.gitignore.txt` / `tools/README.md.txt` / `mcp/README.md.txt` / `skills/README.md.txt` / `memory/README.md.txt` / `skills/example/SKILL.md.txt` |
| 新增 · provider 索引 | 1 | `providers/README.md.txt` |
| 新增 · provider 配置 | 26 | `providers/<id>.toml.txt`（26 个） |
| **合计** | **37** | 目录条目与 sqlite3 条目**无**源文件 |

**目录树（安装包内）**：

```text
donkey/core/workspace/templates/
├── manifest.json
├── instruction.md.txt              ← 覆盖 P1 占位
├── README.md.txt                   ← 新增
├── .gitignore.txt                  ← 新增
├── providers/
│   ├── default.toml.txt            ← 覆盖 P1 占位
│   ├── README.md.txt               ← 新增（列全 26 家）
│   ├── openai.toml.txt             ← 新增 ×26
│   ├── anthropic.toml.txt
│   ├── google.toml.txt
│   ├── ollama.toml.txt
│   ├── xai.toml.txt
│   ├── mistral.toml.txt
│   ├── qwen.toml.txt
│   ├── deepseek.toml.txt
│   ├── doubao.toml.txt
│   ├── kimi.toml.txt
│   ├── zhipu.toml.txt
│   ├── minimax.toml.txt
│   ├── tencent.toml.txt
│   ├── xiaomi.toml.txt
│   ├── stepfun.toml.txt
│   ├── openai-compatible.toml.txt
│   ├── meta.toml.txt
│   ├── bedrock.toml.txt
│   ├── groq.toml.txt
│   ├── fireworks.toml.txt
│   ├── together.toml.txt
│   ├── cohere.toml.txt
│   ├── perplexity.toml.txt
│   ├── databricks.toml.txt
│   ├── cerebras.toml.txt
│   └── openrouter.toml.txt
├── mcp/
│   ├── mcp.json.txt                ← 覆盖 P1 占位
│   └── README.md.txt               ← 新增
├── skills/
│   ├── README.md.txt               ← 新增
│   └── example/
│       └── SKILL.md.txt            ← 新增
├── tools/
│   └── README.md.txt               ← 新增（3 个内置 @tool 属 P3）
└── memory/
    └── README.md.txt               ← 新增（三模板 + --force 备份指引）
```

---

## 4. 占位符契约

| 占位符 | 替换为 | 备注 |
|---|---|---|
| `{{ workspace_name }}` | 工作区名称 | 主形态 |
| `{{workspace_name}}` | 工作区名称 | 无空格变体，同样 MUST 被识别 |
| 其它 `{{ ... }}` | **原样保留** | MUST NOT 报错、MUST NOT 替换为空串 |
| （名称取值约束） | 工作区名称含空格 / Unicode / 特殊字符时 MUST **原样注入**，MUST NOT 转义、MUST NOT 截断 | 约束注入值本身，非占位符（spec FR-015） |

**当前用到占位符的源文件**：`instruction.md.txt`（标题）、`README.md.txt`（标题）、`providers/default.toml.txt`（注释头）。

**MUST NOT 残留**：渲染后的 workspace 内 MUST NOT 出现任何占位符字面量（spec SC-014）。

---

## 5. 各模板的内容契约

### 5.1 `instruction.md`（系统提示词）

- 标题 = 工作区名称；
- 三个留白小节：**角色** / **风格** / **限制**（供用户填写）；
- MUST NOT 含任何 Python 入口文件（MUST NOT 出现 `agent.py` / `main.py`）。

### 5.2 `providers/default.toml`（保留名 · 全局默认）

- 两个字段：`default_provider` / `default_model`，**出厂态均为空串**；
- 注释 MUST 说明取值契约（provider 须指向同目录下的对应文件且该文件 `enabled = true`；model 须存在于该 provider 的 `[models]` 表中）；
- MUST NOT 含任何凭据；MUST NOT 是 provider 名。

### 5.3 `providers/README.md`（目录索引）

- MUST 列出**全部 26 个** provider id（一行一个）；
- MUST 说明"一 provider 一文件、文件名 stem == provider_id"的命名规则；
- MUST 说明启用三步：① `enabled = true` → ② 填凭据 → ③ 设 `default_provider` + `default_model`；
- MUST 说明未启用的文件**完全惰性**（不校验字段 / 不要求凭据 / 不参与连通性检查）。

### 5.4 26 份 `providers/<id>.toml`（provider 配置）

**统一骨架**：

```toml
# 启用步骤：1) enabled 改 true  2) 填凭据  3) 在 default.toml 设默认
enabled = false

api_key = ""              # 高敏感字段；TOML 明文，donkey 不读环境变量
api_host = ""
timeout = 60
max_retries = 6
temperature = 1.0
max_tokens = 16384

[models.<model_id>]
...
```

**三条硬约束**：

| # | 约束 | 依据 |
|---|---|---|
| P1 | MUST **逐字对齐** `harness/report/大模型toml参数设计.md` §8.3.3 ~ §8.3.28 的对应小节（含解释性注释） | spec FR-046 |
| P2 | MUST **完整收录**该小节的全部 `[models.*]` 子表（26 家合计 **51** 条），MUST NOT 删减 | spec FR-046 / SC-015 |
| P3 | MUST NOT 含 `REPLACE_ME` 类占位符；凭据字段出厂为空串 | spec FR-046 |
| P4 | `bedrock.toml` MUST NOT 含 `api_key`，改用 `aws_access_key_id` / `aws_secret_access_key` / `aws_region` / `aws_session_token` 四字段（出厂全为空串） | spec FR-047 / §8.2 |
| P5 | `ollama` / `meta` 等本地或自托管 provider 的凭据字段出厂为空串且 MUST NOT 被要求填写 | spec FR-047 |

**模型条目分布**（脚本核对全文，R-09）：

| provider | 条数 | provider | 条数 | provider | 条数 |
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

> **抄录方式**：MUST 用**脚本**从 §8.3 的 fenced code block 抽取（`##### 8.3.x` 标题定位 + ```toml 围栏取正文），
> 人工复核 diff 后提交；MUST NOT 手工誊写（誊写必漏注释行与空行）。脚本不落仓库。

### 5.5 `mcp/mcp.json`

合法 JSON，含一个空的 `mcpServers` 对象；MUST NOT 含任何预置服务器定义。

### 5.6 `skills/example/SKILL.md`

- frontmatter **恰含** `name`（值 `example`）与 `description` 两字段（MUST NOT 有额外字段，宪法 D-07）；
- 正文体现三层渐进披露模型（Level 1 头部元信息 / Level 2 正文主体 / Level 3 附属资源）；
- MUST 明确标注"完整第二层正文 + 第三层示例由 F001-P3 补齐"。

### 5.7 `README.md`（工作区总览）

- MUST 含工作区名称占位符（渲染后 MUST 出现名称）；
- MUST 概述各目录职责（`instruction.md` / `providers/` / `tools/` / `mcp/` / `skills/` / `memory/`）；
- MUST NOT 承诺引擎层能力（diff 审阅 / 路径权限交互等，宪法 AC-5）。

### 5.8 `tools/README.md` / `mcp/README.md` / `skills/README.md`

| 文件 | MUST 覆盖 |
|---|---|
| `tools/README.md` | 工具开发约定（命名 / 参数 / 错误处理 / timeout 建议）+ 标注内置工具文件属后续阶段 |
| `mcp/README.md` | 配置形状 + "用户自行填写"的定位 |
| `skills/README.md` | 三层模型 + frontmatter 两必填字段 |

### 5.9 `memory/README.md`

MUST 明确告知：

1. `memory/` 目录与三个 sqlite3 文件**全部是模板**、由 init 阶段预创建；
2. `sessions.sqlite3` 含上游 saver 的 `checkpoints` / `writes` + donkey 自管的 `sessions_metadata`（6 字段 + 2 索引）；
3. `store.sqlite3` / `knowledge.sqlite3` 在当前版本**仅占位空文件**（schema 推迟到后续版本）；
4. **`--force` 会删掉重建三个文件并清空历史与元数据，用户须在执行前手动备份** + MUST 给出 `cp` 备份命令示例；
5. "运行数据可选择性导出"仍成立（模板身份 ≠ 必须导出，宪法 D-02）。

### 5.10 `.gitignore`

```
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
venv/
memory/*.sqlite3
memory/*.sqlite3-wal
memory/*.sqlite3-shm
```

**已知遗留**（不在本 Phase 范围）：不忽略 `providers/*.toml` → 用户提交 workspace 会连带提交明文密钥。
由提示词固定内容 + 宪法 §3.5"凭据由用户自负"共同决定，建议随 v2 的 workspace 打包 / 导出功能一并设计。

---

## 6. sqlite3 条目的构造契约

| 条目 | 构造器 | 产出 | 源文件 |
|---|---|---|---|
| `memory/sessions.sqlite3` | `build_sessions_sqlite` | 3 表 + 2 索引（`sessions_metadata` 记录数 0） | 无 |
| `memory/store.sqlite3` | `build_store_sqlite` | 0 表 0 索引的空 sqlite3 文件 | 无 |
| `memory/knowledge.sqlite3` | `build_knowledge_sqlite` | 0 表 0 索引的空 sqlite3 文件 | 无 |

**安装包 MUST NOT 携带二进制 sqlite3 模板**（spec FR-030 / 宪法 D-05）→ `templates/` 下 MUST NOT 出现 `.sqlite3` / `.db` 文件。

**`--force` 行为**：unlink 主库 **+ unlink `-wal` / `-shm`** → 重新构造（spec FR-011）。
实测结论见 [research.md](../research.md) R-03：正常关闭连接时侧车会被 SQLite 自动清理；
陈旧 WAL 因盐值不匹配被安全忽略 → 连带删除是**防御性**措施，实现时注释 MUST NOT 声称"不删必然污染"。

---

## 7. 构建期自检（MUST 在交付前跑通）

| # | 检查 | 命令 / 方法 | 期望 |
|---|---|---|---|
| B1 | 清单条目总数 | 解析 `manifest.json` | `46` |
| B2 | 文本条目 ↔ 源文件**一一对应** | 对每个文本条目检查 `templates/<path>.txt` 存在；反向检查无孤儿 `.txt` | 各 37，双向无差。**并按打包产物核对**：wheel / sdist 解包后 37 个源文件全部在包内，**含 `.gitignore.txt` 这类以 `.` 开头的隐藏名** —— setuptools 的 `package_data` glob 会过滤隐藏文件名，隐藏源须在 `pyproject.toml` 的 `package-data` 中**显式列入** |
| B3 | 目录条目 ↔ 无源文件 | 检查 `templates/<dir>.txt` **不存在** | 6 个全部不存在 |
| B4 | sqlite3 条目 ↔ 无源文件 | 检查 `templates/memory/*.sqlite3.txt` **不存在** | 3 个全部不存在 |
| B5 | 26 份 provider 可被 `tomllib` 解析 | `tomllib.loads` 逐份解析 | 26/26 无异常 |
| B6 | provider 开关全为关闭 + 凭据为空 | 解析后断言 `enabled is False`、凭据字段为空 | 26/26 |
| B7 | **模型条目合计 51 条** | 统计 26 份文件中 `[models.` 开头的行数 | `51` |
| B8 | `providers/default.toml` 可解析且两字段存在 | `tomllib.loads` | 两个字段均在、值为空串 |
| B9 | `mcp/mcp.json` 可被 `json.loads` 解析 | 标准库 | 无异常、含 `mcpServers` |
| B10 | `SKILL.md` frontmatter 恰 2 字段 | 纯文本 split 解析 | `name` + `description`，无其它 |
| B11 | 安装包无二进制 sqlite3 模板 | `find templates/ -name "*.sqlite3"` | 无结果 |
| B12 | 渲染后无占位符残留 | 渲染到临时目录后 grep `{{` | 无结果 |

---

## End of template-manifest contract.
