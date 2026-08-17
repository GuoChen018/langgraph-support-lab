from langgraph_support_lab.knowledge import search_knowledge


def test_search_returns_relevant_documentation():
    results = search_knowledge(
        "create_react_agent is deprecated after my v1 upgrade",
        "documentation",
    )

    assert results
    assert results[0]["title"] == "LangChain v1 migration guide"
    assert results[0]["relevance"] > 0


def test_search_returns_empty_for_unrelated_query():
    results = search_knowledge("quantum banana accounting", "release_note")

    assert results == []
