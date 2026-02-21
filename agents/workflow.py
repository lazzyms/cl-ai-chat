from langgraph.graph import StateGraph
from langgraph.graph import END

from agents.agent import call_agent, should_continue, tool_node
from agents.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_agent)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",  # from this node
    should_continue,  # decider function
    {"tools": "tools", END: END},  # tools node or finish
)

workflow.add_edge("tools", "agent")  # after tools execute go back to agent

agent = workflow.compile()
