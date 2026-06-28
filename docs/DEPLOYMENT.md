# Hosted Demo Deployment

This repo has two deployable surfaces:

1. Cloudflare hosts the React/Excalidraw app and the original TypeScript Worker agent.
2. A Python ASGI host, preferably Modal for the demo, hosts the Python agent API.

The frontend chooses between them with the existing `Cloudflare | Python` toggle.

## Architecture

```text
Browser
  |
  | Cloudflare mode
  v
Cloudflare Worker + Durable Object agent

Browser
  |
  | Python mode
  v
Python FastAPI backend
  |
  v
OpenAI + SQLite traces + eval flywheel
```

## Frontend: Cloudflare Workers

The repo already uses:

- `@cloudflare/vite-plugin`
- `wrangler.toml`
- Durable Objects for `DesignAgent`
- Worker assets configured as a single-page app

### Local Production Config

Copy the production env template:

```bash
cp .env.production.example .env.production
```

Set the deployed Python API URL:

```bash
VITE_PYTHON_AGENT_URL=https://your-python-agent-api.example.com
```

This value is consumed at build time by Vite. If the Python backend URL changes, rebuild and redeploy the frontend.

### Cloudflare Secrets

Configure Worker secrets in Cloudflare with Wrangler:

```bash
npx wrangler secret put OPENAI_API_KEY
npx wrangler secret put TAVILY_API_KEY
npx wrangler secret put UPSTASH_VECTOR_REST_URL
npx wrangler secret put UPSTASH_VECTOR_REST_TOKEN
```

What each secret does:

- `OPENAI_API_KEY`: required by the Cloudflare TypeScript agent.
- `TAVILY_API_KEY`: enables `searchWeb`.
- `UPSTASH_VECTOR_REST_URL`: enables knowledge search.
- `UPSTASH_VECTOR_REST_TOKEN`: enables knowledge search.

Local-only eval and Python secrets still live in `.dev.vars` or the Python host secret store:

- `BRAINTRUST_API_KEY`
- Python backend `OPENAI_API_KEY`

### Deploy

Build and deploy:

```bash
npm run deploy
```

Equivalent explicit form:

```bash
npm run build
npx wrangler deploy
```

After deploy, save the Cloudflare URL in your project notes and test both backend modes.

## Python Backend: Modal Demo Plan

For the hosted demo, Modal is the preferred Python backend target because it can serve FastAPI as an ASGI app without a long-running VM.

### Required Python Secrets

Configure these in Modal:

```text
OPENAI_API_KEY
BRAINTRUST_API_KEY
```

Optional later:

```text
TAVILY_API_KEY
UPSTASH_VECTOR_REST_URL
UPSTASH_VECTOR_REST_TOKEN
```

### Cost Controls

Use these rules for the demo:

- CPU only.
- No GPU.
- No always-on containers.
- Low request timeout.
- Demo traffic only.
- Keep SQLite trace storage local/ephemeral for the first demo, then move to managed storage only if needed.

### Modal Implementation

```text
python_agent/src/diagram_agent/modal_app.py
```

This file wraps the existing FastAPI app with Modal:

```python
import modal

app = modal.App("diagram-agent-api")


@app.function(image=image, secrets=[modal.Secret.from_name("diagram-agent-secrets")])
@modal.asgi_app()
def fastapi_app():
    from diagram_agent.api import app as api

    return api
```

The key design choice is that Modal imports `diagram_agent.api:app`; it does not create a separate hosted API implementation.

### Modal Setup

Install/sync Python dependencies:

```bash
cd python_agent
uv sync
```

Authenticate Modal:

```bash
uv run modal setup
```

Create the secret used by `modal_app.py`:

```bash
uv run modal secret create diagram-agent-secrets \
  OPENAI_API_KEY=your-openai-api-key \
  BRAINTRUST_API_KEY=your-braintrust-api-key
```

If the secret already exists, update it from the Modal dashboard or recreate it intentionally.

Deploy command:

```bash
cd python_agent
uv run modal deploy src/diagram_agent/modal_app.py
```

The deploy output should include a public HTTPS URL. Put that URL in `.env.production` as `VITE_PYTHON_AGENT_URL`, rebuild, then redeploy Cloudflare.

## Demo Checklist

Before recording or interviewing:

1. Open the Cloudflare frontend URL.
2. Verify `Cloudflare` mode can create a diagram.
3. Switch to `Python`.
4. Verify Python backend health says `online`.
5. Send a prompt.
6. Verify plan review appears.
7. Click `Execute`.
8. Verify canvas updates.
9. Click `View trace`.
10. Add thumbs-down feedback.
11. Show the trace and eval candidate flow from the CLI.

Useful commands:

```bash
cd python_agent
uv run diagram-agent traces list
uv run diagram-agent candidates list
uv run diagram-agent eval \
  --dataset ../evals/datasets/golden_2.json \
  --dataset ../evals/datasets/generated_regressions.json
```

## Deployment Definition Of Done

- Cloudflare URL opens publicly.
- Frontend build has production `VITE_PYTHON_AGENT_URL`.
- Cloudflare mode works.
- Python mode reaches the hosted Python API.
- `/health`, `/plan`, `/run`, and `/traces/{trace_id}` work on the Python backend.
- README links to this deployment guide.
- Secrets are documented but not committed.
