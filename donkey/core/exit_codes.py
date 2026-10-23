"""退出码常量与段位定义（全局唯一来源）。

段位分配见宪法 §4.4：``donkey`` 全子命令的退出码段位严格不重叠（N-08）。

| 段位      | 归属              |
| --------- | ----------------- |
| ``1-10``  | ``donkey init``   |
| ``11-20`` | ``donkey load``   |
| ``21-30`` | ``donkey session``|
| ``31-100``| ``donkey run``    |

F001-P1（``cli_validation``）只使用 ``0`` / ``1`` / ``2``；F001-P2
（``template_skeleton``）启用 ``3``（模板骨架生成失败）；``4`` / ``5-10``
属后续阶段，MUST NOT 被本阶段任何代码路径触发（spec FR-037）。
"""

# --- 本阶段实际使用的退出码 ---------------------------------------------------

#: 成功。
EXIT_CODE_OK = 0
#: 路径 / 输入 / 参数用法不合法（``PathNotFoundError``）。
EXIT_CODE_PATH_NOT_FOUND = 1
#: 权限不足（``PathPermissionError``）。
EXIT_CODE_PATH_PERMISSION = 2
#: 模板骨架生成失败（``TemplateGenerationError``）—— 本阶段启用。
EXIT_CODE_TEMPLATE_GENERATION = 3

# --- 后续阶段建档（本阶段 MUST NOT 使用）-------------------------------------

#: 内置工具生成失败 —— 属 F001-P3（子段 3），本阶段不触发。
EXIT_CODE_BUILTIN_TOOL_GENERATION = 4

# --- 段位元组 -----------------------------------------------------------------

#: ``donkey init`` 独占段位。
EXIT_CODE_SEGMENT_INIT = (1, 10)
#: ``donkey load`` 独占段位。
EXIT_CODE_SEGMENT_LOAD = (11, 20)
#: ``donkey session`` 独占段位。
EXIT_CODE_SEGMENT_SESSION = (21, 30)
#: ``donkey run`` 独占段位。
EXIT_CODE_SEGMENT_RUN = (31, 100)
#: ``donkey web`` 独占段位。
EXIT_CODE_SEGMENT_WEB = (101, 170)
#: ``donkey gui`` 独占段位。
EXIT_CODE_SEGMENT_GUI = (171, 200)

__all__ = [
    "EXIT_CODE_OK",
    "EXIT_CODE_PATH_NOT_FOUND",
    "EXIT_CODE_PATH_PERMISSION",
    "EXIT_CODE_TEMPLATE_GENERATION",
    "EXIT_CODE_BUILTIN_TOOL_GENERATION",
    "EXIT_CODE_SEGMENT_INIT",
    "EXIT_CODE_SEGMENT_LOAD",
    "EXIT_CODE_SEGMENT_SESSION",
    "EXIT_CODE_SEGMENT_RUN",
    "EXIT_CODE_SEGMENT_WEB",
    "EXIT_CODE_SEGMENT_GUI",
]
