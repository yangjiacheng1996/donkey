# 立项书评审
在 harness/中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。
在 harness/features/中存放了三个从其他智能体项目复制过来的feature提示词：f001_buildin_tools.md、f002_init_workspace.md、f003_load_workspace.md 。
在 harness/reports中存放了一些调研报告，报告可信度很高。
这三个feature提示词不具备权威性，仅仅是供上游的“立项书.md”参考。立项书具备绝对的权威性，不要让立项书去贴合feature提示词的设计。
现在，请你阅读框架官方文档、报告，对 `harness/features/立项书.md` 进行评审，将评审意见写入 `harness/features/立项书-评审1.md` 。


# 宪法
在 harness/中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。
在 harness/reports中存放了一些调研报告，报告可信度很高。
我打算使用Speckit来开发本项目，在启动Feature 001开发之前，需要提交宪法。
请你阅读官方文档和报告，根据`harness/features/立项书.md`内容 ，帮我写一份宪法初稿，写入 `harness/features/宪法初稿.md`。我会人工评审。


# Phase分阶段
在 harness/中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。
在 harness/reports中存放了一些调研报告，报告可信度很高。
已经通过 /speckit.constitution命令生成了宪法，`.specify/memory/constitution.md` 。
已经手动撰写了立项书，`harness/features/立项书.md` 。
我打算使用Speckit来开发本项目，现在准备开发Feature 001 ，donkey init <workspace> 。
由于每个Feature很大，涉及功能点很多，所以无法使用 /speckit.specify命令一次性完成整个Feature的开发。
所以我打算把每个Feature拆成多个Phase阶段。每个Phase一个提示词文件，文件名 featurexxx_phasexxx_<phase name>.md，比如feature001_phase001_builtin_tools.md 。
新建了 `harness/features/README.md`，这个文件用于记录众多feature文件、phase文件的开发顺序、phase划分依据、大致内容等等，相当于开发目录。
请你阅读以上官方文档、报告、立项书，撰写README.md开发目录，我会人工修改这个文件。

# Phase README生成
我看了READMD.md，你没有将“程序异常退出原因”与“退出码”进行映射，而是举例说明，让我在后续的feature提示词中再规定哪个报错对应哪个退出码。
比如如下内容：
**异常退出码（Exit Code，落在 1-3 段位内）**：- 例：`exit 1` = PATH 不合法 / 不存在父目录；`exit 2` = 权限不足；`exit 3` = 目录已存在 workspace 且未传 `--force`。具体码值到场景的最终映射在 F001-P1 spec 中敲定。

请你不要这么做。
我期望的README.md内容应该是这样的：
1. 有一个“Phase一览表”，表头是 Feature编号、Phase编号、异常类名称（class XxxError类名）、退出码、异常原因描述。
2. Phase的划定遵循奥卡姆剃刀，大概率会出现的Error分配一个退出码，那种一年遇不到几次的Error就不要给一个退出码了，退出码数量有限，应该给重要报错，不重要的就不给，把退出码留存后用。
3. 因为Speckit是TDD测试驱动开发，目前的Phase划分是“报错驱动开发”，与TDD很像。一个正常功能可以有一个或多个异常状态，用退出码反推正常软件开发流程是个好办法。
4. README这次只是初稿，我会人工审批，写错了不要紧，请你大胆设计。

# 关于donkey init场景讨论
你这个回答还是不对，比如这一句：用户误删 / 改坏模板文件时，跑 donkey init --force 恢复；

我来给你最终答案：
情况1，当没有worksapce目录，这个最简单，直接新建所有目录和文件。只要父目录拥有读写执行权限即可。
情况2, 已经存在workspace，但是命令行没有添加--force。此时幂等性，帮用户补齐缺失的模板文件。如果用户有改坏的模板文件，用户可以删除，重新init。
情况3, 用户绝望了，整个workspace改的乱七八糟的，不想改了，但是又不想把整个worksapce删除，尽可能保留最多内容（非模板文件）。此时donkey init --force，帮助用户删除全部模板文件，重新补齐。至于workspace中其他部分，比如用户自己的media/ 视频目录，不动。
情景4, 用户放弃整个workspace。用户可以手动删除这个worksapce，重新init。而不是采用--force 。 

