# LangSmith Engine Triage: Friction Points and Design Opportunities

## Context

This assessment identifies potential friction points in the Engine triage journey and pairs them with design opportunities.

## Summary

| Rank | Theme | Friction point | Design opportunity |
| --- | --- | --- | --- |
| 1 | Evidence and trust | Engine shows a conclusion, recurrence chart, linked traces, and likely cause, but does not clearly separate observed facts from inferred diagnosis or connect them into one verifiable explanation. | Explainable issue summary |
| 2 | Evidence and trust | Linked traces open the full execution, but do not point to the exact span, field, or transition that demonstrates the claimed failure. | Guided trace proof |
| 3 | Impact and prioritization | Severity and occurrence volume do not show the user-visible consequence or blast radius: how many sessions or users were affected, which workflows failed, and whether impact is spreading. | User-impact and scope breakdown |
| 4 | Fix and validation | Engine can propose a PR, evaluator, and offline examples, but there is no guided flow to determine available coverage, run the PR version, and interpret whether it is safe to merge. | Guided validation flow |
| 5 | Fix and continuity | Fixing spans the issue page, evaluation surfaces, and GitHub; there is no single place to see what is complete, stale, blocked, or ready to resume. | Unified, resumable Fix workspace |
| 6 | Deferral and notifications | Leaving an issue Open does not record when it should return, what signal will bring it back, or where the developer should be notified. | Snooze with return conditions |
| 7 | Lifecycle and ownership | Open and Closed do not distinguish issues awaiting triage, fixes underway, resolved problems, and intentional dismissals. | Clear triage and outcome states |
| 8 | Return and recurrence | When an issue returns after a snooze or resolution, the developer may need to reconstruct why it returned and what changed since the previous decision. | Return reason and issue history |
| 9 | Lifecycle and feedback | Closing an issue does not record whether Engine was wrong, the risk was accepted, or the issue was irrelevant or duplicated. | Structured dismissal feedback |

One opportunity can address several friction points. For example, issue assessment and guided trace evidence together form a broader evidence experience.

## Ranked friction points

### 1. Engine does not clearly separate what it observed from what it inferred

Engine already provides evidence: an issue description, recurrence chart, linked traces, and a proposed fix or cause. The gap is not the absence of evidence. The gap is the connection between those elements.

An Engine issue combines several different statements:

1. **Observed event** — what directly occurred in a trace.
2. **Behavioral failure** — why that event represents incorrect agent behavior.
3. **Recurring pattern** — why multiple traces count as the same issue.
4. **User or system consequence** — what failed downstream.
5. **Likely cause** — Engine's explanation for why the behavior occurred.

For the authentication scenario, those statements might be:

```text
Observed
account_management returned 401 token_expired.

Behavioral failure
The agent did not refresh credentials, retry, or disclose the failure.

Consequence
The final response claimed the account update succeeded.

Recurring pattern
The same trajectory appeared in 84 of 700 eligible calls.

Likely cause
Structured authentication results may bypass exception-based recovery.
This is a diagnosis, not a confirmed fact.
```

The current ingredients may support this explanation, but the developer still has to assemble it from the issue summary, chart, traces, and proposed fix. The interface also risks presenting the likely cause with the same certainty as directly observed behavior.

This matters because the next actions can turn Engine's interpretation into durable product decisions:

- A PR may change production behavior.
- An evaluator may repeatedly grade future traces against the same interpretation.
- Offline examples may encode the proposed expected behavior.
- An Ignore decision may remove a real problem from active triage.

The developer therefore needs to see which parts are observed, which are inferred, and how the evidence connects before choosing a path.

### 2. Linked traces do not point to the exact proof of the claimed failure

Engine links to traces that support the issue, but the trace view contains the complete execution:

- Model calls
- Tool calls
- Retrieval steps
- Inputs and outputs
- State changes
- Evaluator results

The developer must identify which span, field, or transition supports Engine's conclusion and understand why that detail matters.

The trace should make clear:

- Why this trace was included
- Where the relevant behavior occurs
- Which span or field provides the strongest evidence
- What was expected
- What happened instead
- Whether the trace supports the issue, the proposed cause, or both

### 3. Severity and occurrence volume do not explain the consequence or blast radius

