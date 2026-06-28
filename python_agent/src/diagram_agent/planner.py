from pydantic import BaseModel, Field
from typing import Literal

PlanningMode = Literal["off", "required", "auto"]
PlannerBackend = Literal["local", "openai"]

class Plan(BaseModel):
    intent: str
    steps: list[str] = Field(default_factory=list)
    tools_likely_needed: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)

def should_plan(prompt: str, mode: PlanningMode, has_seed_canvas: bool = False) -> bool:
    if mode == "off":
        return False
    
    if mode =="required":
        return True
    
    prompt_lower = prompt.lower()
    complex_markers = ["modify", "update", "fix", "improve", "jwt", "auth", "oauth"]
    return has_seed_canvas or len(prompt.split()) >= 10 or any(marker in prompt_lower for marker in complex_markers)

def create_plan(prompt: str) -> Plan:
    return Plan(
        intent=f"Create a diagram for {prompt}",
        steps = [
            "identify the main entities in the requested diagram.",
            "place entities left to right in flow order",
            "Connect related entities with arrows."
        ],
        tools_likely_needed=["add_elements"],
        risks=["May miss domain-specific entities until model planning is implemented."],
    )
