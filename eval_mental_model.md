This system has four connected parts:

```text
1. Structured tracing
        ↓
2. Feedback capture
        ↓
3. Eval candidates
        ↓
4. Data flywheel / regression promotion
        ↓
5. Eval automation
        ↓
Back to improving the agent
```

The big idea is:

> Every real agent run should become observable. Every user complaint should be attached to a trace. Some complaints should become eval cases. Eval cases should run automatically so the same failure does not silently come back.

That is what makes this more than “I called OpenAI from an app.”

---

**1. Structured Tracing**

Structured tracing means: every agent run is saved as machine-readable data, not just printed logs.

In your project, tracing lives mainly here:

[tracing.py](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent/src/diagram_agent/tracing.py)

The central class is:

```python
class TraceStore:
```

It creates a SQLite DB at:

```text
python_agent/.data/traces.sqlite
```

The important tables are:

```text
traces
tool_events
feedback
eval_candidates
```

A trace answers:

```text
What did the user ask?
Did we plan?
What tools did the agent call?
What did each tool receive?
What did each tool return?
What final canvas was produced?
Did errors happen?
How long did it take?
```

A single trace is basically the flight recorder for one agent run.

For example, when the agent runs:

```bash
uv run diagram-agent run "Draw a JWT auth flow" --backend openai --planning required
```

or when the UI calls:

```text
POST /run
```

your code eventually saves:

```python
TraceStore(DEFAULT_TRACE_DB).save_run(result)
```

That `result` is an `AgentRunResult`.

It includes things like:

```python
prompt
plan
final_text
steps
tool_calls
canvas_elements
errors
latency_ms
trace_id
```

This is important because AI systems fail in non-obvious ways. Without traces, all you can say is:

> “The diagram looked wrong.”

With traces, you can say:

> “The model planned correctly, called `addElements`, created the right nodes, but the arrow bindings were wrong.”

That is a much stronger engineering story.

---

**2. Tool Events**

Tool events are a subpart of tracing.

In agent systems, tool calls are where intent becomes action.

Your `tool_events` table stores each tool call:

```text
trace_id
call_index
tool_call_id
tool_name
input_json
output_json
```

Example:

```text
trace_123
0
call_abc
addElements
{"elements": [...]}
{"added": [...], "canvas": [...]}
```

This matters because agent bugs often happen at the tool boundary.

The model might say:

```text
I created a JWT auth flow.
```

But the trace might show:

```json
{
  "tool_name": "addElements",
  "input_json": {
    "elements": [
      {"id": "user", "type": "rectangle"},
      {"id": "api", "type": "rectangle"}
    ]
  }
}
```

Then you know the model did not actually add Auth Server, JWT, Refresh Token, etc.

So the trace separates:

```text
model claim
from
actual tool action
```

That distinction is very interview-relevant.

---

**3. Feedback Capture**

Feedback capture means: the user can react to a specific agent result.

In the UI, after a Python run, the assistant message includes:

```text
Trace: trace_...
```

Then the frontend extracts that trace id and shows buttons like:

```text
Good
Bad
View trace
```

When the user clicks feedback, the frontend calls:

```text
POST /feedback
```

That endpoint is in:

[api.py](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent/src/diagram_agent/api.py)

The backend calls:

```python
TraceStore(DEFAULT_TRACE_DB).add_feedback(
    trace_id=request.trace_id,
    rating=request.rating,
    note=note,
)
```

The important thing is that feedback is not floating around by itself.

Bad version:

```text
User clicked thumbs down.
```

Good version:

```text
User clicked thumbs down on trace_abc123, whose prompt was X, whose plan was Y, whose tool calls were Z, and whose final canvas was W.
```

That join is everything.

Feedback without traces is weak.
Traces without feedback are incomplete.
Together, they tell you which real runs matter.

---

**4. Eval Candidates**

When feedback is negative, your system creates an eval candidate.

In [tracing.py](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent/src/diagram_agent/tracing.py), this is the key rule:

```python
if rating == "down":
    INSERT OR IGNORE INTO eval_candidates ...
```

So:

```text
thumbs up → store feedback
thumbs down → store feedback + create eval candidate
```

Why not immediately create a regression test?

Because not every downvote should become a permanent eval.

Sometimes the user was unclear.
Sometimes the feedback is not actionable.
Sometimes the model output was acceptable but the user expected something else.

So you create an intermediate queue:

```text
eval_candidates
```

Statuses:

```text
new
ignored
promoted
```

This gives you a review step.

That is good AI engineering practice. The data flywheel should not blindly ingest every signal. It should have curation.

---

**5. Data Flywheel**

The data flywheel is the full loop:

```text
real user interaction
→ trace
→ feedback
→ candidate
→ promoted regression
→ future eval
→ agent improves
```

Your flywheel logic lives here:

[flywheel.py](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent/src/diagram_agent/flywheel.py)

The core function is:

```python
promote_candidate(...)
```

It does roughly:

