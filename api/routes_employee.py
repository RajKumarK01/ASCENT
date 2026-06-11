from __future__ import annotations
import re
import json
import random
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Query

from .deps import current_user, require_role
from .models import RegenerateRequest, ChatRequest, ProfileUpdateRequest, PathInterpretRequest
from .agent_client import run_for_learner

router = APIRouter(prefix="/api", tags=["employee"])

_employee = require_role("employee")

_WEEKS_RE  = re.compile(r'(\d+)[\s\-]*week', re.I)
_FOCUS_RE  = re.compile(r'focus\s+on\s+([A-Za-z/ ]{3,30})', re.I)

# Path to persistent study data files
CONTRIBUTIONS_FILE = Path(__file__).parent.parent / "data" / "study_contributions.json"
PROFILE_FILE = Path(__file__).parent.parent / "data" / "learner_profiles.json"
SEMANTIC_SEED_FILE = Path(__file__).parent.parent / "data" / "semantic_seed.json"

def _load_contributions() -> dict:
    """Load study contributions from JSON file."""
    if CONTRIBUTIONS_FILE.exists():
        with open(CONTRIBUTIONS_FILE, encoding='utf-8') as f:
            raw = json.load(f)
        return _normalize_contributions(raw)
    return {}

def _save_contributions(data: dict) -> None:
    """Save study contributions to JSON file."""
    CONTRIBUTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTRIBUTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _normalize_contributions(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}

    normalized: dict = {}
    for learner_id, learner_data in raw.items():
        if isinstance(learner_data, dict) and "dates" in learner_data:
            normalized[learner_id] = learner_data
        elif isinstance(learner_data, dict):
            normalized[learner_id] = {"dates": learner_data, "activities": []}
        else:
            normalized[learner_id] = {"dates": {}, "activities": []}
    return normalized


def _to_date_key(dt: datetime) -> str:
    return f"{dt.year}-{dt.month:02d}-{dt.day:02d}"


def _get_learner_contributions(user: dict) -> tuple[dict, dict]:
    contributions = _load_contributions()
    learner_id = user["scope"]
    learner_data = contributions.get(learner_id)
    if learner_data is None:
        learner_data = {"dates": {}, "activities": []}
        contributions[learner_id] = learner_data
    elif not isinstance(learner_data, dict) or "dates" not in learner_data:
        learner_data = {"dates": learner_data if isinstance(learner_data, dict) else {}, "activities": []}
        contributions[learner_id] = learner_data
    return contributions, learner_data


def _record_activity(user: dict, activity_type: str, count: int = 1, date: datetime | None = None, allow_duplicate: bool = False) -> None:
    contributions, learner_data = _get_learner_contributions(user)
    date_key = _to_date_key(date or datetime.now())

    if not allow_duplicate:
        for activity in learner_data["activities"]:
            if activity.get("date") == date_key and activity.get("type") == activity_type:
                return

    learner_data["dates"][date_key] = learner_data["dates"].get(date_key, 0) + count
    learner_data["activities"].append({
        "date": date_key,
        "type": activity_type,
        "count": count,
    })
    _save_contributions(contributions)


