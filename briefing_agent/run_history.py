"""JSONL run history for completed briefing executions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

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