# Phase开发进度书评审
在 harness/中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。
在 harness/reports中存放了一些调研报告，报告可信度很高。
已经通过 /speckit.constitution命令生成了宪法，`.specify/memory/constitution.md` 。
已经手动撰写了立项书，`harness/features/立项书.md` 。
已经手动撰写了Phase开发进度书，`harness/features/README.md` .
请你阅读以上官方文档、报告、立项书，对README.md进行评审，将评审意见写入`harness/features/READMD评审.md`, 我会人工阅读评审，手动修改READMD这个文件。



# Phase提示词
在 `harness/`中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。
在 `harness/reports`中存放了一些调研报告，报告可信度很高。
已经通过 /speckit.constitution命令生成了宪法，`.specify/memory/constitution.md` 。
已经手动撰写了立项书，`harness/features/立项书.md` 。
已经手动撰写了Phase开发进度书，`harness/features/README.md` .
请你阅读以上官方文档、报告、立项书，根据README.md中Phase设计，帮我更新F001_P001、F001_P002、F001_P003的相关开发提示词，提示词已经分别写入以下三个文件：

- harness/features/feature001_phase001_cli_validation.md
- harness/features/feature001_phase002_template_skeleton.md
- harness/features/feature001_phase003_builtin_tools.md

要求这三个文件的内容相互独立，不允许引用其他文件内容，文件中的内容可以直接用于/speckit.specify命令。提示词不需要考虑/speckit.plan和tasks，这两个命令是spec的延伸，不可以提前撰写。

# provider.toml参数设计
智能体provider设计原则：
1. 解析层：由于每个大模型供应商的数据格式不一样（messages、tool、usage等信息），所以在应用中的数据解析层应该为不同的供应商逐个开发数据解析class，解析必须严谨。
2. 应用层：为了方便开发者，需要从不同的供应商数据格式中提取相同数据，进行高级抽象，开发者只需要使用这些高级抽象即可，无需关心底层如何实现。
3. 网络层：在传输解析层发出的数据，并返回响应时，需要保持透传，网络层不应该修改任何数据。

关于 `harness/report/大模型toml参数设计.md` ，我提出以下修改建议：
- **简洁 vs 灵活**，有的参数是必填的，有的参数是非必要的，应该暴露最常用 8–12 个 + 扩展口。
- **跨协议统一 vs 协议特异性**，我用过很多智能体，基本上都是每个 provider 一个独立 schema，因为每家的数据格式不统一，数据在网络传输的时候只能参数透传，调用方拿到数据后为每个provider专门写一个解析类。LangChain已经实现了多种provider schema的适配和参数统一抽象。口号是“传输的时候要透传，解析的时候要严谨”。
- **安全 vs 易用** ，由于本项目要求workspace高度可移植性，不同操作系统的环境变量不一样，所以不能依赖环境变量，否则软件行为不可控。所以本项目要求：只允许 TOML 字段明文！用户自行承担workspace 变成git仓库后敏感信息泄露的后果。
- 五类常见陷阱：默认温度 0.2问题，如果供应商强制，本项目不承担责任，尽人事知天命。至于用户填错字段，这个不用担心，本项目F002 load功能静态格式检查可以检查出来。secret_key必须明文写死TOML。base_url 必须对所有 provider 都可选，Ollama也是有url的，如果小白用户在同一台电脑启动Ollama和智能体，那么允许Ollama的base_url=default这个值就行了。我不希望沿用之前`[provider.extra]`的设计，因为每个 provider 一个独立 schema，参数解析要严谨。用户如果使用了不在本项目可解析provider白名单内的大模型，本项目不会为了兼容性而放弃安全和易用，冷僻大模型的用户需等待后续项目代码更新。
- 1.3 本报告的核心主张，这个主张撤销。效仿Cherry Studio，每个provider独立一套参数，项目代码中为每个provider专门编写参数解析代码。解析代码的实现尽量采用LangChain。
- 我先给出本项目需要适配的provider名单（世界top 20 provider），其他provider暂时不需要考虑——后续如需新增，按调研 §3.0 Provider 治理原则（v2.5 起）走硬理由 + GitHub issue + 社区评审 ≥14 天流程，绝不以个人偏好入选 / 排除。

