# Specification Quality Checklist: F001-P2 `template_skeleton` —— `donkey init` workspace 模板骨架幂等生成

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-23
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] CHK001 No implementation details (languages, frameworks, APIs)
- [x] CHK002 Focused on user value and business needs
- [x] CHK003 Written for non-technical stakeholders
- [x] CHK004 All mandatory sections completed

## Requirement Completeness

- [x] CHK005 No [NEEDS CLARIFICATION] markers remain
- [x] CHK006 Requirements are testable and unambiguous
- [x] CHK007 Success criteria are measurable
- [x] CHK008 Success criteria are technology-agnostic (no implementation details)
- [x] CHK009 All acceptance scenarios are defined
- [x] CHK010 Edge cases are identified
- [x] CHK011 Scope is clearly bounded
- [x] CHK012 Dependencies and assumptions identified

## Feature Readiness

- [x] CHK013 All functional requirements have clear acceptance criteria
- [x] CHK014 User scenarios cover primary flows
- [x] CHK015 Feature meets measurable outcomes defined in Success Criteria
- [x] CHK016 No implementation details leak into specification

## Notes

### 第 1 轮校验（2026-10-23）—— 自检结果

**逐项复核记录**：

| 项 | 结论 | 依据 / 具体问题 |
|---|---|---|
| CHK001 | PASS（附条件说明） | spec 正文以"用户能拿到什么 / 用户看到什么"为主线。**但**本 Phase 的契约天然涉及文件与配置清单（46 条模板条目、6 个必填目录、4 个 manifest 字段），故 spec 必须逐项锁定这些**产物形态**（否则下游无法判定通过与否）。这些属于"交付物口径"，非"实现手段"。**唯一实质泄漏**：FR-031 点名了上游 saver 的"实例初始化能力"与具体表名 —— 这是**结构契约本身**（F002-P2 的 schema 健康检查依赖同名表），不是实现选型。 |
| CHK002 | PASS | 14 个用户故事全部从用户视角叙述（"用户敲下 init 期望…""用户手滑删掉了文件"）；Edge Cases 亦为用户可观察场景。 |
| CHK003 | PASS | 用户故事正文无代码；FR 中出现的 MUST/MUST NOT 为可验证的行为口径。 |
| CHK004 | PASS | 模板要求的 User Scenarios & Testing / Requirements / Success Criteria / Assumptions 四节齐备，另附 Phase 元信息与 Clarifications（与 F001-P1 spec 同构）。 |
| CHK005 | PASS | 全文 0 处 `[NEEDS CLARIFICATION]`。提示词已自包含，18 项歧义在 §Clarifications 内以"提问 → 决策"形式显式落定（清单顺序 / 计数口径 / 占位符写法 / 索引完整性 / stub 内容来源 / bedrock 凭据 / 占位库表数 / 版本号来源 / WAL 附属文件 / 目录清理范围 / 已损坏 sqlite3 的处理）；定向澄清轮再增 6 项裁决（该轮合计 **24 项** = 13 AI 推断 + 5 Maintainer 裁决 + 6 定向澄清修订；**现行 27 项** —— 其后经三文档交叉复核再增 3 项定点修订，澄清 #25 ~ #27）。 |
| CHK006 | PASS | FR-001 ~ FR-069 全部为「MUST + 可观察结果」句式；FR-055 逐条列出 **16 个**必备单测类别；FR-059 逐条列出 14 个必备 e2e 场景。 |
| CHK007 | PASS | SC-001 ~ SC-021 全部含量化阈值（14 断言 100% / 46 条目 / 3 表 2 索引 / 记录数 0 / 0 表 / ≤10 秒 / ≥80% 覆盖率 / 26/26 / 0 处）。 |
| CHK008 | PASS | SC 全部为用户 / 验收视角（"用户拿到的工作区…""缺失数为 0""零处被删除"），未出现框架、数据库、库名等实现依赖。唯一可争议项 SC-013 的"覆盖率 ≥ 80%"沿用宪法 §4.6 既定技术指标，且已注明度量工具由 plan 落定 —— 属项目治理既定口径，非本 spec 新增的框架依赖。 |
| CHK009 | PASS | 14 个用户故事各含 Given/When/Then 验收场景（共 **41** 条），与 e2e 黑盒 14 场景一一对应。 |
| CHK010 | PASS | Edge Cases 分 **6** 组（**前置与根目录类** / 清单与源文件类 / 渲染与幂等类 / `--force` 类 / memory 模板边界类 / 其它边界），共 **32** 条。 |
| CHK011 | PASS | Phase 元信息表锁定「本阶段使用 / 不占用」退出码；FR-066 明确 3 个推迟项；Assumptions「范围外」段列出全部排除项。 |
| CHK012 | PASS | Assumptions 列出前置 Phase 依赖、已建档资产、资产总数口径、命名口径、强制重置作用域口径、sqlite3 结构归属口径、配置检查边界口径、上游依赖、工具链、运行平台、特权环境、术语口径与范围外共 **27 条**（**现行值**；第 1 / 2 轮记录的“15 条”为当时快照）。 |
| CHK013 | PASS | 每条 FR 均可映射到 FR-059 的 14 个 e2e 场景或 FR-055 的 **16** 个单测类别或静态检查（见 §需求追溯矩阵）。 |
| CHK014 | PASS | 覆盖主流程（US1 新建）、保护流程（US6 幂等 / US7 补齐 / US8 强制 / US9 用户内容保护 / US13 数据清空告知）、边界流程（US10 整体删除 / US11 范围边界 / US12 不越权检查 / US14 结构完好）、可用性流程（US2 供应商 / US3 MCP / US4 Skill 元信息 / US5 命名一致）。 |
| CHK015 | PASS | 21 条 SC 覆盖"可创建 / 不破坏 / 能重置 / 不越界 / 结构完好 / 退出码正确 / 质量门禁"六个面。 |
| CHK016 | PASS | 复核 §FR-001 ~ FR-069 与 §Success Criteria：未出现"先实现 A 再实现 B"式步骤、未出现依赖包版本号、未给出测试代码。 |

