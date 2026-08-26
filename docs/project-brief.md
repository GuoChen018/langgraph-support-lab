# LangGraph Support Lab: Project Brief

## Executive summary

This project has two connected purposes:

1. Learn the fundamentals of agent development, orchestration, observability,
   evaluation, deployment, and continuous improvement by building a real agent.
2. Study the LangChain and LangSmith experience as if joining the product team,
   then identify three to five evidence-backed product opportunities and
   prototype one of them.

The working product is a **LangChain Developer Support Agent**. It investigates
real developer problems using official documentation, GitHub issues, release
notes, migration guides, and information provided by the developer.

The support agent is not the final portfolio concept. It is a realistic system
that gives us agent behavior, traces, failures, evaluations, and cross-functional
workflows to study.

## Goals

### Learn agent development

Develop a practical understanding of:

- Models, messages, prompts, context, and structured outputs
- Tool calling and retrieval
- Agent loops and termination
- Shared state and orchestration
- Conditional routing and parallel execution
- Persistence, threads, checkpoints, and memory
- Human-in-the-loop clarification and exception-based escalation
- Latency, cost, reliability, and autonomy tradeoffs

### Learn agent observability and evaluation

Understand how teams:

- Inspect runs, traces, threads, tool calls, and state transitions
- Diagnose where an agent's behavior first diverged
- Distinguish operational failures from semantic-quality failures
- Turn production failures into reusable dataset examples
- Define code, human, and LLM-based evaluators
- Compare prompts, models, tools, and architectures through experiments
- Monitor quality after deployment
- Feed production findings back into development

### Understand LangChain's product ecosystem

Experience the lifecycle across:

- LangChain
- LangGraph
- Deep Agents, where appropriate
- LangSmith Studio
- Prompt and Context Hub workflows
- Observability, Chat, and Insights
- Datasets, evaluators, experiments, and annotation
- Deployment and managed runtime concepts
- LangSmith Engine
- Fleet, Gateway, and Sandboxes where they add useful comparison

### Produce product-design outcomes

By the end of the project, produce:

- A working agent
- A map of core users, jobs, and workflows
- A failure taxonomy
- A documented evaluation strategy
- Evidence from real LangSmith usage
- Three to five prioritized product opportunities
- One product prototype based on the strongest finding
- A case study framed like an internal product investigation

## What we are building

### LangChain Developer Support Agent

The agent supports two related jobs:

1. Explain LangChain, LangGraph, and LangSmith concepts, relationships, and
   workflows using current sources and practical examples.
2. Investigate a developer problem such as:

> After upgrading LangGraph, my graph restarts instead of resuming after an
> interrupt. I am using Python 3.13 and LangGraph 1.x.

It should:

1. Extract symptoms, environment details, and package versions.
2. Detect missing information and ask a clarifying question.
3. Search official documentation.
4. Search related GitHub issues and resolutions.
5. Search release notes and migration guides.
6. Compare evidence and develop a diagnosis.
7. Communicate confidence and uncertainty.
8. Cite supporting sources.
9. Return a supported answer directly when evidence is sufficient.
10. Preserve conversation state across clarification turns.

### Why this use case

This use case:

- Relies on public rather than fictional company data.
- Teaches the LangChain ecosystem while we build.
- Produces meaningful multi-step traces.
- Contains objective and subjective notions of quality.
- Has real historical resolutions that can become evaluation references.
- Naturally requires state, branching, parallelism, and human intervention.
- Exposes workflows involving engineers, product teams, and domain reviewers.

It is also more substantial than a generic documentation chatbot. The agent
must investigate, reconcile evidence, manage uncertainty, and decide when it
cannot safely answer.

## Core users and jobs

### Developer seeking support

**Job:** Help me understand and resolve an unfamiliar LangChain ecosystem
problem without searching fragmented documentation and issues myself.

Needs:

- Accurate and current guidance
- Clear diagnostic steps
- Evidence and citations
- Explicit uncertainty
- Requests for missing information
- No invented APIs or unsupported fixes

### Agent engineer

**Job:** Help me build, debug, test, and improve the support agent reliably.

Needs:

- Understand why a run failed
- Locate the causal step
- Reproduce behavior
- Compare versions
- Prevent regressions
- Balance quality, cost, and latency

### Product manager or designer

**Job:** Help me understand real agent behavior and define what acceptable
behavior looks like without requiring deep implementation knowledge.

Needs:

- Product-level failure patterns
- Understandable traces
- Behavioral criteria
- Production insights
- Ways to prioritize improvements

### Domain expert or reviewer

**Job:** Let me apply my expertise efficiently and turn my judgment into
repeatable improvements.

Needs:

- Sufficient context
- Clear review criteria
- Focused annotation workflows
- Evidence that feedback affects future behavior

