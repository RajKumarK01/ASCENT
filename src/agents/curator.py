"""Learning Path Curator — maps a cert goal to skills and CITED content.

Grounding sources (decided by the LLM via tool-use):
  1. Foundry IQ knowledge base (Azure AI Search over docs/)
  2. Microsoft Learn — via microsoft_docs_search + microsoft_docs_fetch tools
  3. YouTube — via youtube_search tool (LLM picks the best video for the cert)

Rule: answer from retrieved content and always cite; never invent.
The LLM decides which tools to invoke and how many times (up to max_turns=6).
"""
from __future__ import annotations

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT

SYSTEM_PROMPT = """You are the Learning Path Curator for an enterprise certification system.
You have three tools available:
1. microsoft_docs_search — find official Microsoft Learn training paths and exam objectives
2. microsoft_docs_fetch  — fetch full content from a specific Microsoft Learn URL
3. youtube_search        — find the best tutorial video for a skill and learner level

Your job:
a) Search Microsoft Learn for the certification's official learning paths.
b) Optionally fetch one URL for deeper detail.
c) Search YouTube for ONE recommended tutorial video that fits the learner's skill level.
d) Write a concise 4-6 sentence learning path summary grounded in the retrieved content.

Rules:
- Always call microsoft_docs_search at least once.
- Always call youtube_search exactly once — the LLM must choose the query and skill level.
- Cite every claim: use the URL or title from retrieved content.
- Never invent module names, URLs, or video titles.
- End your response with: CITATIONS: <comma-separated list of URLs used>"""

_ML_QUERY_SUFFIX = "Microsoft Learn modules hands-on labs exam objectives study path"


def run(role: str, cert_id: str, mastered_skills: list[str] | None = None) -> dict:
    info = fabric_iq.cert_info(cert_id)

    # Foundry IQ retrieval — internal knowledge base (always runs, both modes)
    grounded_kb = foundry_iq.retrieve(
        f"{role} {cert_id} skills study pattern recommended hours {_ML_QUERY_SUFFIX}"
    )

    all_skills = info.skills if info else []
    effective_mastered = mastered_skills or []

    if MODE == "foundry":
        summary, tool_calls, ml_citations, yt_video = _run_with_tools(
            role, cert_id, grounded_kb, effective_mastered
        )
        is_grounded = grounded_kb.is_grounded or bool(ml_citations)
        all_citations = list(grounded_kb.citations) + ml_citations
        grounding_sources = ["Foundry IQ knowledge base"]
        if ml_citations:
            grounding_sources.append("Microsoft Learn (tool)")
        if yt_video:
            grounding_sources.append("YouTube (tool)")
    else:
        # LOCAL: direct API fallback, no LLM
        ml_live = _search_microsoft_learn(cert_id)
        ml_citations = ml_live if ml_live else _fetch_microsoft_learn_fallback(cert_id)
        all_citations = list(grounded_kb.citations) + ml_citations
        is_grounded = grounded_kb.is_grounded or bool(ml_citations)
        summary = grounded_kb.answer
        tool_calls = []
        yt_video = None
        grounding_sources = ["Foundry IQ knowledge base"]
        if ml_citations:
            grounding_sources.append("Microsoft Learn (live)" if ml_live else "Microsoft Learn (curated)")

    return {
        "agent": "curator",
        "role": role,
        "certification": cert_id,
        "skills": all_skills,
        "mastered_skills": effective_mastered,
        "recommended_hours": info.recommended_hours if info else None,
        "prerequisites": info.prerequisites if info else [],
        "content_summary": summary,
        "citations": [c.source for c in all_citations],
        "microsoft_learn_modules": [c.source for c in ml_citations],
        "is_grounded": is_grounded,
        "grounding_sources": grounding_sources,
        "tool_calls": tool_calls,           # logged in orchestrator trace
        "recommended_video": yt_video,      # LLM-selected YouTube video
    }


