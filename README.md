# ASCENT

**Adaptive Skills & Certification ENablement for Teams**
A multi-agent enterprise learning system for the Reasoning Agents track (Battle #2), built on Microsoft Foundry + the Microsoft Agent Framework.

> ⚠️ **All data and documents in this repository are SYNTHETIC and for demonstration only.** No real personal, customer, employee, or proprietary data is used. Identifiers such as `L-1001`, `EMP-001`, and `TEAM-A` are fabricated.

---

## What it does

A learner gives a certification goal. The system:

1. Curates cited learning content for that goal and role (**Foundry IQ**).
2. Builds a realistic, capacity-aware study plan (**Fabric IQ** semantic model).
3. Schedules reminders around real work rhythm (**Work IQ** signals).
4. Generates grounded, cited practice questions and scores readiness (**Foundry IQ** + **Fabric IQ**).
5. Passes ready learners forward or loops back into preparation.
6. Surfaces team-level readiness and risk to managers — without exposing PII.

## Architecture

A top-level **Orchestrator** plans and routes to five specialist agents:

| Agent | Role | Grounding |
|---|---|---|
| Orchestrator | Plan + route + assemble | Agent Framework workflow |
| Learning Path Curator | Cert → skills → cited content | Foundry IQ + Microsoft Learn MCP |
| Study Plan Generator | Content → schedule + milestones | Fabric IQ |
| Engagement Agent | Study windows around work load | Work IQ |
| Assessment Agent | Cited questions + readiness score | Foundry IQ + Fabric IQ |
| Manager Insights Agent | Team readiness + risk (no PII) | Fabric IQ + Work IQ |

### Orchestration flow

```
Orchestrator.plan_route()
    │
    ├─[parallel]──┬── Curator        uses microsoft_docs_search + youtube_search tools
    │             └── Engagement     reads Work IQ signals
    │
    ├─[sequential]─── Study Planner  depends on curator output + engagement window
    │
    └─[critic loop]── Assessment     generates cited MCQs → readiness gate
              │
              └── if NOT READY → self-reflect → re-plan (max 2 loops)
```

### Reasoning patterns

| Pattern | Implementation |
|---|---|
| **Planner–Executor** | `plan_route()` decides full route before any specialist fires |
| **Role specialisation** | 5 bounded agents, each with a single concern and system prompt |
| **Concurrent execution** | Curator + Engagement run in parallel via `ThreadPoolExecutor` |
| **Critic / Verifier** | Assessment refuses uncited output; enforces pass threshold |
| **Self-reflection** | On fail: gap-skill analysis → LLM-driven priority + hours reasoning → re-plan |

### Agent responsibilities

| Agent | File | Responsibility |
|---|---|---|
| **Orchestrator** | `src/orchestrator.py` | Plans route, fans out to specialists, enforces readiness gate, assembles trace |
| **Curator** | `src/agents/curator.py` | Maps cert → skills → cited learning path using 3 tools (ML docs + YouTube) |
| **Study Planner** | `src/agents/study_planner.py` | Turns curator output into a weekly schedule; sequences by skill gaps and prerequisites |
| **Engagement** | `src/agents/engagement.py` | Recommends study windows from Work IQ signals; privacy-conscious |
| **Assessment** | `src/agents/assessment.py` | Generates cited MCQ questions; scores readiness; acts as Critic/Verifier |
| **Manager Insights** | `src/agents/manager_insights.py` | Aggregate team readiness and risk — never exposes individual data |

### IQ layers

| Layer | File | Role |
|---|---|---|
| **Foundry IQ** | `src/iq/foundry_iq.py` | Grounds answers in Azure AI Search (`ascent-kb`); returns citations |
| **Fabric IQ** | `src/iq/fabric_iq.py` | Semantic ontology — cert metadata, skill graphs, readiness thresholds |
| **Work IQ** | `src/iq/work_iq.py` | Work-signal scheduling — meeting load, focus windows, weekly capacity |

### External tools & APIs

| Tool | Used by | Purpose |
|---|---|---|
| `microsoft_docs_search` (MCP) | Curator | Official Microsoft Learn training paths and exam objectives |
| `microsoft_docs_fetch` (MCP) | Curator | Deep-read a specific Microsoft Learn URL |
| `youtube_search` | Curator | One recommended tutorial video matched to skill level |
| Azure AI Search | Foundry IQ | Knowledge base retrieval with semantic ranking |
| Azure AI Foundry SDK | All foundry-mode agents | Model inference via `AIProjectClient` + agent registration |
| Application Insights | Server | OpenTelemetry traces for agent-to-agent flow visibility |

### Data sources

All data is **synthetic**. No real employees, customers, or proprietary information.

| File | Contents |
|---|---|
| `data/learner_profiles.json` | Synthetic learner profiles (L-1001…L-1020) — roles, certs, scores |
| `data/semantic_seed.json` | Cert metadata — skills, recommended hours, prerequisites, advancement paths |
| `data/study_contributions.json` | Synthetic study activity signals |
| `docs/` | Synthetic knowledge base documents indexed into `ascent-kb` |

---

## Quickstart (local — backend agents)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in your Foundry values

python -m src.orchestrator L-1001   # runs the full flow locally with stub fallbacks
python -m evals.run_evals           # runs the eval scorecard (23/23 expected)
```

The code runs locally with deterministic fallbacks even before Azure resources exist. Flip `ASCENT_MODE=foundry` in `.env` to switch to real Foundry + Azure AI Search.

## Quickstart (local — full UI)

```bash
# Terminal 1 — FastAPI backend-for-frontend
pip install -r requirements.txt
python scripts/seed_users.py        # generates data/demo_users.json
uvicorn api.main:app --port 8000

# Terminal 2 — React frontend
cd ui
npm install
npm run dev                          # http://localhost:5173
```

### Demo credentials

| Email | Password | Role | Scope |
|---|---|---|---|
| `emp.morgan@ascent.demo` | `demo-pass-1` | Employee | L-1001 (Cloud Eng, loops to READY) |
| `emp.alex@ascent.demo` | `demo-pass-2` | Employee | L-1002 (DevOps, READY) |
| `emp.casey@ascent.demo` | `demo-pass-3` | Employee | L-1004 (failing learner) |
| `mgr.taylor@ascent.demo` | `demo-mgr` | Manager | TEAM-A |
| `mgr.jordan@ascent.demo` | `demo-mgr2` | Manager | All teams |

The journey is **path-aware and dynamic**: pick a certification (recommended or a custom path such as **SC-200**) and the Curator, Study Plan, modules, Microsoft Learn deep links, and Assessment all re-derive from that choice. Changing the plan length (4 / 6 / 8 / 12 weeks) produces a genuinely different week-by-week breakdown. The same behaviour runs server-side in Foundry — invoke any specialist from the **Agent Console** to watch it reason and call its tools.

---

## Register the agents in Microsoft Foundry

The five specialists are published to the **Foundry Agent Service** as **prompt agents** (model + instructions), where they appear in the Foundry portal under **Agents** and are invokable by name. This uses the new Foundry projects API (`azure-ai-projects` 2.x) — `agents.create_version(...)` with a `PromptAgentDefinition`.

> **Project endpoint format (important).** The Agents data-plane API requires the project path:
> `https://<resource>.services.ai.azure.com/api/projects/<project-name>` — not just the resource host.

Registration is a **one-time setup step** (not part of container startup). Run it locally after `az login`:

```bash
pip install azure-ai-projects azure-identity python-dotenv
# .env must contain:
#   AZURE_AI_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
#   AZURE_AI_MODEL_DEPLOYMENT=<your chat model deployment, e.g. gpt-4.1>
py scripts/register_foundry_agents.py     # publishes the 5 agents (version 1)
py scripts/invoke_foundry_agent.py ascent-curator "What should an AZ-204 candidate focus on first?"
```

`register_foundry_agents.py` reads each specialist's `SYSTEM_PROMPT` so the published instructions stay in sync with the code. Re-run it after changing any system prompt (creates a new agent version). `invoke_foundry_agent.py` calls a registered agent through the Responses API (`agent_reference`) to confirm it is live.

The grounding agents own **real Foundry-native tools** so they never depend on a single source: **Curator** and **Assessment** carry both **Azure AI Search** (internal Foundry IQ knowledge base) and the **Microsoft Learn MCP** (official module/exam deep links); **Study Planner** carries **Web Search** + the **Microsoft Learn MCP**. The Microsoft Learn MCP is the public hosted server (`https://learn.microsoft.com/api/mcp`) — no key, no setup — so a query like "official SC-200 path" returns real `learn.microsoft.com/training/paths/...` links cited alongside the internal KB.

> Open the agents in the **Microsoft Foundry portal** ([ai.azure.com](https://ai.azure.com)) signed in with the **same account/tenant** that owns the Foundry resource, with the correct project selected.

## Deploy the orchestrator as a Foundry Hosted Agent

The entry orchestrator runs as a **Foundry Hosted Agent** (`kind: hosted`) — Foundry pulls the container image, provisions a per-session sandbox, assigns the agent its own Microsoft Entra identity, and exposes a dedicated Responses endpoint. The container's custom code handles the multi-agent orchestration (Planner→Executor, Critic/Verifier, self-reflection) and calls Foundry models for reasoning. `src/server.py` serves the Responses protocol via `azure-ai-agentserver-responses`.

```bash
# 1. Build + push the image to ACR (remote build — no local Docker needed)
az acr build --registry <acr-name> --image ascent:hosted-v1 --platform linux/amd64 .

# 2. Let the Foundry project identity pull the image
az role assignment create --role AcrPull \
  --assignee-object-id <foundry-project-identity-objectId> --assignee-principal-type ServicePrincipal \
  --scope <acr-resource-id>

# 3. Register the hosted agent (reads endpoints/model from .env; polls until active)
py scripts/deploy_hosted_agent.py

# 4. Grant the agent's runtime identity model + search access (object ID printed by step 3)
az role assignment create --role "Cognitive Services OpenAI User" \
  --assignee-object-id <agent-identity-objectId> --assignee-principal-type ServicePrincipal \
  --scope <foundry-account-resource-id>
az role assignment create --role "Search Index Data Reader" \
  --assignee-object-id <agent-identity-objectId> --assignee-principal-type ServicePrincipal \
  --scope <search-service-resource-id>

# 5. Invoke through the agent's dedicated endpoint
py scripts/invoke_hosted_agent.py ascent-orchestrator "Help L-1001 prepare for AZ-204"
```

Notes:
- The agent runs `ASCENT_MODE=foundry`; the deploy script passes `AZURE_AI_PROJECT_ENDPOINT` (with the `/api/projects/<project>` path), `AZURE_AI_MODEL_DEPLOYMENT` (e.g. `gpt-4.1`), `AZURE_SEARCH_ENDPOINT`, and `AZURE_SEARCH_KNOWLEDGE_BASE` as the version's environment variables.
- **No secret is baked into the agent.** Search uses the agent's managed identity (`foundry_iq` falls back to `DefaultAzureCredential` when no key is set) — that's why step 4 grants Search Data Reader. Production secret path is a Key Vault connection.
- The orchestration **degrades gracefully**: if a grounding source or the model is unreachable, the agent still returns a plan (local-doc grounding / deterministic readiness) rather than failing.
- Endpoint: `{project}/agents/ascent-orchestrator/endpoint/protocols/openai/responses`
- `infra/` (`azd provision`) provisions the supporting ACR + Application Insights; the agent itself is registered by `scripts/deploy_hosted_agent.py`, not by `azd deploy`.

---

## Outlook calendar scheduling (separate test tenant)

The Study Plan page turns the agent's week-by-week milestones into concrete dates — each
week's **study block** is anchored to the learner's most active day (derived from the
contribution heatmap by Work IQ) and the **assessment checkpoint** follows two days later.
The **"📅 Add study plan to Outlook"** button writes these as calendar events (marked
**Busy**) via Microsoft Graph.

Auth is **app-only (client credentials)** against a **different tenant** than the
Foundry-hosted app — client-credential tokens are issued per-tenant, so the calendar tenant
just needs its own app registration:

1. In the **test tenant**: register an app → **API permissions** → Microsoft Graph →
   **Application** → `Calendars.ReadWrite` → **Grant admin consent**.
2. Add a client secret, then set in `.env` (never commit):
   ```
   GRAPH_TENANT_ID=<test-tenant-id>
   GRAPH_CLIENT_ID=<app-client-id>
   GRAPH_CLIENT_SECRET=<app-client-secret>
   GRAPH_DEFAULT_USER=<sample-user@testtenant.onmicrosoft.com>
   GRAPH_TIMEZONE=UTC
   ```
3. Verify: `py scripts/test_graph_calendar.py` creates one test event on the mailbox.

**No setup? Still works.** When `GRAPH_*` is unset the button downloads a standard `.ics`
file (events marked Busy) that imports into any calendar — so the feature is demoable with
zero Azure configuration. Uses `azure-identity` (`ClientSecretCredential`) + `httpx`, already
in `requirements.txt`.

---

## Repo layout

```
ascent/
├── README.md  .gitignore  .env.example
├── requirements.txt  azure.yaml  Dockerfile  agent.yaml
├── api/                # FastAPI BFF (auth, employee routes, manager routes, chat)
├── data/               # synthetic datasets (learners, work signals, semantic seed, demo users)
├── docs/               # synthetic knowledge docs (Foundry IQ source)
├── scripts/            # seed_users.py; register_foundry_agents.py (prompt specialists);
│                       # deploy_hosted_agent.py + invoke_hosted_agent.py (hosted orchestrator)
├── src/
│   ├── orchestrator.py  server.py  config.py
│   ├── agents/         # curator, study_planner, engagement, assessment, manager_insights
│   └── iq/             # foundry_iq, fabric_iq, work_iq
├── evals/              # testcases.json + run_evals.py (23 cases)
└── ui/                 # React + Vite + Tailwind SPA
    └── src/
        ├── pages/      # Login, EmployeeDashboard, StudyPlan, Assessment, ManagerDashboard, AgentConsole
        └── components/ # TraceTimeline, ProgressRing, CitationChip, Badge, Card
```