def _load_profiles() -> dict:
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_profiles(data: dict) -> None:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def _load_semantic_seed() -> dict:
    if SEMANTIC_SEED_FILE.exists():
        with open(SEMANTIC_SEED_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def _cert_info(cert_id: str) -> dict | None:
    seed = _load_semantic_seed()
    for cert in seed.get("certifications", []):
        if cert["id"] == cert_id:
            return cert
    return None

def _resolve_certification(user: dict) -> str:
    cert_id = user.get("certification")
    if cert_id and _validate_certification(cert_id):
        return cert_id

    seed = _load_semantic_seed()
    role_info = seed.get("roles", {}).get(user.get("role", ""), {})
    primary = role_info.get("primary_cert")
    if primary and _validate_certification(primary):
        return primary

    certifications = seed.get("certifications", [])
    return certifications[0]["id"] if certifications else ""

def _recommended_chain(user: dict) -> list[str]:
    cert_id = _resolve_certification(user)
    cert_info = _cert_info(cert_id)
    chain = [cert_id] if cert_id else []
    if cert_info and cert_info.get("advancement"):
        chain.append(cert_info["advancement"])
    return chain

def _path_options(user: dict) -> list[dict]:
    seed = _load_semantic_seed()
    role_info = seed.get("roles", {}).get(user.get("role", ""), {})
    current_cert = _resolve_certification(user)
    options = [
        {
            "key": "recommended",
            "title": "Recommended journey",
            "description": "Primary certification plus advancement path for your role.",
            "certifications": _recommended_chain(user),
        },
        {
            "key": "custom",
            "title": "Custom journey",
            "description": "Pick a certification goal that fits your own career path.",
            "certifications": [current_cert],
        },
    ]
    secondary = role_info.get("secondary_cert")
    if secondary and secondary != current_cert:
        options[1]["certifications"].append(secondary)
    return options

def _make_modules(cert_id: str) -> list[dict]:
    info = _cert_info(cert_id) or {}
    skills = info.get("skills", [])
    per_module = round(info.get("recommended_hours", 20) / max(len(skills), 1), 1)
    return [
        {
            "id": f"{cert_id}-{idx}",
            "title": skill,
            "skill": skill,
            "status": "not started",
            "target_hours": per_module,
        }
        for idx, skill in enumerate(skills, start=1)
    ]

def _create_default_profile(user: dict) -> dict:
    cert_chain = _recommended_chain(user)
    active_cert = cert_chain[0]
    modules = _make_modules(active_cert)
    return {
        "learner_id": user["scope"],
        "selected_path": "recommended",
        "active_certification": active_cert,
        "certification_chain": cert_chain,
        "path_title": "Recommended certification journey",
        "path_options": _path_options(user),
        "modules": modules,
        "progress": {"completed": 0, "total": len(modules)},
        "needs_selection": True,
        "message": "Welcome! Choose your first study path to personalise your journey.",
    }

def _ensure_profile(user: dict) -> dict:
    profiles = _load_profiles()
    profile = profiles.get(user["scope"])
    if not profile:
        profile = _create_default_profile(user)
        profiles[user["scope"]] = profile
        _save_profiles(profiles)
    return profile

def _save_profile(user: dict, profile: dict) -> dict:
    profiles = _load_profiles()
    profiles[user["scope"]] = profile
    _save_profiles(profiles)
    return profile

def _make_mcq_question(question: dict, cert_id: str) -> dict:
    skill = question.get("skill", "Study skill")
    q_text = question.get("question", "Review the material and choose the best answer.")

    # If the LLM already returned a full MCQ (FOUNDRY mode), shuffle and re-track the index.
    if question.get("choices") and isinstance(question["choices"], list) and len(question["choices"]) >= 2:
        choices = list(question["choices"])
        correct_idx = int(question.get("correct_index", 0))
        correct_answer = choices[correct_idx]
        random.shuffle(choices)
        new_correct = choices.index(correct_answer)
        return {
            "skill": skill,
            "question": q_text,
            "choices": choices,
            "correct_index": new_correct,
            "hint": question.get("hint", "Focus on the certification context."),
            "explanation": question.get("explanation", ""),
            "citations": question.get("citations", []),
        }

    # LOCAL mode: build skill-aware distractors from the semantic seed.
    seed = _load_semantic_seed()
    cert_skills = next(
        (c["skills"] for c in seed.get("certifications", []) if c["id"] == cert_id),
        []
    )
    other_skills = [s for s in cert_skills if s != skill]

    distractor_templates = [
        f"Configure {other_skills[0] if other_skills else 'Azure networking'} settings to satisfy this requirement.",
        f"Use {other_skills[1] if len(other_skills) > 1 else 'Azure Monitor'} to address this scenario instead.",
        f"Apply a general cloud architecture pattern not specific to {cert_id}.",
    ]

    correct_answer = q_text
    choices = [correct_answer] + distractor_templates[:3]
    random.shuffle(choices)
    correct_index = choices.index(correct_answer)

    return {
        "skill": skill,
        "question": q_text,
        "choices": choices,
        "correct_index": correct_index,
        "hint": question.get("hint", f"Consider the specific {cert_id} context for {skill}."),
        "explanation": "",
        "citations": question.get("citations", []),
    }

def _cap_profile_progress(profile: dict) -> dict:
    completed = sum(1 for module in profile.get("modules", []) if module.get("status") == "complete")
    profile["progress"] = {"completed": completed, "total": len(profile.get("modules", []))}
    return profile

def _validate_certification(cert_id: str) -> bool:
    return _cert_info(cert_id) is not None

def _update_profile_path(user: dict, path: str, certification: str | None = None) -> dict:
    profile = _ensure_profile(user)
    chosen_cert = certification if certification else profile["active_certification"]
    if not _validate_certification(chosen_cert):
        chosen_cert = profile["active_certification"]
    if path == "recommended":
        profile["certification_chain"] = [chosen_cert]
        next_cert = _cert_info(chosen_cert).get("advancement") if _cert_info(chosen_cert) else None
        if next_cert:
            profile["certification_chain"].append(next_cert)
        profile["path_title"] = "Recommended certification journey"
    else:
        profile["certification_chain"] = [chosen_cert]
        profile["path_title"] = "Custom certification journey"
    profile["selected_path"] = path
    profile["active_certification"] = chosen_cert
    profile["modules"] = _make_modules(chosen_cert)
    profile["needs_selection"] = False
    profile["message"] = "Your journey is set. Track progress across modules and certifications."
    _cap_profile_progress(profile)
    return _save_profile(user, profile)

def _complete_module(user: dict, module_id: str) -> dict:
    profile = _ensure_profile(user)
    for module in profile.get("modules", []):
        if module.get("id") == module_id:
            if module.get("status") != "complete":
                module["status"] = "complete"
                _cap_profile_progress(profile)
                _save_profile(user, profile)
                _record_activity(user, "module_completed", 1)
            return profile
    return _save_profile(user, profile)

def _parse_intent(message: str, default_weeks: int = 4) -> dict:
    """Extract weeks and focus-skill hints from free-text."""
    weeks_match = _WEEKS_RE.search(message)
    weeks = int(weeks_match.group(1)) if weeks_match else default_weeks
    weeks = max(1, min(16, weeks))

    focus_match = _FOCUS_RE.search(message)
    focus_skill = focus_match.group(1).strip() if focus_match else None

    return {"weeks": weeks, "focus_skill": focus_skill}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"email": user["sub"], "name": user["name"],
            "role": user["role"], "scope": user["scope"]}


