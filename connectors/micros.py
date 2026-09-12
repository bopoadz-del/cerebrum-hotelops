"""Oracle Micros Simphony POS — fixture-driven."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector
from hotelops.event_bus import HotelEvent


class MicrosConnector(BaseConnector):
    name = "micros"
    source = "micros_simphony"
    live_env_keys = ("micros_base_url", "micros_api_key")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.micros_base_url.rstrip('/')}/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.micros_api_key}"}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        events = []
        for row in records:
            events.append(
                HotelEvent(
                    topic="guest.folio.charge" if resource == "checks" else f"connector.pos.{resource}",
                    surface="guest" if resource == "checks" else "ops",
                    source=self.source,
                    payload={
                        "check_id": row.get("check_id") or row.get("id"),
                        "outlet": row.get("outlet"),
                        "amount": row.get("amount"),
                        "room": row.get("room"),
                        "covers": row.get("covers"),
                        "closed": row.get("closed", False),
                    },
                )
            )
        return events
