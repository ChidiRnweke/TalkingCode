# TalkingCode Evals Guide

## Goal

TalkingCode evals should measure agent behavior, not just final answer text.

The core question is: did the agent search the right evidence, use tools well,
cite real sources, avoid unsupported claims, and produce a useful answer grounded
in indexed repositories?

MLflow should be the system of record for traces, eval datasets, scorer results,
and human feedback.

## Evaluation Strategy

Use four layers:

1. Golden regression set
2. Trace-derived dataset
3. Scorers
4. Human feedback loop

## 1. Golden Regression Set

Maintain a small, hand-curated set of high-signal examples that must keep
working.

Recommended categories:

- Repo discovery
- File-specific explanation
- Cross-repo comparison
- Citation correctness
- Uncertainty and refusal
- Tool-use discipline

Example cases:

- "Which projects use Svelte?"
- "Explain the chat agent loop."
- "Compare the frontend and backend architecture."
- "What tech stack is used in TalkingCode?"
- "How many total projects have I ever built?"

Golden cases should include expectations like:

- whether tools should be used
- which tools are expected
- expected source paths
- prohibited unsupported claims
- rubric for answer quality

## 2. Trace-Derived Dataset

Use real MLflow traces from app usage to build eval datasets.

Promote traces when they represent:

- a great answer worth preserving
- wrong repo selection
- weak retrieval
- missing or incorrect citation
- excessive tool use
- slow or expensive execution
- hallucinated scope
- poor uncertainty handling

Trace-derived evals are especially important because TalkingCode failures are
usually behavioral, not simple string mismatches.

## 3. Scorers

Use both deterministic code-based scorers and LLM judge scorers.

### Code-Based Scorers

Recommended checks:

- answer includes citations when referencing code
- citations map to actual retrieved or read files
- no citation points to a nonexistent source id
- required tools were called
- prohibited tools were not called
- no tool errors occurred
- latency stays below threshold
- tool count stays below threshold
- iteration count stays below threshold
- answer avoids unsupported absolute claims like "all projects" unless evidence
  supports it

### LLM Judge Scorers

Recommended rubric dimensions:

- groundedness
- relevance
- completeness
- uncertainty calibration
- citation usefulness
- source faithfulness
- whether the answer represents Chidi's work accurately
- whether the agent used evidence appropriately

## 4. Human Feedback Loop

Use MLflow traces for review.

Workflow:

1. Run the app.
2. Inspect MLflow traces.
3. Mark good and bad traces.
4. Promote selected traces into eval datasets.
5. Add expectations.
6. Refine scorers around observed failures.
7. Run evals before prompt, model, retrieval, or tool changes.

## Eval Record Shape

A useful eval record should conceptually include:

```yaml
input:
  question: "Explain the chat agent loop."

expectations:
  should_use_tools: true
  required_tool_names:
    - search_github
    - read_file
  expected_source_paths:
    - backend/src/talkingcode/services/agent/agent_loop.py
  prohibited_claims:
    - "This covers all repositories"
  rubric: >
    Answer must be grounded in indexed repo evidence, cite relevant files,
    and avoid claiming exhaustive knowledge beyond retrieved sources.

outputs:
  final_answer: null

trace_fields:
  tools_called: []
  retrieved_paths: []
  read_paths: []
  citations: []
  latency_ms: null
  token_usage: null
  errors: []
```

## MLflow Notes

Use MLflow for:

- trace capture
- eval datasets
- scorer execution
- model/prompt comparison
- human feedback
- regression tracking

MLflow docs:

- GenAI overview: https://mlflow.org/docs/latest/genai/
- Tracing: https://mlflow.org/docs/latest/genai/tracing/
- DeepAgents tracing: https://mlflow.org/docs/latest/genai/tracing/integrations/listing/deepagent/
- Datasets: https://mlflow.org/docs/latest/genai/datasets/
- Scorers: https://mlflow.org/docs/latest/genai/eval-monitor/scorers/
- Eval quickstart: https://mlflow.org/docs/latest/genai/eval-monitor/quickstart/

## Hosting Requirement

Use a real MLflow Tracking Server with SQL-backed storage from the start.

Do not rely on local file-only tracking if eval datasets and trace promotion are
first-class workflows.

For local development, host MLflow in Docker Compose with Postgres-backed
tracking.

## Guiding Principle

Do not optimize for exact answer matching.

Optimize for:

- correct evidence use
- good tool choice
- grounded final answers
- useful citations
- appropriate uncertainty
- low operational cost
- low latency
- clear traceability
