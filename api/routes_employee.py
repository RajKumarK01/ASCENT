from __future__ import annotations
import re
from fastapi import APIRouter, Depends, Query

from .deps import current_user, require_role
from .models import RegenerateRequest, ChatRequest
from .agent_client import run_for_learner

router = APIRouter(prefix="/api", tags=["employee"])

_employee = require_role("employee")

_WEEKS_RE  = re.compile(r'(\d+)[\s\-]*week', re.I)
_FOCUS_RE  = re.compile(r'focus\s+on\s+([A-Za-z/ ]{3,30})', re.I)


def _parse_intent(message: str, default_weeks: int = 4) -> dict:
    """Extract weeks and focus-skill hints from free-text."""
    weeks_match = _WEEKS_RE.search(message)
    weeks = int(weeks_match.group(1)) if weeks_match else default_weeks
    weeks = max(1, min(16, weeks))

    focus_match = _FOCUS_RE.search(message)
    focus_skill = focus_match.group(1).strip() if focus_match else None

    return {"weeks": weeks, "focus_skill": focus_skill}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"email": user["sub"], "name": user["name"],
            "role": user["role"], "scope": user["scope"]}


@router.get("/plan")
def get_plan(weeks: int = Query(default=4, ge=1, le=16),
             user: dict = Depends(_employee)):
    return run_for_learner(user["scope"], weeks=weeks)


@router.post("/plan/regenerate")
def regenerate_plan(body: RegenerateRequest, user: dict = Depends(_employee)):
    return run_for_learner(user["scope"], weeks=body.weeks)


@router.get("/assessment")
def get_assessment(user: dict = Depends(_employee)):
    result = run_for_learner(user["scope"])
    return result.get("assessment", {})


@router.post("/chat")
def chat(body: ChatRequest, user: dict = Depends(_employee)):
    """Free-text chat: interpret intent, run the orchestrator, return a structured reply."""
    intent = _parse_intent(body.message)
    result = run_for_learner(user["scope"], weeks=intent["weeks"])

    # Build a plain-language reply summarising the result
    plan   = result.get("study_plan", {})
    asmt   = result.get("assessment", {})
    r      = asmt.get("readiness", {})
    passed = result.get("passed", False)
    loops  = result.get("loops", 0)

    if "help" in body.message.lower() or "prepare" in body.message.lower() or not body.message.strip():
        reply = (
            f"I've reviewed {user['scope']}'s learning profile for "
            f"{result.get('curator', {}).get('certification', 'your certification')}. "
        )
    elif "ready" in body.message.lower() or "exam" in body.message.lower():
        reply = f"Readiness check for {user['scope']}: "
    elif intent["focus_skill"]:
        reply = f"I've built a plan focusing on {intent['focus_skill']}. "
    else:
        reply = "Here's an updated learning plan based on your request. "

    if passed:
        reply += (
            f"Good news — you're on track to be exam-ready in {plan.get('weeks')} weeks "
            f"({plan.get('hours_per_week')}h/week). "
        )
        if result.get("next_step"):
            reply += f"After this certification, consider {result['next_step']}."
    else:
        reply += (
            f"You need {r.get('hours_gap', 0)}h more study and "
            f"+{r.get('score_gap', 0)}% on practice scores. "
            f"I've extended your plan to {plan.get('weeks')} weeks to close the gap."
        )
        if loops:
            reply += f" The planner ran {loops} reflection loop(s) to find the best path."

    return {
        "message": body.message,
        "reply": reply,
        "result": result,
        "intent": intent,
    }
