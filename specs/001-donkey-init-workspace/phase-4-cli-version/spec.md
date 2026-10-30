# Feature Specification: F001-P4 `cli_version` —— `donkey version` 查询版本号

**Feature Branch**: `main`（本次执行未注册分支创建钩子，也未创建分支；spec 目录名与分支名相互独立）

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: 为 F001 新增 Phase F001-P4 `cli_version` —— 给 donkey CLI 增加一条查询版本号的命令 `donkey version`。用户当前只能靠 `python -c "import donkey; print(donkey.__version__)"` 这种绕路方式看版本，不合理；按人类使用 CLI 的习惯，应当有 `donkey version`。本 spec 是该提示词的规范化落地，不替代提示词本身

---

## Phase 元信息

| 字段 | 值 |
|---|---|
| **Feature 编号** | **无** —— `donkey version` 按宪法 §4.2（修订后）/ §4.2.1 的「元信息命令豁免」条款**豁免 F 编号登记**。交付物仍**归属 F001 目录**（`specs/001-donkey-init-workspace/`）与 **F001-P4** Phase 编号：「Phase 编号 = F001-P4」是**开发阶段**标识（宪法 §4.3），「命令无 F 编号」是**登记**标识（宪法 §4.2.1），两者**不冲突**（豁免的授权来源 = 宪法 §4.2.1 + §4.3 两处限定语 + 第 5 章 [D-20]） |
| **Phase 编号 / 英文名** | F001-P4 / `cli_version` |
| **Phase 中文描述** | 为 CLI 增加**顶层 `version` 子命令**：只读地暴露 donkey 的**唯一版本号**（软件功能版本，当前 `v0.1.0`）。**图版本 ≡ 软件版本**（两者 MUST 保持一致）；客户端版本（`donkey web version` / `donkey gui version`）归 F005 / F006，本 Phase **只登记、不实现** |
| **核心库 API** | **无** —— 本 Phase 不新增、不修改 `donkey.core.api` 的库 API（元信息命令豁免的边界之一：不需要库 API） |
| **段位 / 子段** | **不占用任何 exit code 子段** —— 本 Phase 实际返回的码值集合 = `{0, 1}`：`0` 走宪法 §4.4 的「全子命令」共用段；`1`（参数用法错误）**归属 F001 段位（`1-10`）内的既有口径**（F001-P1 已建立的 `DonkeyArgumentParser.error()` 覆写，与 `donkey init` 的参数用法错误**同源**）。即本 Phase **未引入 §4.4 之外的任何码值**、不新增 Error class，退出码由**既有的全局异常 → 退出码映射表**与参数解析器的既有错误路径承载（FR-028 ~ FR-030 / SC-008） |
| **本阶段使用的退出码** | `0`（成功）、`1`（参数用法错误 —— 复用 F001-P1 既有口径，MUST NOT 用参数解析器的默认失败码 `2`）。**`1` 的段位归属登记**：宪法 §4.4 的 `1-10` 段归属写为「`donkey init`」，本 Phase 作为 F001 目录下的 Phase **复用该段位的既有码值 `1`**（子段分配仍属 `donkey init`）—— MUST NOT 被理解为「`donkey version` 自占 `1-10` 段位」，本 Phase **不占用任何子段**（FR-029 / FR-030 口径） |
| **本阶段不占用的退出码** | `2-10`（F001 段位内其余码值，本 Phase 全部**不触发**）、`11-200`（其它 Feature 段位）、`201+`（预留） |
| **准入条件（Entry Gate）** | F001-P1（`cli_validation`）/ P2（`template_skeleton`）/ P3（`builtin_tools`）的退出条件全部满足（宪法 §4.3 的入口条件 = **前置 Phase 的退出条件**；本 Phase 不引入跨 Feature 的前置依赖） |
| **授权基础** | 宪法 §4.2.1「元信息命令豁免」小节 + §4.3 的**两处**限定语 + 第 5 章 [D-20] —— **已由 Maintainer 于 2026-10-30 前置落地**（4 处）；**另有 [D-21] / [D-22]** 两条 ADR（2026-10-30 · Maintainer 裁决）—— 分别登记本 Phase 交付的「工作区清单字段变更」与「`donkey init` 执行报告变更」（详见文末「后续修订登记」§1 ~ §3）（FR-036 / Clarifications **Session 2026-10-30（analyse 缺陷修复轮）Q6 / Q8**），MUST **先于**本 Phase 的其余交付物完成**核对**；spec MUST NOT 自设宪法例外（FR-031） |
| **退出条件（Exit Gate）** | SC-001 ~ SC-016 全部达成 + `tests/e2e/phase/verify_phase_f001_p4.py` 的 **7** 个断言函数 100% PASS + 既有三套 verify 脚本（F001-P1 / P2 / P3）保持全绿 + 静态检查零 error + **宪法四处修订已落地**并通过自检（FR-036 / SC-012） |
| **验收脚本** | `tests/e2e/phase/verify_phase_f001_p4.py`（**7** 个功能场景，与 **7** 个 User Story **1:1** 对应） |
| **闭环复杂度** | 低（7 个 e2e 断言 + 1 个 CLI 子命令 + 1 处版本取值来源登记 + 1 处宪法修订登记；**无**模板清单变更、**无**依赖变更、**无**新增退出码 / Error class） |
| **治理依据** | 宪法 N-03 / N-04 / N-05 / N-08 / §2.8 / §4.2（修订后）/ §4.2.1 / §4.3（修订后）/ §4.4 / §4.5 / §6.2 / 第 5 章 [D-20] |

---

## Clarifications

### Session 2026-10-30

> 本段记录本轮 `/speckit.clarify` 的裁决。Maintainer 已先前置裁决 **3 条**（D-1 命令形态 / D-2 版本语义 / D-3 退出码），它们**不是**待澄清项，直接作为既定事实落地。
> 本轮 5 条待裁决项的最终结论见下列条目。

- **Q1: F001-P4 交付时 LangGraph 主图尚不存在（要到 F004-P7 `agent_loop` 才建成），`donkey version` 的 core 版本该打印什么？** → A（**已被 Q2 覆盖并作废** —— 留痕以记录决策演进）：原拟打印 `v0.0.0`（`x` = 0 = 图版本 0、`y` = `z` = 0 = 尚无节点）。**作废理由**：Maintainer 裁决"图版本就是包版本，必须保持一致"（见 Q2）—— 打印 `v0.0.0` 会让仓库里同时存在两个打架的版本号，正是"五花八门"。**当前口径以 Q2 为准**（FR-012 / FR-013 / FR-014）。

- **Q2: 包 / 发布版本 `0.1.0` 是真实存在、且已被工作区清单的 `donkey_version` 字段与 `sessions_metadata.donkey_version` 列（宪法 D-03 的迁移提示）使用的值，它该怎么暴露？** → A: **donkey 只有 ONE 个版本号** —— **图版本 ≡ 包版本 ≡ 软件功能版本**，三者 MUST 保持一致（MUST NOT 出现两个各自维护、可能打架的版本号）。`donkey version` 的 **stdout 恰好是一行 `v0.1.0`**（裸版本值，**无** `[donkey version]` 前缀、**无** `key=value` 字段名）。**`v` 是显示前缀**（贴合宪法 §4.5 / 立项书 §1.5.2 的 `vx.y.z` 记法），其底层取值 `0.1.0` 与 `pyproject.toml` 的 `version`、包内 `__version__`、工作区清单 `donkey_version` 字段**逐字节一致**（用户可直接拿 `donkey version` 的输出去比对工作区清单）。**取值来源**：优先取**安装分发元数据**查询（与 F001-P2 FR-021「将来若动态化 MUST 使用包元数据查询方式」一致），不可得时回退包自身 `__version__` 常量，MUST NOT 抛异常 / MUST NOT 使命令失败。**被否决的替代方案**：① 同一条摘要里 `core=` 与 `package=` 两字段并存（两个字段即两个可能打架的版本号）；② 图版本单独一个字段、另设 `donkey --version` 暴露包版本（语义割裂 + 两个入口）；③ 只展示包版本、把图版本留到 F004（用户拿不到"核心功能版本"）。**权威表述见 FR-007 ~ FR-018**。


- **Q3: 输出值 `v0.1.0` 按宪法 §4.5 的 `vx.y.z` 拆开看是 `x=0 / y=1 / z=0`，但 §4.5 字面上说 `y` 是**节点 id** —— 而图还不存在、根本没有"1 号节点"。这个 `y` 该作何解？** → B: **严格按 §4.5 读作 `x=0` / `y=1` / `z=0`，不作额外解释** —— 版本值的三个分量 MUST 按 §4.5 的字面定义读（`x` = 后端 LangGraph 图版本 / `y` = 该图版本内各节点与中间件的 id / `z` = 该节点的修改次数），MUST NOT 另立一套"里程碑序号"的读法（那正是"五花八门"）。**被否决的替代方案**：① 登记为"软件 / 里程碑版本线"并把 `y` 解释成里程碑序号（§5.2.2：v0.1.0 = F001）—— 会与 §4.5 的字面定义冲突，等于在 spec 内自设读法；② 输出版本值去掉 `v` 前缀（`0.1.0`）—— 与 Q2「stdout 带 `v`」的裁决冲突。**配套边界不变**：本命令 MUST NOT 输出节点清单、MUST NOT 输出任何节点的**独立**版本号（那属 F004-P7，FR-015）。**权威表述见 FR-013**。补充登记（2026-10-30 analyse 缺陷修复轮）：§4.5 的 `x` 定义含『前端版本 **或** 后端 LangGraph 图版本』两个分支，本 Phase 取后端图版本分支；前一支分支（前端版本）在本 Phase 不适用 —— web / gui 端版本入口归 F005 / F006，本 Phase 只登记不实现（FR-005 / FR-023）。


- **Q4: 除 `version` 子命令外，顶层解析器要不要再加一个 `donkey --version` 标志？** → A: **不加** —— 版本查询的**唯一入口**是 `donkey version`；`donkey --version` 按"未知参数"以退出码 `1` 失败、MUST NOT 输出任何版本号。理由：Q2 之后 donkey 只剩**一个**版本号，多一个入口**没有任何信息增益**，而"顶层 `--version`"在工具生态里通常被默认为"包版本"，与本命令"唯一版本号"的语义打架、易让脚本挑错入口；且与 D-2 的"客户端各自二级命令（`donkey web version` / `donkey gui version`）"设计**对称** —— 三端各自的版本入口都在各自的**子命令**层，顶层不留平级旁路。**被否决的替代方案**：① 加且与 `version` 子命令**完全等价**（两份等价入口 —— 纯重复）；② 加且两者**形态分工**（`--version` 出 `0.1.0`、子命令出 `v0.1.0`）—— 同一个值出现两种记法，正是"五花八门"。**权威表述见 FR-038**，对应判据见 SC-014。

