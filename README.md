# LangGraph Support Lab

A developer-support agent that uses a stateful LangGraph workflow to investigate
LangChain ecosystem issues. The project is also a product-design field study of
the complete LangSmith agent-engineering lifecycle.

See the [project brief](docs/project-brief.md) for the goals, research approach,
architecture, evaluation plan, and current status.

## What the first version demonstrates

- Structured shared state
- Standard chat messages and persistent conversation threads
- Conditional routing for missing information
- Parallel live searches across docs, GitHub issues, release notes, and Forum topics
- Educational answers for LangChain concepts, relationships, and product workflows
- Multi-turn clarification in the same thread
- Deterministic synthesis without an API key
- Optional model-backed synthesis
- Automatic LangSmith tracing when configured
- A customized Next.js chat interface based on Agent Chat UI

Live retrieval is enabled by default in hybrid mode. The agent searches current
LangChain Markdown documentation, public GitHub issues, release and migration
pages, and full LangChain Forum topics. The small local corpus remains available
as a deterministic fallback when a source is unavailable.

## Setup

```bash
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

To use Anthropic or OpenAI for synthesis:

```bash
python -m pip install -e ".[dev,anthropic]"
# or
python -m pip install -e ".[dev,openai]"
cp .env.example .env
```

Set `MODEL` and the corresponding provider key in `.env`. Without `MODEL`, the
workflow remains fully runnable using its transparent local synthesizer.

### Live retrieval

`RETRIEVAL_MODE=hybrid` is recommended for local development:

- `hybrid`: use live sources, then fall back to `data/knowledge.json`
- `live`: use only current public sources
- `local`: use only the deterministic starter corpus

GitHub public search works without credentials, but `GITHUB_TOKEN` is recommended
for repeated experiments because unauthenticated search is rate-limited. Docs and
Forum search require no credentials. Retrieval requests use bounded timeouts and
short-lived caches so a slow source does not block the entire support answer.

## Run

```bash
support-lab \
  "After upgrading to langchain 1.0, create_react_agent fails with a deprecated API error on python 3.13."
```

The workflow responds directly when the issue is sufficiently specified. If
required diagnostic information is missing, it asks in chat and uses the
developer's next message as additional context in the same thread.

To run the Agent Server and open the graph in LangSmith Studio:

```bash
cp .env.example .env
langgraph dev
```

To run the customized chat interface in another terminal:

```bash
cd web
nvm use
npm install
npm run dev
```

Open `http://localhost:3000`. The local UI connects to the `support_agent`
graph at `http://localhost:2024` and does not require a LangSmith API key.

## Test

```bash
pytest
ruff check .
```

## Product investigation

The project will eventually move through:

1. Build and debug in LangGraph and Studio.
2. Trace agent behavior in LangSmith.
3. Turn real failures into corrected regression examples and evaluators.
4. Compare agent versions through experiments.
5. Deploy and generate production-like traffic.
6. Study Insights, Chat, Engine, and human-review workflows.
7. Synthesize three to five evidence-backed product opportunities.
