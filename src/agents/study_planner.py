"""Study Plan Generator — turns content into a realistic, capacity-aware schedule.

Grounding: Fabric IQ (recommended hours, prerequisites, skills) + Work IQ cadence.

The schedule STRUCTURE (skill order, hour weighting) is deterministic and exact —
driven by Fabric IQ skill gaps and recommended hours. In foundry mode the agent
adds a reasoning layer on top: it explains the pacing strategy and **curates a
YouTube video per focus skill** from candidates supplied by the orchestrator,
justifying each pick. On any LLM failure it returns the deterministic plan.
"""
from __future__ import annotations

from ..iq import fabric_iq
from ..config import MODE


SYSTEM_PROMPT = """You are the Study Plan Generator agent.
You receive a capacity-aware schedule skeleton (skills sequenced by gap and
prerequisite, with per-week hour targets) plus the learner's work rhythm and a
set of candidate YouTube videos per focus skill.

Your job is to REASON about the plan and design a REAL week-by-week schedule that
fits the given number of weeks and the certification. Return JSON only:
{
  "rationale": "2-3 sentences on the pacing/sequencing strategy and how it fits the learner's capacity",
  "weeks": [
    {
      "week": <int 1..N>,
      "focus_skill": "<the primary skill for this week, chosen from the sequenced skills>",
      "objective": "<one concrete, skill-specific learning objective for the week>",
      "checkpoint": "<a specific, measurable checkpoint for the week — NOT a generic phrase>",
      "target_hours": <float hours for the week>
    }
  ],
  "videos": { "<focus_skill>": { "index": <int index into that skill's candidate list>, "why": "<one line: why this video fits>" } }
}
Rules for "weeks":
- Produce EXACTLY one entry per week for ALL N weeks (week 1..N), in order.
- Distribute the sequenced skills across the weeks — earlier weeks cover gap skills
  and prerequisites; later weeks reinforce and integrate. A skill may span multiple
  weeks if it needs more time, and a light week may consolidate/review.
- target_hours across all weeks should sum to roughly the total recommended hours.
- objectives and checkpoints must be specific to the focus_skill and certification
  (e.g. "Deploy an HTTP-triggered Azure Function and bind it to a queue"), never the
  same generic sentence repeated.
Pick the single best video per focus skill. Use only the candidate indices given.
Never invent video titles or URLs. If a skill has no good candidate, omit it."""


def run(curator_output: dict, work_window: dict, weeks: int = 4,
        focus_skills: list[str] | None = None,
        video_candidates: dict[str, list[dict]] | None = None) -> dict:
    """Build the deterministic plan, then (foundry mode) add reasoning + video picks."""
    plan = _build_plan(curator_output, work_window, weeks, focus_skills)

    if MODE == "foundry":
        enriched = _reason_plan(plan, curator_output, work_window, video_candidates or {})
        if enriched:
            plan.update(enriched)
    return plan


