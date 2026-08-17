from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from langgraph_support_lab.graph import _estimate_confidence, build_graph


def test_complete_issue_returns_response_without_interrupt(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph()
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
    graph = build_graph()
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
    assert "insufficient" in result["response"].lower() or "does not" in result["response"].lower()


def test_estimate_confidence_uses_relevance_not_source_count():
    weak = [
        {"source_type": "documentation", "relevance": 0.13, "title": "a", "excerpt": "", "url": ""},
        {"source_type": "github_issue", "relevance": 0.05, "title": "b", "excerpt": "", "url": ""},
        {"source_type": "release_note", "relevance": 0.12, "title": "c", "excerpt": "", "url": ""},
    ]
    strong = [
        {"source_type": "documentation", "relevance": 0.25, "title": "a", "excerpt": "", "url": ""},
        {"source_type": "github_issue", "relevance": 0.2, "title": "b", "excerpt": "", "url": ""},
    ]

    assert _estimate_confidence(weak) == "low"
    assert _estimate_confidence(strong) == "high"


def test_incomplete_issue_requests_and_accepts_clarification(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "incomplete-issue"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="My agent behaves strangely.")]},
        config=config,
    )

    assert result["awaiting_clarification"] is True
    assert "please provide" in result["response"].lower()

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
