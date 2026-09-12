"""Operator / reviewer token auth."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hotelops.settings import get_settings

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    actor: str
    role: str


def get_principal(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    settings = get_settings()
    if creds is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = creds.credentials
    if token == settings.operator_token:
        return Principal("operator", "operator")
    if token == settings.reviewer_token:
        return Principal("reviewer", "reviewer")
    raise HTTPException(status_code=403, detail="unknown token")


def require_operator(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.role != "operator":
        raise HTTPException(status_code=403, detail="operator role required")
    return principal
