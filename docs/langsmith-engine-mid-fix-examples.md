# LangSmith Engine: Returning Mid-Fix

## What “returning mid-fix” means

A developer started addressing an Engine issue, left before completing the fix, and later reopened the issue.

The important product challenge is not restoring the previous screen. Engine must synchronize the durable state that may have changed while the developer was away:

- Pull request and commit
- CI status
- Offline examples
- Evaluator
- Experiment results
- Review feedback
- Reproduction environment
- Known blockers

Engine should then show:

```text
What is complete?
What changed while I was away?
What is blocked?
What should I do next?
```

## Example 1: Experiment failures

```text
Developer opens PR
→ Adds 3 offline examples
→ Creates evaluator
→ Experiment on the PR version fails 2 cases
→ Developer leaves
→ Developer returns
→ Reviews the 2 failing examples
→ Updates PR
→ Reruns experiment
```

### What the developer should see

- Linked PR and current commit
- Latest experiment marked **Failed**
- Two failing examples with evaluator scores and reasons
- Which evaluator, dataset, model, and configuration were used
- Whether the experiment result still matches the current PR commit
- Passing work that does not need to be repeated

### Recommended next action

> Review the two failing examples, update the PR, and rerun the affected experiment cases.

## Example 2: CI is still running

```text
Developer opens PR
→ CI starts
→ Developer leaves
→ CI fails
→ Developer returns
→ Reviews failed checks
→ Updates PR
```

### What the developer should see

- PR status and current commit
- CI changed from **Running** to **Failed**
- Failed checks and concise failure summaries
- Links to the relevant logs
- Whether candidate experiments passed, failed, or have not run
- Whether any previous validation became stale after a PR update

### Recommended next action

> Open the first actionable CI failure, update the PR, and rerun the failed checks before continuing validation.

## Example 3: Previous validation became stale

```text
Experiment on PR version passes
→ Reviewer requests code changes
→ Developer updates PR
→ Previous experiment no longer represents the latest commit
→ Developer leaves
→ Developer returns
→ Engine marks the previous result as stale
→ Developer reruns the experiment on the latest commit
```

Validation may become stale when:

- The PR commit changes
- The evaluator changes
- The dataset changes
- The model or configuration changes
- The environment changes materially

### What the developer should see

- Previous experiment marked **Stale**
- Commit tested by the previous experiment
- Current PR commit
- The exact change that invalidated the result
- Whether the dataset, evaluator, model, or environment also changed
- Previous results retained for context but excluded from current readiness

### Recommended next action

> Rerun the experiment using the latest PR commit and current evaluation setup.

## Example 4: Offline examples await review

```text
Engine proposes 10 offline examples
→ Developer reviews 4
→ Remaining examples enter the annotation queue
→ Developer leaves
→ Developer returns
→ Continues reviewing the remaining 6 examples
```

### What the developer should see

- Four of ten examples reviewed
- Six examples remaining in the annotation queue
- Dataset destination
- Proposed inputs, reference outputs, and assertions
- Examples edited, accepted, skipped, or marked ambiguous
- Whether an experiment is waiting for this coverage

### Recommended next action

> Continue with the next unreviewed example, then add approved examples to the dataset.

## Example 5: Evaluator judgments are unreliable

```text
Developer creates evaluator
→ Tests it on linked traces
→ Evaluator incorrectly passes a known failure
→ Developer leaves
→ Developer returns
→ Revises evaluator criteria
→ Retests evaluator
```

### What the developer should see

- Evaluator definition and latest saved version
- Known failure that the evaluator incorrectly passed
- Other false-positive or false-negative examples
- Evaluator score, reasoning, and expected judgment side by side
- Runs already used to test the evaluator
- Whether the evaluator is attached to a dataset or production project

### Recommended next action

> Revise the evaluator criteria and retest it against known failures and successful counterexamples before relying on its scores.

## Example 6: Production failure cannot be reproduced

