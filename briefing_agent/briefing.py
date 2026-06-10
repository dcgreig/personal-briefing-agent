"""Terminal and Markdown formatting for the daily briefing."""

from __future__ import annotations

from datetime import datetime, timezone

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


def build_markdown_briefing(
    classifications: list[Classification],
    generated_at: datetime | None = None,
) -> str:
    """Build a Markdown briefing for saving to disk."""
    generated_at = generated_at or datetime.now(timezone.utc)
    lines = [
        "# Daily Briefing",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        "## Summary Counts",
        "",
    ]

    counts = _category_counts(classifications)
    for category in CATEGORY_ORDER:
        lines.append(f"- {CATEGORY_LABELS[category]}: {counts[category]}")

    lines.append("")

    for category in CATEGORY_ORDER:
        items = [
            classification
            for classification in classifications
            if classification.category == category
        ]
        lines.append(f"## {_markdown_section_title(category)}")
        lines.append("")

        if not items:
            lines.append("No items.")
            lines.append("")
            continue

        for item in items:
            lines.append(f"### {item.title}")
            lines.append("")
            lines.append(f"- Source: {item.source_name}")
            lines.append(f"- Type: {item.source_type}")
            lines.append(f"- Classification: {item.category}")
            lines.append(f"- Reason: {item.reason}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _category_counts(classifications: list[Classification]) -> dict[Category, int]:
    return {
        category: sum(
            1
            for classification in classifications
            if classification.category == category
        )
        for category in CATEGORY_ORDER
    }


def _markdown_section_title(category: Category) -> str:
    if category == "ignore":
        return "Ignored Items"
    return f"{CATEGORY_LABELS[category]} Items"
