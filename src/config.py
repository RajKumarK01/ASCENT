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

MODEL_DEPLOYMENT = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
PROJECT_ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
KNOWLEDGE_BASE = os.environ.get("AZURE_SEARCH_KNOWLEDGE_BASE", "ascent-kb")
SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")  # set in .env; never commit

PASS_THRESHOLD = 75


def load_json(name: str) -> dict | list:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def learners() -> list[dict]:
    return load_json("learner_performance.json")


def work_signals() -> list[dict]:
    return load_json("work_signals.json")


def semantic_seed() -> dict:
    return load_json("semantic_seed.json")
