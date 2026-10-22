"""donkey.cli —— 客户端层（argparse 命令行入口）。

分层约束（宪法 N-04 / N-08）：

- MUST NOT 直接 import ``langchain`` / ``langgraph`` / ``sqlite3``；
- 触达文件系统行为 MUST 只通过 ``donkey.core.api`` 门面；
- 退出码段位严格不重叠（``donkey init`` 占 ``1-10``）。
"""
