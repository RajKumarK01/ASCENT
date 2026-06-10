"""Fabric IQ — semantic layer: entities, relationships, and business rules.

Implements the ontology contract (Learner, Role, Certification, Skill, SkillGap,
ReadinessScore, RecommendedHours, PassThreshold) over the synthetic seed. The
same contract can be backed by a real Fabric IQ semantic model later — the
reasoning is what matters. See BUILD_STEPS/06.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..config import semantic_seed


@dataclass
class CertInfo:
    id: str
    title: str
    skills: list[str]
    recommended_hours: int
    prerequisites: list[str]
    advancement: str | None


def _seed() -> dict:
    return semantic_seed()


def cert_for_role(role: str) -> str | None:
    return _seed()["roles"].get(role, {}).get("primary_cert")


def cert_info(cert_id: str) -> CertInfo | None:
    for c in _seed()["certifications"]:
        if c["id"] == cert_id:
            return CertInfo(c["id"], c["title"], c["skills"], c["recommended_hours"],
                            c["prerequisites"], c.get("advancement"))
    return None


def skill_gap(cert_id: str, mastered_skills: list[str]) -> list[str]:
    info = cert_info(cert_id)
    if not info:
        return []
    return [s for s in info.skills if s not in set(mastered_skills)]


def readiness(practice_score_avg: float, hours_studied: float, cert_id: str) -> dict:
    """Apply the pass-threshold + hours rule from the semantic seed."""
    rules = _seed()["rules"]
    info = cert_info(cert_id)
    rec = info.recommended_hours if info else 20
    needed_hours = rec * rules["min_recommended_hours_ratio"]
    ready = (practice_score_avg >= rules["pass_threshold_practice_score"]
             and hours_studied >= needed_hours)
    return {
        "ready": ready,
        "pass_threshold": rules["pass_threshold_practice_score"],
        "recommended_hours": rec,
        "hours_gap": max(0, round(needed_hours - hours_studied, 1)),
        "score_gap": max(0, rules["pass_threshold_practice_score"] - practice_score_avg),
    }


def risk_flags(learner: dict) -> list[str]:
    rules = _seed()["rules"]
    info = cert_info(learner.get("certification", ""))
    rec = info.recommended_hours if info else 20
    flags = []
    if learner.get("practice_score_avg", 0) < rules["pass_threshold_practice_score"]:
        flags.append("low_practice")
    if learner.get("hours_studied", 0) < rec * 0.7:
        flags.append("under_studied")
    return flags
