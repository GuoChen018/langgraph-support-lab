# Desired Triage Flow: Silent Authentication Failures

## Scenario

> Engine has been running on my production tracing project for three days. I got a notification that it found a new issue: a recurring authentication error silently failing in about 12% of my agent's tool calls. I need to understand whether this is real, decide what to do about it, and either fix it or make sure I hear back if it keeps happening.

This document maps a desired UX for this specific issue. It is intentionally concrete rather than a general framework for every Engine issue.

For the reusable evidence-layer model, see [Designing a General Evidence Layer for LangSmith Engine](./langsmith-engine-evidence-layer.md).

## What may actually be failing

The notification may combine two related failures:

1. **The tool cannot authenticate.**
   - A credential is missing, expired, malformed, or sent to the wrong environment.
   - The tool returns `401`, `403`, or an authentication exception.

2. **The agent handles that failure incorrectly.**
   - It does not refresh credentials.
   - It does not retry.
   - It suppresses the error.
   - It continues as though the tool succeeded.
   - It gives the user a misleading response.

The second failure may be more important than the authentication error itself. Authentication errors can be expected; silently claiming success after one is not.

## Desired journey

```text
Engine notification
        ↓
Review issue summary and evidence
        ↓
Is this a real, valuable issue?
   ├── Yes, act now → Fix
   ├── Possibly, need more evidence → Watch
   └── No → False positive
```

---

# 1. Notification

The notification should provide enough information to establish urgency without requiring the developer to open raw traces immediately.

```text
New high-priority issue

Authentication errors silently fail in account-management tool calls

- 84 failures across 700 eligible calls
- 12% failure rate during the last 72 hours
- 51 user sessions affected
- Increased after agent version v43
- Some final responses incorrectly implied success
```

Primary action:

> Review issue

The notification should avoid presenting Engine’s root-cause hypothesis as a confirmed fact.

---

# 2. Issue overview

The issue page should begin with a concrete claim:

```text
Affected behavior
Calls to account_management fail authentication.

Agent behavior
The agent continues without recovering or disclosing the failure.

Observed conditions
Most failures involve expired OAuth access tokens.

Prevalence
84 of 700 account-management calls during the last 72 hours.

Consequence
Some users receive confirmation even though the requested action was not completed.
```

The developer should immediately understand:

- What failed
- Where it failed
- How often it failed
- Whether users were affected
- Why Engine considers the failures one pattern
- What remains uncertain

---

# 3. Evidence review

## 3.1 Verify the 12% claim

The developer needs a transparent denominator:

```text
84 authentication failures
out of 700 calls to account_management
across 63 traces
and 51 user sessions
from the production project
during the last 72 hours
```

The UI should clarify:

- Whether retries count as separate calls
- Whether one trace can contain multiple failures
- Whether test or staging traffic is included
- Whether Engine analyzed all calls or a sample
- Whether calls with incomplete tracing were excluded

Without this context, “12%” could overstate or understate the problem.

## 3.2 Show recurrence over time

The issue should show:

- First occurrence
- Most recent occurrence
- Failure rate by hour or day
- Whether the trend is increasing
- Nearby deployments or configuration changes
- Credential rotations or provider incidents

Example:

```text
Before agent v43: 2% authentication failure rate
After agent v43: 18% authentication failure rate
Current three-day average: 12%
```

This supports—but does not prove—the hypothesis that v43 contributed to the issue.

## 3.3 Show scope

Break the issue down by relevant dimensions:

```text
By tool
- account_management: 79 failures
- billing_history: 5 failures

By authentication state
- expired access token: 61
- missing token: 14
- unknown: 9

By tenant
- two tenants account for 40% of failures
- remaining failures distributed across 49 sessions

By version
- v42: 2%
- v43: 18%
```

This helps distinguish:

- An agent regression
- A tool-specific integration problem
- A tenant configuration problem
- A credential-provider incident
- A tracing or clustering error