- **Q5: 本 Phase 的范围边界怎么定 —— 宪法修订由谁落地、要不要顺带修过期的 `46` 计数、客户端版本要不要写占位？** → A: **(a) 宪法修订由本 Phase 作为第一项交付物实施**（§4.2「元信息命令豁免」条款 + §4.3 限定语 + 第 5 章 [D-20]）—— 修订内容已由 Maintainer 批准，**本 Phase 只负责落地**；spec MUST 自包含地引用它，MUST NOT 自设宪法例外（FR-031 / FR-036），tasks 的第一项即"改宪法"。理由：宪法修订是本 Phase 的**授权基础**，若由外部单独完成，spec 与 tasks 就无法自证合规、且实施时点与 spec 落地脱节。
  **(b) 顺带修正过期计数** —— `donkey init --help` 的「46 个模板条目」→ **54**、`donkey/core/api.py` 的 `InitResult` docstring 同步（属**实现与文档同步**）；MUST NOT 回改 F001-P1 / P2 已冻结 spec 的 FR 编号与断言。**已核对**：无任何既有测试断言依赖那两个字符串（grep `46 个模板条目` / `templates=46` 在 `tests/` 下零命中），故本次修正**不使任何既有断言失效**、不需登记阶段边界改写（FR-037）。
  **(c) 客户端版本只登记、不实现** —— `donkey web version` / `donkey gui version` 只写进 spec 的「与其它 Phase / Feature 的关系」段落（含"三端各有版本入口"以正面回应宪法 N-11 / §2.8），MUST NOT 实现任何代码或**解析器占位**（占位会让未交付的能力被报成已交付）（FR-005 / FR-023）。
  **被否决的替代方案**：B（宪法修订由 Maintainer 单独完成、spec 只引用）—— spec 失去自包含性、实施时点与 spec 落地脱节；C / D（不修过期计数）—— 缺陷继续留在用户可见的 `--help` 里，且与本 Phase「实现与文档同步」的边界自相矛盾。**权威表述见 FR-036 / FR-037 / FR-023**。**补充登记（2026-10-30 analyse 缺陷修复轮）**：本条 (a) 关于**落地方式**的裁决已被 Maintainer 裁决**取代** —— 宪法修订**已由 Maintainer 于 2026-10-30 前置落地**（**4 处**：§4.2.1 新增「元信息命令豁免」小节 / §4.3 第 253 行括注 / §4.3 第 269 行 v1 baseline 限定语 / 第 5 章 [D-20]），本 Phase **只核对、不改**（spec FR-036 / H 段 (a)/(b)/(b2)/(c)）；故被否决的替代方案 B 现已成为**实际采用**的方案，(a) 中「本 Phase 只负责落地」「tasks 的第一项即『改宪法』」的表述**不再成立**。本条 (b) / (c) 的裁决**不受影响**。**来源：/speckit.analyze 缺陷修复轮 · Maintainer 裁决（2026-10-30）**。

### Session 2026-10-30（analyse 缺陷修复轮）

> 本段记录 `/speckit.analyze` **缺陷修复轮**的 Maintainer 裁决（**不是**新一轮需求澄清）：共 **4** 条，均已在 spec 内定向落地；FR / SC 的编号与条数、User Story 编号与场景条数一律未动。

- **Q6: 宪法 §4.3 的 v1 baseline 句与「提示词文件」口径是否一并豁免？** → A: **一并豁免** —— 元信息命令**不占用** exit code 子段、**不需要**提示词文件，故「1 Phase = 1 子段 = 1 提示词文件 = 1 verify 脚本」的 1:1 口径对 F001-P4 **不适用**。**授权来源** = 宪法 §4.2.1 + §4.3 的**两处**限定语 + 第 5 章 [D-20]；F001-P4 **无**提示词文件（`harness/features/feature001_phase004_cli_version.md` 不存在 —— 与 F001-P1 / P2 / P3 不同，属**有意偏离**），登记载体 = [D-20] 的影响面条目。**来源：/speckit.analyze 缺陷修复轮 · Maintainer 裁决（2026-10-30）**。

- **Q7: FR-013 / FR-014 / SC-003 的「逐字节一致」与 FR-018（元数据优先）冲突时以哪个为准？** → A: **以 FR-018 为准（元数据优先）** —— FR-013 / FR-014 / SC-003 / US2 场景 2 / US3 场景 1 的「逐字节一致」口径**限定在常规安装形态下**（安装元数据值 == 工作树声明值）；两者不等（陈旧安装）时输出底层取值 MUST == **安装分发元数据值**（FR-018），且该不等情形 MUST 由验收脚本**显式断言**（SC-003 的双比对口径），MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段（那会产生假失败）。**来源：/speckit.analyze 缺陷修复轮 · Maintainer 裁决（2026-10-30）**。

- **Q8: 宪法修订 (c) 的权威文本以哪一份为准？** → A: **以宪法 [D-20] 行为准** —— spec 的 H 段 (c) 由「四字段表」改为**引用宪法 [D-20] 行的落地文本（逐字）**（代码块承载）；H 段 (a) / (b) / (b2) 逐字不变；SC-012 的判据改为「四处」，并要求**四处的实际措辞与 H 段登记文本逐字一致**。**来源：/speckit.analyze 缺陷修复轮 · Maintainer 裁决（2026-10-30）**。

- **Q9: 宪法 §4.5 的 `x` 取哪个分支？「x+1 ⇒ 包版本 bump」是否为 MUST？** → A: **取「后端图版本」分支并登记** —— §4.5 的 `x` 定义含「前端版本 **或** 后端 LangGraph 图版本」两个分支，本 Phase 取后端图版本分支；前一支分支（前端版本）在本 Phase 不适用（web / gui 端版本入口归 F005 / F006，本 Phase 只登记不实现 —— FR-005 / FR-023）。**「x+1 ⇒ 软件版本同步递增」降级为登记约定**：当前**不是 MUST**，MUST 由 F004-P7 在其 spec 中显式登记并取得 Maintainer 批准后才成立；本 Phase MUST NOT 把它写成对后续 Phase 的强制约束。**来源：/speckit.analyze 缺陷修复轮 · Maintainer 裁决（2026-10-30）**。


---

## User Scenarios & Testing *(mandatory)*

> 本 Phase 的 **7** 个 User Story 与验收脚本 `tests/e2e/phase/verify_phase_f001_p4.py` 的 **7** 个功能场景（`test_scenario_1_*` ~ `test_scenario_7_*`）**一一对应**（故事 US N ↔ 场景 N）。
> **术语定名**：本 spec 中「验收场景」专指 Given/When/Then 验收场景；验收脚本的 `test_scenario_*` 一律称「e2e 黑盒场景」。
> **无 CI 交付检查类断言**：本 Phase 不引入新的 CI 交付检查；「既有三套 verify 脚本保持全绿」属**强制退出条件**（FR-034 / SC-009），MUST NOT 被升格为 User Story。
> 全部故事共享同一前提：**F001-P1 / P2 / P3 已就绪**；本 Phase 在其之上交付**一条只读的版本查询命令**。

### User Story 1 - 一条命令就能看到版本号 (Priority: P1)

用户想知道"我这套 donkey 到底是哪个版本"。现在他只能绕路敲 `python -c "import donkey; print(donkey.__version__)"` —— 这既不像 CLI 的用法，也要求用户知道 Python 怎么进。他期望直接敲 `donkey version`，stdout 上就出现一个版本号。

**Why this priority**: 这是本 Phase 唯一不可替代的价值 —— "版本号查询"是一件不可缺少却缺失的小事。缺了它，每个用户都得自己发明绕路方式。

**Independent Test**: 可独立验证 —— 执行 `donkey version`，断言退出码为 `0`、stdout **恰好一行**且内容为 `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`）、stderr 为空。

**Acceptance Scenarios**:

1. **Given** 一个已安装 donkey 的环境，**When** 用户执行 `donkey version`，**Then** 命令以退出码 `0` 结束，stdout 输出**恰好一行**、内容为 `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`；分发元数据不可得或与工作树声明值不一致时按 FR-018 以元数据为准，见 Edge Cases「版本取值与来源类」；「`v0.1.0` 是当前值」的硬断言见 SC-003），stderr 为空。
2. **Given** 同一个环境，**When** 用户连续执行两次 `donkey version`，**Then** 两次 stdout **逐字节相同**（MUST NOT 含时间戳 / 主机名 / 路径等非确定性内容）。
3. **Given** 一个**当前目录下不存在 workspace** 的位置，**When** 用户执行 `donkey version`，**Then** 命令仍以退出码 `0` 结束（MUST NOT 要求工作区存在、MUST NOT 读取工作区）。

---

### User Story 2 - 版本号只有一个，不会出现两个打架的值 (Priority: P2)

donkey 的"核心功能版本"与"包版本"在仓库里是同一个数（`0.1.0`）。用户报 bug 时只需要报**一个**版本号 —— 他不希望看到两个长得像、含义却不同的版本号，更不希望自己判断"该报哪个"。

**Why this priority**: 两个取值相同、字段名不同的版本号，会让用户与脚本都无法判断哪个才是权威值；一个值、一处来源是这条命令唯一合理的形态。

**Independent Test**: 可独立验证 —— 执行 `donkey version`，断言 stdout 里的版本值**恰好出现 1 次**，且与工作区清单的 `donkey_version` 字段可逐字节比对（该比对的前提与跳过条件见 US2 验收场景 2）。

**Acceptance Scenarios**:

1. **Given** 已安装 donkey 的环境，**When** 用户执行 `donkey version`，**Then** stdout 里的**版本值恰好出现 1 次**（MUST NOT 出现第二个版本值），该值形如 `v<数字>.<数字>.<数字>`。
2. **Given** 同一次输出，**When** 用户拿它与工作区清单的 `donkey_version` 字段比对，**Then** 去掉显示前缀 `v` 后的取值与该字段**逐字节一致**（用户可直接用 `donkey version` 的输出做迁移比对）（**常规安装形态下** —— 分发元数据不可得或与工作树声明值不一致时按 FR-018 以元数据为准，见 Edge Cases「版本取值与来源类」；**「工作区清单字段」这一比对的额外前提**：清单值 `donkey_version` 被 F001-P2 FR-021 **锁死**为**当时的**版本，故该比对 MUST 以「工作树声明值 == 清单字段」为前提 —— 不成立时（**陈旧清单**形态）MUST **跳过**该比对，改以**分发元数据 / 工作树声明值**为准，详见 Assumptions「版本号 bump 的跨 Phase 联动」）。

---

### User Story 3 - 图还没建时也给得出确定的答案 (Priority: P3)

用户现在装的 donkey **还没有**智能体主图（那是后面阶段的事）。他执行 `donkey version` 时，期望看到的是一个**确定的、有明确含义**的版本号，而不是"未知"或一段报错说明，也不是一个拿"图节点数"冒充版本号的怪东西。

**Why this priority**: "查不到就报错"与"拿别的含义凑数"都是坏答案 —— 前者让命令不可用，后者让用户拿到一个**错误但看起来合理**的值。

**Independent Test**: 可独立验证 —— 执行 `donkey version`，断言其值恒为 `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`），且输出中**不含任何节点级版本信息**。

**Acceptance Scenarios**:

