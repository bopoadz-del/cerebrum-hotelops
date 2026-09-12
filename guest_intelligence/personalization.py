"""Personalization against the guest_journey schema. Missing opt-in is UNPROVABLE."""

from __future__ import annotations

from typing import Any

from domain_kit.loader import load_kit
from guest_intelligence.crm import GuestCRM


class Personalizer:
    def __init__(self) -> None:
        self.schema = load_kit().personalization_schema
        self.crm = GuestCRM()

    def recommend(self, guest_id: str) -> dict[str, Any]:
        profile = self.crm.profile(guest_id)
        attrs = self.schema["attributes"]
        applied: dict[str, Any] = {}
        unprovable: list[str] = []
        for key in attrs:
            if key in profile:
                applied[key] = profile[key]
            else:
                unprovable.append(key)
        if not profile.get("marketing_opt_in"):
            applied.pop("newspaper", None)
        return {
            "guest_id": guest_id,
            "market": profile["market"],
            "applied": applied,
            "unprovable": unprovable,
            "marketing_allowed": bool(profile.get("marketing_opt_in")),
        }