## 3.4 Explain the cluster

Engine should explain:

> These traces were grouped because `account_management` returned the same authentication error, the agent did not complete a successful recovery, and the final response did not disclose the failed action.

The developer should see:

- Shared error signature
- Shared tool
- Shared failure-handling behavior
- Shared downstream outcome
- Important differences within the cluster
- Engine’s clustering confidence

This reveals whether Engine found one coherent issue or mixed unrelated authentication failures.

## 3.5 Present curated traces

The linked-trace section should identify why each selected trace matters.

### Canonical trace

```text
User asks to update account information
→ Agent calls account_management
→ Tool returns 401: token expired
→ Agent does not refresh or retry
→ Agent tells the user the update succeeded
```

### Most severe trace

A failure that caused the largest user or system consequence.

### Most common trace

The trajectory that best represents the majority of the cluster.

### Boundary trace

An ambiguous case that tests whether Engine’s cluster is too broad.

### Counterexample

```text
Tool returns 401
→ Agent refreshes the token
→ Retry succeeds
→ User receives an accurate response
```

The counterexample lets the developer understand what correct recovery looks like and whether similar successful traces were incorrectly included.

## 3.6 Highlight the decisive spans

For each representative trace, emphasize:

- The agent decision that triggered the tool
- Tool name and sanitized arguments
- Authentication error type
- Credential refresh attempt, if any
- Retry behavior
- How the tool result was returned to the model
- Subsequent agent action
- Final response
- User or evaluator feedback

The developer should not need to expand every trace span to understand the failure.

## 3.7 Compare expected and observed behavior

```text
Expected
- Refresh an expired token and retry once.
- If recovery fails, tell the user the action was not completed.
- Never claim success after a failed tool call.

Observed
- No token refresh occurred.
- No successful retry occurred.
- The failure was not disclosed.
- The response implied that the action succeeded.
```

This behavioral gap can later become the fix’s acceptance criteria.

## 3.8 Present diagnosis as a hypothesis

Engine might propose:

> Agent v43 stopped forwarding refresh tokens to account-management tool calls.

The developer should see:

- Code or configuration implicated
- Deployment correlation
- Evidence supporting the hypothesis
- Evidence against it
- Alternative explanations
- Confidence
- Missing instrumentation

The developer should be able to accept the issue while rejecting Engine’s diagnosis.

## 3.9 Summarize the decision

Before showing triage actions:

```text
Why this likely matters
- Recurs across 51 user sessions.
- Increased after v43.
- Can produce false confirmation messages.

What remains uncertain
- Token expiration is not visible in nine traces.
- Two tenants account for a disproportionate share.

Engine recommendation
- Fix now.
- Reproduce an expired-token state before merging.
```

The developer chooses:

- Fix
- Watch
- False positive

---

# 4. Fix path

## 4.1 Enter a resumable Fix workspace

The workspace should preserve:

- Issue evidence
- Root-cause hypothesis
- Linked PR
- Offline examples
- Evaluator
- Validation environment
- Experiment history
- Blockers
- Recommended next action

The PR, offline examples, and evaluator should be shown as independent workstreams—not mandatory sequential steps.

## 4.2 Remediate the behavior

Create or link a PR that may:

- Restore credential propagation
- Refresh expired tokens
- Retry recoverable failures
- Limit retry loops
- Surface unrecoverable failures
- Prevent false success responses

Possible PR states:

- Not started
- Draft
- Open
- Changes requested
- Approved
- Merged
- Closed without merge

## 4.3 Add issue-specific offline examples

Candidate examples include:

### Expired token with successful recovery

```text
Input
User requests an account update.

Environment
Access token is expired; refresh token is valid.

Expected
Refresh credentials, retry once, complete the update, and respond accurately.
```

### Expired token with failed recovery

```text
Input
User requests an account update.

Environment
Access and refresh tokens are invalid.

Expected
Do not claim success. Explain that the action could not be completed.
```

