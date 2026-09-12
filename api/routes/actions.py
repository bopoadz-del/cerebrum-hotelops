from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal, require_operator
from hotelops.actions import get_registry
from hotelops.db import get_sessionmaker, init_db
from hotelops.models import ActionRun

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("")
def list_actions(_: Principal = Depends(get_principal)):
    return {"actions": get_registry().list()}


@router.post("/{action_id}")
def run_action(action_id: str, body: dict, principal: Principal = Depends(require_operator)):
    return get_registry().run(action_id, body, actor=principal.actor, role=principal.role)


@router.get("/runs/recent")
def recent(_: Principal = Depends(get_principal)):
    init_db()
    session = get_sessionmaker()()
    rows = session.query(ActionRun).order_by(ActionRun.id.desc()).limit(50).all()
    session.close()
    return {
        "runs": [
            {
                "id": r.id,
                "action_id": r.action_id,
                "actor": r.actor,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
