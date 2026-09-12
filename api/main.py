"""HotelOps API — ops reasoner + guest intelligence on one event bus."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.audit_middleware import AuditMiddleware
from api.mcp_server import router as mcp_router
from api.routes import actions, audit, documents, engineering, guest, licensing, operational, pre_opening
from hotelops.db import init_db
from hotelops.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Cerebrum HotelOps",
    version="1.0.0",
    description="Pilot-ready hospitality AI — UAE + generic, dual surfaces, fixture-first.",
)

app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pre_opening.router)
app.include_router(engineering.router)
app.include_router(licensing.router)
app.include_router(guest.router)
app.include_router(operational.router)
app.include_router(documents.router)
app.include_router(actions.router)
app.include_router(audit.router)
app.include_router(mcp_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "product": "cerebrum-hotelops",
        "markets": ["uae", "generic"],
        "surfaces": ["ops", "guest"],
        "fixture_mode": settings.fixture_mode,
        "llm": settings.llm_provider,
    }


FRONTEND = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="ui")


def create_app() -> FastAPI:
    return app
