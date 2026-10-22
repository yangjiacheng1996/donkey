"""donkey.core —— 引擎层 / 核心库 API。

分层约束（宪法 N-03 / N-05）：

- MUST NOT import 任何客户端层（cli / web / gui）；
- MUST NOT 依赖命令行参数解析或进程参数读取（``argparse`` / ``click`` /
  ``typer`` 与进程参数属客户端层职责）；
- MUST NOT 感知进程退出码——退出码只在客户端层产生。
"""