1. **Given** 主图尚未构建的当前代码库，**When** 用户执行 `donkey version`，**Then** stdout 恒为 `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`），MUST NOT 是 `unknown` 一类的占位串，MUST NOT 是 `dev` 一类的后缀串，MUST NOT 是 `v0.0.0` 一类"图版本 0"的取值（分发元数据不可得或与工作树声明值不一致时按 FR-018 以元数据为准，见 Edge Cases「版本取值与来源类」）。
2. **Given** 同一次输出，**When** 用户检查是否含节点级版本信息，**Then** 输出中节点级版本信息（节点 id / 节点修改次数）的出现次数为 **0** —— 本 Phase 不实现节点级版本号。

---

### User Story 4 - 两种调用方式结果一致 (Priority: P4)

用户可能通过安装后的 `donkey` 命令调用，也可能直接从源码目录用 `python -m donkey` 调用（CI、未安装环境、fork 二次开发场景）。他期望两条入口**完全等价** —— 否则"我这边好的、你那边不对"的排查噩梦就开始了。

**Why this priority**: 两条入口的等价性是 F001-P1 已确立的持久契约；新命令一旦破坏它，就会让 CI 与本地行为分叉。

**Independent Test**: 可独立验证 —— 分别执行 `donkey version` 与 `python -m donkey version`，断言退出码与 stdout **逐字节相同**。

**Acceptance Scenarios**:

1. **Given** 已安装 donkey 的环境，**When** 分别执行 `donkey version` 与 `python -m donkey version`，**Then** 两者的退出码相同、stdout **逐字节相同**、stderr 均为空。
2. **Given** 两条入口的调用结果，**When** 用户比较两行输出，**Then** 版本取值在两条入口下相等。

---

### User Story 5 - 用错了要报错，且报错方式跟别的命令一致 (Priority: P5)

用户可能顺手敲 `donkey version --json`，或以为可以 `donkey version web` 看某个客户端的版本。他期望命令**明确失败**，而且失败方式跟 `donkey init` 完全一致（退出码 `1`）—— 而不是参数解析器的默认 `2`，更不是静默忽略。

**Why this priority**: 退出码语义一致性是脚本化调用的前提；`2` 在 `donkey init` 段位里已被"权限不足"占用，混用会让脚本误判。

**Independent Test**: 可独立验证 —— 执行 `donkey version --bogus` / `donkey version web` / `donkey version extra`，断言三者退出码**均为 `1`**、stdout 为空、stderr 含用法提示。

**Acceptance Scenarios**:

1. **Given** 任意一个已安装 donkey 的环境，**When** 用户执行 `donkey version --bogus`，**Then** 退出码为 **1**（MUST NOT 为参数解析器的默认失败码 `2`），错误信息写 stderr 且含用法提示，stdout 为空。
2. **Given** 同一环境，**When** 用户执行 `donkey version web` 或 `donkey version extra`，**Then** 退出码同样为 **1**、stdout 为空 —— `version` MUST NOT 接受任何客户端参数（MUST NOT 静默忽略）。
3. **Given** 同一环境，**When** 用户执行 `donkey version --help`，**Then** 退出码为 **0**（帮助请求**不**是用法错误），且 MUST NOT 产生任何文件系统副作用。

---

### User Story 6 - 装没装都能给出确定的版本 (Priority: P6)

用户可能没把 donkey 装进 Python 环境（直接从源码检出跑 `python -m donkey`），或者用的是非标准安装方式。他期望 `donkey version` 在这种情况下**仍然给得出确定的版本号**，而不是抛一个"找不到包"的异常。

**Why this priority**: 一条"查版本"的命令如果自己在某些安装形态下就崩掉，等于在最需要它的时候失灵 —— 而它恰恰是最该在任何环境下都能跑的命令。

**Independent Test**: 可独立验证 —— 在分发元数据查询失败的前提下执行 `donkey version`，断言退出码仍为 `0` 且输出仍是一个**确定可解析**的版本值（不为空、不报错）。

**Acceptance Scenarios**:

1. **Given** 一个**取不到安装分发元数据**的环境（如从源码检出直接运行），**When** 用户执行 `donkey version`，**Then** 命令以退出码 `0` 结束，stdout 仍是一个**确定可解析**的版本值（MUST NOT 为空、MUST NOT 抛异常、MUST NOT 使命令失败）。
2. **Given** 同一次输出，**When** 用户检查版本值，**Then** 它的取值**不依赖**安装形态（取不到元数据时 MUST NOT 影响版本值）。

---

### User Story 7 - 查询版本不会动我的东西 (Priority: P7)

用户的 workspace 是他的心血。他担心"查个版本"这种只读操作会不会顺手改点东西（生成文件、写缓存、改 manifest）。他期望这条命令**一个字节都不写**。

**Why this priority**: 只读命令写了东西，就破坏了"查询"这个语义，也会在用户毫不知情时污染 workspace。

**Independent Test**: 可独立验证 —— 记录目标目录树的文件 / 目录 / 内容指纹，执行 `donkey version`，再次比对，断言**零变化**。

**Acceptance Scenarios**:

1. **Given** 一个含若干文件的目录树，**When** 用户在其下执行 `donkey version`，**Then** 命令结束后该目录树的文件数、目录数与各文件内容指纹**全部不变**（副作用数 = **0**）。
2. **Given** 同一个目录树，**When** 用户在命令执行前后检查工作区清单文件，**Then** 该文件**未被创建、未被修改**（`donkey version` MUST NOT 触碰工作区）。

---

### Edge Cases

**命令面与参数类**

- `donkey version` 额外携带**未知长选项**（如 `--json`） → MUST 以退出码 `1` 失败，MUST NOT 被静默忽略，MUST NOT 输出部分结果。
- `donkey version` 携带**位置参数**（如 `donkey version web` / `donkey version 0.1.0`） → MUST 以退出码 `1` 失败；MUST NOT 被解释为"指定要查的版本号"。
- `donkey version --help` / `donkey version -h` → MUST 以退出码 `0` 结束（帮助请求不是用法错误），MUST NOT 产生文件系统副作用。
- **顶层** `donkey --version` → MUST 以退出码 `1` 失败（顶层解析器不提供该标志），MUST NOT 输出版本号 —— 语义歧义由 FR-038 消除。
- `donkey`（不带子命令） → 沿用 F001-P1 既有口径：以退出码 `1` 失败并附用法提示。
- `donkey init version`（把 `version` 当路径） → 沿用 `donkey init` 的既有语义：`version` 是**路径参数**，MUST NOT 被解释为子命令。**本 Phase 无独立 FR / SC** —— 该行为由 FR-001 / FR-002 / FR-022 的既有断言**自然覆盖**（argparse 与只读语义的结果），MUST NOT 为其新增专门断言。
- 用户在**管道**中调用 `donkey version`（stdout 非 tty） → MUST 输出同一行版本值，MUST NOT 因非 tty 而改变输出形态。**本 Phase 无独立 FR / SC** —— 该行为由 FR-001 / FR-002 / FR-022 的既有断言**自然覆盖**（argparse 与只读语义的结果），MUST NOT 为其新增专门断言。

**版本取值与来源类**

- **安装分发元数据不可得**（未安装 / 非标准安装 / 从源码检出直接运行） → MUST 回退到包自身的 `__version__` 常量，MUST NOT 抛异常、MUST NOT 输出空值、MUST NOT 使命令失败。
- **安装分发元数据与包自身 `__version__` 不一致**（例如装的是旧版本、源码已改） → MUST 以**分发元数据**为准（它代表用户实际安装的那一份），MUST NOT 报错、MUST NOT 因此使命令失败。此时输出与工作树声明值 / 清单 `donkey_version` 字段**不**逐字节一致 —— 这与 FR-013 / SC-003 的「逐字节一致」口径**不冲突**（后两者已限定在常规安装形态下）。
- **主图尚未构建**（F001-P4 交付时的常态） → 版本值恒为 `v0.1.0`（= 当前唯一的软件版本）；MUST NOT 是 `unknown` / `dev` 一类的占位串，MUST NOT 是 `v0.0.0` 一类"图版本 0"的取值。
- **主图已构建**（F004-P7 之后） → 图结构变化触发宪法 §4.5 的 `x+1` 时，**宜**伴随软件版本同步递增（图版本 ≡ 软件版本，同一个数）—— 该联动**当前不是 MUST**：它 MUST 由 F004-P7 在其 spec 中显式登记并取得 Maintainer 批准后才成立；本 Phase MUST NOT 把它写成对后续 Phase 的强制约束；MUST NOT 出现第二个各自维护的版本定义点。
- 用户把 **workspace 清单的格式版本**（整数 `1`）误当成版本号 → 版本值 MUST NOT 取该值（MUST 是软件 / 包版本）。
- **底层取值与显示前缀**：输出的 `v` 是**显示前缀**；**在常规安装形态下**去掉 `v` 后的取值 MUST 与工作区清单 `donkey_version` 字段**逐字节一致**（FR-013 口径）—— 用户可直接用 `donkey version` 的输出做迁移比对（宪法 D-03）。
- **工作区清单 `donkey_version` 与工作树声明值不一致**（**陈旧清单**形态 —— 清单值被 F001-P2 FR-021 锁死为**当时的**版本，而 `pyproject.toml` 已被后续 Phase bump） → 「输出底层取值 vs 清单字段」的比对 MUST **跳过**（MUST NOT 断言输出 == 清单字段 —— 那是假失败），改以**分发元数据 / 工作树声明值**为准（FR-018）；该形态的成因与联动登记见 Assumptions「版本号 bump 的跨 Phase 联动」。

**只读性与作用域类**

- 命令在**只读**文件系统 / 只读目录中执行 → MUST 仍然成功（退出码 `0`），MUST NOT 因不可写而失败。
- 命令在**工作区不存在** / **工作区损坏**（manifest 缺失或非法）的目录下执行 → MUST 仍然成功，MUST NOT 读取或校验工作区。
- 命令在 **workspace 内部**（cwd = 工作区根）执行 → MUST 仍然成功，MUST NOT 产生任何工作区副作用。
- 用户在命令执行**期间**删除工作区 → MUST NOT 影响命令结果（MUST NOT 读取工作区）。**本 Phase 无独立 FR / SC** —— 该行为由 FR-001 / FR-002 / FR-022 的既有断言**自然覆盖**（argparse 与只读语义的结果），MUST NOT 为其新增专门断言。

**阶段边界类**

- 本 Phase **依宪法 §4.3 第 269 行的既有豁免限定语执行**（该句**已含**「**（元信息命令按 §4.2 豁免）**：§4.2.1 定义的元信息命令**不占用** exit code 子段、**不需要**提示词文件，故本句的 1:1 口径对元信息命令**不适用**」—— 本 Phase 属该豁免的**适用对象**，**不是**「打破宪法」）—— 对元信息命令而言，「1 Phase = 1 子段 = 1 提示词文件 = 1 verify 脚本」**不适用**两项：① **不占 exit code 子段**；② **不需要提示词文件**。授权 = 宪法 §4.2.1 + §4.3 两处限定语 + [D-20]；Maintainer 已决定不修订 `harness/features/README.md`（其非强制）→ MUST 在本 spec 显式登记，MUST NOT 以「顺带修订 README」为由扩大本 Phase 范围。
- 本 Phase **不**新增 exit code 子段、不新增 Error class → 既有退出码映射表（F001-P1 FR-018 / 契约 M-01 ~ M-05）与段位表 MUST **逐项未改**。
- F001-P1 / P2 / P3 的 FR / SC 编号与断言 → MUST 保持不变；若某条既有断言因本 Phase 而失效，MUST 在本 spec 中**显式登记该断言的改写**，MUST NOT 让既有测试红着提交。
- 本 Phase **不**触碰工作区清单的 `donkey_version` 硬编码值（F001-P2 FR-021 锁死）、**不**改包内 `__version__`、**不**改 `pyproject.toml` 版本号。
- 本 Phase **不**做 F002 `donkey load` 的任何事 —— 尤其**不**做「工作区清单 `donkey_version` 与当前运行时版本对比 / 迁移提示」。

