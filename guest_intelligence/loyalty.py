"""Loyalty tier engine on fixture nights / LMS profiles."""

from __future__ import annotations

from typing import Any

from connectors.loyalty_lms import LoyaltyLMSConnector
from domain_kit.loader import load_kit


class LoyaltyEngine:
    def __init__(self) -> None:
        self.tiers = load_kit().loyalty_tiers["tiers"]

    def tier_for_nights(self, nights: int) -> dict[str, Any]:
        current = self.tiers[0]
        for row in self.tiers:
            if nights >= int(row["nights_from"]):
                current = row
        return current

    def evaluate(self, profile_id: str) -> dict[str, Any]:
        lms = LoyaltyLMSConnector()
        lms.connect()
        raw = lms.fetch("profiles")
        rec = next((r for r in raw["records"] if r["profile_id"] == profile_id), None)
        if rec is None:
            return {"status": "UNPROVABLE", "profile_id": profile_id, "reason": "profile not in LMS fixtures"}
        computed = self.tier_for_nights(int(rec["nights"]))
        return {
            "status": "ok",
            "profile_id": profile_id,
            "market": rec.get("market"),
            "nights": rec["nights"],
            "points": rec["points"],
            "stated_tier": rec["tier"],
            "computed_tier": computed["id"],
            "aligned": rec["tier"] == computed["id"],
            "benefits": computed["benefits"],
            "earn_rate": computed["points_earn"],
        }