**第 1 轮发现并已修正的问题**：

1. 追溯矩阵表头原为「验收场景」，与本 spec 顶部「验收场景 = Given/When/Then 验收场景」的术语约定冲突（e2e 黑盒场景被误标）→ 已改为「e2e 黑盒场景」，并把两处「全部场景」展开为「全部 14 个场景」。

**遗留说明（不影响放行）**：

- CHK001 / CHK008 的"附条件说明"并非未通过项 —— 本 Phase 的验收对象本身是**文件与目录产物**，产物清单（46 条 / 6 目录 / 4 manifest 字段 / 3 表 2 索引）属于交付契约的一部分，已按"交付物口径"而非"实现手段"处理。若后续 `/speckit.clarify` 认为需要进一步去技术化，应回头收敛 FR-039 ~ FR-054 的条目清单粒度（而非删减约束本身）。
- 无 [NEEDS CLARIFICATION] 残留，无需进入澄清问答流程。

**放行结论**：全部 16 项通过 → spec 可进入 `/speckit.clarify`（如需）或 `/speckit.plan`。

---

### 第 2 轮校验（2026-10-23，analyse 驱动）—— 定点修订后的复核

**触发**：`/speckit.analyse` 复核出 26 项跨文档缺陷，其中 **8 类判定为 spec 层缺陷**（需求语义自相矛盾 / 事实性错误 / 验收口径未绑定 / 约束过严），已按 Maintainer 裁决**定点修订** spec.md；plan / tasks / contracts / research / data-model / quickstart / 宪法 已同步对齐。

**逐项复核记录**：

