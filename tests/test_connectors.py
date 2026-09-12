from __future__ import annotations

from connectors.grms import GRMSConnector
from connectors.maximo import MaximoConnector
from connectors.opera import OperaConnector
from hotelops.event_bus import get_bus


def test_opera_normalises_and_emits_guest_events():
    result = OperaConnector().ingest("reservations")
    assert result["mode"] == "fixture"
    assert result["emitted"] >= 3
    topics = {e["topic"] for e in result["events"]}
    assert "guest.booking.reservation" in topics
    assert get_bus().history(surface="guest")


def test_grms_complete_map_passes():
    result = GRMSConnector().ingest("config")
    event = result["events"][0]
    assert event["payload"]["room_map_complete"] is True
    assert event["verdict"] == "PASS"


def test_grms_incomplete_is_unprovable():
    import json

    conn = GRMSConnector()
    conn.connect()
    raw = json.loads((conn.fixture_dir / "config_incomplete.json").read_text())
    events = conn.normalise("config", raw)
    assert events[0].verdict == "UNPROVABLE"


def test_maximo_assets_ops_surface():
    result = MaximoConnector().ingest("assets")
    assert result["emitted"] >= 3
    assert all(e["surface"] == "ops" for e in result["events"])
    assert any(e["payload"]["asset_type"] == "fire_pump" for e in result["events"])
