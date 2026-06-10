"""FastAPI dependencies: current_user, require_role."""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import decode_token

_bearer = HTTPBearer()


def current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    return decode_token(creds.credentials)


def require_role(role: str):
    def _check(user: dict = Depends(current_user)) -> dict:
        if user["role"] != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Requires role: {role}")
        return user
    return _check
