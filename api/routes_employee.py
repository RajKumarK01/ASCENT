from __future__ import annotations
import json
import random
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Query

from .deps import current_user, require_role
from .models import (
    RegenerateRequest, ProfileUpdateRequest, PathInterpretRequest, AssessmentSubmitRequest,
    ScheduleCalendarRequest,
)
from .scheduling import build_schedule
from .agent_client import run_for_learner
from src.integrations import graph_calendar

router = APIRouter(prefix="/api", tags=["employee"])

_employee = require_role("employee")

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

def _fetch_ms_learn_modules(cert_id: str) -> list[dict]:
    """Fetch live Microsoft Learn learning path modules for a certification."""
    try:
        query = urllib.parse.quote(f"{cert_id} learning path training modules")
        url = (f"https://learn.microsoft.com/api/search"
               f"?search={query}&locale=en-us&%24top=8&facet=category")
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                    "User-Agent": "ASCENT/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        modules = []
        for r in results[:6]:
            title = r.get("title", "")
            src_url = r.get("url", "")
            desc = (r.get("description") or "")[:120]
            if title and src_url:
                modules.append({
                    "title": title,
                    "url": src_url,
                    "description": desc,
                    "source": "microsoft_learn",
                })
        return modules
    except Exception:
        return []


# Process-level cache so repeated profile regenerations don't re-hit the Learn API.
_MS_LEARN_LINK_CACHE: dict[tuple[str, str], list[dict]] = {}


def _ms_learn_links(cert_id: str, skill: str, top: int = 3) -> list[dict]:
    """Return real Microsoft Learn DEEP links for a (cert, skill) pair.

    Hits the keyless Microsoft Learn search API and returns the actual module/doc
    URLs (not a generic /search?terms= page). Cached + resilient (→ [] on failure).
    """
    key = (cert_id, skill)
    if key in _MS_LEARN_LINK_CACHE:
        return _MS_LEARN_LINK_CACHE[key]
    links: list[dict] = []
    try:
        query = urllib.parse.quote(f"{cert_id} {skill}")
        url = (f"https://learn.microsoft.com/api/search"
               f"?search={query}&locale=en-us&%24top={min(top, 5)}&facet=category")
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                   "User-Agent": "ASCENT/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        for r in data.get("results", [])[:top]:
            title = (r.get("title") or "").strip()
            src_url = (r.get("url") or r.get("displayUrl") or "").strip()
            if title and src_url:
                links.append({"label": title[:80], "url": src_url})
    except Exception:
        links = []
    _MS_LEARN_LINK_CACHE[key] = links
    return links


def _make_modules(cert_id: str) -> list[dict]:
    info = _cert_info(cert_id) or {}
    skills = info.get("skills", [])
    total_hours = info.get("recommended_hours", 40)
    per_skill = round(total_hours / max(len(skills), 1), 1)

    import os as _os
    use_yt_api = bool(_os.environ.get("YOUTUBE_API_KEY"))

    def _yt_for_skill(skill: str) -> dict | None:
        # 1) Live YouTube Data API — freshest, skill-specific (needs key + quota).
        if use_yt_api:
            results = _search_youtube(f"{cert_id} {skill} tutorial Microsoft Azure")
            if results and results[0].get("video_id"):
                return results[0]
        # 2) Public YouTube search page — real, skill-specific, no API quota.
        scraped = _scrape_youtube(f"{cert_id} {skill} tutorial")
        if scraped:
            return scraped
        # 3) Curated map — offline-safe, hand-picked.
        vids = _CURATED_VIDEOS.get(skill)
        if vids:
            return _video_dict(vids[0]["video_id"], vids[0]["title"], vids[0]["channel"])
        # 4) Final floor: the certification overview video (always a real, verified link),
        #    so a module never falls back to an empty "Search on YouTube" tile.
        ov = _CERT_OVERVIEW_VIDEOS.get(cert_id)
        if ov:
            return _video_dict(ov["video_id"], ov["title"], ov["channel"])
        return None

    # Skill-based modules from semantic seed
    modules = []
    for idx, skill in enumerate(skills, start=1):
        resources = _ms_learn_links(cert_id, skill)
        modules.append({
            "id": f"{cert_id}-{idx}",
            "title": skill,
            "skill": skill,
            "status": "not started",
            "target_hours": per_skill,
            "source": "internal",
            # Primary "Open on Microsoft Learn" link = the top real deep link for the skill.
            "url": resources[0]["url"] if resources else None,
            "resources": resources,
            "description": f"Master {skill} as required for the {cert_id} certification.",
            "youtube": _yt_for_skill(skill),
        })

    # Live Microsoft Learn modules appended after skill modules
    ml_modules = _fetch_ms_learn_modules(cert_id)
    for i, ml in enumerate(ml_modules, start=len(modules) + 1):
        # Map each ML module to a skill by 0-based position (not an off-by arbitrary offset).
        skill_guess = skills[(i - len(skills) - 1) % len(skills)] if skills else cert_id
        modules.append({
            "id": f"{cert_id}-ml-{i}",
            "title": ml["title"],
            "skill": skill_guess,
            "status": "not started",
            "target_hours": round(total_hours / max(len(skills) + len(ml_modules), 1), 1),
            "source": "microsoft_learn",
            "url": ml["url"],
            "description": ml.get("description", ""),
            "youtube": _yt_for_skill(skill_guess),
        })

    return modules


