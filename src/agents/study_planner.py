"""Study Plan Generator — turns content into a realistic, capacity-aware schedule.

Grounding: Fabric IQ (recommended hours, prerequisites, skills) + Work IQ cadence.
"""
from __future__ import annotations

from ..iq import fabric_iq

SYSTEM_PROMPT = """You are the Study Plan Generator.
Convert curated content into a practical study schedule. Allocate hours using the
certification's recommended hours, sequence by prerequisites and difficulty, and
respect the learner's weekly capacity. Produce milestones at role level."""


def run(curator_output: dict, work_window: dict, weeks: int = 4) -> dict:
    cert_id = curator_output["certification"]
    info = fabric_iq.cert_info(cert_id)
    total_hours = info.recommended_hours if info else 20
    per_week = round(total_hours / weeks, 1)
    skills = curator_output.get("skills", [])

    # Prioritise skills the learner hasn't mastered yet (skill gaps first)
    mastered = curator_output.get("mastered_skills", [])
    gaps = fabric_iq.skill_gap(cert_id, mastered)
    ordered = [s for s in skills if s in gaps] + [s for s in skills if s not in gaps]

    milestones = []
    for i, skill in enumerate(ordered, start=1):
        milestones.append({
            "week": min(i, weeks),
            "focus_skill": skill,
            "target_hours": round(total_hours / max(len(ordered), 1), 1),
            "checkpoint": "Weekly practice assessment",
            "is_gap": skill in gaps,
        })

    return {
        "agent": "study_planner",
        "certification": cert_id,
        "total_recommended_hours": total_hours,
        "weeks": weeks,
        "hours_per_week": per_week,
        "cadence": work_window.get("cadence"),
        "preferred_slot": work_window.get("preferred_slot"),
        "prerequisites": info.prerequisites if info else [],
        "milestones": milestones,
    }
