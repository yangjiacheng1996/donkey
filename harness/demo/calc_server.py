"""Calc MCP server (stdio transport).

Launched by MCPAdapter via the `command` entry in mcp_config.json.
No need to start this manually - the agent spawns it as a subprocess.
"""
from fastmcp import FastMCP

mcp = FastMCP("CalcServer")


@mcp.tool
def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


@mcp.tool
def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b


@mcp.tool
def power(base: float, exponent: float) -> float:
    """Return base raised to the exponent."""
    return base ** exponent


if __name__ == "__main__":
    mcp.run()