**其它边界**

- **已知缺口（v1 不补）· 节点级版本号**：节点级版本号（`vx.y.z` 中的 `y` / `z`）需要真实存在的图与节点，**属 F004-P7**；本 Phase MUST NOT 枚举节点、MUST NOT 展示任何节点的版本号。
- **已知缺口（v1 不补）· 客户端版本**：`donkey web version` / `donkey gui version` 归 **F005 / F006**；本 Phase MUST NOT 实现任何代码或解析器占位（否则等于把未交付的能力报成"已交付"）。
- **已知缺口（v1 不补）· 三套版本号体系的其余关系**：仓库里并存**三套**版本号体系 —— 软件 / 包 / 发布版本、图版本、workspace 格式版本；前两套已按 Q2 裁决**合并为同一个数**（FR-012），**第三套（workspace 格式版本，整数 `1`）不暴露**（FR-021）；除这一合并外，三套之间的**其余**关系至今**全文没有任何规定** —— 本 Phase MUST NOT 自设其关系。
- **风险登记 · 客户端三端对等（宪法 N-11 / §2.8）**：`version` 入口目前**仅 cli 端**存在；web / gui 端的版本入口由 F005 / F006 各自落地。本 Phase MUST 在「与其它 Phase / Feature 的关系」段落登记这一缺口，MUST NOT 以"cli 先行"为由声称三端已对等。**不违反 N-11 的理由**：N-11 的 MUST 是 **v1 整体交付**要求（cli / web / gui 三端缺一不可），**不是**单个 Phase 的要求 —— F005 / F006 尚未开工，web / gui 端尚不存在任何命令，故本 Phase 交付 cli 端版本入口**不构成**「功能仅 cli 独有」的违例；但一旦 F005 / F006 交付而仍缺版本入口，即构成违例。
- **过期文案 · `donkey init --help` 与 `InitResult` docstring**：仍写「46 个模板条目」，而实际清单已 **54** 条 —— 处置范围见 FR-037。
- **过期文案 · 第三处（**已知缺口 · 本 Phase 不修**）**：`tests/e2e/phase/verify_phase_f001_p2.py` 的场景 1 docstring 仍写「全部 **46** 条落地物就位」—— 该文件属 **F001-P2 的冻结快照**，受 FR-034（MUST NOT 改动既有测试文件）保护，本 Phase **MUST NOT** 修正；其口径差异（46 vs 54）已由 F001-P3 的契约文档登记为当前权威口径。**登记为已知缺口**，留给独立的文档 / 快照清理工作项。
- **运行平台**：验收以当前开发平台为准；平台差异（Windows 下路径分隔符等）不影响本 Phase 的判据（本命令不触碰文件系统）。

---

## Requirements *(mandatory)*

### Functional Requirements

#### A. 命令面与入口（FR-001 ~ FR-006）

- **FR-001**: 顶层命令面 MUST 注册 `version` 子命令 —— 命令行为 `donkey version`；该子命令 MUST **无任何参数**（MUST NOT 有位置参数，MUST NOT 有可选开关）。**形态已由 Maintainer 裁决**：D-1 —— 本 Phase 交付**顶层 `version` 子命令**，"只有顶层 `--version` 标志"的形态已被否决。
- **FR-002**: `version` MUST NOT 接受任何额外参数 —— 任何位置参数与任何未知开关 MUST 以退出码 `1` 失败，MUST NOT 被静默忽略，MUST NOT 输出部分结果。
- **FR-003**: 顶层 `donkey --help` 的子命令列表 MUST 出现 `version` 条目（与 `init` 并列）—— 版本查询入口 MUST 是**可发现**的。
- **FR-004**: `donkey version --help` MUST 以退出码 `0` 结束，且 MUST NOT 产生任何文件系统副作用（帮助请求**不**是用法错误）。
- **FR-005**: `donkey version` MUST NOT 接受任何客户端参数 —— 客户端版本由**各自的二级命令**暴露（`donkey web version` / `donkey gui version`，归 F005 / F006），本 Phase **不实现、只登记**（见「与其它 Phase / Feature 的关系」段）。**语义已由 Maintainer 裁决**：D-2 —— 本命令**永远只展示 donkey 自身的版本**。
- **FR-006**: `donkey`（控制台脚本入口）与 `python -m donkey`（模块入口）两条入口 MUST 产生**完全相同的退出码与输出**（沿用 F001-P1 已确立的入口等价性契约）。

#### B. 输出契约（FR-007 ~ FR-011）

- **FR-007**: 成功时 MUST 向 stdout 输出**恰好一行** —— 该行内容 = 版本值 + **一个**行终止符；MUST NOT 带 `[donkey version]` 一类前缀，MUST NOT 带 `key=value` 字段名，MUST NOT 带任何其它文字，MUST NOT 有前导 / 尾随空白（判据一律以"**去掉行终止符后**"的正文为准 —— 跨平台的行终止符差异不构成本命令的差异）。
- **FR-008**: 输出 MUST 含且仅含**一个**版本值（版本值在 stdout 中的出现次数恰为 **1**）；MUST NOT 出现第二个版本值，MUST NOT 出现客户端版本、节点级版本信息、workspace 格式版本或工作区路径。
- **FR-009**: 成功路径 MUST NOT 向 stderr 写任何内容；失败信息 MUST 写 stderr（契约 M-04）。
- **FR-010**: 输出 MUST 是**裸版本值** —— 本命令是**元信息命令**（宪法 §4.2 修订后），MUST NOT 套用 `donkey init` 的「单行 `key=value` 摘要」形态；其 stdout MUST 可被直接取用（例：`V=$(donkey version)`）。
- **FR-011**: 输出 MUST NOT 含任何非确定性内容（时间戳 / 主机名 / 绝对路径 / 进程号）—— 同一条命令两次执行 MUST 产生**逐字节相同**的 stdout。

#### C. 版本语义与来源（FR-012 ~ FR-021）

- **FR-012**: donkey 只有**一个**版本号 —— **软件功能版本**；**图版本 ≡ 软件版本 ≡ 包 / 发布版本**，三者 MUST 是**同一个数**（结构上同源，MUST NOT 存在两个各自维护、可能打架的版本号）。**语义已由 Maintainer 裁决**（Clarifications Q2）："图版本就是包版本，必须保持一致"；"version 的本质意思是软件功能的版本"。
- **FR-013**: 版本值的展示形态 MUST 遵循宪法 §4.5 / 立项书 §1.5.2 的 `vx.y.z` 记法（带 `v` 前缀）；`v` 是**显示前缀**，**在分发元数据可得的常规安装形态下**（即安装元数据值 == 工作树声明值）去掉 `v` 后的底层取值 MUST 与 `pyproject.toml` 的 `version`、包内 `__version__`、工作区清单 `donkey_version` 字段**逐字节一致**（用户可直接用本命令的输出做迁移比对 —— 宪法 D-03）。**不一致时以分发元数据为准**（FR-018）—— 此时输出**不**与工作树声明值 / 清单 `donkey_version` 字段逐字节一致，这**不违反**本条，因为本条的「逐字节一致」口径已限定在常规安装形态下；该不一致情形 MUST 由验收脚本**显式断言**（见 SC-003），MUST NOT 被静默接受。版本值的三个分量 MUST **严格按 §4.5 读作** `x` = 后端 LangGraph 图版本 / `y` = 该图版本内各节点与中间件的 id / `z` = 该节点的修改次数，MUST NOT 对 `y` / `z` 另作解释（Clarifications Q3 的权威表述）。**§4.5 读法登记**：宪法 §4.5 对 `x` 的定义是「**前端版本或** donkey 后端 LangGraph 图版本」；本 Phase 按 Maintainer 裁决取**后者**（后端图版本 ≡ 软件版本 ≡ 包版本），MUST NOT 声称 §4.5 只有这一种读法，亦 MUST NOT 把 `y` / `z` 另作解释（Clarifications Q3 的权威表述）。
- **FR-014**: 当前（F001-P4 交付时）版本值 MUST 等于 `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`；陈旧安装形态下 = **分发元数据值**，FR-018）——「`v0.1.0` 是当前值」这条**硬断言由 SC-003 唯一承载**（工作树声明值 MUST 当前为 `0.1.0`），本条 MUST NOT 自设第二处当前值口径。底层取值的「逐字节一致」口径见 FR-013（FR-014 MUST NOT 重复承载）；按 §4.5 读作 `x=0` / `y=1` / `z=0`（FR-013）。MUST NOT 是 `unknown` 一类的占位串，MUST NOT 是 `dev` 一类的后缀串，MUST NOT 是 `v0.0.0` 一类"图版本 0"的取值。
- **FR-015**: 本命令 MUST **不输出节点清单**、MUST NOT 输出任何节点的**独立**版本号（§4.5 中每个节点各自的 `y` / `z` 编号）—— 主图要到 F004-P7 才建成；MUST NOT 枚举节点。
- **FR-016**: 版本取值的来源 MUST **优先**取**安装分发元数据**查询的结果（标准库的分发元数据接口，查询的发行版名为 `donkey`）—— 与 F001-P2 FR-021「将来若改为动态获取，MUST 使用包元数据查询方式」一致；MUST NOT 读取 `pyproject.toml`（构建期文件，运行期不可靠）。
- **FR-017**: 分发元数据**不可得**时（包未安装 / 非标准安装 / 从源码检出直接运行），MUST 回退到**包自身的 `__version__` 常量**；MUST NOT 抛异常、MUST NOT 使命令失败、MUST NOT 输出空值。
- **FR-018**: 分发元数据与包自身 `__version__` **不一致**时，MUST 以**分发元数据**为准（它代表用户实际安装的那一份），MUST NOT 报错、MUST NOT 因此使命令失败。
- **FR-019**: 版本取值 MUST 只有一个**运行期来源**（即 FR-016 / FR-017 的解析结果）；MUST NOT 存在第二个独立维护的版本定义点（尤其 MUST NOT 另立一个"图版本"常量）—— 否则 §4.5 的 `x+1` 与软件版本会各自漂移。**口径澄清（不计入"来源数"的两处）**：① `donkey/__init__.py` 的 `__version__` —— **就是** FR-017 的回退源本身；② `donkey/core/workspace/manifest.py` 的 `_DONKEY_VERSION` —— 工作区清单的**存储值**（F001-P2 FR-021 锁死、MUST NOT 改动，FR-026）。二者属**别的用途**，MUST NOT 被误判为版本定义点。**跨 Phase 前瞻（F004-P7）**：F004-P7 建图后若需**独立递增** §4.5 的 `x`，即意味着出现第二个版本定义点 —— 该情形 MUST 由 **F004-P7 在其 spec 中显式登记并取得 Maintainer 批准**后才成立；在此之前本条维持为 **MUST**（当前**不是** MUST 的只有「§4.5 `x+1` 伴随软件版本同步递增」这一**联动**，见 Edge Cases「版本取值与来源类」）。
- **FR-020**: 版本取值的解析 MUST 落在**核心层**（`donkey/core/` 下，图是核心层产物），MUST NOT 落在客户端层（`donkey/cli/`）—— 否则 F004-P7 将被迫改客户端，MUST NOT 破坏分层；且本命令 MUST NOT 因此新增 `donkey.core.api` 的库 API（宪法 §4.2 豁免的边界之一）。
- **FR-021**: 版本值 MUST NOT 取自仓库里**第三套**版本号体系（workspace 格式版本，整数 `1`）—— MUST 是软件 / 包版本。

