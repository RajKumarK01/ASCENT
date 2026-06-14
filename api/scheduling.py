"""Project week-relative study milestones onto concrete calendar dates.

Pure + deterministic given a start date. Uses the work-signal/heatmap window that the
engagement agent already produces (`preferred_day` from contribution history,
`preferred_slot`/`reminder_time` from work signals) so the schedule reflects the
learner's proven study rhythm. Output feeds both the UI (visible dates) and the
Microsoft Graph / .ics calendar export.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta

_DAY_INDEX = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}
_DEFAULT_DAY = "Saturday"          # weekend study when no historical signal
_SLOT_START = {"Morning": (9, 0), "Afternoon": (14, 0), "Evening": (18, 30)}


def _slot_start(window: dict) -> tuple[int, int]:
    rt = window.get("reminder_time")
    if isinstance(rt, str) and ":" in rt:
        try:
            h, m = rt.split(":")
            return int(h), int(m)
        except ValueError:
            pass
    return _SLOT_START.get(window.get("preferred_slot", "Morning"), (9, 0))


def _first_occurrence(start: date, weekday: int) -> date:
    """First date on/after `start` whose weekday matches."""
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def _iso(d: date, hour: int, minute: int) -> str:
    return datetime(d.year, d.month, d.day, hour, minute).strftime("%Y-%m-%dT%H:%M:%S")


def build_schedule(study_plan: dict, window: dict, start_date: date | None = None) -> dict:
    """Return {"events": [...], "milestones": [...annotated with dates...]}.

    Per milestone: one Study block on the preferred day/slot of that week, plus an
    Assessment checkpoint ~2 days later. All events are later marked Busy.
    """
    start_date = start_date or date.today()
    cert = study_plan.get("certification", "")
    milestones = study_plan.get("milestones", []) or []
    day_name = window.get("preferred_day") or _DEFAULT_DAY
    weekday = _DAY_INDEX.get(day_name, _DAY_INDEX[_DEFAULT_DAY])
    slot = window.get("preferred_slot", "Morning")
    hour, minute = _slot_start(window)
    anchor = _first_occurrence(start_date, weekday)  # week-1 study day

    events: list[dict] = []
    annotated: list[dict] = []
    for m in milestones:
        week = int(m.get("week", 1) or 1)
        skill = m.get("focus_skill", "")
        study_day = anchor + timedelta(weeks=week - 1)
        # Study block: 1–2h sized from the week's target hours.
        try:
            dur_h = min(max(float(m.get("target_hours", 1)), 1.0), 2.0)
        except (TypeError, ValueError):
            dur_h = 1.0
        s_start = _iso(study_day, hour, minute)
        s_end = (datetime.fromisoformat(s_start) + timedelta(hours=dur_h)).strftime("%Y-%m-%dT%H:%M:%S")
        events.append({
            "type": "study", "skill": skill, "date": study_day.isoformat(), "slot": slot,
            "title": f"Study: {skill} ({cert})" if cert else f"Study: {skill}",
            "body": m.get("objective", "") or f"Study block for {skill}.",
            "start_iso": s_start, "end_iso": s_end,
        })
        # Assessment checkpoint: ~2 days later, 45 min.
        a_day = study_day + timedelta(days=2)
        a_start = _iso(a_day, hour, minute)
        a_end = (datetime.fromisoformat(a_start) + timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%S")
        events.append({
            "type": "assessment", "skill": skill, "date": a_day.isoformat(), "slot": slot,
            "title": f"Assessment checkpoint: {skill}",
            "body": m.get("checkpoint", "") or f"Practice assessment on {skill}.",
            "start_iso": a_start, "end_iso": a_end,
        })
        annotated.append({**m, "study_date": study_day.isoformat(), "assessment_date": a_day.isoformat()})

    return {"events": events, "milestones": annotated}
