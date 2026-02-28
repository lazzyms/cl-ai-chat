# cl-ai-chat

Simple local chat framework that composes small agents, prompts and tools to run conversations with an Ollama model.

### What it does

- Provides a lightweight structure for building chat workflows using modular agents (`agents/`), prompt templates (`prompts/`) and helper tools (`tools/`).
- Interactive CLI with colored output, a live thinking spinner, and real-time token streaming.
- Maintains conversation history within a session using LangGraph's `add_messages` reducer — no history is persisted between sessions.
- Automatically compresses long conversations using an LLM-based summarization technique (triggered after 20 messages, keeping the 6 most recent verbatim).
- Intended for local experimentation with Ollama-compatible LLMs and Python-based orchestration.

### Prerequisites

- Python 3.10+
- Ollama installed and a local Ollama model available (an Ollama-compatible chat model). Make sure your chosen model is pulled/installed in Ollama.
- A [Serper](https://serper.dev) API key for the Google search tool (set `SERPER_API_KEY` in a `.env` file).
- I prefer `uv` as the package manager

### Quick setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
uv sync
```

3. Add your Serper API key to a `.env` file in the project root:

```bash
SERPER_API_KEY=your_key_here
```

4. Ensure Ollama is running and your model is available. Example (replace `<model>` with your model name):

```bash
# pull an Ollama model (example)
ollama pull <model>
# ensure Ollama service/daemon is running and reachable
```

Note: `qwen3:latest` is hardcoded in `agents/agent.py` — change `model=` there to use a different model.

### How to run

```bash
uv run main.py
```

Type `exit`, `quit`, or `bye` to end the session.

### CLI output colours

| Color           | Meaning                                      |
| --------------- | -------------------------------------------- |
| Cyan (bright)   | Your input prompt                            |
| Green           | AI response tokens                           |
| Magenta (dim)   | Model thinking / `<think>` blocks            |
| Yellow (bright) | Spinner while searching (shows query)        |
| Yellow (dim)    | Tool result preview                          |
| Blue (dim)      | System notices (summarization, session info) |
| Red             | Errors                                       |

### Project layout

- `main.py` — entrypoint, REPL loop, streaming display, spinner, summarization logic
- `agents/` — agent node (`agent.py`), LangGraph workflow (`workflow.py`), state schema (`state.py`)
- `prompts/` — system prompt template
- `tools/` — helper tools used by agents (`search_tool.py` — Google search via Serper)

### Usage notes

- Conversation history is session-scoped only — restarting the process starts a fresh session.
- To tune the summarization behaviour, adjust `SUMMARY_THRESHOLD` and `KEEP_RECENT` at the top of `main.py`.
- If you modify or add external dependencies, update `pyproject.toml` and run `uv sync`.

### Future plans

- Documents in context (vector store, pg-vector) - [Using this project](https://github.com/lazzyms/pdf-markdown-embed)
- Store conversation. Go back to older conversation.
- Settings: Personalized behavior, Learn from the conversations.

### Contributing

Feel free to open issues or send PRs with improvements, examples, or bug fixes.
