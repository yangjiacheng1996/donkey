"""Multi-tool agent.

Builds on harness/demo/create_an_agent.py and adds two capabilities:

1. Progressive disclosure of Agent Skills. LangChain has no built-in
   middleware for this (see
   harness/report/LangChain内置中间件速查表.md), so we ship our own
   `SkillMiddleware` that scans `skills/` for SKILL.md files and:
     - injects each skill's `name` + `description` (from YAML frontmatter)
       into the system prompt, so the model knows when a skill is relevant;
     - registers a `load_skill` tool that returns the markdown body on demand.

   The on-disk format follows the Agent Skills standard
   (https://agentskills.io/), with `skills/<skill-name>/SKILL.md`. Add or
   remove skill folders to change what the agent knows about — no code
   changes needed. The pattern is adapted from
   harness/LangChain_doc/multi-agent/skills-sql-assistant.md.

2. MCP server tools, loaded via `MCPAdapter` from a single JSON config
   (`mcp_config.json`) that supports BOTH transport modes in one file:

     Mode A - command-driven stdio: `command` + `args` (+ optional `cwd`,
              `env`). The MCP client spawns the server as a subprocess.
     Mode B - pre-launched server reachable by URL: `url` + `transport`
              (`stdio` / `http` / `sse` / `streamable-http`). You start
              it yourself, then point `url` at it.

   The script just loads the JSON config; it does NOT pre-launch servers.

To install:
    pip install -qU langchain "langchain[openai] mcp[cli] fastmcp" pyyaml

To run:
    python3 harness/demo/multi_tool.py

To also exercise Mode B:
    # in another terminal
    python3 harness/demo/notes_server.py --transport streamable-http --port 8765
"""
import asyncio
import json
import re
import socket
from collections.abc import Callable
from pathlib import Path
from pprint import pprint
from typing import TypedDict
from urllib.parse import urlparse

import yaml
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from langchain.mcp import MCPAdapter
from langchain.messages import SystemMessage
from langchain.tools import tool


MODEL_NAME = "MiniMax-M3"
BASE_URL = "https://api.minimaxi.com/v1"
API_KEY = "sk-cp-hahaha"

model = init_chat_model(
    model=MODEL_NAME,
    model_provider="openai",
    base_url=BASE_URL,
    api_key=API_KEY,
)


# ---------------------------------------------------------------------------
# 1. Skills (progressive disclosure, loaded from disk)
# ---------------------------------------------------------------------------
class Skill(TypedDict):
    name: str
    description: str
    content: str


SKILLS_DIR = Path(__file__).parent / "skills"

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


def parse_skill_md(path: Path) -> Skill:
    """Parse a SKILL.md with `name`, `description` in YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(
            f"{path}: missing YAML frontmatter (expected `---\\n...\\n---\\n<body>`)"
        )
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    name = meta.get("name") or path.parent.name
    description = meta.get("description", "").strip()
    if not description:
        raise ValueError(f"{path}: frontmatter must include `description`")
    return {"name": name, "description": description, "content": body}


def load_all_skills(skills_dir: Path = SKILLS_DIR) -> list[Skill]:
    """Discover and parse every SKILL.md under skills_dir."""
    if not skills_dir.exists():
        print(f"[multi_tool] no skills directory at {skills_dir} - skipping")
        return []
    skills: list[Skill] = []
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        try:
            skills.append(parse_skill_md(skill_md))
        except ValueError as e:
            print(f"[multi_tool] WARNING: {e}")
    return skills


SKILLS: list[Skill] = load_all_skills()
print(f"[multi_tool] loaded {len(SKILLS)} skill(s): " + ", ".join(s["name"] for s in SKILLS))


@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into context.

    Skills are loaded from the `skills/` directory at startup; their
    names and descriptions appear in the system prompt.
    """
    for s in SKILLS:
        if s["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{s['content']}"
    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available: {available}"


class SkillMiddleware(AgentMiddleware):
    """Inject skill descriptions into the system prompt.

    Pattern source: `harness/LangChain_doc/multi-agent/skills-sql-assistant.md`.
    `wrap_model_call` appends a lightweight "Available Skills" section to the
    system message on every model call; `load_skill` is registered via the
    class-level `tools` attribute so the agent can fetch the full content
    on demand.
    """

    tools = [load_skill]

    def __init__(self, skills: list[Skill] | None = None) -> None:
        skills = skills if skills is not None else SKILLS
        if not skills:
            self._addendum = ""
            return
        descriptions = "\n".join(
            f"- **{s['name']}**: {s['description']}" for s in skills
        )
        self._addendum = (
            "\n\n## Available Skills\n\n"
            f"{descriptions}\n\n"
            "Use the load_skill tool to fetch the full content of a skill "
            "when a request matches its description."
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return self._call(request, handler)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return await self._acall(request, handler)

    def _call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        new_system_message = self._build_system_message(request)
        return handler(request.override(system_message=new_system_message))

    async def _acall(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        new_system_message = self._build_system_message(request)
        return await handler(request.override(system_message=new_system_message))

    def _build_system_message(self, request: ModelRequest) -> SystemMessage:
        if not self._addendum:
            return request.system_message
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": self._addendum}
        ]
        return SystemMessage(content=new_content)


# ---------------------------------------------------------------------------
# 2. A trivial local tool (kept from create_an_agent.py for parity)
# ---------------------------------------------------------------------------
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# ---------------------------------------------------------------------------
# 3. MCP config loading + graceful skip of unreachable URL-mode servers
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "mcp_config.json"


def load_mcp_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_url_reachable(url: str, timeout: float = 0.5) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def filter_unreachable_servers(config: dict) -> dict:
    """Drop URL-mode servers whose host:port isn't accepting connections.

    Command-mode entries are kept untouched: they're started on demand by
    MCPAdapter and need no pre-launching. URL-mode servers that aren't
    reachable are skipped with a warning so the demo still runs.
    """
    servers = config.get("mcpServers", {})
    keep: dict[str, dict] = {}
    for name, srv in servers.items():
        if "url" in srv and not _is_url_reachable(srv["url"]):
            print(
                f"[multi_tool] skipping unreachable MCP server '{name}' "
                f"at {srv['url']} (pre-launch notes_server.py to enable)."
            )
            continue
        keep[name] = srv
    return {"mcpServers": keep}


# ---------------------------------------------------------------------------
# 4. Build and invoke
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = "You are a helpful assistant."


async def build_agent():
    config = filter_unreachable_servers(load_mcp_config())
    if not config["mcpServers"]:
        raise RuntimeError("No MCP servers available - check mcp_config.json")

    async with MCPAdapter(config) as adapter:
        mcp_tools = await adapter.list_tools()
        print(f"[multi_tool] discovered {len(mcp_tools)} MCP tool(s):")
        for t in mcp_tools:
            print(f"  - {t.name}")

        tools = [get_weather] + mcp_tools
        return create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[SkillMiddleware()],
        )


async def main() -> None:
    agent = await build_agent()
    question = "你可以调用哪些工具?"
    print(f"\n[multi_tool] Q: {question}\n")
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    pprint(result)


if __name__ == "__main__":
    asyncio.run(main())