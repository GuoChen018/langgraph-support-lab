from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from langgraph_support_lab.graph import _estimate_confidence, build_graph
from langgraph_support_lab.knowledge import LocalRetrievalBackend


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
    weak = [
        {"source_type": "documentation", "relevance": 0.13, "title": "a", "excerpt": "", "url": ""},
        {"source_type": "github_issue", "relevance": 0.05, "title": "b", "excerpt": "", "url": ""},
        {"source_type": "release_note", "relevance": 0.12, "title": "c", "excerpt": "", "url": ""},
    ]
    strong = [
        {"source_type": "documentation", "relevance": 0.3, "title": "a", "excerpt": "", "url": ""},
        {"source_type": "github_issue", "relevance": 0.2, "title": "b", "excerpt": "", "url": ""},
    ]

    assert _estimate_confidence(weak) == "low"
    assert _estimate_confidence(strong) == "high"


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
