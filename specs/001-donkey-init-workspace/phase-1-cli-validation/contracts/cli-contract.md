# 契约：命令行接口（`donkey init`）

**版本**：v1（F001-P1 冻结）
**所有者**：`donkey/cli/cli_client.py`
**上游**：`spec.md` FR-001 ~ FR-004、FR-018 ~ FR-023、FR-027；澄清决策 1 / 2 / 6

---

## 1. 命令面

```
donkey init <PATH> [--force]
```

| 参数 | 形态 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `<PATH>` | 位置参数 | 是 | — | workspace 目录路径；绝对或相对均可，相对路径以进程工作目录为解析基准 |
| `--force` | 布尔开关 | 否 | 假 | 强制重置已存在模板文件。**P1 仅记录并回显**，不触发任何删除 / 重置（属 F001-P2） |

**不存在其它参数**（spec FR-003）：v1 **不提供** `--name` 或任何等价的独立命名参数——workspace 名称恒取路径末段。

```
$ donkey init --help
usage: donkey init [-h] [--force] path
```

## 2. 退出码

| 退出码 | 触发条件 | 输出流向 |
|---|---|---|
| `0` | 成功（目录已就位） | 结果摘要 → stdout |
| `1` | 路径 / 输入不合法（父目录不存在、非法字符、根路径、空路径、目标不是目录……）；**参数用法错误**（缺子命令、缺必填参数、未知参数） | 错误信息 → stderr |
| `2` | 权限不足（写位 / 执行位 / 读位缺失） | 错误信息 → stderr |
| `3` / `4` / `5-10` | 本 Phase **不触发** | — |

**语义唯一性**：`1` = 输入不合法，`2` = 权限不足。参数解析器的默认失败码 `2` MUST 被改写为 `1`（实现见 `research.md` R-01）。

## 3. 输出契约

### 3.1 成功（stdout，单行）

```
[donkey init] workspace=<绝对路径> name=<名称> force=<true|false> templates=0 created=0 skipped=0
```

| 字段 | 取值 | 约束 |
|---|---|---|
| `workspace` | 绝对路径 | MUST 与实际创建 / 复用的目录一致 |
| `name` | 路径末段 | MUST 等于 `workspace` 的末段名 |
| `force` | `true` / `false` | 本次是否带 `--force` |
| `templates` / `created` / `skipped` | 整数 | P1 恒为 `0` |

### 3.2 失败（stderr，单行起头）

```
[donkey init] 失败：<人类可读原因>
```

错误信息 MUST 包含可识别标识，便于脚本判断失败类别（spec FR-019）：

- 路径类：含错误类别名（`PathNotFoundError`）或"父目录不存在"等关键词；
- 权限类：含错误类别名（`PathPermissionError`）或"权限"字样，**且同时指明缺失的权限种类与对应路径**（spec FR-015）；
- 用法错误：含用法提示（usage）。
- 三类面向用户的失败（路径类 / 权限类 / 用法错误）消息 MUST 同时包含**一条用户可执行的下一步**（spec FR-019 / SC-012）；未登记异常子类的内部兜底消息不在此约束内。

## 4. 行为契约

| # | 规则 | 依据 |
|---|---|---|
| C-01 | 校验通过后创建 workspace 根目录；目标已存在**不是错误** | FR-008 |
| C-02 | MUST NOT 自动创建缺失的父目录 | FR-009 |
| C-03 | 名称恒为解析后路径的末段名；末段名为空（根路径）→ 退出码 `1` | FR-003 / FR-012 |
| C-04 | 幂等：重复执行不报错、不破坏任何已存在内容（`--force` 同样不重置） | FR-028 |
| C-05 | 本 Phase MUST NOT 加载模板清单、MUST NOT 写任何模板文件 | FR-029 |
| C-06 | 失败时 MUST NOT 产生未捕获的异常堆栈 | FR-030 |

## 5. 入口点

| 入口 | 形式 | 要求 |
|---|---|---|
| 控制台脚本 | `donkey ...` | MUST 存在（`[project.scripts]`） |
| 模块入口 | `python -m donkey ...` | MUST 存在，与控制台脚本行为完全一致 |

两条入口 MUST 产生**完全相同的退出码与输出**（`research.md` R-02 已验证：`sys.exit(main())` 的整型返回值原样成为进程退出码）。

## 6. 调用示例

```bash
# 成功
$ donkey init ~/agents/my-agent
[donkey init] workspace=/home/u/agents/my-agent name=my-agent force=false templates=0 created=0 skipped=0

# 路径类失败（退出码 1）
$ donkey init /nonexistent/parent/ws
[donkey init] 失败：PathNotFoundError: 父目录不存在：/nonexistent/parent
$ echo $?
1

# 权限类失败（退出码 2）
$ chmod 555 /tmp/ro && donkey init /tmp/ro/ws
[donkey init] 失败：PathPermissionError: 缺少写权限：/tmp/ro
$ echo $?
2

# 用法错误（退出码 1，非 2）
$ donkey init
usage: donkey init [-h] [--force] path
donkey init: error: the following arguments are required: path
$ echo $?
1
```
