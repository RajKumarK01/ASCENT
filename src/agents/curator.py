"""Learning Path Curator — maps a cert goal to skills and CITED content.

Grounding: Foundry IQ knowledge base (+ optional Microsoft Learn MCP).
Rule: answer from retrieved content and always cite; never invent.
"""
from __future__ import annotations
import json

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT

SYSTEM_PROMPT = """You are the Learning Path Curator for an enterprise learning system.
Use ONLY the grounded knowledge base content provided in the user message to answer.
If the content doesn't contain the answer, say "I don't know".
Always ground your response in the provided citations. Never invent facts."""


def run(role: str, cert_id: str) -> dict:
    info = fabric_iq.cert_info(cert_id)
    grounded = foundry_iq.retrieve(f"{role} {cert_id} skills study pattern recommended hours")

    if MODE == "foundry" and grounded.is_grounded:
        summary = _llm_summarise(role, cert_id, grounded)
    else:
        summary = grounded.answer

    return {
        "agent": "curator",
        "role": role,
        "certification": cert_id,
        "skills": info.skills if info else [],
        "recommended_hours": info.recommended_hours if info else None,
        "prerequisites": info.prerequisites if info else [],
        "content_summary": summary,
        "citations": [c.source for c in grounded.citations],
        "is_grounded": grounded.is_grounded,
    }


def _llm_summarise(role: str, cert_id: str, grounded) -> str:
    try:
        from ._foundry import get_openai_client
        client = get_openai_client()
        citation_list = ", ".join(c.source.split("/")[-1] for c in grounded.citations)
        user_msg = (
            f"Role: {role}. Certification goal: {cert_id}.\n\n"
            f"Grounded knowledge base content:\n{grounded.answer}\n\n"
            f"Citations: {citation_list}\n\n"
            "Summarise the key learning path for this role and certification in 3-5 sentences. "
            "Ground every claim in the provided content. "
            "If the content is insufficient, respond: I don't know."
        )
        resp = client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return grounded.answer