#### D. 只读性与作用域（FR-022 ~ FR-027）

- **FR-022**: `donkey version` MUST 是**只读**的 —— MUST NOT 创建 / 修改 / 删除任何文件，MUST NOT 读取任何工作区，MUST NOT 要求当前目录存在工作区，MUST NOT 产生任何文件系统副作用。
- **FR-023**: 本 Phase MUST NOT 实现 `donkey web version` / `donkey gui version` 的**任何代码或解析器占位**。
- **FR-024**: 本 Phase MUST NOT **实现**节点级版本号的枚举 / 展示（**实现层**约束）—— 与 FR-015（**输出层**约束）**正交**、非重复：FR-015 管「输出里不得出现」，本条管「代码里不得实现」；图尚不存在，且属 F004-P7。
- **FR-025**: 本 Phase MUST NOT 做 F002 `donkey load` 的任何事 —— 尤其 MUST NOT 做「工作区清单 `donkey_version` 与当前运行时版本对比 / 迁移提示」。
- **FR-026**: 本 Phase MUST NOT 改动工作区清单的 `donkey_version` 硬编码值（F001-P2 FR-021 锁死）、MUST NOT 改动包内 `__version__` 常量、MUST NOT 改动 `pyproject.toml` 的版本号。
- **FR-027**: 本 Phase MUST NOT 引入 `langchain` / `langgraph` / `sqlite3` 的导入（宪法 N-04），MUST NOT 引入任何中间件。

#### E. 退出码与段位（FR-028 ~ FR-031）

- **FR-028**: 退出码 MUST 为 —— 成功 `0`（宪法 §4.4 的「全子命令」共用段）；参数用法错误 `1`（**复用 F001-P1 既有口径**，MUST NOT 使用参数解析器的默认失败码 `2`）。**退出码已由 Maintainer 裁决**：D-3。
- **FR-029**: 本 Phase MUST **不占用任何 exit code 子段**、MUST NOT 新增 Error class、MUST NOT 改动退出码映射表的结构与既有条目、MUST NOT 改动段位表（宪法 N-08）。**码值 `1` 的归属登记**：本命令实际返回的 `{0, 1}` 两个码值**均落在宪法 §4.4 的既有表内** —— `0` = 「全子命令」共用段；`1` = F001 段位 `1-10` 内的既有口径（由 F001-P1 的 `DonkeyArgumentParser.error()` 覆写承载，与 `donkey init` 的参数用法错误**同源**）→ 本 Phase **未引入 §4.4 之外的任何码值**，段位表**逐字未改**；`donkey version` **不占用** `1-10` 中的任何子段（子段分配仍属 `donkey init`）。
- **FR-030**: 本 Phase **依宪法 §4.3 第 269 行的既有豁免限定语执行** —— 该句**已含**「**（元信息命令按 §4.2 豁免）**：… 故本句的 1:1 口径对元信息命令**不适用**」，本 Phase 属该豁免的**适用对象**（**不是**「打破宪法」）。具体地，「v1 baseline：1 Phase = 1 子段 = 1 提示词文件 = 1 verify 脚本」对 F001-P4 **不适用**两项 —— ① **Phase ↔ exit code 子段 1:1**（本 Phase **不占用** exit code 子段）；② **Phase ↔ 提示词文件 1:1**（本 Phase **无**提示词文件 —— `harness/features/feature001_phase004_cli_version.md` 不存在，与 F001-P1 / P2 / P3 不同；登记载体 = 宪法第 5 章 [D-20] 的影响面条目）。**授权来源** = 宪法 §4.2.1 + §4.3 的**两处**限定语（「（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）」+ v1 baseline 句的「**（元信息命令按 §4.2 豁免）**」）+ 第 5 章 [D-20]。**归因说明**：`harness/features/README.md` §1.2 / §12 的「1 Phase = 1 提示词文件」表述为**同口径旁证**（非权威源）；该 README §1.5 的原文为「v1 baseline 27 Phase 与 27 子段 1:1 对齐……**是设计选择，不是逻辑必须**」。Maintainer 已决定**不修订**该 README（其非强制），故该例外的**登记义务 MUST 落在本 spec** —— 本 Phase MUST **显式登记**；`version` 的退出码由**既有的全局异常 → 退出码映射表**承载（成功走 `0`「全子命令」共用段；参数用法错误复用 `1` —— 即 F001-P1 契约 M-01 ~ M-05 的既有口径；码值归属登记见 FR-029）。
- **FR-031**: 本 Phase MUST NOT 自设任何宪法例外 —— 元信息命令豁免 MUST **引用**宪法 §4.2（修订后）+ §4.3（修订后）+ 第 5 章 [D-20]，MUST NOT 在未引用它们的情况下声称获豁免。

#### F. 交付与验收（FR-032 ~ FR-038）

- **FR-032**: 系统 MUST 提供黑盒验收脚本 `tests/e2e/phase/verify_phase_f001_p4.py`，MUST 含 **7** 个 `test_scenario_*` 断言函数，与本 spec 的 **7** 个 User Story **1:1** 对应（故事 N ↔ 场景 N）。
- **FR-033**: 验收脚本 MUST NOT import `donkey.*` 的业务代码，只以子进程方式观察退出码、stdout / stderr 与文件系统副作用；MUST 断言 `donkey` 与 `python -m donkey` 两条入口的**等价性**（FR-006）。
- **FR-034**: 既有三套 verify 脚本（F001-P1 / F001-P2 / F001-P3）MUST 保持**全绿**；F001-P1 / P2 / P3 的 FR / SC 编号与断言 MUST 保持不变；若某条既有断言因本 Phase 而失效，MUST 在本 spec 中**显式登记该断言的改写**，MUST NOT 让既有测试红着提交。
- **FR-035**: 本 Phase 的交付物 MUST 通过静态检查（代码规范 + 类型检查）且**零 error**。
- **FR-036**: 宪法修订**已由 Maintainer 于 2026-10-30 前置落地**（**4 处**，见 H 段 (a) / (b) / (b2) / (c)：§4.2.1「元信息命令豁免」小节、§4.3 第 253 行括注、§4.3 第 269 行 v1 baseline 限定语、第 5 章 [D-20]（ADR 编号只增不删，当前最大为 D-19））→ 本 Phase MUST **保持其逐字不变**、实施期 MUST NOT 再改动；Phase 元信息表中的「第一项交付物」相应改为「已前置落地」；MUST NOT 改动 F001-P1 / P2 / P3 的 FR / SC 编号与断言。
- **FR-037**: `donkey init --help` 中过期的模板条目计数 MUST 修正 —— 「46 个模板条目」→ 「**54** 个模板条目」（当前清单口径，权威源 = F001-P3 的 `contracts/cli-contract.md`「全新创建 / 二次 init / --force」三行计数表）；`donkey/core/api.py` 的 `InitResult` docstring 中过期的计数 MUST 同步修正为 **54**（清单条目总数）/ **48**（全新创建的文件型条目数）/ **48**（二次 init 的 `files_skipped`）—— 二者属**实现与文档同步**，MUST NOT 被实现为回改 F001-P1 / P2 已冻结 spec 的 FR 编号与断言。**范围边界**：F001-P2 的 `contracts/*.md` 属**该 Phase 的冻结快照**（F001-P3 的契约文档已显式登记「P2 是 46/40/0；P3 的 54 = 46 + 8」这一差异并作为当前权威口径），本 Phase MUST NOT 改动那三份文档。
- **FR-038**: 顶层解析器 MUST **NOT** 提供 `--version` 标志 —— `donkey --version` MUST 以退出码 `1` 失败（顶层解析器**不提供**该标志；**实测**报错为「the following arguments are required: command」，因 `add_subparsers(dest="command", required=True)` 的必填校验先于未识别参数检查触发；断言以**退出码 == 1 且 stdout 不含任何版本号**为准，MUST NOT 依赖具体报错措辞）；版本查询的唯一入口是 `version` 子命令（Clarifications Q4 的权威表述）。

#### G. 与其它 Phase / Feature 的关系（范围外登记）

- **本 Phase 只登记、不实现**：
  - **客户端版本入口** —— `donkey web version` / `donkey gui version` 归 **F005 / F006**（FR-005 / FR-023）。宪法 N-11 / §2.8 要求 v1 三端对等、任何客户端不允许出现"功能仅 cli 独有" —— 本 Phase 只在 cli 端提供版本入口，web / gui 端的版本入口由 F005 / F006 各自补齐，属**已登记的前序缺口**，MUST NOT 被理解为"三端已对等"。
  - **节点级版本号** —— 节点级 `vx.y.z` 属 **F004-P7**（FR-015 / FR-024）。
  - **包版本与工作区清单的对比 / 迁移提示** —— 属 **F002 `donkey load`**（FR-025）。
  - **workspace 格式版本**（整数 `1`）—— 不暴露（FR-021）。
  - **三套版本号体系的其余关系** —— 至今**全文没有任何规定**；本 Phase MUST NOT 自设其关系（MUST NOT 推断 workspace 格式版本（整数 `1`）与软件版本之间的任何对应关系 —— FR-021）。
  - **用户手册的过期文案** —— `docs/User_Guide/01_init_workspace.md` 仍把 `python -c "import donkey; print(donkey.__version__)"` 写成查版本方式，并把「`donkey init --help` 仍写 46 个模板条目」列为已知缺口 K-1 → 本 Phase 交付 `donkey version` 后该手册即过期；但**文档修订归独立的文档 Phase**，本 Phase MUST NOT 修改 `docs/` 下的任何文件（属范围外登记）。

#### H. 宪法修订文本（Maintainer 已批准 · 已落地 · MUST 逐字保持）

> 宪法修订**已落地**（Maintainer 于 2026-10-30 前置落地）—— 本 Phase MUST **保持其逐字不变**，实施期 MUST NOT 再改动（FR-036）。以下**四处**修订内容**已由 Maintainer 批准**（宪法 §6.2 第 2 条）；MUST NOT 改写措辞、MUST NOT 缩减条款；**本 spec MUST NOT 自设任何宪法例外**（FR-031）。
> 载体文件：`.specify/memory/constitution.md`。
>
> **（2026-10-30 补登）**：本 Phase 另交付两项变更，由宪法 **[D-21]** / **[D-22]** 登记（工作区清单字段变更 / `donkey init` 执行报告变更）—— **H 段 (a) / (b) / (b2) / (c) 的登记文本逐字不变**（宪法 §6.2「ADR 编号只增不删」）；两项变更的登记详见文末「后续修订登记」段。

