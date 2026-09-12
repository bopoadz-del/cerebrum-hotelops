from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import Principal, get_principal
from hotelops.db import get_sessionmaker, init_db
from hotelops.models import Document
from hotelops.retrieval import retrieve

router = APIRouter(prefix="/documents", tags=["documents"])


class DocIn(BaseModel):
    title: str
    doc_type: str
    body: str
    surface: str = "ops"
    market: str = "uae"


@router.get("")
def list_docs(_: Principal = Depends(get_principal)):
    init_db()
    session = get_sessionmaker()()
    rows = session.query(Document).order_by(Document.id.desc()).all()
    session.close()
    return {
        "documents": [
            {"id": d.id, "title": d.title, "doc_type": d.doc_type, "surface": d.surface, "market": d.market}
            for d in rows
        ]
    }


@router.post("")
def create_doc(doc: DocIn, _: Principal = Depends(get_principal)):
    init_db()
    session = get_sessionmaker()()
    row = Document(**doc.model_dump())
    session.add(row)
    session.commit()
    payload = {"id": row.id, "title": row.title}
    session.close()
    return payload


@router.get("/search")
def search(q: str, _: Principal = Depends(get_principal)):
    return {"hits": retrieve(q)}
