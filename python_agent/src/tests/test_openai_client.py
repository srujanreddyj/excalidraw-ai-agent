from types import SimpleNamespace

from diagram_agent.openai_client import OpenAIPlannerClient, OpenAIResponsesModelClient


class FakeResponsesResource:
    def __init__(self, response: SimpleNamespace) -> None:
        self.response = response
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return self.response


class FakeOpenAIClient:
    def __init__(self, response: SimpleNamespace) -> None:
        self.responses = FakeResponsesResource(response)


def test_openai_responses_client_sends_model_input_and_tools() -> None:
    response = SimpleNamespace(output=[], output_text="Done")
    raw_client = FakeOpenAIClient(response)
    model_client = OpenAIResponsesModelClient(raw_client, model="gpt-5-mini")

    result = model_client.create_response(
        messages=[{"role": "user", "content": "Draw a box"}],
        tools=[{"type": "function", "name": "queryCanvas", "parameters": {"type": "object"}}],
    )

    call = raw_client.responses.calls[0]
    assert call["model"] == "gpt-5-mini"
    assert call["input"] == [{"role": "user", "content": "Draw a box"}]
    assert call["tools"][0]["name"] == "queryCanvas"
    assert result == {"final_text": "Done", "tool_calls": []}


def test_openai_responses_client_normalizes_function_calls() -> None:
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="function_call",
                call_id="call_123",
                name="addElements",
                arguments='{"elements":[]}',
            )
        ],
        output_text="",
    )
    raw_client = FakeOpenAIClient(response)
    model_client = OpenAIResponsesModelClient(raw_client)

    result = model_client.create_response(messages=[], tools=[])

    assert result == {
        "final_text": "",
        "tool_calls": [
            {
                "id": "call_123",
                "name": "addElements",
                "arguments": '{"elements":[]}',
            }
        ],
    }


def test_openai_planner_client_returns_structured_plan() -> None:
    response = SimpleNamespace(
        output=[],
        output_text=(
            '{"intent":"Draw auth flow",'
            '"steps":["Identify actors","Place nodes"],'
            '"tools_likely_needed":["addElements"],'
            '"risks":["May miss token refresh"]}'
        ),
    )
    raw_client = FakeOpenAIClient(response)
    planner = OpenAIPlannerClient(raw_client, model="gpt-5-mini")

    plan = planner.create_plan("Draw a JWT auth flow")

    call = raw_client.responses.calls[0]
    assert call["model"] == "gpt-5-mini"
    assert call["input"][0]["role"] == "system"
    assert "Do not call tools" in call["input"][0]["content"]
    assert plan.intent == "Draw auth flow"
    assert plan.tools_likely_needed == ["addElements"]
