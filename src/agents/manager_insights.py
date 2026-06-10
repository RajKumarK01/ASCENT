"""Manager Insights Agent — team-level readiness and risk, with NO PII.

Grounding: Fabric IQ (readiness, risk flags) + Work IQ (capacity).
Aggregates only; never surfaces individual schedule detail or personal data.
"""
from __future__ import annotations
from collections import defaultdict

from ..iq import fabric_iq, work_iq
from ..config import learners

SYSTEM_PROMPT = """You are the Manager Insights Agent.
Summarise learning progress by team, role, or certification. Highlight capacity-
constrained teams and likely exam-risk areas. Present aggregate insights only —
never expose individual personal data or another person's schedule."""


def run(team: str | None = None) -> dict:
    rows = [l for l in learners() if team is None or l["team"] == team]
    by_team: dict[str, dict] = defaultdict(lambda: {"learners": 0, "ready": 0,
                                                     "at_risk": 0, "capacity_constrained": 0})
    for l in rows:
        r = fabric_iq.readiness(l["practice_score_avg"], l["hours_studied"], l["certification"])
        flags = fabric_iq.risk_flags(l)
        sig = work_iq.signal_for(l["learner_id"])
        t = by_team[l["team"]]
        t["learners"] += 1
        t["ready"] += int(r["ready"])
        t["at_risk"] += int(bool(flags))
        if sig and sig.get("meeting_hours_per_week", 0) > 20:
            t["capacity_constrained"] += 1

    summary = {}
    for t, v in by_team.items():
        n = v["learners"]
        summary[t] = {
            **v,
            "readiness_rate": round(100 * v["ready"] / n) if n else 0,
            "risk_rate": round(100 * v["at_risk"] / n) if n else 0,
        }
    return {"agent": "manager_insights", "scope": team or "all_teams", "teams": summary}
