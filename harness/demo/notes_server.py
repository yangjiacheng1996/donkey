"""Notes MCP server (streamable-http transport).

Pre-launch this in a separate terminal before running multi_tool.py:

    python3 harness/demo/notes_server.py --transport streamable-http --port 8765

The agent's mcp_config.json connects to it via the `url` entry. This
demonstrates the "pre-launched server" mode in the MCP config format.
"""
import argparse

from fastmcp import FastMCP

mcp = FastMCP("NotesServer")


@mcp.tool
def create_note(title: str, body: str) -> str:
    """Create a new note and return its id."""
    return f"Created note '{title}' (body length={len(body)})."


@mcp.tool
def list_notes() -> str:
    """List all notes (placeholder, in-memory only)."""
    return "Notes: (in-memory demo - nothing persisted)."


@mcp.tool
def server_info() -> str:
    """Return a self-description string identifying this server."""
    return "NotesServer (streamable-http transport)"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", default="streamable-http")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--path", default="/mcp")
    args = parser.parse_args()

    transport_kwargs = {}
    if args.transport in ("http", "streamable-http", "sse"):
        transport_kwargs = {
            "host": args.host,
            "port": args.port,
            "path": args.path,
        }

    mcp.run(transport=args.transport, **transport_kwargs)