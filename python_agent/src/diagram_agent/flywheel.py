import json
from pathlib import Path
from typing import Any

from diagram_agent.tracing import TraceStore


def build_regression_case(
    trace: dict[str, Any],
    candidate: dict[str, Any],
    feedback: list[dict[str, Any]],
) -> dict[str, Any]:
    notes = [item["note"] for item in feedback if item.get("note")]
    characteristics = [
        f"Human feedback: {note}"
        for note in notes
    ]

    if not characteristics:
        characteristics = [f"Human feedback: {candidate['reason']}"]

    return {
        "id": f"trace-regression-{trace['trace_id']}",
        "input": trace["input"],
        "expectedCharacteristics": characteristics,
        "expectedKeywords": [],
        "difficulty": "medium",
        "category": "create",
    }


def load_regression_cases(dataset_path: Path) -> list[dict[str, Any]]:
    if not dataset_path.exists():
        return []

    return json.loads(dataset_path.read_text())


def write_regression_case(dataset_path: Path, case: dict[str, Any]) -> None:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    cases = load_regression_cases(dataset_path)
    cases_by_id = {item["id"]: item for item in cases}
    cases_by_id[case["id"]] = case
    dataset_path.write_text(
        json.dumps(list(cases_by_id.values()), indent=2) + "\n",
    )


def promote_candidate(
    store: TraceStore,
    trace_id: str,
    dataset_path: Path,
) -> dict[str, Any]:
    trace = store.get_trace(trace_id)
    if trace is None:
        raise ValueError(f"Unknown trace_id: {trace_id}")

    candidate = store.get_eval_candidate(trace_id)
    if candidate is None:
        raise ValueError(f"Trace is not an eval candidate: {trace_id}")

    case = build_regression_case(
        trace=trace,
        candidate=candidate,
        feedback=store.get_feedback(trace_id),
    )
    write_regression_case(dataset_path, case)
    store.update_eval_candidate_status(trace_id, "promoted")
    return case
