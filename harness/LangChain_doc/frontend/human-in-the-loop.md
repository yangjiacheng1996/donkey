# Human-in-the-Loop

> Add approval workflows with interrupt-based human review

Not every agent action should run unsupervised. When an agent is about to send an email, delete a record, execute a financial transaction, or perform any irreversible operation, you need a human to review and approve the action first. The Human-in-the-Loop (HITL) pattern lets your agent pause execution, present the pending action to the user, and resume only after explicit approval.

Because HITL is built on LangGraph interrupts and checkpoints, the pause is durable. A user can refresh the page, a reviewer can answer from a different component, and the agent still resumes from the exact point where execution stopped instead of replaying the whole run.

## How interrupts work

LangGraph agents support **interrupts**, explicit pause points where the agent yields control back to the client. When the agent hits an interrupt:

1. The agent stops executing and emits an interrupt payload
2. The `useStream` hook surfaces the interrupt via `stream.interrupt`
3. Your UI renders a review card with approve/reject/edit options
4. The user makes a decision
5. Your code calls `stream.submit()` with a resume command
6. The agent picks up where it left off

The frontend SDK keeps the interrupt alongside the rest of the thread state, so your UI can render it wherever it makes sense: inline in the transcript, in a review queue, in an admin dashboard, or in a modal that blocks the next user action until the decision is made.

## Setting up `useStream`

Connect `useStream` to your human-in-the-loop agent. When the graph hits an interrupt, the hook exposes the pending payload on `stream.interrupt`. Render an approval card while that value is set, then resume the run with `stream.submit(null, { command: { resume: response } })` after the user approves, rejects, or edits the action.

```tsx React
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function Chat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "agent",
  });

  if (stream.interrupt) {
    return <ApprovalCard interrupt={stream.interrupt} onSubmit={stream.submit} />;
  }

  return (
    <div>
      {stream.messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

## Decision types

The middleware defines four ways a human can respond to an interrupt:

| Decision | Description                                  |
| -------- | -------------------------------------------- |
| approve  | Execute as-is                                |
| edit     | Modify the tool arguments before execution  |
| reject   | Skip the tool call and surface feedback      |
| respond  | Provide the human's message as the tool result |

## See also

- [Human-in-the-loop](/oss/python/langchain/human-in-the-loop) (server-side)
- [Tool calling](/oss/python/langchain/frontend/tool-calling)
- [Middleware](/oss/python/langchain/middleware)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/human-in-the-loop.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>