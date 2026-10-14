# assistant-ui

> Headless React AI chat framework with a full runtime layer, bridged to useStream

[assistant-ui](https://www.assistant-ui.com/) is a headless React UI framework for AI chat. It provides a full runtime layer—thread management, message branching, attachment handling—that connects to [`useStream`](https://reference.langchain.com/javascript/langchain-react/index/useStream) via the `useExternalStoreRuntime` adapter.

## How it works

1. **Stream with [`useStream`](https://reference.langchain.com/javascript/langchain-react/index/useStream)**: connect to your agent and get reactive messages, loading state, and submit/cancel callbacks
2. **Adapt with `useExternalStoreRuntime`**: bridge `stream.messages` into assistant-ui's runtime format by converting `BaseMessage[]` to `ThreadMessageLike[]`
3. **Provide the runtime**: wrap your UI in `AssistantRuntimeProvider` and render any assistant-ui thread component

## Installation

```bash
bun add @assistant-ui/react @assistant-ui/react-markdown
```

## Wiring `useStream`

The `useExternalStoreRuntime` adapter bridges `stream.messages` into the assistant-ui runtime. Pass it to `AssistantRuntimeProvider` and render any thread component:

```tsx React
import { useCallback, useMemo } from "react";
import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type AppendMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { useStream } from "@langchain/react";
import { Thread } from "@assistant-ui/react";

export function Chat() {
  const stream = useStream({
    apiUrl: "http://localhost:2024",
    assistantId: "claude",
  });

  const onNew = useCallback(
    async (message: AppendMessage) => {
      const text = message.content
        .filter((c) => c.type === "text")
        .map((c) => c.text)
        .join("");
      await stream.submit({ messages: [{ type: "human", content: text }] });
    },
    [stream],
  );

  const messages = useMemo(
    () => toThreadMessages(stream.messages),
    [stream.messages],
  );

  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages,
    onNew,
    onCancel: () => stream.stop(),
    convertMessage: (m) => m,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
```

## Best practices

- **Memoise message conversion:** wrap `toThreadMessages(stream.messages)` in `useMemo`
- **Handle attachments:** use `CompositeAttachmentAdapter` with `SimpleImageAttachmentAdapter` for image uploads
- **Use branching:** assistant-ui has built-in message branching support via `MessageBranch`
- **Thread persistence:** persist `threadId` with `onThreadId` and pass it back into `useStream` on page load

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/integrations/assistant-ui.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>