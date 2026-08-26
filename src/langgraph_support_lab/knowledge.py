from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from httpx import HTTPError

from langgraph_support_lab.state import Evidence

DEFAULT_KNOWLEDGE_PATH = Path(__file__).parents[2] / "data" / "knowledge.json"
logger = logging.getLogger(__name__)


class RetrievalBackend(Protocol):
    def search(self, query: str, source_type: str, *, limit: int = 3) -> list[Evidence]: ...


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_.-]+", text.lower()))


def _search_local(
    query: str,
    source_type: str,
    *,
    limit: int = 3,
    path: Path = DEFAULT_KNOWLEDGE_PATH,
) -> list[Evidence]:
    """Search the local starter corpus using transparent keyword overlap."""
    corpus = json.loads(path.read_text())
    query_tokens = _tokens(query)
    scored: list[Evidence] = []

    for item in corpus.get(source_type, []):
        searchable = " ".join(
            [item["title"], item["excerpt"], " ".join(item.get("keywords", []))]
        )
        item_tokens = _tokens(searchable)
        overlap = query_tokens & item_tokens
        if not overlap:
            continue

        score = len(overlap) / max(1, len(query_tokens))
        scored.append(
            {
                "source_type": source_type,
                "title": item["title"],
                "excerpt": item["excerpt"],
                "url": item["url"],
                "relevance": round(score, 3),
            }
        )

    return sorted(scored, key=lambda item: item["relevance"], reverse=True)[:limit]


class LocalRetrievalBackend:
    def __init__(self, path: Path = DEFAULT_KNOWLEDGE_PATH) -> None:
        self.path = path

    def search(self, query: str, source_type: str, *, limit: int = 3) -> list[Evidence]:
        return _search_local(query, source_type, limit=limit, path=self.path)


@lru_cache(maxsize=1)
def _live_backend() -> RetrievalBackend:
    from langgraph_support_lab.retrieval import LiveRetrievalBackend

    return LiveRetrievalBackend()


def search_knowledge(
    query: str,
    source_type: str,
    *,
    limit: int = 3,
    path: Path = DEFAULT_KNOWLEDGE_PATH,
    backend: RetrievalBackend | None = None,
) -> list[Evidence]:
    """Search live sources with a deterministic local fallback.

    `RETRIEVAL_MODE=hybrid` is the normal development default. Tests and
    offline runs can inject `LocalRetrievalBackend` or set the mode to `local`.
    """

    if backend is not None:
        return backend.search(query, source_type, limit=limit)

    mode = os.getenv("RETRIEVAL_MODE", "hybrid").lower()
    if mode not in {"local", "live", "hybrid"}:
        raise ValueError("RETRIEVAL_MODE must be one of: local, live, hybrid")
    if mode == "local":
        return _search_local(query, source_type, limit=limit, path=path)

    try:
        results = _live_backend().search(query, source_type, limit=limit)
        if results or mode == "live":
            return results
    except (HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.warning("Live %s retrieval failed: %s", source_type, exc)
        if mode == "live":
            return []

    return _search_local(query, source_type, limit=limit, path=path)