```text
Developer opens PR
→ Adds production traces as offline examples
→ Local replay does not reproduce the failure
→ Developer identifies missing environment or state
→ Developer leaves while arranging test credentials
→ Developer returns
→ Configures the required environment
→ Runs the experiment
```

Examples of missing conditions include:

- Expired credentials
- Tenant permissions
- External provider state
- Checkpoint or thread state
- A particular document-index version
- Production network behavior

### What the developer should see

- Reproduction status marked **Blocked**
- Production trace and offline examples already captured
- Environment or state believed to be missing
- Local replay result and how it differed from production
- PR, evaluator, and dataset work already completed
- Credentials, sandbox, mock, checkpoint, or index version still required

### Recommended next action

> Configure or mock the missing production condition, then rerun the affected examples before treating the fix as validated.

## Example 7: PR receives review feedback

```text
Developer validates the PR version
→ Opens PR for review
→ Reviewer requests changes
→ Developer leaves
→ Developer returns
→ Reviews requested changes
→ Updates PR
→ Reruns affected tests
```

### What the developer should see

- PR review status and unresolved comments
- Files and behavior affected by requested changes
- Current PR commit
- Validation result associated with the previous commit
- Which tests or experiments must be rerun after the changes
- Evaluator and dataset artifacts that remain reusable

### Recommended next action

> Address the requested changes, update the PR, and rerun the validation affected by those changes.

## Example 8: Long-running experiment completes later

```text
Developer starts experiment
→ Agent trials take 20 minutes each
→ Developer leaves
→ Experiment completes
→ Developer returns
→ Reviews failed trials
→ Decides whether to update the PR
```

### What the developer should see

- Experiment status changed from **Running** to **Complete**
- PR commit and configuration tested
- Passed and failed trial counts
- Failed trials grouped by failure mode
- Evaluator scores, verifier results, artifacts, duration, and cost
- Whether the PR changed while the experiment was running

### Recommended next action

> Review the highest-severity failed trials. Update the PR and rerun them, or continue toward merge if the result meets the acceptance criteria.

## Example 9: PR merges while the developer is away

```text
Developer opens a validated PR
→ Teammate merges it
→ Developer returns to the Engine issue
→ Engine detects the merged PR
→ Developer reviews the outcome
→ Marks the issue Resolved
```

### What the developer should see

- PR status changed to **Merged**
- Merged commit and merge time
- Latest experiment and CI results
- Whether those results tested the merged commit
- Deployment status, when available
- Online evaluator or recurrence monitoring status
- Engine issue still awaiting resolution

### Recommended next action

> Confirm the merged version was adequately validated and deployed, then mark the issue Resolved and keep monitoring active if desired.

## Example 10: PR closes without merging

```text
Developer opens PR
→ PR is closed or superseded
→ Developer returns
→ Chooses to replace the PR, abandon the fix, or defer the issue
```

### What the developer should see

- PR status changed to **Closed without merge**
- Closure reason, when available
- Whether a replacement PR exists
- Latest validation result and tested commit
- Offline examples and evaluator retained
- Issue remains unresolved

### Recommended next action

> Choose whether to reopen or replace the PR, abandon the fix while retaining evaluation coverage, or defer the issue with a reminder condition.

## Recommended desired flow

```text
Developer returns to unfinished Fix
        ↓
Synchronize PR, CI, evaluator, dataset, and experiment state
        ↓
Show current status and recommended next action
        ↓
Is the latest validation still current?
├── No result → Run experiment
├── Stale result → Rerun experiment
├── Failed result → Review failures and update PR
└── Current passing result → Continue to review or merge
```

## Best examples to include in the triage map

The highest-value examples are:

1. **Experiment failed:** Shows resumption inside the fix loop.
2. **Validation became stale:** Shows why Engine must associate results with a specific PR version and evaluation setup.
3. **PR changed while away:** Shows why Engine must synchronize external state rather than merely restore the last UI screen.

These examples demonstrate that “returning mid-fix” is a state-reconciliation problem, not a navigation problem.