_CURATED_VIDEOS: dict[str, list[dict]] = {
    "API Development":           [{"video_id": "9HFB3UG5CQ4", "title": "Azure API Management Tutorial", "channel": "Microsoft Azure"}],
    "Azure Functions":           [{"video_id": "Vxf-rOEO1q4", "title": "Azure Functions Full Tutorial", "channel": "Microsoft Azure"}],
    "Azure Storage":             [{"video_id": "UzTtastcBsk", "title": "Azure Storage Overview", "channel": "Microsoft Azure"}],
    "Azure Cosmos DB":           [{"video_id": "R_Fi59j6BMo", "title": "Azure Cosmos DB in 15 minutes", "channel": "Microsoft Azure"}],
    "Azure App Service":         [{"video_id": "4BwyqmRTrx8", "title": "Azure App Service Tutorial", "channel": "Microsoft Azure"}],
    "Azure Key Vault":           [{"video_id": "PgujSug1ZbI", "title": "Azure Key Vault - Getting Started", "channel": "Microsoft Azure"}],
    "CI/CD Pipelines":           [{"video_id": "NuYDAs3kNV8", "title": "Azure DevOps CI/CD Pipeline", "channel": "Microsoft Azure"}],
    "GitHub Actions":            [{"video_id": "mFFXuXjVgkU", "title": "GitHub Actions CI/CD Tutorial", "channel": "GitHub"}],
    "Infrastructure as Code":    [{"video_id": "t8GNpxHJGCE", "title": "Bicep Tutorial - IaC on Azure", "channel": "Microsoft Azure"}],
    "Microsoft Sentinel":        [{"video_id": "mJCkvzdMKH4", "title": "Microsoft Sentinel Overview", "channel": "Microsoft Security"}],
    "KQL Query Language":        [{"video_id": "P9iBPpbDjJc", "title": "KQL Tutorial for Beginners", "channel": "Microsoft Azure"}],
    "Threat Detection":          [{"video_id": "WZHv3O53BNI", "title": "Microsoft Defender Threat Detection", "channel": "Microsoft Security"}],
    "Azure Synapse Analytics":   [{"video_id": "p4EWBSIGe2A", "title": "Azure Synapse Analytics Tutorial", "channel": "Microsoft Azure"}],
    "Azure Databricks":          [{"video_id": "UoB65LIe7lU", "title": "Azure Databricks Introduction", "channel": "Microsoft Azure"}],
    "Stream Processing":         [{"video_id": "N7az1b4jWZE", "title": "Azure Stream Analytics Tutorial", "channel": "Microsoft Azure"}],
    "Solution Architecture Design": [{"video_id": "73ML9lZ_A5c", "title": "Azure Architecture Best Practices", "channel": "Microsoft Azure"}],
    "Azure Networking":          [{"video_id": "9DuTWSvsLXM", "title": "Azure Networking Fundamentals", "channel": "Microsoft Azure"}],
}

# Final per-certification fallback video (real, oEmbed-verified). Used when neither the
# live API, the scrape, nor a skill-specific curated entry yields a video — guarantees
# every module shows a real thumbnail rather than an empty search placeholder.
_CERT_OVERVIEW_VIDEOS: dict[str, dict] = {
    "AZ-204": {"video_id": "anef67apIEA", "title": "AZ-204 Full Course — Azure Developer Certification", "channel": "A Guide to Cloud & AI"},
    "AZ-305": {"video_id": "Dir7pH5F4Lc", "title": "Azure Solutions Architect (AZ-305) — Overview", "channel": "DecisionForest"},
    "AZ-400": {"video_id": "11KT1hPNkY4", "title": "Azure DevOps Engineer Expert (AZ-400) — Full Course", "channel": "freeCodeCamp.org"},
    "DP-203": {"video_id": "Gh7v6XCHNxU", "title": "Azure Data Engineering (DP-203) — Step-by-Step Guide", "channel": "Darshil Parmar"},
    "SC-200": {"video_id": "wdRlM_CvUA4", "title": "How to Pass SC-200 — Security Operations Analyst", "channel": "CloudThat"},
}


