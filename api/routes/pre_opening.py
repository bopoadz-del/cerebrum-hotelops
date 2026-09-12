from fastapi import APIRouter, Depends

from agents.coordinator import run_agent
from api.auth import Principal, get_principal, require_operator
from domain_kit.loader import load_kit
from hotelops.actions import get_registry

router = APIRouter(prefix="/pre-opening", tags=["pre_opening"])


@router.get("/milestones")
def milestones(_: Principal = Depends(get_principal)):
    return load_kit().pre_opening_milestones


@router.get("/mitigations")
def mitigations(_: Principal = Depends(get_principal)):
    kit = load_kit()
    return {
        "library": kit.pre_opening_mitigations["library"],
        "registry": kit.pre_opening_registry,
        "milestone_table": kit.pre_opening_milestone_table,
        "ffe_ose": kit.pre_opening_ffe_ose,
        "structural_gaps": kit.structural_gaps,
    }


@router.post("/simulate")
def simulate(body: dict, principal: Principal = Depends(require_operator)):
    return get_registry().run("pre_opening.simulate", body, actor=principal.actor, role=principal.role)


@router.post("/agent")
def agent(body: dict, principal: Principal = Depends(require_operator)):
    return run_agent(body.get("intent", "pre-opening cascade"), body, body.get("market", "uae"))
