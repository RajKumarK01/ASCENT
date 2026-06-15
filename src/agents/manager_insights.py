"""Manager Insights Agent — team-level readiness and risk, with NO PII.

Grounding: Fabric IQ (readiness, risk flags) + Work IQ (capacity).
Aggregates only; never surfaces individual schedule detail or personal data.
"""
from __future__ import annotations
from collections import defaultdict

from ..iq import fabric_iq, work_iq
from ..config import learners, MODE
# The SYSTEM_PROMPT instructs the Manager Insights Agent to analyze aggregated, k-anonymized team statistics related to readiness, risk, and capacity. The agent is expected to generate a narrative that provides actionable insights for managers, along with prioritized risk callouts. The response must be in JSON format and should avoid any mention or implication of individual data, focusing solely on aggregate metrics.
SYSTEM_PROMPT = """You are the Manager Insights Agent.
You receive already-aggregated, k-anonymised team statistics (no individual data).
Reason about them and return JSON only:
{
  "narrative": "2-3 sentences a manager can act on — where the team stands and the biggest lever",
  "risks": ["<short, prioritised risk callout>", "..."]
}
Discuss only aggregates (readiness rate, risk rate, capacity). Never name or
imply an individual. Be specific and decision-useful, not generic."""


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
        if n < 3:
            # k-anonymity: suppress per-team detail when team is too small to anonymise
            summary[t] = {
                "learners": n,
                "k_anon_applied": True,
                "suppressed": True,
                "reason": "Team has fewer than 3 members; detail suppressed to prevent re-identification.",
                "readiness_rate": None,
                "risk_rate": None,
                "capacity_constrained": None,
            }
        else:
            summary[t] = {
                **v,
                "k_anon_applied": False,
                "readiness_rate": round(100 * v["ready"] / n),
                "risk_rate": round(100 * v["at_risk"] / n),
            }
    result = {"agent": "manager_insights", "scope": team or "all_teams", "teams": summary}

    if MODE == "foundry":
        reasoned = _reason_insights(summary, team or "all_teams")
        if reasoned:
            result.update(reasoned)  # narrative + risks
    return result


def _reason_insights(summary: dict, scope: str) -> dict | None:
    """FOUNDRY: turn aggregates into a manager narrative + risk callouts. No PII."""
    from ._reason import reason_or_delegate
    import json as _json

    # Only the non-suppressed teams carry usable aggregates.
    visible = {t: v for t, v in summary.items() if not v.get("suppressed")}
    if not visible:
        return None
    user = (
        f"Scope: {scope}. Aggregated team stats (k-anonymised, no individuals):\n"
        f"{_json.dumps(visible, indent=2)}\n\n"
        "Give a manager-actionable narrative and prioritised risk callouts."
    )
    data = reason_or_delegate("ascent-manager-insights", SYSTEM_PROMPT, user, max_tokens=400)
    if not data:
        return None
    out: dict = {}
    if data.get("narrative"):
        out["narrative"] = str(data["narrative"])[:600]
    risks = data.get("risks")
    if isinstance(risks, list):
        out["risks"] = [str(r)[:200] for r in risks[:5]]
    return out or None
