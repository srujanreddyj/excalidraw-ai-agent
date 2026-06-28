# Python Agent Implementation Plan

Goal: make this resume claim true in a defensible way:

> Built a Python-first AI agent engineering system for a React/Excalidraw diagramming app, including tool-calling, planning-before-action, structured tracing, feedback capture, eval automation, and a data flywheel that promotes real user interactions into regression test cases.

This plan keeps the existing React/Excalidraw frontend in place and adds a Python AI engineering layer inside this repo.

## End State

By the end of the two-day build, you should be able to demo this loop:

1. Run the Python diagram agent on a prompt.
2. See a planning step before tool execution.
3. See Python tool calls mutate a simulated canvas.
4. Save a structured trace automatically.
5. Add feedback to the trace.
6. Promote the trace into a regression dataset.
7. Run evals against both the existing golden dataset and generated regressions.
8. Host the existing React/Excalidraw app for demo purposes, preferably on Cloudflare.

## Repo Strategy

Keep everything in this repo.

```text
ai-engineering-fundamentals/
  src/                  # existing React + Cloudflare frontend/backend
  evals/                # existing eval datasets and TS eval runner
  python_agent/         # new Python implementation and local plan
```

The frontend/client-side Excalidraw experience should remain the same. Python starts as an agent/eval/flywheel implementation beside the existing app. Later, the same frontend can be wired to a Python backend if desired.

## Day 1: Python Agent, Planning, And Evals

Target outcome: run the diagram agent from Python against existing eval cases.

### Step 1: Create Python Package Skeleton

Inside `python_agent/`, create:

```text
pyproject.toml
README.md
src/
  diagram_agent/
    __init__.py
    prompts.py
    schemas.py
    canvas.py
    tools.py
    agent.py
    planner.py
    evals.py
    cli.py
tests/
  test_canvas.py
```

Suggested dependencies:

```bash
uv init python_agent
cd python_agent
uv add openai pydantic python-dotenv typer rich pytest ruff
```

CLI goals:

```bash
uv run diagram-agent run "Draw a flow from User to API to Database"
uv run diagram-agent eval --dataset ../evals/datasets/golden_2.json
```

Definition of done:

- `uv run pytest` works.
- `uv run diagram-agent --help` works.
- Package imports cleanly.

### Step 2: Port The System Prompt

Create `src/diagram_agent/prompts.py`.

Copy the agent system prompt from `src/agent-core.ts` into Python as `SYSTEM_PROMPT`.

Definition of done:

- Python agent and TS agent share the same behavioral contract.
- Prompt changes later have one obvious place to update in Python.

### Step 3: Implement Pydantic Schemas

Create `src/diagram_agent/schemas.py`.

Implement Pydantic models for:

- rectangle
- ellipse
- diamond
- arrow
- text
- `AddElementsInput`
- `UpdateElementsInput`
- `RemoveElementsInput`
- `AgentResult`
- `ToolCallRecord`
- `Plan`

Keep the first version pragmatic. The models do not need perfect Excalidraw fidelity, but they should validate the fields the agent uses.

Definition of done:

- Invalid tool inputs fail validation.
- Valid simple rectangles/arrows/text pass validation.
- Tests cover basic valid and invalid objects.

### Step 4: Build The Canvas Simulator

Create `src/diagram_agent/canvas.py`.

Implement:

```python
class CanvasState:
    def query(self) -> str: ...
    def add_elements(self, elements: list[dict]) -> dict: ...
    def update_elements(self, updates: list[dict]) -> dict: ...
    def remove_elements(self, ids: list[str]) -> dict: ...
    def to_elements(self) -> list[dict]: ...
```

Canvas behavior to support:

- Store elements in memory.
- Add model-proposed elements.
- Expand shape labels into child text elements when useful.
- Bind arrow starts/ends when `start.id` and `end.id` are provided.
- Update existing elements by id.
- Remove elements by id.
- Return compact canvas summaries.
- Detect obvious overlaps.

Use these TS files as behavioral references:

- `src/context/applySkeleton.ts`
- `src/context/overlaps.ts`
- `src/context/canvas-state.ts`

Definition of done:

- Adding elements changes canvas state.
- Updating by id changes only targeted elements.
- Removing by id removes expected elements.
- `query()` returns a human-readable summary.
- Overlap detection catches obvious collisions.

### Step 5: Implement Python Tools

Create `src/diagram_agent/tools.py`.

Implement Python functions:

```python
query_canvas()
add_elements(elements)
update_elements(updates)
remove_elements(ids)
```

Each function should:

- validate input with Pydantic
- call `CanvasState`
- return structured JSON-serializable output
- include useful errors instead of crashing when possible

Optional later:

- `search_web`
- `search_knowledge`

Definition of done:

- Tools can be called directly from tests.
- Tool outputs are serializable.
- Tool outputs are suitable to feed back into an LLM tool loop.

### Step 6: Implement The Python Tool-Calling Agent

Create `src/diagram_agent/agent.py`.

Implement a manual OpenAI tool loop:

