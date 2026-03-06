from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import END
from pydantic import BaseModel
from typing import Literal

from agents.state import AgentState
from config.settings import settings
from prompts.supervisor import supervisor_prompt

llm = ChatOllama(model=settings.model, temperature=0)


class RouteDecision(BaseModel):
    route: Literal["search", "retriever", "general"]


structured_llm = llm.with_structured_output(RouteDecision)

prompt = ChatPromptTemplate.from_messages(
    [("system", supervisor_prompt), MessagesPlaceholder(variable_name="messages")]
)


async def supervisor(state: AgentState):
    messages = state["messages"]
    formatted = prompt.format_messages(messages=messages)
    decision: RouteDecision = await structured_llm.ainvoke(formatted)
    return {"route": decision.route}


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
