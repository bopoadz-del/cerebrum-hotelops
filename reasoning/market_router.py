"""Route work to UAE or generic. Every other market — including KSA — is refused."""

from __future__ import annotations

from typing import Any

from domain_kit.loader import load_kit
from reasoning.guard import GuardError, guard_request
from reasoning.sheet import class_b_meta


class MarketRouter:
    DEMO = {"uae", "generic"}

    def normalize(self, market: str | None, *, demo_only: bool = False) -> str:
        code = (market or "generic").lower().strip()
        guard_request(market=code, demo_only=demo_only)
        if code in {"dubai", "abu_dhabi", "abudhabi", "sharjah", "ajman", "uae"}:
            return "uae"
        if code == "generic":
            return "generic"
        raise GuardError("market_unsupported", f"Market {market!r} is not UAE or generic.")

    def licensing_pack(self, market: str | None) -> dict[str, Any]:
        kit = load_kit()
        code = self.normalize(market)
        if code == "uae":
            return {
                "market": "uae",
                "licenses": kit.licensing_uae["licenses"],
                "prerequisites": kit.licensing_prereq["maps"],
                **class_b_meta(),
            }
        return {
            "market": "generic",
            "licenses": kit.licensing_generic["licenses"],
            "prerequisites": kit.licensing_generic.get("prerequisite_map") or {},
            **class_b_meta(),
        }

    def ppm_pack(self, market: str | None) -> dict[str, Any]:
        code = self.normalize(market)
        kit = load_kit()
        if code == "uae":
            return kit.ppm_uae_statutory
        return {
            "market": code,
            "layer": "statutory_floor",
            "authoritative_frequencies": False,
            "tasks": [],
            "duties": [
                {"id": "STAT-FIRE", "asset_types": ["fire_pump", "fire_alarm"], "authority": "fire_service"},
                {"id": "STAT-LIFT", "asset_types": ["elevator"], "authority": "lift_authority"},
                {"id": "STAT-PRESSURE", "asset_types": ["pressure_vessel"], "authority": "pressure_vessel"},
                {"id": "STAT-WATER", "asset_types": ["domestic_water"], "authority": "water_hygiene"},
            ],
            "note": "Statutory floor only. Operator SOP is mandatory. Frequencies are never estimated.",
            **class_b_meta(),
        }
