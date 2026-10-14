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

