from __future__ import annotations

import html
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

import httpx

from langgraph_support_lab.state import Evidence

logger = logging.getLogger(__name__)

DEFAULT_DOCS_INDEXES = (
    "https://docs.langchain.com/oss/python/llms.txt",
    "https://docs.langchain.com/oss/python/langchain/llms.txt",
    "https://docs.langchain.com/oss/python/langgraph/llms.txt",
    "https://docs.langchain.com/oss/python/releases/llms.txt",
    "https://docs.langchain.com/oss/python/migrate/llms.txt",
    "https://docs.langchain.com/oss/javascript/llms.txt",
    "https://docs.langchain.com/langsmith/llms.txt",
)
DEFAULT_GITHUB_REPOS = ("langchain-ai/langchain", "langchain-ai/langgraph")
STOP_WORDS = {
    "a",
    "after",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "can",
    "do",
    "does",
    "error",
    "failed",
    "fails",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "langchain",
    "langgraph",
    "langsmith",
    "my",
    "new",
    "of",
    "on",
    "or",
    "python",
    "run",
    "starts",
    "the",
    "this",
    "to",
    "using",
    "what",
    "when",
    "with",
    "changes",
}


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_.-]+", text.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def _relevance(query: str, searchable: str, *, boost: float = 0.0) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    overlap = query_tokens & _tokens(searchable)
    if not overlap:
        return 0.0
    coverage = len(overlap) / min(max(len(query_tokens), 1), 10)
    return round(min(0.5, 0.08 + coverage * 0.42 + boost), 3)


def _expand_docs_query(query: str) -> str:
    lower = query.lower()
    additions: list[str] = []
    if re.search(r"\b1(?:\.0|\.x)\b", lower):
        if "langchain" in lower:
            additions.append("langchain-v1")
        if "langgraph" in lower:
            additions.append("langgraph-v1")
    if any(term in lower for term in ("interrupt", "resume", "thread_id", "checkpoint")):
        additions.extend(["persistence", "checkpoint", "interrupts", "resume", "thread_id"])
    if any(term in lower for term in ("deprecated", "upgrade", "migration")):
        additions.extend(["migration", "release", "deprecated", "changelog"])
    if "create_react_agent" in lower:
        additions.extend(["create_agent", "agents", "langchain-v1"])
    if "import" in lower:
        additions.extend(["migration", "compatibility", "install"])
    return " ".join([query, *additions])


def _source_search_terms(query: str, *, limit: int = 4) -> str:
    ordered = [
        token
        for token in re.findall(r"[a-zA-Z0-9_.-]+", query.lower())
        if len(token) > 1 and token not in STOP_WORDS
    ]
    priority_terms = {
        "agentexecutor",
        "checkpoint",
        "create_agent",
        "create_react_agent",
        "deprecated",
        "interrupt",
        "migration",
        "resume",
        "streaming",
        "thread_id",
    }

    def priority(item: tuple[int, str]) -> tuple[int, int]:
        index, token = item
        if "_" in token or token in priority_terms:
            weight = 3
        elif token in {"langchain", "langgraph", "langsmith"}:
            weight = 2
        elif any(character.isdigit() for character in token):
            weight = 1
        else:
            weight = 0
        return (-weight, index)

    selected: list[str] = []
    for _, token in sorted(enumerate(ordered), key=priority):
        if token not in selected:
            selected.append(token)
        if len(selected) == limit:
            break
    return " ".join(f'"{token}"' if "_" in token else token for token in selected)


def _query_anchors(query: str) -> set[str]:
    anchor_terms = {
        "agentexecutor",
        "checkpoint",
        "create_agent",
        "create_react_agent",
        "deprecated",
        "interrupt",
        "migration",
        "resume",
        "thread_id",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_.-]+", query.lower())
        if "_" in token or token in anchor_terms
    }


def _title_key_terms(query: str) -> set[str]:
    return {
        token
        for token in _tokens(query)
        if not re.fullmatch(r"\d+(?:\.\d+)*", token)
        and token not in {"api", "agent", "graph", "issue", "version"}
    }


def _identifier_in_title(anchors: set[str], title: str) -> bool:
    identifiers = anchors & {"agentexecutor", "create_agent", "create_react_agent"}
    if not identifiers:
        return True
    normalized_title = re.sub(r"[\s-]+", "_", title.lower())
    return any(anchor in normalized_title for anchor in identifiers)


