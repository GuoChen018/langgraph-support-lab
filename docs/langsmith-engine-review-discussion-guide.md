# LangSmith Engine Review Discussion Guide

## Core story

**Thesis:** Finding an issue is not enough. Before an AI engineer acts, they need to understand what happened, judge whether it matters, verify the diagnosis against real evidence, and carry the fix through validation.

The presentation should feel like one connected argument—not a tour of every artifact produced.

## Suggested 20-minute structure

1. Grounding and process — 2 minutes
2. Desired triage flow — 3 minutes
3. Scope decision and explorations — 3 minutes
4. Authentication issue walkthrough — 9 minutes
5. Tradeoffs and next steps — 3 minutes

If time runs short, compress the process and explorations. Preserve the scenario walkthrough and tradeoffs.

---

## 1. Grounding and process — 2 minutes

### What to say

> I wanted to understand the agent-engineering workflow from the inside rather than redesigning Engine as an isolated surface. I built ChainSupport, connected it to LangSmith, and used it to work with traces, datasets, evaluators, and experiments.

> I focused first on getting retrieval working so the agent could answer from current LangChain sources. I also explored an educational question path—for example, letting someone ask what an experiment is—because learning the product vocabulary was part of learning the workflow.

> That gave me a much more concrete view of what an AI engineer sees when something fails, what evidence is available, and how a production issue can become an evaluator, dataset example, and experiment.

### What to show

- Show ChainSupport only briefly.
- Use one trace or workflow view to establish that it is a functioning agent connected to LangSmith.
- Avoid a technical architecture walkthrough unless the engineer asks for one.

### Point to land

The design decisions came from using the underlying workflow, not only reviewing the existing interface.

---

## 2. From the current flow to the desired triage flow — 3 minutes

### Transition

> Once I understood the tools, I mapped the current triage flow to get the lay of the land. I will not walk through every branch, because the more important artifact is the desired flow that came out of it.

### Desired triage flow

Frame triage as four decisions:

1. **Is this diagnosis credible?**
   - What happened?
   - What evidence supports it?
2. **How important is it?**
   - How often has it appeared?
   - What consequence did it produce?
3. **What should I do with it now?**
   - Fix it.
   - Defer or watch it.
   - Ignore it with intent.
4. **How do I know the fix worked?**
   - Change the implementation.
   - Track the behavior.
   - Add regression examples.
   - Run an experiment.

Status updates—such as Watching, In Progress, Resolved, or Ignored—support this flow, but they are not the flow itself.

### Key friction points

- The diagnosis may be plausible without being easy to verify.
- Impact values do not always explain scope or consequence.
- Relevant failure evidence can be buried inside a full trace.
- Fixing, monitoring, adding examples, and testing span disconnected surfaces.
- A user can change status without necessarily knowing what will happen if the issue resurfaces.

### Point to land

Engine should help users move from **detection → trust → prioritization → remediation → validation**.

---

## 3. Scope decision and explorations — 3 minutes

Do not present every visual variation. Show three explorations that changed the product direction.

### Exploration 1: Issue lifecycle and status banner

**Question tested:** Could clearer lifecycle messaging make Open, Watching, Resolved, and resurfacing behavior understandable?

**What worked:** A banner could explain what Engine will do after a user changes status, especially whether a closed issue can reopen.

**Why it was not the final focus:** The intervention was useful but narrow. Better status messaging does not matter if users still cannot trust the underlying diagnosis.

**How to frame the decision:**

> I did not discard lifecycle as unimportant. I deprioritized it because evidence quality is upstream of every lifecycle action.

### Exploration 2: Evidence presentation

**Question tested:** How much of the trace should Engine explain versus leave for the engineer to inspect?

**What worked:** Representative traces, highlighted problem spans, and issue-specific summaries made the diagnosis much faster to verify.

**Tradeoff:** More explanation reduces hunting, but too much generated interpretation can create another claim the user has to verify.

**Final direction:** Pair a concise diagnosis with direct, inspectable telemetry. The explanation tells the user where to look; the trace remains the source of truth.

### Exploration 3: Impact and comparison context

**Question tested:** Can the interface communicate severity without inventing a universal baseline?

**What worked:** Combining frequency with an issue-specific consequence is more useful than showing a trace count alone.

**Tradeoff:** Comparisons such as “normal latency” or “expected cost” sound precise but are misleading unless the comparison cohort is defined.

**Final direction:** Lead with observed values. Keep baseline comparison optional, and only use comparable unaffected traces when the cohort is defensible.

### Why the final scope became the evidence path

> I focused on the evidence path because it has the highest leverage. If AI developers do not trust that an issue is real, they will not prioritize it, change its status, accept a proposed fix, or create durable evaluation coverage from it.

### Revised HMW

**How might we help AI engineers quickly understand, verify, and act on an Engine issue without making them reconstruct the failure across disconnected LangSmith surfaces?**

---

## 4. Final design walkthrough — 9 minutes