def _video_dict(vid_id: str, title: str, channel: str) -> dict:
    """Standard video card shape (thumbnail + watch URL derived from the id)."""
    return {
        "video_id": vid_id,
        "title": title,
        "channel": channel,
        "thumbnail_url": f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg",
        "url": f"https://www.youtube.com/watch?v={vid_id}",
    }


# Process-level cache so repeated profile regenerations don't re-scrape the same query.
_YT_SCRAPE_CACHE: dict[str, dict | None] = {}


def _scrape_youtube(query: str) -> dict | None:
    """Return a real video for a query by reading the public YouTube search results
    page (video filter). No API key or quota required. Cached + resilient (→ None)."""
    if query in _YT_SCRAPE_CACHE:
        return _YT_SCRAPE_CACHE[query]
    result: dict | None = None
    try:
        url = ("https://www.youtube.com/results?search_query="
               + urllib.parse.quote(query) + "&sp=EgIQAQ%253D%253D")  # sp = filter: videos only
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", "ignore")
        ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
        titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"\}', html)
        if ids:
            title = titles[0] if titles else "YouTube tutorial"
            try:  # decode \uXXXX / \/ escapes from the raw JSON-in-HTML
                title = json.loads(f'"{title}"')
            except Exception:
                pass
            result = _video_dict(ids[0], title, "YouTube")
    except Exception:
        result = None
    _YT_SCRAPE_CACHE[query] = result
    return result


def _search_youtube(query: str) -> list[dict]:
    """Return YouTube video recommendations.

    Tries the YouTube Data API (YOUTUBE_API_KEY env var) first; falls back to
    a curated skill-matched list so thumbnails always display.
    """
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if api_key:
        try:
            encoded = urllib.parse.quote(query)
            url = (f"https://www.googleapis.com/youtube/v3/search"
                   f"?part=snippet&q={encoded}&type=video&maxResults=3&key={api_key}")
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())
            videos = []
            for item in data.get("items", [])[:3]:
                vid_id = item["id"].get("videoId", "")
                snippet = item.get("snippet", {})
                if vid_id:
                    thumb = (snippet.get("thumbnails", {}).get("high", {}).get("url")
                             or f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg")
                    videos.append({
                        "video_id": vid_id,
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "thumbnail_url": thumb,
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                    })
            if videos:
                return videos
        except Exception:
            pass

    # Curated fallback — skill-key lookup from the query
    for skill, vids in _CURATED_VIDEOS.items():
        if skill.lower() in query.lower():
            return [
                {**v,
                 "thumbnail_url": f"https://img.youtube.com/vi/{v['video_id']}/hqdefault.jpg",
                 "url": f"https://www.youtube.com/watch?v={v['video_id']}"}
                for v in vids
            ]

    # Generic fallback — return search link only
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    return [{"video_id": "", "title": f"Search YouTube: {query[:60]}",
             "channel": "YouTube Search", "thumbnail_url": "",
             "url": search_url}]

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
        # Readiness/assessment scores start empty — the learner must take the assessment.
        "assessment": {"taken": False, "score_pct": 0, "date": None, "attempts": 0},
    }

def _ensure_profile(user: dict) -> dict:
    profiles = _load_profiles()
    profile = profiles.get(user["scope"])
    if not profile:
        profile = _create_default_profile(user)
        profiles[user["scope"]] = profile
        _save_profiles(profiles)
        return profile

    # Migrate older cached profiles that predate the assessment field.
    if "assessment" not in profile:
        profile["assessment"] = {"taken": False, "score_pct": 0, "date": None, "attempts": 0}
        profiles[user["scope"]] = profile
        _save_profiles(profiles)

    # Regenerate modules when empty or when the seed has grown
    active_cert = profile.get("active_certification", "")
    current_modules = profile.get("modules", [])
    seed_skills_count = len((_cert_info(active_cert) or {}).get("skills", []))
    internal_count = sum(1 for m in current_modules if m.get("source") != "microsoft_learn")
    import os as _os
    has_youtube = any("youtube" in m for m in current_modules)
    has_yt_api = bool(_os.environ.get("YOUTUBE_API_KEY"))
    # Regenerate if: no modules, seed grew, youtube field missing, or API key appeared since last gen
    youtube_upgraded = has_yt_api and has_youtube and all(
        not m.get("youtube", {}).get("video_id") for m in current_modules
    )
    needs_regen = (not current_modules) or (seed_skills_count > 0 and internal_count < seed_skills_count) or not has_youtube or youtube_upgraded
    if needs_regen and active_cert:
        profile["modules"] = _make_modules(active_cert)
        profile["progress"] = {
            "completed": sum(1 for m in profile["modules"] if m.get("status") == "complete"),
            "total": len(profile["modules"]),
        }
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
    # Switching certification invalidates the prior assessment score — require a re-take.
    if chosen_cert != profile.get("active_certification"):
        profile["assessment"] = {"taken": False, "score_pct": 0, "date": None, "attempts": 0}
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


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"email": user["sub"], "name": user["name"],
            "role": user["role"], "scope": user["scope"]}


