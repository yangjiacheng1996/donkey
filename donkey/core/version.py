"""donkey 核心层版本取值解析。

本模块是 donkey 版本取值的**唯一运行期来源**（spec FR-019）—— 版本取值的
解析 MUST 落在核心层（``donkey/core/`` 下），MUST NOT 落在客户端层
（``donkey/cli/``），否则将来建图（F004-P7）时被迫改客户端（spec FR-020）。

**取值来源与优先级**（contracts/version-contract.md §2）：

1. **安装分发元数据** —— ``importlib.metadata.version("donkey")``（spec FR-016）；
   MUST NOT 读取 ``pyproject.toml``（构建期文件，运行期不可靠）；
2. **包自身常量** —— ``donkey.__version__``，仅在 ① 不可得时回退（spec FR-017）。

**展示形态**：``version_string()`` 返回 ``"v" + resolve_version()`` —— ``v`` 是
**显示前缀**（宪法 §4.5 的 ``vx.y.z`` 记法），**不是版本号的一部分**
（spec FR-013）；前缀逻辑 MUST **单点收敛**在本模块，三端将来复用同一函数
（research.md R-02）。

**一致性契约**：底层取值与 ``pyproject.toml`` 的 ``version``、包内
``__version__``、工作区清单 ``donkey_version`` 字段**逐字节一致** —— 该口径
限定在**常规安装形态**下（安装元数据值 == 工作树声明值）；陈旧安装形态下以
**分发元数据**为准（spec FR-018）。

分层约束（宪法 N-04 / N-05）：本模块 MUST NOT import ``langchain`` /
``langgraph`` / ``sqlite3`` / ``argparse`` / ``click`` / ``typer``，MUST NOT
读取任何环境变量，MUST NOT 打印 / 返回退出码 / 退出进程。
"""

import importlib.metadata

__all__ = ["resolve_version", "version_string"]


def resolve_version() -> str:
    """解析版本底层取值（三段式 ``x.y.z`` 记法的本体，不含显示前缀）。

    优先取安装分发元数据（spec FR-016）；元数据不可得时回退包自身的
    ``__version__`` 常量（spec FR-017）—— MUST NOT 抛异常 / 输出空值；两者
    不一致时**以元数据为准**（spec FR-018）—— 不比较、不告警（告警会污染
    stdout / stderr，违反 spec FR-007 / FR-009）。

    只捕获 ``importlib.metadata.PackageNotFoundError`` —— MUST NOT 用宽泛的
    ``except Exception`` 吞掉未分类错误（F001-P1 契约 M-03 口径）。
    """
    try:
        return importlib.metadata.version("donkey")
    except importlib.metadata.PackageNotFoundError:
        # 局部导入：``donkey/__init__.py`` 零 import，故无循环导入
        # （research.md R-04）；取值在调用时解析，回退源始终是包内常量。
        from donkey import __version__

        return __version__


def version_string() -> str:
    """返回版本展示值 = ``"v" + 底层取值``（宪法 §4.5 的 ``vx.y.z`` 记法）。

    ``v`` 是**显示前缀**，不是版本号的一部分（spec FR-013）；前缀逻辑 MUST
    单点收敛在本函数（research.md R-02）。
    """
    return "v" + resolve_version()
