# cl-ai-chat

A local, multi-agent chat framework built on [LangGraph](https://github.com/langchain-ai/langgraph) and [Ollama](https://ollama.com). A supervisor LLM routes each user message to the right subagent — web search, document retrieval, or general chat — and streams the response back token by token.

---

## Architecture

```
User input
    │
    ▼
┌─────────────┐
│  Supervisor │  classifies intent → search | retriever | general
└──────┬──────┘
       │
  ┌────┴────────────────────────────────┐
  ▼                  ▼                  ▼
Search agent   Retriever agent    General agent
  │  (web)        │  (document)       │  (conversation)
  ▼               ▼                   ▼
search_tool    get_tree              END
 (Serper)      get_node_summary
               get_node_content
```

### Agents

| Agent         | Trigger                                             | Tools                            |
| ------------- | --------------------------------------------------- | -------------------------------- |
| **General**   | Conversational, factual, or default questions       | —                                |
| **Search**    | Questions requiring current or external information | Google Search via Serper         |
| **Retriever** | Questions about an attached document                | Tree traversal tools (see below) |

The supervisor only routes to **Retriever** when an active document session exists (i.e. a `file_id` was provided at startup). Otherwise it falls back to **General**.

---

## Document retrieval — tree-based approach

Instead of embeddings and vector similarity search, document retrieval is done via a **hierarchical tree of nodes** stored in PostgreSQL. Each node maps to a section of the original document (heading → subheading → content) and carries a `title`, `summary`, and `content`.

The Retriever agent:

1. Calls `get_tree(file_id)` to fetch the full document structure.
2. Inspects node titles to narrow down candidates.
3. Calls `get_node_summary(node_id)` on likely candidates to confirm relevance.
4. Fetches full `get_node_content(node_id)` only for the most relevant nodes.
5. Synthesizes an answer from those nodes.

This avoids embedding costs and keeps retrieval interpretable and deterministic.

### Generating the tree from a PDF

The tree structure is produced by a separate pipeline:
**[lazzyms/pdf-markdown-embed](https://github.com/lazzyms/pdf-markdown-embed)**

That project converts a PDF → Markdown (via `docling` + OCR), splits it by Markdown headers into a nested tree, summarizes each leaf node with an LLM, and persists the result to PostgreSQL.

> **There is currently no direct integration between the two repositories.** The workflow is manual:
>
> 1. Run `pdf-markdown-embed` with `PROCESS_TYPE=vectorless` against your PDF.
> 2. Keep the note of the `file_id` you add in the .env for FILES variable (be mindful while working with multiple files)
> 3. Provide that `file_id` at startup of `cl-ai-chat` when prompted.

Both projects share the same PostgreSQL schema (`tree_nodes` table), so they only need to point at the same database.

---

## What it does

- Multi-agent routing: supervisor LLM classifies each question and delegates to the right subagent.
- Interactive CLI with colored output, a live spinner that reflects the supervisor's routing decision, and real-time token streaming.
- Maintains conversation history within a session using LangGraph's `add_messages` reducer — no history is persisted between sessions.
- Automatically compresses long conversations using an LLM-based summarization technique (triggered after 20 messages, keeping the 6 most recent verbatim).
- Optional document session: attach a pre-processed document by `file_id` to enable tree-based retrieval.

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally with a model pulled
- A [Serper](https://serper.dev) API key for web search
- PostgreSQL instance (only required for document sessions — general and search modes work without it)
- `uv` as the package manager (recommended)

---

## Quick setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
uv sync
```

3. Create a `.env` file in the project root:

```bash
SERPER_API_KEY=your_serper_key
OLLAMA_MODEL=qwen3:latest
DATABASE_URL=postgresql://user:password@localhost:5432/your_db   # only needed for document sessions
```

4. Pull your Ollama model:

```bash
ollama pull qwen3:latest
```

> To use a different model, update `OLLAMA_MODEL` in your `.env` file. All agents read the model name from `config/settings.py` via the `OLLAMA_MODEL` env var.

---

## How to run

```bash
uv run main.py
```

At startup you will be asked for a `file_id`:

- **Enter a `file_id`** — starts a document session; questions about the document will be routed to the Retriever agent.
- **Press Enter** — starts in general chat mode; only Search and General agents are active.

Type `exit`, `quit`, or `bye` to end the session.

---

## CLI spinner states

The spinner updates to reflect the supervisor's routing decision in real time:

| Spinner text               | What's happening                            |
| -------------------------- | ------------------------------------------- |
| `Thinking…`                | Supervisor is classifying the question      |
| `Searching…`               | Routed to Search agent                      |
| `Fetching document…`       | Routed to Retriever agent                   |
| `Processing…`              | Routed to General agent                     |
| `Searching for "<query>"…` | Search agent calling the web search tool    |
| `Fetching "<node_id>"…`    | Retriever agent calling a tree node tool    |
| `Processing results…`      | Search tool returned, agent synthesizing    |
| `Analysing document…`      | Retriever tool returned, agent synthesizing |

## CLI output colours

| Color           | Meaning                                      |
| --------------- | -------------------------------------------- |
| Cyan (bright)   | Your input prompt                            |
| Green           | AI response tokens                           |
| Magenta (dim)   | Model thinking / `<think>` blocks            |
| Yellow (bright) | Spinner / tool call status                   |
| Yellow (dim)    | Tool result preview                          |
| Blue (dim)      | System notices (summarization, session info) |
| Red             | Errors                                       |

---

## Project layout

```
main.py                     # Entrypoint, REPL, streaming display, summarization
cli/
  session.py                # Startup prompt — collects file_id from the user
agents/
  state.py                  # AgentState schema (messages, file_id, route)
  supervisor.py             # Supervisor LLM — classifies intent, sets route
  workflow.py               # LangGraph graph — nodes, edges, conditional routing
  subagents/
    general_agent.py        # Conversational agent (no tools)
    search_agent.py         # Web search agent
    retriever_agent.py      # Document retrieval agent (tree traversal)
prompts/
  supervisor.py             # Supervisor routing prompt
  general.py                # General agent system prompt
  search.py                 # Search agent system prompt
  review_nodes.py           # Retriever agent system prompt (includes {file_id})
tools/
  search_tool.py            # Google search via Serper
  file_traversal_tool.py    # get_tree / get_node_summary / get_node_content
config/
  settings.py               # Pydantic settings (env vars)
utils/
  database.py               # SQLAlchemy engine factory
models/
  tree.py                   # Pydantic model for tree nodes
```

---

## Usage notes

- Conversation history is session-scoped — restarting the process starts a fresh session.
- History is automatically compressed after 20 messages (keeps 6 most recent verbatim). Tune `SUMMARY_THRESHOLD` and `KEEP_RECENT` at the top of `main.py`.
- If you add external dependencies, update `pyproject.toml` and run `uv sync`.

---

## Future plans

- Direct integration with [pdf-markdown-embed](https://github.com/lazzyms/pdf-markdown-embed) — auto-process a PDF and start a chat session in one command.
- Persist conversation history across sessions.
- Settings: personalised behaviour, learning from conversations.

---

## Contributing

Feel free to open issues or send PRs with improvements, examples, or bug fixes.
