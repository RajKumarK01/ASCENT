"""Register the 5 ASCENT specialists as PROMPT agents in Azure AI Foundry.

They appear in the Foundry portal under **Agents** and are invokable directly
(e.g. from the UI Agent Console). These instructions are **self-contained
reasoners** — tuned to produce a good answer standalone, since a Foundry prompt
agent invoked on its own cannot execute the in-process tools (Microsoft Learn /
YouTube / Azure Search). The orchestrator's in-process specialists use their own
tool-driven prompts; these mirror the same role for direct invocation.

Run locally (signed in via `az login` / `azd auth login`):
    pip install azure-ai-projects azure-identity python-dotenv
    py scripts/register_foundry_agents.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition, WebSearchTool, MCPTool,
    AzureAISearchTool, AzureAISearchToolResource, AISearchIndexResource, AzureAISearchQueryType,
)
from azure.identity import DefaultAzureCredential

PROJECT_NAME = os.environ.get("AZURE_AI_PROJECT_NAME", "ascentfoundryproject")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4.1")
# Foundry IQ knowledge base: the project's Azure AI Search connection + index.
SEARCH_CONN = os.environ.get("AZURE_SEARCH_CONNECTION_NAME", "ascentsearchxb1ct2")
SEARCH_INDEX = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE", "ascentrag-1781081454381")
# Public Microsoft Learn MCP server — official module/exam content with real deep links,
# zero setup and no auth. Gives the grounding agents a second source so Azure AI Search
# is never the only dependency.
MSLEARN_MCP_URL = os.environ.get("MSLEARN_MCP_URL", "https://learn.microsoft.com/api/mcp")

endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").rstrip("/")
if "/api/projects/" not in endpoint:
    endpoint = f"{endpoint}/api/projects/{PROJECT_NAME}"

CURATOR = (
    "You are the ASCENT Learning Path Curator. Given a Microsoft certification "
    "(e.g. AZ-204, SC-200) and a learner's role, describe the official learning path: "
    "the core skill areas, recommended module sequence, and exam focus. Ground your "
    "answer in TWO sources: (1) your Azure AI Search knowledge base tool for approved "
    "internal guidance, and (2) the Microsoft Learn tool for the official module/learning-path "
    "deep links. Cite both, and prefer real Microsoft Learn URLs for modules. Do not rely on "
    "a single source — if the internal KB lacks the answer, ground in Microsoft Learn. Be "
    "concise (4-6 sentences) and never invent module names or URLs."
)
STUDY_PLANNER = (
    "You are the ASCENT Study Plan agent. Given a certification, total recommended "
    "hours, a number of weeks, and the learner's work capacity, reason about a "
    "realistic, capacity-aware schedule: sequence skills (gaps and prerequisites "
    "first) and allocate weekly hours that vary with the number of weeks. Use the "
    "Microsoft Learn tool to find the official module/lab deep links for each focus skill, "
    "and your web search tool for current tutorial videos/resources; recommend the best one "
    "per skill, citing the real source URL and explaining why it fits. Produce a genuine "
    "week-by-week breakdown (a specific objective + checkpoint per week). Keep it practical."
)
ENGAGEMENT = (
    "You are the ASCENT Engagement agent. Given a learner's work-context signal "
    "(weekly meeting hours, focus hours, preferred slot, busy days, deadlines), "
    "reason about WHEN and HOW OFTEN they should study so learning fits around work "
    "without adding stress. Recommend a cadence, reminder policy, and one line of "
    "supportive guidance. Avoid peak work periods. Never expose another person's data."
)
ASSESSMENT = (
    "You are the ASCENT Assessment agent. Given a certification and skill, write one "
    "realistic multiple-choice practice exam question (4 options, mark the correct "
    "one, add a one-sentence explanation). The question MUST be specific to the given "
    "skill and certification — never test an unrelated topic. Ground it in your Azure AI "
    "Search knowledge base tool for approved content AND the Microsoft Learn tool for the "
    "official objective, citing the source(s); don't depend on a single source. The "
    "question must be answerable and exam-representative."
)
MANAGER = (
    "You are the ASCENT Manager Insights agent. Given aggregated, k-anonymised team "
    "statistics (readiness rate, risk rate, capacity-constrained count), reason about "
    "where the team stands and the highest-impact action a manager should take. "
    "Discuss aggregates only — never name or imply an individual."
)

print("Endpoint:", endpoint)
print("Model deployment:", MODEL)

client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)

# Resolve the search connection id, then build the Foundry-managed Azure AI Search
# tool — curator/assessment query the knowledge base themselves, server-side, cited.
_search_conn_id = client.connections.get(SEARCH_CONN).id
_SEARCH_TOOL = AzureAISearchTool(azure_ai_search=AzureAISearchToolResource(
    indexes=[AISearchIndexResource(
        project_connection_id=_search_conn_id,
        index_name=SEARCH_INDEX,
        query_type=AzureAISearchQueryType.SEMANTIC,
    )]
))
print("Search connection:", SEARCH_CONN, "(", _search_conn_id[-40:], ") | index:", SEARCH_INDEX)

# Microsoft Learn MCP — official module/exam content with real deep links. Runs server-side
# with no approval prompt so the agent can call it unattended.
_MSLEARN_TOOL = MCPTool(
    server_label="microsoft_learn",
    server_url=MSLEARN_MCP_URL,
    server_description="Official Microsoft Learn documentation, modules, and exam objectives.",
    require_approval="never",
)
print("Microsoft Learn MCP:", MSLEARN_MCP_URL)

# (name, instructions, description, tools)
AGENTS = [
    ("ascent-curator",          CURATOR,       "Maps cert goals to grounded, cited learning paths (Foundry IQ search + Microsoft Learn)", [_SEARCH_TOOL, _MSLEARN_TOOL]),
    ("ascent-study-planner",    STUDY_PLANNER, "Sequences a capacity-aware schedule + recommends videos (web search + Microsoft Learn)", [WebSearchTool(), _MSLEARN_TOOL]),
    ("ascent-engagement",       ENGAGEMENT,    "Recommends study windows from work-context signals", None),
    ("ascent-assessment",       ASSESSMENT,    "Generates cited practice questions; gates readiness (Foundry IQ search + Microsoft Learn)", [_SEARCH_TOOL, _MSLEARN_TOOL]),
    ("ascent-manager-insights", MANAGER,       "Surfaces aggregate team readiness, no PII", None),
]

for name, instructions, desc, tools in AGENTS:
    try:
        definition = (
            PromptAgentDefinition(model=MODEL, instructions=instructions, tools=tools)
            if tools else
            PromptAgentDefinition(model=MODEL, instructions=instructions)
        )
        version = client.agents.create_version(
            agent_name=name,
            definition=definition,
            description=desc,
        )
        tool_note = f" [tools: {', '.join(type(t).__name__ for t in tools)}]" if tools else ""
        print(f"  OK   {name}  -> version {getattr(version, 'version', '?')}{tool_note}")
    except Exception as exc:
        print(f"  ERR  {name}: {type(exc).__name__}: {exc}")

print("\nDone. Open the Foundry portal -> your project -> Agents.")