| 项 | 结论 | 依据 / 本轮改动 |
|---|---|---|
| CHK001 | PASS（附条件说明，同上） | 本轮新增的 FR-041 补强句（"安装包 MUST 携带全部 37 个源文件，含隐藏名 `.gitignore.txt`"）属**交付物口径**（安装包完整性是契约的一部分），非实现手段。 |
| CHK002 | PASS | 14 个用户故事仍全部从用户视角叙述；本轮新增的 US6 第 4 条（工作区清单被改坏 → exit 3）亦为用户可观察场景。 |
| CHK003 | PASS | 无变化。 |
| CHK004 | PASS | 四节齐备；Clarifications 仍为 24 项决策（13 + 5 + 6）**（该轮快照；现行 27 项）**，**未新增决策**，仅修正 2 条决策中的事实性错误表述（`-wal` 危害）。 |
| CHK005 | PASS | 0 处 `[NEEDS CLARIFICATION]`；本轮**未引入新决策**（4 个待决点由 Maintainer 直接裁决并已写入正文）。 |
| CHK006 | PASS | **改善**：FR-010（原与 FR-012 自相矛盾）、FR-026（原与 FR-002 口径冲突）、FR-011 / Edge Case（原含事实性错误）已修正；SC-015 与 FR-059 现已绑定"26/26 全量、MUST NOT 抽样"。 |
| CHK007 | PASS | SC-015 补"该覆盖 MUST 逐份断言全部 26 份"→ 量化口径未放松。 |
| CHK008 | PASS | 无变化。 |
| CHK009 | PASS | 验收场景 40 → **41**（US6 补第 4 条）。 |
| CHK010 | PASS | Edge Cases **32** 条（该轮快照为 28 条；现行 32 条 —— 本轮改写 2 条、增补 1 处说明，条目数不减）。 |
| CHK011 | PASS | 无变化。 |
| CHK012 | PASS | Assumptions 15 条；本轮新增的"打包完整性"约束由 FR-041 承载，已在 §需求追溯矩阵内落到 T001 / T032 / T077。 |
| CHK013 | PASS | **改善**：FR-064 的客户端改动白名单由 2 项扩到 3 项（新增 `--help` 文案同步）→ 原先"要么留假话、要么违宪"的无解局面消除；FR-041 的安装包完整性 MUST 有了明确的验证落点。 |
| CHK014 | PASS | 14 个故事与 14 个 e2e 场景的 1:1 映射未变。 |
| CHK015 | PASS | 21 条 SC 全部仍可验证；本轮**未新增** SC（改动只是把既有 SC 的覆盖面写实）。 |
| CHK016 | PASS | 本轮修订只涉及"什么"与"可观察结果"，未引入实现步骤。 |

**放行结论**：全部 16 项通过 → spec 修订版可进入 `/speckit.plan` 复核版与 `/speckit.tasks` 重生成。

---

### 第 3 轮校验（2026-10-23，analyse 驱动）—— 定点修订后的复核

**触发**：`/speckit.analyse` 在第 2 轮修订后复跑，再复核出 **9 项 spec 层缺陷**（语义矛盾 / 验证落点缺口 / 条款越界 / 措辞与契约不符），已按 Maintainer 裁决**定点修订** spec.md（S1 ~ S9）。

**本轮性质**：**定点修订**，非重新生成 —— 以既有 **534 行** spec.md 为基底做外科式改写（**现行 spec.md 为 564 行**）；Phase 元信息表 / 14 个用户故事 / Edge Cases / Key Entities / Assumptions / §需求追溯矩阵 / 21 条 SC 全部保留，FR 与 SC 编号零增删、零重排。

**逐项复核记录**：

