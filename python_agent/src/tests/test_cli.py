import json
import sys

from typer.testing import CliRunner

from diagram_agent.cli import app
from diagram_agent.tracing import TraceStore


runner = CliRunner()


def test_cli_run_defaults_to_local_backend() -> None:
    result = runner.invoke(app, ["run", "Draw a flow"])

    assert result.exit_code == 0
    assert "Diagram agent skeleton" in result.output
    assert "Created a basic flow with 3 nodes." in result.output


def test_cli_run_rejects_openai_backend_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = runner.invoke(app, ["run", "Draw a flow", "--backend", "openai"])

    assert result.exit_code != 0
    assert "OPENAI_API_KEY is required" in result.output


def test_cli_run_saves_trace(tmp_path) -> None:
    trace_db = tmp_path / "traces.sqlite"

    result = runner.invoke(
        app,
        [
            "run",
            "Draw a flow",
            "--trace-db",
            str(trace_db),
        ],
    )

    assert result.exit_code == 0
    assert "Trace:" in result.output

    store = TraceStore(trace_db)
    traces = store.list_traces()

    assert len(traces) == 1
    assert traces[0]["input"] == "Draw a flow"
    assert traces[0]["tool_call_count"] == 1


def test_cli_traces_show_and_tools(tmp_path) -> None:
    trace_db = tmp_path / "traces.sqlite"
    run_result = runner.invoke(
        app,
        [
            "run",
            "Draw a flow",
            "--trace-db",
            str(trace_db),
        ],
    )
    trace_id = TraceStore(trace_db).list_traces()[0]["trace_id"]

    show_result = runner.invoke(
        app,
        ["traces", "show", trace_id, "--trace-db", str(trace_db)],
    )
    tools_result = runner.invoke(
        app,
        ["traces", "tools", trace_id, "--trace-db", str(trace_db)],
    )

    assert run_result.exit_code == 0
    assert show_result.exit_code == 0
    assert "Draw a flow" in show_result.output
    assert tools_result.exit_code == 0
    assert "addElements" in tools_result.output


def test_cli_feedback_and_candidate_promotion(tmp_path) -> None:
    trace_db = tmp_path / "traces.sqlite"
    output_path = tmp_path / "generated_regressions.json"
    runner.invoke(
        app,
        [
            "run",
            "Draw a flow",
            "--trace-db",
            str(trace_db),
        ],
    )
    trace_id = TraceStore(trace_db).list_traces()[0]["trace_id"]

    feedback_result = runner.invoke(
        app,
        [
            "feedback",
            "add",
            trace_id,
            "--rating",
            "down",
            "--note",
            "Boxes overlapped",
            "--trace-db",
            str(trace_db),
        ],
    )
    list_result = runner.invoke(
        app,
        ["candidates", "list", "--trace-db", str(trace_db)],
    )
    promote_result = runner.invoke(
        app,
        [
            "candidates",
            "promote",
            trace_id,
            "--output",
            str(output_path),
            "--trace-db",
            str(trace_db),
        ],
    )

    assert feedback_result.exit_code == 0
    assert "Eval candidate created" in feedback_result.output
    assert list_result.exit_code == 0
    assert trace_id in list_result.output
    assert promote_result.exit_code == 0
    assert output_path.exists()
    assert TraceStore(trace_db).get_eval_candidate(trace_id)["status"] == "promoted"


def test_cli_candidate_ignore(tmp_path) -> None:
    trace_db = tmp_path / "traces.sqlite"
    runner.invoke(
        app,
        [
            "run",
            "Draw a flow",
            "--trace-db",
            str(trace_db),
        ],
    )
    trace_id = TraceStore(trace_db).list_traces()[0]["trace_id"]
    runner.invoke(
        app,
        [
            "feedback",
            "add",
            trace_id,
            "--rating",
            "down",
            "--note",
            "Not useful",
            "--trace-db",
            str(trace_db),
        ],
    )

    result = runner.invoke(
        app,
        ["candidates", "ignore", trace_id, "--trace-db", str(trace_db)],
    )

    assert result.exit_code == 0
    assert TraceStore(trace_db).get_eval_candidate(trace_id)["status"] == "ignored"


class FakeBraintrustExperiment:
    def __init__(self) -> None:
        self.logged: list[dict] = []

    def log(self, **kwargs) -> None:
        self.logged.append(kwargs)

    def summarize(self) -> dict:
        return {"experiment_url": "https://braintrust.example/experiments/cli"}


class FakeBraintrustModule:
    def __init__(self) -> None:
        self.init_kwargs: dict | None = None
        self.experiment = FakeBraintrustExperiment()

    def init(self, **kwargs) -> FakeBraintrustExperiment:
        self.init_kwargs = kwargs
        return self.experiment


def test_cli_braintrust_export_logs_eval_report(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "eval-report.json"
    report_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-30T00:00:00+00:00",
                "dataset_paths": ["evals/datasets/golden_2.json"],
                "total": 1,
                "passed": 1,
                "failed": 0,
                "results": [
                    {
                        "id": "case-pass",
                        "input": "Draw a box labeled User",
                        "passed": True,
                        "scores": {"schema_valid": True},
                        "final_text": "Created the diagram.",
                        "compact_canvas": "user: rectangle 'User' at (0,0)",
                        "missing_keywords": [],
                    }
                ],
            }
        )
    )
    fake_braintrust = FakeBraintrustModule()
    monkeypatch.setenv("BRAINTRUST_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "braintrust", fake_braintrust)

    result = runner.invoke(
        app,
        [
            "braintrust",
            "export",
            "--report",
            str(report_path),
            "--project",
            "Diagram Agent",
            "--experiment",
            "local-eval",
        ],
    )

    assert result.exit_code == 0
    assert fake_braintrust.init_kwargs == {
        "project": "Diagram Agent",
        "experiment": "local-eval",
    }
    assert fake_braintrust.experiment.logged[0]["id"] == "case-pass"
    assert "Braintrust export complete" in result.output
    assert "https://braintrust.example/experiments/cli" in result.output


def test_cli_braintrust_export_requires_api_key(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "eval-report.json"
    report_path.write_text(
        json.dumps(
            {
                "created_at": "2026-05-30T00:00:00+00:00",
                "dataset_paths": [],
                "total": 0,
                "passed": 0,
                "failed": 0,
                "results": [],
            }
        )
    )
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)

    result = runner.invoke(
        app,
        [
            "braintrust",
            "export",
            "--report",
            str(report_path),
            "--project",
            "Diagram Agent",
        ],
    )

    assert result.exit_code != 0
    assert "BRAINTRUST_API_KEY is required" in result.output