| # | 公司／机构 | 总部 | 路线 | 主力 LLM | 主力 VLM / 多模态 |
|---|---|---|---|---|---|
| 1 | OpenAI | 美国 | 闭源 | GPT 系列（含 o 系列推理模型） | GPT-4o / GPT 原生多模态、Sora（视频生成） |
| 2 | Anthropic | 美国 | 闭源 | Claude 系列（Opus / Sonnet / Fable / Mythos 等档位） | Claude 原生多模态、长文档与 GUI Agent |
| 3 | Google DeepMind | 美国 | 闭源+开放权重 | Gemini 系列（Pro / Flash）；开放权重 Gemma | Gemini 原生四模态（图文音视频）、超长上下文 |
| 4 | Meta | 美国 | 开放权重 | Llama 系列 | Llama 多模态 / Muse 系列，开源生态最成熟 |
| 5 | xAI | 美国 | 闭源 | Grok 系列 | Grok 原生多模态，绑定 X 实时数据流 |
| 6 | Mistral AI | 法国 | 开放权重 | Mistral Large / Medium / Small | Pixtral 系列（Apache 2.0，部署友好） |
| 7 | 阿里巴巴·通义千问 | 中国 | 闭源+开源 | Qwen-Max / Qwen-Plus 系列 | Qwen-VL 系列（OCR/GUI Agent 强）、通义万相 |
| 8 | DeepSeek·深度求索 | 中国 | 开源为主 | DeepSeek-V / R 系列 | DeepSeek-VL、Janus、DeepSeek-OCR |
| 9 | 字节跳动·豆包 | 中国 | 闭源 | 豆包 / Seed 系列 | 豆包 Vision、即梦（图像视频生成） |
| 10 | 月之暗面 Kimi | 中国 | 闭源+开源 | Kimi K 系列（长上下文 Agent） | Kimi-VL（截图生代码、长上下文视觉） |
| 11 | 智谱AI Zhipu/Z.ai | 中国 | 闭源+开源 | GLM 系列 | GLM-V / GLM-OCR、CogView |
| 12 | MiniMax | 中国 | 闭源 | MiniMax M 系列 | 原生多模态（语音/视频/音乐全栈）、海螺 |
| 13 | 腾讯 | 中国 | 闭源 | 混元 Hy 系列 | 混元视觉、优图 Youtu-Parsing（文档图表解析） |
| 14 | 百度 | 中国 | 闭源+开源 | 文心 ERNIE 系列 | 文心多模态/VL、PaddleOCR-VL |
| 15 | 科大讯飞 | 中国 | 闭源 | 星火 Spark 系列 | 星火多模态（语音+视觉，教育医疗垂直） |
| 16 | 小米 | 中国 | 开源 | MiMo 系列 | MiMo 全模态（OpenRouter 调用量曾居首） |
| 17 | 商汤科技 | 中国 | 企业级 | SenseNova 系列 | 文档报表解析、私有化交付 |
| 18 | 阶跃星辰 StepFun | 中国 | 闭源 | Step 系列 | Step 视觉 / 视频生成系列 |
| 19 | OpenAI Compatible | github | 开源 | 无 | 很多内部自建大模型通过Newapi/Oneapi对外暴露时所遵循的协议，中国大陆的token中转站也经常使用这个协议 |

综上所述，provider模块需要遵循设计原则（抽象、严谨、透传），LangChain已经实现了抽象，本项目需要基于LangChain LLM抽象对象和init_chat_model函数，为每个provider设计专业的配置文件。
请你修改 `harness/report/大模型toml参数设计.md` 。

# provider设计评审
在 `harness/`中存放了LangChain、LangGraph、Managed deep agents三个框架的官方文档。在 `harness/reports`中存放了一些调研报告，报告可信度很高。
请你阅读以上文档，配合web fetch工具，对 harness/report/大模型toml参数设计.md 进行评审。
将评审意见写入  harness/report/大模型toml参数评审.md


