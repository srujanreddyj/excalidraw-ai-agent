import json

from diagram_agent.agent import AgentRunResult, run_agent
from diagram_agent.planner import Plan, create_plan, should_plan


class FakeModelClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create_response(self, messages: list[dict], tools: list[dict]) -> dict:
        self.calls.append({"messages": messages, "tools": tools})

        if len(self.calls) == 1:
            return {
                "final_text": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "name": "addElements",
                        "arguments": json.dumps(
                            {
                                "elements": [
                                    {
                                        "id": "decision",
                                        "type": "diamond",
                                        "label": {"text": "Decision"},
                                    }
                                ]
                            }
                        ),
                    }
                ],
            }

        return {
            "final_text": "Created the requested diagram.",
            "tool_calls": [],
        }


class BadJsonModelClient:
    def create_response(self, messages: list[dict], tools: list[dict]) -> dict:
        return {
            "final_text": None,
            "tool_calls": [
                {
                    "id": "call_bad_json",
                    "name": "addElements",
                    "arguments": "{bad json",
                }
            ],
        }


class FakePlannerClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def create_plan(self, prompt: str) -> Plan:
        self.prompts.append(prompt)
        return Plan(
            intent="OpenAI planned JWT auth flow",
            steps=["Identify auth actors", "Add token service", "Connect token path"],
            tools_likely_needed=["queryCanvas", "addElements"],
            risks=["Refresh-token path may be omitted"],
        )


def test_run_agent_returns_skeleton_result() -> None:
    result = run_agent("Draw a flow")

    assert isinstance(result, AgentRunResult)
    assert result.prompt == "Draw a flow"
    assert result.final_text == "Created a basic flow with 3 nodes."
    assert result.steps == ["received_prompt", "created_canvas_state", "called_add_elements"]
    assert result.tool_calls[0]["name"] == "addElements"

    tool_input = result.tool_calls[0]["input"]
    assert tool_input["elements"][0]["label"] == {"text": "User"}
    assert tool_input["elements"][-1]["start"] == {"id": "api"}
    assert tool_input["elements"][-1]["end"] == {"id": "database"}

    assert [element["text"] for element in result.canvas_elements[:3]] == ["User", "API", "Database"]

    arrows = [element for element in result.canvas_elements if element["type"] == "arrow"]
    assert len(arrows) == 2
    assert arrows[0]["start_id"] == "user"
    assert arrows[0]["end_id"] == "api"
    assert arrows[1]["start_id"] == "api"
    assert arrows[1]["end_id"] == "database"


def test_run_agent_records_tool_call_output_from_router() -> None:
    result = run_agent("Draw a flow")

    tool_call = result.tool_calls[0]

    assert tool_call["output"]["added"][0]["id"] == "user"
    assert tool_call["output"]["canvas"] == result.canvas_elements


def test_run_agent_records_basic_run_metadata() -> None:
    clock_values = iter([10.0, 10.25])

    result = run_agent(
        "Draw a flow",
        clock=lambda: next(clock_values),
    )

    assert result.step_count == 3
    assert result.latency_ms == 250.0


def test_run_agent_records_trace_id() -> None:
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_test_123",
    )

    assert result.trace_id == "trace_test_123"


def test_run_agent_can_use_injected_model_client_for_tool_loop() -> None:
    model_client = FakeModelClient()

    result = run_agent(
        "Draw a diamond labeled Decision",
        model_client=model_client,
        max_steps=3,
    )

    assert result.final_text == "Created the requested diagram."
    assert len(model_client.calls) == 2
    assert model_client.calls[0]["tools"][1]["name"] == "addElements"
    assert "created_canvas_state" in result.steps
    assert "completed_model_response" in result.steps
    assert result.tool_calls[0]["name"] == "addElements"
    assert result.tool_calls[0]["id"] == "call_1"
    assert result.tool_calls[0]["output"]["added"][0]["id"] == "decision"
    assert result.canvas_elements[0]["text"] == "Decision"


def test_run_agent_sends_system_prompt_to_model_client() -> None:
    model_client = FakeModelClient()

    run_agent(
        "Draw a diamond labeled Decision",
        model_client=model_client,
        max_steps=1,
    )

    first_model_input = model_client.calls[0]["messages"]
    system_item = first_model_input[0]

    assert system_item["role"] == "system"
    assert "Use label.text for shape labels" in system_item["content"]
    assert "Use start.id and end.id for arrows" in system_item["content"]
    assert first_model_input[1] == {
        "role": "user",
        "content": "Draw a diamond labeled Decision",
    }


