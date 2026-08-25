# Designing a General Evidence Layer for LangSmith Engine

## The design problem

An Engine issue might concern:

- An incorrect final answer
- A tool failure
- A hallucination
- Poor retrieval
- A looping trajectory
- Lost conversation state
- A malformed artifact
- Excessive latency or cost
- A safety-policy violation

A fixed evidence layout will not work equally well for all of them.

For example, showing tool calls is essential when diagnosing a silently failing integration. The same view may be mostly irrelevant when the issue is an unsupported claim in the final response.

The general design principle is:

> Show the smallest set of evidence needed to validate the specific issue claim, while preserving access to the complete trace.

The opportunity is not simply to build a better trace viewer. It is to build an evidence layer that understands which parts of a trace matter for the claim Engine is making.

## Treat every issue as a falsifiable claim

Every Engine issue can be expressed as:

```text
Under these conditions,
this component or behavior
deviates from this expectation,
with this frequency and scope,
causing this consequence.
```

For example:

```text
When users ask informational questions about cancellation,
the support agent invokes the cancellation tool
instead of explaining the available options,
in 8% of cancellation-related sessions,
causing unintended subscription changes.
```

This structure is more useful than a broad label such as “cancellation issue.”

## The questions every evidence view must answer

Regardless of the issue type, an AI engineer needs to determine:

1. **What failed?**
2. **What behavior was expected?**
3. **What behavior was observed?**
4. **Under what conditions does it happen?**
5. **How often does it happen?**
6. **What is the denominator?**
7. **Who or what is affected?**
8. **Why does Engine believe these examples represent one pattern?**
9. **Which examples challenge that pattern?**
10. **What changed near the first occurrence?**
11. **How confident is Engine?**
12. **Can the problem be reproduced, evaluated, fixed, or monitored?**

The developer should be able to answer these questions without reading every linked trace.

---

# The stable evidence shell

The issue page can retain a consistent information hierarchy while changing the evidence emphasized inside it.

## Level 1: Decision summary

Help the developer decide whether the issue deserves attention.

Show:

- A falsifiable issue claim
- User or system impact
- Prevalence and denominator
- Trend
- Scope
- Engine confidence
- Recommended next action
- Important uncertainty

Example:

```text
Issue
The agent invokes cancel_subscription when users only request information.

Impact
Users may have subscriptions changed without confirmation.

Prevalence
32 failures across 400 cancellation-related sessions during the last seven days.

Trend
Rate increased after agent version v18.

Confidence
High, with four ambiguous boundary examples.
```

## Level 2: Pattern evidence

Help the developer judge whether Engine found one coherent recurring problem.

Show:

- Why traces were clustered
- Shared signatures or behaviors
- Frequency over time
- Distribution by relevant dimensions
- Change points
- Representative traces
- Counterexamples
- Cluster confidence

## Level 3: Issue-specific evidence

Select the evidence lens appropriate to the failure:

- Tool spans for tool failures
- Claims and sources for hallucinations
- Retrieved documents for retrieval failures
- State transitions for memory failures
- Trajectories for loops
- Artifacts for long-running agents
- Distributions for latency and cost

## Level 4: Complete trace

Preserve expert access to:

- Full trace tree
- Run inputs and outputs
- Metadata
- Feedback
- Logs
- Token usage
- Timing
- Environment and version information

This progressive disclosure supports a fast initial judgment without removing technical depth.

---

# Core evidence modules

## Issue claim

State:

- Affected behavior or component
- Expected behavior
- Observed behavior
- Triggering conditions
- Frequency and scope
- Consequence

Avoid presenting Engine’s diagnosis as though it were already proven.

## Recurrence

Always pair the rate with:

- Count
- Denominator
- Unit of analysis
- Time window
- Environment
- Sampling coverage

“12% of calls” is insufficient.

A useful statement looks like:

```text
84 failures
out of 700 eligible calls
across 63 traces and 51 user sessions
in the production project
during the last 72 hours
```

Also expose whether:

- Retries are counted separately
- One trace can contribute multiple failures
- Test traffic is included
- Only a sample was analyzed
- Missing instrumentation affects the denominator

## Scope and distribution

Break down the pattern using dimensions relevant to the issue:

- Agent version
- Prompt version
- Model
- Tool
- Endpoint
- Environment
- Tenant
- Region
- User segment
- Input category
- Authentication provider
- Deployment

The appropriate dimensions should be selected dynamically. Region may matter for latency but not for a prompt-formatting issue.

## Trend and change points

Show:

- First seen
- Most recent occurrence
- Rate over time
- Direction of change
- Nearby deployments
- Prompt or model changes
- Configuration changes
- External incidents

Correlation should be clearly separated from a causal conclusion.

## Representative examples

Do not equate “all linked traces” with good evidence.

Curate examples with explicit roles:

### Canonical example

The clearest instance of the claimed failure.

### Most severe example

The trace with the greatest user or system consequence.

### Most common example

The behavior nearest the center of the cluster.

### Boundary example

An ambiguous example that clarifies the limits of the pattern.

### Counterexample

A similar trace that was handled correctly or should not belong in the cluster.

Counterexamples let the developer evaluate Engine’s inclusion rule rather than only confirm it.

## Expected versus observed behavior

Describe the behavioral gap explicitly:

