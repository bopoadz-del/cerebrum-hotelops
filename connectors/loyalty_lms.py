"""Loyalty LMS — fixture-driven profiles, tiers, points."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector
from hotelops.event_bus import HotelEvent


class LoyaltyLMSConnector(BaseConnector):
    name = "loyalty_lms"
    source = "loyalty_lms"
    live_env_keys = ("loyalty_lms_base_url", "loyalty_lms_api_key")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.loyalty_lms_base_url.rstrip('/')}/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.settings.loyalty_lms_api_key}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        events = []
        for row in records:
            events.append(
                HotelEvent(
                    topic="guest.loyalty.profile",
                    surface="guest",
                    source=self.source,
                    payload={
                        "profile_id": row.get("profile_id") or row.get("id"),
                        "tier": row.get("tier"),
                        "nights": row.get("nights"),
                        "points": row.get("points"),
                        "market": row.get("market", "uae"),
                    },
                )
            )
        return events
