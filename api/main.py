"""ASCENT FastAPI backend-for-frontend."""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import authenticate, create_token
from .models import LoginRequest, TokenResponse
from .routes_employee import router as emp_router
from .routes_manager import router as mgr_router
from .agent_client import AGENT_TARGET

app = FastAPI(title="ASCENT BFF", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emp_router)
app.include_router(mgr_router)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = authenticate(body.email, body.password)
    token = create_token(user)
    return TokenResponse(
        access_token=token,
        role=user["role"],
        scope=user["scope"],
        email=user["email"],
        name=user["name"],
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": AGENT_TARGET.upper()}
