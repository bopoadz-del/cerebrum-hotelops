from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools import emit_agent, tool_ingest, tool_ppm
from hotelops.llm import get_llm


def _ops(state: AgentState) -> AgentState:
    payload = state.get("payload") or {}
    if payload.get("asset_type"):
        result = tool_ppm(
            payload.get("market") or state.get("market") or "uae",
            payload["asset_type"],
            payload.get("operator_sop"),
            payload.get("task_id"),
        )
    else:
        result = tool_ingest(payload.get("connector", "opera"), payload.get("resource", "in_house"))
    note = get_llm().complete("operational agent")
    emit_agent("ops.operational.tick", "ops", {"keys": list(result.keys())})
    return {**state, "result": result, "notes": note}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("ops", _ops)
    graph.add_edge(START, "ops")
    graph.add_edge("ops", END)
    return graph.compile()
