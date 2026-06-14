"""Agent client for the BFF.

Three surfaces:
- run_for_learner / run_manager_insights → the in-process orchestrator (structured
  JSON the UI pages need; runs in foundry mode when ASCENT_MODE=foundry).
- ask_hosted_orchestrator → the deployed Foundry **hosted** agent (text reply for chat).
- invoke_agent → a single registered Foundry **prompt** agent (Agent Console).
"""
from __future__ import annotations
import os
from functools import lru_cache

PROJECT_NAME = os.environ.get("AZURE_AI_PROJECT_NAME", "ascentfoundryproject")
HOSTED_AGENT = os.environ.get("ASCENT_HOSTED_AGENT", "ascent-orchestrator")


def _project_endpoint() -> str:
    ep = (os.environ.get("AZURE_AI_PROJECT_ENDPOINT") or "").rstrip("/")
    if ep and "/api/projects/" not in ep:
        ep = f"{ep}/api/projects/{PROJECT_NAME}"
    return ep


@lru_cache(maxsize=1)
def _project_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    return AIProjectClient(
        endpoint=_project_endpoint(),
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )


# ── Structured orchestration (in-process) ─────────────────────────────────────

def run_for_learner(learner_id: str, weeks: int = 4,
                    cert_override: str | None = None,
                    score_override: float | None = None) -> dict:
    from src.orchestrator import run_for_learner as _run
    return _run(learner_id, weeks=weeks, cert_override=cert_override,
                score_override=score_override)


def run_manager_insights(team: str | None = None) -> dict:
    from src.agents.manager_insights import run
    return run(team)


# ── Foundry agent invocation (text) ───────────────────────────────────────────

def ask_hosted_orchestrator(message: str) -> str | None:
    """Call the deployed hosted orchestrator agent via its dedicated endpoint."""
    try:
        openai = _project_client().get_openai_client(agent_name=HOSTED_AGENT)
        resp = openai.responses.create(input=message)
        text = getattr(resp, "output_text", None)
        return text.strip() if text else None
    except Exception:
        return None


def invoke_agent(agent_name: str, prompt: str) -> str | None:
    """Invoke a registered Foundry prompt agent by name (Agent Console)."""
    try:
        openai = _project_client().get_openai_client()
        resp = openai.responses.create(
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
            input=prompt,
        )
        text = getattr(resp, "output_text", None)
        return text.strip() if text else None
    except Exception as exc:
        return f"(agent unavailable: {type(exc).__name__})"
