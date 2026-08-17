# Concrete LangSmith Experiment Example

Suppose a customer-support agent incorrectly cancels subscriptions when users only ask about their cancellation options.

## Test dataset

The team creates a dataset containing the behavior it wants to test:

```text
Example 1
Input: "What happens if I cancel?"
Expected: Explain the policy. Do not cancel.

Example 2
Input: "How much does cancellation cost?"
Expected: Explain the fees. Do not cancel.

Example 3
Input: "Please cancel my subscription."
Expected: Ask for confirmation, then cancel.
```

The same dataset can be used to test a prompt configuration or the complete agent.

## Experiment A: Test only the prompt configuration

The existing system prompt says:

```text
Help users manage or cancel subscriptions.
```

The engineer suspects that this wording is ambiguous. In the LangSmith Playground, they change it to:

```text
Answer questions about cancellation without performing it.
Only call cancel_subscription after the user explicitly requests
cancellation and confirms the action.
```

The engineer selects the cancellation dataset and starts the test. LangSmith creates an experiment:

```text
Experiment: clearer-cancellation-prompt

System under test:
- New prompt
- Claude Sonnet
- cancel_subscription tool definition

Results:
- Example 1: PASS
- Example 2: PASS
- Example 3: PASS
```

This experiment tests the prompt, model, and tool configuration directly from the Playground.

## Experiment B: Test the complete agent

The real agent may also contain application logic:

```python
def support_agent(message):
    intent = classify_intent(message)

    if intent == "cancellation":
        return call_cancellation_agent(message)

    return answer_question(message)
```

The classifier might incorrectly label “What happens if I cancel?” as a cancellation request. In that case, changing only the system prompt may not fix the complete application.

The engineer changes the routing logic:

```python
if intent == "cancellation_request" and user_confirmed:
    return call_cancellation_agent(message)
```

They then use their application code and the LangSmith SDK to run the complete agent against the same dataset. This creates another experiment:

```text
Experiment: confirmation-logic-fix

System under test:
- New prompt
- Intent classifier
- Confirmation logic
- Tools
- Model
- Complete agent workflow

Results:
- Example 1: PASS
- Example 2: PASS
- Example 3: PASS
```

## What is the difference?

The experiments answer different questions:

- **Prompt experiment:** Does this prompt and model configuration work?
- **Complete-agent experiment:** Does the complete application—including its prompts, code, routing, and tools—work?

Both follow the same structure:

```text
System under test
        +
     Dataset
        ↓
    Experiment
        ↓
New runs and outputs
        ↓
 Evaluator scores
```

The Playground and SDK are different ways to start the test. The experiment is the recorded execution and results.

## Where does the evaluator fit?

Both experiments can use an evaluator with this rule:

```text
Evaluator: inappropriate_cancellation

FAIL if:
- The user is only asking for information.
- The agent invokes cancel_subscription.
```

The evaluator grades each run. The experiment stores the runs, outputs, evaluator scores, and summary metrics together.

Running another system version against the same dataset creates another experiment. Engineers can compare the experiments to determine which version performs better and whether a change introduced regressions.
