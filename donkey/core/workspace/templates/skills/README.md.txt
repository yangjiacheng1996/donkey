# skills/ —— Skills 目录说明

## 三层渐进披露模型

- **Level 1 —— 头部元信息（frontmatter）**：文件开头的 `---` 块，**恰含两个必填字段** —— `name` 与 `description`。
- **Level 2 —— 正文主体**：这个技能解决什么问题、什么时候该用它、产出是什么。
- **Level 3 —— 附属资源**：`reference/` / `scripts/` / `templates/` 等按需加载的附加文件，主文件只给出索引。

## frontmatter 契约

`name` 与 `description` 是**仅有的**两个字段 —— **不允许自定义额外字段**（多余的字段会让加载器的解析漂移）。

## 示例

见 `skills/example/SKILL.md`。