Keep the walkthrough in character as an AI engineer. Do not introduce every feature before the scenario needs it.

### Setup: the notification

> Imagine I am an AI engineer responsible for a support agent. I get a notification that Engine found a recurring authentication issue across several account tools.

> The important signal is not simply that a `401` or `403` occurred. The workflow did not recover or disclose the failure, and some final responses told users their account change succeeded when it had not.

Open the authentication issue in the prototype.

### Step 1: What Happened

**User question:** “What is Engine claiming went wrong?”

Walk through:

- 84 of 700 observed account-tool calls returned `401` or `403`.
- The workflow skipped the required recovery or failure path.
- 11 final responses falsely implied success.

**Design rationale:**

- Lead with a plain-language causal diagnosis.
- Include the mechanism and consequence, not merely the error category.
- Use precise units so “12%” is not mistaken for 12% of all production traffic.

**What to say:**

> This section gives me a falsifiable claim. I know which calls failed, what the workflow did afterward, and why that behavior matters to users.

### Step 2: Impact

**User question:** “Is this worth addressing now?”

Walk through:

- **Affected Traces:** How much evidence is linked to the issue.
- **Unique Threads:** Whether the problem is concentrated in retries or spread across conversations.
- **Failed Calls:** Frequency of the underlying mechanism.
- **False Success Responses:** The confirmed user-facing consequence.
- Select a metric to show its trend across Engine observations.

**Design rationale:**

- Put the value first.
- Combine scope, frequency, and consequence.
- Adapt the last two metrics to the issue type rather than forcing every issue into generic cards.
- Keep metric definitions and baseline comparisons optional.

**Important caveat if asked:**

Engine issues accumulate matching evidence over time. These values describe the evidence attached to the issue; they should not silently imply exhaustive analysis of all production traces. Any percentage needs an explicit eligible denominator.

**What to say:**

> The 63 traces tell me the issue is recurring. The 51 threads tell me it is not just one noisy conversation. The 11 false success responses tell me the problem has crossed from an internal failure into user harm.

### Step 3: Evidence

**User question:** “Do I trust this diagnosis enough to change production code?”

Open a representative trace and point to:

1. The account tool returns an authentication failure.
2. The refresh callback is not invoked.
3. Routing continues instead of failing closed.
4. The final response reports success.

Switch between the representative traces to show that the pattern recurs across different account tools.

**Design rationale:**

- Start with representative traces instead of an undifferentiated evidence list.
- Highlight the exact span that supports the issue.
- Keep the surrounding trajectory visible so the engineer can challenge the interpretation.
- Preserve direct access to the full trace.

**What to say:**

> I do not have to trust a generated summary blindly. I can inspect the exact run, see the failed tool result, and follow the downstream behavior that produced the false success response.

### Step 4: Review the proposed fix

**User question:** “What change would address the mechanism I just verified?”

Open **Review Proposed Fix** and show:

- Credential refresh on the recoverable authentication case.
- One bounded retry.
- An explicit failure when recovery does not succeed.
- No success claim unless the operation actually completes.

Click **Open PR** and let the action move through loading to **View PR**.

**Design rationale:**

- Keep the proposed fix near the evidence that justifies it.
- Do not put the primary CTA at the top before the user has understood impact or verified the diagnosis.
- Adapt the action to the customer setup: PR, direct changes, or Context Hub where applicable.

### Step 5: Create an evaluator

**User question:** “How do I detect this behavior if it appears again?”

Open **Track This Behavior**, review the proposed rule, and click **Create Evaluator**.

Explain that the evaluator should detect the behavioral failure—not merely the presence of a `401`:

- The operation failed.
- The final answer claimed or implied success.
- The evaluator definition and version must be stored.

Let the action resolve to **View Evaluator**.

### Step 6: Add examples

**User question:** “What cases should become durable regression coverage?”

Open **Add Examples** and show the three production-derived cases:

- Expired token during a billing-address update.
- Invalid token during an email change.
- Insufficient scope during a payment-method change.

Explain that the user reviews and edits examples before adding them to a dataset. Production evidence is a starting point, not automatically accepted ground truth.

Click **Add 3 Examples** and let it resolve to **View Examples**.

### Step 7: Run an experiment

**User question:** “Did the candidate fix improve the behavior without introducing regressions?”

Open **Test Changes** and show:

- Candidate version.
- Dataset.
- Relevant evaluators.
- Estimated run scope and cost.
- Optional baseline where a defensible comparator exists.

Click **Run Experiment** and let it resolve to **View Experiment**.

**What to say:**

> The workflow ends with evidence that the change worked. The issue becomes a reusable evaluator and dataset coverage, not just a one-time patch.

### Final walkthrough takeaway

The page follows the engineer’s actual decision sequence:

**Understand → assess → verify → fix → monitor → add coverage → validate**

---

## 5. Tradeoffs and likely questions — 3 minutes

### Why is the main CTA not at the top?

