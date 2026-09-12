"""Booking funnel placement from Opera-normalised events + fixture reservations."""

from __future__ import annotations

from typing import Any

from connectors.opera import OperaConnector
from domain_kit.loader import load_kit
from guest_intelligence.crm import GuestCRM


class BookingIntelligence:
    def __init__(self) -> None:
        self.funnel = {s["id"]: s for s in load_kit().booking_funnel["stages"]}
        self.crm = GuestCRM()

    def place(self, guest_id: str) -> dict[str, Any]:
        opera = OperaConnector()
        opera.connect()
        reservations = opera.fetch("reservations")["records"]
        mine = [r for r in reservations if r.get("guest_id") == guest_id]
        if not mine:
            stage = "awareness"
        else:
            statuses = {r["status"] for r in mine}
            if "in_house" in statuses:
                stage = "stay"
            elif "checked_out" in statuses:
                stage = "depart"
            elif "reserved" in statuses:
                stage = "book"
            else:
                stage = "consider"
        profile = self.crm.profile(guest_id)
        return {
            "guest_id": guest_id,
            "market": profile["market"],
            "stage": stage,
            "stage_order": self.funnel[stage]["order"],
            "reservations": mine,
        }
