# 契约：模板清单与模板源文件（F001-P3）

**版本**：v1（F001-P2 建档 46 条 → 本 Phase 追加 **8** 条，累计 **54** 条）
**所有者**：`donkey/core/workspace/templates/manifest.json` + `donkey/core/workspace/templates/**.txt`
**上游**：[spec.md](../spec.md) FR-052 ~ FR-057 / FR-068；[research.md](../research.md) R-05 / R-08 / R-09 / R-13 / R-15 / R-16

> **追加纪律**：F001-P2 已有的 46 条 **MUST NOT** 修改路径与格式值；本 Phase 只在 `entries` 数组**末尾追加** 8 条（spec FR-052）。
> **例外**：本 Phase **覆盖** 2 个**已存在**的源文件正文（`tools/README.md.txt` / `skills/example/SKILL.md.txt`）—— **不新增**对应条目（spec FR-056）。

---

## 1. 清单文件

**路径**：`donkey/core/workspace/templates/manifest.json`　**编码**：UTF-8，无 BOM
**打包**：`pyproject.toml` 的 `[tool.setuptools.package-data]` 已含 `"**/*.txt"` → 本 Phase 新增的 8 个 `.txt`（位于 `templates/tools/` 与 `templates/skills/example/**` 子目录）**自动被携带**，MUST NOT 改动该配置（R-09）。

---

## 2. 追加的 8 条（追加到 `entries` 数组末尾）

```json
{ "path": "tools/__init__.py", "format": "python" },
{ "path": "tools/changes.py", "format": "python" },
{ "path": "tools/filesystem.py", "format": "python" },
{ "path": "tools/commandline.py", "format": "python" },
{ "path": "tools/webfetch.py", "format": "python" },
{ "path": "skills/example/reference/example.md", "format": "markdown" },
{ "path": "skills/example/scripts/example.py", "format": "python" },
{ "path": "skills/example/templates/example.md", "format": "markdown" }
```

**条数核对**：

| 项 | 数 |
|---|---|
| F001-P1 建档 | 3 |
| F001-P2 追加 | 43 |
| **F001-P3 追加** | **8** |
| **累计** | **54** = 45 个文本型 + 3 个 sqlite3 型 + 6 个目录型 |
| 其中**文件型**（计入 created / skipped） | **48** |
| 磁盘落地文件 | **49**（48 个清单文件 + 1 份工作区清单） |
| 磁盘目录 | **10**（根 + 6 个清单目录 + 3 个 Skill Level 3 子目录） |

**`format` 取值**：沿用 P2 的 7 种 —— `markdown` / `toml` / `json` / `python` / `text` / `directory` / `sqlite3`；MUST NOT 引入新取值（spec FR-054）。**本 Phase 首次使用 `format: "python"`**（P2 的清单里该格式值**零条目**，见 [phase-2 的 template-manifest.md §2.3](../../phase-2-template-skeleton/contracts/template-manifest.md)）。

**条目顺序无语义**：渲染 MUST NOT 依赖条目顺序（写文件前先确保父目录存在）—— P2 的既有规则，本 Phase 沿用。

---

## 3. 新增的 8 个模板源文件

**源路径规则**：`templates/<条目路径>.txt`（与条目路径一一对应，P2 的 FR-007）。

