# Excalidraw AI Agent

An AI-powered diagramming app that lets users generate, inspect, and modify Excalidraw diagrams through a chat-based agent.

The repo has two agent paths:

- `Cloudflare`: the original TypeScript/Cloudflare Worker agent.
- `Python`: a Python-first AI engineering backend with planning, tool-calling, tracing, feedback capture, evals, Braintrust export, and a data flywheel.

## Architecture

```text
React + Excalidraw frontend
        |
        | Cloudflare mode
        v
Cloudflare Worker / Durable Object agent

React + Excalidraw frontend
        |
        | Python mode
        v
FastAPI Python agent
        |
        v
OpenAI tool loop + Canvas simulator + SQLite traces + eval flywheel
```

The frontend stays React + Excalidraw. The Python backend implements the AI engineering layer.

## Stack

- React
- Excalidraw
- Cloudflare Workers
- AI SDK
- FastAPI
- OpenAI Python SDK
- SQLite tracing
- Typer CLI
- pytest + ruff
- Braintrust export
- Modal deployment target

## Local Setup

Install frontend dependencies:

```bash
npm install
```

Install/sync Python dependencies:

```bash
cd python_agent
uv sync
cd ..
```

Create frontend env config:

```bash
cp .env.example .env
```

For local development, `.env` should contain:

```bash
VITE_PYTHON_AGENT_URL=http://127.0.0.1:8000
```

Create local secrets for the Worker and Python backend:

```bash
cp .dev.vars.example .dev.vars
```

At minimum, fill in:

```bash
OPENAI_API_KEY=...
BRAINTRUST_API_KEY=...
```

`BRAINTRUST_API_KEY` is only needed for Braintrust export. `TAVILY_API_KEY` and Upstash values are only needed for web/knowledge search features.

## Start The App With Python Agent Backend

You need two terminals: one for the Python API and one for the React app.

### Terminal 1: Start Python API

```bash
cd /Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/python_agent
uv run uvicorn diagram_agent.api:app --host 127.0.0.1 --port 8000 --reload
```

Verify the API:

```bash
open http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Terminal 2: Start React/Vite

```bash
cd /Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent
npm run dev -- --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173
```

In the chat header, click:

```text
Python
```

The UI should show:

```text
Python backend online
```

Now send a prompt, review the plan, click `Execute`, then use `View trace` on the assistant response.

## Python CLI

Run the local deterministic agent:

```bash
cd python_agent
uv run diagram-agent run "Draw a flow from User to API to Database"
```

Run OpenAI tool-calling with planning:

```bash
uv run diagram-agent run "Draw a JWT auth flow" \
  --backend openai \
  --planning required \
  --planner-backend openai
```

Run evals:

```bash
uv run diagram-agent eval \
  --dataset ../evals/datasets/golden_2.json
```

Run evals with generated regressions:

```bash
uv run diagram-agent eval \
  --dataset ../evals/datasets/golden_2.json \
  --dataset ../evals/datasets/generated_regressions.json
```

Inspect traces:

```bash
uv run diagram-agent traces list
uv run diagram-agent traces show TRACE_ID
uv run diagram-agent traces tools TRACE_ID
```

Capture feedback and promote a regression:

```bash
uv run diagram-agent feedback add TRACE_ID --rating down --note "Boxes overlapped"
uv run diagram-agent candidates list
uv run diagram-agent candidates promote TRACE_ID --set regression
```

Export an eval report to Braintrust:

```bash
uv run diagram-agent braintrust export \
  --report runs/YOUR_EVAL_REPORT.json \
  --project "Diagram Agent" \
  --experiment "local-eval"
```

## FastAPI Endpoints

The Python backend exposes:

```text
GET  /health
POST /plan
POST /run
POST /feedback
GET  /traces
GET  /traces/{trace_id}
GET  /traces/{trace_id}/tools
GET  /traces/{trace_id}/feedback
GET  /candidates
```

These support the frontend planning UI, trace viewer, feedback capture, and eval flywheel.

## Checks

Frontend:

```bash
npm run build
npm run preview
npm run embed
npm run eval
```

Python:

```bash
cd python_agent
uv run python -m pytest
uv run ruff check src
```

## Hosted Demo

Deployment instructions live in [docs/DEPLOYMENT.md](/Users/srujanjabbireddy/personal_projects/excalidraw-ai-agent/docs/DEPLOYMENT.md).

The hosted demo uses:

- Cloudflare Workers for the React/Excalidraw frontend and TypeScript agent path.
- Modal or another ASGI host for the Python FastAPI backend.
- `VITE_PYTHON_AGENT_URL` to point the frontend at the hosted Python backend.

For production builds:

```bash
cp .env.production.example .env.production
```

Deploy frontend:

```bash
npm run deploy
```

Deploy Python backend target:

```bash
cd python_agent
uv run modal deploy src/diagram_agent/modal_app.py
```

## Resume Claim This Supports

Built a Python-first AI agent engineering system for a React/Excalidraw diagramming app, including tool-calling, planning-before-action, structured tracing, feedback capture, eval automation, Braintrust export, and a data flywheel that promotes real user interactions into regression test cases.
