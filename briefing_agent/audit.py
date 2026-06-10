"""JSONL audit logging for classification decisions."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from briefing_agent.models import ActionSuggestion, ReviewDecision


def append_audit_log(
    reviewed_items: list[ReviewDecision],
    action_suggestions: list[ActionSuggestion],
    path: Path,
    run_id: str,
    generated_at: datetime,
) -> None:
    """Append one JSON object per reviewed classification to a JSONL audit file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = generated_at.isoformat()
    suggestions_by_item_id = {
        suggestion.item_id: suggestion for suggestion in action_suggestions
    }

    with path.open("a", encoding="utf-8") as file:
        for reviewed_item in reviewed_items:
            original = asdict(reviewed_item.original)
            suggestion = suggestions_by_item_id[reviewed_item.original.item_id]
            final = {
                **original,
                "category": reviewed_item.final_category,
            }
            record = {
                "run_id": run_id,
                "timestamp": timestamp,
                "changed": reviewed_item.changed,
                "original_classification": original,
                "final_classification": final,
                "suggested_action": asdict(suggestion),
            }
            file.write(json.dumps(record, sort_keys=True) + "\n")
