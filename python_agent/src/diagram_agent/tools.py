# from tkinter import Canvas
import json
from collections.abc import Callable
from typing import Any
from diagram_agent.canvas import CanvasElement, CanvasElementUpdate, CanvasState
from diagram_agent.schemas import AddElementsInput, RemoveElementsInput, UpdateElementsInput

def query_canvas(canvas: CanvasState) -> dict[str, Any]:
    return {
        "elements": canvas.to_elements(),
        "count": len(canvas.elements),
        "overlaps": canvas.find_overlaps(),
        "compact": canvas.to_compact_text(),
    }

def add_elements(canvas: CanvasState, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = AddElementsInput.model_validate(payload)
    elements = [
        CanvasElement(
            id=element.id,
            type=element.type,
            x=element.x,
            y=element.y,
            width=element.width,
            height=element.height,
            text=element.text or (element.label.text if element.label else None),
            start_id=element.start.id if element.start else None,
            end_id=element.end.id if element.end else None,
        )
        for element in parsed.elements
    ]

    added = canvas.add_elements(elements)

    return {
        "added": [element.model_dump() for element in added],
        "canvas": canvas.to_elements(),
    }

def update_elements(canvas: CanvasState, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = UpdateElementsInput.model_validate(payload)
    updates = [
        CanvasElementUpdate(
            id=update.id,
            type=update.type,
            x=update.x,
            y=update.y,
            width=update.width,
            height=update.height,
            text=update.text or (update.label.text if update.label else None),
            start_id=update.start.id if update.start else None,
            end_id=update.end.id if update.end else None,
        )
        for update in parsed.updates
    ]

    updated = canvas.update_elements(updates)

    return {
        "updated": [element.model_dump() for element in updated],
        "canvas": canvas.to_elements(),
    }

def remove_elements(canvas: CanvasState, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = RemoveElementsInput.model_validate(payload)
    removed = canvas.remove_elements(parsed.ids)

    return {
        "removed": removed,
        "canvas": canvas.to_elements(),
    }


ToolFn = Callable[[CanvasState, dict[str, Any]], dict[str, Any]]

def _query_canvas_tool(canvas: CanvasState, payload: dict[str, Any]) -> dict[str, Any]:
    return query_canvas(canvas)


TOOL_REGISTRY: dict[str, ToolFn] = {
    "queryCanvas": _query_canvas_tool,
    "addElements": add_elements,
    "updateElements": update_elements,
    "removeElements": remove_elements,
}

def execute_tool_call(
    canvas: CanvasState,
    name: str,
    arguments_json: str,
) -> dict[str, Any]:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        return {"error": f"Unknown tool: {name}"}

    try:
        payload = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid JSON arguments: {exc.msg}"}

    return tool(canvas, payload)

def openai_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "queryCanvas",
            "description": "Inspect the current simulated canvas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "addElements",
            "description": "Add shapes, arrows, and text elements to the canvas.",
            "parameters": AddElementsInput.model_json_schema(),
        },
        {
            "type": "function",
            "name": "updateElements",
            "description": "Update existing canvas elements by id.",
            "parameters": UpdateElementsInput.model_json_schema(),
        },
        {
            "type": "function",
            "name": "removeElements",
            "description": "Remove canvas elements by id.",
            "parameters": RemoveElementsInput.model_json_schema(),
        },
    ]