| 项 | 结论 | 依据 / 本轮改动 |
|---|---|---|
| CHK001 | PASS（附条件说明，同前两轮） | 本轮新增的「权威分类法」段与 ①~⑦ 标注属**失败成因的契约口径**（退出码语义的组成部分），非实现手段。 |
| CHK002 | PASS | 14 个用户故事零改动；US6 第 4 条（工作区清单被改坏 → exit 3）本轮获得**单测落点**（FR-055 第 16 类），用户可观察性不变。 |
| CHK003 | PASS | 无变化。 |
| CHK004 | PASS | 四节齐备；本轮新增 `#### 模板生成类失败的 7 类成因（权威分类法）` 子节（置于 §Functional Requirements 内，与其它 `####` 子节同级），未新增 / 删减任何顶层章节。 |
| CHK005 | PASS | 0 处 `[NEEDS CLARIFICATION]`；本轮**未引入新决策**（9 项待决点由 Maintainer 直接裁决并已写入正文）。 |
| CHK006 | PASS | **改善**：FR-038 与 FR-014 原就"权限中途撤销"存在双重语义归属 → 本轮按**阶段**切分消除矛盾；FR-014 改为引用权威分类法（原自列 7 项且与权威清单取样不同）；FR-055 类别数 15 → **16** 且补齐"清单非法 JSON → exit 3"的落点；FR-002 点名 `version` / `entries` / `path` / `format` 四个字段名；FR-012 删除重复句。 |
| CHK007 | PASS | SC 数量 21 未变；SC-008 的类别数 15 → **16**，量化口径**收紧**（未放松）。 |
| CHK008 | PASS | 无变化。 |
| CHK009 | PASS | 验收场景仍为 **41** 条（14 个故事），零增删。 |
| CHK010 | PASS | Edge Cases 分 5 组、条目数不减：S1 限定「目标路径是目录」的适用边界（文本类 / sqlite3 类）；S3 逐条标注权威编号 ①~⑥；S6 为 Windows 条目补平台范围限定。 |
| CHK011 | PASS | 无变化。 |
| CHK012 | PASS | Assumptions **27 条、零增删**（本轮零改动；此前第 1 / 2 轮记录中的"15 条"为当时快照下的计数，续轮未回填 —— 本轮据实记为 27）；S6 新增的"Windows 不在本阶段范围"与 Assumptions「运行平台」互指一致。 |
| CHK013 | PASS | **改善**：FR-018 的"清单解析失败 → exit 3"原零覆盖（仅 US6 场景 4 与 Edge Case 要求）→ 本轮由 FR-055 第 16 类 + §需求追溯矩阵「§4.2 工作区清单」行补上落点；S5 为 FR-027 步骤 ③ 补上 exit `2` 的失败映射（此前完全缺位）。 |
| CHK014 | PASS | 14 个故事与 14 个 e2e 黑盒场景的 1:1 映射未变；FR-059 的 14 个 e2e 场景**零增删**（新增落点走单元测试，因 FR-061 规定会污染已安装包的分支不进黑盒）。 |
| CHK015 | PASS | 21 条 SC 全部仍可验证；本轮**未新增** SC。 |
| CHK016 | PASS | 本轮修订只涉及"什么"与"可观察结果"（退出码语义归属 / 分类法指向 / 验证落点），未引入实现步骤、版本号或测试代码。 |

**S1 ~ S9 改动清单与依据**：

