from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools import emit_agent, tool_cascade
from hotelops.llm import get_llm


def _simulate(state: AgentState) -> AgentState:
    slips = (state.get("payload") or {}).get("slips") or {}
    result = tool_cascade(slips)
    note = get_llm().complete(f"pre-opening cascade critical path {result['critical_path']}")
    emit_agent("ops.pre_opening.simulated", "ops", {"critical_path": result["critical_path"]})
    return {**state, "result": result, "notes": note}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("simulate", _simulate)
    graph.add_edge(START, "simulate")
    graph.add_edge("simulate", END)
    return graph.compile()
