# 数据模型 —— F001-P1 `cli_validation`

**范围**：本 Phase 不引入持久化数据结构（无数据库、无状态文件）；下列"实体"均为**进程内契约对象**与**文件级契约**，供 `contracts/` 与实现阶段对齐。
**数据存储**：文件系统（workspace 根目录）。本 Phase 只创建目录，不写任何文件内容。

---

## 1. `InitResult` —— init 的返回契约对象

**性质**：不可变数据类（frozen dataclass），由 `core.api.init_workspace` 返回，是本 Phase 唯一的对外结果载体。

| 序号 | 字段 | 类型 | 含义 | P1 取值 | 后续阶段取值 |
|---|---|---|---|---|---|
| 1 | `workspace_path` | `Path` | workspace 的**绝对路径**（已解析） | 解析后的目标路径 | 同左 |
| 2 | `name` | `str` | workspace 名称 | **未指定时恒为路径末段**（basename）；库 API 显式传入非空名称时以其为准 | 同左（内容注入见 P2） |
| 3 | `force` | `bool` | 本次是否请求强制重置 | 用户是否传 `--force` | 同左（P2 起驱动重置） |
| 4 | `templates_loaded` | `int` | 已加载的模板清单条目数 | **固定 0**（P1 不加载清单） | 清单条目总数 |
| 5 | `files_created` | `int` | 本次实际新建的文件数 | **固定 0**（P1 只建根目录） | 实际创建数 |
| 6 | `files_skipped` | `int` | 已存在而跳过的文件数 | **固定 0** | 跳过数 |

**校验规则**

- `workspace_path` MUST 为绝对路径（spec FR-010）——相对路径输入 MUST 先被解析为绝对路径；
- `name` 在**未指定**（`None` / 空串）时 MUST 等于 `workspace_path` 的末段名，且 MUST 非空（spec FR-012）——空末段名（根路径）在校验阶段即被拒，不会进入结果对象；
- 库 API 显式传入**非空** `name` 时 MUST 以该值为准（spec FR-005 / FR-017）；CLI 通道 MUST NOT 传入该参数，MUST NOT 存在与路径不一致的命名来源（spec FR-003）；
- `templates_loaded` / `files_created` / `files_skipped` 在 P1 MUST 恒为 `0`（spec FR-007）。

**状态迁移**：不适用（无状态机）。`init` 的幂等语义由"目标已存在不报错"表达（spec FR-008 / FR-028）。

---

## 2. 异常类层次 —— 失败的表达方式

```
Exception
└── DonkeyError                     # donkey 总基类
    └── WorkspaceInitError          # F001 基类
        ├── PathNotFoundError       # exit 1：路径 / 输入不合法
        └── PathPermissionError     # exit 2：权限不足
```

| 异常类 | 退出码 | 触发条件 | 修复动作（用户侧） |
|---|---|---|---|
| `PathNotFoundError` | `1` | 父目录不存在；路径含非法字符（NUL）；解析后末段名为空（根 / 盘符根 / UNC 共享根）；空字符串路径；目标存在但不是目录；父目录是文件；悬空符号链接；路径过长 | "建目录 / 换路径" |
| `PathPermissionError` | `2` | 目标不存在时父目录缺写位或执行位；目标已存在时缺读 / 写 / 执行位 | "调整权限" |

**规则**

- 每个异常类的 docstring MUST 标注其退出码（spec FR-026）；
- 异常 MUST 由 CLI 层统一捕获并映射为退出码，核心层 MUST NOT 感知进程退出码（宪法 N-05 / N-03）；
- **参数用法错误**（缺子命令 / 缺必填参数 / 未知参数）MUST 归入退出码 `1`，不新增异常类（澄清决策 1）。

---

## 3. 校验三元组 —— 综合校验的内部契约

`validate_init_request(path, name, force)` 的返回值，是 `init_workspace` 的唯一内部输入。

