"""JWT auth: login, token issue/verify. Uses bcrypt directly (passlib incompatible with Python 3.14)."""
from __future__ import annotations
import json, os, secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import lru_cache

import bcrypt
import jwt
from fastapi import HTTPException, status

SECRET_KEY = os.environ.get("ASCENT_JWT_SECRET") or secrets.token_hex(32)
ALGORITHM  = "HS256"
EXPIRE_MIN = 60 * 8   # 8 hours — convenient for a demo day


@lru_cache(maxsize=1)
def _load_users() -> list[dict]:
    path = Path(__file__).parent.parent / "data" / "demo_users.json"
    return json.loads(path.read_text(encoding="utf-8"))


def authenticate(email: str, password: str) -> dict:
    users = _load_users()
    user = next((u for u in users if u["email"].lower() == email.lower()), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def create_token(user: dict) -> str:
    payload = {
        "sub":   user["email"],
        "role":  user["role"],
        "scope": user["scope"],
        "name":  user["name"],
        "exp":   datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
