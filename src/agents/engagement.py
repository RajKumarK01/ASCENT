"""Engagement Agent — keeps the learner on track using Work IQ context.

Grounding: Work IQ signals (meeting load, focus hours, preferred slot, historical
day pattern, and synthetic calendar signals). Outputs supportive, privacy-
conscious reminder guidance.

The deterministic Work IQ window (work_iq.study_window) provides the structural
defaults (slot, reminder time, capacity flag). In foundry mode the agent reasons
over the full signal to choose the cadence, reminder policy, and guidance — and
explains why. On any LLM failure it returns the deterministic window.
"""
from __future__ import annotations

from ..iq import work_iq
from ..config import MODE

SYSTEM_PROMPT = """You are the Engagement Agent.
You are given a learner's synthetic work-context signal (meeting load, focus
hours, preferred learning slot, historical active day, and calendar pressure).
Reason about WHEN and HOW OFTEN this person should study so learning fits around
their work without adding stress. Return JSON only:
{
  "cadence": "<e.g. '3 short 30-min sessions/week'>",
  "reminder_policy": "<one line: when/whether to nudge, tied to their rhythm>",
  "guidance": "<one supportive sentence of scheduling advice>",
  "rationale": "<one line: which signals drove this and why>"
}
Avoid disrupting peak work periods. Never expose another person's schedule."""


def run(learner_id: str) -> dict:
    signal = work_iq.signal_for(learner_id)
    if not signal:
        return {"agent": "engagement", "learner_id": learner_id,
                "window": None, "note": "No work signal available; using default cadence."}

    window = work_iq.study_window(signal, learner_id=learner_id)  # deterministic base

    if MODE == "foundry":
        reasoned = _reason_window(signal, window)
        if reasoned:
            # Keep structural keys (slot, reminder_time, capacity flag, preferred_day);
            # let the agent's reasoning drive cadence / policy / guidance.
            window = {**window, **reasoned}

    return {
        "agent": "engagement",
        "learner_id": learner_id,
        "window": window,
        "reminder_policy": window.get("reminder_policy"),
    }


def _reason_window(signal: dict, base: dict) -> dict | None:
    """FOUNDRY: reason over the work signal. Returns keys to merge, or None."""
    from ._reason import reason_or_delegate

    user = (
        "Work-context signal (synthetic):\n"
        f"- meeting_hours_per_week: {signal.get('meeting_hours_per_week')}\n"
        f"- focus_hours_per_week: {signal.get('focus_hours_per_week')}\n"
        f"- preferred_learning_slot: {signal.get('preferred_learning_slot')}\n"
        f"- busy_days: {signal.get('busy_days')}\n"
        f"- upcoming_deadline: {signal.get('upcoming_deadline')}\n"
        f"- recent_meeting_trend: {signal.get('recent_meeting_trend')}\n"
        f"- historical active day: {base.get('preferred_day', 'unknown')}\n"
        f"- capacity_constrained (>20 mtg hrs): {base.get('capacity_constrained')}\n\n"
        "Choose a realistic cadence, reminder policy, and one line of guidance."
    )
    data = reason_or_delegate("ascent-engagement", SYSTEM_PROMPT, user, max_tokens=300)
    if not data:
        return None
    out = {}
    for k in ("cadence", "reminder_policy", "guidance", "rationale"):
        if data.get(k):
            out[k] = str(data[k])[:240]
    if data.get("_via"):
        out["_via"] = data["_via"]
    return out or None
