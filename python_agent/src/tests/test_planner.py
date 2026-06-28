from diagram_agent.planner import Plan, create_plan


def test_create_plan_returns_structured_plan() -> None:
    plan = create_plan("Draw a JWT auth flow")

    assert isinstance(plan, Plan)
    assert "JWT auth flow" in plan.intent
    assert plan.steps
    assert "add_elements" in plan.tools_likely_needed
    assert plan.risks