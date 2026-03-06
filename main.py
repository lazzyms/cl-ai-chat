import asyncio
import sys
from colorama import init, Fore, Style
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.workflow import agent
from agents.supervisor import summarize_history
from cli.session import get_file_ids

# ── Color scheme ─────────────────────────────────────────────────────────────
USER_COLOR = Fore.CYAN + Style.BRIGHT
AI_COLOR = Fore.GREEN
THINK_COLOR = Fore.MAGENTA + Style.DIM
TOOL_CALL_COLOR = Fore.YELLOW + Style.BRIGHT
TOOL_RESULT_COLOR = Fore.YELLOW + Style.DIM
SYSTEM_COLOR = Fore.BLUE + Style.DIM
ERROR_COLOR = Fore.RED + Style.BRIGHT

# ── Tuning knobs ──────────────────────────────────────────────────────────────
SUMMARY_THRESHOLD = 20  # total messages before compression
KEEP_RECENT = 6  # messages kept verbatim after summarization

# ── Spinner ───────────────────────────────────────────────────────────────────
_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


async def _spin(msg: str, stop_event: asyncio.Event):
    """Animated spinner; stops when stop_event is set."""
    i = 0
    try:
        while not stop_event.is_set():
            frame = _FRAMES[i % len(_FRAMES)]
            sys.stdout.write(f"\r{THINK_COLOR}{frame}  {msg}{Style.RESET_ALL}   ")
            sys.stdout.flush()
            i += 1
            await asyncio.sleep(0.08)
    finally:
        sys.stdout.write(f"\r{' ' * (len(msg) + 8)}\r")
        sys.stdout.flush()


class Spinner:
    """Context-manager / awaitable spinner backed by an asyncio task."""

    def __init__(self, msg: str):
        self._msg = msg
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self):
        self._stop.clear()
        self._task = asyncio.create_task(_spin(self._msg, self._stop))
        return self

    async def stop(self):
        self._stop.set()
        if self._task:
            await self._task
            self._task = None

    async def swap(self, new_msg: str):
        """Stop current spinner and start a new one with a different message."""
        await self.stop()
        self._msg = new_msg
        self.start()


# ── Summarization helper ──────────────────────────────────────────────────────
async def maybe_summarize(history: list) -> list:
    if len(history) <= SUMMARY_THRESHOLD:
        return history

    to_summarize = history[:-KEEP_RECENT]
    recent = history[-KEEP_RECENT:]

    print(
        f"\r{SYSTEM_COLOR}📝  Summarizing older context ({len(to_summarize)} messages)…{Style.RESET_ALL}"
    )
    summary_text = await summarize_history(to_summarize)
    compressed = [
        SystemMessage(content=f"[Conversation summary]: {summary_text}")
    ] + recent

    print(
        f"{SYSTEM_COLOR}   ✓ Compressed to {len(compressed)} messages{Style.RESET_ALL}\n"
    )
    return compressed


# ── Thinking-tag renderer ─────────────────────────────────────────────────────
class _ThinkParser:
    """Splits streaming text into (thinking, response) segments on-the-fly."""

    def __init__(self):
        self._buf = ""
        self._in_think = False
        self._think_done = False  # once </think> seen, never go back

    def feed(self, text: str):
        """Returns list of (is_thinking: bool, segment: str) pairs."""
        self._buf += text
        out = []

        while self._buf:
            if self._in_think:
                end = self._buf.find("</think>")
                if end == -1:
                    out.append((True, self._buf))
                    self._buf = ""
                else:
                    out.append((True, self._buf[:end]))
                    self._buf = self._buf[end + len("</think>") :]
                    self._in_think = False
                    self._think_done = True
            else:
                start = self._buf.find("<think>")
                if start == -1 or self._think_done:
                    out.append((False, self._buf))
                    self._buf = ""
                else:
                    if start > 0:
                        out.append((False, self._buf[:start]))
                    self._buf = self._buf[start + len("<think>") :]
                    self._in_think = True
        return out


