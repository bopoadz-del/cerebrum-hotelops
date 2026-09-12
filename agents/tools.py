"""Tools the graphs call — real engines, not stubs."""

from __future__ import annotations

from typing import Any

from connectors import get_connector
from guest_intelligence.booking_intelligence import BookingIntelligence
from guest_intelligence.loyalty import LoyaltyEngine
from guest_intelligence.personalization import Personalizer
from hotelops.event_bus import HotelEvent, get_bus
from hotelops.retrieval import retrieve
from reasoning.cascade_engine import CascadeEngine
from reasoning.evidence import classify_evidence
from reasoning.guard import GuardError, guard_request
from reasoning.licensing import LicensingEngine
from reasoning.ppm_resolver import PPMRefuse, PPMResolver


def tool_cascade(slips: dict[str, int] | None = None) -> dict[str, Any]:
    return CascadeEngine().simulate(slips or {}).as_dict()


def tool_evidence(packet: dict[str, Any]) -> dict[str, Any]:
    return classify_evidence(packet).as_dict()


def tool_licensing(market: str, satisfied: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        guard_request(market=market)
    except GuardError as exc:
        return exc.as_dict()
    return LicensingEngine().evaluate(market, satisfied)


def tool_ppm(market: str, asset_type: str, operator_sop: str | None, task_id: str | None = None) -> dict[str, Any]:
    try:
        return PPMResolver().resolve(
            market=market, asset_type=asset_type, operator_sop=operator_sop, task_id=task_id
        ).as_dict()
    except (PPMRefuse, GuardError) as exc:
        return exc.as_dict()


def tool_ingest(connector: str, resource: str) -> dict[str, Any]:
    return get_connector(connector).ingest(resource)


def tool_guest(guest_id: str) -> dict[str, Any]:
    return {
        "booking": BookingIntelligence().place(guest_id),
        "loyalty": LoyaltyEngine().evaluate(guest_id),
        "personalization": Personalizer().recommend(guest_id),
    }


def tool_retrieve(query: str) -> list[dict[str, Any]]:
    return retrieve(query)


def emit_agent(topic: str, surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    return get_bus().publish(HotelEvent(topic=topic, surface=surface, source="agent", payload=payload)).as_dict()
