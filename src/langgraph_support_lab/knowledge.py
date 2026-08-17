from __future__ import annotations

import json
import re
from pathlib import Path

from langgraph_support_lab.state import Evidence

DEFAULT_KNOWLEDGE_PATH = Path(__file__).parents[2] / "data" / "knowledge.json"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_.-]+", text.lower()))


def search_knowledge(
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

    for item in corpus[source_type]:
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
