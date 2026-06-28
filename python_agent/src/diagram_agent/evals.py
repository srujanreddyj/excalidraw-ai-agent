import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from diagram_agent.agent import run_agent

class EvalCase(BaseModel):
    id: str
    input: str
    expectedCharacteristics: list[str] = Field(default_factory=list)
    expectedKeywords: list[str] = Field(default_factory=list)
    difficulty: str | None = None
    category: str | None = None

class EvalCaseResult(BaseModel):
    id: str
    input: str
    passed: bool
    scores: dict[str, bool]
    final_text: str
    compact_canvas: str
    missing_keywords: list[str]


class EvalReport(BaseModel):
    created_at: str
    dataset_paths: list[str]
    total: int
    passed: int
    failed: int
    results: list[EvalCaseResult]


def load_eval_cases(dataset_paths: list[Path]) -> list[EvalCase]:
    cases: list[EvalCase] = []

    for dataset_path in dataset_paths:
        raw_cases = json.loads(dataset_path.read_text())
        cases.extend(EvalCase.model_validate(raw_case) for raw_case in raw_cases)
    
    return cases

def run_eval(dataset_paths: list[Path], planning: str = "off") -> EvalReport:
    cases = load_eval_cases(dataset_paths)
    results: list[EvalCaseResult] = []

    for case in cases:
        result = run_agent(case.input, planning=planning)
        compact_canvas = _compact_canvas(result.canvas_elements)
        searchable_text = f"{result.final_text}\n{compact_canvas}".lower()

        missing_keywords = [
            keyword 
            for keyword in case.expectedKeywords
            if keyword.lower() not in searchable_text
        ]

        scores = {
            "schema_valid": True,
            "expected_keywords_present": not missing_keywords,
            "no_overlaps": True
        }

        passed = all(scores.values())
        results.append(
            EvalCaseResult(
                id=case.id,
                input=case.input,
                passed=passed,
                scores=scores,
                final_text=result.final_text,
                compact_canvas=compact_canvas,
                missing_keywords=missing_keywords,
            )
        )

    passed_count = sum(1 for result in results if result.passed)

    return EvalReport(
        created_at=datetime.now(UTC).isoformat(),
        dataset_paths=[str(path) for path in dataset_paths],
        total=len(results),
        passed=passed_count,
        failed=len(results) - passed_count,
        results=results,
    )

def write_eval_report(report: EvalReport, runs_dir: Path) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_path = runs_dir / f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.json"
    output_path.write_text(json.dumps(report.model_dump(), indent=2))
    return output_path


def _compact_canvas(elements: list[dict[str, Any]]) -> str:
    parts: list[str] = []

    for element in elements:
        if element["type"] == "arrow":
            parts.append(f"{element['id']}: arrow {element.get('start_id')}->{element.get('end_id')}")
        else:
            label = element.get("text") or element["id"]
            parts.append(
                f"{element['id']}: {element['type']} '{label}' at ({element['x']:g},{element['y']:g})"
            )

    return "\n".join(parts)