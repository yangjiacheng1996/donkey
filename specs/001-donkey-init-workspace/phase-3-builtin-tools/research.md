# 研究与技术决策（F001-P3 `builtin_tools`）

**输入**：[spec.md](spec.md)（105 条 FR / 24 条 SC / **3 段 Clarifications 共 16** 项决策 —— 1 轮 AI 推断 6 项 + 2 轮 Maintainer 裁决各 5 项）
**日期**：2026-10-23
**用途**：本文件是 `/speckit.plan` 的 **Phase 0 产出**，逐条记录"决策 / 理由 / 被否方案"，并给出**实测证据**（而非纸面推断）。[plan.md](plan.md) 的技术路线、契约与任务拆解 MUST 以本文件的决策编号为准。

> **编号纪律**：R-01 ~ R-20 为本 Phase 的决策编号，与 spec 的 FR / SC 编号**互不重叠**。plan / contracts / quickstart MUST 以 R-xx 引用决策，禁止复述决策内容（避免出现第 2 份副本而漂移）。

---

## R-01 · `@tool` 装饰器与 `from __future__ import annotations` 兼容 —— 实测通过

**决策**：模板 MUST 使用 `from langchain_core.tools import tool` 的 `@tool` 装饰器 + **类型注解 + docstring**；docstring **原样**成为工具描述（**不**剥离 `Args:` 段）；函数名即工具名。

**理由（实测证据）**：langchain-core **1.6.12**（本机 `.venv`）实测 ——

```text
tool name: read_file
description[:40]: 'Read the content of a file.\n\n    Args:\n '
args schema keys: ['path', 'start_line', 'num_lines']
invoke: /x|3|None          # 按参数名传参，缺省值生效
schema: {"properties": {"path": {...}, "start_line": {"default": 1, ...},
                        "num_lines": {"anyOf": [{"type":"integer"},{"type":"null"}], "default": null}}}
```

`from __future__ import annotations` 把注解变成字符串，**Pydantic 仍能解析**（`str | None` → `anyOf[integer, null]`）→ 模板用现代联合类型语法不会破坏 schema 生成。

**被否方案**：
- ❌ 自造工具协议（不用官方装饰器）—— 违反 spec FR-024，且未来引擎层挂载中间件时无法识别。
- ❌ 手工构造 `args_schema` —— 徒增维护面，且与官方装饰器的行为可能漂移。

---

## R-02 · 模板单元测试的**模块加载策略**（关键卡点）

**决策**：单元测试 MUST 采用「**渲染到临时工作区 → 把工作区根加入 `sys.path` → `importlib.import_module("tools.<模块>")` → teardown 从 `sys.modules` 摘除相关条目**」的模式；"顶层模块"（绝对导入回退）形态 MUST 由**独立用例**覆盖 —— 该用例把 **`tools/` 目录**（不是工作区根）加入 `sys.path` 后再导入。

**理由（实测证据）**：相对导入 `from .changes import ...` 需要**包上下文**（工作区根在 `sys.path`）；而回退路径 `from changes import ...` 需要 **`tools/` 目录本身**在 `sys.path` 上。实测：

```text
package import: from-package                      # 工作区根在 path → 相对导入生效
# 把 tools/mod_pkg.py 按路径当顶层模块加载（工作区根在 path、tools/ 不在）：
ImportError: attempted relative import with no known parent package
ModuleNotFoundError: No module named 'changes'  # ← 回退也失败
```

即：**只把工作区根加进 `sys.path` 时，绝对导入回退不可用**。这直接决定了测试夹具的形态，也解释了 spec FR-026 为什么要求"两种导入形态都支持"。

**teardown 必须清 `sys.modules`**：模块按名缓存，第二个用例若复用 `tools.filesystem` / `changes` 的名字就会拿到**第一个**工作区的产物 → 验收假绿。这正是 spec FR-062 对集成层要求的同一风险，在单元层同样成立。

**被否方案**：
- ❌ 用 `importlib.util.spec_from_file_location` 按路径加载 → 相对导入必失败（无包上下文），且回退路径同样失败（R-02 实测）。
- ❌ 在测试进程内 `sys.path.insert` 后直接 `import tools.X` 且**不**清 `sys.modules` → 跨用例污染（假绿）。

---

## R-03 · 网络工具 MUST 改用**流式**客户端 —— 与源提示词模板正文的必要偏离

