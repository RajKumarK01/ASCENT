"""Shared config + data loading. No secrets live here — only env var names."""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

# "local"  -> deterministic fallbacks, no Azure calls (default; keeps repo runnable)
# "foundry"-> use real Foundry model + Foundry IQ knowledge base
MODE = os.environ.get("ASCENT_MODE", "local").lower()

MODEL_DEPLOYMENT = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4.1")
# In a Foundry Hosted Agent the runtime injects FOUNDRY_PROJECT_ENDPOINT; fall
# back to it so the orchestrator reaches the model without explicit config.
PROJECT_ENDPOINT = (
    os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    or os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
)
SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
KNOWLEDGE_BASE = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE", "ascent-kb")
SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")  # set in .env; never commit

# --- Microsoft Graph (Outlook calendar, TEST tenant — app-only client credentials) ---
# These belong to an app registered + admin-consented in the TEST tenant with the
# Calendars.ReadWrite APPLICATION permission. Cross-tenant works because client-credential
# tokens are issued per-tenant. Secrets live only in .env; never commit them.
GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID")
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET")
GRAPH_DEFAULT_USER = os.environ.get("GRAPH_DEFAULT_USER")  # sample mailbox UPN in the test tenant
GRAPH_TIMEZONE = os.environ.get("GRAPH_TIMEZONE", "UTC")

PASS_THRESHOLD = 75


def load_json(name: str) -> dict | list:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def learners() -> list[dict]:
    return load_json("learner_performance.json")


def work_signals() -> list[dict]:
    return load_json("work_signals.json")


def semantic_seed() -> dict:
    return load_json("semantic_seed.json")
