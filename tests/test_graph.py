import httpx
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from langgraph_support_lab.graph import _estimate_confidence, build_graph
from langgraph_support_lab.knowledge import LocalRetrievalBackend
from langgraph_support_lab.retrieval.live import LiveRetrievalBackend


def test_complete_issue_returns_response_without_interrupt(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(retrieval_backend=LocalRetrievalBackend())
    config = {"configurable": {"thread_id": "complete-issue"}}

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "After upgrading to langchain 1.0, create_react_agent fails "
                        "with a deprecated API error on python 3.13."
                    )
                )
            ]
        },
        config=config,
    )

    assert result["awaiting_clarification"] is False
    assert result["confidence"] in {"medium", "high"}
    assert "Sources:" in result["response"]
    assert len(result["messages"]) == 2


def test_out_of_corpus_issue_gets_low_confidence(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(retrieval_backend=LocalRetrievalBackend())
    config = {"configurable": {"thread_id": "out-of-corpus"}}

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "How do I configure Redis as a LangGraph checkpointer store on "
                        "Kubernetes with Helm? Error: connection refused on port 6379. "
                        "LangGraph 0.2, Python 3.11."
                    )
                )
            ]
        },
        config=config,
    )

    assert result["awaiting_clarification"] is False
    assert result["confidence"] == "low"
    assert "don't have enough relevant evidence" in result["response"].lower()


def test_estimate_confidence_uses_relevance_not_source_count():
    issue = "LangGraph interrupt fails to resume because thread_id changes"
    weak = [
        {"source_type": "documentation", "relevance": 0.13, "title": "a", "excerpt": "", "url": ""},
        {"source_type": "github_issue", "relevance": 0.05, "title": "b", "excerpt": "", "url": ""},
        {"source_type": "release_note", "relevance": 0.12, "title": "c", "excerpt": "", "url": ""},
    ]
    strong = [
        {
            "source_type": "documentation",
            "relevance": 0.3,
            "title": "Persistence",
            "excerpt": "Reuse the same thread_id to continue a graph.",
            "url": "",
        },
        {
            "source_type": "github_issue",
            "relevance": 0.2,
            "title": "Interrupt resume ignores a changed thread_id",
            "excerpt": "",
            "url": "",
        },
    ]

    assert _estimate_confidence(weak, issue) == "low"
    assert _estimate_confidence(strong, issue) == "high"


def test_estimate_confidence_is_not_high_for_vague_issue_with_unrelated_evidence():
    unrelated = [
        {
            "source_type": "github_issue",
            "relevance": 0.332,
            "title": title,
            "excerpt": "Nothing reaches the aggregated result, so callers see stale data.",
            "url": f"https://github.com/example/repo/issues/{index}",
        }
        for index, title in enumerate(
            [
                "Streaming drops the audio payload",
                "Expose prompt templates to model callbacks",
                "Cache namespace collapses for non-function callables",
            ]
        )
    ]

    confidence = _estimate_confidence(unrelated, "nothing works. why is this so hard??")

    assert confidence != "high"
    assert confidence == "low"


def test_estimate_confidence_requires_query_anchored_evidence_for_high():
    issue = (
        "After upgrading, create_react_agent fails with a deprecated API error "
        "on python 3.13 in production."
    )
    unanchored = [
        {
            "source_type": "documentation",
            "relevance": 0.4,
            "title": "Streaming responses",
            "excerpt": "Stream tokens from chat models in production.",
            "url": "https://example.com/streaming",
        },
        {
            "source_type": "forum",
            "relevance": 0.35,
            "title": "Upgrading to Python 3.13",
            "excerpt": "Reinstall packages after upgrading Python.",
            "url": "https://example.com/forum",
        },
    ]

    assert _estimate_confidence(unanchored, issue) == "medium"


def test_unsupported_issue_terms_still_downgrade_anchored_confidence(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)

    class AnchoredBackend:
        def search(self, query, source_type, *, limit=3):
            if source_type != "documentation":
                return []
            return [
                {
                    "source_type": "documentation",
                    "relevance": relevance,
                    "title": f"create_agent reference {index}",
                    "excerpt": "create_agent builds an agent graph.",
                    "url": f"https://example.com/create-agent-{index}",
                }
                for index, relevance in enumerate([0.35, 0.3])
            ]

    result = build_graph(retrieval_backend=AnchoredBackend()).invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "My create_agent deployment fails with a timeout behind a kubernetes "
                        "ingress gateway. LangChain 1.0, Python 3.13."
                    )
                )
            ]
        }
    )

    assert result["confidence"] == "medium"


