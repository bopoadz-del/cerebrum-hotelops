from __future__ import annotations

import json
from pathlib import Path

import pytest

from reasoning.cascade_engine import CascadeEngine
from reasoning.evidence import EvidenceClass, Verdict, classify_evidence
from reasoning.guard import GuardError, guard_request
from reasoning.licensing import LicensingEngine
from reasoning.ppm_resolver import PPMRefuse, PPMResolver

ROOT = Path(__file__).resolve().parents[1]


def test_fire_pump_covers_clips_invalid():
    packet = json.loads((ROOT / "fixtures/engineering/fire_pump_covers_clips.json").read_text())
    result = classify_evidence(packet)
    assert "INV-FIRE-PUMP-COVERS-CLIPS" in result.invalidity_ids
    assert result.verdict in {Verdict.FAIL, Verdict.UNPROVABLE}
    assert result.evidence_class in {EvidenceClass.D, EvidenceClass.UNPROVABLE}


def test_fire_pump_class_a_pass():
    packet = json.loads((ROOT / "fixtures/engineering/fire_pump_class_a.json").read_text())
    result = classify_evidence(packet)
    assert result.evidence_class is EvidenceClass.A
    assert result.verdict is Verdict.PASS


def test_grms_incomplete_unprovable():
    result = classify_evidence({"asset_type": "grms", "room_map_complete": False})
    assert result.verdict is Verdict.UNPROVABLE
    assert "INV-GRMS-ROOM-MAP" in result.invalidity_ids


def test_critical_path_computed():
    result = CascadeEngine().compute_critical_path()
    assert result.critical_path
    assert "M01" in result.critical_path
    assert "M15" in result.critical_path
    assert result.project_days > 0
    assert result.float_days["M01"] == 0


def test_cascade_simulator_compounds_m07():
    baseline = CascadeEngine().compute_critical_path()
    slipped = CascadeEngine().simulate({"M07": 10})
    assert slipped.simulated_finish_days >= baseline.project_days
    assert any(a["id"] == "LRM-02" for a in slipped.lrm_alerts)


def test_ppm_refuse_without_sop():
    with pytest.raises(PPMRefuse) as exc:
        PPMResolver().resolve(market="uae", asset_type="fire_pump", operator_sop="")
    assert exc.value.code == "sop_missing"


def test_ppm_issues_with_sop():
    wo = PPMResolver().resolve(
        market="uae",
        asset_type="fire_pump",
        operator_sop="# Monthly fire pump flow test\n1. Isolate.\n2. Flow.\n3. Record.",
    )
    assert wo.task_id == "PPM-CD-FIRE-PUMP"
    assert wo.sop_present


def test_unsupported_market_refused():
    with pytest.raises(GuardError):
        guard_request(market="singapore")
    with pytest.raises(GuardError):
        guard_request(source_system="aconex")
    with pytest.raises(GuardError):
        guard_request(market="ksa")


def test_uae_licensing_cctv_and_utilities_are_prereqs():
    pack = LicensingEngine().evaluate("uae", {"UAE-DED": "PASS"})
    cd = next(r for r in pack["licenses"] if r["id"] == "UAE-CD")
    assert "UAE-CCTV" in cd["missing_prerequisites"] or cd["verdict"] != "PASS"
    assert pack["soft_opening_blocked"]
