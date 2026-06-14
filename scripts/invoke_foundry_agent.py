"""Invoke a registered ASCENT Foundry agent via the Responses API.

Proves the agents created by register_foundry_agents.py are live in the
Foundry Agent Service and invokable by name (agent_reference).

    py scripts/invoke_foundry_agent.py [agent-name] ["your question"]
"""
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

ENDPOINT = "https://ascentfoundryproject-resource.services.ai.azure.com/api/projects/ascentfoundryproject"

agent_name = sys.argv[1] if len(sys.argv) > 1 else "ascent-curator"
question = sys.argv[2] if len(sys.argv) > 2 else "What should an AZ-204 candidate focus on first?"

# allow_preview covers hosted agents (preview); harmless for prompt agents.
project = AIProjectClient(
    endpoint=ENDPOINT, credential=DefaultAzureCredential(), allow_preview=True
)
openai = project.get_openai_client()

print(f"Invoking Foundry agent '{agent_name}'...\n")
response = openai.responses.create(
    extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    input=question,
)
print(response.output_text)
