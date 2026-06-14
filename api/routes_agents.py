"""Agent Console routes — invoke the individual Foundry agents live.

Lets the UI call each independently-deployed Foundry agent directly: the 5 prompt
specialists (via agent_reference) and the hosted orchestrator (its own endpoint).
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .deps import current_user
from .agent_client import invoke_agent, ask_hosted_orchestrator, HOSTED_AGENT

router = APIRouter(prefix="/api/agents", tags=["agents"])

AGENTS = [
    {"name": HOSTED_AGENT, "label": "Orchestrator (hosted)", "kind": "hosted",
     "description": "Entry agent — plans the route and coordinates the 5 specialists. Runs as a Foundry Hosted Agent."},
    {"name": "ascent-curator", "label": "Curator", "kind": "prompt",
     "description": "Maps a cert goal to a grounded, cited learning path (Microsoft Learn + Foundry IQ)."},
    {"name": "ascent-study-planner", "label": "Study Planner", "kind": "prompt",
     "description": "Sequences a capacity-aware schedule and curates a YouTube video per focus skill."},
    {"name": "ascent-engagement", "label": "Engagement", "kind": "prompt",
     "description": "Reasons over Work IQ signals to choose study windows and reminder policy."},
    {"name": "ascent-assessment", "label": "Assessment", "kind": "prompt",
     "description": "Generates cited practice questions and gates readiness (Critic/Verifier)."},
    {"name": "ascent-manager-insights", "label": "Manager Insights", "kind": "prompt",
     "description": "Aggregate team readiness and risk — no individual data (k-anonymised)."},
]

_SAMPLE_PROMPTS = {
    "ascent-curator": "What is the official learning path and key skills for AZ-204?",
    "ascent-study-planner": "Sequence a 40h AZ-204 plan over 4 weeks and recommend video topics.",
    "ascent-engagement": "Recommend a study cadence for a learner with 22h meetings and 10h focus per week.",
    "ascent-assessment": "Write one cited practice MCQ for AZ-204 Azure Functions.",
    "ascent-manager-insights": "Summarise readiness risk for a team of 8 with a 40% readiness rate.",
    HOSTED_AGENT: "Help L-1001 prepare for AZ-204",
}


class InvokeRequest(BaseModel):
    input: str


@router.get("")
def list_agents(_: dict = Depends(current_user)):
    return {"agents": [{**a, "sample": _SAMPLE_PROMPTS.get(a["name"], "")} for a in AGENTS]}


@router.post("/{name}/invoke")
def invoke(name: str, body: InvokeRequest, _: dict = Depends(current_user)):
    prompt = (body.input or "").strip()[:1000] or _SAMPLE_PROMPTS.get(name, "Hello")
    if name == HOSTED_AGENT:
        reply = ask_hosted_orchestrator(prompt)
    else:
        reply = invoke_agent(name, prompt)
    return {"agent": name, "input": prompt, "reply": reply or "(no response)"}
