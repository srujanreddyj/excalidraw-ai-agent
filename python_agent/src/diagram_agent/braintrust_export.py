from typing import Any

from diagram_agent.evals import EvalReport

def _bool_score(value: bool) -> float:
    return 1.0 if value else 0.0

def build_braintrust_rows(report: EvalReport) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for result in report.results:
        scores = {
            "passed": _bool_score(result.passed),
            **{
                name: _bool_score(value)
                for name, value in result.scores.items()
            },
        }
    
        rows.append(
            {
                "id": result.id,
                "input": result.input,
                "output": {
                    "final_text": result.final_text,
                    "compact_canvas": result.compact_canvas,
                },
                "scores": scores,
                "metadata": {
                    "case_id": result.id,
                    "missing_keywords": result.missing_keywords,
                    "dataset_paths": report.dataset_paths,
                    "report_created_at": report.created_at,
                },
            }
        )

    return rows


def log_braintrust_rows(experiment, rows: list[dict[str, Any]]) -> Any:
    for row in rows:
        experiment.log(**row)

    return experiment.summarize()


def export_report_to_braintrust(
    report: EvalReport,
    project_name: str,
    experiment_name: str,
    braintrust_module,
) -> Any:
    experiment = braintrust_module.init(
        project=project_name,
        experiment=experiment_name,
    )
    rows = build_braintrust_rows(report)
    return log_braintrust_rows(experiment, rows)