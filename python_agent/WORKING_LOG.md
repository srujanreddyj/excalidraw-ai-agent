# Python Agent Working Log

This log captures the learning path, design decisions, troubleshooting notes, and interview-ready explanations for the Python-first AI engineering layer.

## Current Architecture

- The frontend remains React + Excalidraw.
- The existing Cloudflare/TypeScript agent path still exists.
- `python_agent/` contains the Python AI engineering layer:
  - Typer CLI
  - canvas simulator
  - Pydantic tool schemas
  - Python tool router
  - OpenAI Responses tool-calling loop
  - OpenAI planning client
  - FastAPI backend
  - SQLite traces
  - eval runner foundation
- The UI can now switch between:
  - `Cloudflare`: existing TypeScript/Cloudflare path
  - `Python`: Python FastAPI path with visible plan review

## Milestones Completed

### Python Package And CLI

- Created `python_agent/` as a separate uv-managed Python package inside the repo.
- Added `diagram-agent` Typer CLI.
- CLI is useful even though the app has a chat UI because it gives us:
  - repeatable local testing
  - eval execution
  - tracing inspection
  - feedback and data flywheel commands later
  - a backend-independent debugging surface

### Canvas Simulator

- Added a Python `CanvasState` that can add, update, remove, query, detect overlaps, and serialize compact canvas text.
- This lets us test agent behavior without a browser.
- The simulator is not full Excalidraw; it is enough to validate agent tool behavior and eval logic.

### Python Tool Layer

- Ported tool input schemas into Pydantic.
- Preserved the TypeScript tool contract:
  - shape labels use `label: {"text": "..."}`
  - arrows use `start: {"id": "..."}` and `end: {"id": "..."}`
- Python internally normalizes those into `CanvasElement.text`, `start_id`, and `end_id`.
- Added a tool registry:
  - `queryCanvas`
  - `addElements`
  - `updateElements`
  - `removeElements`
- This maps OpenAI-facing camelCase tool names to Python functions.

### OpenAI Tool Calling

- Added `OpenAIResponsesModelClient`.
- Added an injectable fake model client for offline tests.
- Built a manual Responses API tool loop:
  1. send messages and tool definitions
  2. receive function calls
  3. execute Python tools
  4. append function call and function output history
  5. continue until final response

### Planning

- Started with deterministic planning.
- Deterministic means local Python code creates the plan without calling OpenAI.
- Added optional OpenAI planning with `OpenAIPlannerClient`.
- Planning mode and planner backend are separate:
  - `--planning off|required|auto` controls whether planning happens
  - `--planner-backend local|openai` controls how the plan is created

### FastAPI Backend And UI Integration

- Added Python FastAPI backend:
  - `GET /health`
  - `POST /plan`
  - `POST /run`
- React UI Python mode now uses the Python backend.
- Python UI flow:
  1. user sends prompt
  2. UI calls `/plan`
  3. UI displays Review Plan
  4. user clicks Execute
  5. UI calls `/run` with `approved_plan`
  6. Python agent executes tools
  7. canvas updates
  8. assistant message shows final text and trace id

### Tracing

- Added `trace_id` to every agent run.
- Added SQLite `traces` table.
- Added SQLite `tool_events` table.
- Added SQLite `feedback` table.
- Added SQLite `eval_candidates` table.
- CLI can inspect saved traces:
  - `diagram-agent traces list`
  - `diagram-agent traces show TRACE_ID`
  - `diagram-agent traces tools TRACE_ID`

### Feedback Capture

- Added `POST /feedback`.
- React assistant messages that include a `Trace: trace_...` line now show feedback buttons.
- Thumbs up stores positive feedback.
- Thumbs down stores feedback and creates an eval candidate.
- This connects the product loop to the data flywheel:

```text
real UI interaction -> trace_id -> feedback -> eval candidate
```

## Key Design Decisions

### Why Keep The CLI If We Have A UI?

The CLI is the engineering/debugging surface. The UI is the product surface.

The CLI makes it easy to:

- run local smoke tests
- run evals
- inspect traces
- reproduce bugs
- add feedback commands
- promote examples into regression datasets

In interviews, this shows the system was designed for iteration and observability, not just a demo.

