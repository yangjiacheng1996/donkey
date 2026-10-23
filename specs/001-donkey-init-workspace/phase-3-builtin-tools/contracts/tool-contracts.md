# 契约：内置 `@tool` 签名与返回形状（F001-P3）

**版本**：v1（本 Phase 首版）
**所有者**：`donkey/core/workspace/templates/tools/{filesystem,commandline,webfetch}.py.txt`
**上游**：[spec.md](../spec.md) FR-013 ~ FR-042 / FR-089 ~ FR-103；[research.md](../research.md) R-01 ~ R-20

> **本文件是"渲染进用户工作区后的公开契约面"** —— 用户自写的工具 MUST 与内置工具遵循同一形态（spec FR-045）。
> **只增不改**：既有字段的名字与语义 MUST 冻结；新增 MUST 以追加方式出现。

---

## 1. 通用约定

| 约定 | 内容 |
|---|---|
| 装饰器 | `from langchain_core.tools import tool`（官方内置，R-01 实测） |
| 工具名 | = 函数名（`read_file` / `write_file` / …） |
| 工具描述 | = docstring **原文**（**不**剥离 `Args:` 段） |
| 参数 schema | 由类型注解自动生成（`str \| None` → `anyOf[integer, null]`） |
| 调用 | `tool.invoke({"参数名": 值})` |
| 路径解析 | 相对路径 → 工作区根；绝对路径 → 原样（白名单由用户自管） |
| 环境变量 | **MUST NOT** 读取（spec FR-104） |
| 异常 | 具体的内置异常类型（`FileNotFoundError` / `IsADirectoryError` / `PermissionError` / `tools.changes.FileChangedError`） |

**统一输出上限**（R-18，两侧共用同一组数值）：

```text
行数上限 = 2000        字节上限 = 50 KiB        单行字符上限 = 2000（仅读取侧）
```

---

## 2. `tools/filesystem.py` —— 7 个 `@tool`

### 2.1 `read_file(path: str, start_line: int = 1, num_lines: int | None = None) -> str`

读取文件（**只读**）。

**返回**：**呈现文本**（不是纯正文）——

```text
Read file {调用方传入的路径}, lines {起始}-{结束}      ← 首行：页范围说明头
{行号}: {行内容}                                       ← 每行带行号前缀
...
[Output truncated. Continue reading with offset: N]      ← 仅截断时出现
```

- 空内容 → `Read file {路径}, 0 lines`
- 单行超 2000 字符 → 该行截断并附 `... (line truncated to 2000 chars)`
- 行数上限 **2000**、字节上限 **50 KiB**，**先到者生效**（**无条件**，含小文件 —— R-11）
- **"整份返回"= 分页代码路径在未发生截断时的自然退化**（spec FR-095）—— 行数上限**无条件**生效：体积 ≤ 50 KiB **但行数 > 2000** 的文件**仍会被截断**并给出续读指针（`[Output truncated. Continue reading with offset: N]`）；MUST NOT 以"体积小"为由整份返回超限行数
- 二进制（含 NUL 字节）→ **报错**，MUST NOT 返回乱码
- 图片 / PDF → **报错**（多模态附件属引擎层，spec FR-096）
- 目标是**目录** → 按目录分支呈现（见 §2.8）
- 起始行越界 → **报错**

**异常**：`FileNotFoundError` / `IsADirectoryError` / `PermissionError` / 解码错误（非法 UTF-8 → 容错替换，MUST NOT 抛）

### 2.2 `write_file(path: str, content: str, dry_run: bool = False, include_previous: bool = False, expected_hash: str | None = None) -> str`

原子写入（**改文件**）。

**返回**（JSON 文本）：

```json
{
  "path": "/abs/path",
  "action": "create" | "update",
  "bytes_written": 12,
  "applied": true,
  "change": { …变更记录… }
}
```

