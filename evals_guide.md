# TalkingCode Evals Guide

## Goal

TalkingCode evals should measure agent behavior, not just final answer text.

The core question is: did the agent search the right evidence, use tools well,
cite real sources, avoid unsupported claims, and produce a useful answer grounded
in indexed repositories?

Phoenix should be the system of record for traces, eval datasets, evaluator
results, and human feedback.

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

Use real Phoenix traces from app usage to build eval datasets.

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

Implemented in `backend/src/talkingcode/evals/scorers.py`; each returns
`{score, label, explanation}` so failures are diagnosable in the Phoenix UI.
They read the structured trajectory captured by
`talkingcode/evals/trajectory.py` (tool calls with arguments and condensed
outputs, retrieved paths, search queries, tool errors, latency), not the
streamed markdown.

- required tools were called
- tools were used when the case requires them
- tool count stays within budget
- latency stays below threshold
- no tool call returned an error
- no duplicate search queries (redundancy = "too much" tool use)
- search queries mention the case's expected terms ("right direction")
- retrieval hit: expected paths were surfaced by tool results (separates
  retrieval failure from the agent ignoring evidence)
- answer mentions the expected source paths
- answer avoids prohibited unsupported claims
- answer carries [n] citations whenever evidence tools ran
- no citation index exceeds the number of retrieved files
- no internal markup (`<tc-...>`, `[Source n]`) leaks into the answer

### LLM Judge Scorers

Implemented in `backend/src/talkingcode/evals/judge.py`: a trajectory judge
(Arize trace-level eval pattern) that reads the ordered tool calls with
arguments and condensed results — not the final answer — and labels the
decision path `on_track` (1.0), `wandering` (0.5), or `lost` (0.0) with an
explanation. Runs through OpenRouter; model defaults to the intent-extraction
model and is overridable with `--judge-model`. Disable with `--no-judge`.

Candidate future rubric dimensions (not yet implemented): groundedness of the
final answer in tool outputs, uncertainty calibration, citation usefulness.

## 4. Human Feedback Loop

Use Phoenix traces for review.

Workflow:

1. Run the app.
2. Inspect Phoenix traces.
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

## Phoenix Notes

Use Phoenix for:

- trace capture (OpenInference instrumentation of the OpenAI Agents SDK)
- eval datasets
- experiment/evaluator execution
- model/prompt comparison
- human feedback (annotations)
- regression tracking

Dataset semantics: golden examples carry stable ids (the case id) and are
diff-synced — `create_dataset` compares the upload against the current version
and applies the minimal adds, edits, and deletes, so editing a case locally
and re-syncing updates it in place (new dataset version; old experiments keep
their version). Each case's category is also its dataset split, so
experiments can target a slice (e.g. only `tool_use_discipline`).

Running:

```
uv run python -m talkingcode.evals.runner \
  [--sync-dataset] [--dry-run] [--no-judge] \
  [--repetitions 3] [--concurrency 3] [--model-name ...] [--judge-model ...]
```

Repetitions matter because agent runs are nondeterministic: a single run per
case makes pass/fail flappy; 3 repetitions per case gives a variance signal.

Phoenix docs:

- Overview: https://arize.com/docs/phoenix
- Tracing: https://arize.com/docs/phoenix/tracing/llm-traces
- OpenAI Agents integration: https://arize.com/docs/phoenix/tracing/integrations-tracing/openai-agents-sdk
- Datasets: https://arize.com/docs/phoenix/datasets-and-experiments/datasets
- Experiments & evaluators: https://arize.com/docs/phoenix/datasets-and-experiments/experiments

## Hosting

Traces and datasets go to the hosted Phoenix instance at
https://phoenix.chidinweke.be (`PHOENIX_BASE_URL` +
`PHOENIX_API_KEY`); no local server is required for development.

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
