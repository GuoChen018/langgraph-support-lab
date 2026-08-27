# LangSmith Engine Impact Metrics — Prototype Revision

## Goal

Revise the prototype so its Impact section uses metrics that:

- Can be computed when an Engine issue is ready to view.
- Describe exactly what Engine observed without implying exhaustive production coverage.
- Help an AI engineer judge scope, severity, and likely remediation value.
- Do not require user configuration, an undefined comparison cohort, or invented precision.
- Use concise, production-ready labels.

## Current Engine constraints

Official documentation establishes that Engine:

- Tracks an issue over time.
- Adds newly matching traces to the existing issue during later scans.
- Shows contributing traces and how recently the issue was observed.
- Runs scans on a dynamic schedule.

The documentation does not establish:

- That Engine analyzes every eligible production trace.
- That the displayed evidence count represents total production incidence.
- A fixed reporting window.
- A standard control cohort or “normal” baseline.
- A published formula for excess cost, added latency, or issue severity.

Therefore, the prototype should call Engine-attached traces **linked traces**, not total affected traces.

## Production metric model

Use a stable four-part data model:

1. **Linked traces**
   - Number of traces Engine attached to the issue.
   - This is evidence coverage, not an estimate of total production incidence.

2. **Unique threads**
   - Distinct `thread_id` or `session_id` values represented by linked traces.
   - Show only when thread metadata coverage is reliable.
   - Omit the card when the value cannot be computed; do not request additional setup after the issue appears.

3. **Detected events**
   - The issue-specific behavior Engine identified.
   - Examples: failed calls, unsupported claims, repeated calls, wrong selections, or failed-open checks.

4. **Confirmed outcomes**
   - The user, business, or security consequence associated with the issue.
   - Examples: false successes, high-risk claims, completed wrong actions, or data exposures.

The backend structure can remain consistent while the two adaptive cards use issue-specific labels.

## Metrics by issue

### Authentication failure

- Linked traces
- Unique threads
- Failed calls
- False successes

`False success` means the operation failed, but the final answer claimed or strongly implied that it succeeded. This requires structured operation truth plus a versioned semantic evaluator.

### Hallucination

- Linked traces
- Unique threads
- Unsupported claims
- High-risk claims

Claims and responses must not be mixed in the same ratio. If the numerator counts claims, its denominator must also count eligible claims.

### Agent looping

- Linked traces
- Repeated calls
- Repeat-call cost
- Repeat-call time

These values include only calls classified as redundant. They do not require a hypothetical “normal” trace:

- Repeat-call cost is the recorded cost of redundant tool or model calls.
- Repeat-call time is the measured duration attributable to those redundant calls.

An optional baseline can still add context by comparing the affected traces with comparable traces that completed the same task without redundant calls. The direct metrics answer how much cost and time came from repetition; the baseline answers whether the affected traces were materially more expensive or slower than otherwise similar executions.

The loop detector must define argument equivalence, result equivalence, and allowed retry behavior.

### Latency

- Linked traces
- Unique threads
- P50 latency
- P95 latency

Do not use “slow traces” until Engine has a product-owned threshold that requires no customer configuration. P50 and P95 are observed values derived from linked traces.

### Prompt regression

- Linked traces
- Unique threads
- Failed evaluations
- Quality failures

These require prompt-version metadata and a versioned evaluator generated or owned by Engine. Avoid “changed responses”: changed behavior is not necessarily degraded behavior.

### Wrong tool

- Linked traces
- Unique threads
- Wrong selections
- Completed wrong actions

The outcome metric distinguishes incorrect selection attempts from actions that actually produced an unwanted side effect.

### Guardrail bypass

- Linked traces
- Affected accounts
- Failed-open checks
- Data exposures

For security issues, account or protected-resource scope is more useful than thread count. Any confirmed exposure may independently raise severity regardless of frequency.

## Scalable computation

Metrics should not require an LLM to rescan the complete issue every time the UI loads.

1. Engine links a new trace to an issue.
2. A deterministic rule or versioned evaluator records structured labels for that trace.
3. The label includes its detector version and confidence where applicable.
4. Metrics are calculated through normal aggregation over stored labels and telemetry.
5. Reprocessing occurs only when the detector definition changes.

Direct trace telemetry can provide:

- Trace and thread identity.
- Tool status and errors.
- Span duration and end-to-end latency.
- Token and recorded cost data.
- Prompt, model, tool, and graph versions when instrumented.

Semantic evaluators are required for:

- False-success claims.
- Unsupported or high-risk claims.
- Quality failures.
- Wrong-tool intent.
- Unauthorized outcomes.
- Restricted disclosures when deterministic policy or DLP signals are insufficient.

## Chart strategy

