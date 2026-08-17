from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import MessagesState


class Evidence(TypedDict):
    source_type: Literal["documentation", "github_issue", "release_note", "forum"]
    title: str
    excerpt: str
    url: str
    relevance: float


class SupportState(MessagesState, total=False):
    issue: str
    symptoms: list[str]
    versions: list[str]
    missing_fields: list[str]
    awaiting_clarification: bool
    documentation_evidence: list[Evidence]
    github_evidence: list[Evidence]
    release_evidence: list[Evidence]
    evidence: list[Evidence]
    diagnosis: str
    confidence: Literal["low", "medium", "high"]
    response: str
