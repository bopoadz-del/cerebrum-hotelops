"""Evidence classes A/B/C/Unprovable and three-valued PASS/FAIL/UNPROVABLE."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from domain_kit.loader import load_kit


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


@dataclass
class EvidenceResult:
    evidence_class: EvidenceClass
    verdict: Verdict
    reasons: list[str]
    invalidity_ids: list[str] = field(default_factory=list)
    remediation: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_class": self.evidence_class.value,
            "verdict": self.verdict.value,
            "reasons": self.reasons,
            "invalidity_ids": self.invalidity_ids,
            "remediation": self.remediation,
        }


def _has(docs: Iterable[str], name: str) -> bool:
    return name in set(docs)


def classify_evidence(packet: EvidencePacket | dict[str, Any]) -> EvidenceResult:
    """Assign A/B/C/D/Unprovable and a three-valued verdict.

    Absence of evidence is UNPROVABLE, never a silent PASS.
    Fire-pump covers/clips that hide the nameplate invalidate Class A.
    """
    if isinstance(packet, dict):
        packet = EvidencePacket(**{k: v for k, v in packet.items() if k in EvidencePacket.__dataclass_fields__})

    kit = load_kit()
    reasons: list[str] = []
    invalid: list[str] = []
    remediation: list[str] = []
    docs = packet.documents

    if packet.asset_type == "fire_pump":
        cover_hit = bool(set(packet.photo_tags) & FIRE_PUMP_COVER_TAGS) or packet.nameplate_readable is False
        if cover_hit:
            invalid.append("INV-FIRE-PUMP-COVERS-CLIPS")
            reasons.append("Fire pump nameplate is obscured by covers/clips or is unreadable.")
            remediation.append(kit.invalidity_case("INV-FIRE-PUMP-COVERS-CLIPS")["required_remediation"])
            if not any(d in docs for d in ("witnessed_commissioning_sheet", "commissioning_report")):
                return EvidenceResult(
                    EvidenceClass.UNPROVABLE,
                    Verdict.UNPROVABLE,
                    reasons + ["No independent document remains after photo invalidity."],
                    invalid,
                    remediation,
                )
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                reasons + ["Photo is uncontrolled; remaining pack is insufficient for Class A/B."],
                invalid,
                remediation,
            )

        serial_ok = (
            packet.serial_on_certificate
            and packet.serial_on_register
            and packet.serial_on_certificate == packet.serial_on_register
        )
        if packet.serial_on_certificate and packet.serial_on_register and not serial_ok:
            invalid.append("INV-FIRE-PUMP-SERIAL-MISMATCH")
            reasons.append("Certificate serial does not match the asset register.")
            remediation.append(kit.invalidity_case("INV-FIRE-PUMP-SERIAL-MISMATCH")["required_remediation"])
            return EvidenceResult(EvidenceClass.D, Verdict.FAIL, reasons, invalid, remediation)

        stale = packet.test_age_days is not None and packet.test_age_days > 365 and not packet.site_witness
        if stale:
            invalid.append("INV-FIRE-PUMP-STALE-TEST")
            reasons.append("Factory test is older than 12 months and was not site-witnessed.")
            remediation.append(kit.invalidity_case("INV-FIRE-PUMP-STALE-TEST")["required_remediation"])
            return EvidenceResult(EvidenceClass.UNPROVABLE, Verdict.UNPROVABLE, reasons, invalid, remediation)

        class_a_docs = {
            "as_built_drawing",
            "witnessed_commissioning_sheet",
            "nameplate_photo_unobstructed",
            "serial_on_asset_register",
        }
        if class_a_docs.issubset(set(docs)) and serial_ok and packet.nameplate_readable:
            return EvidenceResult(
                EvidenceClass.A,
                Verdict.PASS,
                ["Certified as-built, witnessed test, and serial-matched nameplate."],
            )
        if {"as_built_drawing", "commissioning_report"}.issubset(set(docs)):
            return EvidenceResult(
                EvidenceClass.B,
                Verdict.PASS,
                ["As-built plus commissioning report. Not sufficient as Civil Defense primary evidence."],
            )
        if "om_manual_or_datasheet" in docs and len(docs) == 1:
            return EvidenceResult(
                EvidenceClass.C,
                Verdict.UNPROVABLE,
                ["Vendor literature only — cannot prove the installed asset."],
            )
        if docs:
            return EvidenceResult(
                EvidenceClass.D,
                Verdict.FAIL,
                ["Uncontrolled or incomplete fire-pump pack."],
            )
        return EvidenceResult(
            EvidenceClass.UNPROVABLE,
            Verdict.UNPROVABLE,
            ["No fire-pump evidence supplied."],
        )

    if packet.asset_type == "grms":
        if packet.room_map_complete is False or packet.room_map_complete is None:
            invalid.append("INV-GRMS-ROOM-MAP")
            reasons.append("GRMS configuration is missing a complete room→controller map.")
            remediation.append(kit.invalidity_case("INV-GRMS-ROOM-MAP")["required_remediation"])
            return EvidenceResult(EvidenceClass.UNPROVABLE, Verdict.UNPROVABLE, reasons, invalid, remediation)
        return EvidenceResult(EvidenceClass.A, Verdict.PASS, ["GRMS room map is complete."])

    if packet.asset_type == "elevator" and packet.market == "uae" and packet.conformity_mark is False:
        invalid.append("INV-ELEVATOR-NO-TUV")
        return EvidenceResult(
            EvidenceClass.D,
            Verdict.FAIL,
            ["UAE elevator missing conformity mark."],
            invalid,
            [kit.invalidity_case("INV-ELEVATOR-NO-TUV")["required_remediation"]],
        )

    if not docs:
        return EvidenceResult(
            EvidenceClass.UNPROVABLE,
            Verdict.UNPROVABLE,
            ["No evidence documents supplied."],
        )

    if {"as_built_drawing", "witnessed_commissioning_sheet", "serial_on_asset_register"}.issubset(set(docs)):
        return EvidenceResult(EvidenceClass.A, Verdict.PASS, ["Class A pack complete."])
    if {"as_built_drawing", "commissioning_report"}.issubset(set(docs)):
        return EvidenceResult(EvidenceClass.B, Verdict.PASS, ["Class B pack complete."])
    if "om_manual_or_datasheet" in docs:
        return EvidenceResult(EvidenceClass.C, Verdict.UNPROVABLE, ["Class C — literature only."])
    return EvidenceResult(EvidenceClass.D, Verdict.FAIL, ["Class D — uncontrolled evidence."])


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
