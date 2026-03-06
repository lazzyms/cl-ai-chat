from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import ToolNode

from agents.state import AgentState
from config.settings import settings
from prompts.review_nodes import review_nodes_prompt
from tools.file_traversal_tool import get_node_content, get_node_summary, get_tree

llm = ChatOllama(model=settings.model, temperature=0)

tools = [get_tree, get_node_content, get_node_summary]

retriever_tool_node = ToolNode(tools)

llm_with_tools = llm.bind_tools(tools)

prompt = ChatPromptTemplate.from_messages(
    [("system", review_nodes_prompt), MessagesPlaceholder(variable_name="messages")]
)


async def retriever_agent(state: AgentState):
    messages = state["messages"]
    file_id = state.get("file_id", "")
    formatted = prompt.format_messages(messages=messages, file_id=file_id)
    response = await llm_with_tools.ainvoke(formatted)
    return {"messages": [response]}
