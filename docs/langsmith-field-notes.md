# LangSmith Field Notes: What We Built, How It Connects, What Should Come Next

A working summary from building **LangGraph Support Lab** — a developer-support
agent used as a product-design field study of the LangSmith lifecycle.

Audience: future-you, or anyone who asks what you learned and what you believe
LangSmith should become.

---

## 1. What we actually did

We did not “tour LangSmith.” We used it the way an agent engineer would:

1. **Built** a LangGraph support agent (intake → clarify or search → synthesize).
2. **Traced** real runs into LangSmith.
3. **Created a dataset** (`support-agent-baseline-v1`) from those runs.
4. **Corrected reference outputs** to describe what a good response should do
   (not “whatever the agent said”).
5. **Defined evaluators** (UI LLM-as-judge + SDK code metrics).
6. **Ran experiments** comparing agent versions.
7. **Explored Playground** and learned it scores *prompts*, not our graph.
8. **Shipped a fix** (confidence from evidence relevance, not source-type count)
   and re-ran experiments to prove the improvement.

That loop is the product:

```text
Build → Trace → Understand → Dataset → Evaluate → Experiment → Improve → Repeat
```

---

## 2. Topology: who does what

Think in **three layers**. Confusing them is the #1 mental-model failure.

```text
┌─────────────────────────────────────────────────────────────┐
│  LAYER A — The system under test                            │
│  Your LangGraph agent (code): routing, tools, confidence    │
│  Alternate: a Playground prompt + model (not your graph)    │
└────────────────────────────┬────────────────────────────────┘
                             │ produces answers
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER B — The test harness                                 │
│  Dataset (test questions + expected responses)              │
│  Evaluators (how “good” is defined)                         │
│  Experiments (one run of a generator over the dataset)      │
└────────────────────────────┬────────────────────────────────┘
                             │ scored in
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER C — Observation & iteration surfaces                 │
│  Tracing, Studio, Playground, Annotation, Prompts, Hub…     │
└─────────────────────────────────────────────────────────────┘
```

| Surface | Layer | Job |
|---|---|---|
| **Your agent / chat UI / CLI** | A | Produce support answers |
| **Tracing** | C | Inspect one run |
| **Studio** | C | Debug graph state/nodes |
| **Datasets** | B | Save reusable test cases |
| **Evaluators** | B | Define scoring rules |
| **Experiments** | B | Compare versions on the same cases |
| **Playground** | A+B hybrid | Iterate on *prompts/models*, optionally over a dataset |
| **Annotation queues** | B/C | Humans correct references / labels |
| **Prompts / Context Hub** | A/C | Manage reusable prompt/context assets |

**Rule of thumb:** Dataset + evaluator = shared exam. Playground and your agent
are different students taking the same exam.

---

## 3. Key terminology (plain language)

| Term | Meaning |
|---|---|
| **Trace / run** | One execution record: inputs, outputs, nested spans, timing, tokens |
| **Thread** | Multi-turn conversation sharing state (`thread_id`) |
| **Dataset** | A reusable set of examples (inputs + optional reference outputs) |
| **Example** | One test case in a dataset |
| **Input** | What we feed the system (for us: `question`) |
| **Reference output** | What a good response should say or do — not automatically what the agent said |
| **Output schema** | Shape of the *reference label* (and/or run outputs) — **not** “agent must reply in JSON” |
| **Evaluator** | Function or LLM judge that scores an output |
| **Experiment** | Running a specific generator over a dataset + collecting scores |
| **Baseline** | First experiment before a change |
| **SDK evaluate** | Code path (`evaluate(target, data=..., evaluators=...)`) that runs *your agent* |
| **Playground experiment** (`pg::…`) | Same harness, but answers come from the Playground prompt/model |
| **Annotation** | Human review to create/correct labels |
| **LLM-as-judge** | Another model grades the agent’s message against a rubric |
| **Code evaluator** | Deterministic checks (e.g. did it clarify? confidence ≠ high) |

### The reference-output trap

When you **Add to dataset** from a trace, LangSmith often prefills reference
output with the agent’s actual reply. That is a **draft**, not ground truth.

- Bad run → still valuable as a **case** (the question/scenario).
- Reference → must be edited to the **desired** behavior.
- Saving failures is normal. Treating a bad answer as the expected answer is the mistake.

---

## 4. Workflows we used (and how they connect)

### Workflow 1 — Agent development

```text
Write graph → run chat/CLI → inspect traces/Studio → fix code → repeat
```

### Workflow 2 — Trace → dataset

```text
Interesting/failed run
  → Add to dataset (keeps the question)
  → Edit reference output (describe the expected response)
  → Optional: annotation queue for non-builders
```

### Workflow 3 — Evaluate an agent version (what mattered for us)

```text
Dataset + evaluators
  → SDK target function invokes LangGraph
  → Experiment scores land in UI
  → Change agent (e.g. confidence calibration)
  → New experiment
  → Compare
```

Command we used:

```bash
python scripts/run_experiment.py --prefix improved-confidence
```

### Workflow 4 — Playground (exploration, not agent truth)

