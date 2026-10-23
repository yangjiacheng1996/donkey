# {{ workspace_name }} 的工作区

本工作区由 `donkey init` 生成 —— 目录结构与说明文档已就位，内容由你接手填写。

## 目录职责

- `instruction.md` —— 本工作区的系统提示词：角色 / 风格 / 限制三个留白小节。
- `providers/` —— 供应商配置目录：26 份供应商配置 + `default.toml`（全局默认）+ `README.md`（目录索引）。
- `tools/` —— 工具目录：内置工具由后续阶段生成，当前只有开发约定说明。
- `mcp/` —— MCP 配置目录：`mcp.json` 存放服务器定义，由用户自行填写。
- `skills/` —— Skills 目录：三层渐进披露模型说明 + 示例 Skill（`skills/example/SKILL.md`）。
- `memory/` —— 记忆库目录：三个 sqlite3 文件，详见 `memory/README.md`。

## 工作区身份

工作区根的 `manifest.json` 记录本工作区的名字、创建时间与版本 —— 它由 `donkey init` 写入，请勿手工编辑。

## 运行数据

运行数据可选择性导出 —— 模板身份不等于必须导出。