- `dry_run=True` → **零磁盘副作用**（不建父目录 / 不写 / 不留临时文件），返回 `applied=false` 的完整变更记录
- `include_previous=True` → 变更记录附 `previous_content`（超 256 KiB 则改为 `previous_content_truncated=true`）
- `expected_hash` 不匹配 → 抛 `tools.changes.FileChangedError`，**不写入**
- 目标已存在且是**目录** → 抛 `IsADirectoryError`
- 自动创建父目录

### 2.3 `copy_file(src: str, dst: str, dry_run: bool = False, expected_hash: str | None = None) -> str`

原子复制（**改文件**）。返回 JSON：`{src, dst, action: "copy", applied, change}`。
`change` 描述**目标路径**，并含 `src` / `src_rel_path`。可复制文件元数据（失败 MUST 被忽略）。

### 2.4 `move_file(src: str, dst: str, dry_run: bool = False, expected_hash: str | None = None) -> str`

移动（**改文件**）。返回 JSON：`{src, dst, action: "move", applied, change}`。
`change` 描述**目标路径**，并含 `src` / `src_rel_path`。源不存在 → `FileNotFoundError`。

### 2.5 `delete_file(path: str, include_previous: bool = False, dry_run: bool = False, expected_hash: str | None = None) -> str`

删除文件或目录树（**改文件**）。返回 JSON：

```json
{ "path": "/abs/path", "type": "file" | "directory", "action": "delete", "applied": true, "change": { … } }
```

- 目录按**目录粒度**记录（不枚举内部逐文件差异）
- `include_previous=True` 且目标是**文件** → 变更记录附 `previous_content`

### 2.6 `list_dir(path: str, include_hidden: bool = True, offset: int = 0, limit: int | None = None) -> list[str]`

列出目录的直接子项（**只读**）。

- 返回**名称列表**（`list[str]`，MUST NOT 改成 JSON —— spec FR-097）
- `include_hidden=False` → 过滤点开头的条目（默认值 `True` = 旧行为）
- `offset` = **0 基**跳过 N 个条目；`limit` = 最多返回多少条（上限 **2000**）（R-12）
- 排序：**名称代码点序**（`sorted()`，与源模板一致 —— R-13；**不**采用 OpenCode 的"目录优先 + 本地化序"）
- 返回类型被冻结 → **不承载**"已截断 / 续读位置"字段；续读指引由 `read_file` 的目录分支 + 工具说明文字承载

### 2.7 `stat(path: str, with_hash: bool = False) -> dict[str, Any]`

取元数据（**只读**）。返回**映射**（MUST NOT 改成 JSON 文本）：

```json
{ "size": 123, "mtime": 1700000000.0, "is_file": true, "is_dir": false, "exists": true }
```

- `with_hash=True` 且是普通文件 → 追加 `"sha256": "sha256:<hex>"`（**与契约库同格式**，带前缀）
- 路径不存在 → 返回 `exists: false` 的映射（MUST NOT 抛异常）

### 2.8 `read_file` 的目录分支

目标是目录时，`read_file` 返回：

```text
Read directory {调用方传入的路径}, entries {起始}-{结束}
{条目名}
...
[Output truncated. Continue reading with offset: N]     ← 仅截断时出现
```

---

## 3. `tools/commandline.py` —— 1 个 `@tool`

### `run_shell(command: str, timeout: int = 60, cwd: str | None = None) -> str`

执行一条命令（**每次新建进程**）。

**返回**（JSON 文本）：

```json
{
  "stdout": "…合并了 stdout 与 stderr…",
  "stderr": "",
  "returncode": 0,
  "timed_out": false,
  "cwd": "/abs/workspace",
  "argv": ["echo", "hello"],
  "truncated": false
}
```

| 字段 | 语义 |
|---|---|
| `stdout` | stdout 与 stderr **合并**后的文本（源模板既有形态，MUST NOT 改） |
| `stderr` | 恒为空串（源模板既有形态） |
| `returncode` | 退出码；**超时**时为 `-1` |
| `timed_out` | 是否超时（**超时不抛异常** —— spec FR-031） |
| `cwd` | 实际工作目录（**默认 = 工作区根**，MUST NOT 依赖进程 cwd） |
| `argv` | 实际执行的参数数组（由 `shlex.split` 拆分） |
| `truncated` | **新增**字段：输出是否被截断 |