def _build_plan(curator_output: dict, work_window: dict, weeks: int,
                focus_skills: list[str] | None) -> dict:
    """Deterministic, capacity-aware schedule (Fabric IQ driven). Always succeeds."""
    cert_id = curator_output["certification"]
    info = fabric_iq.cert_info(cert_id)
    total_hours = info.recommended_hours if info else 20
    per_week = round(total_hours / weeks, 1)
    skills = curator_output.get("skills", [])

    mastered = curator_output.get("mastered_skills", [])
    gaps = fabric_iq.skill_gap(cert_id, mastered)
    ordered = [s for s in skills if s in gaps] + [s for s in skills if s not in gaps]

    if focus_skills:
        focus_set = set(focus_skills)
        ordered = (
            [s for s in ordered if s in focus_set] +
            [s for s in ordered if s not in focus_set]
        )

    focus_set = set(focus_skills or [])
    n = max(len(ordered), 1)
    n_focus = sum(1 for s in ordered if s in focus_set)
    n_rest = n - n_focus
    base = total_hours / (n_focus * 1.5 + n_rest) if n_focus else total_hours / n

    milestones = []
    for i, skill in enumerate(ordered, start=1):
        is_focus = skill in focus_set
        target_h = round(base * 1.5, 1) if is_focus else round(base, 1)
        is_gap = skill in gaps
        # Spread skills across the available weeks instead of piling extras on the last.
        week_no = ((i - 1) % weeks) + 1
        milestones.append({
            "week": week_no,
            "focus_skill": skill,
            "target_hours": target_h,
            "objective": (f"Close the {skill} gap for {cert_id}" if is_gap
                          else f"Reinforce {skill} for {cert_id}"),
            "checkpoint": f"Practice assessment on {skill}",
            "is_gap": is_gap,
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


def _reason_plan(plan: dict, curator_output: dict, work_window: dict,
                 video_candidates: dict[str, list[dict]]) -> dict | None:
    """FOUNDRY: reason about pacing + curate one YouTube video per focus skill.

    Returns a dict to merge into the plan (rationale, recommended_video, and
    per-milestone recommended_video), or None on failure.
    """
    from ._reason import reason_or_delegate

    milestones = plan.get("milestones", [])
    # Pick which skills to curate videos for: focus skills, else the first 3 gaps.
    focus = plan.get("focus_skills") or [m["focus_skill"] for m in milestones if m.get("is_gap")][:3]
    focus = focus[:3]
    if not focus:
        focus = [m["focus_skill"] for m in milestones[:2]]

    # Build a compact candidate list per focus skill for the prompt.
    cand_lines = []
    for skill in focus:
        vids = video_candidates.get(skill, [])[:3]
        if not vids:
            continue
        listing = "; ".join(f"[{i}] {v.get('title','')[:70]} ({v.get('channel','')})"
                            for i, v in enumerate(vids))
        cand_lines.append(f"{skill}: {listing}")

    user = (
        f"Certification: {plan['certification']}. "
        f"Total {plan['total_recommended_hours']}h over {plan['weeks']} weeks "
        f"({plan['hours_per_week']}h/week). "
        f"Work rhythm: {work_window.get('cadence','default')}, "
        f"slot {work_window.get('preferred_slot','n/a')}, "
        f"capacity_constrained={work_window.get('capacity_constrained', False)}.\n"
        f"Sequenced skills (gaps first): {[m['focus_skill'] for m in milestones]}.\n"
        f"Focus skills: {focus}.\n\n"
        "Candidate videos per focus skill (pick by index):\n"
        + ("\n".join(cand_lines) if cand_lines else "(none available)")
    )

    # Generous budget: a full week-by-week breakdown (objective + checkpoint per week)
    # plus rationale and video picks easily exceeds the old 500-token cap and would
    # otherwise truncate into invalid JSON, silently dropping the dynamic milestones.
    data = reason_or_delegate("ascent-study-planner", SYSTEM_PROMPT, user, max_tokens=1600)
    if not data:
        return None

    out: dict = {"rationale": str(data.get("rationale", ""))[:400]}
    if data.get("_via"):
        out["_via"] = data["_via"]

    # If the LLM returned a real week-by-week schedule, use it (preserving the
    # deterministic gap/focus flags by matching on skill). Otherwise keep the
    # deterministic skeleton. This is what makes 4 vs 6 vs 8 weeks genuinely differ.
    llm_weeks = _coerce_llm_weeks(data.get("weeks"), plan["weeks"], milestones)
    if llm_weeks:
        milestones = llm_weeks
        out["milestones"] = milestones

    # Map LLM picks back to real video dicts; attach to milestones + top-level.
    picks = data.get("videos", {}) or {}
    top_video = None
    by_skill: dict[str, dict] = {}
    for skill, choice in picks.items():
        vids = video_candidates.get(skill, [])
        try:
            idx = int(choice.get("index", 0))
        except (TypeError, ValueError, AttributeError):
            idx = 0
        if 0 <= idx < len(vids):
            v = dict(vids[idx])
            v["why"] = str(choice.get("why", ""))[:160] if isinstance(choice, dict) else ""
            by_skill[skill] = v
            if top_video is None:
                top_video = v

    if by_skill:
        new_milestones = []
        for m in milestones:
            m2 = dict(m)
            if m["focus_skill"] in by_skill:
                m2["recommended_video"] = by_skill[m["focus_skill"]]
            new_milestones.append(m2)
        out["milestones"] = new_milestones
        out["recommended_video"] = top_video
    return out


def _coerce_llm_weeks(raw, n_weeks: int, skeleton: list[dict]) -> list[dict] | None:
    """Normalise the LLM's week-by-week schedule into milestone dicts.

    Preserves the deterministic gap/focus flags by matching each week's focus_skill
    against the skeleton. Returns None when the payload is unusable so the caller
    falls back to the deterministic skeleton.
    """
    if not isinstance(raw, list) or not raw:
        return None
    # skill -> (is_gap, is_focus) from the deterministic skeleton
    flags = {m["focus_skill"]: (m.get("is_gap", False), m.get("is_focus", False))
             for m in skeleton}
    out: list[dict] = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        skill = str(item.get("focus_skill", "")).strip()
        if not skill:
            continue
        try:
            week_no = int(item.get("week", i))
        except (TypeError, ValueError):
            week_no = i
        week_no = max(1, min(week_no, n_weeks))
        try:
            target_h = round(float(item.get("target_hours", 0)), 1)
        except (TypeError, ValueError):
            target_h = 0.0
        is_gap, is_focus = flags.get(skill, (False, False))
        out.append({
            "week": week_no,
            "focus_skill": skill,
            "target_hours": target_h,
            "objective": str(item.get("objective", ""))[:200],
            "checkpoint": str(item.get("checkpoint", ""))[:200] or f"Practice assessment on {skill}",
            "is_gap": is_gap,
            "is_focus": is_focus,
        })
    if not out:
        return None
    out.sort(key=lambda m: m["week"])
    return out