```python
trace = store.get_trace(trace_id)
candidate = store.get_eval_candidate(trace_id)
feedback = store.get_feedback(trace_id)

case = build_regression_case(trace, candidate, feedback)

write_regression_case(dataset_path, case)

store.update_eval_candidate_status(trace_id, "promoted")
```

So it takes a real failed interaction and turns it into a dataset case.

The generated file is:

```text
evals/datasets/generated_regressions.json
```

The shape looks like:

```json
{
  "id": "trace-regression-trace_abc123",
  "input": "Draw a data model with fact and dim tables",
  "expectedCharacteristics": [
    "Human feedback: Boxes overlapped"
  ],
  "expectedKeywords": [],
  "difficulty": "medium",
  "category": "create"
}
```

This is the “flywheel” because the system learns from actual usage.

Not model training yet. Not fine-tuning. But evaluation learning.

The agent gets better because your test suite gets smarter.

---

**6. Eval Automation**

Eval automation means: you can run a dataset of prompts and score the agent outputs automatically.

Your eval runner lives here:

[evals.py](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent/src/diagram_agent/evals.py)

The main function is:

```python
run_eval(dataset_paths, planning="off")
```

It loads cases from JSON datasets like:

```text
evals/datasets/golden_2.json
evals/datasets/generated_regressions.json
```

Each case has fields like:

```json
{
  "id": "create-simple-01",
  "input": "Draw a single rectangle labeled Hello",
  "expectedCharacteristics": [
    "1 rectangle element",
    "The rectangle has a label or accompanying text element with content Hello"
  ],
  "expectedKeywords": ["hello"],
  "difficulty": "simple",
  "category": "create"
}
```

For each case, the eval runner:

```python
result = run_agent(case.input, planning=planning)
```

Then it scores the result.

Right now your scoring is still basic:

```python
scores = {
    "schema_valid": True,
    "expected_keywords_present": not missing_keywords,
    "no_overlaps": True,
}
```

This is the part we still need to improve.

Current eval automation proves the loop works.

But better eval automation should eventually score:

```text
Did it create the right number of shapes?
Did it use the right shape types?
Are labels correct?
Are arrows bound correctly?
Are there overlaps?
Did modify prompts preserve existing IDs?
Did expected tool calls happen?
```

So current evals are a skeleton, not the final quality system.

That is okay. The important thing is you built the pipeline first.

---

**7. How These Parts Connect In Your App**

Here is the end-to-end flow when using the UI:

```text
User sends prompt in React
        ↓
Frontend calls Python /plan
        ↓
User reviews plan
        ↓
Frontend calls Python /run
        ↓
Python agent calls tools
        ↓
CanvasState mutates
        ↓
AgentRunResult is created
        ↓
TraceStore saves trace + tool events
        ↓
Frontend receives final_text + trace_id
        ↓
User clicks Bad
        ↓
POST /feedback
        ↓
TraceStore saves feedback
        ↓
If rating is down, eval_candidate is created
        ↓
CLI promotes candidate
        ↓
generated_regressions.json is updated
        ↓
Future eval runs include this regression
```

That is your full system.

---

**8. Why This Matters For Interviews**

A weak resume claim would be:

> “Built an AI diagram generator.”

That mostly says you made a wrapper around an LLM.

Your stronger claim is:

> “Built a Python-first AI agent engineering system for a React/Excalidraw app, including tool-calling, planning-before-action, structured tracing, feedback capture, eval automation, and a data flywheel that promotes real user interactions into regression test cases.”

That says you understand production AI systems.

You are showing:

```text
agent behavior
observability
human feedback
evaluation
regression testing
deployment thinking
```

That is much more serious.

A good interview explanation:

> “I did not want the app to just generate diagrams. I wanted every agent action to be inspectable. So each run gets a trace id, and I store the prompt, plan, tool calls, outputs, final canvas, errors, and latency in SQLite. The UI exposes that trace id, and feedback is attached directly to it. If a user downvotes a result, the trace becomes an eval candidate. I can then promote it into a generated regression dataset, so real product failures become automated tests. That creates a data flywheel around the agent.”

That is the core story.

---

**9. The Current Weak Spots**

You should also understand what is not yet strong.

Current weaknesses:

```text
Eval scoring is still too shallow.
Generated regressions store human feedback but do not yet convert it into rich assertions.
Trace storage is SQLite local, not hosted durable storage.
Braintrust export exists, but Braintrust is not yet the primary eval dashboard.
The UI feedback note is basic.
```

That is fine. You can explain these as staged architecture.

Good phrasing:

> “I started with local deterministic artifacts first: SQLite traces and JSON eval reports. Then I added Braintrust as an external reporting layer. I intentionally kept local reports as the source of truth so the system was not vendor-locked.”

That sounds mature.

---

**10. Simple Mental Model**

If you remember only one thing, remember this:

```text
Tracing records what happened.
Feedback records whether it was good.
Eval candidates decide what is worth keeping.
The flywheel turns real failures into regression tests.
Eval automation checks whether future changes break those cases.
```

That is the entire system.