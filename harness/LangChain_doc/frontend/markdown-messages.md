# Markdown messages

> Render LLM responses as rich, formatted markdown with proper streaming support

LLMs naturally produce markdown-formatted text, including headings, lists, code blocks, tables, and inline formatting. Rendering this content as plain text wastes the structure the model is providing. This pattern shows you how to parse and render markdown in real time as it streams from the agent, across all major frontend frameworks.

## How markdown rendering works

The rendering pipeline has three steps:

1. **Receive:** `useStream` accumulates the streamed text into `msg.text` on each AI message, updating reactively as new tokens arrive.
2. **Parse:** A markdown parser converts the raw text to HTML (or a React element tree). This runs on every update but is fast enough for chat-length content (< 5ms for a 5 KB message).
3. **Render:** The parsed output is rendered into the DOM. React uses virtual DOM diffing; Vue and Svelte use `v-html` / `{@html}` with sanitized HTML.

## Setting up `useStream`

The markdown pattern uses a simple chat agent with no special configuration. Wire up `useStream` with your agent URL and assistant ID.

```tsx React
import { useStream } from "@langchain/react";
import { AIMessage, HumanMessage } from "langchain";

const AGENT_URL = "http://localhost:2024";

export function Chat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "simple_agent",
  });

  return (
    <div>
      {stream.messages.map((msg) => {
        if (AIMessage.isInstance(msg)) {
          return <Markdown key={msg.id}>{msg.text}</Markdown>;
        }
        if (HumanMessage.isInstance(msg)) {
          return <p key={msg.id}>{msg.text}</p>;
        }
      })}
    </div>
  );
}
```

## See also

- [Structured output](/oss/python/langchain/structured-output)
- [Streaming](/oss/python/langchain/streaming)
- [Frontend overview](/oss/python/langchain/frontend/overview)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/markdown-messages.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>