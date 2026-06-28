import json
import sqlite3
from pathlib import Path
from typing import Any

from diagram_agent.agent import AgentRunResult


class TraceStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    input TEXT NOT NULL,
                    plan_json TEXT,
                    final_text TEXT NOT NULL,
                    final_canvas_json TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    errors_json TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    step_count INTEGER NOT NULL,
                    tool_call_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    call_index INTEGER NOT NULL,
                    tool_call_id TEXT,
                    tool_name TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS eval_candidates (
                    trace_id TEXT PRIMARY KEY,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
                )
                """
            )

    def save_run(self, result: AgentRunResult) -> None:
        status = "error" if result.errors else "ok"
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO traces (
                    trace_id,
                    input,
                    plan_json,
                    final_text,
                    final_canvas_json,
                    steps_json,
                    errors_json,
                    latency_ms,
                    step_count,
                    tool_call_count,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.trace_id,
                    result.prompt,
                    json.dumps(result.plan),
                    result.final_text,
                    json.dumps(result.canvas_elements),
                    json.dumps(result.steps),
                    json.dumps(result.errors),
                    result.latency_ms,
                    result.step_count,
                    len(result.tool_calls),
                    status,
                ),
            )

            connection.execute(
                "DELETE FROM tool_events WHERE trace_id = ?",
                (result.trace_id,),
            )

            for call_index, tool_call in enumerate(result.tool_calls):
                connection.execute(
                    """
                    INSERT INTO tool_events (
                        trace_id,
                        call_index,
                        tool_call_id,
                        tool_name,
                        input_json,
                        output_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.trace_id,
                        call_index,
                        tool_call.get("id"),
                        tool_call["name"],
                        json.dumps(tool_call.get("input")),
                        json.dumps(tool_call.get("output")),
                    ),
                )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_tool_events(self, trace_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM tool_events
                WHERE trace_id = ?
                ORDER BY call_index ASC
                """,
                (trace_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM traces
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def add_feedback(self, trace_id: str, rating: str, note: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feedback (trace_id, rating, note)
                VALUES (?, ?, ?)
                """,
                (trace_id, rating, note),
            )
            if rating == "down":
                connection.execute(
                    """
                    INSERT OR IGNORE INTO eval_candidates (trace_id, reason, status)
                    VALUES (?, ?, ?)
                    """,
                    (trace_id, note, "new"),
                )

    def get_feedback(self, trace_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM feedback
                WHERE trace_id = ?
                ORDER BY created_at ASC
                """,
                (trace_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_eval_candidates(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM eval_candidates
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_eval_candidate(self, trace_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM eval_candidates
                WHERE trace_id = ?
                """,
                (trace_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def update_eval_candidate_status(self, trace_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE eval_candidates
                SET status = ?
                WHERE trace_id = ?
                """,
                (status, trace_id),
            )
