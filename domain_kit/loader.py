"""Load populated domain JSON kits. Empty objects are rejected."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

KIT_ROOT = Path(__file__).resolve().parent


def _read(rel: str) -> Any:
    path = KIT_ROOT / rel
    data = json.loads(path.read_text())
    if data == {} or data == []:
        raise ValueError(f"domain kit {rel} is empty — refuse placeholder content")
    return data


class DomainKit:
    def __init__(self) -> None:
        self.pre_opening_milestones = _read("pre_opening/milestones.json")
        self.pre_opening_milestone_table = _read("pre_opening/milestone_table.json")
        self.pre_opening_cascade = _read("pre_opening/cascade.json")
        self.pre_opening_cascade_rules = _read("pre_opening/cascade_rules.json")
        self.pre_opening_lrm = _read("pre_opening/lrm.json")
        self.pre_opening_mitigations = _read("pre_opening/mitigations.json")
        self.pre_opening_registry = _read("pre_opening/registry.json")
        self.pre_opening_ffe_ose = _read("pre_opening/ffe_ose.json")
        self.engineering_classes = _read("engineering_inheritance/classes_a_d.json")
        self.category_a_systems = _read("engineering_inheritance/category_a_systems.json")
        self.category_b_design_locked = _read("engineering_inheritance/category_b_design_locked.json")
        self.category_c_handover_timing = _read("engineering_inheritance/category_c_handover_timing.json")
        self.category_d_commercial_drag = _read("engineering_inheritance/category_d_commercial_drag.json")
        self.asset_register_source_note = _read(
            "engineering_inheritance/asset_register_source_note.json"
        )
        self.evidence_invalidity_cases = _read(
            "engineering_inheritance/evidence_invalidity_cases.json"
        )
        self.licensing_generic = _read("licensing/generic_template.json")
        self.licensing_uae = _read("licensing/uae/licenses.json")
        self.licensing_prereq = _read("licensing/uae/prerequisite_map.json")
        self.ppm_uae_statutory = _read("ppm/uae_statutory.json")
        self.ppm_operator_sop_layer = _read("ppm/operator_sop_layer.json")
        self.ppm_refuse_policy = _read("ppm/refuse_policy.json")
        self.structural_gaps = _read("meta/structural_gaps.json")
        self.booking_funnel = _read("guest_journey/booking_funnel.json")
        self.loyalty_tiers = _read("guest_journey/loyalty_tiers.json")
        self.personalization_schema = _read("guest_journey/personalization_schema.json")
        self.crm_event_taxonomy = _read("guest_journey/crm_event_taxonomy.json")

    def milestone(self, milestone_id: str) -> dict[str, Any]:
        for row in self.pre_opening_milestones["milestones"]:
            if row["id"] == milestone_id:
                return row
        raise KeyError(milestone_id)

    def mitigations_for(self, milestone_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self.pre_opening_mitigations["library"]
            if row.get("programme_milestone") == milestone_id or row.get("milestone") == milestone_id or row.get("id") == milestone_id
        ]

    def mitigation_for(self, milestone_id: str) -> dict[str, Any]:
        rows = self.mitigations_for(milestone_id)
        if not rows:
            raise KeyError(milestone_id)
        return rows[0]

    def invalidity_case(self, case_id: str) -> dict[str, Any]:
        for row in self.evidence_invalidity_cases["cases"]:
            if row["id"] == case_id:
                return row
        raise KeyError(case_id)


@lru_cache(maxsize=1)
def load_kit() -> DomainKit:
    return DomainKit()


def reload_kit() -> DomainKit:
    load_kit.cache_clear()
    return load_kit()
