"""Deploy the ASCENT orchestrator as a Foundry Hosted Agent (kind: hosted).

Registers a new version of the `ascent-orchestrator` agent that runs our
container image and serves the Responses protocol. Foundry pulls the image,
provisions a per-session sandbox, assigns an Entra agent identity, and exposes
the endpoint at {project}/agents/ascent-orchestrator/endpoint/protocols/openai/responses.

Prerequisites:
- Image pushed to ACR:  crjkxq44eis4c6m.azurecr.io/ascent:hosted-v1
- Foundry project managed identity granted AcrPull on that registry.
- Signed in: az login / azd auth login.

    py scripts/deploy_hosted_agent.py
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentProtocol,
    ContainerConfiguration,
    HostedAgentDefinition,
    ProtocolVersionRecord,
)
from azure.identity import DefaultAzureCredential

PROJECT_NAME = os.environ.get("AZURE_AI_PROJECT_NAME", "ascentfoundryproject")
AGENT_NAME = "ascent-orchestrator"
IMAGE = os.environ.get("ASCENT_IMAGE", "crjkxq44eis4c6m.azurecr.io/ascent:hosted-v1")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4.1")

endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").rstrip("/")
if "/api/projects/" not in endpoint:
    endpoint = f"{endpoint}/api/projects/{PROJECT_NAME}"

# Runtime env for the container. The Foundry runtime also injects
# FOUNDRY_PROJECT_ENDPOINT + APPLICATIONINSIGHTS_CONNECTION_STRING automatically.
# NOTE: no AZURE_SEARCH_API_KEY here — foundry_iq.py falls back to
# DefaultAzureCredential (the agent's managed identity) when the key is unset, so
# no secret is baked into the agent version. Grant the agent identity
# "Search Index Data Reader" on the search service after deploy (see README).
env_vars = {
    "ASCENT_MODE": "foundry",
    "AZURE_AI_PROJECT_ENDPOINT": endpoint,
    "AZURE_AI_MODEL_DEPLOYMENT": MODEL,
    "AZURE_SEARCH_ENDPOINT": os.environ.get("AZURE_SEARCH_ENDPOINT", ""),
    "AZURE_SEARCH_KNOWLEDGE_BASE": os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE", ""),
    # True agent-to-agent: the hosted orchestrator delegates to the registered
    # Foundry sub-agents (engagement, study-planner, manager-insights) and uses
    # their output; curator/assessment are also invoked (graceful fallback).
    # NB: AGENT_*/FOUNDRY_* env names are reserved by the platform, so this uses
    # the ASCENT_ prefix.
    "ASCENT_DELEGATION": os.environ.get("ASCENT_DELEGATION", "foundry"),
}

print(f"Endpoint: {endpoint}")
print(f"Image:    {IMAGE}")
print(f"Model:    {MODEL}")

# Hosted Agents is a preview feature — opt in via allow_preview.
client = AIProjectClient(
    endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True
)

version = client.agents.create_version(
    agent_name=AGENT_NAME,
    description="ASCENT entry orchestrator — plans and routes across 5 specialists with IQ grounding (hosted).",
    definition=HostedAgentDefinition(
        container_configuration=ContainerConfiguration(image=IMAGE),
        protocol_versions=[
            ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="1.0.0")
        ],
        cpu="1",
        memory="2Gi",
        environment_variables=env_vars,
    ),
)
ver = getattr(version, "version", "?")
print(f"\nCreated {AGENT_NAME} version {ver}. Provisioning (Foundry pulls image + starts sandbox)...")

# Poll until the version is active (or failed).
for attempt in range(60):  # ~5 min
    time.sleep(5)
    try:
        v = client.agents.get_version(agent_name=AGENT_NAME, agent_version=str(ver))
        status = getattr(v, "status", None) or (v.as_dict().get("status") if hasattr(v, "as_dict") else None)
    except Exception as exc:
        print(f"  poll error: {exc}")
        continue
    print(f"  [{attempt:02d}] status: {status}")
    _s = str(status).lower()
    if status and any(k in _s for k in ("active", "succeeded", "ready")):
        print(f"\n✅ {AGENT_NAME} v{ver} is {status}.")
        # Surface the agent's managed identity so we can grant it data-plane roles
        # (Search Index Data Reader on the search service; model access if needed).
        try:
            d = v.as_dict()
            ident = d.get("instance_identity") or d.get("identity") or {}
            print(f"   agent identity: {ident}")
        except Exception:
            pass
        break
    if status and any(k in _s for k in ("failed", "error")):
        print(f"\n❌ Provisioning failed: {v.as_dict() if hasattr(v, 'as_dict') else v}")
        break
else:
    print("\n⚠️  Still provisioning after timeout — check the Foundry portal.")

print('\nInvoke with: py scripts/invoke_hosted_agent.py ascent-orchestrator "Help L-1001 prepare for AZ-204"')
