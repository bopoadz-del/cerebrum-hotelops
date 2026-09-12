from fastapi import APIRouter, Depends

from api.auth import Principal, get_principal
from hotelops.db import get_sessionmaker, init_db
from hotelops.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(limit: int = 100, _: Principal = Depends(get_principal)):
    init_db()
    session = get_sessionmaker()()
    rows = session.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all()
    session.close()
    return {
        "events": [
            {
                "id": e.id,
                "actor": e.actor,
                "role": e.role,
                "method": e.method,
                "path": e.path,
                "status_code": e.status_code,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ]
    }
