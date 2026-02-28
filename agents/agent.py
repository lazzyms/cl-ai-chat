from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import END

from agents.state import AgentState
from tools.search_tool import search_tool
from prompts.main import system_prompt

llm = ChatOllama(model="qwen3:latest", temperature=0)

tools = [search_tool]

tool_node = ToolNode(tools)

llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), MessagesPlaceholder(variable_name="messages")]
)


async def call_agent(state: AgentState):
    messages = state["messages"]
    formatted = prompt.format_messages(messages=messages)
    response = await llm_with_tools.ainvoke(formatted)
    return {"messages": [response]}


def should_continue(state: AgentState):
    "Router function"
    last_message = state["messages"][-1]

    # Check if the LLM includes tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


async def summarize_history(messages: list[BaseMessage]) -> str:
    """Summarize older conversation messages to compress long histories."""
    summarize_prompt = [
        SystemMessage(
            content=(
                "You are a conversation summarizer. "
                "Summarize the following conversation history concisely, "
                "preserving key facts, decisions, and context the user may reference later. "
                "Output only the summary, no preamble."
            )
        ),
        *messages,
    ]
    response = await llm.ainvoke(summarize_prompt)
    return response.content