def test_vague_complaint_asks_for_details_instead_of_citing_unrelated_issue(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    unrelated_title = "Streaming drops the audio payload, so a streamed turn cannot be continued"

    def handler(request):
        if request.url.path == "/search/issues":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "title": unrelated_title,
                            "body": (
                                "Nothing of the audio reaches the aggregated message. "
                                "Why a guard seems worth it: the failure is silent."
                            ),
                            "state": "open",
                            "labels": [{"name": "bug"}],
                            "html_url": "https://github.com/langchain-ai/langchain/issues/1",
                        }
                    ]
                },
            )
        if request.url.path == "/search.json":
            return httpx.Response(200, json={"topics": [], "posts": []})
        return httpx.Response(200, text="")

    backend = LiveRetrievalBackend(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        docs_indexes=("https://docs.langchain.com/llms.txt",),
        github_repos=("langchain-ai/langchain",),
        forum_base_url="https://forum.langchain.com",
    )
    result = build_graph(retrieval_backend=backend).invoke(
        {"messages": [HumanMessage(content="nothing works. why is this so hard??")]}
    )

    assert result["confidence"] != "high"
    assert unrelated_title not in result["response"]
    assert "try naming the specific" in result["response"].lower()


def test_incomplete_issue_requests_and_accepts_clarification(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(
        checkpointer=InMemorySaver(),
        retrieval_backend=LocalRetrievalBackend(),
    )
    config = {"configurable": {"thread_id": "incomplete-issue"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="My agent behaves strangely.")]},
        config=config,
    )

    assert result["awaiting_clarification"] is True
    assert "i can help investigate this" in result["response"].lower()
    assert "could you share" in result["response"].lower()
    assert "help me separate" in result["response"].lower()
    assert "before i investigate, please provide" not in result["response"].lower()

    resumed = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "LangChain 1.0 on Python 3.13 fails with a create_agent import error."
                    )
                )
            ]
        },
        config=config,
    )

    assert resumed["awaiting_clarification"] is False
    assert "Sources:" in resumed["response"]
    assert len(resumed["messages"]) == 4


def test_complete_issue_searches_and_collects_forum_evidence(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)

    class RecordingBackend:
        def __init__(self):
            self.sources = []

        def search(self, query, source_type, *, limit=3):
            self.sources.append(source_type)
            if source_type != "forum":
                return []
            return [
                {
                    "source_type": "forum",
                    "title": "Solved forum discussion",
                    "excerpt": "A maintainer confirmed the migration path.",
                    "url": "https://forum.langchain.com/t/solved/123",
                    "relevance": 0.25,
                }
            ]

    backend = RecordingBackend()
    graph = build_graph(retrieval_backend=backend)
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "LangChain 1.0 fails with a deprecated create_agent error "
                        "on Python 3.13."
                    )
                )
            ]
        }
    )

    assert set(backend.sources) == {
        "documentation",
        "github_issue",
        "release_note",
        "forum",
    }
    assert result["forum_evidence"][0]["source_type"] == "forum"
    assert result["evidence"] == result["forum_evidence"]


def test_capability_question_explains_learning_and_support_modes(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)

    class NoSearchBackend:
        def search(self, query, source_type, *, limit=3):
            raise AssertionError("Capability questions should not trigger retrieval")

    result = build_graph(retrieval_backend=NoSearchBackend()).invoke(
        {"messages": [HumanMessage(content="What can you do?")]}
    )

    assert result["intent"] == "capabilities"
    assert result["awaiting_clarification"] is False
    assert "Learn LangChain concepts" in result["response"]
    assert "Investigate developer issues" in result["response"]


def test_learning_question_answers_without_requesting_versions(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)

    class LearningBackend:
        def search(self, query, source_type, *, limit=3):
            if source_type != "documentation":
                return []
            return [
                {
                    "source_type": "documentation",
                    "title": "Persistence",
                    "excerpt": (
                        "A checkpointer saves graph state into checkpoints organized by thread."
                    ),
                    "url": "https://docs.langchain.com/oss/python/langgraph/persistence",
                    "relevance": 0.35,
                }
            ]

    graph = build_graph(
        checkpointer=InMemorySaver(),
        retrieval_backend=LearningBackend(),
    )
    config = {"configurable": {"thread_id": "learning-thread"}}
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is a LangGraph checkpointer and how does it relate to threads?"
                    )
                )
            ]
        },
        config=config,
    )

    assert result["intent"] == "learning"
    assert result["awaiting_clarification"] is False
    assert "package versions" not in result["response"].lower()
    assert "available documentation" in result["response"].lower()
    assert "Persistence" in result["response"]

    follow_up = graph.invoke(
        {"messages": [HumanMessage(content="How does that relate to memory?")]},
        config=config,
    )

    assert follow_up["intent"] == "learning"
    assert follow_up["awaiting_clarification"] is False
    assert "Follow-up question" in follow_up["issue"]