@router.get("/plan")
def get_plan(weeks: int = Query(default=4, ge=1, le=16),
             user: dict = Depends(_employee)):
    result = run_for_learner(user["scope"], weeks=weeks)
    result["profile"] = _ensure_profile(user)
    # Expand assessment questions to MCQ format so Assessment page needs no separate call
    cert_id = result.get("curator", {}).get("certification", "")
    asmt = result.get("assessment", {})
    asmt["questions"] = [
        _make_mcq_question(q, cert_id) for q in asmt.get("questions", [])
    ]
    _record_activity(user, "assessment_taken", 1)
    if result.get("passed"):
        _record_activity(user, "assessment_passed", 1)
    return result


@router.post("/plan/regenerate")
def regenerate_plan(body: RegenerateRequest, user: dict = Depends(_employee)):
    result = run_for_learner(user["scope"], weeks=body.weeks)
    result["profile"] = _ensure_profile(user)
    return result


@router.get("/assessment")
def get_assessment(user: dict = Depends(_employee)):
    result = run_for_learner(user["scope"])
    assessment = result.get("assessment", {})
    _record_activity(user, "assessment_taken", 1)
    if result.get("passed"):
        _record_activity(user, "assessment_passed", 1)
    assessment["questions"] = [
        _make_mcq_question(q, result.get("curator", {}).get("certification", ""))
        for q in assessment.get("questions", [])
    ]
    assessment["profile"] = _ensure_profile(user)
    return assessment


@router.get("/employee/profile")
def get_employee_profile(user: dict = Depends(_employee)):
    profile = _ensure_profile(user)
    return profile


@router.post("/employee/profile")
def update_employee_profile(body: ProfileUpdateRequest, user: dict = Depends(_employee)):
    return _update_profile_path(user, body.path, body.certification)


@router.post("/employee/study/module/{module_id}/complete")
def complete_study_module(module_id: str, user: dict = Depends(_employee)):
    return _complete_module(user, module_id)


@router.post("/employee/path/interpret")
def interpret_path(body: PathInterpretRequest, user: dict = Depends(_employee)):
    """Interpret a free-text learning goal and suggest a certification path."""
    seed = _load_semantic_seed()
    certs = seed.get("certifications", [])
    cert_list = "\n".join(
        f"- {c['id']}: {c['title']} (skills: {', '.join(c['skills'])})" for c in certs
    )

    from src.config import MODE, MODEL_DEPLOYMENT
    suggestion = _llm_interpret_path(body.description, cert_list, MODE, MODEL_DEPLOYMENT)

    # Validate suggested cert exists
    valid_ids = {c["id"] for c in certs}
    if suggestion.get("certification") not in valid_ids:
        # Fallback: keyword match
        desc_lower = body.description.lower()
        for c in certs:
            if c["id"].lower() in desc_lower or c["title"].lower() in desc_lower:
                suggestion["certification"] = c["id"]
                suggestion["reasoning"] = f"Matched '{c['id']}' from your description."
                break
        else:
            suggestion["certification"] = certs[0]["id"]
            suggestion["reasoning"] = "Defaulted to primary certification — please adjust if needed."

    cert_info = next((c for c in certs if c["id"] == suggestion["certification"]), {})
    return {
        "certification": suggestion["certification"],
        "cert_title": cert_info.get("title", ""),
        "path": suggestion.get("path", "custom"),
        "reasoning": suggestion.get("reasoning", ""),
        "skills": cert_info.get("skills", []),
        "recommended_hours": cert_info.get("recommended_hours", 20),
        "available_certifications": [c["id"] for c in certs],
    }


