# Structured output

> Render structured agent responses with custom UI components instead of plain text

Structured output lets the agent return typed, machine-readable data instead of plain text. Instead of rendering a single string, you get a structured object you can map to any UI: cards, tables, charts, step-by-step breakdowns, or domain-specific renderers.

## What is structured output?

Instead of returning a free-form text response, the agent uses a tool call to return a structured object conforming to a predefined schema. This gives you:

- **Type-safe data**: parse the response into a known TypeScript type
- **Precise rendering control**: render each field with its own UI treatment
- **Consistent formatting**: every response follows the same structure regardless of the underlying model

The agent accomplishes this by calling a "structured output" tool whose arguments contain the response data. The tool itself doesn't execute any logic and is purely a vehicle for returning typed data.

## Use cases

- **Product comparisons**: feature tables, pros/cons lists, ratings
- **Data analysis**: summaries with metrics, breakdowns, and highlights
- **Step-by-step guides**: ordered instructions with descriptions and code snippets
- **Recipes**: ingredients, steps, timings, and nutritional info
- **Math and science**: formulas rendered with LaTeX, step-by-step derivations
- **Travel planning**: itineraries with dates, locations, and cost estimates

## Define a schema

Define a TypeScript type for the structured data the agent returns. The shape of this schema determines how you render the UI.

```ts
interface MathSolution {
  problem: string; // The original math problem
  steps: {
    explanation: string;
    latex: string; // Optional display math for this step
  }[]; // Step-by-step derivation
  finalAnswer: string; // Plain-text final answer
  finalAnswerLatex: string; // LaTeX representation of the final answer
}
```

## Extract structured output from messages

Iterate `stream.messages`, find the AI message that contains a tool call to your structured-output tool, and parse its arguments:

```ts
function extractStructured<T>(messages: BaseMessage[], toolName: string): T | null {
  for (const msg of messages) {
    if (!AIMessage.isInstance(msg)) continue;
    const tc = (msg.tool_calls ?? []).find((t) => t.name === toolName);
    if (tc) return tc.args as T;
  }
  return null;
}
```

## See also

- [Structured output](/oss/python/langchain/structured-output)
- [Tool calling](/oss/python/langchain/frontend/tool-calling)
- [Markdown messages](/oss/python/langchain/frontend/markdown-messages)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/structured-output.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>