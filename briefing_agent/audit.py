"""JSONL audit logging for classification decisions."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from briefing_agent.models import ReviewDecision


def append_audit_log(reviewed_items: list[ReviewDecision], path: Path) -> None:
    """Append one JSON object per reviewed classification to a JSONL audit file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    with path.open("a", encoding="utf-8") as file:
        for reviewed_item in reviewed_items:
            original = asdict(reviewed_item.original)
            final = {
                **original,
                "category": reviewed_item.final_category,
            }
            record = {
                "timestamp": timestamp,
                "changed": reviewed_item.changed,
                "original_classification": original,
                "final_classification": final,
            }
            file.write(json.dumps(record, sort_keys=True) + "\n")
