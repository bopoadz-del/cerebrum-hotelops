"""Guest-surface reporting across funnel, loyalty, and bus history."""

from __future__ import annotations

from collections import Counter
from typing import Any

from guest_intelligence.booking_intelligence import BookingIntelligence
from guest_intelligence.crm import GuestCRM
from guest_intelligence.loyalty import LoyaltyEngine
from hotelops.event_bus import get_bus


class GuestReporter:
    def snapshot(self) -> dict[str, Any]:
        crm = GuestCRM()
        booking = BookingIntelligence()
        loyalty = LoyaltyEngine()
        stages = Counter()
        markets = Counter()
        tiers = Counter()
        for profile in crm.list_profiles():
            markets[profile["market"]] += 1
            stages[booking.place(profile["guest_id"])["stage"]] += 1
            try:
                ev = loyalty.evaluate(profile["guest_id"])
                if ev.get("computed_tier"):
                    tiers[ev["computed_tier"]] += 1
            except Exception:
                continue
        return {
            "guests": len(crm.list_profiles()),
            "markets": dict(markets),
            "funnel": dict(stages),
            "tiers": dict(tiers),
            "bus_guest_events": len(get_bus().history(surface="guest")),
        }