### Platform or infrastructure engineer

**Job:** Provide a safe and standardized way to deploy, govern, and operate
agents in production.

Needs:

- Durable execution
- Scaling and reliability
- Versioning and rollback
- Access and model governance
- Cost and operational monitoring

## Current LangGraph architecture

The initial workflow is:

```text
Receive issue
    |
Inspect symptoms and versions
    |
Is required information missing?
    | yes                         | no
Ask for clarification             |
Return a chat message              |
User replies in the same thread    |
    +-----------------------------+
                  |
        Search three sources in parallel
          | documentation
          | GitHub issues
          | release notes
                  |
           Synthesize diagnosis
                  |
             Final response
```

This intentionally mixes deterministic workflow steps with model-driven
reasoning. LangGraph is useful here because the workflow requires:

- Typed shared state
- Explicit nodes and transitions
- Conditional branching
- Parallel work
- Chat-native messages
- Multi-turn user clarification
- Persistent thread state
- Step-level observability

LangChain components can be used inside individual nodes. Deep Agents may later
be tested as an alternative investigation implementation, but it is not required
for the first version.

## Data and tools

### Current starter state

The repository currently uses a small local knowledge corpus and transparent
keyword search. This lets the graph, chat UI, tests, and CLI run without an
external retrieval dependency.

This is scaffolding, not the intended final retrieval system.

### Intended public sources

- Official LangChain documentation
- Official LangGraph documentation
- Official Deep Agents documentation
- LangSmith documentation
- LangChain and LangGraph GitHub issues
- LangChain Forum discussions and accepted answers
- Release notes and migration guides
- Package metadata and compatibility information

### Evaluation source

Resolved GitHub issues and solved forum discussions can provide realistic examples:

- **Input:** Original issue or forum problem description
- **Reference:** Maintainer response, accepted answer, fix, or documented resolution
- **Agent output:** Diagnosis, evidence, and recommended next step

Details can be selectively removed to test whether the agent asks appropriate
clarifying questions rather than guessing.

Forum content is a secondary source rather than automatic ground truth. Community
answers may be outdated, incomplete, or incorrect. The agent should expose each
source's author, date, accepted-answer status, and provenance, and should prefer
official documentation or maintainer-confirmed resolutions when sources conflict.

## Evaluation strategy

Evaluate both final responses and execution trajectories.

### Response quality

- Correct diagnosis
- Relevant recommendation
- Complete answer
- Citation correctness
- Evidence coverage
- Appropriate uncertainty
- Clear and useful communication

### Agent behavior

- Requested necessary information
- Selected relevant tools
- Avoided unnecessary searches
- Reconciled conflicting evidence
- Did not fabricate APIs or facts
- Escalated when evidence was insufficient
- Avoided unnecessary human review

### Operational quality

- Latency
- Token usage
- Model cost
- Tool errors
- Repeated or looping steps

### What a dataset example contains

A dataset is a reusable test suite, not only a list of perfect answers. Each
example starts with an input, such as a developer question. It may also include
a corrected reference answer, required facts, scoring criteria, and metadata.

When a production trace fails, the failed question is valuable because it
reveals an edge case the agent must handle. The agent's bad response is retained
as diagnostic evidence, not copied into the reference output. A reviewer adds
the corrected answer or expected behavior, and that corrected example becomes a
regression test for future agent versions.

### Initial failure taxonomy

- Incorrect diagnosis
- Plausible but unsupported claim
- Outdated recommendation
- Missed relevant evidence
- Wrong tool or source
- Failure to clarify
- Excessive searching
- Premature conclusion
- Incorrect confidence
- Unsafe or unapproved action
- Poor human handoff

## LangSmith lifecycle to study

The central workflow is:

```text
Build -> trace -> understand -> evaluate -> deploy -> monitor -> improve
  ^                                                              |
  +--------------------------------------------------------------+
```

We will examine:

1. How easily a new builder understands the product and terminology.
2. How Studio supports local development and state debugging.
3. Whether traces help users identify causes rather than merely inspect steps.
4. How production behavior becomes datasets and evaluation criteria.
5. How human reviewers and non-engineering roles participate.
6. How experiments communicate quality, latency, and cost tradeoffs.
7. How deployment connects to the rest of the development lifecycle.
8. How much users should trust automated analysis and fixes from Chat, Insights,
   and Engine.
9. Where context is lost when moving among products and roles.
10. How code-first and no-code workflows relate across LangGraph and Fleet.

## Product-research method

Product opportunities must come from observed evidence, not assumptions.

For every friction point, record:

- User and job
- Lifecycle stage
- Intended outcome
- Expected behavior
- Observed behavior
- Screenshot, trace, or concrete example
- Current workaround
- Frequency and severity
- Likely underlying cause
- Product opportunity
- Constraints and tradeoffs

