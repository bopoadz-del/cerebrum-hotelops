from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools import emit_agent, tool_evidence, tool_ingest
from hotelops.llm import get_llm


def _judge(state: AgentState) -> AgentState:
    payload = state.get("payload") or {}
    if payload.get("ingest"):
        ingested = tool_ingest(payload.get("connector", "maximo"), payload.get("resource", "assets"))
        result = {"ingest": ingested}
    else:
        result = tool_evidence(payload)
    note = get_llm().complete(f"engineering evidence {result}")
    emit_agent("ops.engineering.judged", "ops", result if "verdict" in result else {"ingest": True})
    return {**state, "result": result, "notes": note}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("judge", _judge)
    graph.add_edge(START, "judge")
    graph.add_edge("judge", END)
    return graph.compile()
