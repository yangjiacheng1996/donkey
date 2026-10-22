# 契约：退出码与异常映射

**版本**：v1（F001-P1 冻结）
**所有者**：`donkey/core/exit_codes.py`（常量）+ `donkey/cli/cli_client.py`（映射表）
**上游**：`spec.md` FR-018、FR-026、FR-027；宪法 §4.4 段位表

---

## 1. 段位总表（宪法 §4.4，全局不重叠）

| 段位 | 归属 | 本 Phase |
|---|---|---|
| `0` | 全子命令 | 使用 |
| `1-10` | `donkey init`（F001） | **本 Phase 占子段 1 = `1-2`** |
| `11-20` | `donkey load`（F002） | 不涉及 |
| `21-30` | `donkey session`（F003） | 不涉及 |
| `31-100` | `donkey run`（F004） | 不涉及 |
| `101-170` | `donkey web`（F005） | 不涉及 |
| `171-200` | `donkey gui`（F006） | 不涉及 |
| `201+` | v2 / v3 / v4+ | 预留 |

## 2. F001 段位内的码值分配

| 码值 | Error class | 触发条件 | 修复动作 | 状态 |
|---|---|---|---|---|
| `0` | — | 成功 | — | 本 Phase 使用 |
| `1` | `PathNotFoundError` | 父目录不存在 / 非法字符 / 末段名为空（根）/ 空路径 / 目标不是目录 / 父目录是文件 / 悬空链接 / 路径过长 | 建目录 / 换路径 | 本 Phase 使用 |
| `2` | `PathPermissionError` | 写位 / 执行位 / 读位缺失 | 调整权限 | 本 Phase 使用 |
| `3` | `TemplateGenerationError` | 模板骨架生成失败 | 重装 donkey / 重试 init | P2 |
| `4` | `BuiltinToolGenerationError` | 内置工具生成失败 | 重装 donkey | P3 |
| `5-10` | — | v1.x 试运行期新发现 | — | 预留，本 Phase 不触发 |

**参数用法错误**（缺子命令 / 缺必填参数 / 未知参数）→ 归入 `1`，**不新增错误类、不占用预留码**（澄清决策 1）。

## 3. 异常 → 退出码映射表

映射表是**全局唯一来源**，定义在 `donkey/cli/cli_client.py`：

```python
_EXCEPTION_TO_EXIT_CODE: dict[type[DonkeyError], int] = {
    PathNotFoundError:    EXIT_CODE_PATH_NOT_FOUND,    # 1
    PathPermissionError:  EXIT_CODE_PATH_PERMISSION,   # 2
}
```

| 规则 | 说明 |
|---|---|
| M-01 | 基类 `WorkspaceInitError` **不**登记在表中——基类应被子类细化 |
| M-02 | 未登记的 `WorkspaceInitError` 子类 MUST 兜底到 `1`（路径类 / 输入不合法） |
| M-03 | MUST NOT 使用宽泛捕获（如 `except Exception`）吞掉未分类错误 |
| M-04 | 错误信息 MUST 写 `stderr`；成功摘要 MUST 写 `stdout` |
| M-05 | 错误信息 MUST 含可识别标识（错误类别名或关键词），供脚本判断失败类别 |

## 4. 常量定义（`donkey/core/exit_codes.py`）

- `EXIT_CODE_OK = 0`
- `EXIT_CODE_PATH_NOT_FOUND = 1`
- `EXIT_CODE_PATH_PERMISSION = 2`
- 段位常量（预留，本 Phase 不使用）：`EXIT_CODE_TEMPLATE_GENERATION = 3`（P2）、`EXIT_CODE_BUILTIN_TOOL_GENERATION = 4`（P3）、`EXIT_CODE_SEGMENT_INIT = (1, 10)` 及 F002~F006 的段位元组。

> 段位常量在本 Phase 只**建档**（作为后续 Phase 的入口条件资产），P1 的代码路径 MUST NOT 使用 `3` / `4` / `5-10`（spec FR-026）。

## 5. 不变量

1. 本 Phase 实际使用的退出码集合 **恰为 `{0, 1, 2}`**（spec SC-011）；
2. `1` 与 `2` 各自保持单一语义，参数用法错误 MUST NOT 占用 `2`；
3. 退出码 MUST NOT 与其它子命令的段位空间重叠（N-08）；
4. 核心层 MUST NOT 感知退出码——退出码只在客户端层产生（宪法 N-05）。
