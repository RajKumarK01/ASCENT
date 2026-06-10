from __future__ import annotations
import re
from fastapi import APIRouter, Depends, Query

from .deps import current_user, require_role
from .models import RegenerateRequest, ChatRequest
from .agent_client import run_for_learner, run_for_learner_chat

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
    """Free-text chat: Orchestrator classifies intent, plans route, dispatches only needed agents."""
    params = _parse_intent(body.message)
    result = run_for_learner_chat(user["scope"], query=body.message, weeks=params["weeks"])

    intent = result.get("intent", "full")
    asmt   = result.get("assessment") or {}
    plan   = result.get("study_plan") or {}
    cur    = result.get("curator") or {}
    eng    = result.get("engagement") or {}
    r      = asmt.get("readiness") or {}
    passed = result.get("passed")
    loops  = result.get("loops", 0)

    # Build reply based on which agents actually ran
    if intent == "assessment":
        qs = asmt.get("questions", [])
        if qs:
            reply = (
                f"Here are {len(qs)} practice question(s) for your "
                f"{asmt.get('certification', 'certification')} grounded in the knowledge base. "
                f"All questions are cited." if asmt.get("all_questions_cited") else
                f"Here are {len(qs)} practice question(s) generated for you."
            )
        else:
            reply = "No grounded questions could be generated — the knowledge base returned no content for your skills."

    elif intent == "readiness":
        if r:
            if passed:
                reply = (f"You're READY! Practice score and study hours both meet the threshold. "
                         f"Next certification: {result.get('next_step') or 'none'}.")
            else:
                reply = (f"Not quite ready yet. "
                         f"{'Score gap: +' + str(r['score_gap']) + '% needed. ' if r.get('score_gap') else ''}"
                         f"{'Hours gap: ' + str(r['hours_gap']) + 'h more study needed.' if r.get('hours_gap') else ''}")
        else:
            reply = "Could not compute readiness — no assessment data available."

    elif intent == "study_plan":
        if plan:
            reply = (f"Here's your study plan for {plan.get('certification')}: "
                     f"{plan.get('total_recommended_hours')}h over {plan.get('weeks')} weeks "
                     f"({plan.get('hours_per_week')}h/week). "
                     f"Milestones are sequenced with skill gaps first.")
        else:
            reply = "Could not generate a study plan."

    elif intent == "engagement":
        window = eng.get("window") or {}
        reply  = (f"Based on your work rhythm: {window.get('cadence', 'default cadence')}. "
                  f"{eng.get('reminder_policy', '')} "
                  f"{'High meeting load detected — condensed sessions recommended.' if window.get('capacity_constrained') else ''}")

    elif intent == "curator":
        reply = (f"For {cur.get('certification')}, focus on: {', '.join(cur.get('skills', []))}. "
                 f"Recommended study: {cur.get('recommended_hours')}h. "
                 f"Content grounded in {len(cur.get('citations', []))} source(s).")

    else:  # full pipeline
        if passed:
            reply = (f"Full plan complete. You're on track for exam readiness in "
                     f"{plan.get('weeks')} weeks ({plan.get('hours_per_week')}h/week). "
                     f"{'Next: ' + result['next_step'] + '.' if result.get('next_step') else ''}")
        else:
            reply = (f"Full plan complete. You need {r.get('hours_gap', 0)}h more study and "
                     f"+{r.get('score_gap', 0)}% on practice scores. "
                     f"Plan extended to {plan.get('weeks')} weeks.")
            if loops:
                reply += f" Reflection loop ran {loops} time(s)."

    return {
        "message": body.message,
        "reply":   reply,
        "result":  result,
        "intent":  {"intent": intent, "route": result.get("route", []), "weeks": params["weeks"]},
    }
