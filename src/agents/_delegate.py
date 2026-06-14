"""Agent-to-agent delegation — invoke a registered Foundry prompt agent by name.

Used by the orchestrator when AGENT_DELEGATION=foundry to genuinely delegate to
the independently-deployed Foundry specialist agents (ascent-curator, etc.) and
surface their reasoning in the trace. Best-effort: returns None on any failure so
the orchestrated result (built in-process) is never affected.
"""
from __future__ import annotations


def delegate(agent_name: str, prompt: str, max_output: int = 600) -> str | None:
    """Invoke a Foundry prompt agent via the Responses API; return its text."""
    try:
        from ._foundry import get_openai_client
        client = get_openai_client()
        resp = client.responses.create(
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
            input=prompt,
        )
        text = getattr(resp, "output_text", None)
        return text[:max_output].strip() if text else None
    except Exception as exc:
        # Surface the reason (callers that need clean output ignore "[error]…").
        return f"[error] {type(exc).__name__}: {str(exc)[:240]}"


def _extract_json(text: str) -> dict | None:
    """Parse a JSON object from agent text (tolerates code fences / surrounding prose)."""
    import json
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t[3:] else t.lstrip("`")
        t = t[4:] if t[:4].lower() == "json" else t
    try:
        return json.loads(t)
    except Exception:
        pass
    start, end = t.find("{"), t.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(t[start:end + 1])
        except Exception:
            return None
    return None


def delegate_json(agent_name: str, system: str, user: str) -> dict | None:
    """True delegation: have the Foundry sub-agent produce the structured result.

    Sends the specialist's contract (system) + inputs (user) to the registered
    Foundry agent and parses its JSON. Returns None on any failure so the caller
    falls back to in-process reasoning.
    """
    prompt = (
        f"{system}\n\n{user}\n\n"
        "Respond with ONLY a single valid JSON object — no prose, no code fences."
    )
    text = delegate(agent_name, prompt, max_output=4000)
    return _extract_json(text) if text else None
