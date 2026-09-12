"""Minimal MCP-style tool listing for operators (stdio-less HTTP)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal
from hotelops.actions import get_registry
from hotelops.retrieval import retrieve

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/tools")
def tools(_: Principal = Depends(get_principal)):
    return {
        "protocol": "hotelops-mcp-http",
        "tools": get_registry().list()
        + [
            {"action_id": "retrieval.search", "description": "Hybrid kit retrieval", "surfaces": ["ops", "guest"]},
            {"action_id": "agent.run", "description": "Coordinator LangGraph", "surfaces": ["ops", "guest"]},
        ],
    }


@router.post("/retrieve")
def mcp_retrieve(body: dict, _: Principal = Depends(get_principal)):
    # Reviewers may search the kit; this path does not persist product state.
    return {"hits": retrieve(body.get("query", ""), limit=int(body.get("limit", 8)))}
