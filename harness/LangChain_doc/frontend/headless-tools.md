# Headless tools

> Run browser and device APIs on the client with headless tool implementations

Headless tools let your agent call tools whose real execution must happen in the user's app instead of on the server. The agent still sees a normal tool schema, but the implementation lives in the frontend, where it can access browser APIs like IndexedDB, geolocation, clipboard, canvas, or file pickers.

This pattern is especially useful when data should stay local to the device. The playground example on this page uses a small browser-memory toolkit backed by IndexedDB plus a geolocation tool that runs entirely on the client.

## How headless tools work

At a high level, headless tools split the tool schema from the browser-only implementation.

1. Register a tool on the agent that immediately calls `interrupt()` to defer execution to the frontend.
2. Mirror the same tool names and argument fields in frontend definitions.
3. Implement the matching tools in the frontend with `.implement(...)` and pass them to `useStream({ tools: [...] })`.
4. When the agent invokes a matching tool, the client handles the action and resumes the interrupted run with the tool result.

## Register the tool on the agent

The playground defines a small set of client-side tools that follow the same pattern: the agent exposes a tool schema, and the frontend handles the actual execution.

Define normal tools on the server that immediately call `interrupt()`, then mirror the same tool names and argument fields in a frontend `tools.ts` file.

```python agent.py
from typing import Any

from langchain import create_agent
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from pydantic import BaseModel


class MemoryPutInput(BaseModel):
    key: str
    value: Any


class MemoryGetInput(BaseModel):
    key: str


class GeolocationGetInput(BaseModel):
    save: bool = True


def _interrupt_for_client(
    tool_name: str,
    args: dict[str, Any],
    runtime: ToolRuntime,
) -> Any:
    return interrupt({
        "type": "tool",
        "tool_call": {
            "id": runtime.tool_call_id,
            "name": tool_name,
            "args": args,
        },
    })


@tool(args_schema=MemoryPutInput)
def memory_put(key: str, value: Any, runtime: ToolRuntime) -> Any:
    """Store a key/value pair in browser memory."""
    return _interrupt_for_client("memory_put", {"key": key, "value": value}, runtime)


@tool(args_schema=MemoryGetInput)
def memory_get(key: str, runtime: ToolRuntime) -> Any:
    """Read a key/value pair from browser memory."""
    return _interrupt_for_client("memory_get", {"key": key}, runtime)


@tool(args_schema=GeolocationGetInput)
def geolocation_get(save: bool = True, runtime: ToolRuntime) -> Any:
    """Get the user's geolocation."""
    return _interrupt_for_client(
        "geolocation_get", {"save": save}, runtime
    )


agent = create_agent(
    "gpt-5.5",
    tools=[memory_put, memory_get, geolocation_get],
    checkpointer=MemorySaver(),
)
```

## Implement the same tools in the frontend

Mirror the agent tools in `tools.ts`, providing real implementations with `.implement(...)`. The SDK then matches tool calls to these implementations when the agent defers to the client.

```ts tools.ts
import { tool } from "@langchain/core/tools";
import { z } from "zod";

export const toolsClient = [
  tool(
    async (input: { key: string; value: unknown }) => {
      localStorage.setItem(input.key, JSON.stringify(input.value));
      return "saved";
    },
    {
      name: "memory_put",
      description: "Store a key/value pair in browser memory.",
      schema: z.object({ key: z.string(), value: z.unknown() }),
    }
  ),
  tool(
    async (input: { key: string }) => {
      return localStorage.getItem(input.key) ?? "not found";
    },
    {
      name: "memory_get",
      description: "Read a key/value pair from browser memory.",
      schema: z.object({ key: z.string() }),
    }
  ),
  tool(
    async (input: { save: boolean }) => {
      return new Promise<string>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          (pos) =>
            resolve(
              JSON.stringify({
                lat: pos.coords.latitude,
                lng: pos.coords.longitude,
              })
            ),
          (err) => reject(err)
        );
      });
    },
    {
      name: "geolocation_get",
      description: "Get the user's geolocation.",
      schema: z.object({ save: z.boolean().default(true) }),
    }
  ),
];
```

## See also

- [Tool calling](/oss/python/langchain/frontend/tool-calling)
- [Human-in-the-Loop](/oss/python/langchain/frontend/human-in-the-loop)
- [Streaming](/oss/python/langchain/streaming)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/headless-tools.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>