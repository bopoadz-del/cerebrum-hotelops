"""Operator / reviewer token auth."""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hotelops.settings import AuthTokensNotConfigured, get_settings, require_auth_tokens

_bearer = HTTPBearer(auto_error=False)

ANONYMOUS_ACTOR = "anonymous"
ANONYMOUS_ROLE = "unknown"


@dataclass(frozen=True)
class Principal:
    actor: str
    role: str


ANONYMOUS = Principal(actor=ANONYMOUS_ACTOR, role=ANONYMOUS_ROLE)


def _token_eq(provided: str, expected: str) -> bool:
    if not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def principal_from_token(token: str | None) -> Principal | None:
    """Resolve a bearer token to a Principal. None if missing, unknown, or tokens unset."""
    settings = get_settings()
    if not settings.auth_tokens_configured() or not token:
        return None
    token = token.strip()
    if _token_eq(token, settings.operator_token.strip()):
        return Principal("operator", "operator")
    if _token_eq(token, settings.reviewer_token.strip()):
        return Principal("reviewer", "reviewer")
    return None


def principal_from_authorization(authorization: str | None) -> Principal:
    """Same resolution as HTTPBearer auth. Never reads x-actor / x-role headers."""
    if not authorization:
        return ANONYMOUS
    scheme, sep, token = authorization.partition(" ")
    if not sep or scheme.lower() != "bearer":
        return ANONYMOUS
    return principal_from_token(token.strip()) or ANONYMOUS


def get_principal(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    try:
        require_auth_tokens()
    except AuthTokensNotConfigured:
        raise HTTPException(status_code=503, detail="auth tokens are not configured") from None
    if creds is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    principal = principal_from_token(creds.credentials)
    if principal is None:
        raise HTTPException(status_code=403, detail="unknown token")
    return principal


def require_operator(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.role != "operator":
        raise HTTPException(status_code=403, detail="operator role required")
    return principal
