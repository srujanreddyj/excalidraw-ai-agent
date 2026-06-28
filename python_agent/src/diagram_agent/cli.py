import typer
import json
from rich.console import Console
from diagram_agent.agent import run_agent
from diagram_agent.planner import PlanningMode
from pathlib import Path
import os
import importlib
from typing import Literal
from dotenv import load_dotenv
from diagram_agent.flywheel import promote_candidate
from diagram_agent.tracing import TraceStore
from diagram_agent.openai_client import OpenAIPlannerClient, OpenAIResponsesModelClient
from diagram_agent.evals import run_eval, write_eval_report
from diagram_agent.braintrust_export import export_report_to_braintrust
from diagram_agent.evals import EvalReport


app = typer.Typer(help="Python-first diagram agent CLI.")
console = Console()

load_dotenv()
load_dotenv("../.dev.vars")
load_dotenv("../.dev.var")
DEFAULT_TRACE_DB = Path(".data/traces.sqlite")
DEFAULT_REGRESSION_DATASET = Path("../evals/datasets/generated_regressions.json")

@app.callback()
def main() -> None:
    """Python-first diagram agent CLI."""
    pass


@app.command()
def run(
        prompt: str,
        json_output: bool = typer.Option(False, "--json", help = "print the full result as JSON."),
        planning: PlanningMode = typer.Option(
            "off",
            "--planning",
            help="Planning mode: off, required, or auto.",
        ),
        backend: Literal["local", "openai"] = typer.Option(
            "local",
            "--backend",
            help="Agent backend: local deterministic simulator or OpenAI tool-calling.",
        ),
        trace_db: Path = typer.Option(
            DEFAULT_TRACE_DB,
            "--trace-db",
            help="Path to the SQLite trace database.",
        ),
        planner_backend: Literal["local", "openai"] = typer.Option(
            "local",
            "--planner-backend",
            help="Planner backend: local deterministic planner or OpenAI no-tool planner.",
        ),
    ) -> None:
    """Run the local diagram agent simulator."""

    model_client = None
    if backend == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise typer.BadParameter("OPENAI_API_KEY is required for --backend openai")
        model_client = OpenAIResponsesModelClient()

    plan_client = None
    if planner_backend == "openai" and planning != "off":
        if not os.getenv("OPENAI_API_KEY"):
            raise typer.BadParameter("OPENAI_API_KEY is required for --planner-backend openai")
        plan_client = OpenAIPlannerClient()

    result = run_agent(
            prompt,
            planning=planning,
            model_client=model_client,
            plan_client=plan_client,
        )
    TraceStore(trace_db).save_run(result)

    if json_output:
        print(json.dumps(result.model_dump(), indent=2))
        return

    

    if result.plan:
        console.print(f"Plan intent: {result.plan['intent']}")
    
    console.print("[bold]Diagram agent skeleton[/bold]")
    console.print(f"Prompt: {prompt}")
    console.print(f"Final: {result.final_text}")
    console.print(f"Steps: {', '.join(result.steps)}")
    console.print(f"Trace: {result.trace_id}")
    # console.print("Status: CLI wiring works")

@app.command()
def eval(
    dataset: list[Path] = typer.Option(..., "--dataset", help="Path to an eval dataset JSON file."),
    planning: PlanningMode = typer.Option("off", "--planning", help="Planning mode: off, required, or auto."),
    json_output: bool = typer.Option(False, "--json", help="Print the full report as JSON."),
) -> None:
    """Run evals against one or more datasets."""
    report = run_eval(dataset, planning=planning)
    output_path = write_eval_report(report, Path("runs"))

    if json_output:
        print(json.dumps(report.model_dump(), indent=2))
        return

    console.print("[bold]Eval complete[/bold]")
    console.print(f"Total: {report.total}")
    console.print(f"Passed: {report.passed}")
    console.print(f"Failed: {report.failed}")
    console.print(f"Report: {output_path}")

traces_app = typer.Typer(help="Inspect saved agent traces.")
app.add_typer(traces_app, name="traces")


