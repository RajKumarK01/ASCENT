"""Agent client: routes to local in-process call or hosted Foundry endpoint."""
from __future__ import annotations
import os

AGENT_TARGET = os.environ.get("AGENT_TARGET", "local").lower()
AGENT_ENDPOINT = os.environ.get("AGENT_ENDPOINT", "")


def run_for_learner(learner_id: str, weeks: int = 4) -> dict:
    if AGENT_TARGET == "foundry":
        return _call_hosted(f"Help {learner_id} prepare", learner_id)
    return _call_local(learner_id, weeks)


def run_manager_insights(team: str | None = None) -> dict:
    if AGENT_TARGET == "foundry":
        # Manager insights don't go through the hosted agent — run locally always.
        from src.agents.manager_insights import run
        return run(team)
    from src.agents.manager_insights import run
    return run(team)


def _call_local(learner_id: str, weeks: int) -> dict:
    from src.orchestrator import run_for_learner as _run
    return _run(learner_id, weeks=weeks)


def _call_hosted(message: str, learner_id: str) -> dict:
    import httpx
    from azure.identity import DefaultAzureCredential
    token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
    resp = httpx.post(
        f"{AGENT_ENDPOINT}/responses",
        json={"input": message},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()
