from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    intent: str
    market: str
    payload: dict[str, Any]
    route: str
    result: dict[str, Any]
    notes: str
