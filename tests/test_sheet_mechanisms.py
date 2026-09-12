"""Sheet §9 mechanisms and computed fire/CD pacing — Class B labeled."""

from __future__ import annotations

import json
from pathlib import Path

from domain_kit.loader import load_kit
from reasoning.cascade_engine import CascadeEngine
from reasoning.evidence import Verdict, classify_evidence

ROOT = Path(__file__).resolve().parents[1]


def test_fire_pump_test_to_tank_invalid():
    packet = json.loads((ROOT / "fixtures/engineering/fire_pump_test_to_tank.json").read_text())
    result = classify_evidence(packet)
    assert result.verdict is Verdict.FAIL
    assert "INV-FIRE-PUMP-TEST-TO-TANK" in result.invalidity_ids
    assert result.as_dict()["evidence_class"] in {"D", "B"}
    assert result.as_dict()["document_status"] == "UNVERIFIED"


def test_covers_clips_sheet_mechanism():
    packet = json.loads((ROOT / "fixtures/engineering/fire_pump_covers_clips.json").read_text())
    result = classify_evidence(packet)
    assert "INV-FIRE-PUMP-COVERS-CLIPS" in result.invalidity_ids
    assert result.verdict is Verdict.UNPROVABLE


def test_grms_cert_ne_config():
    packet = json.loads((ROOT / "fixtures/engineering/grms_cert_mismatch.json").read_text())
    result = classify_evidence(packet)
    assert result.verdict is Verdict.UNPROVABLE
    assert "INV-GRMS-CERT-NE-CONFIG" in result.invalidity_ids


def test_never_infer_integrated_from_unit_tests():
    packet = json.loads((ROOT / "fixtures/engineering/ce_unit_tests_only.json").read_text())
    result = classify_evidence(packet)
    assert result.verdict is Verdict.UNPROVABLE
    assert "INV-CE-UNIT-NOT-INTEGRATED" in result.invalidity_ids


def test_fire_cd_is_computed_master_pacer():
    result = CascadeEngine().compute_critical_path()
    pacer = result.master_pacer
    assert pacer["method"] == "max_earliest_finish_on_licensing_path"
    assert pacer["kind"] == "fire_cd"
    assert pacer["milestone"] == "M13"
    assert pacer["evidence_class"] == "B"
    # Not a hardcoded constant: M13 wins because its EF is greatest on the path.
    path = pacer["computed_from"]
    assert result.earliest_finish["M13"] == max(result.earliest_finish[m] for m in path if m in result.earliest_finish)


def test_mitigation_library_m1_to_m15_class_b():
    kit = load_kit()
    ids = {row["id"] for row in kit.pre_opening_mitigations["library"]}
    expected = {f"M-{i}" for i in range(1, 16)}
    assert expected <= ids
    assert all(row["evidence_class"] == "B" for row in kit.pre_opening_mitigations["library"])
    m6 = next(r for r in kit.pre_opening_mitigations["library"] if r["id"] == "M-6")
    assert "IPTV" in m6["risk"] or "iptv" in m6["root_cause"].lower() or "IPTV" in m6["mitigation"]


def test_structural_gaps_eleven():
    gaps = load_kit().structural_gaps["gaps"]
    assert [g["id"] for g in gaps] == list(range(1, 12))
    assert load_kit().structural_gaps["open_list_note"]
