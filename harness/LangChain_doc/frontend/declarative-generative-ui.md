# Declarative generative UI

> Compose agent-generated interfaces from a registered component catalog using json-render and A2UI

## Overview

Declarative generative UI is in the middle of the [generative UI spectrum](/oss/python/langchain/frontend/generative-ui-overview). The agent emits a structured specification, and the frontend composes the interface from a catalog of components you register ahead of time. Instead of rendering text responses in chat bubbles, the agent output **is** the UI: forms, cards, dashboards, and more. You define which components are available (the "catalog"), and the agent composes them into a valid UI tree.

The catalog is the guardrail that makes this approach safe: the agent can arrange and combine your components freely, but cannot step outside the set you approve. This balances creativity against predictability. It is where the long tail lives, trading pixel-perfection for breadth, which suits secondary interactions, internal tools, and dashboards where showing something useful matters more than exact control. This page covers declarative generative UI with [json-render](https://json-render.dev), a generative UI framework that defines component catalogs, generates specs with AI, and renders them safely across React, Vue, Svelte, and Angular. For Google's A2UI specification (integrated via CopilotKit), see [A2UI](#a2ui-an-alternative-declarative-spec) below.

## When to use this approach

Use declarative generative UI for the long tail of your product, where the agent can compose layouts you did not fully anticipate while staying inside a set of components you approve: secondary interactions, internal tools, and dashboards. When a surface is high-traffic or brand-critical and must be exact, move toward [controlled generative UI](/oss/python/langchain/frontend/controlled-generative-ui). When you want interfaces created outside your application, move toward [open-ended generative UI](/oss/python/langchain/frontend/open-ended-generative-ui).

## How it works

1. **Define a catalog**: declare what components the AI can use, with typed props
2. **Prompt the AI**: describe the UI you want in natural language
3. **AI generates a spec**: a JSON document describing the component tree
4. **Frontend renders**: the spec is validated against the catalog and rendered

The frontend never trusts raw AI output: every prop is validated against its schema before being passed to a component. If the AI generates something out of catalog, the renderer falls back to a sensible default rather than crashing the page.

## See also

- [Generative UI overview](/oss/python/langchain/frontend/generative-ui-overview)
- [Controlled generative UI](/oss/python/langchain/frontend/controlled-generative-ui)
- [Open-ended generative UI](/oss/python/langchain/frontend/open-ended-generative-ui)

***

<div className="source-links">
  <Callout icon="terminal-2">
    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  </Callout>

  <Callout icon="edit">
    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/frontend/declarative-generative-ui.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  </Callout>
</div>