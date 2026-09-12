"""Persist every API call to audit_events."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from hotelops.db import get_sessionmaker, init_db
from hotelops.models import AuditEvent


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/health") or request.url.path.startswith("/assets"):
            return response
        actor = request.headers.get("x-actor", "anonymous")
        role = request.headers.get("x-role", "unknown")
        auth = request.headers.get("authorization", "")
        if "operator" in auth:
            role = "operator"
            actor = "operator"
        elif "reviewer" in auth:
            role = "reviewer"
            actor = "reviewer"
        try:
            init_db()
            session = get_sessionmaker()()
            session.add(
                AuditEvent(
                    actor=actor,
                    role=role,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    detail="",
                )
            )
            session.commit()
            session.close()
        except Exception:
            pass
        return response
