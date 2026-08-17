from __future__ import annotations

import os
import re
from collections.abc import Callable

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from langgraph_support_lab.knowledge import search_knowledge
from langgraph_support_lab.state import Evidence, SupportState


def _extract_versions(text: str) -> list[str]:
    patterns = [
        r"\b(?:langchain|langgraph|langsmith)[=<>~! ]+[vV]?\d+(?:\.\d+){0,2}\b",
        r"\bpython[=<>~! ]+[vV]?\d+(?:\.\d+){0,2}\b",
    ]
    return [
        match.group(0)
        for pattern in patterns
        for match in re.finditer(pattern, text, flags=re.IGNORECASE)
    ]


def _message_text(message: BaseMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    return " ".join(
        block.get("text", "")
        for block in message.content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def inspect_intake(state: SupportState) -> SupportState:
    latest_human = next(
        (
            _message_text(message)
            for message in reversed(state["messages"])
            if isinstance(message, HumanMessage)
        ),
        "",
    )
    if state.get("awaiting_clarification"):
        issue = f"{state.get('issue', '')}\n\nAdditional information:\n{latest_human}"
    else:
        issue = latest_human

    lower = issue.lower()
    versions = _extract_versions(issue)
    missing: list[str] = []

    if not any(word in lower for word in ["error", "fails", "failed", "wrong", "deprecated"]):
        missing.append("the observed error or incorrect behavior")
    if not versions:
        missing.append("relevant LangChain, LangGraph, and Python versions")

    return {
        "issue": issue,
        "versions": versions,
        "symptoms": [line.strip() for line in issue.splitlines() if line.strip()],
        "missing_fields": [] if state.get("awaiting_clarification") else missing,
        "awaiting_clarification": False,
        "documentation_evidence": [],
        "github_evidence": [],
        "release_evidence": [],
        "evidence": [],
    }


def route_after_intake(state: SupportState) -> str | list[str]:
    if state.get("missing_fields"):
        return "ask_clarification"
    return ["search_docs", "search_issues", "search_releases"]


def ask_clarification(state: SupportState) -> SupportState:
    missing = ", ".join(state["missing_fields"])
    question = f"Before I investigate, please provide {missing}."
    return {
        "messages": [AIMessage(content=question)],
        "response": question,
        "awaiting_clarification": True,
    }


def _search_node(
    source_type: str,
    state_field: str,
) -> Callable[[SupportState], SupportState]:
    def search(state: SupportState) -> SupportState:
        return {
            state_field: search_knowledge(state["issue"], source_type),
        }

    return search


def _collect_evidence(state: SupportState) -> list[Evidence]:
    return (
        state.get("documentation_evidence", [])
        + state.get("github_evidence", [])
        + state.get("release_evidence", [])
    )


def _estimate_confidence(evidence: list[Evidence]) -> str:
    """Score confidence from evidence relevance, not from source-type count.

    Weak keyword hits across many sources previously produced false "high"
    confidence for out-of-corpus questions (e.g. Redis/Helm).
    """
    if not evidence:
        return "low"

    ranked = sorted(
        (item["relevance"] for item in evidence),
        reverse=True,
    )
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else 0.0

    if best >= 0.2 and second >= 0.1:
        return "high"
    if best >= 0.18:
        return "medium"
    return "low"


def _deterministic_diagnosis(evidence: list[Evidence]) -> tuple[str, str]:
    confidence = _estimate_confidence(evidence)
    if not evidence or confidence == "low":
        return (
            (
                "The available local knowledge does not strongly support a diagnosis. "
                "Evidence is missing, weak, or only loosely related to the question. "
                "Ask for more detail or consult official docs before applying a fix."
            ),
            "low",
        )

    strongest = sorted(evidence, key=lambda item: item["relevance"], reverse=True)[:3]
    findings = "; ".join(f"{item['title']}: {item['excerpt']}" for item in strongest)
    return f"The strongest evidence suggests: {findings}", confidence


def synthesize(state: SupportState) -> SupportState:
    evidence = _collect_evidence(state)
    confidence = _estimate_confidence(evidence)
    model_name = os.getenv("MODEL")

    if model_name:
        model = init_chat_model(model_name)
        sources = "\n".join(
            f"- ({item['relevance']:.3f}) {item['title']}: {item['excerpt']} ({item['url']})"
            for item in sorted(evidence, key=lambda item: item["relevance"], reverse=True)
        )
        message = model.invoke(
            [
                (
                    "system",
                    (
                        "Diagnose LangChain developer issues using only the supplied evidence. "
                        "State uncertainty explicitly and do not invent APIs. "
                        f"Calibrated confidence for this evidence set is '{confidence}'. "
                        "If confidence is low, say the evidence is insufficient, do not invent "
                        "setup steps, and keep the tone uncertain. "
                        "If confidence is medium, give a tentative diagnosis with caveats. "
                        "Only give a firm diagnosis when confidence is high."
                    ),
                ),
                (
                    "user",
                    (
                        f"Issue:\n{state['issue']}\n\n"
                        "Evidence (relevance scores in parentheses):\n"
                        f"{sources or 'No evidence found.'}"
                    ),
                ),
            ]
        )
        diagnosis = str(message.content)
    else:
        diagnosis, confidence = _deterministic_diagnosis(evidence)

    citations = "\n".join(
        f"- [{item['title']}]({item['url']})" for item in evidence[:5]
    )
    response = f"{diagnosis}\n\nSources:\n{citations or '- No supporting source found.'}"
    return {
        "messages": [AIMessage(content=response)],
        "evidence": evidence,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "response": response,
    }


def build_graph(checkpointer=None):
    builder = StateGraph(SupportState)
    builder.add_node("inspect_intake", inspect_intake)
    builder.add_node("ask_clarification", ask_clarification)
    builder.add_node(
        "search_docs",
        _search_node("documentation", "documentation_evidence"),
    )
    builder.add_node(
        "search_issues",
        _search_node("github_issue", "github_evidence"),
    )
    builder.add_node(
        "search_releases",
        _search_node("release_note", "release_evidence"),
    )
    builder.add_node("synthesize", synthesize)

    builder.add_edge(START, "inspect_intake")
    builder.add_conditional_edges("inspect_intake", route_after_intake)
    builder.add_edge("ask_clarification", END)
    builder.add_edge("search_docs", "synthesize")
    builder.add_edge("search_issues", "synthesize")
    builder.add_edge("search_releases", "synthesize")
    builder.add_edge("synthesize", END)

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
