"""Shared structured-reasoning helper for foundry-mode specialist agents.

Generalises the JSON-mode LLM pattern already used by assessment._llm_question
and orchestrator._llm_reflect, so every specialist can reason with one call and
a consistent failure contract: returns the parsed dict, or None on any error
(callers fall back to deterministic output — no specialist should ever raise).
"""
from __future__ import annotations
import json
import os

from ..config import MODEL_DEPLOYMENT


def reason_or_delegate(agent_name: str, system: str, user: str, max_tokens: int = 500) -> dict | None:
    """Reason for a specialist — via its registered Foundry sub-agent when
    AGENT_DELEGATION=foundry (true agent-to-agent; the sub-agent's output IS the
    result), otherwise via a direct model call. Falls back to the direct call if
    delegation fails, so the orchestration never breaks.
    """
    if os.environ.get("ASCENT_DELEGATION", "local").lower() == "foundry":
        try:
            from ._delegate import delegate_json
            delegated = delegate_json(agent_name, system, user)
        except Exception:
            delegated = None
        if delegated is not None:
            delegated["_via"] = agent_name  # marker so the orchestrator can trace it
            return delegated
    return reason_json(system, user, max_tokens)


def reason_json(system: str, user: str, max_tokens: int = 500) -> dict | None:
    """Run one JSON-mode reasoning call. Returns parsed dict or None on failure."""
    try:
        from ._foundry import get_openai_client
        client = get_openai_client()
        resp = client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None