### Missing credentials

```text
Expected
Do not repeatedly retry. Surface the configuration or authentication problem safely.
```

### Valid credentials

```text
Expected
Call the tool normally without triggering unnecessary refresh behavior.
```

These examples give the candidate explicit coverage of the production issue and nearby edge cases.

## 4.4 Create or reuse an evaluator

The evaluator may check:

- Did authentication fail?
- Was recovery attempted when appropriate?
- Did retry behavior remain within limits?
- Was the final tool outcome represented accurately?
- Did the agent claim success after a failed call?
- Was an unrecoverable error disclosed clearly?

The same evaluator can be used:

- Offline on dataset experiments
- Online on production traces

The attachments determine where it runs.

## 4.5 Show validation readiness without imposing sequence

### PR and existing dataset only

Run the candidate against the existing suite and inspect available results. Clearly state that the production authentication cases may not be covered.

### PR and issue-specific examples, without a suitable evaluator

Replay the issue cases and review the outputs and tool trajectories manually.

### PR and evaluator, without issue-specific examples

Score the candidate on the existing dataset. Show:

> The evaluator is available, but the production authentication failures are not explicitly represented in this dataset.

### PR, issue-specific examples, and evaluator

Run a scored candidate experiment over the enriched dataset.

## 4.6 Reproduce the authentication state

This is the scenario’s most important validation edge case.

The production input alone may not reproduce:

- An expired token
- Missing credentials
- OAuth refresh state
- Tenant permissions
- Provider availability
- Network policy
- Secret-store configuration

The Fix workspace should ask:

> Can the validation environment reproduce the authentication state that caused the issue?

Possible actions:

- Use an expired test token in a sandbox
- Mock an authentication-provider response
- Add a deterministic integration test
- Configure a safe staging tenant
- Mark environment setup as blocking validation

An offline example without the required environment state may produce a false sense of coverage.

## 4.7 Run candidate validation

Acceptance criteria:

- Valid credentials continue working
- Expired credentials refresh when recovery is possible
- Recovery does not loop
- Unrecoverable failures are disclosed
- Failed calls never produce success claims
- Existing quality, latency, and cost thresholds remain acceptable

A candidate-only experiment is enough when these criteria have meaningful thresholds.

An optional baseline comparison can answer:

> How did the candidate change relative to the current version?

It is not automatically required.

## 4.8 Handle failed tests

If the candidate fails:

```text
Candidate fails authentication-recovery assertion
        ↓
Show failing example and decisive spans
        ↓
Update PR
        ↓
Rerun affected tests
        ↓
Rerun broader suite when ready
```

Preserve the dataset, evaluator, environment, and experiment history throughout the loop.

## 4.9 Handle an interrupted fix

If the developer leaves, mark the issue:

> Fix in progress

On return, show:

```text
Completed
- PR opened
- Evaluator configured

Blocked
- Expired-token test environment not configured

Latest result
- Existing suite passed
- Production failure not yet reproduced

Recommended next action
- Configure an expired-token sandbox and run the four issue-specific examples.
```

The developer should not need to reconstruct the workflow manually.

## 4.10 Handle a PR closed without merging

Ask whether to:

- Replace or reopen the PR
- Abandon the fix but retain evaluation artifacts
- Move the issue to Watch
- Return to open triage

Do not delete examples or evaluators automatically.

## 4.11 Complete the fix

When the PR is merged and validation is accepted:

- Mark the issue **Resolved**
- Record the PR
- Record the candidate experiment
- Record known validation gaps
- Keep the online evaluator active if deployed

Done means:

> The code change shipped, the outcome was recorded, and recurrence can be detected.

If the same behavior returns, Engine automatically reopens the issue with new evidence.

---

# 5. Watch path

Watch is appropriate when:

- The issue seems plausible but evidence is incomplete
- Impact is currently too low to prioritize
- The developer suspects a temporary provider incident
- The failure may be isolated to a small number of tenants
- The developer wants a clearer recurrence pattern before changing code

