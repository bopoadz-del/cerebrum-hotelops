"""Acceptance A01–A05 + guest. Writes tests/RUNLOG.md."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from connectors.grms import GRMSConnector
from connectors.opera import OperaConnector
from guest_intelligence.booking_intelligence import BookingIntelligence
from guest_intelligence.crm import GuestCRM
from hotelops.event_bus import get_bus
from reasoning.cascade_engine import CascadeEngine
from reasoning.evidence import classify_evidence
from reasoning.guard import GuardError, guard_request
from reasoning.licensing import LicensingEngine
from reasoning.ppm_resolver import PPMRefuse, PPMResolver

ROOT = Path(__file__).resolve().parents[2]
RUNLOG = ROOT / "tests" / "RUNLOG.md"
RESULTS: list[str] = []


def _log(aid: str, ok: bool, detail: str) -> None:
    RESULTS.append(f"- {'PASS' if ok else 'FAIL'} **{aid}**: {detail}")


@pytest.fixture(scope="session", autouse=True)
def _write_runlog():
    yield
    RUNLOG.write_text(
        "# HotelOps acceptance RUNLOG\n\n"
        "Offline pytest — no Opera/Micros/Jetson/LLM secrets.\n\n"
        + "\n".join(RESULTS)
        + "\n"
    )


@pytest.mark.acceptance
def test_a01_pre_opening_critical_path():
    result = CascadeEngine().simulate({"M07": 10})
    ok = "M15" in result.critical_path and bool(result.lrm_alerts)
    _log("A01", ok, f"critical_path={result.critical_path} alerts={len(result.lrm_alerts)}")
    assert ok


@pytest.mark.acceptance
def test_a02_fire_pump_invalidity():
    packet = json.loads((ROOT / "fixtures/engineering/fire_pump_covers_clips.json").read_text())
    judged = classify_evidence(packet)
    ok = "INV-FIRE-PUMP-COVERS-CLIPS" in judged.invalidity_ids
    _log("A02", ok, judged.as_dict().__repr__())
    assert ok


@pytest.mark.acceptance
def test_a03_uae_licensing_prereqs():
    pack = LicensingEngine().evaluate("uae", {})
    ids = {r["id"] for r in pack["licenses"]}
    ok = {"UAE-CD", "UAE-DTCM", "UAE-CCTV", "UAE-UTIL", "UAE-ISP"}.issubset(ids)
    _log("A03", ok, f"licenses={sorted(ids)}")
    assert ok
    with pytest.raises(GuardError):
        guard_request(market="riyadh")


@pytest.mark.acceptance
def test_a04_ppm_two_layer_refuse():
    with pytest.raises(PPMRefuse):
        PPMResolver().resolve(market="uae", asset_type="fire_pump", operator_sop=None)
    wo = PPMResolver().resolve(
        market="uae",
        asset_type="fire_pump",
        operator_sop="SOP: monthly flow test witnessed by engineering.",
    )
    ok = wo.task_id == "PPM-CD-FIRE-PUMP"
    _log("A04", ok, "refuse without SOP; issue with SOP")
    assert ok


@pytest.mark.acceptance
def test_a05_dual_surface_event_bus():
    OperaConnector().ingest("reservations")
    GRMSConnector().ingest("config")
    guest_events = get_bus().history(surface="guest")
    ops_events = get_bus().history(surface="ops")
    ok = bool(guest_events) and bool(ops_events)
    _log("A05", ok, f"guest={len(guest_events)} ops={len(ops_events)}")
    assert ok


@pytest.mark.acceptance
def test_a_guest_intelligence():
    markets = {p["market"] for p in GuestCRM().list_profiles()}
    stay = BookingIntelligence().place("G-NOOR")["stage"]
    ok = markets == {"uae", "generic"} and stay == "stay"
    _log("A-GUEST", ok, f"markets={markets} noor_stage={stay}")
    assert ok