| # | 源文件 | 落地路径 | 内容契约 |
|---|---|---|---|
| 1 | `templates/tools/__init__.py.txt` | `tools/__init__.py` | 仅 docstring；说明 3 个内置工具模块 + **契约库（0 个工具函数）** + 用户可自行追加。**MUST NOT** 定义任何工具函数 |
| 2 | `templates/tools/changes.py.txt` | `tools/changes.py` | 变更记录契约库 —— 见 [change-record-contract.md](change-record-contract.md) §5 与 [tool-contracts.md](tool-contracts.md) §5。**0 个 `@tool`**、**零框架导入**、**无 `__main__`** |
| 3 | `templates/tools/filesystem.py.txt` | `tools/filesystem.py` | 7 个 `@tool` —— 见 [tool-contracts.md](tool-contracts.md) §2 |
| 4 | `templates/tools/commandline.py.txt` | `tools/commandline.py` | 1 个 `@tool` —— 见 [tool-contracts.md](tool-contracts.md) §3 |
| 5 | `templates/tools/webfetch.py.txt` | `tools/webfetch.py` | 1 个 `@tool` —— 见 [tool-contracts.md](tool-contracts.md) §4。**MUST 用流式读取**（R-03） |
| 6 | `templates/skills/example/reference/example.md.txt` | `skills/example/reference/example.md` | Level 3 参考文档示例 |
| 7 | `templates/skills/example/scripts/example.py.txt` | `skills/example/scripts/example.py` | Level 3 脚本示例 —— **MUST 保留** `if __name__ == "__main__": sys.exit(main())` 入口块（授权来源：宪法 §6.3 例外 E-02 + §5 章 [D-19]，spec FR-050 MUST **引用**该例外、MUST NOT 自设豁免） |
| 8 | `templates/skills/example/templates/example.md.txt` | `skills/example/templates/example.md` | Level 3 模板文件示例 |

---

## 4. 覆盖的 2 个既有源文件（**不新增条目**）

| 源文件 | 落地路径 | 覆盖内容 |
|---|---|---|
| `templates/tools/README.md.txt` | `tools/README.md` | P2 的占位正文 → **完整工具开发规范**（8 项必备内容 + "改文件的工具怎么写（变更记录契约）"小节 + "契约库不是工具"声明 —— spec FR-044 / FR-045 / FR-046） |
| `templates/skills/example/SKILL.md.txt` | `skills/example/SKILL.md` | P2 的占位 Level 2 → **完整 Level 2 正文**（三层模型说明 + 按需使用 Level 3 的指引 + "示例路径以工作区根为基准"—— spec FR-048） |

**P2 已建的条目 MUST NOT 改路径与格式值**（`tools/README.md` 与 `skills/example/SKILL.md` 的条目**保持原样**）。

---

## 5. Skills 三层的文件清单

| 层 | 文件 | 内容要求 |
|---|---|---|
| **Level 1** | `skills/example/SKILL.md` 的 frontmatter | **恰含** `name` + `description` 两字段（宪法 D-07 —— MUST NOT 含任何自定义额外字段）；以 `---` 开头 |
| **Level 2** | `skills/example/SKILL.md` 的正文 | 非空；讲清三层模型；给出按需使用 Level 3 的指引；**示例路径以工作区根为基准**（FR-048）；说明"改本 Skill 请保留头部元信息"与"其它字段不被解析"（FR-051） |
| **Level 3** | `reference/example.md` | 深层参考文档示例；说明"模型不会主动加载它" |
| | `scripts/example.py` | 可被命令工具调用的演示脚本；含 `__main__` 入口块；仅演示"打印一行输出" |
| | `templates/example.md` | 模板文件示例（**占位记法 MUST NOT 用 `{{ … }}`** —— 渲染器只替换 `{{ workspace_name }}`，其余 `{{ … }}` 会**原样保留**并出现在渲染产物中 → 破坏 F001-P2 契约 B12「渲染后无占位符残留」这条持久不变量；MUST 改用其它占位记法（如 `<<title>>` / `<title>`），并在文件内注明其为示例占位 —— spec FR-049 / FR-056 / FR-069） |

**三个 Level 3 子目录 MUST NOT 作为清单条目新增**（由父目录自动创建规则承接 —— spec FR-049）。

---

## 6. 构建期自检（MUST 在交付前跑通）