**截断行为**（R-17）：以 stdout+stderr 合并文本为计量对象，行数上限 **2000**、字节上限 **50 KiB**（与读取侧同一组数值）→ 截断时追加标记：

```text
[showing lines 1-{已保留行数} of {总行数}; full output not saved]
```

**完整输出 MUST NOT 落盘**（spec FR-101）—— 模型取剩余部分自行改跑更窄的命令。

**已知缺口（MUST 写进 docstring）**：命令造成的文件副作用**不进**变更记录（命令绕过工具的写路径）—— 引擎层将来靠工作区快照对账。

**入参形态 vs 执行形态**（spec FR-028 / FR-030 —— 二者 MUST NOT 混淆）：

| 维度 | 口径 |
|---|---|
| **入参形态** | 命令以**单个命令字符串**传入（`command: str`）—— 调用方 **MUST NOT** 传入 `list[str]` |
| **执行形态** | 工具内部按 POSIX 引号规则把该字符串拆成**参数数组**，再**不经 shell** 直接执行（`shell=False`）—— "显式参数数组"指的是**执行形态**，**不**意味着调用方传入数组 |
| **拆分规则** | `shlex.split`（返回的数组即 `argv` 字段） |
| **注入防护** | 命令解释器被完全绕开（`shell=False`）→ 从源头避免命令注入 |

**不支持**：管道 / 重定向（命令被显式拆成参数数组、不经命令解释器 —— 本 Phase MUST NOT 承诺支持；MUST 如实回报执行失败，MUST NOT 崩溃）。

---

## 4. `tools/webfetch.py` —— 1 个 `@tool`

### `fetch_url(url: str, method: str = "GET", headers: dict[str, str] | None = None, timeout: int = 30) -> str`

发起一次 HTTP 请求（**只读**）。**返回**（JSON 文本）：

```json
{ "status_code": 200, "body": "…", "headers": { … }, "url": "https://…（重定向后的最终地址）" }
```

**四道边界**（spec FR-089，R-19）：

| 边界 | 行为 |
|---|---|
| 协议白名单 | `scheme` MUST ∈ {`http`, `https`}；否则**报错**（MUST NOT 发起请求） |
| 响应体上限 **5 MiB** | 先看 `Content-Length` 声明，再在**读取过程中**持续守住上限；超限**报错**（MUST NOT 先读进内存） |
| 非文本 MIME 拒绝 | 文本 MIME = `text/*` ∪ {`application/json`, `application/xml`, `application/xhtml+xml`}；非文本 MIME 一律**报错**（图片 / PDF 一律拒绝） |
| 非 2xx | **报错**，MUST NOT 返回正文 |

**其它约束**：
- **说明文字（docstring）MUST 逐条写明**四道边界及其触发后果（spec FR-090 / SC-021(b)）—— 协议白名单（http / https）/ 响应体上限（5 MiB）/ 非文本 MIME 拒绝 / 非 2xx 报错；MUST NOT 保留任何与实际行为不符的措辞
- 超时上限 **120 秒**：`timeout > 120` MUST 在**发请求前**报错（spec FR-037）
- 默认超时 **30 秒**（spec FR-038）
- MUST 用**流式**读取（`httpx.Client` + `client.stream(...)`）—— R-03
- 客户端 MUST 以 **`trust_env=False`** 构造（`httpx.Client(trust_env=False, ...)`）—— httpx 默认的 `trust_env=True` 会隐式读取代理 / 证书环境变量，违反 spec FR-104（"工具 MUST 不读取任何环境变量"），并与 FR-089 的"MUST NOT 实现…代理"相悖（R-03 / R-19）
- **不**持久化会话凭据（每次新建连接）
- **不**做 HTML → Markdown 转换（保持原始正文 —— spec FR-098 的第三处偏离）
- 网络异常（超时 / 网络 / 协议）**透传**给调用方（MUST NOT 被吞掉）—— 与 `run_shell` 的"超时返回标记"构成**有意的不对称**（spec FR-041）
- **只读** → MUST NOT 产生变更记录、MUST NOT 落盘

