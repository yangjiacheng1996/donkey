# 我的提问
咨询一个问题，对于LangGraph框架，python的哪些对象可以作为节点Node？函数function还是类class。
在harness/demo/multi_tool.py中我看到了加载Skills的中间件class SkillMiddleware(AgentMiddleware)，这个中间件可以算作节点吗？
如果不算，它是怎么运行的，多处影响Agent Loop吗？

# 调研结果
直接答案：

**LangGraph 节点**：任何 callable 都行——函数、lambda、实现了 `__call__` 的类（含方法）。`graph.add_node(name, callable)` 注册的必须是 callable。

**`SkillMiddleware` 不算节点。** 我dump 了图验证（4 个版本对比）：

| 中间件配置 | 实际图节点 |
|---|---|
| 只有 `wrap_model_call`（类）| `__start__`, `__end__`, `model`, `tools` |
| 只有 `@before_model`/`@after_model`（函数）| 多出 `bm.before_model`, `am.after_model` 两个真节点 |
| 只有 `@wrap_model_call`（装饰器）| 同第一行，没有新增 |

所以是两类截然不同的挂钩方式：

**1. Node-style hooks（`before_model`/`after_model`/`before_agent`/`after_agent`）— 真节点**
被插入到图里，路由真的走它。`__start__ → bm.before_model → model → am.after_model → ...`，因此会按 `before_*` 顺序、`after_*` 反序执行。

**2. Wrap-style hooks（`wrap_model_call`/`wrap_tool_call`）— 不是节点**
嵌套在 `model`/`tools` 节点的执行内部。`model` 节点还是只有一个，但里面是洋葱式调用链：
```
middleware1.wrap_model_call() 
  → middleware2.wrap_model_call() 
  → middleware3.wrap_model_call() 
  → 真正的模型调用
```
图上看不到新节点，但每次进 `model` 节点都会穿过所有 wrap 层。

**对你 `SkillMiddleware` 的影响：**
- 它只用了 `wrap_model_call`/`awrap_model_call`，所以图结构跟最朴素的 `create_agent(model, tools=[...])` 一样——只有 `model` 和 `tools` 两个节点
- 它影响 agent loop 的方式：每次进 `model` 节点时，它从洋葱链的最外层（或中间某层）接到 `ModelRequest`，**改写 `system_message`**（追加 Available Skills 区块），然后把改写后的 request 传给下一层 handler
- 它注册的 `load_skill` 工具则走另一条路——被合入 `tools` 节点的工具列表，agent 决定调 `load_skill` 时由 `tools` 节点执行，与 `model` 节点无关

所以"多处影响 agent loop"是指：每个模型调用都过一遍（洋葱式），以及工具列表里多了一个 load_skill（被 tools 节点处理）。这两条路在图上是分开的，但都是同一个 middleware 类提供的。