A severity label and a trace or occurrence count describe Engine's assessment and the volume of detected events. They do not necessarily reveal how many people or workflows experienced a meaningful failure.

For example, `84 authentication failures` could mean:

- 84 retries within a small number of sessions
- 84 different users unable to complete an account update
- Failures that recovered automatically
- Failures followed by misleading success confirmations
- Failures isolated to one tenant, workflow, or deployment

These situations should not receive the same priority.

The developer needs the denominator and scope that are relevant to the decision:

- `84 of 700 eligible account-management calls`
- `63 traces across 51 sessions`
- `11 sessions received a false success confirmation`
- `2 account-update workflows affected`
- `18% after v43, compared with 2% before v43`

Where user or business impact cannot be observed, Engine should state that limitation instead of allowing trace volume to stand in for impact.

### 4. Engine can propose a PR, evaluator, and offline examples, but there is no guided flow to set up, run, and interpret tests before merging

The developer may need to:

1. Find or create a relevant dataset.
2. Decide whether issue-specific examples are needed.
3. Find, create, or configure evaluators.
4. Run an experiment against the PR version.
5. Optionally run a baseline experiment.
6. Compare the results.
7. Decide whether the evidence is sufficient to merge.

The product exposes these evaluation capabilities, but it does not currently guide the developer from a proposed change to a completed test plan.

The appropriate validation also depends on what already exists:

- A relevant dataset
- Issue-specific examples
- Existing evaluators
- A newly proposed evaluator
- An executable PR version
- Baseline experiment results

### 5. Fixing spans the issue page, evaluation surfaces, and GitHub; there is no single place to see what is complete or resume later

Resolving an issue can involve:

- A PR and its commits
- Offline examples
- Evaluators
- Experiments
- CI results
- Review comments

These artifacts progress independently across the issue page, evaluation surfaces, and GitHub.

When a developer returns:

- The PR may have new commits.
- CI may have failed.
- An experiment may refer to an older commit.
- An evaluator or dataset may have changed.
- The PR may have been merged, replaced, or closed.

There is no single current view of what exists, what changed, what is stale, and what should happen next.

### 6. Leaving an issue for later does not specify when or how it should return

A developer may want to:

1. Return on a specific date.
2. Return if the behavior happens again.
3. Return if frequency or severity increases.

Without an explicit Snooze action, the issue may remain in the triage queue without a clear follow-up or disappear from attention without a reliable return condition.

The developer needs to know:

- What event or date will bring it back
- Where the notification will appear
- Whether the issue will remain visible
- Whether new evidence will be highlighted

Creating an evaluator is separate. An evaluator can improve recurrence detection; the Snooze rule determines what condition returns the issue, and notification settings determine where the developer hears about it.

### 7. Open and Closed do not communicate the triage decision or outcome

An issue may be:

- Newly detected
- Under review
- Being fixed
- Snoozed until a date or recurrence condition
- Resolved
- Dismissed because it was incorrectly flagged
- Dismissed because the risk was accepted

If these appear only as Open or Closed, another developer cannot quickly tell whether a decision is still needed, remediation is underway, the issue was fixed, or it was intentionally dismissed.

### 8. A returning issue may not explain why it requires attention again

An issue can return for different reasons:

- A Snooze date arrived.
- A recurrence or impact threshold was met.
- The same failure returned after a fix.

The developer should not have to reconstruct the trigger or compare the new episode manually.

The returned issue should explain:

- Why it returned now
- Which new traces or measurements met the condition
- How current frequency, scope, and impact compare with the previous snapshot
- Which agent version or deployment is affected
- Which evaluator or Engine signal detected the recurrence
- The previous decision, fix, and validation outcome

A snoozed issue should return with a **Returned** label and its saved condition. A resolved issue should return with recurrence-after-fix context. If Engine detects a materially different failure, it should create a new related issue rather than return the old one.

### 9. Closing an issue does not record why it was dismissed

Ignoring can mean:

- Engine grouped the traces incorrectly.
- The expected behavior is wrong.
- The issue is real but not relevant.
- The issue is a duplicate.
- The risk is acceptable.
- The impact is too low.

Without a reason, the team cannot tell whether Engine's detection was poor or the issue was consciously deprioritized.

