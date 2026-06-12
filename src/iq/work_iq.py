"""Work IQ - work-context layer.

Interprets synthetic work signals (meeting load, focus hours, preferred slot)
into supportive scheduling guidance. In a real deployment these signals come
from Microsoft 365 / Work IQ; here they come from data/work_signals.json.
Keep outputs supportive and privacy-conscious. See BUILD_STEPS/06.
"""
from __future__ import annotations
import json
from pathlib import Path

from ..config import work_signals

_CONTRIBUTIONS_FILE = Path(__file__).parent.parent.parent / "data" / "study_contributions.json"
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def signal_for(employee_or_learner_id: str) -> dict | None:
    for s in work_signals():
        if employee_or_learner_id in (s.get("employee_id"), s.get("learner_id")):
            return s
    return None


def _dow_pattern(learner_id: str) -> dict[int, int]:
    """Return day-of-week → session count from historical contributions (0=Mon … 6=Sun)."""
    try:
        if not _CONTRIBUTIONS_FILE.exists():
            return {}
        with open(_CONTRIBUTIONS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        dates = raw.get(learner_id, {}).get("dates", {})
        from datetime import date as _date
        dow: dict[int, int] = {}
        for date_str, count in dates.items():
            if (count or 0) > 0:
                try:
                    d = _date.fromisoformat(date_str)
                    dow[d.weekday()] = dow.get(d.weekday(), 0) + 1
                except ValueError:
                    pass
        return dow
    except Exception:
        return {}


_SLOT_TIMES = {"Morning": "09:00", "Afternoon": "14:00", "Evening": "19:00"}


def study_window(signal: dict, learner_id: str | None = None) -> dict:
    """Choose a realistic study cadence from a learner's work rhythm.

    When learner_id is supplied, historical contribution patterns boost the
    recommended day so the schedule aligns with proven study habits.
    """
    meetings = signal.get("meeting_hours_per_week", 0)
    focus = signal.get("focus_hours_per_week", 0)
    slot = signal.get("preferred_learning_slot", "Morning")
    reminder_time = _SLOT_TIMES.get(slot, "09:00")

    capacity_constrained = meetings > 20
    if capacity_constrained:
        cadence = "3 short 30-min sessions/week"
        note = "High meeting load - condensed sessions, no reminders during peak meeting windows."
        reminder_policy = f"Defer reminders; send a single nudge at {reminder_time} only on low-meeting days."
    elif focus >= 15:
        cadence = "4-5 sessions/week, 45-60 min"
        note = "Strong focus capacity - schedule blocks during focus-heavy periods."
        reminder_policy = f"Send a reminder at {reminder_time} to open a 45-60 min focus block."
    else:
        cadence = "3-4 sessions/week, 45 min"
        note = "Moderate capacity - steady cadence."
        reminder_policy = f"Send a gentle reminder at {reminder_time}."

    window: dict = {
        "preferred_slot": slot,
        "reminder_time": reminder_time,
        "cadence": cadence,
        "capacity_constrained": capacity_constrained,
        "guidance": note,
        "reminder_policy": reminder_policy,
    }

    # Enrich with historical contribution signal when available
    if learner_id:
        dow = _dow_pattern(learner_id)
        if dow:
            best_dow = max(dow, key=dow.get)  # type: ignore[arg-type]
            best_count = dow[best_dow]
            if best_count >= 3:
                window["preferred_day"] = _DAY_NAMES[best_dow]
                window["contribution_signal"] = (
                    f"Historically most active on {_DAY_NAMES[best_dow]}s "
                    f"({best_count} sessions) — schedule anchor study block on this day."
                )

    return window