@traces_app.command("list")
def traces_list(
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    store = TraceStore(trace_db)
    for trace in store.list_traces():
        console.print(
            f"{trace['trace_id']} | {trace['status']} | {trace['input']}"
        )


@traces_app.command("show")
def traces_show(
    trace_id: str,
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    trace = TraceStore(trace_db).get_trace(trace_id)
    if trace is None:
        raise typer.BadParameter(f"Unknown trace_id: {trace_id}")

    console.print(json.dumps(trace, indent=2))


@traces_app.command("tools")
def traces_tools(
    trace_id: str,
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    events = TraceStore(trace_db).get_tool_events(trace_id)
    for event in events:
        console.print(
            f"{event['call_index']} | {event['tool_name']} | {event['tool_call_id']}"
        )


feedback_app = typer.Typer(help="Capture feedback for saved traces.")
app.add_typer(feedback_app, name="feedback")


@feedback_app.command("add")
def feedback_add(
    trace_id: str,
    rating: Literal["up", "down"] = typer.Option(..., "--rating"),
    note: str = typer.Option("", "--note"),
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    store = TraceStore(trace_db)
    if store.get_trace(trace_id) is None:
        raise typer.BadParameter(f"Unknown trace_id: {trace_id}")

    store.add_feedback(trace_id=trace_id, rating=rating, note=note)
    console.print(f"Feedback saved for {trace_id}")
    if rating == "down":
        console.print("Eval candidate created")


candidates_app = typer.Typer(help="Promote feedback traces into regression evals.")
app.add_typer(candidates_app, name="candidates")


@candidates_app.command("list")
def candidates_list(
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    candidates = TraceStore(trace_db).list_eval_candidates()
    if not candidates:
        console.print("No eval candidates")
        return

    for candidate in candidates:
        console.print(
            f"{candidate['trace_id']} | {candidate['status']} | {candidate['reason']}"
        )


@candidates_app.command("ignore")
def candidates_ignore(
    trace_id: str,
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    store = TraceStore(trace_db)
    if store.get_eval_candidate(trace_id) is None:
        raise typer.BadParameter(f"Unknown eval candidate: {trace_id}")

    store.update_eval_candidate_status(trace_id, "ignored")
    console.print(f"Ignored eval candidate {trace_id}")


@candidates_app.command("promote")
def candidates_promote(
    trace_id: str,
    set_name: str = typer.Option("regression", "--set"),
    output: Path = typer.Option(
        DEFAULT_REGRESSION_DATASET,
        "--output",
        help="Regression dataset JSON path.",
    ),
    trace_db: Path = typer.Option(DEFAULT_TRACE_DB, "--trace-db"),
) -> None:
    if set_name != "regression":
        raise typer.BadParameter("Only --set regression is supported for now")

    case = promote_candidate(
        store=TraceStore(trace_db),
        trace_id=trace_id,
        dataset_path=output,
    )
    console.print(f"Promoted {trace_id} to {output}")
    console.print(f"Case id: {case['id']}")

braintrust_app = typer.Typer(help="Export eval reports to Braintrust.")
app.add_typer(braintrust_app, name="braintrust")

@braintrust_app.command("export")
def braintrust_export(
    report: Path = typer.Option(..., "--report", help="Path to an eval report JSON file."),
    project: str = typer.Option("Diagram Agent", "--project"),
    experiment: str = typer.Option("diagram-agent-eval", "--experiment"),
) -> None:
    if not os.getenv("BRAINTRUST_API_KEY"):
        raise typer.BadParameter("BRAINTRUST_API_KEY is required")
    
    if not report.exists():
        raise typer.BadParameter(f"Report file not found: {report}")

    braintrust = importlib.import_module("braintrust")
    eval_report = EvalReport.model_validate_json(report.read_text())
    summary = export_report_to_braintrust(
        report=eval_report,
        project_name=project,
        experiment_name=experiment,
        braintrust_module=braintrust,
    )

    console.print("Braintrust export complete")
    if isinstance(summary, dict) and summary.get("experiment_url"):
        console.print(summary["experiment_url"])
    else:
        console.print(summary)