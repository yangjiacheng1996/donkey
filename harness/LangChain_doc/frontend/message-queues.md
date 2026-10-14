# Message queues

> Queue multiple messages and manage them while the agent processes sequentially

Message queuing lets users send multiple messages in rapid succession without waiting for the agent to finish processing the current one. Each message is accepted immediately, queued for the active thread, and processed sequentially, giving you full visibility and control over the pending work.

<Note>
  This feature requires the [LangGraph Agent Server](/oss/python/langgraph/local-server). Run your agent locally with `langgraph dev` or [deploy it to LangSmith](/langsmith/deployment) to use this pattern.
</Note>

## Why message queues?

In a typical chat interface, users must wait for the agent to finish responding before sending another message. This creates friction in several scenarios:

- **Batch questions**: a user wants to ask five related questions at once rather than waiting for each answer
- **Follow-up chains**: submitting clarifications or additional context while the agent is still working
- **Automated testing sequences**: programmatically sending a series of prompts to validate agent behavior
- **Data entry workflows**: feeding structured inputs one after another for processing

Message queuing solves this by accepting all submissions immediately and processing them in order.

This is an agent UX primitive rather than a cosmetic chat feature. The SDK keeps track of the queue as part of the stream controller, so your UI can show pending work, cancel stale requests, and keep the composer active while the current run continues.

## How it works

Pass `multitaskStrategy: "enqueue"` when you want a submission to wait behind the currently running request. While the agent is processing, queued submissions are added to the active thread's queue. Once the current run completes, the next queued message is dispatched automatically.

```tsx React
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function Chat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "agent",
    multitaskStrategy: "enqueue",
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

## See also

- [Join & rejoin streams](/oss/python/langchain/frontend/join-rejoin)
- [Streaming](/oss/python/langchain/streaming)
- [Frontend overview](/oss/python/langchain/frontend/overview)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/message-queues.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>