from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal, require_operator
from hotelops.actions import get_registry
from reasoning.guard import GuardError
from reasoning.licensing import LicensingEngine

router = APIRouter(prefix="/licensing", tags=["licensing"])


@router.get("/pack/{market}")
def pack(market: str, _: Principal = Depends(get_principal)):
    try:
        return LicensingEngine().evaluate(market, {})
    except GuardError as exc:
        return exc.as_dict()


@router.post("/evaluate")
def evaluate(body: dict, principal: Principal = Depends(require_operator)):
    return get_registry().run("licensing.evaluate", body, actor=principal.actor, role=principal.role)