## Ranked design opportunities

### 1. Explainable issue summary

Turn the existing evidence into a traceable explanation instead of adding another generic summary.

The issue page should distinguish:

- **Observed behavior** — facts directly present in traces
- **Expected behavior** — the standard Engine believes was violated
- **Pattern evidence** — frequency, denominator, shared trajectory, and scope
- **Consequence** — what happened to the user, workflow, or system
- **Likely cause** — the diagnosis, its supporting evidence, and confidence
- **Uncertainty** — missing data and credible alternatives

For each important claim, the developer should be able to open the supporting trace or measurement directly.

The structure remains stable, but the proof adapts to the issue type. Tool failures, incorrect answers, retrieval failures, loops, state loss, latency, and safety problems require different decisive evidence.

### 2. Guided trace proof

When a developer opens a linked trace:

- Jump to the relevant span.
- Highlight the decisive input, output, tool result, or state change.
- Explain why that evidence supports the issue.
- Show expected and observed behavior together.
- Distinguish evidence of the failure from evidence of the proposed cause.
- Preserve access to the complete trace.

The goal is not to hide the trace. It is to give the developer a useful starting point.

### 3. User-impact and scope breakdown

Translate event volume into the units that matter for prioritization.

Show, when available:

- Eligible calls and affected calls
- Unique traces, threads or sessions, and users
- User-visible failure outcomes
- Affected workflows, tenants, tools, and versions
- Current trend and change from the previous period
- Concentration versus broad distribution
- Relevant deployment or configuration changes

Do not treat trace count as a proxy for user impact. When identity, business outcomes, or complete denominators are unavailable, label those gaps explicitly.

Engine can recommend urgency from the available evidence, but the underlying measurements should remain visible so the team can make the priority decision.

### 4. Guided validation flow

Guide the developer from a proposed change to a completed test.

The flow should:

- Inspect existing datasets, examples, and evaluators.
- Recommend only the missing coverage.
- Let the developer run experiments from the issue.
- Explain when a PR-version-only experiment is sufficient.
- Offer a baseline comparison when relative change matters.
- Tie each result to the tested PR commit and evaluation setup.
- Compare results and summarize remaining risk.

### 5. Unified, resumable Fix workspace

Coordinate the PR, evaluator, examples, experiments, CI, and review state in one place.

Show:

- What exists
- Which versions are current
- What changed
- Which results are missing, stale, failed, or passing
- What is blocked
- The recommended next action

### 6. Snooze with return conditions

Let the developer remove an issue from the To review queue until:

- A chosen date
- The same pattern occurs again
- Frequency, scope, or severity reaches a threshold
- A chosen number of additional sessions is affected

Keep three concepts separate:

- **Return condition** — what brings the issue back
- **Detection** — Engine matching and an optional issue-specific evaluator
- **Notification destination** — LangSmith, Slack, email, or another configured channel

Snoozed issues should remain discoverable through View options. When the condition is met, return the issue to To review with a **Returned** label and a summary of what changed.

### 7. Clear triage and outcome states

Use four primary views:

```text
To review
Active
Resolved
Ignored
```

- **To review** — requires an intentional decision
- **Active** — remediation is underway
- **Resolved** — the developer believes the issue was fixed
- **Ignored** — the issue was deliberately dismissed with a reason

Snooze is an attention action, not another status. It temporarily hides an issue from To review until its return condition is met and remains discoverable through View options.

### 8. Return reason and issue history

When an issue returns, lead with:

- The condition that brought it back
- The date of the previous decision
- New evidence since that decision
- Current versus previous frequency, scope, and impact
- Affected agent version or deployment
- Previous fix and validation outcome, when applicable

Keep the original detection, triage decision, fix, resolution, snooze periods, and recurrences in one history.

### 9. Structured dismissal feedback

Capture why an issue left active triage:

- Incorrectly flagged
- Expected behavior
- Not relevant
- Duplicate
- Acceptable risk
- Insufficient impact

This makes the decision understandable and creates feedback about issue quality and relevance.

## How the opportunities map to the triage journey

### Assess the issue

Addresses the questions **Is this real?** and **Is it worth addressing?**

- Explainable issue summary
- Guided trace proof
- User-impact and scope breakdown

