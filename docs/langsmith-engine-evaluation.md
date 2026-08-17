# Understanding LangSmith Engine: Issues, Evaluators, and Offline Examples

## The scenario used in this guide

The LangSmith Engine announcement describes a customer-support agent that can cancel subscriptions.

Some users only ask informational questions such as:

> What are my cancellation options?

The agent misunderstands those questions and tries to cancel the subscription immediately. Several production conversations show the same behavior.

Engine groups those conversations into a named issue:

> **Agent fails to handle subscription cancellation requests accurately**

This cancellation scenario comes from the LangSmith blog post. The rest of this guide uses it to explain Engine's terminology.

## The key concepts

### 1. Trace

A **trace** is a record of one execution of the agent. It can contain the user's input, the agent's response, tool calls, and intermediate steps.

One conversation in which the agent incorrectly calls the cancellation tool is one failing trace.

### 2. Issue

An **issue** is a named item in the Engine UI representing a recurring behavior found across related traces. It is not the same as an individual failure.

For example, Engine may group these traces into one issue:

- A user asks about cancellation fees, and the agent cancels the subscription.
- A user asks what cancellation would do, and the agent invokes the cancellation tool.
- A user asks which cancellation options exist, and the agent claims the subscription was cancelled.

The issue is the row an engineer reviews. The traces are its evidence.

### 3. Evaluator

An **evaluator** is an automated grader. It examines an agent run and returns feedback such as:

- Pass or fail
- A numeric score
- A reason for the result

An evaluator measures behavior; it does not fix the agent.

For this issue, an evaluator could implement the following rule:

> If the user is only requesting cancellation information, fail the run if the agent performs or claims to perform a cancellation.

For a new production trace, it might return:

```text
cancellation_intent_handling: FAIL
Reason: The user requested information, but the agent invoked cancel_subscription.
```

### 4. Experiment

An **experiment** is a recorded batch test of a particular agent version against a dataset.

Suppose the cancellation dataset contains 20 saved examples. An engineer changes the agent's cancellation tool description and starts an experiment:

1. LangSmith runs the updated agent on all 20 inputs.
2. Those executions produce 20 new runs and outputs.
3. One or more evaluators grade the outputs.
4. LangSmith stores the runs, evaluator scores, and summary metrics together as an experiment.

The experiment answers:

> How did this version of my agent perform across this dataset?

An evaluator answers a different question:

> How should one run, or a collection of runs, be graded?

Therefore, an experiment is not a grader. It is the test execution and its recorded results. Evaluators are grading functions used within that experiment.

```text
Dataset of examples
        +
Agent version
        ↓
    Experiment
        ↓
New runs and outputs
        ↓
 Evaluator scores
```

Running another agent version against the same dataset creates another experiment. Engineers can compare the experiments to determine whether the new version improved the targeted behavior or caused regressions elsewhere.

## How evaluators and issues are related

Evaluators and issues are separate LangSmith concepts:

- An evaluator grades runs or traces.
- An Engine issue groups evidence about a recurring problem.

They become directly connected when Engine creates an evaluator for a particular issue.

When the blog says that Engine proposes an evaluator “scoped to the exact problem,” it means the evaluator's grading instructions are written specifically to recognize that issue's failure pattern. It is not a general response-quality evaluator.

The relationship works like this:

1. Engine finds several related failing traces.
2. Engine creates the cancellation-handling issue.
3. Engine proposes an evaluator designed to recognize that exact behavior.
4. The engineer reviews and deploys the evaluator.
5. The evaluator grades future production traces.
6. Its failures become a signal that Engine uses when scanning for recurring problems.
7. If Engine detects the same problem again, it reopens the existing issue and adds the new evidence.

“If it fires again” means that the evaluator produces a failing result on new production behavior. It does not mean that the evaluator itself is an issue. It supplies evidence to Engine, which manages the issue.

It is also safer not to interpret the phrase as “one failed score always reopens the issue immediately.” Engine scans and clusters production signals; the evaluator failure is a high-priority signal used to recognize recurrence.

## What is an online evaluator?

An **online evaluator** grades live production traces during or after deployment.

It usually has access to the actual input, output, and trace details, but it does not have a human-written correct answer for every new production request. It therefore uses a rule, heuristic, or LLM judge to decide whether the behavior is acceptable.

The cancellation evaluator is useful online because it can continuously ask:

> Is the agent cancelling subscriptions when users only request information?

Its purpose is detection after deployment.

## What is an offline example?

An **offline example** is a saved test case in a LangSmith dataset. It normally contains:

- An input
- A reference answer or assertions describing acceptable behavior
- Optional metadata

Engine can convert a failing production trace into an example such as:

```text
Input:
"What happens if I cancel my subscription?"

Expected behavior:
- Explain the cancellation policy.
- Do not invoke the cancellation tool.
- Ask for explicit confirmation before performing cancellation.
```

During development, the engineer runs a new version of the agent against this saved input. An evaluator then checks whether the new output satisfies the expected behavior.

This distinction is important: **an offline example is test data, not a grader**. An evaluator grades the output produced from that example.

Its purpose is prevention before deployment.

## Should an engineer create an online evaluator or offline examples?

They are not alternatives. For an important production failure, the engineer will often want both.

Create offline examples when the team needs to:

- Reproduce a known failure while developing a fix.
- Verify the fix before deployment.
- Ensure later prompt, model, tool, or code changes do not break that case again.
- Define expected behavior for specific, known inputs.

Create an online evaluator when the team needs to:

- Monitor behavior on new, unpredictable production inputs.
- Detect whether the failure pattern returns after deployment.
- Measure how frequently a behavior occurs in real traffic.
- Surface new variants that were not included in the offline dataset.

A practical rule is:

> Use offline examples to test known cases before shipping. Use online evaluators to detect unknown future instances after shipping.

For a low-impact one-off failure, saving an offline example may be enough. For a severe or recurring production failure, use both: offline coverage to block the known regression and online monitoring to catch new variations.

## What does “regression evaluator” mean?

A **regression** occurs when behavior that previously worked, or was fixed, becomes broken again.

“Regression evaluator” usually describes what an evaluator is being used for; it is not necessarily a separate evaluator type.

Regression protection can happen at two stages:

1. **Before deployment:** Offline examples confirm that a new version still handles known cases correctly.
2. **After deployment:** An online evaluator detects the same failure pattern in new production traffic.

## The complete Engine loop

```text
Production traces contain a recurring failure
    ↓
Engine groups the traces into a named issue
    ↓
Engine diagnoses the cause and proposes a fix
    ↓
Failing traces become offline examples
    ↓
The team tests the fix against those examples
    ↓
A targeted online evaluator monitors future traffic
    ↓
If the pattern returns, Engine reopens the issue with new evidence
```

## Further reading

- [Introducing LangSmith Engine](https://www.langchain.com/blog/introducing-langsmith-engine)
- [LangSmith Engine workflow](https://docs.langchain.com/langsmith/engine)
- [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