Chart type should follow the unit being displayed.

### Bar charts

Use for discrete events added during each scan:

- Linked traces
- Unique threads
- Failed calls
- Unsupported claims
- Repeated calls
- Wrong selections
- Failed-open checks
- Data exposures

Use actual scan timestamps. Do not imply a fixed daily or six-hour cadence.

### Line charts

Use for ordered summary statistics:

- P50 latency
- P95 latency
- Cost per linked trace

Points must correspond to real scan timestamps or explicitly defined aggregation buckets.

### Stacked bars

Use for outcome composition:

- False success versus other outcomes after a failed call.
- High-risk versus lower-risk unsupported claims.
- Wrong selections that did versus did not complete an action.
- Blocked versus failed-open guardrail decisions.

### Histograms

Use when the distribution is more meaningful than a trend:

- End-to-end latency.
- Repeat-call time.
- Per-trace cost.

## Required prototype changes

1. Replace **Affected traces** with **Linked traces**.
2. Replace **Affected threads** with **Unique threads** and support omission when thread IDs are unavailable.
3. Keep baseline comparison as an optional prototype toggle, defaulted off.
4. When the toggle is enabled, show comparisons only for metrics with a defined and available cohort; leave unsupported cards unchanged.
5. Remove synthetic previous-72-hour, unexplained “matched traces,” expected-cost, and expected-latency values.
6. Replace counterfactual cost and latency labels with directly measured repeat-call cost and repeat-call time.
7. Apply the issue-specific metric sets defined above.
8. Give every sidebar issue its own complete metric, chart, and evidence payload.
9. Remove the current behavior where only the sidebar trace count changes while other values remain attached to a shared issue template.
10. Replace synthetic rotated/rescaled chart values with explicit per-metric series.
11. Use the cadence stored by each series rather than hardcoding a six-hour interval.
12. Keep every metric label short; place definitions and methodology outside the label.

## Future baseline direction

An accumulating issue does not technically prevent baseline comparison. Accumulation and comparison are separate concerns:

- The **issue cohort** can contain linked traces observed from the issue’s first observation through the latest scan.
- A **comparison cohort** can cover the same calendar span and be selected using a declared methodology.

The problem is not that Engine issues accumulate. The problem is that Engine does not currently document a standard baseline method.

### Baselines to avoid

#### All other traces

Do not compare against every trace outside the issue. Different intents, tools, models, routes, environments, and workloads make this comparison misleading.

#### All traces without the issue

This is better than all other traces but still produces selection bias. The unaffected population may contain fundamentally easier tasks.

### Most defensible baseline

Use **comparable unaffected traces** selected from the same period:

- Same project and environment.
- Same task or intent.
- Same route or graph path.
- Same relevant tool.
- Same model, prompt, and application version.
- Similar input or context size where cost and latency are compared.
- No positive label from the issue detector.

This cohort should be called **comparable traces** in methodology. The UI should not use unexplained language such as “matched traces.”

### Better baseline by metric

- **Authentication, wrong actions, and disclosures:** The expected harmful-outcome count is zero. Compare against a product or policy expectation rather than unrelated traces.
- **Agent looping:** Use within-trace attribution for repeat-call cost and time. When comparison is enabled, compare total per-trace cost and latency with comparable traces that completed the same task without redundant calls.
- **Latency and cost:** Comparable unaffected traces can provide P50/P95 or per-trace cost context when the cohort definition is reliable.
- **Prompt regression:** Compare the same evaluation set or equivalent production cohorts across prompt versions.
- **Quality and hallucination:** Compare evaluator failure rates across equivalent task cohorts, using the same evaluator version.

### Recommendation for the current prototype

Treat baseline comparison as an optional prototype experiment rather than a claim about current Engine behavior. Keep the toggle off by default until each supported metric has a defensible comparison cohort.

When the baseline toggle is enabled:

1. Apply only to metrics with a defensible comparator.
2. Show the observed value first and one concise comparison line beneath it.
3. Leave metrics without a valid baseline unchanged instead of inventing a universal comparison.
4. State the comparison cohort in accessible methodology.
5. Use normalized per-trace values or rates rather than cumulative totals.
6. Expose coverage and evaluator confidence.
7. Never present a synthetic value as current Engine behavior.

## Acceptance criteria

- Every displayed value has a stable machine-readable definition.
- Numerator and denominator use compatible units.
- No card implies exhaustive production impact from sampled evidence.
- No metric requires customer configuration after issue creation.
- Semantic metrics identify their evaluator contract.
- Charts use real per-metric data and timestamps.
- Metric labels fit on one line at the target viewport.
- The baseline toggle affects only metrics with an explicitly defined comparator.
- Security and irreversible outcomes can raise severity independently of trace count.
