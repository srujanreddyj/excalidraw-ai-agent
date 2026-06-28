import json
from typing import Any

from openai import OpenAI

from diagram_agent.planner import Plan


class OpenAIResponsesModelClient:
    def __init__(
        self,
        raw_client: OpenAI | None = None,
        model: str = "gpt-5-mini",
    ) -> None:
        self.raw_client = raw_client or OpenAI()
        self.model = model

    def create_response(self, messages: list[dict], tools: list[dict]) -> dict[str, Any]:
        response = self.raw_client.responses.create(
            model=self.model,
            input=messages,
            tools=tools,
        )

        tool_calls = []
        for item in getattr(response, "output", []):
            if getattr(item, "type", None) == "function_call":
                tool_calls.append(
                    {
                        "id": getattr(item, "call_id", None),
                        "name": getattr(item, "name"),
                        "arguments": getattr(item, "arguments", "{}"),
                    }
                )

        return {
            "final_text": getattr(response, "output_text", "") or "",
            "tool_calls": tool_calls,
        }


class OpenAIPlannerClient:
    def __init__(
        self,
        raw_client: OpenAI | None = None,
        model: str = "gpt-5-mini",
    ) -> None:
        self.raw_client = raw_client or OpenAI()
        self.model = model

    def create_plan(self, prompt: str) -> Plan:
        response = self.raw_client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a planning-only diagram agent. Do not call tools. "
                        "Return only valid JSON matching this shape: "
                        '{"intent": string, "steps": string[], '
                        '"tools_likely_needed": string[], "risks": string[]}.'
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        return Plan.model_validate(json.loads(response.output_text))
