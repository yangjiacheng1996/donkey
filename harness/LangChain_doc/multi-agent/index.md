# Multi-agent

Multi-agent systems coordinate specialized components to tackle complex workflows. However, not every complex task requires this approach—a single agent with the right (sometimes dynamic) tools and prompt can often achieve similar results.

<Tip>
  For built-in multi-agent support, use [Deep Agents](/oss/python/deepagents/overview): a higher-level harness built on LangChain that ships with [subagents](/oss/python/deepagents/subagents), [skills](/oss/python/deepagents/skills), planning, a virtual filesystem, and context management.
</Tip>

## Why multi-agent?

When developers say they need "multi-agent," they're usually looking for one or more of these capabilities:

- **Context management**: Provide specialized knowledge without overwhelming the model's context window.
- **Distributed development**: Allow different teams to develop and maintain capabilities independently, composing them into a larger system with clear boundaries.
- **Parallelization**: Spawn specialized workers for subtasks and execute them concurrently for faster results.

Multi-agent patterns are particularly valuable when a single agent has too many [tools](/oss/python/langchain/tools) and makes poor decisions about which to use, when tasks require specialized knowledge with extensive context (long prompts and domain-specific tools), or when you need to enforce sequential constraints that unlock capabilities only after certain conditions are met.

<Tip>
  At the center of multi-agent design is **[context engineering](/oss/python/langchain/context-engineering)**—deciding what information each agent sees.
</Tip>

## Patterns

| Pattern                                                                  | How it works                                                                                                                         |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| [**Subagents**](/oss/python/langchain/multi-agent/subagents)             | A main agent coordinates subagents as tools. All routing passes through the main agent.                                                  |
| [**Handoffs**](/oss/python/langchain/multi-agent/handoffs)               | Behavior changes dynamically based on state. Tools update a state variable to switch agents or configurations.                       |
| [**Skills**](/oss/python/langchain/multi-agent/skills)                   | Specialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context as needed.               |
| [**Router**](/oss/python/langchain/multi-agent/router)                   | A routing step classifies input and directs it to specialized agents. Results are synthesized.                                         |
| [**Custom workflow**](/oss/python/langchain/multi-agent/custom-workflow) | Build bespoke execution flows with [LangGraph](/oss/python/langgraph/overview), mixing deterministic and agentic behavior.          |

### Choosing a pattern

| Pattern                                                      | Distributed dev | Parallelization | Multi-hop | Direct user interaction |
| ------------------------------------------------------------ | :--------------: | :-------------: | :-------: | :---------------------: |
| [**Subagents**](/oss/python/langchain/multi-agent/subagents) |      ⭐⭐⭐⭐⭐       |     ⭐⭐⭐⭐⭐      |   ⭐⭐⭐⭐⭐    |           ⭐            |
| [**Handoffs**](/oss/python/langchain/multi-agent/handoffs)   |        -         |        -        |   ⭐⭐⭐⭐⭐    |         ⭐⭐⭐⭐⭐          |
| [**Skills**](/oss/python/langchain/multi-agent/skills)       |      ⭐⭐⭐⭐⭐       |      ⭐⭐⭐       |   ⭐⭐⭐⭐⭐    |         ⭐⭐⭐⭐⭐          |
| [**Router**](/oss/python/langchain/multi-agent/router)       |       ⭐⭐⭐        |     ⭐⭐⭐⭐⭐      |     -      |          ⭐⭐⭐           |

<Tip>
  You can mix patterns! Subagents can invoke tools that call custom workflows or routers. Subagents can even use skills to load context on-demand.
</Tip>

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/multi-agent/index.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>