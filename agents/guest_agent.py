from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools import emit_agent, tool_guest
from hotelops.llm import get_llm


def _profile(state: AgentState) -> AgentState:
    guest_id = (state.get("payload") or {}).get("guest_id", "G-AYA")
    result = tool_guest(guest_id)
    note = get_llm().complete(f"guest intelligence {guest_id}")
    emit_agent("guest.intelligence.ready", "guest", {"guest_id": guest_id})
    return {**state, "result": result, "notes": note}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("profile", _profile)
    graph.add_edge(START, "profile")
    graph.add_edge("profile", END)
    return graph.compile()