| # | 自检 | 判据 |
|---|---|---|
| B1 | 清单条数 | `len(entries) == 54`，且追加的 8 条在**数组末尾** |
| B2 | 源文件齐备 | 54 条中 45 个文本型条目的 `<条目路径>.txt` **全部存在**（缺一个 → 安装后 `donkey init` 报 exit 3） |
| B3 | 打包携带 | 按 wheel / sdist 产物核对 45 个源文件**全部**在内（R-09） |
| B4 | 语法自检 | 每个渲染出的 `.py` MUST `compile()` 成功（R-08 —— 模板正文零静态检查覆盖） |
| B5 | 工具计数 | 渲染产物中 `@tool` 函数共 **9** 个（7 + 1 + 1）；`changes.py` 与 `__init__.py` 各 **0** 个 |
| B6 | 无智能体入口 | 6 个 `.py` 中**无** `agent.py` / `main.py`；Skill 第三层脚本的 `__main__` **获宪法授权**（E-02 + [D-19]，见 FR-050） |
| B7 | 无可观测性字样 | 8 个新源 + 2 个覆盖源中 MUST NOT 出现 `langsmith` 等字样（FR-079） |
| B8 | 零环境变量 | 8 个新源 + 2 个覆盖源中 MUST NOT 出现 `os.environ` / `getenv`（FR-104） |

---

## 7. 与 F001-P2 既有断言的关系（改写清单）

> **口径**：本表列举的是**断言组**；每组内**具体断言语句的条数与位置 MUST 以 `tests/unit/test_template_skeleton.py` 与 `tests/e2e/phase/verify_phase_f001_p2.py` 的实际内容为准**（R-16 的逐行核对锚点表）—— MUST NOT 以任何概括性计数（如"7 条"）为准。

| # | P2 的断言组 | P3 的正确口径 | 依据 |
|---|---|---|---|
| (a) | 清单 46 / 文件型 40 / 落地文件 41 / 落地目录 7 | **动态口径**（按加载器实际返回值计算）+ 绝对值 **54 / 48 / 49 / 10** 作为独立断言（目录数 7 → 10 = 根 + 6 个清单目录 + 3 个 Skill Level 3 子目录）；`templates_loaded == 46` 在单测中**出现于 3 个不同的用例函数**，MUST **全部**改写 | spec FR-068(a) / R-16 |
| (b) | "工作区内无任何 `.py` 文件" + "内置工具文件**不存在**"（4 条否定断言） | "**除本 Phase 新增的 6 个 `.py` 文件外**无其它"（`tools/` 下 5：3 工具 + 契约库 + 包初始化；Skill 第三层演示脚本 1）+ "这 4 个文件**已存在**"；**MUST 保留**"工作区内无**智能体入口文件**"这条持久不变量（口径按 FR-050 引用的宪法 §6.3 例外 E-02 + §5 章 [D-19]） | spec FR-068(b) / FR-050 / R-16 |
| (c) | 退出码集合 `{0,1,2,3}` / 映射表 `{1,2,3}` / "退出码 4 **不在**实际使用集合中" | `{0,1,2,3,4}` / `{1,2,3,4}` / "退出码 4 **已在**实际使用集合中"；"运行期依赖恰为 1 个"**保持不变** | spec FR-068(c) / R-16 |
| (d) | `tools/README.md` **源文件正文**含"内置工具由后续阶段生成" | 因 FR-056 的正文覆盖而失效 → 随新正文改写为"正文 MUST 含 P3 阶段写入的 **8 项**规范要点"（口径见 FR-044） | spec FR-068(d) / R-16 |
| (e) | e2e 场景 1 的 `templates=46 created=40 skipped=0` + 落地文件数 / 目录数；e2e 场景 11 的 4 条否定断言 | 场景 1 → `templates=54 created=48 skipped=0` + 落地文件数 **49** / 目录数 **10**；场景 11 → "除本 Phase 的 **5** 个文件（3 工具 + 契约库 + `__init__.py`）外无其它内置工具文件"，`tools/README.md` 仍在 | spec FR-068(e) / R-15 / R-16 |

**MUST NOT 改写**（P2 的**持久不变量**，其成立由本 Phase 的其他条款保证）：

- **e2e 场景 5** 的"渲染产物 MUST NOT 残留 `{{ … }}` 占位符"断言 → **保持原样** —— 其成立由 spec FR-049 的**占位记法约束**保证（见 §5 的 `templates/example.md` 行）；
- 单测侧同源的"渲染结果中 MUST 无占位符残留"断言 → 同上，**保持原样**（spec FR-069 的持久不变量枚举已补登该项）。

**MUST NOT**：删掉 P2 的场景（等于抹掉阶段边界记录，spec FR-069）；把 P2 的断言改红后提交。
