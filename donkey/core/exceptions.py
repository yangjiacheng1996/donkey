"""donkey 异常层次。

```
Exception
└── DonkeyError                     # donkey 总基类
    └── WorkspaceInitError          # F001 基类
        ├── PathNotFoundError       # exit 1：路径 / 输入不合法
        ├── PathPermissionError     # exit 2：权限不足
        └── TemplateGenerationError # exit 3：模板骨架生成失败
```

每个异常类 MUST 在其说明中标注对应的退出码，便于客户端做退出码映射
（spec FR-026）。核心层 MUST NOT 返回退出码、MUST NOT 打印、MUST NOT 退出
进程（宪法 N-05 / N-03）。
"""

#: 模板类失败统一的"下一步"提示（spec FR-069 / SC-020）。
#:
#: 与 P1 的路径类 ``_NEXT_STEP``（位于 ``donkey/core/workspace/init.py``）
#: **并列而非替换** —— 二者语义不同：路径类提示"建目录 / 换路径"，模板类提示
#: "重装 donkey / 检查权限 / 重试 init"（research.md R-12）。
#:
#: MUST 落在本模块而非 ``init.py`` —— ``init.py`` 需要 import ``manifest.py``，
#: 而 ``manifest.py`` / ``sqlite3_templates.py`` 同样需要该文案；若常量落在
#: ``init.py`` 会形成 ``manifest.py → init.py → manifest.py`` 的循环 import。
_NEXT_STEP_TEMPLATE = (
    "下一步：请重装 donkey（模板清单或模板源缺失），或检查目标目录的写权限后重试 init。"
)


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


class TemplateGenerationError(WorkspaceInitError):
    """模板骨架生成失败。

    退出码：``3``（``EXIT_CODE_TEMPLATE_GENERATION``）。

    失败成因的**权威分类法**见 spec『模板生成类失败的 7 类成因（权威分类法）』
    段（七类合并为一个码值 —— 七者对用户的修复动作相同：重装 donkey / 检查
    权限 / 重试 init）；其镜像见
    [contracts/exit-codes.md](../../specs/001-donkey-init-workspace/phase-2-template-skeleton/contracts/exit-codes.md)
    §4 的 7 行表。本类 MUST NOT 自行复述该清单（spec FR-035）—— 避免出现第
    5 份副本而漂移。

    用户修复动作：重装 donkey（模板清单或模板源缺失）/ 检查目标目录写权限 /
    修复后重试 ``init``。错误信息 MUST 同时含可识别的失败标识与一条可执行
    的下一步（spec FR-069 / SC-020）—— 固定文案见 ``_NEXT_STEP_TEMPLATE``。
    """