- **(a) 宪法 §4.2 新增「元信息命令豁免」条款**：

  > F 编号表锁定的是**核心功能**的一级命令；**元信息命令**（只读地暴露工程元信息、不承载业务能力、不占用 exit code 段位、不需要 `donkey.core.api` 库 API）**豁免 F 编号登记**，当前唯一成员是 `donkey version`。
  > 边界：元信息命令 MUST NOT 被后续 Feature 扩张为业务命令 —— 一旦它开始承载可失败的业务能力（需要 Error class / exit code 段位 / 库 API），MUST 先按 §6.2 Governance 流程取得 F 编号。

- **(b) 宪法 §4.3 的「一级命令已被 F 编号锁死」加限定语**：

  > 「**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免」。

  > **核对基准（不改本段登记文本 —— Clarifications Q8 要求 H 段 (a) / (b) / (b2) 逐字不变）**：本段登记的是该括注的**内层文本**；宪法第 253 行的实文为 `（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）`（**外层圆括号属句子的一部分**，不在本段登记文本内）。T005⑧ / SC-012 的「逐字一致」比对 MUST 以**内层文本**为准（MUST NOT 因外层圆括号判 FAIL）；完整句的逐字文本见 [contracts/constitution-amendment.md](contracts/constitution-amendment.md) §2「改为（修订后）」代码块。

- **(b2) 宪法 §4.3 的 v1 baseline 句限定语**：

  > **（元信息命令按 §4.2 豁免）**：§4.2.1 定义的元信息命令**不占用** exit code 子段、**不需要**提示词文件，故本句的 1:1 口径对元信息命令**不适用**（当前唯一成员 = `donkey version`，见 [D-20]）。

- **(c) 宪法 [D-20] 行的落地文本（逐字）**（宪法第 5 章表尾新增 [D-20]；ADR 编号只增不删，当前最大为 D-19）：

  ```text
| **[D-20]** | **元信息命令豁免 F 编号登记** —— 版本号查询不可缺少但不属于核心功能，套用 F 编号会污染 §4.2 的"核心功能"语义与 §4.5 的图版本口径。**影响面**：宪法 §4.2 新增「元信息命令豁免」小节（§4.2.1）+ §4.3 的**两处**限定语（「（**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免）」+ v1 baseline 句的「**（元信息命令按 §4.2 豁免）**」）+ `specs/001-donkey-init-workspace/phase-4-cli-version/` 全套（F001-P4 `cli_version` Phase）。**不变项**：F001-P1 / P2 / P3 的 FR / SC 编号与断言**一律不动**；§4.3 的规则 A / 规则 B 两张表逐字未动。**迁移路径**：无（纯新增能力，不改变任何既有行为）。**边界**：元信息命令一旦开始承载可失败的业务能力（需要 Error class / exit code 段位 / 库 API），MUST 先按 §6.2 取得 F 编号 | 立项书 §1.5.2 + §3.2.1 + F001-P4 Maintainer 裁决（2026-10-30） |
  ```

  > **登记说明**：[D-20] 的影响面条目即为 F001-P4 在项目索引中的**登记载体** —— `harness/features/README.md` 按 D-3 的决定**逐字未改**（SC-012），故本 Phase MUST NOT 在该 README 中新增 F001-P4 行（新增即构成对被豁免的索引表的修订）。宪法修订共 **4 处**（§4.2.1 / §4.3 第 253 行括注 / §4.3 第 269 行 v1 baseline 限定语 / [D-20]），本 Phase MUST **保持其逐字不变**（FR-036 / SC-012）。

#### 需求追溯矩阵

| 需求组 | 需求条目 | e2e 黑盒场景 | 成功判据 |
|---|---|---|---|
| A. 命令面与入口 | FR-001 ~ FR-006 | 场景 1 / 4 / 5 / 6 | SC-001 / SC-004 / SC-013 / SC-014 |
| B. 输出契约 | FR-007 ~ FR-011 | 场景 1 / 2 / 7 | SC-002 / SC-015 |
| C. 版本语义与来源 | FR-012 ~ FR-021 | 场景 2 / 3 / 6 | SC-002 / SC-003 / SC-007 |
| D. 只读性与作用域 | FR-022 ~ FR-027 | 场景 7 / 全部场景 | SC-005 / SC-010（+ 非 SC 载体） |
| E. 退出码与段位 | FR-028 ~ FR-031 | 场景 5 + 退出码核对 | SC-006 / SC-008 / SC-012 |
| F. 交付与验收 | FR-032 ~ FR-038 | 全部 7 个断言 | SC-001 / SC-009 / SC-010 / SC-011 / SC-012 / SC-013 / SC-016 |
| H. 宪法修订文本 | FR-036（文本见 H 段） | 宪法登记核对 | SC-012 |

> **脚注**：FR-023（不实现 `donkey web version` / `donkey gui version`）、FR-024（不实现节点级版本号）、FR-025（不做 F002 `donkey load` 的版本对比）三条**没有专属 SC**，其自动化载体为任务层的门禁冒烟与场景断言（实施期由 /speckit.tasks 落到具体任务：FR-023 / FR-025 → T037 的门禁冒烟 ⑤⑥；FR-024 的**输出层** → T020 / T021 的否定断言、**实现层** → T008 / T009 / T010 的函数面限定（新模块 MUST 只导出 `resolve_version` / `version_string` 两个函数，无任何节点枚举入口））。

### Key Entities

- **`version` 元信息命令**：顶层一级子命令，**无参数**、**只读**、不占用 exit code 子段、不需要 `donkey.core.api` 库 API —— 按宪法 §4.2（修订后）/ §4.2.1 豁免 F 编号登记；当前唯一成员。
- **软件功能版本（唯一版本号）**：donkey 的**唯一**版本号 —— **图版本 ≡ 软件版本 ≡ 包 / 发布版本**（FR-012）。当前底层取值 `0.1.0`，展示形态 `v0.1.0`（`v` 为显示前缀）；取值来源优先为**安装分发元数据**、不可得时回退包自身 `__version__` 常量（FR-016 ~ FR-018）；运行期**只有一个**取值来源（FR-019），解析落在核心层（FR-020）。
- **常规安装形态 / 陈旧安装形态（判定谓词）** —— 本 spec 全文反复使用这两个形态词，其**可判定定义**如下（判据一律以此为准，MUST NOT 以「文档里写了什么」为准）：
  | 形态 | 判定条件 | 后果 |
  |---|---|---|
  | **常规安装形态** | **安装分发元数据值 == 工作树声明值**（`importlib.metadata.version("donkey")` == `pyproject.toml` 的 `version`） | FR-013 / FR-014 / SC-002 / SC-003 的「逐字节一致」**全部成立**；输出底层取值 == 两者 == 包内 `__version__` == 工作区清单 `donkey_version` 字段 |
  | **陈旧安装形态** | 两者**不等**（安装的那一份已陈旧） | 输出底层取值 MUST == **分发元数据值**（FR-018）；MUST NOT 断言输出 == 工作树声明值 / 清单 `donkey_version` 字段（假失败） |
  | **陈旧清单形态**（**陈旧安装形态**的一个子集） | **工作树声明值 != 工作区清单 `donkey_version` 字段**（清单值被 F001-P2 FR-021 锁死为**当时的**版本） | 「输出 vs 清单字段」的比对 MUST **跳过**（US2 验收场景 2 / Assumptions「版本号 bump 的跨 Phase 联动」） |
  > **单一事实源**：分发元数据值（FR-016）· 工作树声明值 = `pyproject.toml` 的 `version` · 清单字段 = 工作区清单 `donkey_version` · 包内 `__version__` —— 四者在本 Phase 当前**恒等**（皆 `0.1.0`）；任何形态差异 MUST 由上表的口径消化，MUST NOT 静默产生假失败。
