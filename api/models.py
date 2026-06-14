from __future__ import annotations
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    scope: str
    email: str
    name: str


class RegenerateRequest(BaseModel):
    weeks: int = 4


class ProfileUpdateRequest(BaseModel):
    path: str
    certification: str | None = None


class PathInterpretRequest(BaseModel):
    description: str


class AssessmentSubmitRequest(BaseModel):
    score_pct: int
    correct: int | None = None
    total: int | None = None


class ScheduleCalendarRequest(BaseModel):
    weeks: int = 4
