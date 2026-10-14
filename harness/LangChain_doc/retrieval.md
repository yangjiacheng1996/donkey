# Retrieval

Large Language Models (LLMs) are powerful, but they have two key limitations:

* **Finite context**: they can't ingest entire corpora at once.
* **Static knowledge**: their training data is frozen at a point in time.

Retrieval addresses these problems by fetching relevant external knowledge at query time. This is the foundation of **Retrieval-Augmented Generation (RAG)**, enhancing an LLM's answers with context-specific information.

## Building a knowledge base

A **knowledge base** is a repository of documents or structured data used during retrieval.

If you need a custom knowledge base, you can use LangChain's document loaders and vector stores to build one from your own data.

<Note>
  If you already have a knowledge base (for example a SQL database, a document database, a CRM, or an internal documentation system), you do **not** need to rebuild it. You can:

  * Connect it as a **tool** for an agent in Agentic RAG.
  * Query it and supply the retrieved content as context to the LLM [(2-Step RAG)](#2-step-rag).
</Note>

For more information, see the following tutorial to build a searchable knowledge base and minimal RAG workflow:

<Card title="Tutorial: Semantic search" icon="database" href="/oss/python/langchain/knowledge-base" arrow cta="Learn more">
  Learn how to create a searchable knowledge base from your own data using LangChain's document loaders, embeddings, and vector stores.
</Card>

### From retrieval to RAG

Retrieval allows LLMs to access relevant context at runtime. But most real-world applications go one step further: they **integrate retrieval with generation** to produce grounded, context-aware answers.

This is the core idea behind **Retrieval-Augmented Generation (RAG)**. The retrieval pipeline becomes a foundation for a broader system that combines search with generation.

### Retrieval pipeline

A typical retrieval workflow looks like this:

```mermaid actions={true} theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
flowchart TB
  subgraph ingest[" "]
    direction LR
    S(["Sources<br>(Google Drive, Slack, Notion, etc.)"]) --> L[Document Loaders]
    L --> A([Documents])
  end
  A --> B[Split into chunks]
  B --> C[Turn into embeddings]
  C --> D[(Vector Store)]
  Q([User Query]) --> E[Query embedding]
  E --> D
  D --> F[Retriever]
  F --> G[LLM uses retrieved info]
  G --> H([Answer])

  classDef trigger fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
  classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:2px,color:#030710
  classDef output fill:#EBD0F0,stroke:#885270,stroke-width:2px,color:#441E33
  classDef neutral fill:#F2FAFF,stroke:#40668D,stroke-width:2px,color:#2F4B68

  class S,Q trigger
  class L,B,C,E,F,G process
  class D output
  class A,H neutral
```

Each component is modular: you can swap loaders, splitters, embeddings, or vector stores without rewriting the app's logic.

### Building blocks

<Columns cols={2}>
  <Card title="Document loaders" icon="file-import" href="/oss/python/integrations/document_loaders" arrow cta="Learn more">
    Ingest data from external sources (Google Drive, Slack, Notion, etc.), returning standardized [`Document`](https://reference.langchain.com/python/langchain-core/documents/base/Document) objects.
  </Card>

  <Card title="Text splitters" icon="scissors" href="/oss/python/integrations/splitters" arrow cta="Learn more">
    Break large docs into smaller chunks that will be retrievable individually and fit within a model's context window.
  </Card>

  <Card title="Embedding models" icon="sitemap" href="/oss/python/integrations/embeddings" arrow cta="Learn more">
    An embedding model turns text into a vector of numbers so that texts with similar meaning land close together in that vector space.
  </Card>

  <Card title="Vector stores" icon="database" href="/oss/python/integrations/vectorstores/" arrow cta="Learn more">
    Specialized databases for storing and searching embeddings.
  </Card>

  <Card title="Retrievers" icon="binoculars" href="/oss/python/integrations/retrievers/" arrow cta="Learn more">
    A retriever is an interface that returns documents given an unstructured query.
  </Card>
</Columns>

## RAG architectures

RAG can be implemented in multiple ways, depending on your system's needs.

| Architecture    | Description                                                                | Control   | Flexibility | Latency    | Example Use Case                                  |
| --------------- | -------------------------------------------------------------------------- | --------- | ----------- | ---------- | ------------------------------------------------- |
| **2-Step RAG**  | Retrieval always happens before generation. Simple and predictable         | ✅ High    | ❌ Low       | ⚡ Fast     | FAQs, documentation bots                          |
| **Agentic RAG** | An LLM-powered agent decides *when* and *how* to retrieve during reasoning | ❌ Low     | ✅ High      | ⏳ Variable | Research assistants with access to multiple tools |
| **Hybrid**      | Combines characteristics of both approaches with validation steps          | ⚖️ Medium | ⚖️ Medium   | ⏳ Variable | Domain-specific Q\&A with quality validation      |

### 2-step RAG

In **2-Step RAG**, the retrieval step is always executed before the generation step. This architecture is straightforward and predictable.

```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
graph TB
    A[User Question] --> B["Retrieve Relevant Documents"]
    B --> C["Generate Answer"]
    C --> D[Return Answer to User]

    classDef startend fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
    classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:1.5px,color:#030710

    class A,D startend
    class B,C process
```

<CardGroup cols={2}>
  <Card title="Tutorial: Semantic search" icon="database" href="/oss/python/langchain/knowledge-base" arrow cta="Learn more">
    Build a searchable knowledge base with document loaders, embeddings, and vector stores, then run a minimal retrieve-then-generate RAG workflow.
  </Card>

  <Card title="Tutorial: Evaluate a RAG application" icon="clipboard-check" href="/langsmith/evaluate-rag-tutorial" arrow cta="Learn more">
    Build a simple retrieve-then-generate RAG app and measure answer correctness, relevance, groundedness, and retrieval quality with LangSmith.
  </Card>
</CardGroup>

### Agentic RAG

**Agentic Retrieval-Augmented Generation (RAG)** combines the strengths of Retrieval-Augmented Generation with agent-based reasoning. Instead of retrieving documents before answering, an agent (powered by an LLM) reasons step-by-step and decides **when** and **how** to retrieve information during the interaction.

<Tip>
  The only thing an agent needs to enable RAG behavior is access to one or more **tools** that can fetch external knowledge, such as documentation loaders, web APIs, or database queries.
</Tip>

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
import requests
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent


@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text

system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[fetch_url],
    system_prompt=system_prompt,
)
```

<Card title="Tutorial: RAG with Deep Agents" icon="robot" href="/oss/python/deepagents/rag" arrow cta="Learn more">
  Build a documentation Q\&A agent that retrieves relevant chunks at query time, offloads them to the filesystem, and delegates analysis to subagents.
</Card>

### Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks.

Typical components include:

* **Query enhancement**: Modify the input question to improve retrieval quality.
* **Retrieval validation**: Evaluate whether retrieved documents are relevant and sufficient.
* **Answer validation**: Check the generated answer for accuracy, completeness, and alignment with source content.

The architecture often supports multiple iterations between these steps:

```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
graph TB
    A[User Question] --> B[Query Enhancement]
    B --> C[Retrieve Documents]
    C --> D{Sufficient Info?}
    D -- No --> E[Refine Query]
    E --> C
    D -- Yes --> F[Generate Answer]
    F --> G{Answer Quality OK?}
    G -- No --> H{Try Different Approach?}
    H -- Yes --> E
    H -- No --> I[Return Best Answer]
    G -- Yes --> I
    I --> J[Return to User]

    classDef startend fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
    classDef decision fill:#FDF3FF,stroke:#7E65AE,stroke-width:2px,color:#504B5F
    classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:1.5px,color:#030710

    class A,J startend
    class B,C,E,F,I process
    class D,G,H decision
```

This architecture is suitable for:

* Applications with ambiguous or underspecified queries
* Systems that require validation or quality control steps
* Workflows involving multiple sources or iterative refinement

<Card title="Tutorial: Agentic RAG with Self-Correction" icon="robot" href="/oss/python/langgraph/agentic-rag" arrow cta="Learn more">
  An example of **Hybrid RAG** that combines agentic reasoning with retrieval and self-correction.
</Card>

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/retrieval.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>