from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import END

from agents.state import AgentState
from config.settings import settings
from tools.search_tool import search_tool
from prompts.search import search_prompt

llm = ChatOllama(model=settings.model, temperature=0)

tools = [search_tool]

search_tool_node = ToolNode(tools)

llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages(
    [("system", search_prompt), MessagesPlaceholder(variable_name="messages")]
)


async def search_agent(state: AgentState):
    messages = state["messages"]
    formatted = prompt.format_messages(messages=messages)
    response = await llm_with_tools.ainvoke(formatted)
    return {"messages": [response]}
