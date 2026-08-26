import httpx

from langgraph_support_lab import knowledge
from langgraph_support_lab.knowledge import LocalRetrievalBackend, search_knowledge
from langgraph_support_lab.retrieval.live import LiveRetrievalBackend


def test_search_returns_relevant_documentation():
    results = search_knowledge(
        "create_react_agent is deprecated after my v1 upgrade",
        "documentation",
        backend=LocalRetrievalBackend(),
    )

    assert results
    assert results[0]["title"] == "LangChain v1 migration guide"
    assert results[0]["relevance"] > 0


def test_search_returns_empty_for_unrelated_query():
    results = search_knowledge(
        "quantum banana accounting",
        "release_note",
        backend=LocalRetrievalBackend(),
    )

    assert results == []


def test_live_docs_fetches_ranked_markdown_and_caches_requests():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if request.url.path.endswith("llms.txt"):
            return httpx.Response(
                200,
                text=(
                    "- [LangGraph persistence]"
                    "(https://docs.langchain.com/oss/python/langgraph/persistence): "
                    "Save and resume graph state with checkpointers and thread IDs."
                ),
            )
        if request.url.path.endswith("persistence.md"):
            return httpx.Response(
                200,
                text=(
                    "# Persistence\n\nA checkpointer saves graph state. "
                    "Reuse the same thread_id when resuming an interrupted graph."
                ),
            )
        return httpx.Response(404)

    backend = LiveRetrievalBackend(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        docs_indexes=("https://docs.langchain.com/oss/python/langgraph/llms.txt",),
    )
    first = backend.search(
        "LangGraph interrupt fails to resume because thread_id changes",
        "documentation",
    )
    second = backend.search(
        "LangGraph interrupt fails to resume because thread_id changes",
        "documentation",
    )

    assert first == second
    assert first[0]["title"] == "LangGraph persistence"
    assert first[0]["url"].endswith("/persistence")
    assert "thread_id" in first[0]["excerpt"]
    assert 0 < first[0]["relevance"] <= 0.5
    assert len(calls) == 2


def test_live_github_search_maps_real_issue_results():
    def handler(request):
        assert request.url.path == "/search/issues"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "title": "Resume starts a new run with a changed thread ID",
                        "body": "The graph resumes correctly when the original thread_id is reused.",
                        "state": "closed",
                        "labels": [{"name": "bug"}],
                        "html_url": "https://github.com/langchain-ai/langgraph/issues/123",
                    }
                ]
            },
        )

    backend = LiveRetrievalBackend(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        github_repos=("langchain-ai/langgraph",),
    )
    results = backend.search(
        "LangGraph resume starts a new run when thread_id changes",
        "github_issue",
    )

    assert results[0]["source_type"] == "github_issue"
    assert results[0]["url"].endswith("/issues/123")
    assert "State: closed" in results[0]["excerpt"]


def test_live_forum_fetches_full_topic_and_prioritizes_accepted_answer():
    def handler(request):
        if request.url.path == "/search.json":
            return httpx.Response(
                200,
                json={
                    "topics": [
                        {
                            "id": 42,
                            "slug": "resume-interrupt",
                            "title": "How to resume a LangGraph interrupt",
                        }
                    ],
                    "posts": [
                        {
                            "topic_id": 42,
                            "post_number": 1,
                            "blurb": "My graph starts over when I resume it.",
                        }
                    ],
                },
            )
        if request.url.path == "/t/42.json":
            return httpx.Response(
                200,
                json={
                    "title": "How to resume a LangGraph interrupt",
                    "slug": "resume-interrupt",
                    "post_stream": {
                        "posts": [
                            {
                                "post_number": 1,
                                "cooked": "<p>My graph starts over after an interrupt.</p>",
                            },
                            {
                                "post_number": 2,
                                "accepted_answer": True,
                                "staff": True,
                                "cooked": (
                                    "<p>Reuse the original <code>thread_id</code> "
                                    "with Command(resume=...).</p>"
                                ),
                            },
                        ]
                    },
                },
            )
        return httpx.Response(404)

    backend = LiveRetrievalBackend(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        forum_base_url="https://forum.langchain.com",
    )
    results = backend.search(
        "LangGraph interrupt resume starts over thread_id",
        "forum",
    )

    assert results[0]["source_type"] == "forum"
    assert results[0]["excerpt"].startswith("Accepted answer available.")
    assert "thread_id" in results[0]["excerpt"]
    assert results[0]["url"].endswith("/t/resume-interrupt/42/1")


def test_hybrid_mode_falls_back_to_local_corpus(monkeypatch):
    class FailingBackend:
        def search(self, query, source_type, *, limit=3):
            raise httpx.ConnectError("source unavailable")

    monkeypatch.setenv("RETRIEVAL_MODE", "hybrid")
    monkeypatch.setattr(knowledge, "_live_backend", lambda: FailingBackend())

    results = search_knowledge(
        "create_react_agent is deprecated after my v1 upgrade",
        "documentation",
    )

    assert results[0]["title"] == "LangChain v1 migration guide"