**决策**：`tools/webfetch.py` MUST 用 `httpx.Client(trust_env=False, follow_redirects=True, timeout=...)` + `client.stream(...)` **逐块**读取响应体，MUST NOT 用 `httpx.request(...)` 顶层便捷函数。**客户端 MUST 以 `trust_env=False` 构造** —— httpx 的 `trust_env` 默认为 `True`，会隐式读取 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` / `NO_PROXY` / `SSL_CERT_FILE` / `.netrc` 来决定请求走向，既违反 spec FR-104（"工具 MUST 不读取任何环境变量"），也与 FR-089 的"MUST NOT 实现任何形式的地址范围限制（黑名单 / 白名单 / **代理** / 沙箱）"相悖（与 R-19 同一口径）。

**理由**：spec FR-089(b) 要求"**在读取响应体的过程中**持续守住上限"。`httpx.request()` 会**一次性把整个响应体读进内存**再返回 —— 对 chunked 编码（无 `Content-Length`）的响应，根本不存在"读取过程中守上限"的可能。流式路径实测可行：

```text
bounded: b'hello'
bounded too small: raised -> too large (declared)
follow_redirects param exists: True
```

**偏离登记**：源提示词 §4.3 的模板正文用的是 `httpx.request(...)`。本 Phase MUST 改用流式形态 —— **spec FR-089(b) 优先于模板正文的字面写法**，且这是**唯一**必须偏离源模板正文之处（其余偏离见 R-11 / R-12 / R-13）。

**被否方案**：
- ❌ 沿用 `httpx.request()` + 事后判大小 → 违反 FR-089(b)，超大响应会先撑爆内存。
- ❌ 用 `Content-Length` 单独把关 → chunked 响应无该头，仍会读爆内存。
- ❌ 沿用 httpx 默认的 `trust_env=True` → 工具行为被 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 等环境变量**隐式**改变（违反 FR-104），且实质上"实现了一个代理"。

---

## R-04 · HTTP 拦截库 = `pytest-httpx`（新增 **dev** 依赖）

**决策**：新增开发期依赖 `pytest-httpx>=0.35`（本机实测装入 **0.36.2**），MUST NOT 进 `[project].dependencies`（spec FR-080 —— donkey 自身的运行期依赖 MUST 仍恰为 **1** 个）。

**理由（实测证据）**：pytest-httpx 0.36.2 + httpx 0.28.1 下，**四类网络用例全部通过**（`httpx_mock` fixture 与 `client.stream()` 兼容）：

```text
test_ok        PASS   # 200 + body
test_stream_cap PASS  # chunked 响应 → 读取中触发上限 → ValueError
test_timeout   PASS   # add_exception(ReadTimeout) → httpx.TimeoutException 透传
test_non2xx    PASS   # 500 → httpx.HTTPStatusError
```

`test_stream_cap` 用 `content=iter([b"x"*65536]*200)` 制造无 `Content-Length` 的流式响应 → **恰好覆盖 FR-089(b) 的"读取过程中守上限"**。

**被否方案**：
- ❌ 用本地回环 HTTP 服务器替代 mock → 单元测试会依赖端口与线程，CI 上易 flaky；mock 更确定。

---

## R-05 · 行切分 MUST 用 `split("\n")`，MUST NOT 用 `splitlines()`

**决策**：模板里的一切行切分 MUST 以 `\n` 为**唯一**行界（末尾换行视为"结束最后一行"而非"开启一个空行"）；MUST NOT 使用 `str.splitlines()`。

**理由**：`str.splitlines()` 除 `\n` 外还会把 `\v` `\f` `\x1c` `\x1d` `\x1e` `\x85` `\u2028` `\u2029` **全部**当作行界 —— 与 OpenCode 的 `text.split("\n")` 语义不同，会让"行号前缀"与差异文本的行号**对不齐**，也会让"2000 行"的上限含义漂移。实测 `difflib.unified_diff` 在 `splitlines(keepends=True)` 下的输出与 OpenCode 的差异头一致：

```text
'--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n'
```

**被否方案**：❌ `splitlines()` —— 行界语义与 OpenCode 不一致（见上）。

---

## R-06 · 原子写的实现要点

**决策**：契约库的原子写 MUST 在**目标同目录**用 `tempfile.mkstemp(dir=目标父目录, prefix=".<名>.", suffix=".donkey-tmp")` 建临时文件 → 写入 → `flush()` + `os.fsync()` → `os.replace()` 落位；任何异常路径 MUST `unlink` 临时文件。

**理由（实测）**：`os.replace` 同目录替换在 POSIX 上是原子的（实测 `replace ok: b'new'`）；**跨目录**的替换不保证原子（POSIX 无 `renameat2` 跨目录保证，Windows 更严格）→ 临时文件 MUST 同目录。点开头的临时文件名不污染目录列表的默认视图（spec FR-008）。

**被否方案**：❌ `NamedTemporaryFile(delete=False)` + 手动拼接 → 名字不可控且默认落在系统临时目录（跨目录，破坏原子性）。

---

## R-07 · **契约库豁免于强制重置**的实现落点 —— 与 spec FR-070 的冲突及其解法

**决策**：豁免 MUST 落在 **`init_workspace_inner` 的步骤 ④**（编排层）：当 `force=True` **且**契约库已存在时，把契约库条目**从传给 `render_templates` 的条目列表中剔除**，并将该条目计入 `files_skipped`。`render_templates` 本身 **一字不改**。

**冲突登记（spec 内部张力）**：spec **FR-070** 要求"MUST NOT 修改 F001-P1 / F001-P2 已实现的模块（……模板渲染逻辑……）"，而 **FR-105** 要求契约库豁免于强制重置 —— 后者必然要动到渲染路径。**本 plan 的解法**：只改**编排层**（`init_workspace_inner`，6 行），**不动**通用渲染器（`render_templates`）→ P2 的"清单内文本条目先删后重建"通则对其余全部条目**原样成立**（spec FR-069 的要求），且不出现第二套渲染分支。

**计数口径（R-07 的直接推论，必须写进契约）**：

| 场景 | `files_created` | `files_skipped` | `templates_loaded` |
|---|---|---|---|
| 全新创建 | **48** | 0 | **54** |
| 二次 init（非强制） | 0 | **48** | 54 |
| **`--force`**（契约库已存在） | **47** | **1** | 54 |

**被否方案**：
- ❌ 在 `render_templates` 里加"条目级豁免"分支 → 改的是**通用渲染器**，通用规则被污染（FR-069 的反例），且违背 FR-070 的字面。
- ❌ 把契约库移出清单、改由专门代码路径写入 → 违反 FR-053（契约库 MUST 是清单条目）与 FR-055（同批生成）。

**已回填 spec（2026-10-23 `/speckit.analyze` 闭合）**：FR-070 已定点修订为"允许在 `init_workspace_inner` 步骤 ④ 增加**一条**条目级强制重置豁免（契约库）"—— spec 内部张力已消解。

---

## R-08 · 模板正文**无静态检查覆盖** → MUST 以编译自检兜底

**决策**：每个渲染出的 `.py` 文件 MUST 在单元测试里 `compile()` 成功（语法自检）；MUST NOT 依赖 ruff / mypy 覆盖模板正文。

**理由（实测）**：`templates/**.txt` **不是** `.py` 文件 → ruff 的 `check donkey/` 不扫它；mypy 的 `files = ["donkey"]` 只看 `.py` → **模板正文零静态检查覆盖**。而模板正文是**会被用户执行的 Python**（含真实的算法逻辑），语法错误会直接让用户的 workspace 不可用。

**被否方案**：❌ 把模板改成 `.py` 后缀 + 打包时改名 → 与 P2 已确立的"`<条目路径>.txt` 一一对应"规则冲突（FR-007），且清单里同一路径两种源文件会引入歧义。

---

## R-09 · `package-data` MUST NOT 改动

**决策**：MUST NOT 改 `pyproject.toml` 的 `[tool.setuptools.package-data]`。

**理由**：现有配置已是 `"donkey.core.workspace.templates" = ["**/*.txt", "**/*.json", ".gitignore.txt"]` —— `**/*.txt` 递归覆盖新增的 `templates/tools/*.txt` 与 `templates/skills/example/**` 下的 3 个 `.txt` → 自动被携带。

**被否方案**：❌ 追加显式路径 → 冗余，且未来新增条目会再次漏配。

---

## R-10 · 退出码 4 的常量**已存在**，本 Phase 只需激活

**决策**：`donkey/core/exit_codes.py` 的 `EXIT_CODE_BUILTIN_TOOL_GENERATION = 4` **已由 F001-P1 建档**（现文档串写的是"属 F001-P3（子段 3），本阶段不触发"）→ 本 Phase MUST 只把该文档串改为"本阶段启用"；另新增 1 个异常类 `BuiltinToolGenerationError` + 客户端映射表 **1 行**。

**理由**：避免出现第 2 份退出码常量定义（漂移源）。**本 Phase 改动总量 = 4 处**（异常类 1 个 + 退出码常量文档串 1 处 + 客户端映射 1 行 + **编排层条目级豁免 1 处** —— 与 contracts/cli-contract.md §1 的「3 处 + 1 处编排层豁免」及 contracts/exit-codes.md §6 的「全部改动 = 4 处」一致，见 R-07）—— 其中**客户端**改动 = 2 处（异常类 1 个 + 映射 1 行），与 spec FR-073 / FR-088 一致。

**被否方案**：❌ 新建常量 → 与既有定义重复。

---

## R-11 · 读算法统一为**一条**分页代码路径（与 OpenCode 的第 4 处有意偏离）

**决策**：读取 MUST 统一走"分页"一条代码路径（起始行缺省 1、行数上限 2000、字节预算 50 KiB）；"整份返回"= 该路径在**未发生截断**时的自然退化（spec FR-095 —— 即体积 ≤ 50 KiB **且行数 ≤ 2000** 且调用方未指定起始行 / 行数）。**行数上限无条件生效**（含小文件 —— 行数 > 2000 的文件**仍会被截断**并给出续读指针）。

**理由与偏离登记**：OpenCode 的**整份路径不套行数上限**（其 `MAX_READ_LINES` 只在分页路径生效）→ 一个"行数多但 ≤ 50 KiB"的文件（如 5000 行短行、30 KB）在 OpenCode 里会**整份返回 5000 行**（行数超限）。但 spec **FR-092** 明文要求"单次返回的行数上限为 2000 且单次返回的字节数上限为 50 KiB，**二者先到者生效**"（无条件）→ donkey MUST 截断。

**统一路径的收益**：① 消除"整份 / 分页"两套呈现逻辑的分支（少一处可错）；② 行为与 FR-092 完全一致；③ 代价（整份路径也套行数上限）是**收紧**，不会让模型拿到超预期体积的上下文。

**偏离清单更新**：spec FR-098 的"已知三处有意偏离" → 本 Phase 实为**五处**（新增本条 + R-12 + R-13）。**已回填 spec（2026-10-23 闭合）—— 见 spec FR-098 的"五处有意偏离"逐条登记**。

**被否方案**：❌ 照搬 OpenCode 的双路径（小文件不套行数上限）→ 与 FR-092 字面冲突，且违背"单一代码路径"的简洁性。

---

## R-12 · `list_dir` 的分页参数名与语义 —— `offset`（0 基）+ `limit`

**决策**：`list_dir(path, include_hidden=True, offset=0, limit=None)` —— `offset` 为 **0 基**（跳过 N 个条目）、`limit` 上限 **2000**；MUST NOT 改动既有参数 `include_hidden` 的语义。

**理由**：spec FR-097 只给了**语义**（"起始位置与条目数，条目数上限 2000"），**未给名字** → 属 plan 级决策。返回类型被冻结为 `list[str]`（MUST NOT 改 JSON）→ 没有 `next` 字段可依，调用方无法知道"还有多少" → `offset` 只能表达"跳过 N 个" → **0 基切片偏移**是 Python 惯例（1 基的"第几个条目"在无 `next` 的结构里语义别扭）。名字取 OpenCode 的 `offset`/`limit` 以与"照搬"主线一致。

**被否方案**：❌ 沿用 `read_file` 的 `start_line`/`num_lines` → 目录条目不是"行"，语义混淆；❌ 改成 JSON 以承载 `truncated`/`next` → 违反 FR-097 的类型冻结。

---

## R-13 · `list_dir` 的排序保持**源模板的代码点序**（与 OpenCode 的第 5 处有意偏离）

**决策**：`list_dir` 的结果 MUST 按**名称代码点序**排序（`sorted()`，与源提示词模板正文一致）；MUST NOT 改成 OpenCode 的"目录优先 + 本地化序"。

**理由**：① 源提示词的模板正文是权威给出的，其 `list_dir` 实现即 `sorted(...)`；② OpenCode 的"目录优先"是它的**呈现层（UI）**选择（面向人类看列表），而 donkey 的 `list_dir` 返回的是给**模型**用的名称列表，无 UI 场景；③ FR-015 / FR-097 冻结的是**返回类型**与**参数**，未规定顺序 → 顺序属实现细节，按源模板走。

**偏离清单更新**：并入 R-11 的五处偏离。**已回填 spec（2026-10-23 闭合）—— 见 spec FR-098 的"五处有意偏离"逐条登记**。

**被否方案**：❌ 照搬 OpenCode 的目录优先 + `localeCompare` → 与源模板正文不一致，且 `localeCompare` 的排序结果**依赖运行环境的 locale**，跨机器不稳定（CI 抖动风险）。

---

## R-14 · CI 工作流文件的最小内容与矩阵

**决策**：`.github/workflows/ci.yml` MUST 含 —— `pytest tests/`（全量）、`pytest tests/unit/ --cov=donkey.core --cov-fail-under=80`（覆盖率，MUST NOT 写入 pytest 全局 `addopts`，否则 e2e 单独跑时因不 import 业务代码会把覆盖率拉到 0 而误报）、`ruff check donkey/ tests/`、`mypy donkey/ tests/`；Python 版本矩阵 MUST 覆盖 **3.11 与 3.12**（`requires-python = ">=3.11"`）。

**理由**：spec FR-065 要求该文件含四类关键命令；宪法 §6.3 的临时例外 **E-01**（"F001-P1 与 F001-P2 均不交付 ci.yml"）的过期时间是**「F001-P3 结束前」** → 本 Phase MUST 交付（spec FR-065 / SC-001 的第 16 个断言）。

**被否方案**：❌ 只跑 `pytest tests/` 不跑覆盖率 → 宪法 §4.6 的 ≥80% 指标无人守护；❌ 把 `--cov` 写进 `addopts` → e2e 单独跑时误报失败（同 P2 的 R-13）。

---

## R-15 · P2 e2e **场景 11** 的改写口径

**决策**：P2 的 `test_scenario_11_no_builtin_tools_yet`（断言 `tools/` 下无 `filesystem.py` / `commandline.py` / `webfetch.py` / `__init__.py`）MUST 改写为 P3 的口径 —— "除本 Phase 的 **3 个内置工具 + 契约库 + 包初始化文件**这 5 个之外，`tools/` 下无其它内置工具文件"，且 `tools/README.md` 仍在。

**理由**：该场景编码的是 **P2 的阶段边界**（"还没有内置工具"），而那正是 P3 的交付物 → spec FR-068(e) 的"显式改写"要求。**P2 的 14 个场景其余 12 个 MUST 原样保持绿**（场景 1 与场景 11 **都**被改写 —— 见 R-16 与 spec FR-068；FR-069：MUST NOT 靠改红既有测试蒙混过关）。

**被否方案**：❌ 删除该场景 → 等于抹掉 P2 的边界记录（FR-069 的反例）。

---

## R-16 · P2 既有断言的改写口径（**5 组断言组** · 逐行核对两个真实测试文件）

**决策**：P2 的既有测试 MUST 按 spec FR-068 **显式改写**编码了**阶段边界**的断言组 —— **本条列举的是"断言组"，不是"断言语句的条数"**；每组内**具体断言语句的条数与位置 MUST 以 `tests/unit/test_template_skeleton.py` 与 `tests/e2e/phase/verify_phase_f001_p2.py` 的实际内容为准**（实施前 MUST **逐行核对**这两个文件，MUST NOT 以任何概括性计数为准，MUST NOT 遗漏任何一条会因本 Phase 交付而失效的断言）。五组口径如下：

| 组 | 位置 | P2 的断言 | P3 的正确口径 |
|---|---|---|---|
| (a) | 单测侧 | "清单条数 / 文件型条数 / 落地文件数 / **落地目录数**"的**绝对值断言** | **动态口径**（按加载器的实际返回值计算）+ 绝对值 **54 / 48 / 49 / 10** 作为**独立**断言保留（目录数 7 → 10 = 根 + 6 个清单目录 + 3 个 Skill Level 3 子目录） |
| (b) | 单测侧 | "工作区内无任何 `.py` 文件" + "内置工具文件**不存在**" | "**除本 Phase 新增的 6 个 `.py` 文件外**无其它"（`tools/` 下 5：3 工具 + 契约库 + 包初始化；Skill 第三层演示脚本 1）+ "这 4 个文件**已存在**"（P3 起它们是清单内条目，否定断言必然失败）；**同时 MUST 保留**"工作区内无**智能体入口文件**"这条**持久不变量**（口径按 FR-050 引用的**宪法 §6.3 例外 E-02 + §5 章 [D-19]** —— Skill 第三层演示脚本**获宪法授权**，**不计入**违例；FR-050 已于 2026-10-23 定点改写为引用口径，MUST NOT 自设豁免） |
| (c) | 单测侧 | 退出码集合 / 映射表取值集合 / 退出码 4 的在用性 | "退出码集合恰为 `{0,1,2,3}`" → `{0,1,2,3,4}`；"客户端异常映射表取值集合恰为 `{1,2,3}`" → `{1,2,3,4}`；"退出码 4 **不在**实际使用集合中" → "**已在**实际使用集合中"（P3 起 4 进入映射表）；"运行期依赖恰为 1 个"**保持不变** |
| (d) | 单测侧 | `tools/README.md` **源文件正文**的契约断言（断言其正文含"内置工具由后续阶段生成"） | 因 FR-056 的正文覆盖而失效 → 随新正文改写为"正文 MUST 含 P3 阶段实际写入的 **8 项**规范要点"（口径见 FR-044） |
| (e) | e2e 侧 | 场景 1 的 `templates=46 created=40 skipped=0` + 落地文件数 / 目录数；场景 11 的 4 条否定断言 | 场景 1 → `templates=54 created=48 skipped=0` + 落地文件数 49 / 目录数 10；场景 11 → "除本 Phase 的 **5** 个文件（3 工具 + 契约库 + `__init__.py`）外无其它内置工具文件"，`tools/README.md` 仍在 |

**另有两项 MUST NOT 改写**（P2 的**持久不变量**，其成立由本 Phase 的其他条款保证）：

- **e2e 场景 5** 的"渲染产物 MUST NOT 残留 `{{ … }}` 占位符"断言 → **保持原样、MUST NOT 改写** —— 其成立由 spec FR-049 的**占位记法约束**保证（第三层"模板文件"示例 MUST NOT 使用 `{{ … }}` 记法，改用 `<<title>>` / `<title>`）；
- 单测侧同源的"渲染结果中 MUST 无占位符残留"断言 → 同上，**保持原样**。

**逐行核对锚点（2026-10-23 实测，实施前 MUST 复核）**：

| 断言 | 位置 | 归属组 |
|---|---|---|
| `templates_loaded == 46` | `tests/unit/test_template_skeleton.py:737` / `:1130` / `:1454` —— **共 3 处，分属 3 个不同的用例函数**，MUST **全部**改写为 54，MUST NOT 只改第一处 | (a) |
| `files_created == 40` | `:738` | (a) |
| `len(files) == 41` | `:744` | (a) |
| `len(directories) + 1 == 7` | `:746` | (a) |
| `assert not (workspace / "tools" / name).exists()` ×4 | `:1099-1100` | (b) |
| `assert [p for p in workspace.rglob("*.py")] == []` | `:1104` | (b) |
| `used == {0, 1, 2, 3}` | `:1252` | (c) |
| `set(cli_client._EXCEPTION_TO_EXIT_CODE.values()) == {1, 2, 3}` | `:1261` | (c) |
| `assert exit_codes.EXIT_CODE_BUILTIN_TOOL_GENERATION not in used` | `:1266` | (c) |
| `assert "内置工具由后续阶段生成" in tools_doc` | `:817` | (d) |
| `templates=46 created=40 skipped=0` / 落地文件数 / 目录数 | `tests/e2e/phase/verify_phase_f001_p2.py:249` / `:272` / `:273` | (e) |
| 场景 11 的 4 条否定断言 | `tests/e2e/phase/verify_phase_f001_p2.py:515-516` | (e) |
| 场景 5 的无占位符残留断言 | `tests/e2e/phase/verify_phase_f001_p2.py:393-395` | **MUST NOT 改写** |

**理由**：spec FR-068 / FR-069 登记了**断言组**；FR-068 明确要求"具体断言语句的条数与位置 MUST 以两个测试文件的实际内容为准，MUST NOT 以任何概括性计数（如'7 条'）为准"—— 本轮修订已把 FR-068 里与真实测试文件不符的概括计数删除，故本决策**同步**改为按组登记 + 逐行核对口径。**持久不变量 MUST NOT 被削弱**（FR-069）：其中"渲染产物 MUST 无 `{{ … }}` 占位符残留"（F001-P2 契约 B12）已由本轮的 FR-049 / FR-056 占位记法约束显式登记。

**被否方案**：
- ❌ 让 P2 的断言"继续成立" → 与 P3 的交付物直接冲突，等于把 P2 改红。
- ❌ 以"共 N 条具体断言语句"之类的概括计数登记改写范围 → 计数与真实测试文件不符，必然漏项；FR-068 已明令禁止。
- ❌ 改写 e2e 场景 5 的占位符残留断言以"让断言更简洁" → 该断言是 P2 的**持久不变量**，MUST NOT 被削弱（FR-069）；其成立由 FR-049 的占位记法约束保证，MUST NOT 靠删断言兑现。

---

## R-17 · 命令输出的截断口径

**决策**：命令输出的截断 MUST 以 **stdout + stderr 合并后的文本**为计量对象（源模板本就合并：`completed.stdout + completed.stderr`），按 `\n` 切行（R-05），行数上限 **2000**、字节上限 **50 KiB**（R-18 的统一常量）；返回结果新增 `truncated` 布尔字段 + 末尾标记 `[showing lines 1-{已保留} of {总数}; full output not saved]`。

**理由**：源模板把 stderr 合并进 stdout（`stderr` 字段恒为空串）→ 计量对象只有一个，不存在"分别计量"的歧义。

**被否方案**：❌ 分别计量 stdout 与 stderr → 需要两个上限常量，且与合并后的实际返回文本不一致。

---

## R-18 · 统一输出上限常量

**决策**：**2000 行 / 50 KiB** 这一组数值 MUST 在读取侧与命令输出侧**共用**（spec FR-099 / FR-103）；因本 Phase MUST NOT 新增清单条目（FR-052），各工具模块 MAY 各自定义本地副本，但**单元测试 MUST 断言两侧数值相等**。

**理由**：OpenCode 由**引擎层**的同一套服务对所有工具输出施加同一组上限（`tool-output.ts` 的 `MAX_LINES` / `MAX_BYTES`）；donkey 是材料层无该服务 → 用"数值钉死 + 单测守护一致性"替代共享实现。

**被否方案**：❌ 新增一个 `tools/limits.py` 模块 → 违反 FR-052 的 8 条追加口径（清单条目数 MUST 保持 54）。

---

## R-19 · 网络工具的协议与 MIME 判定

**决策**：① **协议白名单** —— 解析 URL 后 `scheme` MUST ∈ `{http, https}`（大小写不敏感），否则报错；② **MIME 白名单** —— `Content-Type` 的媒体类型 MUST ∈ `text/*` ∪ {`application/json`, `application/xml`, `application/xhtml+xml`}，否则报错（图片与 PDF 一律拒绝）；③ **非 2xx** MUST 报错（MUST NOT 返回正文）；④ `timeout > 120` MUST 在**发请求前**报错；⑤ **客户端 MUST 以 `trust_env=False` 构造**（`httpx.Client(trust_env=False, ...)`）—— httpx 默认的 `trust_env=True` 会隐式读取代理 / 证书环境变量，违反 spec FR-104（"工具 MUST 不读取任何环境变量"），并与 FR-089 的"MUST NOT 实现…代理"相悖（与 R-03 同一口径）。

**理由**：逐条对应 spec FR-089(a)(c)(d) 与 FR-037。② 的白名单比"仅 text/*"略宽 —— 因为 JSON 是最常见的可读响应形态；OpenCode 的 `Mime.isTextual` 亦覆盖 JSON。⑤ 的理由见 R-03 —— httpx 的 `trust_env=True` 会让"用户本机的代理设置"**隐式**改变工具行为，与 spec FR-104 的"智能体不允许被环境变量所影响"原则直接冲突，且 donkey v1 无任何代理相关能力（属引擎层职责）。

**被否方案**：
- ❌ 只允许 `text/*` → JSON 接口全部被拒，实用性差。
- ❌ 沿用 httpx 默认的 `trust_env=True` → 同 R-03，违反 FR-104 且实质"实现了一个代理"。

---

## R-20 · e2e 的网络拦截 MUST 与导入同处**一个子进程**（FR-067）

**决策**：e2e 场景 5 MUST 在子进程内**先**打桩 `httpx.Client.send`，**再**导入并调用工作区的 `tools.webfetch`；MUST NOT 在测试进程内导入工作区产物（模块按名缓存 → 假绿，spec FR-062 / FR-066）。

**理由（实测）**：pytest-httpx 的 `httpx_mock` fixture 只对**当前进程**生效（它 monkeypatch 当前进程的 `httpx` 模块对象）→ 子进程不受影响 → 源提示词 §6.5 的"mock 与 import MUST 同处一个子进程"**只能**靠子进程内自行打桩实现。实测可行：

```text
# 在工作区目录内执行 python -c "..."
$ python -c "import httpx
def fake_send(self, request, **kwargs):
    return httpx.Response(200, text='mocked body', request=request)
httpx.Client.send = fake_send
from tools.webfetch import fetch_url
print(fetch_url.invoke({'url': 'https://example.com'}))"
{"status_code": 200, "body": "mocked body"}   # （样本节选 —— 实际返回还含 headers / url 两个字段，见 FR-039）
```

**子进程必须用 `python -c`**（MUST NOT 用脚本文件）：`-c` 会把**当前工作目录**加入 `sys.path`，脚本文件则加入**脚本所在目录** → 后者找不到工作区的 `tools` 包（实测 `ModuleNotFoundError: No module named 'tools'`）。

**单元测试的网络用例**（FR-058 的四类）MUST 在**进程内**用 `pytest-httpx` 的 `httpx_mock` fixture 覆盖（R-04 实测四类全通）—— 单元层不涉及"跨工作区模块缓存"问题（每个用例独立渲染 + teardown 清 `sys.modules`）。

**被否方案**：
- ❌ 单元层也用子进程 → 失去 `httpx_mock` 的确定性，且慢 10 倍。
- ❌ e2e 用本地回环 HTTP 服务器 → 需端口与线程，CI 易 flaky；打桩更确定。

---

## 待回填 spec 的清单 —— **已于 2026-10-23 全部闭合**（`/speckit.analyze` 修正轮 + 本轮 spec 定点修订）

> ✅ **状态：已闭合**。下列 5 项已在 `/speckit.analyze` 的修正轮中直接写入 spec（FR-070 的定点修订 / FR-098 的「五处偏离」并逐条列明 / FR-092 的整份路径口径登记 / FR-097 的分页参数名写实 / FR-069 的实现口径）；**第 6 项**是本轮（`/speckit.analyze` 之后的 spec 定点修订轮）新增的 6 处设计缺陷修复。本表**保留**作为决策溯源，不再是待办。

| # | 事项 | 依据 |
|---|---|---|
| 1 | **FR-070** 需定点修订：允许在 `init_workspace_inner` 步骤 ④ 增加**一条**条目级强制重置豁免（契约库） | R-07 |
| 2 | **FR-098** 的"已知三处有意偏离" → 实为**五处**（新增：整份路径也套行数上限 / `list_dir` 排序为代码点序） | R-11 / R-13 |
| 3 | **FR-092** 的"双上限无条件生效"与 OpenCode 整份路径的差异需在 spec 侧显式登记 | R-11 |
| 4 | **FR-097** 的 `list_dir` 分页参数名与语义（`offset` 0 基 / `limit` ≤ 2000）需写实 | R-12 |
| 5 | **FR-069** 的"唯一一处通则例外"已在 spec 中登记，实现口径由 R-07 承载（计数 47/1/54） | R-07 |
| 6 | **本轮 spec 定点修订的 6 处设计缺陷**：**A-1** FR-095 补"行数 ≤ 2000"限定（消除与 FR-092 / FR-098(d) 的字面冲突）/ **A-2** FR-028 + FR-030 澄清命令工具的**入参形态**（`command: str`，"显式参数数组"仅指**执行形态** `shell=False`）/ **A-3** FR-049 + FR-056 补第三层模板示例的**占位记法约束**（禁用 `{{ … }}`）+ FR-069 补登"渲染产物 MUST 无 `{{ … }}` 占位符残留"（契约 B12）/ **A-4** FR-068 + SC-002 改写为**按断言组登记 + 以两个真实测试文件的实际内容为准**（删除概括性计数（如「7 条」）式的表述，补齐 3 处 `templates_loaded == 46` / 落地目录数 10 / 映射表 `{1,2,3}`→`{1,2,3,4}` / 退出码 4 在用性 / `tools/README.md` 正文契约断言 / e2e 场景 5 MUST NOT 改写）/ **A-5** Key Entities 末条改为「**已知缺口与风险登记**」（变更记录契约侧 2 条 + 读取与媒体侧 2 条，共 4 条）/ **A-6** FR-105 整条**原样**移至 FR-104 之后（编号不变） | **本轮 spec 定点修订**（R-11 读取口径 / R-16 断言组口径 / R-15 场景计数） |
