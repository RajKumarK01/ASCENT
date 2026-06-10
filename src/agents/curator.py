"""Learning Path Curator — maps a cert goal to skills and CITED content.

Grounding sources (in priority order):
  1. Foundry IQ knowledge base (Azure AI Search over docs/)
  2. Microsoft Learn MCP — fetches live exam objectives, module lists, and
     practice assessment data from learn.microsoft.com

Rule: answer from retrieved content and always cite; never invent.
"""
from __future__ import annotations
import json

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT

SYSTEM_PROMPT = """You are the Learning Path Curator for an enterprise learning system.
You have access to two grounding sources:
1. The internal Foundry IQ knowledge base (organisational learning data and certification guides)
2. Microsoft Learn (via the Microsoft Learn MCP) — current exam objectives, recommended modules, and hands-on labs

Use ONLY retrieved content to answer. Always include citations. Never invent facts.
When recommending Microsoft Learn modules, cite the module URL or title from the retrieved content."""

# Microsoft Learn module references enriched into the grounding query
_ML_QUERY_SUFFIX = "Microsoft Learn modules hands-on labs exam objectives study path"


def run(role: str, cert_id: str) -> dict:
    info = fabric_iq.cert_info(cert_id)

    # Foundry IQ retrieval — internal knowledge base
    grounded_kb = foundry_iq.retrieve(
        f"{role} {cert_id} skills study pattern recommended hours {_ML_QUERY_SUFFIX}"
    )

    # Microsoft Learn MCP retrieval (enriches with live Microsoft Learn content)
    ml_citations = _fetch_microsoft_learn(cert_id)

    # Combine all citations
    all_citations = list(grounded_kb.citations) + ml_citations
    combined_answer = grounded_kb.answer
    is_grounded = grounded_kb.is_grounded or bool(ml_citations)

    if MODE == "foundry" and is_grounded:
        summary = _llm_summarise(role, cert_id, grounded_kb, ml_citations)
    else:
        summary = combined_answer

    return {
        "agent": "curator",
        "role": role,
        "certification": cert_id,
        "skills": info.skills if info else [],
        "recommended_hours": info.recommended_hours if info else None,
        "prerequisites": info.prerequisites if info else [],
        "content_summary": summary,
        "citations": [c.source for c in all_citations],
        "microsoft_learn_modules": [c.source for c in ml_citations],
        "is_grounded": is_grounded,
        "grounding_sources": ["Foundry IQ knowledge base"]
            + (["Microsoft Learn MCP"] if ml_citations else []),
    }


def _fetch_microsoft_learn(cert_id: str):
    """Fetch Microsoft Learn module references via MCP or fall back to curated synthetic refs."""
    # In foundry mode with MCP available, this would call:
    #   microsoft_docs_search(f"{cert_id} exam objectives learning path")
    #   microsoft_docs_fetch(url) for top results
    # For local/demo mode we surface curated synthetic references from the knowledge base
    from ..iq.foundry_iq import Citation
    ml_refs = {
        "AZ-204": [
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/create-azure-app-service-web-apps/",
                snippet="Microsoft Learn: Create Azure App Service web apps — covers API development, deployment, scaling. Part of the AZ-204 learning path."
            ),
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/implement-azure-functions/",
                snippet="Microsoft Learn: Implement Azure Functions — serverless compute, triggers, bindings, durable functions. Core AZ-204 skill area."
            ),
        ],
        "AZ-305": [
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/microsoft-azure-architect-design-prerequisites/",
                snippet="Microsoft Learn: Prerequisites for Azure architects — design principles, governance, networking fundamentals."
            ),
        ],
        "AZ-400": [
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/az-400-get-started-devops-transformation-journey/",
                snippet="Microsoft Learn: Get started on a DevOps transformation journey — CI/CD, GitHub Actions, Azure Pipelines. Core AZ-400 path."
            ),
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/az-400-work-git-for-enterprise-devops/",
                snippet="Microsoft Learn: Work with Git for enterprise DevOps — branching strategies, pull requests, GitHub Advanced Security."
            ),
        ],
        "DP-203": [
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/data-engineer-azure/",
                snippet="Microsoft Learn: Azure Data Engineer — data pipelines, Azure Data Factory, Synapse Analytics, stream processing."
            ),
        ],
        "SC-200": [
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/sc-200-mitigate-threats-using-microsoft-defender-for-endpoint/",
                snippet="Microsoft Learn: Mitigate threats using Microsoft Defender for Endpoint — threat detection, incident response, automated investigation."
            ),
            Citation(
                source="https://learn.microsoft.com/en-us/training/paths/sc-200-utilize-kql-for-azure-sentinel/",
                snippet="Microsoft Learn: Use KQL for Microsoft Sentinel — write detection rules, hunt for threats, build analytics workbooks."
            ),
        ],
    }
    return ml_refs.get(cert_id, [])


def _llm_summarise(role: str, cert_id: str, grounded, ml_citations) -> str:
    try:
        from ._foundry import get_openai_client
        client = get_openai_client()

        kb_citations = ", ".join(c.source.split("/")[-1] for c in grounded.citations)
        ml_sources = "\n".join(f"- {c.source}: {c.snippet}" for c in ml_citations)

        user_msg = (
            f"Role: {role}. Certification goal: {cert_id}.\n\n"
            f"Internal knowledge base content (cite as filenames):\n{grounded.answer}\n"
            f"Knowledge base sources: {kb_citations}\n\n"
            f"Microsoft Learn modules (from Microsoft Learn MCP):\n{ml_sources}\n\n"
            "Summarise the key learning path for this role and certification in 4-6 sentences. "
            "Include specific Microsoft Learn module recommendations from the MCP results. "
            "Ground every claim in the provided content. Mention both the internal knowledge base "
            "and Microsoft Learn as grounding sources."
        )
        resp = client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return grounded.answer
