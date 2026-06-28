SYSTEM_PROMPT = """You are a diagramming agent for an Excalidraw-style canvas.

Use the provided tools to inspect and mutate the canvas.

Hard rules:
- Use label.text for shape labels.
- Use start.id and end.id for arrows.
- Prefer addElements for new diagrams.
- Query the canvas before modifying an existing diagram.
- Keep element ids stable and meaningful.
- Avoid overlapping shapes.
- Return a concise final summary after tool calls are complete.
"""


def select_flow_labels(prompt: str) -> list[str]:
    prompt_lower = prompt.lower()

    if "hello" in prompt_lower:
        return ["Hello"]

    if all(word in prompt_lower for word in ["start", "process", "end"]):
        return ["Start", "Process", "End"]

    if "jwt" in prompt_lower or "auth" in prompt_lower:
        return ["User", "Login API", "JWT Service", "Database"]
    
    if all(word in prompt_lower for word in ["data", "mode", "entities", "columns"]):
        return ["data", "model", "data-model", "entities"]
    
    if all(word in prompt_lower for word in ["top", "middle", "bottom"]):
        return ["Top", "Middle", "Bottom"]

    return ["User", "API", "Database"]