1. Start with system prompt and user messages.
2. Send OpenAI request with tool schemas.
3. If the model returns tool calls, execute Python tools.
4. Append tool results to the conversation.
5. Continue until no tool calls or `max_steps`.
6. Return text, final elements, tool calls, usage, steps, latency, and errors.

Suggested result shape:

```python
AgentResult(
    text=str,
    elements=list[dict],
    tool_calls=list[ToolCallRecord],
    steps=list[dict],
    usage=dict,
    latency_ms=int,
)
```

Definition of done:

```bash
uv run diagram-agent run "Draw a single rectangle labeled Hello"
```

prints:

- final assistant text
- list of tool calls
- final canvas element count
- latency
- usage if available

### Step 7: Add Planning Before Acting

Create `src/diagram_agent/planner.py`.

Before the tool loop, make one model call with no tools. Ask for structured JSON:

```python
Plan(
    intent=str,
    steps=list[str],
    tools_likely_needed=list[str],
    risks=list[str],
)
```

Then pass the plan into the agent as context:

```text
Before acting, follow this approved plan:
...
```

Support CLI modes:

```bash
uv run diagram-agent run "..." --planning off
uv run diagram-agent run "..." --planning required
uv run diagram-agent run "..." --planning auto
```

Initial `auto` heuristic:

- plan if prompt is long
- plan if seed canvas is non-empty
- plan if prompt asks to modify existing content
- plan if prompt implies multiple tools or many elements

Definition of done:

- A run with `--planning required` prints the plan before the result.
- A run with `--planning off` skips the planning call.
- The result stores the plan if one was produced.

### Step 8: Build The Python Eval Runner

Create `src/diagram_agent/evals.py`.

Load existing eval cases from:

```text
../evals/datasets/golden_2.json
```

For each case:

- create initial `CanvasState` from `seed.elements` if present
- run the Python agent
- score basic properties
- write a JSON report

Start with these scorers:

- schema validity
- expected keywords present
- expected tool calls
- no obvious overlaps
- preserved ids for modify cases

Output reports to:

```text
python_agent/runs/eval-YYYYMMDD-HHMMSS.json
```

Definition of done:

```bash
uv run diagram-agent eval --dataset ../evals/datasets/golden_2.json --planning required
```

prints:

- number of cases
- pass/fail summary
- average latency
- average token usage if available
- path to report JSON

## Day 2: Tracing, Feedback, Flywheel, And Demo Hosting

Target outcome: every Python run becomes a trace, feedback can be attached, bad traces can become regression eval cases, and the existing app can be hosted for demos.

### Step 9: Add SQLite Trace Storage

Create `src/diagram_agent/tracing.py`.

Use SQLite first. Store the database at:

```text
python_agent/.data/traces.sqlite
```

Create tables:

```sql
create table if not exists traces (
  id text primary key,
  created_at text not null,
  input text not null,
  plan_json text,
  final_text text,
  final_elements_json text,
  usage_json text,
  latency_ms integer,
  status text not null
);

create table if not exists tool_events (
  id text primary key,
  trace_id text not null,
  step_index integer not null,
  tool_name text not null,
  input_json text not null,
  output_json text not null
);

create table if not exists feedback (
  id text primary key,
  trace_id text not null,
  rating text not null,
  note text,
  created_at text not null
);

create table if not exists eval_candidates (
  id text primary key,
  trace_id text not null,
  reason text not null,
  status text not null,
  created_at text not null
);
```

Definition of done:

- Every `run` creates a trace.
- Every tool call creates a tool event.
- Failed runs also create traces with `status = "error"`.

### Step 10: Add Trace CLI Commands

Extend `src/diagram_agent/cli.py`.

Commands:

```bash
uv run diagram-agent traces list
uv run diagram-agent traces show TRACE_ID
uv run diagram-agent traces tools TRACE_ID
```

`show` should display:

- input
- plan
- final text
- latency
- usage
- final element count
- status

Definition of done:

- You can inspect recent traces from the terminal.
- A trace is readable enough to debug an agent failure.

### Step 11: Add Feedback Capture

Add CLI commands:

```bash
uv run diagram-agent feedback add TRACE_ID --rating down --note "Boxes overlapped"
uv run diagram-agent feedback add TRACE_ID --rating up --note "Good complex diagram"
```

Rules:

- thumbs down creates an `eval_candidate`
- thumbs up can create an `eval_candidate` when the prompt is complex or unusual
- free-text notes are stored with the trace

Definition of done:

- Feedback is joined to the trace that produced the output.
- A negative feedback item appears in the candidate queue.

### Step 12: Build Promotion Pipeline

Add CLI commands:

```bash
uv run diagram-agent candidates list
uv run diagram-agent candidates promote TRACE_ID --set regression
uv run diagram-agent candidates ignore TRACE_ID
```

Promotion writes to:

```text
../evals/datasets/generated_regressions.json
```

Generated case shape:

```json
{
  "id": "trace-regression-20260527-001",
  "input": "original user prompt",
  "expectedCharacteristics": [
    "Human feedback: Boxes overlapped"
  ],
  "expectedKeywords": [],
  "difficulty": "medium",
  "category": "create"
}
```

