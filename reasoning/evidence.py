"""Evidence classes A/B/C/Unprovable and three-valued PASS/FAIL/UNPROVABLE."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from domain_kit.loader import load_kit
from reasoning.sheet import CAVEAT, class_b_meta

class EvidenceClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    UNPROVABLE = "Unprovable"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNPROVABLE = "UNPROVABLE"


FIRE_PUMP_COVER_TAGS = {
    "cover_closed",
    "clip_obscuring_nameplate",
    "plastic_wrap_on_plate",
}


@dataclass
class EvidencePacket:
    asset_type: str
    asset_id: str = ""
    documents: list[str] = field(default_factory=list)
    photo_tags: list[str] = field(default_factory=list)
    nameplate_readable: bool | None = None
    serial_on_certificate: str | None = None
    serial_on_register: str | None = None
    test_age_days: int | None = None
    site_witness: bool = False
    room_map_complete: bool | None = None
    conformity_mark: bool | None = None
    market: str = "generic"
    claimed_class: str | None = None
    test_line_to_tank: bool | None = None
    covers_clips_removed: bool | None = None
    grms_cert_matches_config: bool | None = None
    individual_tests_pass: bool | None = None
    integrated_interface_test: bool | None = None


@dataclass
class EvidenceResult:
    evidence_class: EvidenceClass
    verdict: Verdict
    reasons: list[str]
    invalidity_ids: list[str] = field(default_factory=list)
    remediation: list[str] = field(default_factory=list)
    sheet_meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "evidence_class": self.evidence_class.value,
            "verdict": self.verdict.value,
            "reasons": self.reasons,
            "invalidity_ids": self.invalidity_ids,
            "remediation": self.remediation,
        }
        if self.sheet_meta:
            payload.update(self.sheet_meta)
        else:
            payload.update(class_b_meta())
        return payload


def _packet(raw: EvidencePacket | dict[str, Any]) -> EvidencePacket:
    if isinstance(raw, EvidencePacket):
        return raw
    return EvidencePacket(**{k: v for k, v in raw.items() if k in EvidencePacket.__dataclass_fields__})


def classify_evidence(packet: EvidencePacket | dict[str, Any]) -> EvidenceResult:
    """Sheet §9 mechanisms + three-valued verdicts.

    Sheet-derived invalidity is labeled Class B. Class A is only returned when
    the packet itself carries certified as-built + witnessed + serial match
    (owner artefacts), never from sheet numbers alone.
    """
    packet = _packet(packet)
    kit = load_kit()
    reasons: list[str] = []
    invalid: list[str] = []
    remediation: list[str] = []
    docs = packet.documents
    bmeta = class_b_meta()

    if packet.asset_type in {"fire_life_safety", "fls", "ce_matrix"}:
        if packet.individual_tests_pass and packet.integrated_interface_test is not True:
            case = kit.invalidity_case("INV-CE-UNIT-NOT-INTEGRATED")
            return EvidenceResult(
                EvidenceClass.UNPROVABLE,
                Verdict.UNPROVABLE,
                ["§9.4.1 Individual tests passed; integrated interfaced response is unproven."],
                ["INV-CE-UNIT-NOT-INTEGRATED"],
                [case["required_remediation"]],
                bmeta,
            )
        if packet.integrated_interface_test is True:
            return EvidenceResult(
                EvidenceClass.A,
                Verdict.PASS,
                ["Integrated C&E chain witnessed (detection→dampers→pressurisation→lifts→door release→BMS)."],
            )

    if packet.asset_type == "fire_pump":
        if packet.test_line_to_tank:
            case = kit.invalidity_case("INV-FIRE-PUMP-TEST-TO-TANK")
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                ["Fire pump flow certificate is test-line-to-tank — invalid."],
                ["INV-FIRE-PUMP-TEST-TO-TANK"],
                [case["required_remediation"]],
                bmeta,
            )

        cover_hit = (
            packet.covers_clips_removed is False
            or bool(set(packet.photo_tags) & FIRE_PUMP_COVER_TAGS)
            or packet.nameplate_readable is False
        )
        if cover_hit:
            case = kit.invalidity_case("INV-FIRE-PUMP-COVERS-CLIPS")
            invalid.append("INV-FIRE-PUMP-COVERS-CLIPS")
            reasons.append("Covers/clips obscure the nameplate or were not removed.")
            remediation.append(case["required_remediation"])
            if not any(d in docs for d in ("witnessed_commissioning_sheet", "commissioning_report")):
                return EvidenceResult(
                    EvidenceClass.UNPROVABLE,
                    Verdict.UNPROVABLE,
                    reasons + ["No independent document remains after photo invalidity."],
                    invalid,
                    remediation,
                    bmeta,
                )
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                reasons + ["Photo is uncontrolled; remaining pack is insufficient for Class A/B."],
                invalid,
                remediation,
                bmeta,
            )

        serial_ok = (
            packet.serial_on_certificate
            and packet.serial_on_register
            and packet.serial_on_certificate == packet.serial_on_register
        )
        if packet.serial_on_certificate and packet.serial_on_register and not serial_ok:
            case = kit.invalidity_case("INV-FIRE-PUMP-SERIAL-MISMATCH")
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                ["Certificate serial does not match the asset register."],
                ["INV-FIRE-PUMP-SERIAL-MISMATCH"],
                [case["required_remediation"]],
                bmeta,
            )

        stale = packet.test_age_days is not None and packet.test_age_days > 365 and not packet.site_witness
        if stale:
            case = kit.invalidity_case("INV-FIRE-PUMP-STALE-TEST")
            return EvidenceResult(
                EvidenceClass.UNPROVABLE,
                Verdict.UNPROVABLE,
                ["Factory test is older than 12 months and was not site-witnessed."],
                ["INV-FIRE-PUMP-STALE-TEST"],
                [case["required_remediation"]],
                bmeta,
            )

        class_a_docs = {
            "as_built_drawing",
            "witnessed_commissioning_sheet",
            "nameplate_photo_unobstructed",
            "serial_on_asset_register",
        }
        if class_a_docs.issubset(set(docs)) and serial_ok and packet.nameplate_readable and not packet.test_line_to_tank:
            return EvidenceResult(
                EvidenceClass.A,
                Verdict.PASS,
                ["Certified as-built, witnessed test (not to tank), and serial-matched nameplate."],
            )
        if {"as_built_drawing", "commissioning_report"}.issubset(set(docs)):
            return EvidenceResult(
                EvidenceClass.B,
                Verdict.PASS,
                ["As-built plus commissioning report. Sheet-grade Class B — not CD primary evidence."],
                sheet_meta=bmeta,
            )
        if "om_manual_or_datasheet" in docs and len(docs) == 1:
            return EvidenceResult(
                EvidenceClass.C,
                Verdict.UNPROVABLE,
                ["Vendor literature only — cannot prove the installed asset."],
                sheet_meta=bmeta,
            )
        if docs:
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                ["Uncontrolled or incomplete fire-pump pack."],
                sheet_meta=bmeta,
            )
        return EvidenceResult(
            EvidenceClass.UNPROVABLE,
            Verdict.UNPROVABLE,
            ["No fire-pump evidence supplied."],
            sheet_meta=bmeta,
        )

    if packet.asset_type == "grms":
        if packet.grms_cert_matches_config is False:
            case = kit.invalidity_case("INV-GRMS-CERT-NE-CONFIG")
            return EvidenceResult(
                EvidenceClass.UNPROVABLE,
                Verdict.UNPROVABLE,
                ["GRMS certificate does not match the live room-by-room configuration."],
                ["INV-GRMS-CERT-NE-CONFIG"],
                [case["required_remediation"]],
                bmeta,
            )
        if packet.room_map_complete is False or packet.room_map_complete is None:
            case = kit.invalidity_case("INV-GRMS-ROOM-MAP")
            return EvidenceResult(
                EvidenceClass.UNPROVABLE,
                Verdict.UNPROVABLE,
                ["GRMS configuration is missing a complete room→controller map."],
                ["INV-GRMS-ROOM-MAP"],
                [case["required_remediation"]],
                bmeta,
            )
        if packet.grms_cert_matches_config is True and packet.room_map_complete is True:
            return EvidenceResult(EvidenceClass.A, Verdict.PASS, ["GRMS cert matches live room map."])
        return EvidenceResult(EvidenceClass.A, Verdict.PASS, ["GRMS room map is complete."])

    if packet.asset_type == "elevator" and packet.market == "uae" and packet.conformity_mark is False:
        case = kit.invalidity_case("INV-ELEVATOR-NO-TUV")
        return EvidenceResult(
            EvidenceClass.D,
            Verdict.FAIL,
            ["UAE elevator missing conformity mark."],
            ["INV-ELEVATOR-NO-TUV"],
            [case["required_remediation"]],
            bmeta,
        )

    if not docs:
        return EvidenceResult(
            EvidenceClass.UNPROVABLE,
            Verdict.UNPROVABLE,
            ["No evidence documents supplied."],
            sheet_meta=bmeta,
        )

    if {"as_built_drawing", "witnessed_commissioning_sheet", "serial_on_asset_register"}.issubset(set(docs)):
        return EvidenceResult(EvidenceClass.A, Verdict.PASS, ["Class A pack complete."])
    if {"as_built_drawing", "commissioning_report"}.issubset(set(docs)):
        return EvidenceResult(EvidenceClass.B, Verdict.PASS, ["Class B pack complete."], sheet_meta=bmeta)
    if "om_manual_or_datasheet" in docs:
        return EvidenceResult(EvidenceClass.C, Verdict.UNPROVABLE, ["Class C — literature only."], sheet_meta=bmeta)
    return EvidenceResult(EvidenceClass.D, Verdict.FAIL, ["Class D — uncontrolled evidence."], sheet_meta=bmeta)


def combine_verdicts(verdicts: Iterable[Verdict]) -> Verdict:
    """FAIL beats UNPROVABLE beats PASS (conservative three-valued fold)."""
    values = list(verdicts)
    if any(v is Verdict.FAIL for v in values):
        return Verdict.FAIL
    if any(v is Verdict.UNPROVABLE for v in values):
        return Verdict.UNPROVABLE
    if values and all(v is Verdict.PASS for v in values):
        return Verdict.PASS
    return Verdict.UNPROVABLE