### Fix the issue

Addresses **How should I validate the proposed change?** and **How do I continue if the work spans multiple sessions?**

- Guided validation flow
- Unified, resumable Fix workspace

### Revisit the issue

Addresses **How can I defer this intentionally and understand why it returned?**

- Snooze with return conditions
- Return reason and issue history

### Complete triage

Addresses **What state is the issue in, and why did it leave active triage?**

- Clear triage and outcome states
- Structured dismissal feedback

## Part 2 scoping recommendation

Do not attempt to prototype the entire desired triage journey. The opportunities overlap because they share the same issue and artifacts, but each can still be evaluated as a focused product slice.

### Recommended focus: explainable issue assessment

Focus Part 2 on the moment between opening an Engine issue and choosing Fix, Snooze, or Dismiss.

The specific problem is:

> Engine provides a conclusion, recurrence data, linked traces, and a likely cause, but the developer must still connect them to determine what was directly observed, whether the pattern is coherent, what consequence occurred, and how much confidence to place in the diagnosis.

The prototype should show:

1. **Issue claim** — expected behavior, observed behavior, and consequence
2. **Pattern and scope** — numerator, denominator, affected sessions, trend, and relevant breakdowns
3. **Representative trace proof** — the decisive spans and why they support the claim
4. **Diagnosis** — likely cause clearly separated from observed facts
5. **Uncertainty** — missing evidence or credible alternatives
6. **Triage actions** — Fix, Snooze, and Dismiss after the evidence has been reviewed

Keep raw traces available, but do not redesign the complete trace viewer. Demonstrate the handoff from the issue-level explanation to one highlighted trace.

This scope combines opportunities 1–3 because together they answer one decision:

> Is this a real problem with enough impact to deserve action?

### Alternative focus: validation checkpoint inside the Fix workspace

Guided validation and the resumable Fix workspace can be combined, but only around one checkpoint:

> Given a proposed PR, available examples, and available evaluators, what validation can the developer run now, and what do the results mean?

The prototype should begin after the issue has already been accepted and a proposed fix exists. Show:

- Linked PR and current commit
- Existing and missing test coverage
- Available dataset examples and evaluators
- The validation that can run with the current artifacts
- Latest result: missing, stale, failed, or passing
- Failing examples and evaluator explanations
- Recommended next action

Do not also redesign issue assessment, PR authoring, the complete experiment product, CI, review, merge, and post-deployment monitoring. Those remain connected context rather than part of the prototype.

### Recommendation

Choose the **explainable issue assessment** for Part 2.

It is the earliest trust decision in the journey, directly addresses the provided authentication scenario, and can be demonstrated without assuming that Engine can execute arbitrary PR code or reproduce every production environment. It also creates a clear improvement over the current page: not more evidence, but a visible chain from claim to proof, impact, diagnosis, and uncertainty.

If the Fix experience is more compelling, choose the narrower **validation checkpoint**, not the entire unified Fix workspace.

## Validation

### Product analytics

Measure:

- Time from opening an issue to choosing an outcome
- Percentage of issues where linked traces are opened
- Time spent locating relevant spans after opening a trace
- Number of traces inspected before acting
- Issues left in To review without a decision
- Snoozed issues whose return conditions are changed or canceled
- Fix flows abandoned after creating one artifact
- Experiments rerun because earlier results became stale
- Decisions later reversed

### User research

Observe AI engineers triaging several issue types:

- What evidence they inspect first
- Whether they can locate the relevant evidence inside a trace
- What increases or reduces trust
- How they judge impact and priority
- How they decide whether validation is sufficient
- Where they leave LangSmith for more context
- What they expect Snooze, recurrence detection, and notifications to do
- What they need when returning to unfinished work

## Sources

- [LangSmith Engine documentation](https://docs.langchain.com/langsmith/engine)
- [Introducing LangSmith Engine](https://www.langchain.com/blog/introducing-langsmith-engine)
- [Sentry Issue Details](https://docs.sentry.io/product/issues/issue-details/)
- [Datadog Watchdog Root Cause Analysis](https://docs.datadoghq.com/watchdog/rca/)
- [Honeycomb BubbleUp](https://docs.honeycomb.io/investigate/analyze/identify-outliers/)

