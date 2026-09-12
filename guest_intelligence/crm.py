"""CRM over synthetic UAE + generic guest fixtures and the event bus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from domain_kit.loader import load_kit
from hotelops.event_bus import HotelEvent, get_bus
from hotelops.settings import get_settings


class GuestCRM:
    def __init__(self) -> None:
        self.taxonomy = {row["type"]: row for row in load_kit().crm_event_taxonomy["taxonomy"]}
        path = Path(get_settings().fixture_root) / "guests" / "profiles.json"
        self.profiles = {p["guest_id"]: p for p in json.loads(path.read_text())["records"]}

    def profile(self, guest_id: str) -> dict[str, Any]:
        if guest_id not in self.profiles:
            raise KeyError(guest_id)
        return self.profiles[guest_id]

    def list_profiles(self, market: str | None = None) -> list[dict[str, Any]]:
        rows = list(self.profiles.values())
        if market:
            rows = [p for p in rows if p["market"] == market]
        return rows

    def ingest(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        spec = self.taxonomy.get(event_type)
        if spec is None:
            raise ValueError(f"Unknown CRM event type {event_type}")
        missing = [field for field in spec["required"] if field not in payload]
        if missing:
            return {"status": "UNPROVABLE", "missing": missing, "event_type": event_type}
        event = get_bus().publish(
            HotelEvent(
                topic=f"guest.crm.{event_type}",
                surface=spec["surface"] if spec["surface"] != "both" else "both",
                source="guest_crm",
                payload={"event_type": event_type, **payload},
            )
        )
        return {"status": "ok", "event": event.as_dict()}
