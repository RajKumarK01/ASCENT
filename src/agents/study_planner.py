"""Study Plan Generator — turns content into a realistic, capacity-aware schedule.

Grounding: Fabric IQ (recommended hours, prerequisites, skills) + Work IQ cadence.
"""
from __future__ import annotations

from ..iq import fabric_iq

SYSTEM_PROMPT = """You are the Study Plan Generator.
Convert curated content into a practical study schedule. Allocate hours using the
certification's recommended hours, sequence by prerequisites and difficulty, and
respect the learner's weekly capacity. Produce milestones at role level."""


def run(curator_output: dict, work_window: dict, weeks: int = 4,
        focus_skills: list[str] | None = None) -> dict:
    cert_id = curator_output["certification"]
    info = fabric_iq.cert_info(cert_id)
    total_hours = info.recommended_hours if info else 20
    per_week = round(total_hours / weeks, 1)
    skills = curator_output.get("skills", [])

    # Prioritise gaps first, then apply focus_skills from self-reflection on top
    mastered = curator_output.get("mastered_skills", [])
    gaps = fabric_iq.skill_gap(cert_id, mastered)
    ordered = [s for s in skills if s in gaps] + [s for s in skills if s not in gaps]

    if focus_skills:
        focus_set = set(focus_skills)
        ordered = (
            [s for s in ordered if s in focus_set] +
            [s for s in ordered if s not in focus_set]
        )

    # Compute per-milestone hours: focus skills get 1.5× weight, normalised to total budget
    focus_set = set(focus_skills or [])
    n = max(len(ordered), 1)
    n_focus = sum(1 for s in ordered if s in focus_set)
    n_rest = n - n_focus
    base = total_hours / (n_focus * 1.5 + n_rest) if n_focus else total_hours / n

    milestones = []
    for i, skill in enumerate(ordered, start=1):
        is_focus = skill in focus_set
        target_h = round(base * 1.5, 1) if is_focus else round(base, 1)
        milestones.append({
            "week": min(i, weeks),
            "focus_skill": skill,
            "target_hours": target_h,
            "checkpoint": "Weekly practice assessment",
            "is_gap": skill in gaps,
            "is_focus": is_focus,
        })

    return {
        "agent": "study_planner",
        "certification": cert_id,
        "total_recommended_hours": total_hours,
        "weeks": weeks,
        "hours_per_week": per_week,
        "cadence": work_window.get("cadence"),
        "preferred_slot": work_window.get("preferred_slot"),
        "preferred_day": work_window.get("preferred_day"),
        "prerequisites": info.prerequisites if info else [],
        "milestones": milestones,
        "focus_skills": list(focus_set) if focus_set else [],
    }
