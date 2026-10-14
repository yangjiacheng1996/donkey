# Join & rejoin streams

> Disconnect from and reconnect to running agent streams

Join and rejoin lets you disconnect from a running agent stream without stopping the agent, then reconnect to it later. The agent continues executing server-side while the client is away, and you pick up the stream exactly where you left off.

<Note>
  This feature requires the [LangGraph Agent Server](/oss/python/langgraph/local-server). Run your agent locally with `langgraph dev` or [deploy it to LangSmith](/langsmith/deployment) to use this pattern.
</Note>

## Why join & rejoin?

Traditional streaming APIs tightly couple the client and server: if the client disconnects, the stream is lost. Join and rejoin breaks this coupling, enabling several important patterns:

- **Network interruptions**: mobile users moving between cell towers or Wi-Fi networks can seamlessly resume
- **Page navigation**: users navigating away from a chat page and returning later without losing progress
- **Mobile backgrounding**: apps suspended by the OS can rejoin the stream when foregrounded
- **Long-running tasks**: agents performing multi-minute operations (research, code generation, data analysis) where users don't need to keep the page open
- **Multi-device handoff**: start a conversation on your phone, rejoin on your desktop

## Core concepts

The join/rejoin pattern involves three key mechanisms:

| Method / Option                  | Purpose                                                                |
| -------------------------------- | ---------------------------------------------------------------------- |
| `threadId`                       | Bind the stream to the LangGraph thread you want to observe            |
| `onThreadId`                     | Persist newly-created thread IDs so a remount can reconnect            |
| `stream.disconnect()`            | Leave the stream client-side while the agent keeps running server-side |
| Remount with the same `threadId` | Reattach to in-flight work for that thread                             |

## Use `useStream` to join an existing thread

```tsx React
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function Chat({ threadId }: { threadId: string }) {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "agent",
    threadId,
  });

  return (
    <div>
      {stream.messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

Passing a `threadId` tells the stream to join an existing thread instead of creating a new one. Combined with `stream.disconnect()`, you can leave and come back without losing progress.

## See also

- [Streaming](/oss/python/langchain/streaming)
- [Threads](/oss/python/langgraph/persistence)
- [Generative UI overview](/oss/python/langchain/frontend/generative-ui-overview)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/join-rejoin.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>