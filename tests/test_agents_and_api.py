from __future__ import annotations

from fastapi.testclient import TestClient

from agents.coordinator import run_agent
from api.main import app
from hotelops.actions import get_registry


def test_coordinator_routes_pre_opening():
    state = run_agent("pre-opening cascade slip", {"slips": {"M07": 8}})
    assert state["route"] == "pre_opening"
    assert "critical_path" in state["result"]


def test_coordinator_routes_guest():
    state = run_agent("guest loyalty for G-AYA", {"guest_id": "G-AYA"})
    assert state["route"] == "guest"
    assert state["result"]["loyalty"]["status"] == "ok"


def test_action_registry_audits():
    result = get_registry().run(
        "engineering.classify",
        {"asset_type": "grms", "room_map_complete": False},
        actor="operator",
        role="operator",
    )
    assert result["verdict"] == "UNPROVABLE"


def _client() -> TestClient:
    return TestClient(app)


def test_health_and_auth():
    client = _client()
    assert client.get("/health").json()["markets"] == ["uae", "generic"]
    denied = client.get("/pre-opening/milestones")
    assert denied.status_code in {401, 403}
    ok = client.get("/pre-opening/milestones", headers={"Authorization": "Bearer operator-pilot"})
    assert ok.status_code == 200
    assert len(ok.json()["milestones"]) == 15


def test_licensing_and_ppm_routes():
    client = _client()
    headers = {"Authorization": "Bearer operator-pilot"}
    lic = client.post("/licensing/evaluate", json={"market": "uae", "satisfied": {"UAE-DED": "PASS"}}, headers=headers)
    assert lic.status_code == 200
    ppm = client.post(
        "/operational/ppm",
        json={"market": "uae", "asset_type": "fire_pump", "operator_sop": ""},
        headers=headers,
    )
    assert ppm.json()["status"] == "refused"
