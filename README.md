# cl-ai-chat

Simple local chat framework that composes small agents, prompts and tools to run conversations with an Ollama model.

### What it does

- Provides a lightweight structure for building chat workflows using modular agents (`agents/`), prompt templates (`prompts/`) and helper tools (`tools/`).
- Intended for local experimentation with Ollama-compatible LLMs and Python-based orchestration.

### Prerequisites

- Python 3.10+
- Ollama installed and a local Ollama model available (an Ollama-compatible chat model). Make sure your chosen model is pulled/installed in Ollama.
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

3. Ensure Ollama is running and your model is available. Example (replace <model> with your model name):

```bash
# pull an Ollama model (example)
ollama pull <model>
# ensure Ollama service/daemon is running and reachable
```

Note: I have hardcoded "qwen3:latest" in `agents/agent.py`

How to run

- Run the main script directly:

```bash
uv run main.py
```

Project layout

- `main.py` — entrypoint / runner
- `agents/` — agent implementations and orchestration (`agent.py`, `workflow.py`, `state.py`)
- `prompts/` — prompt templates and prompt-related helpers
- `tools/` — small utility tools used by agents (e.g., `search_tool.py`)

Usage notes

- This project is intentionally minimal: adapt the agent implementations and prompt templates for your use-case and swap the Ollama model as required.
- If you modify or add external dependencies, update the dependency manifest (`pyproject.toml` or `requirements.txt`).

Future plans

- Add an interactive and continuous cli with streaming responses and behind the scene logs
- Add more tools and deepagents.

Contributing

- Feel free to open issues or send PRs with improvements, examples, or bug fixes.
