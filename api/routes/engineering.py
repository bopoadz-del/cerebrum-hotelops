from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal, require_operator
from connectors.maximo import MaximoConnector
from domain_kit.loader import load_kit
from hotelops.actions import get_registry

router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.get("/classes")
def classes(_: Principal = Depends(get_principal)):
    return load_kit().engineering_classes


@router.get("/invalidity")
def invalidity(_: Principal = Depends(get_principal)):
    return load_kit().evidence_invalidity_cases


@router.post("/classify")
def classify(body: dict, principal: Principal = Depends(require_operator)):
    return get_registry().run("engineering.classify", body, actor=principal.actor, role=principal.role)


@router.post("/assets/ingest")
def ingest_assets(principal: Principal = Depends(require_operator)):
    return MaximoConnector().ingest("assets")