| 位置 | 字段 | 类型 | 语义 |
|---|---|---|---|
| 0 | `abs_path` | `Path` | 解析后的绝对路径（末段名非空） |
| 1 | `resolved_name` | `str` | 名称：`name` 为 `None` / 空串时 = `abs_path` 末段名；为非空串时 = 该值 |
| 2 | `force` | `bool` | 原样透传的强制标志 |

**不变量**：`abs_path.parent` 存在；`abs_path.name` 非空；`resolved_name` 在 `name` 未指定时 == `abs_path.name`、显式指定非空值时 == 该值（spec FR-005 / FR-017）；三者 MUST 无副作用地产生（spec FR-016）。

---

## 4. 退出码段位 —— F001 域的编码空间

| 码值 | 归属 | 语义 | 本 Phase |
|---|---|---|---|
| `0` | 全子命令 | 成功 | ✓ 使用 |
| `1` | F001 子段 1 | 路径 / 输入 / 参数用法不合法（`PathNotFoundError`） | ✓ 使用 |
| `2` | F001 子段 1 | 权限不足（`PathPermissionError`） | ✓ 使用 |
| `3` | F001 子段 2（P2） | `TemplateGenerationError` | ✗ 不触发 |
| `4` | F001 子段 3（P3） | `BuiltinToolGenerationError` | ✗ 不触发 |
| `5-10` | F001 段位预留 | v1.x 试运行期新错误 | ✗ 不触发 |

**不变量**（spec FR-027 / SC-011）：本 Phase 实际使用的退出码集合恰为 `{0, 1, 2}`；`1` 与 `2` 各自保持单一语义。

---

## 5. 模板清单条目 —— P1 的本阶段自建资产（P1 不消费）

**性质**：P1 只**建档**、不加载、不解析、不校验。列出目的是锁定 P2 的对接格式与源文件命名规则。

**Schema**

```json
{
  "version": 1,
  "entries": [
    { "path": "instruction.md",        "format": "markdown" },
    { "path": "providers/default.toml", "format": "toml" },
    { "path": "mcp/mcp.json",           "format": "json" }
  ]
}
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `version` | `int` | P1 = `1` |
| `entries` | `list[dict]` | 每条含 `path`（相对 workspace 根）；可选 `format`（7 选 1：`markdown` / `toml` / `json` / `text` / `python` / `directory` / `sqlite3`） |

**源文件命名规则（权威，来自 Phase 提示词 §3.2 的规则项）**

```
donkey/core/workspace/templates/{entry['path']}.txt
```

| 条目 `path` | 对应源文件（P1 建立） |
|---|---|
| `instruction.md` | `templates/instruction.md.txt` |
| `providers/default.toml` | `templates/providers/default.toml.txt` |
| `mcp/mcp.json` | `templates/mcp/mcp.json.txt` |

> （历史注记）提示词 §3.2 原把第三个源写作 `mcp.json.txt`，与本节规则冲突；**已于 2026-10-21 按 R-06 规则修正为 `mcp/mcp.json.txt`**。

**后续阶段的追加节奏**（本 Phase 不实施）：P1 = 3 条 → P2 追加 43 条 = 46 条 → P3 追加 7 条 = 53 条；**每一条都必须有同名 `.txt` 源**，否则 P2 渲染时 exit 3。

---

## 6. 关系图

```
donkey init <PATH> [--force]
        │
        ▼
   cli.cli_client.main()  ──异常──▶ _EXCEPTION_TO_EXIT_CODE ──▶ 进程退出码
        │                                   ▲
        │ 成功                                │
        ▼                                    │
 core.api.init_workspace(path, name=None, force=False) ──▶ InitResult
        │
        ▼
 core.workspace.init.validate_init_request(path, name, force)
        │
        ├── check_path(path)        ──▶ 绝对 Path ／ PathNotFoundError(exit 1)
        ├── check_permission(path) ──▶ None ／ PathPermissionError(exit 2)
        └── 名称 = name（None / 空串 → abs_path 末段名；非空 → 该值）
        │
        ▼
   创建 workspace 根目录（exist_ok=True；MUST NOT 补建缺失的父目录——父目录缺失已在路径校验阶段按 FR-009 判为路径类错误）
```