```text
Expected
- Ask for confirmation before invoking the destructive tool.
- Explain options when the user asks an informational question.

Observed
- The tool was invoked immediately.
- No confirmation was requested.
```

This comparison can later inform:

- PR acceptance criteria
- Dataset assertions
- Evaluator criteria
- Online monitoring

## Diagnosis and confidence

Present root cause as a hypothesis.

Show:

- Supporting evidence
- Contradictory evidence
- Relevant code or configuration
- Alternative explanations
- Confidence
- Missing evidence

The developer should be able to reject the diagnosis while still accepting that the issue is real.

## Reproducibility and actionability

Explain whether the issue can be recreated:

- From trace inputs alone
- With an existing dataset
- In a sandbox
- With mocked dependencies
- Only in a production-like environment
- Not yet reproducible

Also identify whether correct behavior can be expressed as:

- A deterministic test
- A reference output
- Assertions
- An evaluator
- An environment-state verifier
- A monitoring condition

---

# Issue-specific evidence lenses

## Wrong or low-quality final answer

Emphasize:

- User input
- Final response
- Reference answer or criteria
- Human feedback
- Evaluator rationale
- Similar semantic failures

Tool calls are secondary unless they explain the incorrect answer.

## Tool failure

Emphasize:

- Tool selection
- Sanitized arguments
- Tool result or exception
- Retry and recovery behavior
- How the result was returned to the model
- Downstream agent behavior
- Final response

## Hallucination or unsupported claim

Emphasize:

- Individual claims in the response
- Retrieved or cited sources
- Whether each source supports the claim
- Missing evidence
- Evaluator or reviewer rationale

## Retrieval failure

Emphasize:

- Search query
- Retrieved documents
- Ranking
- Missing relevant documents
- Retrieval scores
- Whether generation failed despite good retrieval

This distinction prevents treating every incorrect answer as a retrieval problem.

## Looping or inefficient trajectory

Emphasize:

- Repeated sequence of actions
- Number of model and tool calls
- Progress between iterations
- Time and cost accumulation
- Termination condition
- The first point at which the loop became detectable

## State or memory failure

Emphasize:

- Relevant prior turns
- State before and after the operation
- Checkpoints
- Thread linkage
- Where information was lost, overwritten, or recalled incorrectly

## Long-running agent failure

Emphasize:

- Milestones
- Trajectory
- Environment state
- Files, database records, or other artifacts
- Verifier results
- Pause and resume events
- Timeout or termination reason

The final response alone is rarely sufficient.

## Latency or cost regression

Emphasize:

- Distribution rather than a single trace
- Median and tail latency
- Token and tool cost
- Slowest spans
- Change by version, model, tool, and traffic segment
- Whether quality improved enough to justify the cost

## Safety or policy failure

Emphasize:

- Relevant input and output excerpt
- Policy category
- Violated criterion
- Evaluator or reviewer rationale
- Comparable safe examples
- Severity and exposure

---

# Design principles

## Start with the claim, not the trace tree

The trace tree is raw evidence. The issue claim explains why the evidence matters.

## Adapt evidence without changing the page’s mental model

Keep the same high-level hierarchy across issue types:

```text
Claim
→ Impact and recurrence
→ Pattern evidence
→ Issue-specific evidence
→ Complete traces
```

Only the issue-specific evidence module needs to change substantially.

## Make the denominator first-class

A rate without its unit, population, time window, and sampling method is not actionable.

## Show counterevidence

An evidence view that only presents confirming examples encourages automation bias.

## Separate correlation, diagnosis, and proof

“Started after deployment v43” is evidence. “Deployment v43 caused it” is a hypothesis.

## Surface uncertainty

Missing spans, redacted values, sampled traffic, and weak cluster boundaries should be visible.

## Optimize for decisions

The evidence layer should end by clarifying:

- Why the issue likely matters
- What remains uncertain
- What Engine recommends
- What additional evidence would change the recommendation

---

# What an AI engineer ultimately cares about

Across issue types:

- **Validity:** Is the signal real rather than instrumentation noise?
- **Coherence:** Are these examples one failure mode?
- **Severity:** What is the actual consequence?
- **Prevalence:** How large and representative is the pattern?
- **Scope:** Which versions, tools, users, and conditions are affected?
- **Causality:** What supports the root-cause hypothesis?
- **Reproducibility:** Can the behavior be recreated safely?
- **Evaluability:** Can correct behavior be expressed as criteria?
- **Fixability:** Is there a concrete intervention?
- **Monitorability:** Can recurrence be detected reliably?

# Biggest design opportunity

The strongest opportunity is an **adaptive evidence layer built around an evidence contract**.

It would:

- Explain each issue as a falsifiable claim.
- Select the evidence lens appropriate to the failure type.
- Present recurrence with a trustworthy denominator.
- Curate representative examples and counterexamples.
- Separate observed facts from diagnosis.
- Expose uncertainty and missing instrumentation.
- Translate expected behavior into validation and monitoring criteria.

The central design question is not:

> Which trace fields should always be visible?

It is:

> What evidence does a developer need to accept or reject this particular issue claim?

## References

- [LangSmith Engine overview](https://docs.langchain.com/langsmith/engine-overview)
- [Find and fix issues with LangSmith Engine](https://docs.langchain.com/langsmith/engine)
- [LangSmith evaluators](https://docs.langchain.com/langsmith/evaluators)