def test_answered_issue_retains_context_and_versions_on_follow_up(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(checkpointer=InMemorySaver(), retrieval_backend=LocalRetrievalBackend())
    config = {"configurable": {"thread_id": "async-follow-up"}}
    question = "LangGraph 1.0 on Python 3.12 fails with an event loop error."
    first = graph.invoke({"messages": [HumanMessage(content=question)]}, config=config)
    assert first["awaiting_clarification"] is False

    follow_up = "We call asyncio.run inside an async FastAPI route."
    result = graph.invoke({"messages": [HumanMessage(content=follow_up)]}, config=config)

    assert question in result["issue"]
    assert follow_up in result["issue"]
    assert result["versions"] == ["LangGraph 1.0", "Python 3.12"]
    assert question in result["symptoms"]
    assert result["missing_fields"] == []
    assert result["awaiting_clarification"] is False
    assert "Sources:" in result["response"]


def test_import_follow_up_reaches_search_and_model_with_prior_context(monkeypatch):
    monkeypatch.setenv("MODEL", "test-model")
    queries = []
    model_inputs = []

    class RecordingBackend:
        def search(self, query, source_type, *, limit=3):
            queries.append((source_type, query))
            return [
                {
                    "source_type": source_type,
                    "title": "Agent imports",
                    "excerpt": "create_agent is imported from langchain.agents.",
                    "url": f"https://example.com/{source_type}",
                    "relevance": 0.9,
                }
            ]

    class RecordingModel:
        def invoke(self, messages):
            model_inputs.append(messages)
            return AIMessage(content="Use the documented agent import.")

    monkeypatch.setattr(
        "langgraph_support_lab.graph.init_chat_model", lambda name: RecordingModel()
    )
    graph = build_graph(checkpointer=InMemorySaver(), retrieval_backend=RecordingBackend())
    config = {"configurable": {"thread_id": "import-follow-up"}}
    question = (
        "My create_agent import from langgraph.prebuilt fails with an import error "
        "after an old tutorial. LangChain 1.0, Python 3.13."
    )
    graph.invoke({"messages": [HumanMessage(content=question)]}, config=config)
    queries.clear()
    model_inputs.clear()
    follow_up = "Is it the right package?"
    result = graph.invoke({"messages": [HumanMessage(content=follow_up)]}, config=config)

    assert result["awaiting_clarification"] is False
    assert {source for source, _ in queries} == {
        "documentation",
        "github_issue",
        "release_note",
        "forum",
    }
    assert all(question in query and follow_up in query for _, query in queries)
    assert len(model_inputs) == 1
    user_input = model_inputs[0][-1][1]
    assert question in user_input
    assert follow_up in user_input


def test_explicit_topic_change_clears_prior_issue_and_versions(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(checkpointer=InMemorySaver(), retrieval_backend=LocalRetrievalBackend())
    config = {"configurable": {"thread_id": "topic-change"}}
    graph.invoke(
        {"messages": [HumanMessage(content="LangGraph 1.0 fails with an event loop error.")]},
        config=config,
    )
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content="New topic: My deployment fails with a timeout error.")
            ]
        },
        config=config,
    )

    assert "event loop" not in result["issue"]
    assert result["versions"] == []
    assert result["awaiting_clarification"] is True
    assert result["missing_fields"] == ["relevant LangChain, LangGraph, and Python versions"]


def test_partial_clarifications_request_only_remaining_details(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(checkpointer=InMemorySaver(), retrieval_backend=LocalRetrievalBackend())
    config = {"configurable": {"thread_id": "partial-clarification"}}
    first = graph.invoke(
        {"messages": [HumanMessage(content="My agent behaves strangely.")]}, config=config
    )
    assert len(first["missing_fields"]) == 2
    partial = graph.invoke(
        {"messages": [HumanMessage(content="LangGraph 1.0 on Python 3.12.")]}, config=config
    )
    assert partial["awaiting_clarification"] is True
    assert partial["missing_fields"] == ["the observed error or incorrect behavior"]
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content="It fails with an event loop error, also on Python 3.13.")
            ]
        },
        config=config,
    )
    assert result["awaiting_clarification"] is False
    assert result["versions"] == ["LangGraph 1.0", "Python 3.12", "Python 3.13"]
    assert result["missing_fields"] == []
