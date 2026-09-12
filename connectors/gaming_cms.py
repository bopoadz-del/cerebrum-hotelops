"""Optional gaming CMS — complete fixture-driven module (no live casino dependency)."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector
from hotelops.event_bus import HotelEvent


class GamingCMSConnector(BaseConnector):
    name = "gaming_cms"
    source = "gaming_cms"
    live_env_keys = ("gaming_cms_base_url", "gaming_cms_api_key")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.gaming_cms_base_url.rstrip('/')}/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.settings.gaming_cms_api_key}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        return [
            HotelEvent(
                topic="guest.gaming.comp",
                surface="guest",
                source=self.source,
                payload={
                    "player_id": row.get("player_id") or row.get("id"),
                    "comp_balance": row.get("comp_balance", 0),
                    "host": row.get("host"),
                    "linked_reservation": row.get("linked_reservation"),
                },
            )
            for row in records
        ]
