# LangSmith Engine: Desired Triage Journey

## Goal

Help a developer understand a production issue, decide whether it deserves action, and move it toward one of three outcomes:

- **Fix** — address the issue now
- **Defer** — return on a date or when conditions change
- **Ignore** — remove it from active triage with a recorded reason

The journey must preserve context across interrupted work, failed validation, and recurrence after a fix.

## Journey overview

```text
New issue
    ↓
Assess whether it is real
    ↓
Decide whether it is worth addressing
    ↓
Choose whether to act now
    ├── Fix
    ├── Defer
    └── Ignore
```

## 1. New issue

Engine notifies the developer that it found a recurring production problem.

The issue overview should show:

- What behavior appears to be wrong
- What should have happened instead
- Severity and affected population
- Frequency with a clear denominator
- When the pattern began and how it is trending
- Representative traces
- Likely cause and supporting evidence
- Relevant deployment, prompt, model, or tool changes

## 2. Assess the issue

### Is this a real problem?

The developer evaluates whether:

- The traces demonstrate the claimed behavior
- The traces belong to the same pattern
- The expected behavior is reasonable
- The recurrence estimate is credible
- The proposed cause has sufficient support

If not, the developer moves to **Ignore** and records why the issue was incorrectly flagged or not useful.

### Is this worth addressing?

A real problem may still be low value.

The developer considers:

- User and business impact
- Frequency and trend
- Severity
- Relevance to the team
- Cost and risk of remediation
- Whether the behavior is an accepted limitation

If it is not worth addressing, the developer can Ignore it as acceptable risk, insufficient impact, or not relevant.

### Should I act now or later?

If the issue is real and valuable:

- **Act now** → Fix
- **Return on a date** → Defer with a reminder
- **Return if it continues or worsens** → Defer with monitoring

## 3. Fix

Choosing Fix opens a workspace around the issue.

The developer can independently:

- Open or link a PR
- Add issue-specific offline examples
- Create or review an evaluator

These actions produce different artifacts:

- A proposed agent, prompt, or code version
- Dataset examples that improve test coverage
- An evaluator that grades the behavior

They are not mandatory sequential steps. The workspace should show what exists, what coverage is missing, and what validation is currently possible.

### Validate the proposed fix

Possible validation paths include:

- **PR-version-only experiment** — verifies that the proposed version meets the required criteria
- **Baseline and PR-version comparison** — measures relative change using the same dataset and evaluators
- **Manual replay** — checks known production inputs when automated coverage is not ready, with lower confidence clearly stated

A baseline comparison is useful when relative improvement matters. It is not mandatory when a PR-version-only experiment can establish that the proposed version passes the required behavior and broader regression coverage.

### If validation fails

Engine should:

1. Show failing examples and evaluator reasons.
2. Confirm whether results match the current PR commit.
3. Preserve completed artifacts.
4. Return the developer to the PR.
5. Rerun affected tests after the fix changes.

### If the developer returns mid-fix

Engine should synchronize:

- PR and commit state
- CI state
- Evaluator and dataset changes
- Latest experiments
- Review comments

The issue should summarize:

- What is complete
- What changed
- What is stale
- What is blocked
- The recommended next action

### Fix completion

The Fix path is complete when:

- The chosen validation is accepted
- The fix is merged or deployed
- The issue is **Resolved**
- The fix and validation outcome remain attached to the issue history

Monitoring may continue after resolution, but it does not determine whether the fix is complete.

## 4. Defer

Defer is an intentional decision to return later. It should not mean leaving an issue Open without a plan.

### Time-based reminder

Use when the issue matters but the developer cannot address it now.

- Choose a date or time
- Keep the issue Open
- Notify the developer when the date arrives
- Return with the latest evidence

### Recurrence-based monitoring

Use when the issue is not urgent unless it continues or worsens.

- Choose a recurrence, frequency, or severity condition
- Choose the notification destination
- Optionally create an issue-specific evaluator
- Keep the issue Open with monitoring active

Creating an evaluator and configuring a reminder are independent:

- The evaluator grades behavior.
- The reminder rule determines when and where the developer is notified.

### Defer completion

The session is complete for now when:

- A return condition is saved
- The notification destination is clear
- The issue remains Open
- The active reminder or monitoring rule is visible

When the condition is met, Engine should notify the developer, move the issue to the top of the relevant view, and highlight what changed.

## 5. Ignore

Ignore removes an issue from active triage without fixing it.

The developer records a reason:

- Incorrectly flagged
- Expected behavior
- Not relevant
- Duplicate
- Acceptable risk
- Insufficient impact

These reasons distinguish "Engine was wrong" from "Engine was right, but this is not worth fixing."

### Ignore completion

The Ignore path is complete when:

- The issue leaves active triage
- Its disposition and reason are recorded
- The decision remains visible in issue history
- The developer can revisit it if the judgment changes

## 6. Recurrence after resolution

If the same failure pattern appears after a fix, Engine should return the existing issue to Open.

The issue should show:

- A **Recurrence after fix** label
- New traces
- Updated frequency, scope, and impact
- The affected deployment or agent version
- The previous fix and validation outcome
- What differs from the earlier episode

The developer then decides whether to:

- Fix again
- Defer with a new return condition
- Ignore the new occurrence

If the behavior is materially different, Engine should create a new issue and link it to the earlier one.

## State summary

### Fix

```text
Open → Fix in progress → Validation accepted → Resolved
```

### Defer

```text
Open → Reminder or monitoring active → Condition met → Review again
```

### Ignore

```text
Open → Reason recorded → Removed from active triage
```

### Recurrence

```text
Resolved → Same pattern detected → Open with recurrence context
```

