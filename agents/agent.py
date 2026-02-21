from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
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
