"""Persist API calls to audit_events from the authenticated Principal.

This is a pure ASGI middleware (not BaseHTTPMiddleware) so the response body is
not buffered on ordinary GET/unauthenticated traffic.

SSE caveat: HotelOps has no SSE routes today (`sse-starlette` is a dependency
only). Audit is written after the ASGI app finishes. A future long-lived stream
would delay the row until the stream ends; this middleware will not swallow the
stream the way BaseHTTPMiddleware can. Authenticated mutating responses are
held until the audit row is persisted so a persist failure can be surfaced as
503 instead of a silent 2xx. Do not put SSE on mutating routes.

DB schema is created at app startup (`init_db`); this middleware does not call
it per request.

Accountability: if audit persistence fails on an authenticated mutating request
that would otherwise succeed (2xx), the client receives 503. The handler may
already have committed its own writes — treat 503 as "verify state / retry
carefully" rather than a silent success with no record.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from hotelops.db import get_sessionmaker
from hotelops.models import AuditEvent

from api.auth import ANONYMOUS_ROLE, principal_from_authorization

logger = logging.getLogger("hotelops.audit")

PUBLIC_PREFIXES = ("/health", "/assets")
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
AUDIT_FAIL_DETAIL = "audit persistence failed"


def is_public_audit_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def persist_audit_event(
    *,
    actor: str,
    role: str,
    method: str,
    path: str,
    status_code: int,
    detail: str = "",
) -> None:
    session = get_sessionmaker()()
    try:
        session.add(
            AuditEvent(
                actor=actor,
                role=role,
                method=method,
                path=path,
                status_code=status_code,
                detail=detail,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _header_map(scope: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in scope.get("headers") or []:
        name = key.decode("latin-1").lower()
        if name not in out:
            out[name] = value.decode("latin-1")
    return out


class AuditMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        method = scope.get("method") or ""
        if is_public_audit_path(path):
            await self.app(scope, receive, send)
            return

        headers = _header_map(scope)
        principal = principal_from_authorization(headers.get("authorization"))
        actor = principal.actor
        role = principal.role
        authenticated = role != ANONYMOUS_ROLE
        hold = authenticated and method.upper() in MUTATING_METHODS

        status_code = 500
        start_message: dict[str, Any] | None = None
        body_messages: list[dict[str, Any]] = []

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code, start_message
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                if hold:
                    start_message = message
                    return
            elif hold and message["type"] == "http.response.body":
                body_messages.append(message)
                return
            await send(message)

        await self.app(scope, receive, send_wrapper)

        persist_ok = True
        try:
            persist_audit_event(
                actor=actor,
                role=role,
                method=method,
                path=path,
                status_code=status_code,
            )
        except Exception:
            persist_ok = False
            logger.exception(
                "audit persist failed method=%s path=%s actor=%s role=%s status=%s",
                method,
                path,
                actor,
                role,
                status_code,
            )

        if not hold:
            return

        fail_closed = persist_ok is False and 200 <= status_code < 400
        if fail_closed:
            body = json.dumps({"detail": AUDIT_FAIL_DETAIL}).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        if start_message is not None:
            await send(start_message)
            for message in body_messages:
                await send(message)
            if not body_messages:
                await send({"type": "http.response.body", "body": b""})