- **版本值的 §4.5 读法**：`v0.1.0` **严格**读作 `x=0`（后端 LangGraph 图版本）/ `y=1`（该图版本内各节点与中间件的 id）/ `z=0`（该节点的修改次数），MUST NOT 另作解释（FR-013）；本 Phase 不输出节点清单（F004-P7 落地，FR-015）。**§4.5 读法登记**：宪法 §4.5 对 `x` 的定义是「**前端版本或** donkey 后端 LangGraph 图版本」；本 Phase 按 Maintainer 裁决取**后者**（后端图版本 ≡ 软件版本 ≡ 包版本），MUST NOT 声称 §4.5 只有这一种读法，亦 MUST NOT 把 `y` / `z` 另作解释（Clarifications Q3 的权威表述）。
- **底层取值与显示前缀**：`v0.1.0` 的 `v` 是显示前缀；**在常规安装形态下**去掉 `v` 后的 `0.1.0` 与 `pyproject.toml` 的 `version` / 包内 `__version__` / 工作区清单 `donkey_version` 字段**逐字节一致**（FR-013 口径）—— 用户可直接用本命令的输出做迁移比对；不一致时以分发元数据为准（FR-018）。
- **术语对齐（spec ↔ data-model §6）**：本 spec 沿用「**版本值**」一词指**展示层**的 stdout 输出（`v0.1.0`）—— 它与 data-model §6 术语表中的「**展示值**」**同义**（两个名字指同一个东西，非两套概念）；data-model 的「**底层取值**」= 不带 `v` 前缀的本体（`0.1.0`）。MUST NOT 混用：凡指 stdout 那个字符串时用「版本值 / 展示值」，凡指底层取值时 MUST 用「底层取值」；data-model §6 的「不得与之混用」条款**同样适用于**本 spec 的「版本值」一词。
- **节点级版本号**：`vx.y.z` 中的 `y`（节点 id）/ `z`（节点修改次数）所在的**节点级**版本 —— 属 F004-P7；本 Phase **不实现、不展示**（FR-015 / FR-024）。
- **workspace 格式版本**：工作区清单 `version` 字段的整数 `1` —— 仓库里**第三套**版本号体系；本 Phase **不暴露**（FR-021）。
- **客户端版本入口**：`donkey web version` / `donkey gui version` —— 归 F005 / F006；本 Phase **只登记、不实现**（FR-005 / FR-023），是宪法 N-11 / §2.8 下**已登记的前序缺口**。
- **版本输出**：stdout 的**单行裸版本值**（`v0.1.0`），与 `donkey init` 的「单行 `key=value` 摘要」形态**有意不同**（元信息命令，FR-010）；**确定性**（两次执行逐字节相同，FR-011）。
- **已知缺口与风险登记**：**节点级版本号未暴露**（F004-P7）+ **客户端版本入口缺失**（F005 / F006）+ **三套版本号体系关系未规定** —— 均登记于 Edge Cases「其它边界」，v1 不补。

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 验收脚本 `tests/e2e/phase/verify_phase_f001_p4.py` 的 **7** 个断言函数 100% 通过（零失败），且 **7** 个函数与本 spec 的 **7** 个 User Story **1:1** 对应（故事 N ↔ 场景 N）。
- **SC-002**: `donkey version` 的退出码为 `0`；stdout **恰好一行**，该行**去掉行终止符后**的内容**逐字节等于** `resolve_version()` 的解析结果（**常规安装形态下** = `v0.1.0`；陈旧安装形态下 = **安装分发元数据值** —— 判据口径见 FR-007 / FR-018 / SC-003）；stdout 中版本值的出现次数恰为 **1**（MUST NOT 出现第二个版本值）；stderr 为空（FR-007 ~ FR-009）。
- **SC-003**: 版本值 MUST 匹配 `^v\d+\.\d+\.\d+$`；**在分发元数据可得的常规安装形态下**去掉 `v` 后的底层取值 MUST 与工作区清单的 `donkey_version` 字段**逐字节一致**（FR-013）；**常规安装形态下**当前值 MUST 为 `v0.1.0`（FR-014）；输出中**节点清单 / 节点独立版本号的出现次数为 0**（FR-015 / FR-024）。**期望值的取数口径（双比对）**：验收脚本 MUST 读取**两个**来源并分别断言：① **工作树声明值** = `pyproject.toml` 的 `version`（MUST 另行断言其当前为 `0.1.0` —— FR-014 的自动化载体）；② **安装分发元数据值** = `importlib.metadata.version("donkey")`（**允许**使用标准库 `importlib.metadata`，MUST NOT import `donkey.*` 业务代码 —— FR-033）。**断言规则**：两者相等 → 输出底层取值 MUST == 二者；两者不等（陈旧安装）→ 输出底层取值 MUST == **安装分发元数据值**（FR-018），且 MUST **显式断言**该不等情形、MUST NOT 断言输出 == 工作树声明值或清单 `donkey_version` 字段（那会产生假失败）。**清单字段比对的额外前提**：工作区清单 `donkey_version` 被 F001-P2 FR-021 锁死为**当时的**版本，故「输出 vs 清单字段」的比对 MUST 以「**工作树声明值 == 清单字段**」为前提 —— 不成立时（**陈旧清单**形态）MUST **跳过**该比对，MUST NOT 断言输出 == 清单字段（假失败）；改以**分发元数据 / 工作树声明值**为准（见 Key Entities「常规安装形态 / 陈旧安装形态」与 Assumptions「版本号 bump 的跨 Phase 联动」）。MUST NOT 因安装形态漂移而产生**假失败**。
- **SC-004**: `donkey version` 与 `python -m donkey version` 两条入口的**退出码相同**、stdout **逐字节相同**、stderr 均为空（FR-006 / FR-033）。控制台脚本不可用（解析不到属于当前工作树的 `donkey`）时，验收脚本 MUST 打印**一次显式告警**到 stderr（**非静默跳过**）并只断言模块入口一侧；该降级情形 MUST 在 verify 脚本的 stderr 中可见。
- **SC-005**: `donkey version` 的文件系统副作用数为 **0**（执行前后目标目录树的文件数 / 目录数 / 内容指纹全部不变）；命令在**工作区不存在**（含 manifest 缺失或非法）的目录下执行同样以退出码 `0` 结束（FR-022）。
- **SC-006**: 参数用法错误 —— `donkey version --bogus` / `donkey version web` / `donkey version extra` 三类输入的退出码**均为 `1`**（MUST NOT 为 `2`），错误信息写 stderr 且含用法提示，stdout 为空（FR-002 / FR-028）。
- **SC-007**: 在**安装分发元数据不可得**的前提下执行 `donkey version`，命令**仍以退出码 `0` 结束**，stdout 仍是一个**确定可解析**的版本值（MUST NOT 为空 / 抛异常），且该值**不依赖**安装形态（取不到元数据时 MUST NOT 影响版本值 —— FR-017；FR-018 的**不一致**情形以**分发元数据**为准）；该回退路径 MUST 有单元测试覆盖。
- **SC-008**: 退出码占用核对 —— 本 Phase 新增的 exit code 子段数 = **0**、新增的 Error class 数 = **0**、退出码映射表的条目集合与结构**逐项未变**；本 Phase 代码路径实际可返回的退出码集合 = `{0, 1}`（FR-029 / FR-030）。
- **SC-009**: 既有三套 verify 脚本（F001-P1 **7** 个 / F001-P2 **14** 个 / F001-P3 **16** 个断言函数）100% 仍通过；F001-P1 / P2 / P3 的 FR / SC 编号与断言**逐字未改**（除本 spec 显式登记的改写外）（FR-034）。
- **SC-010**: 静态检查（代码规范 + 类型检查）零 error；**本 Phase 新增 / 改动的代码文件**对框架与 sqlite3 的导入次数 = **0** —— ① `donkey/core/version.py`（新增）：`langchain` / `langgraph` / `sqlite3` / `argparse` / `click` / `typer` 的导入次数 = **0**（宪法 N-04 / N-05）；② `donkey/cli/cli_client.py`（改动）：`langchain` / `langgraph` / `sqlite3` 的导入次数 = **0**（宪法 N-04）。**范围界定**：仓库中**既有**的 `donkey/core/workspace/sqlite3_templates.py` 对 `sqlite3` 的导入（以及 `donkey init` 运行时经上游 saver 触发的 `langgraph` 导入）属**既有事实**，MUST NOT 被计入本条判据 —— 宪法 N-04 约束的是「**直接** import」，且该文件属 F001-P2 的冻结产物；本 Phase MUST NOT 扩大范围去整改它（FR-027 / FR-035）。
- **SC-011**: 单次 `donkey version` 执行在 **5 秒**内返回（纯内存 / 元数据查询，无网络、无文件写入）。
- **SC-012**: 宪法修订登记核对 —— **四处**：① 宪法 §4.2 含「元信息命令豁免」条款（§4.2.1 豁免小节）、② §4.3 含「**核心功能的**一级命令已被 F 编号锁死；元信息命令按 §4.2 豁免」限定语、③ §4.3 的 v1 baseline 句含「**（元信息命令按 §4.2 豁免）**」限定语、④ 第 5 章含 **[D-20]**（**四处的实际措辞 MUST 与本 spec H 段 (a) / (b) / (b2) / (c) 登记的文本逐字一致**）；且 `harness/features/README.md` **逐字未改**（Maintainer 决定不修订该惯例表述与索引表，F001-P4 由 [D-20] 的影响面条目登记）（FR-030 / FR-036）。
- **SC-013**: `donkey --help` 的子命令列表 MUST 出现 `version` 条目（可发现性）；`donkey version --help` 的退出码为 `0`（FR-003 / FR-004）。
- **SC-014**: 顶层解析器**不提供** `--version` 标志 —— `donkey --version` MUST 以退出码 `1` 失败（**实测**报错为「the following arguments are required: command」，因 `add_subparsers(dest="command", required=True)` 的必填校验先于未识别参数检查触发；断言以**退出码 == 1 且 stdout 不含任何版本号**为准，MUST NOT 依赖具体报错措辞），MUST NOT 输出任何版本号（FR-038）。
- **SC-015**: 同一条命令连续执行两次，stdout **逐字节相同**（确定性输出；FR-011）。
- **SC-016**: 过期计数修正 —— `donkey init --help` 的输出 MUST NOT 再出现「46 个模板条目」，且 MUST 出现「**54** 个模板条目」；`donkey/core/api.py` 的 `InitResult` docstring MUST 含 **54** / **48** 三个计数的当前口径（清单条目总数 / 全新创建文件数 / 二次 init 跳过数），MUST NOT 再出现 **46** / **40**；F001-P2 的三份 `contracts/*.md` MUST **逐字未改**（FR-037）。

---

## Assumptions

- **前置 Phase 已完成**：F001-P1（`cli_validation`）/ P2（`template_skeleton`）/ P3（`builtin_tools`）的退出条件全部满足；其已实现的 CLI 解析器、退出码映射表、工作区清单能力**不**被本 Phase 修改（仅追加一个子命令 + 一处版本取值解析）。
- **图尚不存在**：LangGraph 主图要到 **F004-P7 `agent_loop`** 才建成（立项书 §4.4.2：v1.0.0 发布时主图共 10 个节点，节点 id 形如 `{Middleware.name}.{hook}`）；仓库内当前**没有任何** LangGraph State / 节点定义。本 Phase 交付时图**不存在** —— 故不暴露任何节点级版本信息（FR-015）。
- **只有一个版本号**：仓库里原本并存**三套**版本号体系（软件 / 包 / 发布版本、图版本、workspace 格式版本）；Maintainer 已裁决「**图版本就是包版本，必须保持一致**」，故前两套在本 Phase **合并为同一个数**（FR-012），**第三套（workspace 格式版本，整数 `1`）不暴露**（FR-021）。三套之间的**其它**关系至今**全文没有任何规定** —— 本 Phase MUST NOT 自设其关系。
- **宪法修订先行**：本 Phase 的授权基础 = 宪法 §4.2 新增「元信息命令豁免」小节（§4.2.1）+ §4.3 的**两处**限定语 + 第 5 章新增 [D-20]（ADR 编号只增不删，当前最大为 D-19）；[D-20] 的动机 = 版本号查询不可缺少但不属于核心功能，套用 F 编号会污染 §4.2 的「核心功能」语义与 §4.5 的图版本口径；**影响面** = 宪法 §4.2 新增「元信息命令豁免」小节（§4.2.1）+ §4.3 的**两处**限定语 + `specs/001-donkey-init-workspace/phase-4-cli-version/` 全套（F001-P4 `cli_version` Phase）；**迁移路径** = 无（纯新增能力，不改变任何既有行为）；**不变项** = F001-P1 / P2 / P3 的 FR / SC 编号与断言**一律不动**；§4.3 的规则 A / 规则 B 两张表逐字未动。**落地状态**：宪法修订**已由 Maintainer 于 2026-10-30 前置落地**（4 处，见 H 段 (a) / (b) / (b2) / (c)）→ 本 Phase MUST **保持其逐字不变**、实施期 MUST NOT 再改动（FR-036 / SC-012）。
- **豁免边界**：元信息命令 MUST NOT 被后续 Feature 扩张为业务命令 —— 一旦 `version` 开始承载可失败的业务能力（需要 Error class / exit code 段位 / 库 API），MUST 先按宪法 §6.2 Governance 流程取得 F 编号。
- **元信息命令的实现形态**：本命令**不需要** `donkey.core.api` 库 API（宪法 §4.2 豁免的边界之一）；但版本取值的解析 MUST 落在核心层（FR-020），以免 F004-P7 被迫改客户端层。
- **本 Phase 不承担的工作**：节点级版本号（F004-P7）/ 客户端版本入口（F005 / F006）/ 工作区清单的版本对比与迁移提示（F002）/ 三套版本号体系的关系规定 —— 全部属其它 Phase / Feature。
- **运行平台**：验收以当前开发平台为准；本命令不触碰文件系统，故平台差异（路径分隔符、只读挂载等）不影响判据。
- **环境与安装形态**：验收覆盖「已安装」与「未安装 / 非标准安装（从源码检出直接运行）」两类形态；后者由分发元数据不可得路径承载（FR-017 / SC-007）。验收脚本的**期望版本值按双比对口径取数**：工作树声明值（`pyproject.toml` 的 `version`）与安装分发元数据值（`importlib.metadata.version("donkey")`）分别读取；两者相等时以二者为期望值，两者不等（陈旧安装）时以**安装分发元数据值**为期望值（FR-018）—— 以免安装形态漂移导致假失败（SC-003）。
- **冻结快照的既有惯例**：F001-P2 的 `contracts/*.md` 保留其 Phase 当时的计数（46 / 40），差额由 F001-P3 的契约文档显式登记为当前口径（54 / 48）—— 本 Phase 的文案同步**只改代码侧**（`--help` 与 `api.py` docstring），MUST NOT 回改已冻结的快照（FR-037）。
- **版本号 bump 的跨 Phase 联动（登记）**：SC-003 把当前版本值钉死为 `v0.1.0`（FR-014 引用该口径，MUST NOT 重复承载硬断言）。将来任一 Phase 把 `pyproject.toml` 的 `version` bump（如 F002 → `0.2.0`）时，MUST **同步**更新 ① 本 spec 的 SC-003 的当前值、② 本 Phase 验收脚本中"工作树声明值当前为 `0.1.0`"的那条断言 —— 否则 SC-003 会变红（该断言 MUST NOT 被删）。**此外（清单比对的可跳过口径）**：工作区清单的 `donkey_version` 字段被 F001-P2 FR-021 **锁死**为**当时的**版本（`0.1.0`），本 Phase MUST NOT 改动它（FR-026）—— 故 bump 之后「输出底层取值 vs 清单 `donkey_version` 字段」的比对**必然不相等**；该比对的**前提** = 「**工作树声明值 == 清单字段**」，不成立时（**陈旧清单**形态）验收脚本 MUST **跳过**该比对，MUST NOT 断言输出 == 清单字段（那会产生假失败），改以**分发元数据 / 工作树声明值**为准（FR-018 / SC-003 / US2 验收场景 2）。
- **设计观察（登记，非违例）**："元信息命令不需要 `donkey.core.api` 库 API"（宪法 §4.2 修订后）在**进程层面尚未解耦** —— `donkey/cli/cli_client.py` 模块级已 `import donkey.core.api`（既有结构），故 `donkey version` 仍会加载 core 的 init / manifest / sqlite3_templates 导入链。**实测该链纯标准库**（`langgraph` **不**进入 `sys.modules`）→ 不构成违例（FR-020 的口径是"MUST NOT **新增**库 API"）；若将来要把元信息命令彻底解耦，MUST 另开决策。

