"""Oracle Opera PMS — fixture-driven connect/fetch/normalise/emit."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector
from hotelops.event_bus import HotelEvent


class OperaConnector(BaseConnector):
    name = "opera"
    source = "opera_pms"
    live_env_keys = ("opera_base_url", "opera_client_id", "opera_client_secret")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.opera_base_url.rstrip('/')}/v1/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"X-Client-Id": self.settings.opera_client_id, "X-Client-Secret": self.settings.opera_client_secret}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        events: list[HotelEvent] = []
        for row in records:
            if resource == "reservations":
                topic = "guest.booking.reservation"
                payload = {
                    "confirmation_id": row.get("confirmation_id") or row.get("id"),
                    "guest_id": row.get("guest_id"),
                    "arrival": row.get("arrival"),
                    "departure": row.get("departure"),
                    "room_type": row.get("room_type"),
                    "status": row.get("status"),
                    "rate_code": row.get("rate_code"),
                    "market": row.get("market", "uae"),
                }
                surface = "guest"
            elif resource == "in_house":
                topic = "ops.pms.in_house"
                payload = {
                    "room": row.get("room"),
                    "guest_id": row.get("guest_id"),
                    "status": row.get("status"),
                    "vip": row.get("vip", False),
                }
                surface = "ops"
            elif resource == "housekeeping":
                topic = "ops.pms.housekeeping"
                payload = {"room": row.get("room"), "hk_status": row.get("hk_status")}
                surface = "ops"
            else:
                topic = f"connector.pms.{resource}"
                payload = dict(row)
                surface = "both"
            events.append(HotelEvent(topic=topic, surface=surface, source=self.source, payload=payload))
        return events