### Why Start With Deterministic Planning?

We started with deterministic planning to define the contract first:

```text
Plan:
  intent: str
  steps: list[str]
  tools_likely_needed: list[str]
  risks: list[str]
```

This made planning:

- cheap
- testable
- offline
- predictable

Then we added OpenAI planning behind the same contract.

### Why Separate Planning Mode From Planner Backend?

Planning mode answers: should we plan?

```text
off|required|auto
```

Planner backend answers: who creates the plan?

```text
local|openai
```

This lets us run offline tests with local planning and real demo flows with OpenAI planning.

### Why `/plan` Then `/run`?

The UI needed human-in-the-loop planning-before-action.

`/plan` creates a visible plan. `/run` executes only after the user approves it.

This is stronger than hidden planning because the user can inspect intent, steps, tools, and risks before the canvas is mutated.

### Why Python API Instead Of Replacing React?

React + Excalidraw is still the right client.

Python owns the AI engineering layer:

- planning
- tool-calling orchestration
- validation
- tracing
- evals
- feedback/flywheel

The frontend remains responsible for rendering and applying Excalidraw elements.

### Why Preserve TypeScript Tool Shapes?

The existing app already taught the model a useful tool contract.

Preserving `label.text` and `start.id/end.id` avoids creating two incompatible tool languages.

Python can have idiomatic internals, but the model-facing schema should stay compatible with the UI's Excalidraw assumptions.

## Troubleshooting / Battle Scars

### `diagram-agent` Not Found

Problem:

```text
Failed to spawn: diagram-agent
```

Cause:

- uv project script was not available because package configuration was incomplete or the command was not run through uv.

Fix:

- added proper `pyproject.toml` script and package config
- use:

```bash
uv run diagram-agent ...
```

### Typer Treated `run` As A Prompt

Problem:

```text
Got unexpected extra argument(s)
```

Cause:

- Typer app did not have the right command/callback structure at first.

Fix:

- configured `app = typer.Typer(...)`
- used subcommands properly

### JSON Output Was Polluted

Problem:

```text
uv run diagram-agent run ... --json | python -m json.tool
Extra data
```

Cause:

- CLI printed human-readable text after JSON output.

Fix:

- when `--json` is enabled, print JSON and return immediately.

### Tool Functions Did Not Mutate Canvas

Problem:

- tests expected added elements, but `result["added"]` was empty.

Cause:

- `add_elements` parsed inputs but forgot to call `canvas.add_elements(elements)`.

Fix:

- call canvas mutation method, then return added elements and updated canvas.

### Responses API Tool History Bug

Problem from live OpenAI call:

```text
No tool call found for function call output with call_id ...
```

Cause:

- The next Responses API request included `function_call_output`, but not the original `function_call` item.
- OpenAI could not match the output to the original call id.

Fix:

- append both items to message history:

```python
{
    "type": "function_call",
    "call_id": call_id,
    "name": name,
    "arguments": arguments_json,
}
```

then:

```python
{
    "type": "function_call_output",
    "call_id": call_id,
    "output": json.dumps(tool_output),
}
```

Interview note: this is a real production-style agent bug. Tool loops need correct provider-specific conversation state, not just tool execution.

### `.dev.vars` Not Automatically Loaded

Problem:

- OpenAI key was present for Cloudflare but Python did not see it.

Cause:

- Python `python-dotenv` does not automatically load Cloudflare `.dev.vars`.

Fix:

```python
load_dotenv()
load_dotenv("../.dev.vars")
load_dotenv("../.dev.var")
```

### `package.json` Had Comments

Problem:

```text
npm error JSON.parse Invalid package.json
```

Cause:

- `package.json` contained JavaScript-style comments.

Fix:

- removed commented script lines so npm tooling could parse the file.

### FastAPI Import Confusion

Problem:

- `uv run pytest` initially reported `ModuleNotFoundError: fastapi`.

Cause:

- environment/script mismatch after adding dependencies.

Fix:

- confirmed with:

```bash
uv run python -c "import fastapi; print(fastapi.__version__)"
```

- running tests through the uv interpreter worked:

```bash
uv run python -m pytest
```

## Interview Notes

### How To Explain The System

This system separates the product UI from the AI engineering runtime.

