"""Foundry IQ — grounded, cited knowledge retrieval.

LOCAL mode: keyword search over docs/ returning snippets + filename citations,
so the repo runs and demonstrates grounding without Azure.

FOUNDRY mode (TODO): call an Azure AI Search knowledge base via the Foundry IQ
knowledge-base API / MCP tool. See BUILD_STEPS/03 and the Microsoft Learn MCP
(`microsoft_docs_search "Foundry IQ knowledge base agentic retrieval"`).
"""
from __future__ import annotations
from dataclasses import dataclass

from ..config import DOCS, MODE, SEARCH_ENDPOINT, KNOWLEDGE_BASE, SEARCH_API_KEY


@dataclass
class Citation:
    source: str          # document / URL
    snippet: str


@dataclass
class GroundedResult:
    answer: str
    citations: list[Citation]

    @property
    def is_grounded(self) -> bool:
        return len(self.citations) > 0


def retrieve(query: str, k: int = 3) -> GroundedResult:
    """Return grounded snippets for a query. Always cite or say 'I don't know'."""
    if MODE == "foundry":
        return _retrieve_foundry(query, k)
    return _retrieve_local(query, k)


_DOC_CACHE: dict[str, list[tuple[str, str]]] | None = None  # {doc_name: [(para, para), ...]}

def _load_doc_cache() -> dict[str, list[str]]:
    global _DOC_CACHE
    if _DOC_CACHE is None:
        _DOC_CACHE = {}
        for doc in sorted(DOCS.glob("*.md")):
            text = doc.read_text(encoding="utf-8")
            _DOC_CACHE[doc.name] = [p.strip() for p in text.split("\n\n") if p.strip()]
    return _DOC_CACHE


def _retrieve_local(query: str, k: int) -> GroundedResult:
    terms = {t.lower() for t in query.split() if len(t) > 2}
    hits: list[tuple[int, Citation]] = []
    for doc_name, paras in _load_doc_cache().items():
        for para in paras:
            score = sum(para.lower().count(t) for t in terms)
            if score:
                hits.append((score, Citation(source=doc_name, snippet=para[:400])))
    hits.sort(key=lambda h: h[0], reverse=True)
    top = [c for _, c in hits[:k]]
    if not top:
        return GroundedResult(answer="I don't know — not found in the knowledge base.", citations=[])
    answer = " ".join(c.snippet for c in top)
    return GroundedResult(answer=answer, citations=top)


def _decode_parent_id(result: dict) -> str | None:
    """Decode the Base64 blob URL stored in parent_id by the RAG wizard indexer."""
    import base64, re
    raw = result.get("parent_id", "")
    if not raw:
        return None
    try:
        # Azure Search appends a single trailing byte that makes length ≡ 1 (mod 4) — strip it
        if len(raw) % 4 == 1:
            raw = raw[:-1]
        padding = (4 - len(raw) % 4) % 4
        decoded = base64.b64decode((raw + "=" * padding).encode()).decode("utf-8", errors="ignore")
        if not decoded.startswith("http"):
            return None
        # Trim trailing bytes after the file extension (base64 artifacts)
        m = re.match(r'(.*\.[a-zA-Z]{2,4})', decoded)
        return m.group(1) if m else decoded
    except Exception:
        return None


def _retrieve_foundry(query: str, k: int) -> GroundedResult:
    try:
        from azure.search.documents import SearchClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        return _retrieve_local(query, k)

    if not SEARCH_ENDPOINT or not KNOWLEDGE_BASE:
        return GroundedResult(
            answer="I don't know — knowledge base not configured.", citations=[]
        )

    if SEARCH_API_KEY:
        from azure.core.credentials import AzureKeyCredential
        credential = AzureKeyCredential(SEARCH_API_KEY)
    else:
        credential = DefaultAzureCredential()
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=KNOWLEDGE_BASE,
        credential=credential,
    )
    results = list(client.search(search_text=query, top=k))
    citations: list[Citation] = []
    for r in results:
        # RAG wizard index uses: chunk (text), title (filename), parent_id (b64 blob URL)
        snippet = (r.get("chunk") or r.get("content") or "")[:400]
        if not snippet:
            continue
        source = _decode_parent_id(r) or r.get("title") or r.get("id", "unknown")
        citations.append(Citation(source=source, snippet=snippet))

    if not citations:
        return GroundedResult(
            answer="I don't know — not found in the knowledge base.", citations=[]
        )
    return GroundedResult(answer=" ".join(c.snippet for c in citations), citations=citations)
