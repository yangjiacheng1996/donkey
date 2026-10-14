# Time travel

> Inspect, navigate, and resume from any checkpoint in the conversation history

Every state change in a LangGraph agent creates a **checkpoint**, a complete snapshot of the agent's state at that moment. Time travel lets you inspect any checkpoint, view the exact state the agent held, and **resume execution from that point** to explore alternative paths. It's a debugger, an undo button, and an audit log all in one.

<Note>
  This feature requires the [LangGraph Agent Server](/oss/python/langgraph/local-server). Run your agent locally with `langgraph dev` or [deploy it to LangSmith](/langsmith/deployment) to use this pattern.
</Note>

## How checkpoints work

LangGraph persists agent state after every node execution. Each persisted state is a `ThreadState` object that captures:

- **checkpoint**: metadata identifying this specific snapshot (ID, timestamp)
- **values**: the full agent state at this point (messages, custom keys)
- **tasks**: the graph nodes that were scheduled to run next
- **next**: the names of upcoming nodes in the execution plan

This creates a linear timeline of every decision the agent made, every tool it called, and every response it produced. Your UI can render this timeline and let users jump to any point.

## Setting up `useStream`

Create the stream for your agent, then fetch checkpoint history explicitly from the LangGraph client for the active thread. Resuming from a checkpoint uses `forkFrom: { checkpointId }`.

```tsx React
import { useStream } from "@langchain/react";
import { useEffect, useState } from "react";

const AGENT_URL = "http://localhost:2024";

export function TimeTravelChat() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [history, setHistory] = useState<ThreadState[]>([]);
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "agent",
    threadId,
    onThreadId: setThreadId,
  });

  // Load checkpoint history when threadId changes
  useEffect(() => {
    if (!threadId) return;
    fetch(`${AGENT_URL}/threads/${threadId}/state/history`)
      .then((res) => res.json())
      .then((data) => setHistory(data));
  }, [threadId]);

  // ...
}
```

## Use cases

- **Debugging**: replay a conversation from any point to inspect state
- **A/B testing prompts**: fork at a checkpoint and try a different tool sequence
- **User undo**: let users roll back to a prior state and continue
- **Auditing**: review the agent's decision path for compliance

## See also

- [Branching chat](/oss/python/langchain/frontend/branching-chat)
- [Persistence](/oss/python/langgraph/persistence)
- [Streaming](/oss/python/langchain/streaming)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/time-travel.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>