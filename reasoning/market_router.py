"""Route work to UAE or generic markets only. KSA is refused."""

from __future__ import annotations

from typing import Any

from domain_kit.loader import load_kit
from reasoning.guard import GuardError, guard_request


class MarketRouter:
    """UAE + generic only. No KSA pack or branch."""

    UAE = {"uae", "dubai", "abu_dhabi", "abudhabi", "sharjah", "ajman"}
    GENERIC = {"generic"}

    def resolve_market(self, market: str) -> str:
        code = (market or "").lower().strip()
        guard_request(market=code)
        if code in self.UAE:
            return "uae"
        if code in self.GENERIC:
            return "generic"
        raise GuardError("market_unsupported", f"Market {market!r} is not UAE or generic.")

    def licensing_pack(self, market: str) -> dict[str, Any]:
        code = self.resolve_market(market)
        kit = load_kit()
        uae = getattr(kit, "licensing_uae", None) or {}
        gen = getattr(kit, "licensing_generic", None) or {}
        if code == "uae":
            return {
                "market": "uae",
                "licenses": (uae.get("licenses") if isinstance(uae, dict) else uae) or [],
                "prerequisites": (uae.get("prerequisite_map") if isinstance(uae, dict) else {}) or {},
            }
        return {
            "market": "generic",
            "licenses": (gen.get("licenses") if isinstance(gen, dict) else gen) or [],
            "prerequisites": (gen.get("prerequisite_map") if isinstance(gen, dict) else {}) or {},
        }