Putting **Open PR** at the top would optimize for action before trust. A proposed fix is useful only after the user understands the consequence and verifies that the evidence supports the diagnosis. The Next Steps section keeps action contextual to the reasoning that precedes it.

The tradeoff is discoverability. A future version could add a lightweight sticky action summary after the user reviews the evidence, rather than presenting an immediate top-level fix.

### Why focus on one detailed scenario?

The authentication scenario exercises the complete system:

- A structured tool failure.
- A missed recovery path.
- A semantic false success response.
- A code change.
- An evaluator.
- Regression examples.
- An experiment.

The tradeoff is breadth. Other issue types—hallucination, looping, latency, wrong-tool selection, and guardrail bypass—still need validation, but one coherent scenario exposes workflow problems more clearly than many shallow screens.

### Can these metrics be computed at production scale?

Some metrics come directly from telemetry:

- Trace and thread identity.
- Tool status and errors.
- Duration, token use, and recorded cost.

Other metrics require a versioned semantic evaluator:

- False success responses.
- Unsupported claims.
- Wrong-tool intent.
- Restricted disclosures.

The scalable model is to classify each newly linked trace once, store the structured label and evaluator version, then aggregate those labels. It should not require an LLM to rescan the entire issue whenever the page loads.

### Why not always compare against “normal” traces?

There is no universal normal trace. Intent, route, model, prompt version, tool, context size, and environment all affect cost, latency, and quality.

Where comparison is useful, the baseline should use comparable unaffected traces from the same period and disclose the cohort definition. If that cohort is not defensible, the UI should show the observed value without inventing a comparison.

### Does Watching still make sense if closed issues reopen?

Watching is understandable as an active posture: “keep this visible while I gather more evidence.” Closing or resolving is a lifecycle outcome: “I believe this is no longer active.”

The unresolved product question is whether users understand that Engine can reopen a resolved issue when it resurfaces. That behavior needs explicit messaging regardless of whether Watching remains.

### How much should users trust an AI-generated diagnosis?

The diagnosis should be treated as a hypothesis backed by inspectable evidence—not an unquestionable conclusion. Confidence comes from:

- A precise claim.
- Representative examples.
- Direct trace evidence.
- Detector or evaluator versioning.
- The ability to inspect exceptions and false positives.

### Why keep actions together on the issue page?

The actions form one remediation loop and share the same evidence context. Keeping them together reduces the translation work of rebuilding the issue in separate products.

The tradeoff is page density and the risk of duplicating full-featured evaluator, dataset, or experiment builders. The issue page should initiate and preconfigure those workflows, then link to the canonical surface for deeper editing.

---

## 6. What I would do with more time

This answer is about strengthening the current proposal:

1. Test the workflow with AI engineers using real issues and ask them to identify false positives.
2. Validate the design across hallucination, latency, looping, wrong-tool, and security scenarios.
3. Define the data contract for every metric, including numerator, denominator, window, evaluator version, and coverage.
4. Explore lifecycle messaging for Watching, Resolved, Ignored, and automatic resurfacing.
5. Test whether representative traces are sufficient or whether users need clustering, counterexamples, or confidence indicators.
6. Refine responsive behavior and accessibility with the production design system.

Suggested answer:

> With more time, I would spend less of it adding surface area and more of it validating trust. I would test whether engineers can correctly explain the issue, find the supporting span, identify a false positive, and predict what each action will do.

---

## 7. What I would do next

This answer is about sequencing the immediate product work:

1. Validate the evidence-first workflow with five to eight AI engineers.
2. Partner with engineering to inventory which proposed metrics are directly observable and which require semantic evaluation.
3. Implement one end-to-end issue type—authentication failure—with real trace labels, evaluator creation, dataset review, and experiment handoff.
4. Measure whether the design reduces time to verify, time to remediation, and repeated navigation across LangSmith.
5. Use those findings to decide whether to expand the model to more issue types or first solve lifecycle and resurfacing.

Suggested answer:

> My next step would be to prove this workflow with one real issue type rather than immediately generalizing the UI. If users can move from a new authentication issue to a trusted fix and regression coverage faster, then I would expand the metric and action model to other issue categories.

---

## 8. Questions to ask the reviewers

Aim for targeted critique:

- **For design:** Does the page reveal enough evidence to earn trust before asking the user to act, or does it still over-explain?
- **For engineering:** Which parts of the proposed issue payload could Engine produce reliably today, and which would require new evaluator or indexing infrastructure?
- **For both:** Is initiating the full remediation loop from the issue page the right boundary, or should some actions remain links into existing LangSmith surfaces?

---

## Delivery notes

- Lead with the thesis, not the list of artifacts.
- Say what question each section answers before describing its UI.
- Use the authentication scenario as the spine of the presentation.
- Distinguish observed telemetry from semantic evaluation.
- Call out unresolved questions directly; do not present prototype assumptions as current Engine behavior.
- Stop after the final experiment state. Do not continue clicking through every issue or control.
