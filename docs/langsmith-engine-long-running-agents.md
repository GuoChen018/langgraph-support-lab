# LangSmith Engine and Long-Running Stateful Agents

## Why these agents are harder to evaluate

A simple LLM application usually follows a short cycle:

```text
Input → LLM call → Text response
```

Testing it often means running a collection of inputs through the application and grading its responses.

A long-running, stateful agent is different. It may:

- Run for 15–30 minutes or longer
- Make many model and tool calls
- Modify files or databases
- Interact with external services
- Pause and resume
- Maintain state across multiple turns
- Produce artifacts instead of a text response
- Reach the correct outcome through several valid paths

The final message alone may not reveal whether the agent succeeded. Evaluation must often consider its trajectory, artifacts, and final environment state.

## How Engine observes a long-running agent

Engine works from production traces and feedback.

A single long-running operation can produce a large trace:

```text
Trace: Complete coding task
└── Root run: coding_agent
    ├── Child run: inspect_repository
    ├── Child run: edit_authentication_code
    ├── Child run: run_tests
    ├── Child run: fix_test_failure
    └── Child run: produce_summary
```

If the work continues across several turns, LangSmith can group the traces into a thread:

```text
Thread: One stateful agent session
├── Trace 1: User provides the task
├── Trace 2: User answers a clarification
└── Trace 3: Agent resumes and completes the task
```

Engine scans this production activity and uses signals such as:

- Errors and timeouts
- Repeated or unnecessary tool calls
- Unexpectedly long trajectories
- Online evaluator failures
- Human feedback from annotation queues
- User feedback

Engine can then cluster related failures into a named issue.

For example:

> Coding agent repeatedly edits the same file but terminates without running the test suite.

## What an evaluator can measure

For a simple application, an evaluator might only grade the final answer.

For a long-running agent, evaluators can measure several layers.

### Final response

Did the agent clearly and accurately report what it accomplished?

### Trajectory

Did the agent take a reasonable sequence of actions?

For example:

```text
Inspect repository
→ Identify failing code
→ Edit implementation
→ Run tests
→ Report result
```

An evaluator could fail the run if the agent modified source files but never ran tests.

Trajectory evaluation should not always require one exact sequence. Multiple paths may be valid. Depending on the task, the evaluator can check:

- Required steps occurred
- Forbidden actions did not occur
- Tool usage stayed within reasonable limits
- The trajectory eventually made progress
- The agent did not repeat nearly identical actions

### Artifacts

Did the agent create or modify the expected files, reports, code, or other deliverables?

### Final environment state

Did the resulting system actually satisfy the task?

For a coding agent, this could mean:

- Required tests pass
- Unrelated tests still pass
- The repository contains the intended behavior
- No credentials or unwanted files were added

### Thread-level outcome

For a multi-turn agent, did the complete session achieve the user's goal?

A thread-level online evaluator can grade the completed conversation rather than scoring every turn independently.

## How Engine closes the production feedback loop

Engine can use the long-running agent's production traces in the same general lifecycle:

```text
Production execution
        ↓
Trace or thread captures the behavior
        ↓
Engine detects a recurring failure pattern
        ↓
Engine creates a named issue
        ↓
Engine proposes a fix and targeted evaluator
        ↓
Engine proposes offline dataset examples
        ↓
Future evaluator failures can resurface the issue
```

For example, Engine might propose an evaluator with this rule:

```text
Fail when:
- The agent modifies source files.
- The agent finishes without running the relevant tests.
```

That evaluator can monitor future production traces for the same behavior.

## Why an offline example alone may not be enough

For a chatbot, an offline example can often be represented as:

```text
Input question
+ Expected response
```

For a long-running agent, the task may depend on an environment. A complete test case may require:

```text
Task instruction
+ Initial repository or filesystem
+ Initial database or service state
+ Mocked or isolated integrations
+ Resource and time limits
+ Success verifier
```

Consider this coding task:

```text
Task:
"Fix the failing authentication test."

Starting environment:
- Repository checked out at commit abc123
- auth_test.py currently fails

Success criteria:
- Authentication tests pass
- Unrelated tests do not regress
- No secrets are committed
```

The instruction alone cannot reproduce the test. The agent also needs the same starting repository and a verifier that checks its work.

## The role of sandboxes and evaluation runners

Each long-running test should normally execute in a fresh, isolated environment.

Isolation prevents:

- One test changing the starting state of another
- Files leaking between trials
- Agents affecting production systems
- Flaky results caused by leftover state

A runner such as Harbor can coordinate these trials, while a sandbox provides the isolated environment.

The evaluation flow becomes:

```text
Dataset task
     +
Environment specification
     ↓
Runner creates a fresh sandbox
     ↓
Agent executes the long-running task
     ↓
Verifier checks artifacts and final state
     ↓
LangSmith records traces, scores, and costs
     ↓
Results appear as an experiment
```

Because agents are nondeterministic, important tasks may need multiple trials. The experiment can aggregate success rate, cost, duration, and evaluator scores across those attempts.

## What Engine does and does not do

Engine helps with:

- Finding recurring production failures
- Grouping related traces into issues
- Diagnosing likely causes using traces and connected code
- Proposing targeted evaluators
- Turning production failures into candidate dataset examples
- Proposing code or prompt fixes

Engine should not be assumed to automatically reconstruct every external environment used by a production agent.

For environment-dependent tasks, engineers may still need to:

- Package the initial files and system state
- Mock or replay external APIs
- Configure an isolated sandbox
- Define a deterministic verifier
- Decide when a long-running thread is complete

The offline example proposed by Engine is therefore often the starting point for a long-running agent test, not the entire executable test environment.

## Practical testing strategy

Use multiple layers rather than relying only on expensive end-to-end trials.

### Fast component tests

Test individual decisions such as tool selection, routing, or state updates.

### Trajectory tests

Verify that required steps occur and pathological loops do not.

### End-to-end sandbox tests

Run the complete agent in a realistic isolated environment and inspect the final state.

### Production monitoring

Use run-level or thread-level online evaluators to detect failures that only appear in real usage.

Together, these layers provide faster development feedback while preserving realistic coverage:

```text
Component tests
      ↓
Trajectory tests
      ↓
End-to-end sandbox experiments
      ↓
Production online evaluators
      ↓
Engine issues and regression coverage
```

## Further reading

- [LangSmith Engine](https://docs.langchain.com/langsmith/engine)
- [Evaluate complex agents](https://docs.langchain.com/langsmith/evaluate-complex-agent)
- [Agent trajectory evaluations](https://docs.langchain.com/langsmith/trajectory-evals)
- [Multi-turn online evaluators](https://docs.langchain.com/langsmith/online-evaluations-multi-turn)
- [Harbor integrations](https://docs.langchain.com/langsmith/harbor-integrations)