def test_run_agent_sends_plan_context_to_model_client() -> None:
    model_client = FakeModelClient()

    result = run_agent(
        "Draw a JWT auth flow",
        planning="required",
        model_client=model_client,
        max_steps=1,
    )

    first_model_input = model_client.calls[0]["messages"]
    plan_item = first_model_input[1]

    assert result.plan is not None
    assert plan_item["role"] == "system"
    assert "Plan before acting" in plan_item["content"]
    assert "JWT auth flow" in plan_item["content"]
    assert first_model_input[2] == {
        "role": "user",
        "content": "Draw a JWT auth flow",
    }


def test_run_agent_uses_injected_planner_client() -> None:
    model_client = FakeModelClient()
    planner_client = FakePlannerClient()

    result = run_agent(
        "Draw a JWT auth flow",
        planning="required",
        model_client=model_client,
        plan_client=planner_client,
        max_steps=1,
    )

    plan_context = model_client.calls[0]["messages"][1]["content"]

    assert planner_client.prompts == ["Draw a JWT auth flow"]
    assert result.plan is not None
    assert result.plan["intent"] == "OpenAI planned JWT auth flow"
    assert "OpenAI planned JWT auth flow" in plan_context
    assert "Refresh-token path may be omitted" in plan_context


def test_run_agent_sends_function_call_output_back_to_model() -> None:
    model_client = FakeModelClient()

    run_agent(
        "Draw a diamond labeled Decision",
        model_client=model_client,
        max_steps=3,
    )

    second_model_input = model_client.calls[1]["messages"]
    function_call_item = second_model_input[-2]
    tool_output_item = second_model_input[-1]

    assert function_call_item == {
        "type": "function_call",
        "call_id": "call_1",
        "name": "addElements",
        "arguments": json.dumps(
            {
                "elements": [
                    {
                        "id": "decision",
                        "type": "diamond",
                        "label": {"text": "Decision"},
                    }
                ]
            }
        ),
    }
    assert tool_output_item["type"] == "function_call_output"
    assert tool_output_item["call_id"] == "call_1"
    assert json.loads(tool_output_item["output"])["added"][0]["id"] == "decision"


def test_run_agent_model_loop_stops_at_max_steps() -> None:
    model_client = FakeModelClient()

    result = run_agent(
        "Draw a diamond labeled Decision",
        model_client=model_client,
        max_steps=1,
    )

    assert result.final_text == "Stopped after reaching max_steps."
    assert len(model_client.calls) == 1
    assert result.canvas_elements[0]["text"] == "Decision"


def test_run_agent_captures_tool_argument_errors() -> None:
    result = run_agent(
        "Draw a broken diagram",
        model_client=BadJsonModelClient(),
        max_steps=1,
    )

    assert result.final_text == "Stopped after reaching max_steps."
    assert result.errors
    assert result.errors[0].startswith("Invalid JSON arguments")
    assert result.tool_calls[0]["id"] == "call_bad_json"
    assert result.tool_calls[0]["output"]["error"].startswith("Invalid JSON arguments")


def test_run_agent_can_include_plan() -> None:
    result = run_agent("Draw a JWT auth flow", planning="required")

    assert result.plan is not None
    assert "JWT auth flow" in result.plan["intent"]
    assert "created_plan" in result.steps

def test_create_plan_returns_structured_plan() -> None:
    plan = create_plan("Draw a JWT auth flow")

    assert isinstance(plan, Plan)
    assert "JWT auth flow" in plan.intent
    assert plan.steps
    assert "add_elements" in plan.tools_likely_needed
    assert plan.risks


def test_should_plan_modes() -> None:
    assert should_plan("Draw a box", "off") is False
    assert should_plan("Draw a box", "required") is True
    assert should_plan("Draw a JWT auth flow", "auto") is True
    assert should_plan("Draw box", "auto") is False


def test_run_agent_creates_jwt_flow_for_auth_prompt() -> None:
    result = run_agent("Draw a JWT auth flow", planning="required")

    node_texts = [
        element["text"]
        for element in result.canvas_elements
        if element["type"] != "arrow"
    ]

    assert node_texts == ["User", "Login API", "JWT Service", "Database"]