---

## 5. `tools/changes.py` —— 契约库（**0 个 `@tool`**）

**公开契约面**（只增不改 —— spec FR-002）：

```python
CHANGE_RECORD_VERSION = 1
MAX_DIFF_BYTES      = 64 * 1024
MAX_PREVIOUS_BYTES  = 256 * 1024

class FileChangedError(RuntimeError): ...

def workspace_root() -> Path
def resolve_path(path: str) -> Path
def relative_path(path: Path) -> str
def sha256_bytes(data: bytes) -> str
def read_existing_bytes(path: Path) -> bytes | None
def atomic_write_bytes(path: Path, data: bytes) -> None
def build_unified_diff(old_text: str, new_text: str, rel: str) -> str
def build_change_record(action: str, path: Path, previous_bytes: bytes | None,
                        new_bytes: bytes | None, *, src: Path | None = None,
                        include_previous: bool = False) -> dict[str, Any]
def check_expected_hash(path: Path, expected_hash: str | None) -> None
```

**硬性约束**：

| 约束 | 内容 | 依据 |
|---|---|---|
| **0 个 `@tool`** | 它是契约底座，MUST NOT 被模型直接调用 | spec FR-001 / FR-091 |
| **零框架导入** | 纯标准库 → 未来的工具扫描器对其零歧义 | spec FR-011 |
| **无 `__main__`** | 宪法 N-01 | spec FR-001 |
| **工作区根恒定** | 由自身位置推导；MUST **NOT** 读环境变量 | spec FR-002 / FR-104 |
| **指纹按原始字节** | MUST NOT 先解码再编码 | spec FR-006 |
| **原子写** | 同目录临时文件 → `fsync` → `os.replace`；异常路径 MUST 清临时文件 | spec FR-008 / R-06 |
| **原子写建父目录** | 保持"写文件自动建父目录"的语义 | spec FR-009 |
| **差异头用相对路径** | `a/<rel>` / `b/<rel>`；工作区外回退为绝对路径 | spec FR-007 |
| **行界只用 `\n`** | MUST NOT 用 `splitlines()` | R-05 |

**变更记录的字段集**：见 [change-record-contract.md](change-record-contract.md)。

---

## 6. `tools/__init__.py` 与 `tools/README.md`

### `tools/__init__.py`

**最小占位**：仅 docstring，MUST 说明 —— 该包由初始化阶段自动生成 / 3 个内置工具模块位于此 / **契约库位于此且不含任何工具函数** / 用户可自行追加工具模块。**MUST NOT** 在其中定义任何工具函数（spec FR-043）。

### `tools/README.md`

MUST 覆盖 8 项（spec FR-044）：（a）工具装饰器的官方导入位置；（b）函数必须有 docstring；（c）路径白名单由用户自管；（d）推荐的超时配置；（e）错误处理建议；（f）**工作区根的推导方式** + 不读环境变量；（g）**契约库与用户自写工具是一套的** + 强制重置不覆盖契约库 + 重置前先备份；（h）**网络工具需自行安装 HTTP 客户端库**。

MUST 含"改文件的工具怎么写（变更记录契约）"小节（6 条 —— spec FR-045），并 MUST 明确说明契约库**是契约库、不是工具**（FR-046）。

---

## 7. 用户自写工具的契约要求

| 要求 | 内容 |
|---|---|
| 装饰器 | 官方 `@tool` + docstring |
| 改文件 | MUST 经 `tools.changes` 的原子写 + MUST 生成变更记录并放进返回 JSON 的 `change` 字段；MUST **提供**期望指纹乐观锁；**建议**提供预览开关 |
| 路径基准 | 相对路径 MUST 以工作区根为基准（用契约库的 `resolve_path`） |
| 环境变量 | MUST NOT 读取以决定行为 |
| 记录格式 | MUST 用契约库，**MUST NOT** 自造第二套指纹 / 差异逻辑 |
