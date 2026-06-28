from diagram_agent.prompts import select_flow_labels


def test_select_flow_labels_defaults_to_basic_flow() -> None:
    assert select_flow_labels("Draw a flow") == ["User", "API", "Database"]


def test_select_flow_labels_detects_jwt_auth_flow() -> None:
    assert select_flow_labels("Draw a JWT auth flow") == [
        "User",
        "Login API",
        "JWT Service",
        "Database",
    ]