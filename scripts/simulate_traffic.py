"""Generate reproducible synthetic conversations through the actual Agent Server.

Dry-run by default. Each conversation has its own thread, with sequential turns.
Metadata makes simulated traffic filterable in LangSmith Insights.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def select_cases(cases: list[dict], count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    # Cover distinct issues before adding weighted repeat contacts.
    coverage = cases.copy()
    rng.shuffle(coverage)
    selected = coverage[:count]
    if count > len(coverage):
        selected.extend(
            rng.choices(cases, weights=[c["traffic_weight"] for c in cases], k=count - len(cases))
        )
    rng.shuffle(selected)
    return selected


async def simulate(args: argparse.Namespace, selected: list[dict]) -> None:
    args.output.mkdir(parents=True, exist_ok=True)
    results_path = args.output / "conversations.jsonl"
    if results_path.exists():
        raise SystemExit("Output already contains results; use a new output directory.")
    semaphore = asyncio.Semaphore(args.concurrency)
    results = []
    async with httpx.AsyncClient(
        base_url=args.api_url, timeout=args.timeout, follow_redirects=False
    ) as client:
        health = await client.get("/ok")
        health.raise_for_status()

        async def conversation(index: int, case: dict) -> None:
            async with semaphore:
                metadata = {
                    "synthetic": True,
                    "simulation_batch": args.batch,
                    "scenario_id": case["id"],
                    "scenario_topic": case["topic"],
                    "simulated_persona": case["persona"],
                    "simulated_user_id": f"{args.batch}-user-{index:04}",
                    "traffic_source": "scripted-simulation",
                }
                record = {
                    "index": index,
                    "scenario": case,
                    "metadata": metadata,
                    "turns": [],
                    "status": "complete",
                    "review_flags": [],
                }
                started = time.monotonic()
                try:
                    response = await client.post("/threads", json={"metadata": metadata})
                    response.raise_for_status()
                    thread_id = response.json()["thread_id"]
                    record["thread_id"] = thread_id
                    for turn, text in enumerate(case["turns"], 1):
                        turn_started = time.monotonic()
                        response = await client.post(
                            f"/threads/{thread_id}/runs/wait",
                            json={
                                "assistant_id": args.assistant_id,
                                "input": {"messages": [{"role": "user", "content": text}]},
                                "config": {
                                    "tags": ["synthetic", "insights-simulation", args.batch],
                                    "metadata": {**metadata, "simulation_turn": turn},
                                },
                            },
                        )
                        response.raise_for_status()
                        values = response.json()
                        # The wait endpoint can return a run error with HTTP 200.
                        if "__error__" in values:
                            error = values["__error__"]
                            kind = (
                                error.get("error", "AgentRunError")
                                if isinstance(error, dict)
                                else "AgentRunError"
                            )
                            raise RuntimeError(kind)
                        answer = values.get("response", "")
                        if not answer:
                            raise RuntimeError("EmptyAgentResponse")
                        runs_response = await client.get(f"/threads/{thread_id}/runs")
                        runs_response.raise_for_status()
                        runs = runs_response.json()
                        latest = max(runs, key=lambda r: r["created_at"])
                        if latest["status"] != "success":
                            raise RuntimeError("AgentRunNotSuccessful")
                        record["turns"].append(
                            {
                                "user": text,
                                "assistant": answer,
                                "run_id": latest["run_id"],
                                "latency_seconds": round(time.monotonic() - turn_started, 3),
                                "awaiting_clarification": bool(
                                    values.get("awaiting_clarification")
                                ),
                                "confidence": values.get("confidence"),
                                "evidence": values.get("evidence", []),
                            }
                        )
                        if turn > 1 and values.get("awaiting_clarification"):
                            record["review_flags"].append(
                                "still_requests_clarification_after_followup"
                            )
                        if not values.get("evidence") and values.get("intent") != "capabilities":
                            record["review_flags"].append("no_evidence")
                        if values.get("confidence") == "low":
                            record["review_flags"].append("low_confidence")
                        # Only inspect the answer, not the echo of the adversarial input.
                        if "COMPROMISED_TEST_MARKER" in answer:
                            record["review_flags"].append("possible_instruction_injection")
                        await asyncio.sleep(args.turn_delay)
                except (httpx.HTTPError, RuntimeError, KeyError, ValueError) as exc:
                    record["status"] = "error"
                    # Exception text can contain auth headers or provider credentials.
                    record["error_type"] = type(exc).__name__
                    if isinstance(exc, httpx.HTTPStatusError):
                        record["http_status"] = exc.response.status_code
                    record["review_flags"].append("runtime_error")
                record["latency_seconds"] = round(time.monotonic() - started, 3)
                results.append(record)
                with results_path.open("a") as output:
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(
                    f"[{len(results)}/{len(selected)}] {case['id']} {case['topic']}: "
                    f"{record['status']} ({len(record['turns'])} turns)",
                    flush=True,
                )

        await asyncio.gather(*(conversation(i, case) for i, case in enumerate(selected, 1)))

    summary = {
        "batch": args.batch,
        "synthetic": True,
        "seed": args.seed,
        "conversations": len(results),
        "completed": sum(r["status"] == "complete" for r in results),
        "failed": sum(r["status"] == "error" for r in results),
        "completed_turns": sum(len(r["turns"]) for r in results),
        "topics": dict(Counter(r["scenario"]["topic"] for r in results)),
        "review_flags": dict(Counter(flag for r in results for flag in set(r["review_flags"]))),
        "limitations": [
            "Synthetic scenarios do not establish actual customer prevalence.",
            "Scripted follow-ups are not an adaptive user simulator.",
            "Review flags are triage signals, not correctness grades.",
            "Low concurrency tests behavior, not production capacity.",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--api-url", default="http://localhost:2024")
    parser.add_argument("--assistant-id", default="support_agent")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--turn-delay", type=float, default=1)
    parser.add_argument(
        "--batch", default="synthetic-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    )
    parser.add_argument("--output", type=Path, default=ROOT.parent / "outputs" / "simulation")
    parser.add_argument(
        "--execute", action="store_true", help="Send real requests; otherwise preview only."
    )
    args = parser.parse_args()
    if args.count < 1 or not 1 <= args.concurrency <= 10 or args.turn_delay < 0:
        parser.error("count must be positive; concurrency 1–10; turn delay nonnegative")
    cases = json.loads((ROOT / "data/simulation/scenarios.json").read_text())["scenarios"]
    selected = select_cases(cases, args.count, args.seed)
    print(
        json.dumps(
            {
                "execute": args.execute,
                "batch": args.batch,
                "conversations": args.count,
                "distinct_scenarios": len({c["id"] for c in selected}),
                "maximum_agent_runs": sum(len(c["turns"]) for c in selected),
                "topics": dict(Counter(c["topic"] for c in selected)),
            },
            indent=2,
        )
    )
    if args.execute:
        asyncio.run(simulate(args, selected))


if __name__ == "__main__":
    main()
