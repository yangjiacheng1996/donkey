# Managed Deep Agents quickstart

> Create and deploy your first Managed Deep Agent with the mda CLI.

Create and deploy your first Managed Deep Agent: scaffold a project, configure the model and instructions, add search, test in [LangSmith Studio](/langsmith/studio), and deploy with the [`mda` CLI](/langsmith/python/managed-deep-agents-cli). Managed Deep Agents supplies the [Deep Agents harness](/oss/python/deepagents/overview) and hosted runtime.

After this quickstart, the [tutorial](/langsmith/python/managed-deep-agents-tutorial) adds durable memory and a daily schedule on the same project.

<Note>
  Managed Deep Agents is in **public [beta](/langsmith/release-stages)** and available on [LangSmith Cloud](/langsmith/cloud) in the US region only.
</Note>

## Prerequisites

To follow along, you need:

* Python and `uv`.

* An API key for your model provider of choice.

## Add the `managed-deep-agents` skill

The [`managed-deep-agents` skill](https://github.com/langchain-ai/langchain-skills/blob/main/config/skills/managed-deep-agents/SKILL.md) walks a coding agent through building, testing, and deploying a Managed Deep Agent with the `mda` CLI. To add it to the current project, run:

```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
npx skills add langchain-ai/langchain-skills --skill managed-deep-agents --yes
```

Or paste this prompt into your coding agent:

<Prompt description="Build a Managed Deep Agent with the quickstart" icon="sparkles" actions={["copy"]}>
  Create and deploy a Managed Deep Agent in this working directory by following the Managed Deep Agents quickstart.

  ## Step 1: Read the guide

  Fetch and follow [https://docs.langchain.com/langsmith/managed-deep-agents-quickstart.md](https://docs.langchain.com/langsmith/managed-deep-agents-quickstart.md) as the source of truth for CLI commands, project layout, and deployment steps. Prefer the Python or TypeScript path that matches this project.

  ## Step 2: Install the skill

  If the `managed-deep-agents` skill is not already available, install it:

  ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  npx skills add langchain-ai/langchain-skills --skill managed-deep-agents --yes
  ```

  Use that skill for the rest of the workflow when it is available.

  ## Step 3: Prerequisites and secrets

  Confirm the user has LangSmith access and any required model or search credentials. If a required API key is missing, ask them to set it in the shell or a `.env` file, then wait. Do not invent, hardcode, or commit secrets.

  ## Step 4: Scaffold, configure, test, and deploy

  Follow the quickstart steps in order: initialize the project with `mda`, configure the model and instructions, add search as shown on the page, test in LangSmith Studio, and deploy with the `mda` CLI. Stop and ask when a dashboard action or credential can only be completed by the user in the LangSmith UI.

  ## Rules

  * Stay scoped to the quickstart. Do not add unrelated products or rewrite the generated project layout unless the guide requires it.
  * Prefer the `mda` CLI and the `managed-deep-agents` skill over inventing a custom deployment path.
  * Ask rather than guess when a secret, plan-tier limit, or UI-only step is unclear.
</Prompt>

## Create and deploy an agent

<Steps>
  <Step title="Set up the project" id="set-up-the-project">
    Create a project and open its directory:

    ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    uvx --from managed-deepagents mda init research-assistant
    cd research-assistant
    ```

    You now have all the scaffolding for your agent.
  </Step>

  <Step title="Add your keys" id="add-keys">
    Add your model provider API key to `.env`:

    ```text .env theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    OPENAI_API_KEY=<OPENAI_API_KEY>
    # ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY>
    # GOOGLE_API_KEY=<GOOGLE_API_KEY>
    ```

    This quickstart uses OpenAI by default. If you choose Google or Anthropic in the next step, set that provider's API key instead. `mda deploy` adds the provider key to the deployment. You can also use any [other chat provider](/oss/python/integrations/chat/).

    <Warning>
      Do not commit the `.env` file into version control. It contains secrets.
    </Warning>
  </Step>

  <Step title="Set up LangSmith" id="set-up-langsmith">
    Managed Deep Agents runs on LangSmith. Your LangSmith API key authenticates local development with `mda dev`, deploys the agent with `mda deploy`, and opens the agent in [LangSmith Studio](/langsmith/studio) so you can chat with it and inspect traces.

    [Sign up for LangSmith](https://smith.langchain.com?utm_source=docs&utm_medium=cta&utm_campaign=langsmith-signup&utm_content=langsmith-managed-deep-agents-quickstart) if you do not already have an account.

    To create a LangSmith API key, open [Settings](https://smith.langchain.com/settings), go to **API Keys**, and click **Create API Key**. For more details, see [Create an account and API key](/langsmith/create-account-api-key).

    Add your LangSmith API key to `.env`:

    ```text .env theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    LANGSMITH_API_KEY=<LANGSMITH_API_KEY>
    ```
  </Step>

  <Step title="Edit the instructions" id="edit-the-instructions">
    Open `instructions.md` and describe how the agent should behave:

    ```markdown instructions.md theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    # Research assistant

    You are a careful research assistant. Use internet search to find sources,
    keep notes, and return concise answers with citations.
    ```

    When you deploy, Managed Deep Agents syncs these instructions to [LangSmith Context Hub](/langsmith/use-the-context-hub), where you can update them without redeploying the agent.
  </Step>

  <Step title="Configure your model and search" id="configure-model-and-search">
    Now set the model and a built-in web search tool. Google, OpenAI, and Anthropic offer server-side search with no extra package or API key. Pass the provider tool dict that matches your model:

    Open `agent.py`:

    <CodeGroup>
      ```python OpenAI theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      from managed_deepagents import define_deep_agent

      # OpenAI's built-in web search — no extra install or API key needed
      agent = define_deep_agent(
          name="research-assistant",
          model="openai:gpt-5.5",
          tools=[{"type": "web_search"}],
      )
      ```

      ```python Google theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      from managed_deepagents import define_deep_agent

      # Google's built-in search — no extra install or API key needed
      agent = define_deep_agent(
          name="research-assistant",
          model="google_genai:gemini-3.6-flash",
          tools=[{"google_search": {}}],
      )
      ```

      ```python Anthropic theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      from managed_deepagents import define_deep_agent

      # Anthropic's built-in web search — no extra install or API key needed
      agent = define_deep_agent(
          name="research-assistant",
          model="anthropic:claude-sonnet-4-6",
          tools=[{"type": "web_search_20260209", "name": "web_search"}],
      )
      ```
    </CodeGroup>

    The agent name is also the default deployment name. For model concepts and provider options, see [Models](/oss/python/langchain/models).

    <Accordion title="Using another provider?">
      You can use a Tavily search tool instead.
      Add a [Tavily API key](https://app.tavily.com) to `.env`:

      ```text .env theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      TAVILY_API_KEY=<TAVILY_API_KEY>
      ```

      Install the Tavily client:

      ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      uv add tavily-python
      ```

      Create a custom `internet_search` tool:

      ```python tools/search.py theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      import os
      from typing import Literal

      from langchain.tools import tool
      from tavily import TavilyClient


      tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


      @tool
      def internet_search(
          query: str,
          max_results: int = 5,
          topic: Literal["general", "news", "finance"] = "general",
      ) -> dict:
          """Search the internet for relevant sources."""
          return tavily_client.search(
              query,
              max_results=max_results,
              topic=topic,
          )
      ```

      Import the tool and add it to the agent:

      ```python agent.py theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
      from managed_deepagents import define_deep_agent

      from tools.search import internet_search

      agent = define_deep_agent(
          name="research-assistant",
          model="openai:gpt-5.5",
          tools=[internet_search],
      )
      ```

      For more authored tools, see [Custom tools](/langsmith/python/managed-deep-agents-tools).
    </Accordion>
  </Step>

  <Step title="Run locally" id="run-locally">
    Install the project dependencies and start the agent:

    ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    uv sync
    uv run mda dev
    ```

    `mda dev` loads the API keys from `.env`, starts a local Agent Server, and opens the agent in LangSmith Studio.

    In Studio, send:

    ```txt wrap theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    What were the main announcements from the latest LangChain release?
    ```

    You should see the agent call the web search tool, then return a concise answer that cites sources. If search never appears in the trace, confirm the provider tool dict matches the model you set in `agent.py` or `agent.ts`.

    For more information, see [Develop locally with LangSmith Studio](/langsmith/python/managed-deep-agents-local-development).
  </Step>

  <Step title="Deploy the agent" id="deploy-the-agent">
    Deploy the project by running:

    ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    uv run mda deploy
    ```

    Managed Deep Agents packages the project and runs it as a hosted deployment on [LangSmith Agent Server](/langsmith/agent-server). When deployment finishes, the CLI prints the deployment dashboard URL.

    Open that URL. You should see the deployment in a ready state. Send the same research question from the previous step and confirm the hosted agent returns an answer with a search tool call. For deployment options and secrets handling, see [Deploy a Managed Deep Agent](/langsmith/python/managed-deep-agents-deploy). To inspect the agent's execution after it runs, use [LangSmith observability](/langsmith/observability-quickstart).
  </Step>
</Steps>

## Next steps

<CardGroup cols={2}>
  <Card title="Tutorial" icon="book" href="/langsmith/python/managed-deep-agents-tutorial">
    Add a custom Tavily search tool, durable memory, and a daily schedule.
  </Card>

  <Card title="Custom tools" icon="tool" href="/langsmith/python/managed-deep-agents-tools">
    Add authored LangChain tools from your project.
  </Card>

  <Card title="Connections" icon="key" href="/langsmith/python/managed-deep-agents-connections">
    Authenticate with external services, as the agent or as the caller.
  </Card>
</CardGroup>

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VScode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/langsmith/managed-deep-agents-quickstart.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>
