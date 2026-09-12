from fastapi import APIRouter, Depends

from agents.coordinator import run_agent
from api.auth import Principal, get_principal, require_operator
from connectors.opera import OperaConnector
from guest_intelligence.booking_intelligence import BookingIntelligence
from guest_intelligence.crm import GuestCRM
from guest_intelligence.loyalty import LoyaltyEngine
from guest_intelligence.personalization import Personalizer
from guest_intelligence.reporting import GuestReporter

router = APIRouter(prefix="/guest", tags=["guest"])


@router.get("/profiles")
def profiles(market: str | None = None, _: Principal = Depends(get_principal)):
    return {"profiles": GuestCRM().list_profiles(market)}


@router.get("/profiles/{guest_id}")
def profile(guest_id: str, _: Principal = Depends(get_principal)):
    return {
        "profile": GuestCRM().profile(guest_id),
        "booking": BookingIntelligence().place(guest_id),
        "loyalty": LoyaltyEngine().evaluate(guest_id),
        "personalization": Personalizer().recommend(guest_id),
    }


@router.post("/crm")
def crm(body: dict, _: Principal = Depends(require_operator)):
    return GuestCRM().ingest(body["event_type"], body.get("payload") or {})


@router.get("/report")
def report(_: Principal = Depends(get_principal)):
    return GuestReporter().snapshot()


@router.post("/reservations/ingest")
def ingest_reservations(_: Principal = Depends(require_operator)):
    return OperaConnector().ingest("reservations")


@router.post("/agent")
def agent(body: dict, _: Principal = Depends(require_operator)):
    return run_agent(body.get("intent", "guest loyalty"), body, body.get("market", "uae"))
