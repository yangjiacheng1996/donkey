# Add instructions to Managed Deep Agents

> Define the system prompt for a managed deep agent in instructions.md.

Instructions define always-on agent behavior. They form the core of the agent's system prompt.

<Note>
  Managed Deep Agents is in **public [beta](/langsmith/release-stages)** and available on [LangSmith Cloud](/langsmith/cloud) in the US region only.
</Note>

Put the instructions for your agent into `instructions.md` at the project root:

```text theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
my-agent/
  instructions.md
```

For the full project layout, see [Project structure](/langsmith/python/managed-deep-agents-project-structure).

## Add instructions

Create or modify `instructions.md` to define the agent's role, behavior, constraints, and guidance for using its tools:

```markdown instructions.md theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
# Assistant

You are a helpful assistant.
```

MDA inserts instructions into the agent's system prompt on every run.
The agent cannot modify these instructions at runtime.

## Deployment

When you run `mda deploy`, MDA syncs `instructions.md` to the agent's [Context Hub](/langsmith/use-the-context-hub).

You can then edit the instructions in the LangSmith UI and have those changes apply to the agent.

It is best to keep the `instructions.md` file in the repo as the source of truth for lasting changes, as later deployments sync the project copy again.

## When to use instructions

| Concept                                                    | Role                           | Loaded when                    |
| ---------------------------------------------------------- | ------------------------------ | ------------------------------ |
| **Instructions**                                           | Always-on system prompt        | Every run                      |
| **[Skills](/langsmith/python/managed-deep-agents-skills)** | Task-specific procedures       | When the agent selects them    |
| **[Memory](/langsmith/python/managed-deep-agents-memory)** | Knowledge the agent can update | When durable memory is enabled |

For more information, see [Project structure](/langsmith/python/managed-deep-agents-project-structure).

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/langsmith/managed-deep-agents-instructions.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>
