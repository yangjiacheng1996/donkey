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