def _identifiers_present(anchors: set[str], text: str) -> bool:
    identifiers = anchors & {"agentexecutor", "create_agent", "create_react_agent"}
    if not identifiers:
        return True
    normalized_text = re.sub(r"[\s-]+", "_", text.lower())
    return any(identifier in normalized_text for identifier in identifiers)


def _best_excerpt(text: str, query: str, *, limit: int = 900) -> str:
    cleaned = re.sub(r"(?m)^---\s*$.*?^---\s*$", "", text, count=1, flags=re.DOTALL)
    cleaned = re.sub(r"</?[A-Z][^>]*>", "", cleaned)
    blocks = [
        re.sub(r"\s+", " ", block).strip()
        for block in re.split(r"\n\s*\n", cleaned)
        if block.strip()
    ]
    ranked = sorted(
        blocks,
        key=lambda block: (_relevance(query, block), len(block) <= limit),
        reverse=True,
    )
    selected = [block for block in ranked if _relevance(query, block) > 0][:2]
    excerpt = " ".join(selected or blocks[:1])
    return excerpt[:limit].rstrip()


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        elif not self._ignored_depth and tag in {"p", "li", "blockquote", "br", "pre"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif not self._ignored_depth and tag in {"p", "li", "blockquote", "pre"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", html.unescape("".join(self.parts))).strip()


def _html_to_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return parser.text()


@dataclass
class _CacheEntry:
    content: bytes
    headers: dict[str, str]
    expires_at: float
    stale_until: float


@dataclass
class _Payload:
    content: bytes
    stale: bool = False

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.content)


class LiveRetrievalBackend:
    """Fetch current public LangChain evidence with bounded, stale-safe caching."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        docs_indexes: tuple[str, ...] | None = None,
        github_repos: tuple[str, ...] | None = None,
        forum_base_url: str | None = None,
        cache_ttl_seconds: float | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        timeout = timeout_seconds or float(os.getenv("RETRIEVAL_HTTP_TIMEOUT_SECONDS", "10"))
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(timeout, connect=min(3.0, timeout)),
            follow_redirects=True,
            headers={"User-Agent": "langgraph-support-lab/0.1"},
        )
        configured_indexes = os.getenv("DOCS_INDEX_URLS")
        self._docs_indexes = docs_indexes or (
            tuple(url.strip() for url in configured_indexes.split(",") if url.strip())
            if configured_indexes
            else DEFAULT_DOCS_INDEXES
        )
        configured_repos = os.getenv("GITHUB_REPOSITORIES")
        self._github_repos = github_repos or (
            tuple(repo.strip() for repo in configured_repos.split(",") if repo.strip())
            if configured_repos
            else DEFAULT_GITHUB_REPOS
        )
        self._forum_base_url = (
            forum_base_url or os.getenv("FORUM_BASE_URL", "https://forum.langchain.com")
        ).rstrip("/")
        self._cache_ttl = cache_ttl_seconds or float(
            os.getenv("RETRIEVAL_CACHE_TTL_SECONDS", "300")
        )
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_lock = threading.Lock()

    def search(self, query: str, source_type: str, *, limit: int = 3) -> list[Evidence]:
        if source_type in {"documentation", "release_note"}:
            return self.search_docs(query, source_type=source_type, limit=limit)
        if source_type == "github_issue":
            return self.search_github(query, limit=limit)
        if source_type == "forum":
            return self.search_forum(query, limit=limit)
        raise ValueError(f"Unsupported live source type: {source_type}")

    def _request(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        ttl: float | None = None,
        stale_ttl: float = 43_200,
    ) -> _Payload:
        request = self._client.build_request("GET", url, params=params)
        key = str(request.url)
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached and cached.expires_at > now:
                return _Payload(cached.content)

        request_headers = dict(headers or {})
        if cached:
            if etag := cached.headers.get("etag"):
                request_headers["If-None-Match"] = etag
            if modified := cached.headers.get("last-modified"):
                request_headers["If-Modified-Since"] = modified

        try:
            response = self._client.get(url, params=params, headers=request_headers)
            if response.status_code == 304 and cached:
                cached.expires_at = now + (ttl or self._cache_ttl)
                return _Payload(cached.content)
            response.raise_for_status()
            max_bytes = 2_000_000
            content = response.content[:max_bytes]
            entry = _CacheEntry(
                content=content,
                headers={key.lower(): value for key, value in response.headers.items()},
                expires_at=now + (ttl or self._cache_ttl),
                stale_until=now + stale_ttl,
            )
            with self._cache_lock:
                self._cache[key] = entry
            return _Payload(content)
        except (httpx.HTTPError, json.JSONDecodeError):
            if cached and cached.stale_until > now:
                logger.warning("Serving stale retrieval response for %s", key)
                return _Payload(cached.content, stale=True)
            raise

    def search_docs(
        self,
        query: str,
        *,
        source_type: str = "documentation",
        limit: int = 3,
    ) -> list[Evidence]:
        candidates: dict[str, tuple[str, str, float]] = {}
        if source_type == "release_note" and not any(
            term in query.lower()
            for term in ("changelog", "deprecated", "import", "migrat", "release", "upgrad")
        ):
            return []
        expanded_query = _expand_docs_query(query)
        anchors = _query_anchors(query)
        for index_url in self._docs_indexes:
            payload = self._request(index_url, ttl=1_800, stale_ttl=86_400)
            for match in re.finditer(r"\[([^\]]+)]\((https?://[^)]+)\)(?::\s*([^\n]+))?", payload.text):
                title, url, description = match.group(1), match.group(2), match.group(3) or ""
                path = httpx.URL(url).path.lower()
                path_boost = 0.0
                if source_type == "documentation" and any(
                    term in path for term in ("release", "migrate", "changelog")
                ):
                    continue
                if (
                    source_type == "documentation"
                    and "integration" not in query.lower()
                    and "/integrations/" in path
                ):
                    continue
                if (
                    source_type == "documentation"
                    and "deprecated" in query.lower()
                    and "/integrations/" in path
                ):
                    path_boost = -0.1
                if source_type == "release_note":
                    if not any(term in path for term in ("release", "migrate", "changelog")):
                        continue
                    path_boost = (
                        0.12 if any(term in path for term in ("release", "migrate")) else 0.0
                    )
                base_score = _relevance(expanded_query, f"{title} {description} {path}")
                score = round(min(0.5, max(0.0, base_score + path_boost)), 3)
                if score > 0 and (url not in candidates or score > candidates[url][2]):
                    candidates[url] = (title, description, score)

        evidence: list[Evidence] = []
        for url, (title, description, initial_score) in sorted(
            candidates.items(), key=lambda item: item[1][2], reverse=True
        )[: max(limit * 2, 4)]:
            try:
                markdown_url = url if httpx.URL(url).path.endswith(".md") else f"{url}.md"
                page = self._request(markdown_url, ttl=900, stale_ttl=86_400)
            except httpx.HTTPError:
                logger.warning("Unable to fetch documentation page %s", url)
                continue
            page_text = page.text
            if re.search(r"<(?:!doctype\s+html|html)\b", page_text[:500], re.IGNORECASE):
                page_text = _html_to_text(page_text)
            if not _identifiers_present(anchors, page_text):
                continue
            excerpt = _best_excerpt(page_text, query)
            score = max(initial_score, _relevance(query, f"{title} {description} {excerpt}"))
            if score < 0.2:
                continue
            canonical_url = re.sub(r"\.md$", "", url)
            evidence.append(
                {
                    "source_type": source_type,
                    "title": title,
                    "excerpt": excerpt or description,
                    "url": canonical_url,
                    "relevance": score,
                }
            )
        return sorted(evidence, key=lambda item: item["relevance"], reverse=True)[:limit]

    def search_github(self, query: str, *, limit: int = 3) -> list[Evidence]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token := os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
        terms = _source_search_terms(query)
        anchors = _query_anchors(query)
        title_terms = _title_key_terms(query)
        candidates: dict[str, Evidence] = {}

        for repo in self._github_repos:
            payload = self._request(
                "https://api.github.com/search/issues",
                params={"q": f"{terms} repo:{repo} is:issue", "per_page": min(limit * 3, 20)},
                headers=headers,
                ttl=120,
                stale_ttl=3_600,
            )
            for item in payload.json().get("items", []):
                body = item.get("body") or ""
                title = item.get("title") or "Untitled issue"
                labels = ", ".join(label.get("name", "") for label in item.get("labels", []))
                if not _identifier_in_title(anchors, title):
                    continue
                normalized_title = re.sub(r"[\s-]+", "_", title.lower())
                if title_terms and not any(
                    term in normalized_title or term.replace("_", " ") in title.lower()
                    for term in title_terms
                ):
                    continue
                searchable = f"{title} {body} {labels}".lower()
                required_anchor_count = min(2, len(anchors))
                if anchors and sum(anchor in searchable for anchor in anchors) < required_anchor_count:
                    continue
                excerpt_body = _best_excerpt(body, query, limit=700)
                excerpt = (
                    f"State: {item.get('state', 'unknown')}. "
                    f"Labels: {labels or 'none'}. {excerpt_body}"
                ).strip()
                title_boost = 0.1 if any(anchor in title.lower() for anchor in anchors) else 0.0
                score = _relevance(query, searchable, boost=title_boost)
                if item.get("state") == "closed":
                    score = min(0.5, round(score + 0.03, 3))
                url = item.get("html_url")
                if not url or score <= 0:
                    continue
                candidate: Evidence = {
                    "source_type": "github_issue",
                    "title": title,
                    "excerpt": excerpt,
                    "url": url,
                    "relevance": score,
                }
                if url not in candidates or score > candidates[url]["relevance"]:
                    candidates[url] = candidate

        return sorted(candidates.values(), key=lambda item: item["relevance"], reverse=True)[:limit]

    def search_forum(self, query: str, *, limit: int = 3) -> list[Evidence]:
        payload = self._request(
            f"{self._forum_base_url}/search.json",
            params={"q": _source_search_terms(query), "page": 0},
            ttl=120,
            stale_ttl=43_200,
        )
        search_data = payload.json()
        anchors = _query_anchors(query)
        topics = {topic["id"]: topic for topic in search_data.get("topics", [])}
        ranked_topics: dict[int, tuple[float, int]] = {}

        for post in search_data.get("posts", []):
            topic_id = post.get("topic_id")
            if topic_id is None:
                continue
            topic = topics.get(topic_id, {})
            score = _relevance(query, f"{topic.get('title', '')} {post.get('blurb', '')}")
            existing = ranked_topics.get(topic_id)
            if score > 0 and (existing is None or score > existing[0]):
                ranked_topics[topic_id] = (score, post.get("post_number", 1))

        evidence: list[Evidence] = []
        for topic_id, (initial_score, matched_post_number) in sorted(
            ranked_topics.items(), key=lambda item: item[1][0], reverse=True
        )[: max(limit * 2, 4)]:
            try:
                topic_data = self._request(
                    f"{self._forum_base_url}/t/{topic_id}.json",
                    ttl=300,
                    stale_ttl=43_200,
                ).json()
            except httpx.HTTPError:
                logger.warning("Unable to fetch forum topic %s", topic_id)
                continue
            posts = topic_data.get("post_stream", {}).get("posts", [])
            if not posts:
                continue
            preferred = sorted(
                posts,
                key=lambda post: (
                    bool(post.get("accepted_answer") or post.get("topic_accepted_answer")),
                    bool(post.get("staff") or post.get("admin") or post.get("moderator")),
                    post.get("post_number") == matched_post_number,
                ),
                reverse=True,
            )
            excerpts: list[str] = []
            for post in preferred:
                text = _html_to_text(post.get("cooked") or "")
                excerpt = _best_excerpt(text, query, limit=600)
                if excerpt and excerpt not in excerpts:
                    excerpts.append(excerpt)
                if len(excerpts) == 2:
                    break
            title = topic_data.get("title") or topics.get(topic_id, {}).get("title", "Forum topic")
            if not _identifier_in_title(anchors, title):
                continue
            searchable = f"{title} {' '.join(excerpts)}".lower()
            if anchors and not any(anchor in searchable for anchor in anchors):
                continue
            accepted = any(
                post.get("accepted_answer") or post.get("topic_accepted_answer") for post in posts
            )
            title_boost = 0.1 if any(anchor in title.lower() for anchor in anchors) else 0.0
            score = max(initial_score, _relevance(query, searchable, boost=title_boost))
            if accepted:
                score = min(0.5, round(score + 0.05, 3))
            slug = topic_data.get("slug") or topics.get(topic_id, {}).get("slug", "topic")
            evidence.append(
                {
                    "source_type": "forum",
                    "title": title,
                    "excerpt": (
                        f"{'Accepted answer available. ' if accepted else ''}{' '.join(excerpts)}"
                    ).strip(),
                    "url": f"{self._forum_base_url}/t/{slug}/{topic_id}/{matched_post_number}",
                    "relevance": score,
                }
            )
        return sorted(evidence, key=lambda item: item["relevance"], reverse=True)[:limit]