```text
Same dataset + evaluator
  → Playground prompt + Claude
  → Experiment named like pg::claude-sonnet-5::…
  → Scores the prompt, not ChainSupport
```

### How they connect

```text
          traces ──────────────────────────────┐
            │                                  │
            ▼                                  ▼
     Studio (debug)                    Dataset examples
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
              SDK experiment            Playground experiment      Annotation
              (your agent)              (prompt + model)           (humans)
                    │                          │
                    └────────────┬─────────────┘
                                 ▼
                           Evaluators score
                                 ▼
                            Compare → decide what to fix next
```

---

## 5. What the experiments proved

Dataset: `support-agent-baseline-v1` (6 reviewed test examples).

| Experiment | Generator | Notable result |
|---|---|---|
| `baseline-current-agent-…` | LangGraph agent v0 | Redis case: `confidence=high` → calibration fail |
| `improved-confidence-…` | LangGraph agent v1 | Redis: `confidence=low` → calibration pass |
| `pg::claude-sonnet-5::…` | Playground Claude | Separate prompt baseline; not the agent |

Fix: confidence from **evidence relevance**, not “we retrieved three source types.”

| Metric | Baseline | Improved |
|---|---|---|
| clarification_match | 1.00 | 1.00 |
| confidence_calibration | 0.83 | **1.00** |
| required_facts | 0.83 | 0.92 |

---

## 6. Design opinions: where LangSmith should go

These are **opinions formed while learning**, grounded in friction we hit.
Stated as a senior designer would: clear stance, evidence, product implication.

### Opinion 1 — Separate “prompt apps” from “agent systems” in the primary IA

**Observation:** Playground Evaluate Mode uses the same dataset/experiment
objects as agent evals, but swaps in a generic model+prompt. That made it feel
like the experiment *should* run our agent — until it didn’t.

**Stance:** LangSmith’s default paths should ask early: *What is generating
answers — a prompt, a deployed graph, or local SDK code?* and keep that choice
visible on every experiment.

**Future:** Experiment = `{generator, dataset, evaluators}` with generator type
as a first-class badge (`graph` / `prompt` / `sdk` / `deployment`), not a
prefix like `pg::` you only notice after the fact.

### Opinion 2 — Adding a trace should save the case, not assume the answer is correct

**Observation:** Prefilling reference output with the agent’s reply teaches the
wrong model: “datasets are correct answers.” We had to unlearn that.

**Stance:** Adding from a failed trace should save the question while clearly
marking its expected response as unfinished, or send it to someone for review.

**Future:** Offer explicit choices: *Save question for later review* vs
*Save question with an approved expected answer*. Make the difference
impossible to miss.

### Opinion 3 — Make causality the unit of debugging, not just span trees

**Observation:** Traces show steps; the hard job is “where did quality first
diverge?” Our failure was confidence policy, not a missing node.

**Stance:** Observability wins when it answers *why the user-facing answer is
wrong*, not only *what ran*.

**Future:** First-class links from evaluator failures → responsible span/state
fields (e.g. highlight `confidence` + evidence relevance), plus suggested
“likely failure mode” from a lightweight taxonomy.

### Opinion 4 — Role-aware loops for builders vs reviewers vs PMs

**Observation:** As a designer without deep LangChain domain knowledge, I could
judge clarification and confidence honesty — not every technical diagnosis.
Domain experts and builders need different surfaces.

**Stance:** Annotation and evaluation should be designed as a **cross-functional
workflow**, not an engineer-only afterthought.

**Future:** Reviewer UI centered on: question, evidence used, proposed answer,
rubric checkboxes, one-click “promote corrected reference.” Less JSON, more
judgment.

### Opinion 5 — Continuous improvement should feel like one product story

**Observation:** Studio, Playground, Datasets, Evaluators, Hub, Deployments are
powerful but easy to experience as disconnected islands.

**Stance:** High-growth agent platforms win on **lifecycle coherence**, not on
surface count.

**Future:** A single “Improve” spine: production/trace failure → case → label →
eval → experiment → ship → monitor, with your place on the spine always visible.
Fleet/Engine/Insights should plug into that spine rather than invent parallel
vocabularies.

## 7. What we have not done yet (honest scope)

- Live docs / GitHub / forum retrieval (still local corpus)
- Rich annotation-queue workflow with a second persona
- Production deployment + monitoring/Insights traffic
- Formal pairwise experiments / prompt hub versioning at scale
- A polished product prototype of one opportunity above

That’s fine. The learning goal was the **trace → eval → improve** loop with
evidence — and we completed it.

---

## 8. Quick reference: artifacts in this repo

| Artifact | Path |
|---|---|
| Project brief | `docs/project-brief.md` |
| This summary (markdown) | `docs/langsmith-field-notes.md` |
| Interactive HTML | `docs/index.html` |
| Agent graph | `src/langgraph_support_lab/graph.py` |
| Experiment runner | `scripts/run_experiment.py` |
| Baseline dataset | LangSmith: `support-agent-baseline-v1` |

Open the HTML locally:

```bash
open docs/index.html
```
