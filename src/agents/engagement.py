"""Engagement Agent — keeps the learner on track using Work IQ context.

Grounding: Work IQ signals (meeting load, focus hours, preferred slot).
Outputs supportive, privacy-conscious reminder guidance — not one-size-fits-all.
"""
from __future__ import annotations

from ..iq import work_iq

SYSTEM_PROMPT = """You are the Engagement Agent.
Use work-context signals to choose supportive study windows and reminder timing.
Avoid disrupting peak work periods. Adapt to the individual's workload and focus
windows. Never expose another person's schedule detail."""


def run(learner_id: str) -> dict:
    signal = work_iq.signal_for(learner_id)
    if not signal:
        return {"agent": "engagement", "learner_id": learner_id,
                "window": None, "note": "No work signal available; using default cadence."}
    window = work_iq.study_window(signal, learner_id=learner_id)
    return {
        "agent": "engagement",
        "learner_id": learner_id,
        "window": window,
        "reminder_policy": window["reminder_policy"],
    }
