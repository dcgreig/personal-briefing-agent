"""Terminal formatting for the daily briefing."""

from __future__ import annotations

from briefing_agent.models import Category, Classification


CATEGORY_ORDER: tuple[Category, ...] = ("urgent", "waiting_on_me", "fyi", "ignore")

CATEGORY_LABELS: dict[Category, str] = {
    "urgent": "Urgent",
    "waiting_on_me": "Waiting On Me",
    "fyi": "FYI",
    "ignore": "Ignore",
}


def build_briefing(classifications: list[Classification]) -> str:
    """Build a human-readable briefing grouped by classification category."""
    lines = ["Daily Briefing", "==============", ""]

    for category in CATEGORY_ORDER:
        items = [
            classification
            for classification in classifications
            if classification.category == category
        ]
        lines.append(f"{CATEGORY_LABELS[category]} ({len(items)})")
        lines.append("-" * (len(lines[-1])))

        if not items:
            lines.append("No items.")
        else:
            for item in items:
                lines.append(f"- [{item.source_type}] {item.title}")
                lines.append(f"  Summary: {item.summary}")
                lines.append(f"  Reason: {item.reason}")

        lines.append("")

    return "\n".join(lines).rstrip()
