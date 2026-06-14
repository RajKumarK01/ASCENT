"""Invoke the ASCENT hosted orchestrator agent via its dedicated endpoint.

Hosted agents are called through their own endpoint (not the agent_reference
pattern used for prompt agents). get_openai_client(agent_name=...) points the
OpenAI client at:
  {project}/agents/<name>/endpoint/protocols/openai/responses

    py scripts/invoke_hosted_agent.py [agent-name] ["your question"]

Note: the first call provisions a per-session sandbox (cold start) and may take
a minute or two.
"""
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

ENDPOINT = "https://ascentfoundryproject-resource.services.ai.azure.com/api/projects/ascentfoundryproject"

agent_name = sys.argv[1] if len(sys.argv) > 1 else "ascent-orchestrator"
question = sys.argv[2] if len(sys.argv) > 2 else "Help L-1001 prepare for AZ-204"

project = AIProjectClient(
    endpoint=ENDPOINT, credential=DefaultAzureCredential(), allow_preview=True
)
openai = project.get_openai_client(agent_name=agent_name)

print(f"Invoking hosted agent '{agent_name}' (cold start may take a minute)...\n")
response = openai.responses.create(input=question)
print(response.output_text)
