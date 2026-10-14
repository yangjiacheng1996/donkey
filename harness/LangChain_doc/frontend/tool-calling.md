# Tool calling

> Display agent tool calls with rich, type-safe UI cards

Agents can invoke external tools like weather APIs, calculators, web search, database queries, and more. The results are in raw JSON. This pattern shows you how to render structured, type-safe UI cards for every tool call your agent makes, complete with loading states and error handling.

## How tool calling works

When a LangGraph agent decides it needs external data, it emits one or more **tool calls** as part of an AI message. Each tool call includes:

- **name**: the tool being invoked (e.g. `"get_weather"`, `"calculator"`)
- **args**: the structured arguments passed to the tool
- **id**: a unique identifier linking the call to its result

The agent runtime executes the tool, and the result comes back as a `ToolMessage`. The `useStream` hook unifies all of this into a single `toolCalls` array you can render directly.

## Setting up `useStream`

The first step is wiring up `useStream` to your agent backend. The hook returns reactive state including a `toolCalls` array that updates in real time as the agent streams.

```tsx React
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function Chat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "tool_calling",
  });

  return (
    <div>
      {stream.messages.map((msg) => (
        <Message key={msg.id} message={msg} toolCalls={stream.toolCalls} />
      ))}
    </div>
  );
}
```

## Tool call lifecycle

Each tool call moves through a lifecycle: pending, complete, or failed. Render each stage as a purpose-built UI:

```tsx
function ToolCard({ toolCall }) {
  if (toolCall.state === "pending") return <LoadingCard name={toolCall.name} />;
  if (toolCall.state === "complete") return <ResultCard result={toolCall.result} />;
  return <ErrorCard error={toolCall.error} />;
}
```

## See also

- [Tools](/oss/python/langchain/tools)
- [Structured output](/oss/python/langchain/structured-output)
- [Controlled generative UI](/oss/python/langchain/frontend/controlled-generative-ui)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/tool-calling.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>