"""Run a LangSmith experiment against support-agent-baseline-v1.

Usage:
  source .venv/bin/activate
  python scripts/run_experiment.py --prefix improved-confidence
"""

from __future__ import annotations

import argparse
import re
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import evaluate

from langgraph_support_lab.graph import build_graph

load_dotenv()

_graph = build_graph(checkpointer=InMemorySaver())


def target(inputs: dict) -> dict:
    question = inputs["question"]
    config = {
        "configurable": {"thread_id": f"exp-{uuid.uuid4().hex}"},
        "tags": ["experiment"],
    }
    result = _graph.invoke({"messages": [HumanMessage(content=question)]}, config=config)
    return {
        "response": result.get("response") or "",
        "should_clarify": bool(result.get("awaiting_clarification")),
        "confidence": result.get("confidence"),
    }


def clarification_match(inputs, outputs, reference_outputs):
    expected = bool(reference_outputs.get("should_clarify"))
    actual = bool(outputs.get("should_clarify"))
    response = (outputs.get("response") or "").lower()
    looks_like_clarify = any(
        phrase in response
        for phrase in ["please provide", "before i investigate", "what version", "missing"]
    )
    if expected:
        ok = actual or looks_like_clarify
    else:
        ok = not actual
    return {
        "key": "clarification_match",
        "score": 1.0 if ok else 0.0,
        "comment": f"expected={expected} actual={actual}",
    }


def required_facts_present(inputs, outputs, reference_outputs):
    facts = reference_outputs.get("required_facts") or []
    if not facts:
        return {"key": "required_facts", "score": 1.0, "comment": "no required facts"}
    text = (outputs.get("response") or "").lower()
    hits, misses = [], []
    for fact in facts:
        tokens = [t for t in re.split(r"[^a-z0-9_.]+", fact.lower()) if len(t) > 3]
        matched = sum(1 for token in tokens if token in text)
        ok = matched >= max(1, len(tokens) // 2)
        (hits if ok else misses).append(fact)
    return {
        "key": "required_facts",
        "score": len(hits) / len(facts),
        "comment": f"hits={hits}; misses={misses}",
    }


def confidence_calibration(inputs, outputs, reference_outputs):
    failure = reference_outputs.get("failure_mode")
    conf = (outputs.get("confidence") or "").lower() if outputs.get("confidence") else None
    if failure == "incorrect_confidence":
        ok = conf != "high"
        return {
            "key": "confidence_calibration",
            "score": 1.0 if ok else 0.0,
            "comment": f"failure_mode=incorrect_confidence confidence={conf}",
        }
    return {"key": "confidence_calibration", "score": 1.0, "comment": "n/a"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prefix",
        default="improved-confidence",
        help="LangSmith experiment name prefix",
    )
    args = parser.parse_args()

    results = evaluate(
        target,
        data="support-agent-baseline-v1",
        evaluators=[clarification_match, required_facts_present, confidence_calibration],
        experiment_prefix=args.prefix,
        max_concurrency=1,
        metadata={"agent_version": args.prefix},
    )
    print(results)


if __name__ == "__main__":
    main()