## 5.1 Configure the watch

The developer confirms:

- Matching tool and error signature
- Whether “silent failure” is required for a match
- Affected environment
- Rate or count threshold
- Time window
- Notification destination

Example:

```text
Notify me if:
- silent authentication failures exceed 5% of account-management calls
- during any rolling one-hour period
- or affect more than 10 unique user sessions
```

An online evaluator can provide a more precise signal by detecting whether the agent mishandled the authentication failure, rather than merely counting `401` responses.

## 5.2 Activate Watch

The issue state becomes:

> Watch active

The issue remains open. Done for the current session means:

- Resurface condition saved
- Notification destination confirmed
- Current evidence snapshot recorded

## 5.3 Resurface the issue

When the condition is met, Engine should show:

```text
Authentication issue resurfaced

Previous rate: 12%
Current rate: 19%
New failures: 43
Newly affected sessions: 28
Scope change: billing_history is now affected
```

Also show:

- New representative traces
- Whether the cluster changed
- Whether impact increased
- Relevant deployments or incidents
- What changed since the developer chose Watch

The developer chooses:

- Fix now
- Keep watching
- Resolve
- Mark as False positive

---

# 6. False-positive path

Possible conclusions:

- Test traffic polluted the production project
- Authentication failures were expected
- Automatic retries recovered successfully
- Users were not misled
- Engine grouped unrelated errors together
- The denominator was misleading
- The affected integration is deprecated
- The behavior is real but not valuable enough to track

The developer selects a reason and may add a scope correction:

```text
Incorrectly flagged

Reason
These failures came from synthetic monitoring traffic.

Correction
Exclude traces tagged traffic_type=synthetic from future clustering.
```

Done means:

- Issue marked **Incorrectly flagged**
- Reason recorded
- Active watching stopped
- Manual reopen remains available

---

# 7. Post-fix recurrence

Closing the issue does not have to stop monitoring.

```text
PR merged
→ Candidate accepted
→ Issue marked Resolved
→ Online evaluator continues monitoring
→ Same failure pattern detected
→ Issue automatically reopened
```

The reopened issue should preserve the previous resolution and explain:

- What is recurring
- Whether the failure signature is identical
- Which versions are now affected
- Whether severity changed
- Whether the previous fix is still deployed
- Whether this is likely a regression or a related new issue

---

# Highest-friction moments in this scenario

## 1. Determining whether the issue represents user impact

A `401` span alone does not prove an agent failure. The developer must determine whether recovery succeeded and whether the user received a misleading outcome.

## 2. Trusting the recurrence claim

The developer must understand the denominator, retries, sampling, traffic source, and cluster boundaries behind “12%.”

## 3. Reproducing production authentication state

Trace inputs do not automatically preserve credentials, token expiration, tenant permissions, provider behavior, or network configuration.

## 4. Turning evidence into validation

The expected behavior must become environment setup, examples, assertions, evaluator logic, or integration tests.

## 5. Coordinating multiple artifacts

The PR, dataset, evaluator, experiment, sandbox, and issue status may all progress independently.

## 6. Returning mid-fix

The developer needs to understand what is completed, what failed, what is blocked, and what to do next.

# Biggest design opportunity in this scenario

The strongest opportunity is a **resumable authentication-issue workspace that carries production evidence into reproducible validation**.

Its most valuable behavior would be recognizing that:

```text
PR ready
Evaluator ready
Offline examples ready
Authentication environment not reproducible
```

does not mean the fix is ready to merge.

The workspace should identify the missing environment prerequisite, preserve all completed work, and guide the developer toward the next useful action.

## References

- [LangSmith Engine overview](https://docs.langchain.com/langsmith/engine-overview)
- [Find and fix issues with LangSmith Engine](https://docs.langchain.com/langsmith/engine)
- [LangSmith evaluators](https://docs.langchain.com/langsmith/evaluators)
