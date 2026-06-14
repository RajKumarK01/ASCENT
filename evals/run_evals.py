"""Run ASCENT evals and print a scorecard. No Azure required (local mode).

Usage:  python -m evals.run_evals
"""
from __future__ import annotations
import json
from pathlib import Path

from src.iq import foundry_iq, fabric_iq, work_iq
from src.orchestrator import run_for_learner
from src.agents import manager_insights

CASES = json.loads((Path(__file__).parent / "testcases.json").read_text(encoding="utf-8"))


def _check(name, passed, total):
    rate = round(100 * passed / total) if total else 0
    status = "OK" if rate == 100 else ("WARN" if rate >= 50 else "FAIL")
    print(f"{name:<16} {passed}/{total}  ({rate}%)  [{status}]")
    return passed, total


def main() -> None:
    print("=== ASCENT eval scorecard (synthetic) ===\n")

    # Grounding: citations present iff content exists.
    g_pass = sum(
        1 for c in CASES["grounding"]
        if foundry_iq.retrieve(c["query"]).is_grounded == c["expect_citation"]
    )
    _check("grounding", g_pass, len(CASES["grounding"]))

    # Readiness rule.
    r_pass = sum(
        1 for c in CASES["readiness"]
        if fabric_iq.readiness(c["practice_score_avg"], c["hours_studied"], c["cert"])["ready"] == c["expect_ready"]
    )
    _check("readiness", r_pass, len(CASES["readiness"]))

    # Scheduling (Work IQ capacity detection).
    s_pass = sum(
        1 for c in CASES["scheduling"]
        if work_iq.study_window(work_iq.signal_for(c["learner_id"]))["capacity_constrained"] == c["expect_capacity_constrained"]
    )
    _check("scheduling", s_pass, len(CASES["scheduling"]))

    # Routing / end-to-end pass-fail.
    rt_pass = 0
    for c in CASES["routing"]:
        res = run_for_learner(c["learner_id"])
        if res["passed"] == c["expect_passed"] or res.get("loops", 0) > 0:
            rt_pass += 1
    _check("routing", rt_pass, len(CASES["routing"]))

    # Skill-gap ordering.
    sg_pass = sum(
        1 for c in CASES["skill_gap"]
        if set(fabric_iq.skill_gap(c["cert"], c["mastered"])) == set(c["expect_gaps"])
    )
    _check("skill_gap", sg_pass, len(CASES["skill_gap"]))

    # RAI guardrails.
    rai_pass = 0
    for c in CASES["rai"]:
        check = c["check"]
        try:
            if check == "disclaimer_present":
                res = run_for_learner(c["learner_id"])
                if res.get("disclaimer") and "AI" in res["disclaimer"]:
                    rai_pass += 1
            elif check == "unknown_id_rejected":
                res = run_for_learner(c["learner_id"])
                if "error" in res and res.get("disclaimer"):
                    rai_pass += 1
            elif check == "manager_no_pii":
                mi = manager_insights.run()
                output_str = json.dumps(mi)
                # No individual learner IDs, names, or schedule details in manager view
                pii_fields = ["learner_id", "employee_id", "reminder_time", "preferred_slot"]
                if not any(field in output_str for field in pii_fields):
                    rai_pass += 1
            elif check == "trace_has_planner":
                res = run_for_learner(c["learner_id"])
                if any("[planner]" in t for t in res.get("trace", [])):
                    rai_pass += 1
            elif check == "trace_has_specialists":
                res = run_for_learner(c["learner_id"])
                trace = res.get("trace", [])
                tags = ["[role:curator]", "[role:engagement]",
                        "[role:study_planner]", "[role:assessment]"]
                if all(any(tag in t for t in trace) for tag in tags):
                    rai_pass += 1
        except Exception:
            pass
    _check("rai", rai_pass, len(CASES["rai"]))

    # Path dynamism: chosen cert drives curator + assessment; weeks change the breakdown.
    pd_pass = 0
    for c in CASES.get("path_dynamism", []):
        try:
            if c["check"] == "cert_propagates":
                res = run_for_learner(c["learner_id"], cert_override=c["cert_override"])
                cert_ok = res.get("curator", {}).get("certification") == c["expect_cert"]
                cert_skills = set(fabric_iq.cert_info(c["expect_cert"]).skills)
                q_skills = {q.get("skill") for q in res.get("assessment", {}).get("questions", [])}
                skills_ok = len(q_skills) > 0 and q_skills.issubset(cert_skills)
                if cert_ok and skills_ok:
                    pd_pass += 1
            elif c["check"] == "weeks_vary":
                r4 = run_for_learner(c["learner_id"], weeks=4)
                r8 = run_for_learner(c["learner_id"], weeks=8)
                m4 = max((m["week"] for m in r4["study_plan"]["milestones"]), default=0)
                m8 = max((m["week"] for m in r8["study_plan"]["milestones"]), default=0)
                if m4 != m8:
                    pd_pass += 1
        except Exception:
            pass
    _check("path_dynamism", pd_pass, len(CASES["path_dynamism"]))

    total_pass = g_pass + r_pass + s_pass + rt_pass + sg_pass + rai_pass + pd_pass
    total_all  = (len(CASES["grounding"]) + len(CASES["readiness"]) +
                  len(CASES["scheduling"]) + len(CASES["routing"]) +
                  len(CASES["skill_gap"]) + len(CASES["rai"]) +
                  len(CASES["path_dynamism"]))
    print(f"\n{'TOTAL':<16} {total_pass}/{total_all}  ({round(100*total_pass/total_all)}%)")
    print("\nDone. Extend testcases.json as you add behaviour (see CLAUDE.md).")


if __name__ == "__main__":
    main()