Definition of done:

- A thumbs-down trace can become a JSON regression case.
- Ignored candidates do not show up in the active queue.
- Promotion is idempotent enough to avoid obvious duplicates.

### Step 13: Include Generated Regressions In Evals

Update the Python eval CLI to accept multiple datasets:

```bash
uv run diagram-agent eval \
  --dataset ../evals/datasets/golden_2.json \
  --dataset ../evals/datasets/generated_regressions.json \
  --planning required
```

Run two comparison evals:

```bash
uv run diagram-agent eval --planning off
uv run diagram-agent eval --planning required
```

Compare:

- score
- latency
- token usage
- tool-call count
- failure modes

Definition of done:

- Generated regressions are part of the Python eval suite.
- You can explain the latency/quality tradeoff of planning-before-action.

### Step 14: Add Minimal React Feedback UI Later

This is optional for the two-day version, but it completes the product loop.

Files to touch:

- `src/components/chat/MessageBubble.tsx`
- `src/components/chat/chat.css`

Add:

- thumbs up button
- thumbs down button
- optional note field on thumbs down

Initial implementation can POST to a Python or Cloudflare endpoint later.

Definition of done:

- Users can rate assistant messages from the existing UI.
- Feedback includes enough context to join to a trace.

### Step 15: Host The Existing App On Cloudflare

Preferred free demo path: Cloudflare.

Why:

- This repo already uses Cloudflare Workers and the Agents SDK.
- The existing app is already configured with `wrangler.toml`.
- The React/Excalidraw frontend can remain unchanged.
- Free-tier limits are suitable for a small demo.

Tasks:

1. Verify build:

   ```bash
   npm run build
   ```

2. Configure Cloudflare secrets:

   ```bash
   npx wrangler secret put OPENAI_API_KEY
   npx wrangler secret put TAVILY_API_KEY
   npx wrangler secret put UPSTASH_VECTOR_REST_URL
   npx wrangler secret put UPSTASH_VECTOR_REST_TOKEN
   ```

3. Deploy:

   ```bash
   npx wrangler deploy
   ```

4. Save the deployed URL.

5. Add a short demo note to the project README:

   ```text
   Demo: hosted React/Excalidraw diagramming app on Cloudflare.
   Python agent engineering layer: planning, traces, feedback, evals, and regression promotion.
   ```

Definition of done:

- App opens from a public Cloudflare URL.
- You can create a diagram from the hosted app.
- You can explain that Cloudflare hosts the product demo while Python powers the agent engineering loop.

### Step 16: Optional Modal Demo For Python Backend

Use Modal only for the Python API demo, not as the primary frontend host.

Suggested files:

```text
src/diagram_agent/server.py
src/diagram_agent/modal_app.py
```

Minimal endpoints:

```text
POST /run
POST /feedback
GET /traces
POST /promote
```

Deploy:

```bash
modal deploy src/diagram_agent/modal_app.py
```

Cost-control rules:

- CPU only
- no GPU
- no always-on containers
- low timeout
- demo traffic only

Definition of done:

- Python service can run on Modal for demos.
- You stay within free/credit-backed usage.

## Final Demo Script

Use this sequence when showing the project:

1. Open the hosted Cloudflare app.
2. Create a diagram in the React/Excalidraw UI.
3. Run Python agent locally:

   ```bash
   uv run diagram-agent run "Draw a JWT auth flow" --planning required
   ```

4. Show the plan and tool calls.
5. List traces:

   ```bash
   uv run diagram-agent traces list
   ```

6. Add feedback:

   ```bash
   uv run diagram-agent feedback add TRACE_ID --rating down --note "Missing token storage"
   ```

7. Promote it:

   ```bash
   uv run diagram-agent candidates promote TRACE_ID --set regression
   ```

8. Run evals:

   ```bash
   uv run diagram-agent eval \
     --dataset ../evals/datasets/golden_2.json \
     --dataset ../evals/datasets/generated_regressions.json \
     --planning required
   ```

## Resume Claim Mapping

The resume point maps to concrete implementation pieces:

- Python-first AI agent engineering system: `python_agent/`
- React/Excalidraw diagramming app: existing `src/`
- tool-calling: `agent.py`, `tools.py`, `schemas.py`
- planning-before-action: `planner.py`
- structured tracing: `tracing.py`
- feedback capture: feedback CLI and `feedback` table
- eval automation: `evals.py`
- data flywheel: candidates and promotion pipeline
- regression test cases: `evals/datasets/generated_regressions.json`

## Two-Day Definition Of Done

The project is successful if all of these are true:

- Python agent can run one prompt end-to-end.
- Python planner produces a visible plan.
- Python tool calls mutate a simulated canvas.
- A structured trace is saved for every run.
- Feedback can be attached to a trace.
- A feedback trace can be promoted to a regression dataset.
- Python eval runner can include generated regressions.
- Existing app can be deployed or is ready to deploy to Cloudflare.

