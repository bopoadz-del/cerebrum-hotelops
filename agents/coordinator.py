"""Coordinator graph — routes intents to specialist LangGraph agents."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents import engineering, guest_agent, licensing_agent, operational, pre_opening
from agents.state import AgentState
from agents.tools import tool_retrieve
from hotelops.llm import get_llm

_SPECIALISTS = {
    "pre_opening": pre_opening.build_graph,
    "engineering": engineering.build_graph,
    "licensing": licensing_agent.build_graph,
    "guest": guest_agent.build_graph,
    "operational": operational.build_graph,
}


def _route(state: AgentState) -> AgentState:
    intent = (state.get("intent") or "").lower()
    if any(w in intent for w in ("milestone", "cascade", "lrm", "pre-opening", "pre_opening", "opening")):
        route = "pre_opening"
    elif any(w in intent for w in ("fire", "pump", "evidence", "asset", "grms", "inherit")):
        route = "engineering"
    elif any(w in intent for w in ("license", "civil", "dtcm", "permit")):
        route = "licensing"
    elif any(w in intent for w in ("guest", "loyalty", "booking", "crm")):
        route = "guest"
    else:
        route = "operational"
    return {**state, "route": route, "notes": get_llm().complete(f"route {intent} -> {route}")}


def _dispatch(state: AgentState) -> AgentState:
    route = state.get("route") or "operational"
    graph = _SPECIALISTS[route]()
    result_state = graph.invoke(state)
    hits = tool_retrieve(state.get("intent") or route)
    merged = {**result_state, "retrieval": hits}
    return merged


def build_coordinator():
    graph = StateGraph(AgentState)
    graph.add_node("route", _route)
    graph.add_node("dispatch", _dispatch)
    graph.add_edge(START, "route")
    graph.add_edge("route", "dispatch")
    graph.add_edge("dispatch", END)
    return graph.compile()


_COORD = None


def get_coordinator():
    global _COORD
    if _COORD is None:
        _COORD = build_coordinator()
    return _COORD


def run_agent(intent: str, payload: dict[str, Any] | None = None, market: str = "uae") -> dict[str, Any]:
    state: AgentState = {"intent": intent, "payload": payload or {}, "market": market}
    return get_coordinator().invoke(state)
