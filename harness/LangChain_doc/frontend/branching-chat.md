# Branching chat

> Edit messages and regenerate responses by forking from checkpoints

Conversations with AI agents are rarely linear. You may want to rephrase a question, regenerate a response you didn't like, or explore a different conversational path without losing the checkpoint history. Branching chat uses LangGraph checkpoints as fork points: every edit or regeneration submits a new run from the selected message's parent checkpoint.

<Note>
  This feature requires the [LangGraph Agent Server](/oss/python/langgraph/local-server). Run your agent locally with `langgraph dev` or [deploy it to LangSmith](/langsmith/deployment) to use this pattern.
</Note>

## What is branching chat?

Branching chat treats a conversation as a checkpointed timeline rather than a flat list. Each message has metadata that points to the checkpoint before that message was created. Editing a message or regenerating a response submits a new run from that checkpoint.

Key capabilities:

- **Edit any user message:** rewrite a previous prompt and re-run the agent from that point
- **Regenerate any AI response:** ask the agent to produce a different answer for the same input
- **Inspect history:** use the LangGraph client to load checkpoints when you need a branch timeline

## Set up stream metadata

Use the root stream for messages, then read per-message checkpoint metadata in the component that renders each message. The metadata includes the parent checkpoint ID to fork from.

<Info>
  The code examples use `useStream<typeof myAgent>` for type-safe stream state. See Type inference for [Python](/oss/python/langchain/frontend/overview#type-inference) or [JavaScript](/oss/javascript/langchain/frontend/overview#type-inference) backends.
</Info>

```tsx React
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function Chat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "simple_agent",
  });

  return (
    <div>
      {stream.messages.map((msg) => (
        <MessageWithForkControls key={msg.id} stream={stream} message={msg} />
      ))}
    </div>
  );
}
```

## See also

- [Generative UI overview](/oss/python/langchain/frontend/generative-ui-overview)
- [Tool calling](/oss/python/langchain/frontend/tool-calling)
- [Streaming](/oss/python/langchain/streaming)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/branching-chat.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>