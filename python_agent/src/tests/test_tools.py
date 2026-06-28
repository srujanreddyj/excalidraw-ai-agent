import json

import pytest
from pydantic import ValidationError

from diagram_agent.canvas import CanvasState
from diagram_agent.tools import (
    add_elements,
    execute_tool_call,
    openai_tool_definitions,
    query_canvas,
    remove_elements,
    update_elements,
)


def test_add_elements_tool_mutates_canvas() -> None:
    canvas = CanvasState()

    result = add_elements(
        canvas,
        {
            "elements": [
                {"id": "user", "type": "rectangle", "text": "User"},
                {"id": "api", "type": "rectangle", "x": 200, "text": "API"},
            ]
        },
    )

    assert result["added"][0]["id"] == "user"
    assert len(result["canvas"]) == 2
    
    summary = query_canvas(canvas)
    assert summary["count"] == 2
    assert summary["overlaps"] == []
    assert "user: rectangle 'User'" in summary["compact"]


def test_update_elements_tool_mutates_canvas() -> None:
    canvas = CanvasState()
    add_elements(canvas, {"elements": [{"id": "api", "type": "rectangle", "text": "API"}]})

    result = update_elements(
        canvas,
        {"updates": [{"id": "api", "text": "Auth API", "x": 240}]},
    )

    assert result["updated"][0]["text"] == "Auth API"
    assert result["canvas"][0]["x"] == 240


def test_remove_elements_tool_mutates_canvas() -> None:
    canvas = CanvasState()
    add_elements(canvas, {"elements": [{"id": "user", "type": "rectangle", "text": "User"}]})

    result = remove_elements(canvas, {"ids": ["user"]})

    assert result["removed"] == ["user"]
    assert result["canvas"] == []


def test_tool_validation_rejects_bad_payload() -> None:
    canvas = CanvasState()

    with pytest.raises(ValidationError):
        add_elements(canvas, {"elements": [{"id": "bad", "type": "hexagon"}]})


def test_query_canvas_reports_overlaps() -> None:
    canvas = CanvasState()
    add_elements(
        canvas,
        {
            "elements": [
                {"id": "a", "type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100},
                {"id": "b", "type": "rectangle", "x": 50, "y": 50, "width": 100, "height": 100},
            ]
        },
    )

    assert query_canvas(canvas)["overlaps"] == [{"first_id": "a", "second_id": "b"}]


def test_add_elements_tool_normalizes_label_and_bindings() -> None:
    canvas = CanvasState()

    add_elements(
        canvas,
        {
            "elements": [
                {
                    "id": "rect_user",
                    "type": "rectangle",
                    "label": {"text": "User"},
                },
                {
                    "id": "rect_api",
                    "type": "rectangle",
                    "x": 320,
                    "label": {"text": "API"},
                },
                {
                    "id": "arrow_user_api",
                    "type": "arrow",
                    "start": {"id": "rect_user"},
                    "end": {"id": "rect_api"},
                },
            ]
        },
    )

    assert canvas.elements["rect_user"].text == "User"
    assert canvas.elements["arrow_user_api"].start_id == "rect_user"
    assert canvas.elements["arrow_user_api"].end_id == "rect_api"


def test_execute_tool_call_routes_add_elements() -> None:
    canvas = CanvasState()

    result = execute_tool_call(
        canvas,
        "addElements",
        json.dumps(
            {
                "elements": [
                    {
                        "id": "user",
                        "type": "rectangle",
                        "label": {"text": "User"},
                    }
                ]
            }
        ),
    )

    assert result["added"][0]["id"] == "user"
    assert canvas.elements["user"].text == "User"


def test_execute_tool_call_handles_unknown_tool() -> None:
    canvas = CanvasState()

    result = execute_tool_call(canvas, "missingTool", "{}")

    assert result == {"error": "Unknown tool: missingTool"}


def test_execute_tool_call_handles_invalid_json() -> None:
    canvas = CanvasState()

    result = execute_tool_call(canvas, "addElements", "{bad json")

    assert result["error"].startswith("Invalid JSON arguments")


def test_openai_tool_definitions_expose_expected_tool_names() -> None:
    tools = openai_tool_definitions()

    names = [tool["name"] for tool in tools]

    assert names == ["queryCanvas", "addElements", "updateElements", "removeElements"]


def test_openai_tool_definitions_include_add_elements_schema() -> None:
    tools = openai_tool_definitions()
    add_elements_tool = next(tool for tool in tools if tool["name"] == "addElements")

    assert add_elements_tool["parameters"]["type"] == "object"
    assert "elements" in add_elements_tool["parameters"]["properties"]
    assert add_elements_tool["parameters"]["properties"]["elements"]["type"] == "array"
