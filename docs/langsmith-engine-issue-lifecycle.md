# LangSmith Engine Issue Lifecycle

## Lifecycle model

Use four user-facing states:

```text
To review
Active
Resolved
Ignored
```

This model separates issues that require a decision from issues that have already been reviewed. It avoids introducing separate lifecycle states for fixing, planning, monitoring, and reminders.

## To review

The issue requires an intentional decision now.

An issue appears here when:

- Engine detects it for the first time.
- A reminder becomes due.
- A configured recurrence condition is met.
- The same failure returns after the issue was resolved.

Examples:

```text
To review · New issue
To review · Reminder due
To review · Recurrence
To review · Severity increased
```

The primary actions are:

```text
Fix
Remind me
Dismiss
```

## Active

The developer reviewed the issue, it remains relevant, and Engine should continue handling it according to that decision.

Active does not mean that someone is currently fixing the issue. It can include:

- A fix that is being prepared or validated.
- A reminder scheduled for a future date.
- A recurrence condition that Engine is monitoring.
- An issue-specific evaluator added to improve detection.

Instead of adding sub-statuses such as **Todo**, **In progress**, **Monitoring**, or **Waiting**, each Active issue shows one plain-language field:

```text
What happens next
```

Examples:

```text
What happens next: Notify me when this failure recurs
What happens next: Remind me on September 3
What happens next: Review validation failures in PR #142
What happens next: Merge PR #142 after approval
```

Supporting context can show what has already been done:

```text
Evaluator enabled
3 offline examples added
PR #142 open
Latest experiment failed
```

These details explain the state of the work without creating additional lifecycle categories.

## Resolved

The developer believes the issue has been fixed.

Examples:

```text
Resolved · PR merged
Resolved · Context Hub update published
Resolved · Manual fix confirmed
```

Resolved describes the outcome more clearly than **Completed**, which usually describes a task, or **Closed**, which does not explain why the issue is no longer active.

If the same failure returns, the issue moves back to **To review** with its previous fix history and updated evidence:

```text
Resolved
    ↓
Same failure pattern returns
    ↓
To review · Recurrence
```

## Ignored

The developer intentionally dismissed the issue without fixing it.

A reason should be required:

```text
Ignored · Incorrectly flagged
Ignored · Expected behavior
Ignored · Accepted risk
Ignored · Low impact
Ignored · Duplicate
```

The reason distinguishes a detection problem from a deliberate decision not to address a real issue.

## Status follows the decision, not individual artifacts

Adding an evaluator is ambiguous by itself:

- It can help validate a fix.
- It can improve ongoing recurrence detection.

Creating an evaluator, adding examples, or opening an experiment should not independently determine lifecycle status.

### Evaluator used during a fix

```text
To review
    ↓
Choose Fix
    ↓
Active
    ↓
Add evaluator and validate the proposed fix
```

### Evaluator used for recurrence detection

```text
To review
    ↓
Choose Remind me when this happens again
    ↓
Active
    ↓
Optionally add an evaluator for more precise detection
```

Both cases remain Active until they require another decision or reach an outcome.

## Complete transition model

### Fix

```text
To review
    ↓
Choose Fix
    ↓
Active
    ↓
Create, validate, and merge the fix
    ↓
Resolved
```

### Remind me on a date

```text
To review
    ↓
Choose a future date
    ↓
Active
What happens next: Remind me on September 3
    ↓
Date arrives
    ↓
To review · Reminder due
```

### Notify me on recurrence

```text
To review
    ↓
Choose a recurrence condition
    ↓
Active
What happens next: Notify me when this failure recurs
    ↓
Condition is met
    ↓
To review · Recurrence
```

### Ignore

```text
To review
    ↓
Choose Dismiss
    ↓
Record a reason
    ↓
Ignored
```

## Issue-list navigation

Use four top-level views:

```text
To review
Active
Resolved
Ignored
```

Suggested default sorting:

- **To review** — Priority first, then the newest qualifying signal.
- **Active** — Priority first, then most recently updated.
- **Resolved** — Most recently resolved.
- **Ignored** — Most recently ignored.

Active issues should show **What happens next** directly in the list. This provides an at-a-glance record of the developer's decision without requiring additional status tabs or sub-statuses.

## Alternatives considered

### Open, In progress, Resolved, and Ignored

This model used **Open** for both unreviewed issues and issues that had been deliberately deferred.

Why it was not selected:

- Open did not clearly distinguish issues still awaiting triage from issues that had already received a decision.
- In progress implied active remediation, which was misleading when the developer had only configured a reminder or recurrence notification.
- Adding an evaluator could support either fixing or monitoring, so it could not reliably determine whether an issue was In progress.

### To review, Todo, In progress, Waiting, Resolved, and Ignored

This model gave each stage of planning, fixing, and deferral its own status.

Why it was not selected:

- Six statuses created too much lifecycle complexity for the core triage flow.
- Waiting was an unnatural label for issues being monitored or intentionally deferred.
- Todo and In progress pushed Engine toward becoming a full project-management system.
- The same issue could move through unnecessary statuses even when the developer only wanted a recurrence notification.

### To review, Active, Resolved, and Ignored with Active sub-statuses

This model introduced categories such as **Fixing**, **Planned**, and **Monitoring** beneath Active.

Why it was not selected:

- The categories added another status system for developers to understand.
- Some issues could fit more than one category, such as an issue with both an open PR and recurrence monitoring.
- The important information is the concrete next event, not a generalized category.

The selected model therefore uses the plain-language **What happens next** field instead.

### To review, Active, and All issues

This model kept only the two frequently used working views and placed Resolved and Ignored issues behind filters in All issues.

Why it was not selected:

- Resolved and Ignored are meaningful outcomes, not merely historical filters.
- Dedicated views make it easier to confirm what was fixed or deliberately dismissed.
- The four-view navigation remains small enough to scan without requiring an All issues destination.

### Snoozing deferred issues

This model removed a deferred issue from the working views until its date or recurrence condition was met.

Why it was not selected:

- It made previously reviewed issues difficult to find before their condition fired.
- It did not provide a visible home for issues that still mattered but did not need immediate attention.
- Active preserves visibility while the reminder or monitoring rule controls when the issue returns to **To review**.

### Inferring status from artifact creation

This model changed status automatically when the developer added an evaluator, offline examples, an experiment, or a PR.

Why it was not selected:

- The same artifact can serve different intentions.
- An evaluator might validate a fix or improve future recurrence detection.
- Automatic transitions would make status behavior difficult to predict.

The selected model changes lifecycle state from an intentional triage decision or outcome. Artifacts provide context but do not independently determine status.

