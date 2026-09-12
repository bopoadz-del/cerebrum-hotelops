"""Guest Room Management System — room map is required evidence."""

from __future__ import annotations

from typing import Any

from connectors.base import BaseConnector
from hotelops.event_bus import HotelEvent
from reasoning.evidence import classify_evidence


class GRMSConnector(BaseConnector):
    name = "grms"
    source = "grms"
    live_env_keys = ("grms_base_url", "grms_api_key")

    def live_url(self, resource: str) -> str:
        return f"{self.settings.grms_base_url.rstrip('/')}/{resource}"

    def live_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.settings.grms_api_key}

    def normalise(self, resource: str, raw: Any) -> list[HotelEvent]:
        if resource == "config":
            rooms = raw.get("rooms") or []
            mapped = sum(1 for r in rooms if r.get("controller_id"))
            complete = bool(rooms) and mapped == len(rooms)
            judged = classify_evidence(
                {
                    "asset_type": "grms",
                    "room_map_complete": complete,
                    "documents": ["room_map"] if complete else [],
                }
            )
            return [
                HotelEvent(
                    topic="ops.engineering.grms_config",
                    surface="ops",
                    source=self.source,
                    payload={
                        "rooms": len(rooms),
                        "mapped": mapped,
                        "room_map_complete": complete,
                        **judged.as_dict(),
                    },
                    evidence_class=judged.evidence_class.value,
                    verdict=judged.verdict.value,
                )
            ]
        records = raw.get("records", raw if isinstance(raw, list) else [raw])
        return [
            HotelEvent(
                topic="ops.grms.room",
                surface="ops",
                source=self.source,
                payload={"room": row.get("room"), "dnd": row.get("dnd"), "occupied": row.get("occupied")},
            )
            for row in records
        ]
