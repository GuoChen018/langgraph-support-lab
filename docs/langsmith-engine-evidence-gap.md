# The Evidence Gap in LangSmith Engine

## What Engine currently provides

Engine currently provides the ingredients needed to assess an issue, but the developer must synthesize them.

The issue view shows:

- An issue claim and diagnosis
- Recurrence count over time
- Linked traces
- A proposed fix
- Actions such as creating an evaluator, adding offline examples, and opening a PR

The missing layer is an explicit explanation of **why those ingredients prove the issue**.

## Example: Retriever tool-call loop

Consider an issue such as:

> Agent stuck in retriever tool-call loop, hitting `max_iterations`.

An AI engineer still has to determine:

- Were the search calls genuinely repetitive?
- Did the query or retrieved information change between calls?
- Was the agent making meaningful progress?
- Did every linked trace terminate at `max_iterations`?
- Did users fail to receive an answer?
- Are 20 linked traces significant relative to all retrieval traces?
- Are there similar long-running traces that eventually succeed?
- Why does Engine believe the proposed search-deduplication fix addresses the cluster?

That evidence probably exists across the linked trace details, but it is not synthesized on the issue page.

---

# Why Engine may not show everything

## 1. Engine samples traces

Engine prioritizes and analyzes selected traces rather than exhaustively processing every trace.

Producing trustworthy denominators, distributions, and counterexamples requires broader analytics than generating a cluster from a sample.

## 2. Agent traces have no universal evidence schema

Different issue types require different evidence:

- A tool loop requires trajectory evidence.
- A hallucination requires claims and sources.
- A state failure requires prior turns and checkpoints.
- A malformed artifact requires inspection of files or environment state.
- A performance regression requires latency and cost distributions.

Engine cannot use one fixed issue layout for all of them.

## 3. User impact is often not directly observable

A tool error does not prove the user experienced a failure.

Engine may lack:

- Downstream business outcomes
- Explicit user feedback
- Complete tracing
- External system state
- Confirmation that the failed operation mattered to the user

## 4. Diagnosis is partly inferential

A diagnosis such as:

> Search instructions are too broad.

is a hypothesis inferred from traces and connected code.

Distinguishing observed facts, supporting evidence, alternative explanations, and causal confidence requires another product layer.

## 5. Detail competes with usability

Putting every trace, distribution, uncertainty, code relationship, and counterexample on the issue page would overwhelm most users.

The better solution is progressive disclosure, not simply displaying more data.

## 6. Deeper analysis costs more

Engine’s LCU consumption scales with the number and complexity of traces analyzed.

Searching broadly for counterexamples, calculating issue-specific cohorts, and generating richer explanations would increase cost and latency.

---

# The product gap

The current experience is approximately:

```text
Engine summarizes its conclusion
        ↓
Developer opens linked traces
        ↓
Developer reconstructs why the conclusion is credible
```

The opportunity is:

```text
Engine states a falsifiable claim
        ↓
Engine presents the decisive evidence and uncertainty
        ↓
Developer drills into raw traces only when necessary
```

The critique should not be:

> Engine needs to show more tool calls.

It should be:

> Engine surfaces evidence, but leaves the developer to connect issue-level claims, recurrence data, and trace-level behavior. The opportunity is an adaptive evidence layer that explains why the selected evidence supports—or challenges—the issue.

This is a credible design opportunity because it improves trust without requiring every issue to use the same evidence layout.