# ── Single turn execution ─────────────────────────────────────────────────────
async def run_turn(history: list, user_input: str, file_id: str | None = None) -> list:
    """
    Stream one conversation turn.
    Returns the extended history list (original + HumanMessage + all
    graph-generated messages appended).
    """
    new_history = history + [HumanMessage(content=user_input)]

    spinner = Spinner("Thinking…").start()

    # Accumulate full messages by id for history (dict preserves insertion order)
    accumulated: dict[str, object] = {}

    first_ai_token = True  # print the AI label once per response block
    ai_printing = False  # True once we have started printing AI content
    parser = _ThinkParser()

    # Agent nodes that produce streaming LLM tokens
    _LLM_NODES = {"search", "retriever", "general"}
    # Tool executor nodes
    _TOOL_NODES = {"search_tool", "retriever_tool"}

    try:
        async for mode, data in agent.astream(
            {"messages": new_history, "file_id": file_id},
            stream_mode=["messages", "updates"],
        ):
            # ── Supervisor decision → update spinner label ─────────────────────
            if mode == "updates":
                if "supervisor" in data:
                    route = data["supervisor"].get("route", "")
                    if route == "search":
                        await spinner.swap("Searching…")
                    elif route == "retriever":
                        await spinner.swap("Fetching document…")
                    elif route == "general":
                        await spinner.swap("Processing…")
                continue

            # mode == "messages": data is (chunk, metadata)
            chunk, metadata = data
            node = metadata.get("langgraph_node", "")

            # ── Accumulate chunks by id for history ───────────────────────────
            cid = getattr(chunk, "id", None)
            if cid:
                if cid in accumulated:
                    try:
                        accumulated[cid] = accumulated[cid] + chunk
                    except Exception:
                        accumulated[cid] = chunk
                else:
                    accumulated[cid] = chunk

            # ── Display logic ─────────────────────────────────────────────────
            if node in _LLM_NODES:
                tool_calls = getattr(chunk, "tool_calls", None) or (
                    getattr(chunk, "additional_kwargs", {}).get("tool_calls")
                )
                has_tool_calls = bool(tool_calls)
                has_content = bool(getattr(chunk, "content", ""))

                if has_tool_calls and not has_content:
                    # LLM decided to call a tool — show what it's fetching
                    tc_list = tool_calls if isinstance(tool_calls, list) else []
                    for tc in tc_list:
                        args = (
                            tc.get("args", {})
                            if isinstance(tc, dict)
                            else getattr(tc, "args", {})
                        )
                        query_val = next(iter(args.values()), None) if args else None
                        if query_val:
                            if node == "retriever":
                                await spinner.swap(f'Fetching "{query_val}"…')
                            else:
                                await spinner.swap(f'Searching for "{query_val}"…')
                        break
                    first_ai_token = True
                    parser = _ThinkParser()

                elif has_content:
                    text = str(chunk.content)
                    if first_ai_token:
                        await spinner.stop()
                        sys.stdout.write(f"{AI_COLOR}🤖  {Style.RESET_ALL}")
                        sys.stdout.flush()
                        first_ai_token = False
                        ai_printing = True

                    for is_thinking, seg in parser.feed(text):
                        if seg:
                            color = THINK_COLOR if is_thinking else AI_COLOR
                            sys.stdout.write(f"{color}{seg}{Style.RESET_ALL}")
                            sys.stdout.flush()

            elif node in _TOOL_NODES:
                await spinner.stop()
                content = getattr(chunk, "content", "")
                if content:
                    preview = str(content)[:240]
                    if len(str(content)) > 240:
                        preview += "…"
                    print(f"\n{TOOL_RESULT_COLOR}   ↳ {preview}{Style.RESET_ALL}")
                if node == "retriever_tool":
                    await spinner.swap("Analysing document…")
                else:
                    await spinner.swap("Processing results…")
                first_ai_token = True
                parser = _ThinkParser()

    finally:
        await spinner.stop()

    if ai_printing:
        print()  # trailing newline after AI tokens

    # Update history: inputs + every new message the graph emitted
    return new_history + list(accumulated.values())


# ── Main REPL ─────────────────────────────────────────────────────────────────
async def chat_loop():
    init(autoreset=False)

    print(f"\n{SYSTEM_COLOR}{'─' * 52}")
    print(f"  cl-ai-chat  |  new session (no history persisted)")
    print(f"  type 'exit', 'quit', or 'bye' to end")
    print(f"{'─' * 52}{Style.RESET_ALL}\n")

    file_id = get_file_ids()

    if file_id:
        print(
            f"{SYSTEM_COLOR}  Document session active  |  file_id: {file_id}{Style.RESET_ALL}\n"
        )
    else:
        print(
            f"{SYSTEM_COLOR}  No document attached  |  general chat mode{Style.RESET_ALL}\n"
        )

    conversation_history: list = []

    while True:
        try:
            sys.stdout.write(f"{USER_COLOR}You: {Style.RESET_ALL}")
            sys.stdout.flush()
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{SYSTEM_COLOR}Session ended.{Style.RESET_ALL}")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye"}:
            print(f"🤖 {SYSTEM_COLOR}Goodbye!{Style.RESET_ALL}")
            break
        if user_input.lower() in {"thank you", "thanks", "thank you!", "thanks!"}:
            print(f"{SYSTEM_COLOR}You're welcome!{Style.RESET_ALL}")
            continue

        # Compress history if it's getting long
        conversation_history = await maybe_summarize(conversation_history)

        try:
            conversation_history = await run_turn(
                conversation_history, user_input, file_id
            )
        except Exception as exc:
            print(f"\n{ERROR_COLOR}Error: {exc}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    asyncio.run(chat_loop())
