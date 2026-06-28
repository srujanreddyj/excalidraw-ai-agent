from pydantic import BaseModel, Field
from diagram_agent.canvas import CanvasState
# from diagram_agent.tools import add_elements
# from diagram_agent.tools import execute_tool_call
from diagram_agent.planner import Plan, create_plan, PlanningMode, should_plan
from diagram_agent.prompts import SYSTEM_PROMPT, select_flow_labels
import json
from typing import Any, Protocol
from collections.abc import Callable
from time import perf_counter
from uuid import uuid4

from diagram_agent.tools import execute_tool_call, openai_tool_definitions

class ModelClient(Protocol):
    def create_response(self, message: list[dict], tools: list[dict]) -> dict[str, Any]: ...


class PlannerClient(Protocol):
    def create_plan(self, prompt: str) -> Plan: ...


class AgentRunResult(BaseModel):
    prompt: str
    final_text: str
    steps: list[str] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    canvas_elements: list[dict] = Field(default_factory=list)
    plan: dict | None = None
    errors: list[str] = Field(default_factory=list)
    step_count: int = 0
    latency_ms: float = 0.0
    trace_id: str


def _build_flow_payload(labels: list[str]) -> dict:
    elements: list[dict] = []

    for index, label in enumerate(labels):
        node_id = label.lower().replace(" ", "_")
        node_type = "ellipse" if "database" in label.lower() else "rectangle"
        elements.append(
            {
                "id": node_id,
                "type": node_type,
                "x": index * 220,
                "y": 0,
                "label": {"text": label}
            }
        )
    
    for index in range(len(labels) - 1):
        start_label = labels[index]
        end_label = labels[index + 1]
        start_id = start_label.lower().replace(" ", "_")
        end_id = end_label.lower().replace(" ", "_")
        elements.append(
            {
                "id": f"{start_id}_to_{end_id}",
                "type": "arrow",
                "x": index * 220 + 120,
                "y": 30,
                "width": 100,
                "height": 0,
                "start": {"id": start_id},
                "end": {"id": end_id},
            }
        )

    return {"elements": elements}


def run_agent(
        prompt: str, 
        planning: PlanningMode = "off",
        model_client: ModelClient | None = None,
        plan_client: PlannerClient | None = None,
        approved_plan: Plan | None = None,
        max_steps: int = 5,
        clock: Callable[[], float] = perf_counter,
        trace_id_factory: Callable[[], str] = lambda: f"trace_{uuid4().hex}",
    ) -> AgentRunResult:

    started_at = clock()
    trace_id = trace_id_factory()
    canvas = CanvasState()

    # add_payload = {
    #     "elements": [
    #         {"id": "user", "type": "rectangle", "x": 0, "y": 0, "text": "User"},
    #         {"id": "api", "type": "rectangle", "x": 220, "y": 0, "text": "API"},
    #         {"id": "database", "type": "ellipse", "x": 440, "y": 0, "text": "Database"},
    #         {"id": "user_to_api", "type": "arrow", "x": 120, "y": 30, "width": 100, "height": 0, "start_id": "user", "end_id": "api"},
    #         {"id": "api_to_database", "type": "arrow", "x": 340, "y": 30, "width": 100, "height": 0, "start_id": "api", "end_id": "database"},
    #     ]
    # }
    labels = select_flow_labels(prompt)
    add_payload = _build_flow_payload(labels)
    plan = approved_plan
    if plan is None and should_plan(prompt, planning):
        plan = plan_client.create_plan(prompt) if plan_client else create_plan(prompt)

    if model_client is not None:
        errors: list[str] = []
        # messages = [{"role": "user", "content": prompt}]
        # messages = [
        #     {"role": "system", "content": SYSTEM_PROMPT},
        #     {"role": "user", "content": prompt},
        # ]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if plan:
            messages.append(
                {
                    "role": "system",
                    "content": f"Plan before acting:\n{json.dumps(plan.model_dump(), indent=2)}",
                }
            )

        messages.append({"role": "user", "content": prompt})

        tools = openai_tool_definitions()
        tool_calls: list[dict] = []
        steps = [
            "received_prompt",
            *(["created_plan"] if plan else ()),
            "created_canvas_state",
        ]

        for _ in range(max_steps): 
            steps.append("called_model")
            response = model_client.create_response(messages, tools)
            response_tool_calls = response.get("tool_calls", [])
            
            if not response_tool_calls:
                steps.append("completed_model_response")
                latency_ms = (clock() - started_at) * 1000
                return AgentRunResult(
                    prompt=prompt,
                    plan=plan.model_dump() if plan else None,
                    final_text=response.get("final_text") or "",
                    steps=steps,
                    tool_calls=tool_calls,
                    canvas_elements=canvas.to_elements(),
                    errors=errors,
                    step_count=len(steps),
                    latency_ms=latency_ms,
                    trace_id=trace_id
                )
        
            for tool_call in response_tool_calls: 
                name = tool_call["name"]
                arguments_json = tool_call.get("arguments") or "{}"
                try:
                    tool_input = json.loads(arguments_json)
                except json.JSONDecodeError:
                    tool_input = {}

                tool_output = execute_tool_call(canvas, name, arguments_json)
                if "error" in tool_output:
                    errors.append(tool_output["error"])

                tool_calls.append(
                    {
                        "id": tool_call.get("id"),
                        "name": name,
                        "input": tool_input,
                        "output": tool_output,
                    }
                )
                steps.append(f"called_{name}")
                # messages.append(
                #     {
                #         "role": "tool",
                #         "tool_call_id": tool_call.get("id"),
                #         "name": name,
                #         "content": json.dumps(tool_output),
                #     }
                # )
                messages.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.get("id"),
                        "name": name,
                        "arguments": arguments_json,
                    }
                )

                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.get("id"),
                        "output": json.dumps(tool_output),
                    }
                )
        latency_ms = (clock() - started_at) * 1000
        return AgentRunResult(
            prompt=prompt,
            plan=plan.model_dump() if plan else None,
            final_text="Stopped after reaching max_steps.",
            steps=steps,
            tool_calls=tool_calls,
            canvas_elements=canvas.to_elements(),
            errors=errors,
            step_count=len(steps),
            latency_ms=latency_ms,
            trace_id=trace_id
        )


    # tool_result = add_elements(canvas, add_payload)
    tool_result = execute_tool_call(
        canvas,
        "addElements",
        json.dumps(add_payload),
    )
    # latency_ms = (clock() - started_at) * 1000
    steps = [
        "received_prompt",
        *(["created_plan"] if plan else ()),
        "created_canvas_state",
        "called_add_elements",
    ]
    latency_ms = (clock() - started_at) * 1000

    return AgentRunResult(
        prompt=prompt,
        plan=plan.model_dump() if plan else None,
        final_text=f"Created a basic flow with {len(labels)} nodes.",
        steps=steps,
        tool_calls = [
            {
                "name": "addElements",
                "input": add_payload,
                "output": tool_result,
            }
        ],
        canvas_elements=canvas.to_elements(),
        step_count=len(steps),
        latency_ms=latency_ms,
        trace_id=trace_id
    )

