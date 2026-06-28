from fastapi.testclient import TestClient

import diagram_agent.api as api_module
from diagram_agent.api import app


def test_health() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_local_backend_returns_canvas() -> None:
    client = TestClient(app)

    response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["final_text"] == "Created a basic flow with 3 nodes."
    assert body["tool_calls"][0]["name"] == "addElements"
    assert body["canvas_elements"][0]["text"] == "User"
    assert body["trace_id"].startswith("trace_")


def test_plan_local_backend_returns_structured_plan() -> None:
    client = TestClient(app)

    response = client.post(
        "/plan",
        json={
            "prompt": "Draw a JWT auth flow",
            "planner_backend": "local",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["prompt"] == "Draw a JWT auth flow"
    assert body["plan"]["intent"] == "Create a diagram for Draw a JWT auth flow"
    assert body["plan"]["steps"]
    assert body["plan"]["tools_likely_needed"] == ["add_elements"]
    assert body["plan"]["risks"]


def test_run_accepts_approved_plan() -> None:
    client = TestClient(app)
    approved_plan = {
        "intent": "User approved JWT auth flow",
        "steps": ["Add client", "Add auth server", "Connect token flow"],
        "tools_likely_needed": ["addElements"],
        "risks": ["May omit refresh token branch"],
    }

    response = client.post(
        "/run",
        json={
            "prompt": "Draw a JWT auth flow",
            "backend": "local",
            "planning": "required",
            "approved_plan": approved_plan,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plan"] == approved_plan
    assert "created_plan" in body["steps"]
    assert body["trace_id"].startswith("trace_")
    assert body["canvas_elements"]


def test_feedback_endpoint_records_rating() -> None:
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )
    trace_id = run_response.json()["trace_id"]

    feedback_response = client.post(
        "/feedback",
        json={
            "trace_id": trace_id,
            "rating": "down",
            "note": "UI thumbs down",
        },
    )

    body = feedback_response.json()
    assert feedback_response.status_code == 200
    assert body == {"status": "ok"}


def test_traces_endpoint_lists_saved_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)
    client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )

    response = client.get("/traces")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["input"] == "Draw a flow"
    assert body[0]["tool_call_count"] == 1


def test_trace_detail_endpoint_returns_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )
    trace_id = run_response.json()["trace_id"]

    response = client.get(f"/traces/{trace_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["trace_id"] == trace_id
    assert body["input"] == "Draw a flow"


def test_trace_detail_endpoint_returns_404_for_missing_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)

    response = client.get("/traces/trace_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trace not found"


def test_trace_tools_endpoint_returns_tool_events(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )
    trace_id = run_response.json()["trace_id"]

    response = client.get(f"/traces/{trace_id}/tools")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["tool_name"] == "addElements"


def test_trace_feedback_endpoint_returns_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )
    trace_id = run_response.json()["trace_id"]
    client.post(
        "/feedback",
        json={
            "trace_id": trace_id,
            "rating": "down",
            "note": "Boxes overlapped",
        },
    )

    response = client.get(f"/traces/{trace_id}/feedback")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["rating"] == "down"
    assert body[0]["note"] == "Boxes overlapped"


def test_candidates_endpoint_lists_eval_candidates(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_TRACE_DB", tmp_path / "traces.sqlite")
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "Draw a flow",
            "backend": "local",
        },
    )
    trace_id = run_response.json()["trace_id"]
    client.post(
        "/feedback",
        json={
            "trace_id": trace_id,
            "rating": "down",
            "note": "Bad layout",
        },
    )

    response = client.get("/candidates")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["trace_id"] == trace_id
    assert body[0]["status"] == "new"
