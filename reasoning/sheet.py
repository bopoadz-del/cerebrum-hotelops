"""Domain Encoding Sheet (Sep 2026) — Class B expert recall, unverified."""

from __future__ import annotations

from typing import Any

SHEET_ID = "domain_encoding_sheet_sep2026"
EVIDENCE_CLASS = "B"
CAVEAT = (
    "UNVERIFIED Class B (expert recall from Domain Encoding Sheet, Sep 2026). "
    "Do not treat sheet numbers or timings as Class A. Promote only when the "
    "owner uploads brand standards, manning, OS&E matrices, licence trackers, or PPM records."
)


def class_b_meta(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "evidence_class": EVIDENCE_CLASS,
        "source": SHEET_ID,
        "document_status": "UNVERIFIED",
        "caveat": CAVEAT,
    }
    if extra:
        payload.update(extra)
    return payload
