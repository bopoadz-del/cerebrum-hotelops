"""Live-pilot security: fail-closed tokens, audit attribution, operator mutations, CORS."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from hotelops.db import get_sessionmaker
from hotelops.models import AuditEvent
from hotelops.settings import AuthTokensNotConfigured, get_settings, require_auth_tokens

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = {"Authorization": "Bearer operator-pilot"}
REVIEWER = {"Authorization": "Bearer reviewer-pilot"}


def _client() -> TestClient:
    return TestClient(app)


def _latest_audit(path: str) -> AuditEvent | None:
    session = get_sessionmaker()()
    try:
        return (
            session.query(AuditEvent)
            .filter(AuditEvent.path == path)
            .order_by(AuditEvent.id.desc())
            .first()
        )
    finally:
        session.close()


def test_settings_source_has_no_hardcoded_pilot_tokens():
    text = (ROOT / "hotelops" / "settings.py").read_text()
    assert "operator-pilot" not in text
    assert "reviewer-pilot" not in text


def test_empty_tokens_refuse_configuration(monkeypatch):
    monkeypatch.setenv("HOTELOPS_OPERATOR_TOKEN", "")
    monkeypatch.setenv("HOTELOPS_REVIEWER_TOKEN", "")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.operator_token == ""
    assert settings.reviewer_token == ""
    assert settings.auth_tokens_configured() is False
    with pytest.raises(AuthTokensNotConfigured):
        require_auth_tokens(settings)


def test_app_startup_refuses_empty_tokens(monkeypatch):
    monkeypatch.setenv("HOTELOPS_OPERATOR_TOKEN", "")
    monkeypatch.setenv("HOTELOPS_REVIEWER_TOKEN", "")
    get_settings.cache_clear()
    with pytest.raises(AuthTokensNotConfigured):
        with TestClient(app):
            pass


def test_reviewer_cannot_run_actions_or_other_mutations():
    client = _client()
    denied = client.post(
        "/actions/engineering.classify",
        json={"asset_type": "grms", "room_map_complete": False},
        headers=REVIEWER,
    )
    assert denied.status_code == 403
    assert client.get("/actions", headers=REVIEWER).status_code == 200
    assert client.post("/mcp/retrieve", json={"query": "ppm"}, headers=REVIEWER).status_code == 200
    create = client.post(
        "/documents",
        json={"title": "x", "doc_type": "note", "body": "no"},
        headers=REVIEWER,
    )
    assert create.status_code == 403


def test_operator_can_run_action():
    client = _client()
    ok = client.post(
        "/actions/engineering.classify",
        json={"asset_type": "grms", "room_map_complete": False},
        headers=OPERATOR,
    )
    assert ok.status_code == 200
    assert ok.json()["verdict"] == "UNPROVABLE"


def test_audit_uses_principal_not_client_headers():
    client = _client()
    forged = {
        **REVIEWER,
        "x-actor": "operator",
        "x-role": "operator",
    }
    r = client.get("/pre-opening/milestones", headers=forged)
    assert r.status_code == 200
    row = _latest_audit("/pre-opening/milestones")
    assert row is not None
    assert row.actor == "reviewer"
    assert row.role == "reviewer"


def test_audit_ignores_authorization_substring():
    client = _client()
    r = client.get(
        "/pre-opening/milestones",
        headers={"Authorization": "Bearer not-an-operator-token"},
    )
    assert r.status_code == 403
    row = _latest_audit("/pre-opening/milestones")
    assert row is not None
    assert row.actor == "anonymous"
    assert row.role == "unknown"


def test_unauthenticated_audit_is_anonymous():
    client = _client()
    r = client.get("/pre-opening/milestones", headers={"x-actor": "operator", "x-role": "operator"})
    assert r.status_code in {401, 403}
    row = _latest_audit("/pre-opening/milestones")
    assert row is not None
    assert row.actor == "anonymous"
    assert row.role == "unknown"


def test_health_is_not_audited():
    client = _client()
    session = get_sessionmaker()()
    before = session.query(AuditEvent).count()
    session.close()
    assert client.get("/health").status_code == 200
    session = get_sessionmaker()()
    after = session.query(AuditEvent).count()
    session.close()
    assert after == before


def test_audit_failure_fail_closed_on_mutating_success(monkeypatch):
    def boom(**_kwargs):
        raise RuntimeError("audit db down")

    monkeypatch.setattr("api.audit_middleware.persist_audit_event", boom)
    client = _client()
    r = client.post(
        "/actions/engineering.classify",
        json={"asset_type": "grms", "room_map_complete": False},
        headers=OPERATOR,
    )
    assert r.status_code == 503
    assert r.json()["detail"] == "audit persistence failed"


def test_audit_failure_does_not_hide_reads(monkeypatch):
    def boom(**_kwargs):
        raise RuntimeError("audit db down")

    monkeypatch.setattr("api.audit_middleware.persist_audit_event", boom)
    client = _client()
    r = client.get("/pre-opening/milestones", headers=OPERATOR)
    assert r.status_code == 200


def test_cors_allowlist_rejects_star_and_unknown_origin():
    settings = get_settings()
    origins = settings.cors_origin_list()
    assert "*" not in origins
    assert "http://127.0.0.1:43123" in origins
    assert "http://localhost:43123" in origins

    client = _client()
    denied = client.options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert denied.headers.get("access-control-allow-origin") not in {"*", "https://evil.example"}

    allowed = client.options(
        "/health",
        headers={"Origin": "http://127.0.0.1:43123", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:43123"
    assert allowed.headers.get("access-control-allow-credentials") != "true"


def test_auth_uses_compare_digest_and_audit_is_not_base_http_middleware():
    auth = (ROOT / "api" / "auth.py").read_text()
    audit = (ROOT / "api" / "audit_middleware.py").read_text()
    assert "hmac.compare_digest" in auth
    assert "from starlette.middleware.base import BaseHTTPMiddleware" not in audit
    assert "class AuditMiddleware(BaseHTTPMiddleware)" not in audit
    assert "init_db()" not in audit