| 编号 | 严重度 | spec.md 落点（行号） | 改动摘要 | 依据 |
|---|---|---|---|---|
| **S1** | CRITICAL | Edge Cases「渲染与幂等类」首条 **L314**；FR-010 末尾补充句 **L365** | 「目标路径已存在且是目录 → exit 3」限定为**文本类 / sqlite3 类**条目；显式声明**目录类条目不在本条范围内**（已存在即按 FR-010 保留不变、MUST NOT 报错）。FR-010 末尾补适用边界句，既有正文语义未改。 | 原表述未排除 `directory` 类，若套用到 6 个目录条目上，`donkey init` 将每次在目录条目上抛 exit 3 → 功能不可用。 |
| **S2** | HIGH | FR-055 **L442**；SC-008 **L503**；Phase 元信息表 Exit Gate **L25** / 闭环复杂度 **L27**；§需求追溯矩阵「§4.2 工作区清单」行 **L469** | 单测类别 **15 → 16**，新增"工作区清单内容非法 JSON 时读取失败并抛模板生成类错误（退出码 `3`）"；单测下限 15 → **16**（三处同步）；追溯矩阵补"含 FR-018 的清单解析失败 → 退出码 3 分支"。 | FR-018 / US6 场景 4 / Edge Case「其它边界」首条要求的该行为此前**零验证覆盖**。 |
| **S3** | HIGH | 新增子节 **L400 ~ L412**；FR-014 **L369**；FR-035 **L416**；Edge Cases「清单与源文件类」**L304 ~ L310**；Key Entities「模板生成类错误」**L484**；§Clarifications 决策条目 **L62** | 新增「模板生成类失败的 7 类成因（权威分类法）」为 spec **唯一权威来源**（①~⑦ 逐字采用）；FR-014 / FR-035 改为**引用**该段、不再自行列举；Edge Cases 该分组逐条标注权威编号；Key Entities 去掉七类复述；Clarifications 既有条目的权威指向改为本 spec 段（条目数与编号不变）。 | 原 FR-014 的取样与权威清单**不相同**（缺 ⑥⑦、多"渲染失败"），且权威被判给 plan 阶段的 `contracts/exit-codes.md §4` / `data-model.md §8.1` —— spec 不得反向依赖下游产物。 |
| **S4** | MEDIUM | FR-055 类别 4 **L442** | "强制标志时清理并重建目录条目" → "强制标志时目录条目**不删除任何文件**（其内清单文件由各自的文本 / sqlite3 条目负责重建为出厂内容）"。 | FR-010 已改为"`--force` 下 MUST NOT 删除任何文件"，原措辞是 FR-010 修订前的旧语义。 |
| **S5** | CRITICAL | FR-038 **L419**；FR-027 **L388**；FR-014 **L369** | FR-038 改为按**阶段**切分（`2` = 前置校验阶段与根目录创建阶段；`3` = 渲染阶段与清单写入阶段，各含列举项）；FR-027 在步骤 ③ 后补括号说明（③ 失败 → `2`；④ / ⑤ 失败 → `3`）；FR-014 补"渲染阶段的一切失败（含权限在渲染中途被撤销）统一归退出码 `3`"。 | FR-038 与 FR-014 原就"权限中途撤销"存在**两个语义归属**；FR-027 步骤 ③ 的失败映射此前**完全缺位**。 |
| **S6** | LOW | Edge Cases「其它边界」末条 **L343** | Windows 条目补"（Windows 平台不在本阶段范围，见 Assumptions「运行平台」——此处仅登记未来的处理约定，本阶段 MUST NOT 实现、亦 MUST NOT 纳入验收。）" | §Assumptions「运行平台」明确 Windows 不在本阶段范围，Edge Case 原表述越出该范围。 |
| **S7** | LOW | FR-002 **L354** | 点名顶层字段名：`version` / `entries` / `path` / `format`（省略时按 `text` 处理）。 | 原表述"版本号字段为整数 / 条目集合字段为列表 / 路径字段 / 格式字段"未给字段名，实现侧无法唯一定位。 |
| **S8** | LOW | FR-012 **L367** | 删除重复出现的"目录条目 MUST NOT 成为文件写入的前置条件"（保留第一次），其余文字与语义未改。 | 同句连续出现两次。 |
| **S9** | INFO | Edge Cases「清单与源文件类」**L309** | "注入用的清单路径 / 模板根目录指向一个不存在的目录" 归入权威分类法 **①（清单缺失）**，并补"注入的模板根目录不存在时，其下的文本源文件随之缺失 → 归入 ②"。 | 该条的归属此前未明确，与 ①（清单缺失）重复计类；已在 S3 第 4 条内一并处理，该分组其余条目未改。 |

**澄清决策**：本轮**未新增任何澄清决策** —— §Clarifications 仍为 **24 项**（13 AI 推断 + 5 Maintainer 裁决 + 6 定向澄清修订）**（该轮快照；现行 27 项 —— 其后经三文档交叉复核再增 3 项定点修订）**；仅按 S3 第 6 条修正了其中 **1 条**既有决策条目**内部**的事实性表述（"权威分类法以 … 为准"的指向 + "FR-014 的 7 项列举保持原样不动" → "FR-014 已改为引用权威分类法"），条目**数量与编号未变化**。

**未改动确认**：FR 编号仍为 FR-001 ~ FR-069（**69 条**）；SC 编号仍为 SC-001 ~ SC-021（**21 条**）；用户故事仍为 **14 个**（US1 ~ US14，验收场景 **41** 条）；§Clarifications **27 项**（13 + 5 + 6 + 3 三文档交叉复核定点修订）；退出码集合 `{0, 1, 2, 3}`、段位 `1-10`、子段 2 = exit `3`、46 条清单 / 37 个源 / 40 个文件型条目 / 51 条模型 / 26 provider / 14 个 e2e 场景 —— 全部数字未改动。

**放行结论**：全部 16 项通过 → spec 修订版待 Maintainer 人工确认后进入 `/speckit.plan`（复核版）与 `/speckit.tasks`（重生成）。

