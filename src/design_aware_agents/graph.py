from __future__ import annotations

from langgraph.graph import END, StateGraph

from design_aware_agents.nodes import analyze_node, refactor_node, route_after_validate, validate_node
from design_aware_agents.state import AgentState


def build_app():
    g = StateGraph(AgentState)
    g.add_node("analyze", analyze_node)
    g.add_node("refactor", refactor_node)
    g.add_node("validate", validate_node)

    g.set_entry_point("analyze")
    g.add_edge("analyze", "refactor")
    g.add_edge("refactor", "validate")
    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"refactor": "refactor", "end": END},
    )
    return g.compile()
