from __future__ import annotations
from fastapi import APIRouter, Depends, Query

from .deps import require_role
from .agent_client import run_manager_insights

router = APIRouter(prefix="/api/manager", tags=["manager"])

_manager = require_role("manager")


@router.get("/insights")
def get_insights(team: str | None = Query(default=None),
                 user: dict = Depends(_manager)):
    # Scope check: managers can only see their own team (or all_teams scope)
    allowed_scope = user["scope"]
    if allowed_scope != "all_teams" and team and team != allowed_scope:
        team = allowed_scope   # silently clamp to authorised scope
    elif not team and allowed_scope != "all_teams":
        team = allowed_scope
    return run_manager_insights(team if team != "all_teams" else None)
