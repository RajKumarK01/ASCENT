"""Shared AIProjectClient factory for foundry-mode agents."""
from __future__ import annotations
from functools import lru_cache


@lru_cache(maxsize=1)
def get_openai_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    from ..config import PROJECT_ENDPOINT
    client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )
    return client.get_openai_client()