def _score_override(profile: dict) -> float | None:
    """The learner's actual taken-assessment score, or None if not taken yet."""
    asmt = profile.get("assessment") or {}
    return float(asmt["score_pct"]) if asmt.get("taken") else None


@router.get("/plan")
def get_plan(weeks: int = Query(default=4, ge=1, le=16),
             user: dict = Depends(_employee)):
    profile = _ensure_profile(user)
    result = run_for_learner(user["scope"], weeks=weeks,
                             cert_override=profile.get("active_certification"),
                             score_override=_score_override(profile))
    result["profile"] = profile
    # Project milestones onto concrete dates (preferred day/slot from work signals)
    # so the UI can show when each study block + assessment is scheduled.
    plan = result.get("study_plan", {})
    window = (result.get("engagement", {}) or {}).get("window", {}) or {}
    sched = build_schedule(plan, window)
    plan["schedule"] = sched["events"]
    plan["milestones"] = sched["milestones"]
    # Expand assessment questions to MCQ format so Assessment page needs no separate call
    cert_id = result.get("curator", {}).get("certification", "")
    asmt = result.get("assessment", {})
    asmt["questions"] = [
        _make_mcq_question(q, cert_id) for q in asmt.get("questions", [])
    ]
    return result


@router.post("/plan/regenerate")
def regenerate_plan(body: RegenerateRequest, user: dict = Depends(_employee)):
    profile = _ensure_profile(user)
    result = run_for_learner(user["scope"], weeks=body.weeks,
                             cert_override=profile.get("active_certification"),
                             score_override=_score_override(profile))
    result["profile"] = profile
    return result


@router.get("/assessment")
def get_assessment(user: dict = Depends(_employee)):
    profile = _ensure_profile(user)
    result = run_for_learner(user["scope"],
                             cert_override=profile.get("active_certification"),
                             score_override=_score_override(profile))
    assessment = result.get("assessment", {})
    assessment["questions"] = [
        _make_mcq_question(q, result.get("curator", {}).get("certification", ""))
        for q in assessment.get("questions", [])
    ]
    assessment["profile"] = profile
    return assessment


@router.post("/employee/assessment/submit")
def submit_assessment(body: AssessmentSubmitRequest, user: dict = Depends(_employee)):
    """Persist the learner's ACTUAL assessment result so readiness becomes real."""
    profile = _ensure_profile(user)
    score = max(0, min(100, int(body.score_pct)))
    prior = profile.get("assessment") or {}
    profile["assessment"] = {
        "taken": True,
        "score_pct": score,
        "date": _to_date_key(datetime.now()),
        "attempts": int(prior.get("attempts", 0)) + 1,
        "correct": body.correct,
        "total": body.total,
    }
    _save_profile(user, profile)
    _record_activity(user, "assessment_taken", 1, allow_duplicate=True)
    if score >= 75:
        _record_activity(user, "assessment_passed", 1)
    return profile


@router.post("/employee/calendar/schedule")
def schedule_calendar(body: ScheduleCalendarRequest, user: dict = Depends(_employee)):
    """Create study/assessment events on the configured Outlook mailbox (cross-tenant,
    app-only). Falls back to a downloadable .ics when Graph isn't configured."""
    profile = _ensure_profile(user)
    result = run_for_learner(user["scope"], weeks=body.weeks,
                             cert_override=profile.get("active_certification"),
                             score_override=_score_override(profile))
    plan = result.get("study_plan", {})
    window = (result.get("engagement", {}) or {}).get("window", {}) or {}
    events = build_schedule(plan, window)["events"]
    if graph_calendar.is_configured():
        outcome = graph_calendar.create_events(events)
        return {"mode": "graph", "events": events, **outcome}
    cert = plan.get("certification", "plan")
    return {
        "mode": "ics",
        "events": events,
        "ics": graph_calendar.build_ics(events),
        "filename": f"ascent-{cert}-study-plan.ics",
    }


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