def _llm_interpret_path(description: str, cert_list: str, mode: str, model: str) -> dict:
    if mode == "foundry":
        try:
            import json as _json
            from src.agents._foundry import get_openai_client
            client = get_openai_client()
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "system",
                    "content": (
                        "You are a learning path advisor. Given a learner's goal description, "
                        "identify the best Azure certification from the list provided. "
                        "Return JSON: {\"certification\": \"<ID>\", \"path\": \"custom\", \"reasoning\": \"<1 sentence>\"}"
                    )
                }, {
                    "role": "user",
                    "content": f"Available certifications:\n{cert_list}\n\nLearner goal: {description}"
                }],
                response_format={"type": "json_object"},
                max_tokens=150,
            )
            return _json.loads(resp.choices[0].message.content)
        except Exception:
            pass

    # Local fallback: simple keyword matching
    desc_lower = description.lower()
    keyword_map = {
        "AZ-204": ["developer", "api", "function", "app service", "develop", "code", "backend"],
        "AZ-305": ["architect", "architecture", "design", "solution", "enterprise"],
        "AZ-400": ["devops", "ci/cd", "pipeline", "github", "deployment", "automation"],
        "DP-203": ["data", "pipeline", "analytics", "synapse", "stream", "etl"],
        "SC-200": ["security", "sentinel", "defender", "threat", "soc", "incident"],
    }
    scores = {cid: sum(1 for kw in kws if kw in desc_lower) for cid, kws in keyword_map.items()}
    best = max(scores, key=scores.get)
    return {
        "certification": best if scores[best] > 0 else "AZ-204",
        "path": "custom",
        "reasoning": f"Based on your description, {best} aligns best with your stated goals.",
    }


@router.post("/chat")
def chat(body: ChatRequest, user: dict = Depends(_employee)):
    """Free-text chat: interpret intent, run the orchestrator, return a structured reply."""
    intent = _parse_intent(body.message)
    result = run_for_learner(user["scope"], weeks=intent["weeks"])

    # Build a plain-language reply summarising the result
    plan   = result.get("study_plan", {})
    asmt   = result.get("assessment", {})
    r      = asmt.get("readiness", {})
    passed = result.get("passed", False)
    loops  = result.get("loops", 0)

    if "help" in body.message.lower() or "prepare" in body.message.lower() or not body.message.strip():
        reply = (
            f"I've reviewed {user['scope']}'s learning profile for "
            f"{result.get('curator', {}).get('certification', 'your certification')}. "
        )
    elif "ready" in body.message.lower() or "exam" in body.message.lower():
        reply = f"Readiness check for {user['scope']}: "
    elif intent["focus_skill"]:
        reply = f"I've built a plan focusing on {intent['focus_skill']}. "
    else:
        reply = "Here's an updated learning plan based on your request. "

    if passed:
        reply += (
            f"Good news — you're on track to be exam-ready in {plan.get('weeks')} weeks "
            f"({plan.get('hours_per_week')}h/week). "
        )
        if result.get("next_step"):
            reply += f"After this certification, consider {result['next_step']}."
    else:
        reply += (
            f"You need {r.get('hours_gap', 0)}h more study and "
            f"+{r.get('score_gap', 0)}% on practice scores. "
            f"I've extended your plan to {plan.get('weeks')} weeks to close the gap."
        )
        if loops:
            reply += f" The planner ran {loops} reflection loop(s) to find the best path."

    return {
        "message": body.message,
        "reply": reply,
        "result": result,
        "intent": intent,
    }


@router.get("/employee/study/contributions")
def get_contributions(user: dict = Depends(_employee)) -> dict:
    """Get study contribution history for the last 365 days."""
    contributions = _load_contributions()
    learner_id = user["scope"]
    learner_data = contributions.get(learner_id, {})
    if isinstance(learner_data, dict) and "dates" in learner_data:
        return learner_data["dates"]
    return learner_data


@router.post("/employee/study/checkin")
def checkin_study(user: dict = Depends(_employee)) -> dict:
    """Mark today's study as completed."""
    today = datetime.now()
    date_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    _record_activity(user, "study_session_completed", 1, date=today, allow_duplicate=True)
    contributions = _load_contributions()
    learner_id = user["scope"]
    learner_data = contributions.get(learner_id, {"dates": {}, "activities": []})

    return {
        "success": True,
        "date": date_str,
        "count": learner_data["dates"].get(date_str, 1)
    }
