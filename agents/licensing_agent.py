from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from agents.tools import emit_agent, tool_licensing
from hotelops.llm import get_llm


def _evaluate(state: AgentState) -> AgentState:
    payload = state.get("payload") or {}
    market = state.get("market") or payload.get("market") or "uae"
    result = tool_licensing(market, payload.get("satisfied"))
    note = get_llm().complete(f"license pack {market} {result.get('overall')}")
    emit_agent("ops.licensing.evaluated", "ops", {"market": market, "overall": result.get("overall")})
    return {**state, "result": result, "notes": note}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("evaluate", _evaluate)
    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile()
