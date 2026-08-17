from __future__ import annotations

import argparse
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from langgraph_support_lab.graph import build_graph

console = Console()


def run(issue: str) -> dict:
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke({"messages": [HumanMessage(content=issue)]}, config=config)

    while result.get("awaiting_clarification"):
        console.print(Markdown(result["response"]))
        answer = Prompt.ask("Additional information")
        result = graph.invoke(
            {"messages": [HumanMessage(content=answer)]},
            config=config,
        )

    return result


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Investigate a LangChain developer issue with a stateful LangGraph workflow."
    )
    parser.add_argument("issue", nargs="?", help="Issue description. Prompts if omitted.")
    args = parser.parse_args()

    issue = args.issue or Prompt.ask("Describe the LangChain or LangGraph issue")
    result = run(issue)
    console.print("\n[bold green]Final response[/bold green]")
    console.print(Markdown(result["response"]))


if __name__ == "__main__":
    main()
