"""donkey 异常层次。

```
Exception
└── DonkeyError                     # donkey 总基类
    └── WorkspaceInitError          # F001 基类
        ├── PathNotFoundError       # exit 1：路径 / 输入不合法
        └── PathPermissionError     # exit 2：权限不足
```

每个异常类 MUST 在其说明中标注对应的退出码，便于客户端做退出码映射
（spec FR-026）。核心层 MUST NOT 返回退出码、MUST NOT 打印、MUST NOT 退出
进程（宪法 N-05 / N-03）。
"""


class DonkeyError(Exception):
    """donkey 总基类。

    退出码：不适用（总基类不直接映射到具体码值）。
    """


class WorkspaceInitError(DonkeyError):
    """``donkey init`` 的基类错误。

    退出码：不适用（基类不登记在退出码映射表中，MUST 由子类细化——
    见 ``contracts/exit-codes.md`` M-01）。
    """


class PathNotFoundError(WorkspaceInitError):
    """路径 / 输入不合法。

    退出码：``1``（``EXIT_CODE_PATH_NOT_FOUND``）。

    触发条件：父目录不存在；路径含非法字符（NUL）；解析后末段名为空
    （文件系统根 / 盘符根 / UNC 共享根）；空字符串路径；目标存在但不是
    目录；父目录是文件；悬空符号链接；路径过长。
    """


class PathPermissionError(WorkspaceInitError):
    """权限不足。

    退出码：``2``（``EXIT_CODE_PATH_PERMISSION``）。

    触发条件：目标不存在时父目录缺写位或执行位；目标已存在时缺读 / 写 /
    执行位。
    """
