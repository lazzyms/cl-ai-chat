from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import END

from agents.state import AgentState
from config.settings import settings
from prompts.general import general_prompt

llm = ChatOllama(model=settings.model, temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [("system", general_prompt), MessagesPlaceholder(variable_name="messages")]
)


async def general_agent(state: AgentState):
    messages = state["messages"]
    formatted = prompt.format_messages(messages=messages)
    response = await llm.ainvoke(formatted)
    return {"messages": [response]}
