# OpenUI

> Generate complete, interactive dashboards and reports using the OpenUI component library and openui-lang

[OpenUI](https://github.com/thesysdev/openui) is a generative UI library that lets a language model produce complete, interactive UIs in a declarative format called **openui-lang**. Instead of returning a chat message, the agent returns a component tree with cards, charts, tables, tabs, and forms that the `Renderer` turns into a real React UI.

This integration is well-suited for data-rich outputs like reports, dashboards, and data explorers, where the model is both the data analyst and the UI designer.

## How it works

1. **Generate the system prompt:** call `openuiLibrary.prompt()` once at startup; it produces a complete openui-lang reference that the model uses to write valid component trees
2. **Inject on first message:** send the system prompt as the opening system message when a new conversation starts
3. **Model writes openui-lang:** the model responds with a program like `root = Stack([header, kpis, chart])` instead of prose
4. **Render with `Renderer`:** pass the text to OpenUI's `Renderer` and the component library; it parses and renders the tree

## Installation

```bash
npm install @langchain/react @openuidev/react-ui @openuidev/react-headless @openuidev/react-lang
```

<Tip>
  OpenUI requires React 19+ and `zustand`.
</Tip>

## Import the component styles

```css
@import "@openuidev/react-ui/components.css";
@import "@openuidev/react-ui/styles/index.css";
```

## Generate the system prompt

OpenUI ships a `openuiLibrary.prompt()` function that generates the complete openui-lang reference:

```ts
import { openuiLibrary, openuiPromptOptions } from "@openuidev/react-ui/genui-lib";

const SYSTEM_PROMPT = openuiLibrary.prompt({
  ...openuiPromptOptions,
  preamble:
    "You are a report generator. When asked for a report, produce a detailed, " +
    "data-rich report using openui-lang: executive summary, KPI cards, charts, " +
    "tables, and multiple sections. Your ENTIRE response must be raw openui-lang " +
    "— no code fences, no markdown, no prose.",
});
```

## Inject the system prompt via useStream

Send the system prompt as the first message of every new thread:

```tsx
import { useCallback } from "react";
import { useStream } from "@langchain/react";

const SYSTEM_PROMPT = openuiLibrary.prompt({ ... });

export function App() {
  const stream = useStream({
    apiUrl: import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://localhost:2024",
    assistantId: "openui",
  });

  const handleSubmit = useCallback(
    (text: string) => {
      const isNewThread = stream.messages.length === 0;
      stream.submit({
        messages: [
          ...(isNewThread ? [{ type: "system", content: SYSTEM_PROMPT }] : []),
          { type: "human", content: text },
        ],
      });
    },
    [stream],
  );

  // ...
}
```

## Render with the Renderer

```tsx
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";
import { AIMessage } from "langchain";

function MessageList({ messages, isLoading }) {
  const lastAiIdx = messages.reduce(
    (acc, msg, i) => (AIMessage.isInstance(msg) ? i : acc),
    -1,
  );

  return messages.map((msg, i) => {
    if (AIMessage.isInstance(msg)) {
      const text = msg.text;
      return (
        <Renderer
          key={msg.id ?? i}
          response={text}
          library={openuiLibrary}
          isStreaming={isLoading && i === lastAiIdx}
        />
      );
    }
    // ... human message bubble
  });
}
```

## Best practices

- **Generate the system prompt at module load:** not inside a React component
- **Inject the system prompt only on fresh threads:** check `stream.messages.length === 0`
- **Use hoisting order:** write `root = Stack([...])` first
- **Gate on complete statements:** avoid re-rendering the Renderer on every token
- **Verify chart data before rendering:** chart components need their `Series` and label arrays defined
- **Keep camelCase variable names:** the openui-lang parser only accepts camelCase identifiers

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/integrations/openui.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>