Distinguish among:

- **Learning friction:** The user lacks domain knowledge.
- **Usability problem:** The product makes a known task unnecessarily difficult.
- **Capability gap:** The product cannot adequately support the task.

### Forum research stream

The LangChain Forum serves two different purposes in this project:

1. **Agent knowledge:** Help the support agent find similar problems, workarounds,
   accepted answers, and maintainer guidance.
2. **Product discovery:** Reveal recurring user goals, confusing concepts,
   broken workflows, feature requests, and unsupported workarounds.

The forum runs on Discourse and exposes public JSON endpoints such as
`/search.json`, `/latest.json`, category feeds, and individual topic JSON. We can
use these endpoints instead of brittle HTML scraping, while caching responses and
respecting rate limits.

Prioritize discussions from:

- OSS Product Help
- LangSmith Product Help
- Observability & Evals
- Deployment and Studio
- Fleet
- Topics tagged `product-feedback`

For each relevant topic, capture:

- Title, URL, category, tags, and date
- Original user goal and problem
- Product area and lifecycle stage
- Replies, views, and whether an answer was accepted
- Staff or maintainer participation
- Reported workaround
- Resolution status
- Similar topics

Do not interpret raw topic frequency or views as product priority. Stronger
signals include repeated recent reports, multiple distinct users, costly
workarounds, maintainer confirmation, unresolved threads, and problems that
block a core lifecycle transition.

Potential research hypotheses include:

- Users struggle to understand the boundaries among LangChain, LangGraph, Deep
  Agents, and LangSmith.
- Complex traces expose detail without making causality clear.
- Moving from a production failure to regression coverage requires too much
  translation.
- Subjective behavior is difficult to turn into trustworthy evaluation criteria.
- Collaboration between engineers and domain experts loses important context.
- The growing number of LangSmith surfaces creates lifecycle discontinuities.

These are hypotheses to test, not predetermined conclusions.

## Opportunity format

Each final opportunity should include:

1. **Observation:** What happened?
2. **Evidence:** How often and in which examples?
3. **Affected user:** Whose job is impaired?
4. **Underlying problem:** Why does it matter?
5. **Opportunity:** What outcome could LangChain improve?
6. **Concept direction:** One plausible intervention, not a premature redesign.
7. **Success signal:** How would we know it helped?
8. **Tradeoffs:** What might be lost or made more complex?

The final prototype should address one narrow, validated problem rather than
attempting to redesign all of LangSmith.

## Non-goals

- Building a production-complete support organization
- Creating fictional customer accounts or private incident databases
- Rebuilding LangSmith or Lapdog from scratch
- Using every LangChain product solely to check a box
- Treating framework adoption statistics as proof of user value
- Preselecting a redesign before collecting evidence
- Shipping real support responses or modifying GitHub issues automatically

## Success criteria

The project succeeds if:

- The agent completes realistic investigations with visible state and evidence.
- We can explain why LangGraph is useful for this workflow.
- At least one failure moves through the complete trace-to-evaluation loop.
- Multiple agent versions are compared using repeatable criteria.
- Findings reflect the needs of more than just the implementing engineer.
- Three to five product opportunities are supported by concrete evidence.
- One opportunity is translated into a clear, testable product prototype.
- The final case study communicates both technical understanding and product
  judgment.

## Current status

Completed:

- Python project and Git repository created
- Current LangChain, LangGraph, and LangSmith packages installed
- Initial StateGraph implemented
- Conditional clarification implemented
- Chat-native message state and persistent threads implemented
- Parallel local source searches implemented
- Direct responses for sufficiently specified issues implemented
- CLI implemented
- LangGraph Studio configuration added
- Anthropic model connection and LangSmith tracing configured
- Customized Agent Chat UI with conversation history added
- Live LangChain documentation and release-note retrieval implemented
- Live GitHub issue and LangChain Forum retrieval implemented
- Hybrid live/local fallback and retrieval caching implemented
- Baseline dataset, online evaluators, and comparison experiments implemented
- Automated tests and linting passing

Not yet completed:

- Deployment and production-like traffic
- A larger dataset grounded in real resolved issues and Forum answers
- Final opportunity synthesis across the broader LangSmith lifecycle

## Immediate next steps

1. Compare live retrieval against the local baseline experiment.
2. Review source-level traces for latency, ranking, rate-limit, and fallback
   failures.
3. Add representative resolved GitHub and Forum cases to the evaluation dataset.
4. Tune source ranking and confidence calibration using experiment evidence.
5. Deploy the agent and generate production-like traffic.
6. Continue synthesizing evidence-backed LangSmith product opportunities.
