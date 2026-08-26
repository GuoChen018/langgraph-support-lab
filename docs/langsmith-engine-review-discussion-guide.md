# LangSmith Engine Review Discussion Guide

## 1. How I grounded myself — 2 minutes

- Built **LangSupport** using LangChain to understand traces, tools, errors, evaluation, and agent behavior firsthand.
- Reviewed the current Engine experience and supporting product material.

**Takeaway:** My decisions came from understanding the underlying workflow, not only redesigning the surface.

## 2. Part 1: Desired triage flow — 5 minutes

Use the [FigJam](https://www.figma.com/board/f90C2ic8MSCaKQHth2pTwR/LangChain-Take-Home?node-id=74-11070) to explain the three core decisions:

1. **Is this a real problem?**
2. **Is it worth addressing?**
3. **Should I act now, watch it, or ignore it?**

Briefly highlight the main gaps:

- Impact and consequences are unclear.
- Linked traces do not pinpoint the relevant failure.
- Watching and ignoring lack structured outcomes.
- Fixing and validation span several disconnected surfaces.

Do not walk through every branch.

**Takeaway:** Engine should support a complete triage lifecycle—not merely surface issues.

## 3. Part 2: Design explorations — 5 minutes

Show only two or three meaningful explorations. For each, explain:

- What question was I testing?
- What worked?
- What tradeoff caused me to change direction?

Example:

> I explored separating evidence and actions more aggressively. It improved focus, but made it harder to understand the fix in the context of the failure.

**Takeaway:** The final direction resulted from explicit tradeoffs rather than visual preference.

## 4. Final design rationale — 8 minutes

Walk through one representative issue:

- **What Happened:** Understand the diagnosis.
- **Impact:** Determine reach and severity.
- **Evidence:** Validate the diagnosis at the exact failing run.
- **Next Steps:** Fix, monitor, add coverage, and validate.

Connect each section back to a FigJam friction point.

**Takeaway:** The interface follows the user’s decision sequence.

## 5. Prototype walkthrough — 8 minutes

Demonstrate only interactions that strengthen the concept:

- Switching issues and impact metrics.
- Inspecting representative evidence.
- Reviewing different customer setups.
- Moving from a proposed fix into evaluator, examples, and experiment workflows.

**Takeaway:** The proposal works as a connected workflow, not just static screens.

## 6. Discussion

Ask for feedback on the unresolved decisions:

- Is the proposed triage model correct?
- What should “impact” mean given Engine’s sampling and scan schedule?
- Is the evidence sufficient to trust the diagnosis?
- Are the next actions realistic and appropriately prioritized?
- What should be simplified or removed?

## Facilitation note

Keep LangSupport and the explorations concise so most of the discussion remains focused on the final product decisions.
