# Build a SQL agent

## Overview

In this tutorial, you will learn how to build an agent that can answer questions about a SQL database using LangChain [agents](/oss/python/langchain/agents).

At a high level, the agent will:

1. Fetch the available tables and schemas from the database
2. Decide which tables are relevant to the question
3. Fetch the schemas for the relevant tables
4. Generate a query based on the question and information from the schemas
5. Double-check the query for common mistakes using an LLM
6. Execute the query and return the results
7. Correct mistakes surfaced by the database engine until the query is successful
8. Formulate a response based on the results

<Warning>
  Building Q\&A systems of SQL databases requires executing model-generated SQL queries. There are inherent risks in doing this. Make sure that your database connection permissions are always scoped as narrowly as possible for your agent's needs. This will mitigate, though not eliminate, the risks of building a model-driven system.
</Warning>

### Concepts

The following tutorial covers the following concepts:

* [Tools](/oss/python/langchain/tools) for reading from SQL databases
* LangChain [agents](/oss/python/langchain/agents)
* [Human-in-the-loop](/oss/python/langchain/human-in-the-loop) processes

## Setup

<Steps>
  <Step title="Install dependencies">
    ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    pip install langchain langgraph
    ```
  </Step>

  <Step title="Set up LangSmith">
    Set up [LangSmith](https://smith.langchain.com?utm_source=docs&utm_medium=cta&utm_campaign=langsmith-signup&utm_content=oss-langchain-sql-agent) to inspect what is happening inside your chain or agent. Then set the following environment variables:

    ```shell theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    export LANGSMITH_TRACING="true"
    export LANGSMITH_API_KEY="..."
    ```
  </Step>
</Steps>

## Build your SQL agent

<Steps>
  <Step title="Select an LLM">
    Select a model that supports [tool-calling](/oss/python/integrations/providers/overview):

    <Tabs>
      <Tab title="OpenAI">
        ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        pip install -U "langchain[openai]"
        ```

        ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        import os
        from langchain.chat_models import init_chat_model

        os.environ["OPENAI_API_KEY"] = "sk-..."

        model = init_chat_model("gpt-5.5")
        ```
      </Tab>

      <Tab title="Anthropic">
        ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        pip install -U "langchain[anthropic]"
        ```

        ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        import os
        from langchain_anthropic import ChatAnthropic

        os.environ["ANTHROPIC_API_KEY"] = "sk-..."

        model = ChatAnthropic(model="claude-sonnet-4-6")
        ```
      </Tab>

      <Tab title="Google Gemini">
        ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        pip install -U "langchain[google-genai]"
        ```

        ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
        import os
        from langchain_google_genai import ChatGoogleGenerativeAI

        os.environ["GOOGLE_API_KEY"] = "..."

        model = ChatGoogleGenerativeAI(model="gemini-3.7-flash")
        ```
      </Tab>
    </Tabs>

    The output shown in the examples below used OpenAI.
  </Step>

  <Step title="Configure the database">
    You will be creating a [SQLite database](https://www.sqlitetutorial.net/sqlite-sample-database/) for this tutorial.

    ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    import pathlib
    import requests

    url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
    local_path = pathlib.Path("Chinook.db")

    if local_path.exists():
        print(f"{local_path} already exists, skipping download.")
    else:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            local_path.write_bytes(response.content)
            print(f"File downloaded and saved as {local_path}")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
    ```
  </Step>

  <Step title="Add tools for database interactions">
    <Warning>
      The following database tools are minimal wrappers for demonstration purposes only. They are not intended to be secure or used in production.
    </Warning>

    ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    import sqlite3
    from langchain.tools import tool

    @tool
    def sql_db_list_tables() -> str:
        """Input is an empty string, output is a comma-separated list of tables in the database."""
        con = sqlite3.connect("Chinook.db")
        try:
            cursor = con.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
            return ", ".join(tables)
        finally:
            con.close()

    @tool
    def sql_db_schema(table_names: str) -> str:
        """Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables."""
        con = sqlite3.connect("Chinook.db")
        try:
            cursor = con.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            valid_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")}
            results = []
            for table in table_names.split(","):
                table = table.strip()
                if table not in valid_tables:
                    results.append(f"Error: table_names {{{table!r}}} not found in database")
                    continue
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
                schema_row = cursor.fetchone()
                if schema_row:
                    results.append(schema_row[0])
            return "\n\n".join(results)
        finally:
            con.close()

    @tool
    def sql_db_query(query: str) -> str:
        """Input to this tool is a detailed and correct SQL query, output is a result from the database."""
        con = sqlite3.connect("Chinook.db")
        try:
            cursor = con.cursor()
            cursor.execute(query)
            res = cursor.fetchall()
            return str(res)
        except Exception as e:
            return f"Error: {e}"
        finally:
            con.close()

    @tool
    def sql_db_query_checker(query: str) -> str:
        """Use this tool to double check if your query is correct before executing it."""
        trigger_prompt = """{query}
    Double check the sqlite query above for common mistakes, including:
    - Using NOT IN with NULL values
    - Using UNION when UNION ALL should have been used
    - Using BETWEEN for exclusive ranges
    - Data type mismatch in predicates

    If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

    Output the final SQL query only.

    SQL Query: """.format(query=query)

        response = model.invoke(trigger_prompt)
        return response.text.strip()

    tools = [sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker]
    ```
  </Step>

  <Step title="Create the agent">
    ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    from langchain.agents import create_agent

    system_prompt = """
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run,
    then look at the results of the query and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain, always limit your
    query to at most {top_k} results.

    You can order the results by a relevant column to return the most interesting
    examples in the database. Never query for all the columns from a specific table,
    only ask for the relevant columns given the question.

    You MUST double check your query before executing it. If you get an error while
    executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
    database.

    To start you should ALWAYS look at the tables in the database to see what you
    can query. Do NOT skip this step.

    Then you should query the schema of the most relevant tables.
    """.format(
        dialect="sqlite",
        top_k=5,
    )

    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
    )
    ```
  </Step>

  <Step title="Run the agent">
    ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    question = "Which genre on average has the longest tracks?"

    stream = agent.stream_events(
        {"messages": [{"role": "user", "content": question}]},
        version="v3",
    )
    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            for token in item.text:
                print(token, end="", flush=True)
        elif kind == "tool_calls":
            print(f"\nTool call: {item.tool_name}({item.input})")
            for delta in item.output_deltas:
                print(delta, end="", flush=True)
            print(f"\nTool result: {item.output}")

    final_state = stream.output
    ```
  </Step>

  <Step title="Implement human-in-the-loop review">
    ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
    from langchain.agents import create_agent
    from langchain.agents.middleware import HumanInTheLoopMiddleware # [!code highlight]
    from langgraph.checkpoint.memory import InMemorySaver # [!code highlight]


    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
        middleware=[ # [!code highlight]
            HumanInTheLoopMiddleware( # [!code highlight]
                interrupt_on={"sql_db_query": True}, # [!code highlight]
                description_prefix="Tool execution pending approval", # [!code highlight]
            ), # [!code highlight]
        ], # [!code highlight]
        checkpointer=InMemorySaver(), # [!code highlight]
    )
    ```
  </Step>
</Steps>

## Next steps

For deeper customization, check out [this tutorial](/oss/python/langgraph/sql-agent) for implementing a SQL agent directly using LangGraph primitives.

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/sql-agent.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>