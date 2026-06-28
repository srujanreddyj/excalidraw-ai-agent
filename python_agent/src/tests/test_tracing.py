from diagram_agent.agent import run_agent
from diagram_agent.tracing import TraceStore


def test_trace_store_saves_and_fetches_trace(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_test_123",
    )

    store.save_run(result)
    trace = store.get_trace("trace_test_123")

    assert trace is not None
    assert trace["trace_id"] == "trace_test_123"
    assert trace["input"] == "Draw a flow"
    assert trace["final_text"] == "Created a basic flow with 3 nodes."
    assert trace["status"] == "ok"
    assert trace["step_count"] == 3
    assert trace["tool_call_count"] == 1


def test_trace_store_marks_error_status(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_error_123",
    )
    result.errors.append("Something failed")

    store.save_run(result)
    trace = store.get_trace("trace_error_123")

    assert trace is not None
    assert trace["status"] == "error"


def test_trace_store_saves_tool_events(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_tools_123",
    )

    store.save_run(result)
    tool_events = store.get_tool_events("trace_tools_123")

    assert len(tool_events) == 1
    assert tool_events[0]["trace_id"] == "trace_tools_123"
    assert tool_events[0]["call_index"] == 0
    assert tool_events[0]["tool_name"] == "addElements"
    assert '"elements"' in tool_events[0]["input_json"]
    assert '"added"' in tool_events[0]["output_json"]


def test_trace_store_adds_feedback_and_downvote_candidate(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_feedback_123",
    )
    store.save_run(result)

    store.add_feedback(
        trace_id="trace_feedback_123",
        rating="down",
        note="Boxes overlapped",
    )

    feedback = store.get_feedback("trace_feedback_123")
    candidates = store.list_eval_candidates()

    assert len(feedback) == 1
    assert feedback[0]["rating"] == "down"
    assert feedback[0]["note"] == "Boxes overlapped"
    assert len(candidates) == 1
    assert candidates[0]["trace_id"] == "trace_feedback_123"
    assert candidates[0]["status"] == "new"


def test_trace_store_upvote_does_not_create_candidate_by_default(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_feedback_up_123",
    )
    store.save_run(result)

    store.add_feedback(
        trace_id="trace_feedback_up_123",
        rating="up",
        note="Looks good",
    )

    assert len(store.get_feedback("trace_feedback_up_123")) == 1
    assert store.list_eval_candidates() == []


def test_trace_store_updates_eval_candidate_status(tmp_path) -> None:
    db_path = tmp_path / "traces.sqlite"
    store = TraceStore(db_path)
    result = run_agent(
        "Draw a flow",
        trace_id_factory=lambda: "trace_candidate_status_123",
    )
    store.save_run(result)
    store.add_feedback(
        trace_id="trace_candidate_status_123",
        rating="down",
        note="Needs regression",
    )

    store.update_eval_candidate_status("trace_candidate_status_123", "ignored")
    candidate = store.get_eval_candidate("trace_candidate_status_123")

    assert candidate is not None
    assert candidate["status"] == "ignored"
