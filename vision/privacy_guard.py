"""Refuse raw face retention and VIP matching without explicit opt-in."""

from __future__ import annotations

from typing import Any


class PrivacyRefuse(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "code": self.code, "message": self.message}


def guard_frame(meta: dict[str, Any]) -> dict[str, Any]:
    if meta.get("faces_raw_retained"):
        raise PrivacyRefuse(
            "raw_faces_forbidden",
            "Raw face frames/templates must not leave the edge node.",
        )
    if meta.get("use_case") == "vip" and not meta.get("opt_in_vip_ids"):
        raise PrivacyRefuse(
            "vip_opt_in_required",
            "VIP recognition requires an explicit opt-in guest id list.",
        )
    return {"status": "ok", "privacy": "edge_metadata_only"}
