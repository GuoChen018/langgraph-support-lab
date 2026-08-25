# LangSmith Engine Take-Home

## Part 1: Desired triage flow

### Summary

The journey begins when Engine surfaces an issue and ends in one of three outcomes: fix it now, watch it under a defined condition, or ignore it with a recorded reason.

Before branching, the developer needs to answer three questions:

1. **Is this a real problem?** Do the linked traces demonstrate the behavior Engine describes?
2. **Is it worth addressing?** How widespread and consequential is it?
3. **Should I act now or later?** Is the right outcome Fix, Watch, or Ignore?

The flow follows each path through its intermediate states and completion criteria:

- **Fix** includes reviewing the proposed change, determining what evaluation coverage already exists, optionally adding an evaluator or offline examples, choosing an appropriate validation method, handling failed tests, and resolving the issue after the change is accepted.
- **Watch** records a recurrence condition. When that condition is met, the issue returns with new evidence and an explanation of what changed.
- **Ignore** records why the issue is leaving active triage, distinguishing an incorrect detection from a real issue that the team has consciously chosen not to address.

The flow also accounts for interrupted work and recurrence. A developer returning mid-fix should see what has been completed, changed, or invalidated. If the same pattern returns after resolution, the existing issue should return with its previous fix, validation history, affected version, and new evidence.

### Highest-friction moments


| Priority | Friction moment                | Description                                                                                                                                                  |
| -------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1        | Judging importance             | The current page does not clearly summarize the issue’s impact, affected population, or user-visible consequence.                                           |
| 2        | Verifying the issue in a trace | Linked traces open the full execution but do not direct the developer to the exact run or field that demonstrates the problem.                               |
| 3        | Testing a proposed change      | Engine can propose a fix, evaluator, and offline examples, but there is no guided experience for setting up, running, and interpreting tests before merging. |
| 4        | Following the issue lifecycle  | Work can span Engine, evaluation surfaces, and GitHub, with no single place to understand what is complete, resume work, or see what happens next.           |


### Biggest design opportunity

The biggest opportunity is helping a developer judge whether an issue is important enough to investigate and act on.

The current experience shows recurrence and linked traces, but the issue’s reach and user consequence are less clear. This decision determines whether the developer continues into the trace, reviews the proposed fix, or moves on, so I chose the evidence layer for Part 2.

## Part 2: High-fidelity designs

**Chosen area:** Evidence layer

### Why I chose this area

Coming from Datadog, I was interested in the observability challenge of moving from a detected pattern to a clear picture of its impact and supporting evidence. Designing this area also required understanding how traces, spans, evaluators, offline examples, and experiments support different parts of remediation.

The authentication scenario made the challenge concrete: Engine identified failures across several account tools, but the interface needs to prove that the tools failed, recovery did not happen, and users received misleading success responses.

### Layout and hierarchy decisions

The page follows the order of the developer’s assessment:

1. **What Happened** summarizes the detected pattern and its consequence.
2. **Impact** shows affected traces, threads, failed tool calls, misleading responses, and frequency over time.
3. **Evidence** places Linked Traces beside message and trace details, directing attention to the failed tool call and misleading response.
4. **Next Steps** consolidates Review Proposed Fix, Track This Behavior, and Add Regression Examples after the evidence.

The structure remains consistent while the evidence adapts to the issue type. Authentication emphasizes tool failures, recovery, and the final response; other issues may emphasize claims and sources, repeated trajectories, latency, or cost.

### Key tradeoffs

- **Evidence before action:** Moving the CTAs from the top-right to the bottom makes them less immediate, but encourages review first and keeps related actions together.
- **Data over confidence labels:** The design avoids arbitrary labels such as “high confidence” and instead shows the counts, denominators, affected workflows, and exact trace evidence behind the issue.
- **Validation depth versus cost:** Experiments rerun the agent and incur model and evaluator costs. The design shows an estimated cost, recommends a candidate experiment, and makes the more expensive production-baseline comparison optional.

### What I would tackle next

With more time, I would:

- Stress-test the design with hallucination, retrieval, looping, latency, cost, state-loss, and long-running-agent issues.
- Build an interactive prototype covering metric selection, trace switching, highlighted evidence, and candidate-versus-baseline experiments.
- Test the flow with AI engineers to learn what they inspect first, where trust breaks down, and how quickly they can reach a defensible triage decision.
- Design missing-data states for sampled traces, unavailable user identity, incomplete instrumentation, and uncertain denominators.

