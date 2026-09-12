from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal
from connectors import get_connector
from hotelops.actions import get_registry
from hotelops.event_bus import get_bus
from vision.edge import ingest as vision_ingest

router = APIRouter(prefix="/operational", tags=["operational"])


@router.post("/ppm")
def ppm(body: dict, principal: Principal = Depends(get_principal)):
    return get_registry().run("ppm.resolve", body, actor=principal.actor, role=principal.role)


@router.post("/connectors/{name}/ingest")
def ingest(name: str, body: dict, _: Principal = Depends(get_principal)):
    return get_connector(name).ingest(body.get("resource", "records") if name != "grms" else body.get("resource", "config"))


@router.get("/events")
def events(surface: str | None = None, _: Principal = Depends(get_principal)):
    return {"events": get_bus().history(surface=surface)}


@router.post("/vision/{name}")
def vision(name: str, _: Principal = Depends(get_principal)):
    return vision_ingest(name)