React + Excalidraw handles user interaction and rendering. Python handles agent orchestration: planning, tool schemas, validation, tool execution, tracing, evals, and eventually feedback-driven regression generation.

### How To Explain Tool Calling

The model does not directly mutate the canvas. It emits structured tool calls like `addElements`. Python validates those inputs with Pydantic, mutates a simulated canvas, returns a JSON tool result, and continues the model loop until a final response.

### How To Explain Planning-Before-Action

The system supports both hidden and visible planning.

In the UI Python mode, planning is human-in-the-loop:

```text
prompt -> /plan -> user review -> Execute -> /run
```

The approved plan is passed into the acting agent so the model acts with explicit intent, steps, likely tools, and risks.

### How To Explain Tracing

Every run gets a `trace_id`.

The trace records:

- input prompt
- plan JSON
- final text
- final canvas
- steps
- errors
- latency
- tool call count

Tool events separately record each tool call input and output.

This makes failures debuggable and later enables feedback-to-eval promotion.

### How To Explain Feedback And The Flywheel

User feedback is attached to a specific `trace_id`, not just a vague prompt.

That matters because a trace contains:

- the original input
- the approved plan
- tool calls
- tool outputs
- final canvas
- errors and latency

When a user gives thumbs down, the system creates an eval candidate. That candidate can later be promoted into a generated regression dataset. This is the data flywheel: real failures become future automated tests.

## Verification Commands

Run Python tests:

```bash
cd python_agent
uv run python -m pytest
```

Run ruff:

```bash
uv run ruff check src
```

Run local CLI:

```bash
uv run diagram-agent run "Draw a flow from User to API to Database"
```

Run OpenAI backend:

```bash
uv run diagram-agent run "Draw a JWT auth flow" \
  --backend openai \
  --planning required \
  --planner-backend openai
```

Start Python API:

```bash
cd python_agent
uv run uvicorn diagram_agent.api:app --host 127.0.0.1 --port 8000
```

Start React UI:

```bash
npm run dev -- --host 127.0.0.1
```

Frontend Python API config:

```bash
cp .env.example .env
```

```bash
VITE_PYTHON_AGENT_URL=http://127.0.0.1:8000
```

Manual UI test:

1. open `http://127.0.0.1:5173`
2. switch backend to `Python`
3. verify the chat shows Python backend health
4. send `Draw a JWT auth flow`
5. verify the chat shows `Planning...`
6. verify Review Plan appears
7. verify the chat shows `Waiting for approval`
8. click Execute
9. verify the chat shows `Executing...`
10. verify canvas updates
11. verify assistant message includes `Trace: trace_...`

Inspect traces:

```bash
uv run diagram-agent traces list
uv run diagram-agent traces show TRACE_ID
uv run diagram-agent traces tools TRACE_ID
```

Capture CLI feedback:

```bash
uv run diagram-agent feedback add TRACE_ID --rating down --note "Boxes overlapped"
```

Inspect and promote eval candidates:

```bash
uv run diagram-agent candidates list
uv run diagram-agent candidates ignore TRACE_ID
uv run diagram-agent candidates promote TRACE_ID --set regression
```

Run evals with human-generated regressions:

```bash
uv run diagram-agent eval \
  --dataset ../evals/datasets/golden_2.json \
  --dataset ../evals/datasets/generated_regressions.json
```

## Open Questions / TODO

- Move inline Review Plan styles from `App.tsx` into CSS.
- Upgrade eval scoring beyond keyword matching.
- Improve frontend feedback UI:
  - show selected thumbs state
  - allow optional note text

## UI Battle Scar: Approval Panel During Execution

The first planning UI kept the Review Plan approval card mounted after the user clicked Execute. That created a confusing state: the agent was already executing, but the old approval panel still occupied the chat area and visually overlapped the conversation.

Fix: clicking Execute now captures the approved plan in local variables, clears `pendingPrompt` / `pendingPlan` immediately, and then starts the `/run` call. The UI now has one active state at a time:

1. `Planning...`
2. Review Plan with Execute / Cancel
3. `Executing...`
4. final assistant response with `Trace: trace_...`

