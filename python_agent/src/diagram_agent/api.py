from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from diagram_agent.agent import AgentRunResult, run_agent
from diagram_agent.tracing import TraceStore

import os

from diagram_agent.openai_client import OpenAIPlannerClient, OpenAIResponsesModelClient
from diagram_agent.planner import Plan, PlanningMode, create_plan

load_dotenv()
load_dotenv("../.dev.vars")
load_dotenv("../.dev.var")

DEFAULT_TRACE_DB = Path(".data/traces.sqlite")

app = FastAPI(title="Diagram Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    prompt: str
    planner_backend: Literal["local", "openai"] = "openai"

class PlanResponse(BaseModel):
    prompt: str
    plan: Plan


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: Literal["up", "down"]
    note: str = ""


class RunRequest(BaseModel):
    prompt: str
    planning: PlanningMode = "off"
    backend: Literal["local", "openai"] = "openai"
    planner_backend: Literal["local", "openai"] = "local"
    approved_plan: Plan | None = None
    max_steps: int = 5

def create_planner(planner_backend: Literal["local", "openai"]):
    if planner_backend == "local":
        return None

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required for OpenAI planning")

    return OpenAIPlannerClient()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest) -> AgentRunResult:
    model_client = OpenAIResponsesModelClient() if request.backend == "openai" else None

    plan_client = None
    if request.approved_plan is None and request.planning != "off":
        plan_client = create_planner(request.planner_backend)

    result = run_agent(
        request.prompt,
        planning=request.planning,
        model_client=model_client,
        plan_client=plan_client,
        approved_plan=request.approved_plan,
        max_steps=request.max_steps,
    )
    TraceStore(DEFAULT_TRACE_DB).save_run(result)
    return result


@app.post("/plan")
def plan(request: PlanRequest) -> PlanResponse:
    planner = create_planner(request.planner_backend)
    result = planner.create_plan(request.prompt) if planner else create_plan(request.prompt)

    return PlanResponse(prompt=request.prompt, plan=result)


@app.post("/feedback")
def feedback(request: FeedbackRequest) -> dict[str, str]:
    note = request.note or f"UI thumbs {request.rating}"
    TraceStore(DEFAULT_TRACE_DB).add_feedback(
        trace_id=request.trace_id,
        rating=request.rating,
        note=note,
    )
    return {"status": "ok"}


# lets the UI or demo list recent agent runs.
@app.get("/traces")
def traces() -> list[dict]:
    return TraceStore(DEFAULT_TRACE_DB).list_traces()

# lets you inspect one full run.
@app.get("/traces/{trace_id}")
def trace_detail(trace_id: str) -> dict:
    trace = TraceStore(DEFAULT_TRACE_DB).get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace

# Shows what tools the agent called.
@app.get("/traces/{trace_id}/tools")
def trace_tools(trace_id: str) -> list[dict]:
    return TraceStore(DEFAULT_TRACE_DB).get_tool_events(trace_id)


#joins user feedback to the trace.
@app.get("/traces/{trace_id}/feedback")
def trace_feedback(trace_id: str) -> list[dict]:
    return TraceStore(DEFAULT_TRACE_DB).get_feedback(trace_id)

@app.get("/candidates")
def candidates() -> list[dict]:
    return TraceStore(DEFAULT_TRACE_DB).list_eval_candidates()