def _run_with_tools(role: str, cert_id: str, grounded_kb, mastered_skills: list) -> tuple:
    """FOUNDRY: run the curator using the LLM tool-use loop.

    Returns (summary, tool_calls_log, ml_citations, yt_video).
    """
    try:
        from ._foundry import get_openai_client
        from .tools import tool_loop, TOOL_SCHEMAS
        from ..iq.foundry_iq import Citation

        client = get_openai_client()

        # Infer learner skill level from mastered skills ratio
        all_skills = grounded_kb.citations  # proxy for total skills
        mastered_ratio = len(mastered_skills) / max(len(all_skills), 1)
        skill_level = "advanced" if mastered_ratio > 0.6 else ("intermediate" if mastered_ratio > 0.2 else "beginner")

        kb_text = grounded_kb.answer[:600] if grounded_kb.is_grounded else "No internal KB content."
        user_msg = (
            f"Role: {role}. Certification: {cert_id}.\n"
            f"Learner skill level: {skill_level}. "
            f"Mastered skills: {', '.join(mastered_skills) or 'none'}.\n\n"
            f"Internal knowledge base excerpt:\n{kb_text}\n\n"
            "Use your tools to:\n"
            "1. Search Microsoft Learn for the official learning path.\n"
            "2. Search YouTube for the best tutorial video for this certification at "
            f"  {skill_level} level.\n"
            "3. Write a 4-6 sentence learning path summary with citations."
        )

        summary, tool_calls_log = tool_loop(
            client=client,
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            tools=TOOL_SCHEMAS,
            max_turns=6,
        )

        # Extract MS Learn citations from tool results
        ml_citations: list[Citation] = []
        yt_video: dict | None = None
        for tc in tool_calls_log:
            if tc["tool"] == "microsoft_docs_search":
                for r in tc["result"].get("results", []):
                    if r.get("url"):
                        ml_citations.append(Citation(
                            source=r["url"],
                            snippet=f"Microsoft Learn: {r.get('title','')} — {r.get('description','')[:100]}",
                        ))
            elif tc["tool"] == "youtube_search":
                vids = tc["result"].get("videos", [])
                if vids:
                    yt_video = vids[0]  # LLM chose to search; first result is best match

        return summary, tool_calls_log, ml_citations, yt_video

    except Exception as exc:
        # Graceful fallback to direct API
        ml = _search_microsoft_learn(cert_id)
        return grounded_kb.answer, [{"tool": "error", "args": {}, "result_summary": str(exc)}], ml, None


# ── LOCAL mode helpers (no LLM) ───────────────────────────────────────────────

def _search_microsoft_learn(cert_id: str) -> list:
    """Direct REST call to learn.microsoft.com/api/search (no LLM, no MCP)."""
    try:
        import json as _json
        import urllib.request as _req
        import urllib.parse as _parse
        from ..iq.foundry_iq import Citation

        query = _parse.quote(f"{cert_id} exam objectives learning path training")
        url = (
            f"https://learn.microsoft.com/api/search"
            f"?search={query}&locale=en-us&%24top=3&facet=category"
        )
        r = _req.Request(url, headers={"Accept": "application/json", "User-Agent": "ASCENT/1.0"})
        with _req.urlopen(r, timeout=8) as resp:
            data = _json.loads(resp.read().decode())
        return [
            Citation(
                source=res.get("url") or res.get("displayUrl", ""),
                snippet=f"Microsoft Learn: {res.get('title','')} — {(res.get('description') or '')[:120]}",
            )
            for res in data.get("results", [])[:3]
            if res.get("url") or res.get("displayUrl")
        ]
    except Exception:
        return []


def _fetch_microsoft_learn_fallback(cert_id: str) -> list:
    """Curated static references used when the live API is unreachable."""
    from ..iq.foundry_iq import Citation
    _fallback: dict[str, list[Citation]] = {
        "AZ-204": [
            Citation(source="https://learn.microsoft.com/en-us/training/paths/create-azure-app-service-web-apps/",
                     snippet="Microsoft Learn: Create Azure App Service web apps — AZ-204 core path."),
            Citation(source="https://learn.microsoft.com/en-us/training/paths/implement-azure-functions/",
                     snippet="Microsoft Learn: Implement Azure Functions — serverless compute for AZ-204."),
        ],
        "AZ-305": [
            Citation(source="https://learn.microsoft.com/en-us/training/paths/microsoft-azure-architect-design-prerequisites/",
                     snippet="Microsoft Learn: Prerequisites for Azure architects."),
            Citation(source="https://learn.microsoft.com/en-us/training/paths/design-identity-governance-monitor-solutions/",
                     snippet="Microsoft Learn: Design identity, governance, and monitoring solutions."),
        ],
        "AZ-400": [
            Citation(source="https://learn.microsoft.com/en-us/training/paths/az-400-get-started-devops-transformation-journey/",
                     snippet="Microsoft Learn: Get started on a DevOps transformation journey."),
        ],
        "DP-203": [
            Citation(source="https://learn.microsoft.com/en-us/training/paths/data-engineer-azure/",
                     snippet="Microsoft Learn: Azure Data Engineer learning path."),
        ],
        "SC-200": [
            Citation(source="https://learn.microsoft.com/en-us/training/paths/sc-200-mitigate-threats-using-microsoft-defender-for-endpoint/",
                     snippet="Microsoft Learn: Mitigate threats using Microsoft Defender for Endpoint."),
        ],
    }
    return _fallback.get(cert_id, [])
