"""JSONL run history for completed briefing executions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from briefing_agent.briefing import category_counts
from briefing_agent.models import Classification


def append_run_history(
    path: Path,
    run_id: str,
    generated_at: datetime,
    enabled_sources: tuple[str, ...],
    classifications: list[Classification],
    briefing_output_path: Path | None,
    audit_log_path: Path,
) -> None:
    """Append one JSON object describing a completed CLI run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = category_counts(classifications)
    record = {
        "run_id": run_id,
        "generated_at": generated_at.isoformat(),
        "enabled_sources": list(enabled_sources),
        "total_item_count": len(classifications),
        "counts_by_classification": {
            category: count for category, count in counts.items()
        },
        "briefing_output_path": (
            str(briefing_output_path) if briefing_output_path is not None else None
        ),
        "audit_log_path": str(audit_log_path),
    }

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")


def load_run_history(path: Path) -> list[dict[str, Any]]:
    """Load run history records from a local JSONL file."""
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON in run history at line {line_number}: {error.msg}"
            ) from error
        if not isinstance(record, dict):
            raise ValueError(f"Run history line {line_number} must be a JSON object")
        records.append(record)
    return records


def find_run(records: list[dict[str, Any]], run_id: str) -> dict[str, Any] | None:
    """Return the first run history record with the requested run id."""
    for record in records:
        if record.get("run_id") == run_id:
            return record
    return None


def build_history_report(records: list[dict[str, Any]], limit: int = 10) -> str:
    """Build terminal output for recent briefing runs."""
    recent_records = list(reversed(records))[:limit]
    lines = [
        "Briefing Run History",
        "====================",
    ]

    if not recent_records:
        lines.append("No briefing runs found yet.")
        return "\n".join(lines)

    for record in recent_records:
        lines.append("")
        lines.append(f"Run ID: {record.get('run_id', 'unknown')}")
        lines.append(f"Generated: {record.get('generated_at', 'unknown')}")
        lines.append(f"Enabled sources: {_join_values(record.get('enabled_sources'))}")
        lines.append(f"Total items: {record.get('total_item_count', 0)}")
        lines.append(
            "Counts: "
            f"{_format_counts(record.get('counts_by_classification', {}))}"
        )
        lines.append(
            f"Briefing output: {record.get('briefing_output_path', 'not configured')}"
        )

    return "\n".join(lines)


def build_run_report(record: dict[str, Any]) -> str:
    """Build terminal output for a single briefing run."""
    lines = [
        "Briefing Run",
        "============",
        f"Run ID: {record.get('run_id', 'unknown')}",
        f"Generated: {record.get('generated_at', 'unknown')}",
        f"Enabled sources: {_join_values(record.get('enabled_sources'))}",
        f"Total items: {record.get('total_item_count', 0)}",
        f"Counts: {_format_counts(record.get('counts_by_classification', {}))}",
        f"Briefing output: {record.get('briefing_output_path', 'not configured')}",
        f"Audit log: {record.get('audit_log_path', 'unknown')}",
    ]
    return "\n".join(lines)


def _format_counts(value: Any) -> str:
    if not isinstance(value, dict):
        return "unavailable"
    ordered_categories = ("urgent", "waiting_on_me", "fyi", "ignore")
    return ", ".join(
        f"{category}={value.get(category, 0)}" for category in ordered_categories
    )


def _join_values(value: Any) -> str:
    if not isinstance(value, list | tuple):
        return "unknown"
    if not value:
        return "none"
    return ", ".join(str(item) for item in value)
