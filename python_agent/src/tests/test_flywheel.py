import json

import pytest

from diagram_agent.agent import run_agent
from diagram_agent.flywheel import promote_candidate
from diagram_agent.tracing import TraceStore


def test_promote_candidate_writes_generated_regression(tmp_path) -> None:
    store = TraceStore(tmp_path / "traces.sqlite")
    result = run_agent(
        "Draw a billing system diagram",
        trace_id_factory=lambda: "trace_promote_123",
    )
    store.save_run(result)
    store.add_feedback(
        trace_id="trace_promote_123",
        rating="down",
        note="Missing payment processor",
    )
    output_path = tmp_path / "generated_regressions.json"

    case = promote_candidate(
        store=store,
        trace_id="trace_promote_123",
        dataset_path=output_path,
    )

    written_cases = json.loads(output_path.read_text())
    candidate = store.get_eval_candidate("trace_promote_123")

    assert case["id"] == "trace-regression-trace_promote_123"
    assert case["input"] == "Draw a billing system diagram"
    assert case["expectedCharacteristics"] == [
        "Human feedback: Missing payment processor"
    ]
    assert written_cases == [case]
    assert candidate is not None
    assert candidate["status"] == "promoted"


def test_promote_candidate_replaces_existing_case_by_id(tmp_path) -> None:
    store = TraceStore(tmp_path / "traces.sqlite")
    result = run_agent(
        "Draw a billing system diagram",
        trace_id_factory=lambda: "trace_promote_123",
    )
    store.save_run(result)
    store.add_feedback(
        trace_id="trace_promote_123",
        rating="down",
        note="First note",
    )
    output_path = tmp_path / "generated_regressions.json"

    promote_candidate(store, "trace_promote_123", output_path)
    store.add_feedback(
        trace_id="trace_promote_123",
        rating="down",
        note="Second note",
    )
    promote_candidate(store, "trace_promote_123", output_path)

    written_cases = json.loads(output_path.read_text())

    assert len(written_cases) == 1
    assert written_cases[0]["expectedCharacteristics"] == [
        "Human feedback: First note",
        "Human feedback: Second note",
    ]


def test_promote_candidate_rejects_unknown_candidate(tmp_path) -> None:
    store = TraceStore(tmp_path / "traces.sqlite")

    with pytest.raises(ValueError, match="Unknown trace_id"):
        promote_candidate(
            store=store,
            trace_id="trace_missing",
            dataset_path=tmp_path / "generated_regressions.json",
        )
