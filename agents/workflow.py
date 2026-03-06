from langgraph.graph import StateGraph
from langgraph.graph import END

from agents.subagents.general_agent import general_agent
from agents.subagents.retriever_agent import retriever_agent, retriever_tool_node
from agents.subagents.search_agent import search_agent, search_tool_node
from agents.supervisor import supervisor
from agents.state import AgentState

workflow = StateGraph(AgentState)


def route_supervisor(state: AgentState):
    """Route from supervisor to the appropriate subagent based on state['route']."""
    route = state.get("route", "general")
    if route == "search":
        return "search"
    elif route == "retriever":
        # Only route to retriever when an active document session exists
        if state.get("file_id"):
            return "retriever"
        return "general"
    return "general"


def should_search(state: AgentState):
    """Route from search agent: call search_tool if there are pending tool calls, else END."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "search_tool"
    return END


def should_retrieve(state: AgentState):
    """Route from retriever agent: call retriever_tool if there are pending tool calls, else END."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "retriever_tool"
    return END


workflow.add_node("supervisor", supervisor)
workflow.add_node("search", search_agent)
workflow.add_node("search_tool", search_tool_node)
workflow.add_node("retriever", retriever_agent)
workflow.add_node("retriever_tool", retriever_tool_node)
workflow.add_node("general", general_agent)
workflow.set_entry_point("supervisor")

# Supervisor routes to the chosen subagent
workflow.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {"search": "search", "retriever": "retriever", "general": "general"},
)

# Search agent loops through its tool node until done
workflow.add_conditional_edges(
    "search",
    should_search,
    {"search_tool": "search_tool", END: END},
)

# Retriever agent loops through its tool node until done
workflow.add_conditional_edges(
    "retriever",
    should_retrieve,
    {"retriever_tool": "retriever_tool", END: END},
)

workflow.add_edge("search_tool", "search")  # after tools execute go back to agent
workflow.add_edge("retriever_tool", "retriever")  # after tools execute go back to agent
workflow.add_edge("general", END)
agent = workflow.compile()