---

## 后续修订登记（不改写本 spec 的 FR / SC 原文）

> **本节只做指针 + 口径登记** —— 上文 FR / SC 的**编号与原文一律不动**，保住本 Phase 的历史记录。
> 登记的两项变更**先于** spec / plan / tasks 落地（**流程倒置**，见本节末的「流程倒置追认」）——
> 授权来源 = 宪法第 5 章 **[D-21]** / **[D-22]** + Maintainer 裁决（2026-10-30）。

### 1 · FR-026 的口径变更（宪法 [D-21] · 工作区清单字段变更）

| 项 | 本 spec 原文（**历史事实**，不改写） | 现行口径 |
|---|---|---|
| **FR-026** | 本 Phase MUST **NOT** 改动工作区清单的 `donkey_version` 硬编码值（F001-P2 FR-021 锁死）、MUST NOT 改动包内 `__version__` 常量、MUST NOT 改动 `pyproject.toml` 的版本号 | **已追认改动**（宪法 [D-21]）：清单的 `donkey_version` 由硬编码 `"0.1.0"` 改为**动态取值** —— `donkey.core.version.resolve_version()`（优先安装分发元数据、不可得时回退包内 `__version__`）。**授权来源**：① 宪法 [D-21]；② F001-P2 FR-021 **自身预留**的演进路径（"将来若改为动态获取，MUST 使用包元数据查询方式"）；③ FR-021 的原始理由"MUST NOT 通过导入内部版本符号获取（循环依赖风险）"因 `donkey.core.version` 的诞生而**已不复存在**（`donkey/__init__.py` **零 import** → 引用不成环）。**变更的必要性**：硬编码的真实代价是 —— 版本 bump 后**新建**的工作区仍记旧版本号 → F002 `donkey load` 的迁移提示**误判**工作区陈旧。FR-026 的**其余两条**（包内 `__version__` / `pyproject.toml` 版本号）MUST NOT 改动 —— **实际未动** |
| **Edge Cases「阶段边界类」** | "本 Phase **不**触碰工作区清单的 `donkey_version` 硬编码值（F001-P2 FR-021 锁死）、**不**改包内 `__version__`、**不**改 `pyproject.toml` 版本号" | 同上 —— 该条以**本登记段追认**，原文 MUST NOT 删改 |
| **清单字段集** | —— | 工作区清单由**四字段**（`version` / `name` / `created_at` / `donkey_version`）改为**三字段**（`name` / `created_at` / `donkey_version`）—— 宪法 [D-21] 修订 D-01；原"版本号（整数 `1`）"字段**全仓无人读取**且与 `donkey_version` 并排时读作"两个打架的版本号" |

### 2 · 既有断言的显式改写登记（宪法 [D-21] / [D-22] · FR-034）

> **FR-034 要求**："若某条既有断言因本 Phase 而失效，MUST 在本 spec 中**显式登记该断言的改写**" ——
> 本节即该登记处。**登记口径**：逐条给出「文件 / 位置 / 原断言 / 新断言 / 改写理由」；
> **实施前 MUST 逐行核对**被改文件的**实际内容**，MUST NOT 以任何概括性计数为准
> （沿用 F001-P3 FR-068 的登记口径）。

**（a）宪法 [D-21] —— 工作区清单字段变更**

| # | 文件 / 位置 | 原断言 | 新断言 | 理由 |
|---|---|---|---|---|
| 1 | `tests/unit/test_template_skeleton.py` · `test_manifest_field_minimal` | `set(written.keys()) == {"version", "name", "created_at", "donkey_version"}` | `== {"name", "created_at", "donkey_version"}` | "版本号"字段已删除 |
| 2 | 同上 | `written["version"] == 1` / `isinstance(written["version"], int)` | （**删除**） | 同上 |
| 3 | 同上 | `written["donkey_version"] == "0.1.0"` | `== resolve_version()` | 硬编码 → 动态取值；MUST NOT 断言字面量（否则版本 bump 后假失败） |
| 4 | 同上 · `test_manifest_json_encoding` | `'\n  "version"' in text` | `'\n  "name"' in text` | 同 #1 |
| 5 | 同上 · 其余 2 处 `set(written.keys())` 断言 | 同 #1 | 同 #1 | 同上 |

**（b）宪法 [D-22] —— `donkey init` 执行报告变更**

| # | 文件 / 位置 | 原断言 | 新断言 | 理由 |
|---|---|---|---|---|
| 6 | `tests/unit/test_cli_client.py` · `test_cli_force_warning_line` | 摘要**六个字段**元组；「不带 force 时 stdout **恰好 1 行**」/「带 force 时**恰好 2 行**」 | 摘要**九个字段**元组；「摘要 1 行 + 图例 1 行 + N 条明细（+ force 时警告 1 行，置于**末尾**）」 | 摘要按「对象 × 动作」分解 + 新增逐项明细 |
| 7 | `tests/unit/test_template_skeleton.py` · 5 处 `render_templates` 计数断言 | `created, skipped = render_templates(...)` + 二元组断言 | `_project(render_templates(...))` + 五类计数投影 | `render_templates` 改返回逐项明细 |
| 8 | 同上 · `test_render_force_overwrite` | `created == 1`（**覆盖**被并入新建） | `files_created == 0` 且 `files_overwritten == 1` | **覆盖 ≠ 新建**（FR-006 字面口径） |
| 9 | 同上 · `test_init_workspace_counts_and_manifest` | `InitResult` 字段清单 = 6 项 | = 10 项（v1 六项 + 四项新增）+ `INIT_RESULT_CONTRACT_VERSION == 2` | 库 API **契约 v2**（FR-006 的"无版本号不得变更"） |
| 10 | `tests/unit/test_builtin_tools.py` · `test_counts_across_init_modes` | `(templates, created, skipped)` 三元组（54/47/1 等） | 六元组（+ `files_overwritten` / `dirs_created` / `dirs_skipped`） | 同 #8 |
| 11 | `tests/e2e/phase/verify_phase_f001_p2.py` · 场景 1 | `"templates=54 created=48 skipped=0"` | `"templates=54 files_created=48 files_overwritten=0 files_skipped=0 dirs_created=6 dirs_skipped=0"` | 摘要分解 |
| 12 | 同上 · 场景 5 字段元组 | 六个字段名 | 九个字段名 | 同上 |
| 13 | `tests/e2e/phase/verify_phase_f001_p3.py` · 场景 1 / 8 / 9 | `"templates=54 created=48 skipped=0"` / `"created=1 skipped=47"` / `"created=47 skipped=1"` | 九字段对应口径（`--force` 行为 `files_created=0 files_overwritten=47 files_skipped=1`） | 同上 |

**MUST NOT 触碰**的持久不变量（沿用 F001-P3 FR-069）："工作区内无**智能体入口文件**"、
"运行期依赖恰为 1 个"、"用户内容不被破坏"、"渲染产物 MUST 无 `{{ … }}` 占位符残留"
—— **四条一律未动**；F001-P1 / P2 / P3 的 **FR / SC 编号**一律不动。

### 3 · 宪法 ADR 的补登（Phase 元信息「授权基础」/ H 段）

| ADR | 主题 | 与本 Phase 的关系 |
|---|---|---|
| **[D-20]** | 元信息命令豁免 F 编号登记 | 本 Phase 的**授权基础**（H 段 (a)/(b)/(b2)/(c) 登记文本**逐字不变**） |
| **[D-21]** | 工作区清单删除"版本号"字段、`donkey_version` 改动态取值 | 本 Phase 的 FR-026 口径变更 + 清单字段集变更（见 §1） |
| **[D-22]** | `donkey init` 的执行报告改为「摘要 + 逐项明细」，计数按「对象 × 动作」分解 | 本 Phase 的库 API 契约 v2 + init 输出形态 + 断言改写（见 §2） |

> H 段 (a) / (b) / (b2) / (c) 的**登记文本 MUST 逐字不动**（宪法 §6.2「ADR 编号只增不删」）。

### 4 · 流程倒置追认（宪法 §4.1 TDD）

> **本 Phase 的两项变更**（[D-21] 工作区清单字段变更、[D-22] `donkey init` 执行报告变更）
> **先于** spec / plan / tasks 落地，偏离了宪法 §4.1 的「spec → plan → tasks → code」序。
>
> **追认**：两项变更的授权来源 = 宪法 [D-21] / [D-22] + Maintainer 裁决（2026-10-30），
> 本节与其余三节即**事后补齐的登记**。**后续变更 MUST 恢复「spec → plan → tasks → code」序** ——
> 本条 MUST NOT 削弱宪法 §4.1 的 TDD 四件套要求，也 MUST NOT 自设任何宪法例外（FR-031）。