Interview lesson: human-in-the-loop agent UX needs explicit state transitions. Planning, approval, execution, and completion should be visually distinct, because ambiguity makes it hard to debug whether the model, the backend, or the user is responsible for the current action.

## Data Flywheel Milestone

Implemented the first complete feedback-to-regression loop:

1. A run is saved into SQLite as a trace.
2. Thumbs-down or CLI feedback is written to `feedback`.
3. Downvotes create an `eval_candidates` row.
4. Candidates can be listed, ignored, or promoted.
5. Promotion writes a compatible eval case to `evals/datasets/generated_regressions.json`.
6. The eval runner already accepts multiple `--dataset` flags, so generated regressions can run beside `golden_2.json`.

Commands added:

```bash
uv run diagram-agent feedback add TRACE_ID --rating down --note "..."
uv run diagram-agent candidates list
uv run diagram-agent candidates ignore TRACE_ID
uv run diagram-agent candidates promote TRACE_ID --set regression
```

Verification:

```bash
uv run python -m pytest
uv run ruff check src
```

Latest result: `62 passed`; ruff passed.

Interview lesson: the flywheel is the difference between a demo agent and an engineering system. The important claim is not that feedback exists; it is that feedback is joined to a trace, converted into a candidate, reviewed/promoted, and then run forever as a regression.

## Frontend Python API Cleanup

The frontend now treats the Python backend as an explicit dependency instead of a hidden local assumption.

Changes:

- `VITE_PYTHON_AGENT_URL` is documented in `.env.example`.
- Local `.env` files are ignored, while `.env.example` is tracked.
- The Python backend defaults to `http://127.0.0.1:8000` for local development.
- Switching to the Python backend checks `/health`.
- The chat UI shows Python backend health: not checked, checking, online, or offline.
- Offline Python requests produce a concrete recovery command instead of a raw fetch error.
- `python_agent/` is no longer ignored by root `.gitignore`, so it can be committed for the portfolio.

Interview lesson: frontend-to-agent integration needs clear operational state. “The model failed” and “the backend is not running” are very different failures, and the UI should help separate them.

## Frontend Trace Viewer

Trace IDs in assistant messages are now actionable from the UI.

Flow:

1. Python `/run` returns `trace_id`.
2. The assistant message includes `Trace: trace_...`.
3. The message bubble extracts that trace id.
4. Clicking `View trace` calls:
   - `GET /traces/{trace_id}`
   - `GET /traces/{trace_id}/tools`
   - `GET /traces/{trace_id}/feedback`
5. The frontend opens a trace panel with run metadata, prompt, final text, steps, tool calls, and feedback.

Interview lesson: observability becomes much more valuable when it is reachable from the product surface. A trace id buried in logs helps engineers; a trace id linked from the assistant response helps debugging, demo review, and feedback triage.

## Hosted Demo Plan

Hosted demo work is required, not optional.

Added:

- `npm run deploy`
- `npm run deploy:cloudflare`
- `.env.production.example`
- `docs/DEPLOYMENT.md`
- `src/diagram_agent/modal_app.py`
- `modal` dependency
- README link to deployment guide

Deployment split:

- Cloudflare hosts the React/Excalidraw app and existing TypeScript Worker agent.
- Modal or another ASGI host runs the Python FastAPI backend.
- The frontend points to Python through `VITE_PYTHON_AGENT_URL`.

Secrets documented:

- Cloudflare Worker: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`
- Python backend: `OPENAI_API_KEY`, `BRAINTRUST_API_KEY`

Interview lesson: hosted demos need a clean operational story. The frontend and backend can be deployed separately as long as the boundary is explicit, the health check is visible, and environment variables are documented.

## Modal Backend Target

Added a small Modal wrapper for the Python backend:

```text
python_agent/src/diagram_agent/modal_app.py
```

It imports and serves the existing FastAPI app from:

```text
diagram_agent.api:app
```

Design choice: Modal is only the hosting shell. It should not fork the API implementation. Local `uvicorn`, tests, and hosted Modal all use the same FastAPI routes.

Deploy command:

```bash
cd python_agent
uv run modal deploy src/diagram_agent/modal_app.py
```

Verification:

```bash
uv run python -m pytest
uv run ruff check src
```

Latest result: `73 passed`; ruff passed.
