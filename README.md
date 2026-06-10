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

Reasoning patterns: Planner–Executor (Orchestrator), Critic/Verifier (Assessment + grounding check), self-reflection loop (pass/fail), role specialisation.

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

The chat panel on the Employee Dashboard accepts free-text queries such as:
- *"Am I ready to book the exam?"*
- *"Build me a 6-week plan"*
- *"Focus on Azure Functions"*

---

## Deploy (Hosted Agent on Foundry Agent Service)

```bash
azd auth login
azd provision   # creates Foundry project, model, App Insights, container registry
azd deploy      # builds container, pushes to ACR, publishes the hosted agent
azd ai agent show
azd ai agent invoke "Help L-1001 prepare for AZ-204"
```

Fallback: deploy the same container to Azure Container Apps if Hosted Agent quota is unavailable.

---

## Repo layout

```
ascent/
├── README.md  .gitignore  .env.example
├── requirements.txt  azure.yaml  Dockerfile  agent.yaml
├── api/                # FastAPI BFF (auth, employee routes, manager routes, chat)
├── data/               # synthetic datasets (learners, work signals, semantic seed, demo users)
├── docs/               # synthetic knowledge docs (Foundry IQ source)
├── scripts/            # seed_users.py — generates demo_users.json
├── src/
│   ├── orchestrator.py  server.py  config.py
│   ├── agents/         # curator, study_planner, engagement, assessment, manager_insights
│   └── iq/             # foundry_iq, fabric_iq, work_iq
├── evals/              # testcases.json + run_evals.py (23 cases)
└── ui/                 # React + Vite + Tailwind SPA
    └── src/
        ├── pages/      # Login, EmployeeDashboard, StudyPlan, Assessment, ManagerDashboard
        └── components/ # ChatPanel, TraceTimeline, ProgressRing, CitationChip, Badge, Card
```
