from diagram_agent.braintrust_export import (
    build_braintrust_rows,
    export_report_to_braintrust,
    log_braintrust_rows,
)
from diagram_agent.evals import EvalCaseResult, EvalReport


def test_build_braintrust_rows_maps_eval_results() -> None:
    report = EvalReport(
        created_at="2026-05-30T00:00:00+00:00",
        dataset_paths=["evals/datasets/golden_2.json"],
        total=2,
        passed=1,
        failed=1,
        results=[
            EvalCaseResult(
                id="case-pass",
                input="Draw a box labeled User",
                passed=True,
                scores={
                    "schema_valid": True,
                    "expected_keywords_present": True,
                    "no_overlaps": True,
                },
                final_text="Created the diagram.",
                compact_canvas="user: rectangle 'User' at (0,0)",
                missing_keywords=[],
            ),
            EvalCaseResult(
                id="case-fail",
                input="Draw a diamond labeled Decision",
                passed=False,
                scores={
                    "schema_valid": True,
                    "expected_keywords_present": False,
                    "no_overlaps": True,
                },
                final_text="Created the diagram.",
                compact_canvas="user: rectangle 'User' at (0,0)",
                missing_keywords=["decision"],
            ),
        ],
    )

    rows = build_braintrust_rows(report)

    assert rows == [
        {
            "id": "case-pass",
            "input": "Draw a box labeled User",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 1.0,
                "schema_valid": 1.0,
                "expected_keywords_present": 1.0,
                "no_overlaps": 1.0,
            },
            "metadata": {
                "case_id": "case-pass",
                "missing_keywords": [],
                "dataset_paths": ["evals/datasets/golden_2.json"],
                "report_created_at": "2026-05-30T00:00:00+00:00",
            },
        },
        {
            "id": "case-fail",
            "input": "Draw a diamond labeled Decision",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 0.0,
                "schema_valid": 1.0,
                "expected_keywords_present": 0.0,
                "no_overlaps": 1.0,
            },
            "metadata": {
                "case_id": "case-fail",
                "missing_keywords": ["decision"],
                "dataset_paths": ["evals/datasets/golden_2.json"],
                "report_created_at": "2026-05-30T00:00:00+00:00",
            },
        },
    ]


class FakeExperiment:
    def __init__(self) -> None:
        self.logged: list[dict] = []
        self.summarized = False

    def log(self, **kwargs) -> None:
        self.logged.append(kwargs)

    def summarize(self) -> dict:
        self.summarized = True
        return {"experiment_url": "https://braintrust.example/experiments/123"}


def test_log_braintrust_rows_logs_each_row_and_summarizes() -> None:
    experiment = FakeExperiment()
    rows = [
        {
            "id": "case-pass",
            "input": "Draw a box labeled User",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 1.0,
                "schema_valid": 1.0,
            },
            "metadata": {
                "case_id": "case-pass",
            },
        },
        {
            "id": "case-fail",
            "input": "Draw a diamond labeled Decision",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 0.0,
                "schema_valid": 1.0,
            },
            "metadata": {
                "case_id": "case-fail",
            },
        },
    ]

    summary = log_braintrust_rows(experiment, rows)

    assert experiment.logged == [
        {
            "id": "case-pass",
            "input": "Draw a box labeled User",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 1.0,
                "schema_valid": 1.0,
            },
            "metadata": {
                "case_id": "case-pass",
            },
        },
        {
            "id": "case-fail",
            "input": "Draw a diamond labeled Decision",
            "output": {
                "final_text": "Created the diagram.",
                "compact_canvas": "user: rectangle 'User' at (0,0)",
            },
            "scores": {
                "passed": 0.0,
                "schema_valid": 1.0,
            },
            "metadata": {
                "case_id": "case-fail",
            },
        },
    ]
    assert experiment.summarized is True
    assert summary == {"experiment_url": "https://braintrust.example/experiments/123"}


class FakeBraintrust:
    def __init__(self) -> None:
        self.init_kwargs: dict | None = None
        self.experiment = FakeExperiment()

    def init(self, **kwargs) -> FakeExperiment:
        self.init_kwargs = kwargs
        return self.experiment


def test_export_report_to_braintrust_initializes_experiment_and_logs_rows() -> None:
    report = EvalReport(
        created_at="2026-05-30T00:00:00+00:00",
        dataset_paths=["evals/datasets/golden_2.json"],
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalCaseResult(
                id="case-pass",
                input="Draw a box labeled User",
                passed=True,
                scores={
                    "schema_valid": True,
                },
                final_text="Created the diagram.",
                compact_canvas="user: rectangle 'User' at (0,0)",
                missing_keywords=[],
            ),
        ],
    )
    braintrust = FakeBraintrust()

    summary = export_report_to_braintrust(
        report=report,
        project_name="Diagram Agent",
        experiment_name="golden-regression",
        braintrust_module=braintrust,
    )

    assert braintrust.init_kwargs == {
        "project": "Diagram Agent",
        "experiment": "golden-regression",
    }
    assert braintrust.experiment.logged[0]["id"] == "case-pass"
    assert braintrust.experiment.logged[0]["scores"] == {
        "passed": 1.0,
        "schema_valid": 1.0,
    }
    assert summary == {"experiment_url": "https://braintrust.example/experiments/123"}
