"""Terminal and Markdown formatting for the daily briefing."""

from __future__ import annotations

from datetime import datetime

from briefing_agent.filters import FilterSummary, filters_to_dict
from briefing_agent.models import ActionSuggestion, Category, Classification


CATEGORY_ORDER: tuple[Category, ...] = ("urgent", "waiting_on_me", "fyi", "ignore")

CATEGORY_LABELS: dict[Category, str] = {
    "urgent": "Urgent",
    "waiting_on_me": "Waiting On Me",
    "fyi": "FYI",
    "ignore": "Ignore",
}


def build_briefing(
    classifications: list[Classification],
    run_id: str,
    generated_at: datetime,
) -> str:
    """Build a human-readable briefing grouped by classification category."""
    lines = [
        "Daily Briefing",
        "==============",
        f"Run ID: {run_id}",
        f"Generated: {generated_at.isoformat()}",
        "",
    ]

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
    run_id: str,
    generated_at: datetime,
    action_suggestions: list[ActionSuggestion] | None = None,
    filter_summary: FilterSummary | None = None,
) -> str:
    """Build a Markdown briefing for saving to disk."""
    suggestions_by_item_id = _suggestions_by_item_id(action_suggestions or [])
    lines = [
        "# Daily Briefing",
        "",
        f"Run ID: {run_id}",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        "## Summary Counts",
        "",
    ]

    counts = category_counts(classifications)
    for category in CATEGORY_ORDER:
        lines.append(f"- {CATEGORY_LABELS[category]}: {counts[category]}")

    lines.append("")
    if filter_summary is not None:
        lines.extend(_build_filter_lines(filter_summary))
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
            suggestion = suggestions_by_item_id.get(item.item_id)
            if suggestion is not None:
                lines.append(f"- Suggested action: {suggestion.action_type}")
                lines.append(f"- Action title: {suggestion.title}")
                lines.append(f"- Rationale: {suggestion.rationale}")
                lines.append(
                    "- Requires human approval: "
                    f"{str(suggestion.requires_human_approval).lower()}"
                )
                lines.append("- Dry-run only: no action was executed.")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_action_suggestions_report(
    classifications: list[Classification],
    action_suggestions: list[ActionSuggestion],
) -> str:
    """Build terminal output for dry-run action suggestions."""
    classifications_by_item_id = {
        classification.item_id: classification for classification in classifications
    }
    lines = [
        "",
        "Dry-Run Action Suggestions",
        "==========================",
        "No external actions were executed.",
        "",
    ]

    for suggestion in action_suggestions:
        classification = classifications_by_item_id[suggestion.item_id]
        lines.append(f"- [{classification.source_type}] {classification.title}")
        lines.append(f"  Final classification: {classification.category}")
        lines.append(f"  Suggested action: {suggestion.action_type}")
        lines.append(f"  Title: {suggestion.title}")
        lines.append(f"  Rationale: {suggestion.rationale}")
        lines.append(
            "  Requires human approval: "
            f"{str(suggestion.requires_human_approval).lower()}"
        )
        lines.append("  Dry-run only: no action was executed.")

    return "\n".join(lines).rstrip()


def category_counts(classifications: list[Classification]) -> dict[Category, int]:
    """Count classifications by category."""
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


def _suggestions_by_item_id(
    action_suggestions: list[ActionSuggestion],
) -> dict[str, ActionSuggestion]:
    return {suggestion.item_id: suggestion for suggestion in action_suggestions}


def _build_filter_lines(filter_summary: FilterSummary) -> list[str]:
    lines = [
        "## Filters Applied",
        "",
        f"- Starting items: {filter_summary.starting_count}",
        f"- After source/type filters: {filter_summary.after_source_type_filters}",
        f"- After max_items: {filter_summary.after_max_items}",
        (
            "- After classification filters: "
            f"{filter_summary.after_classification_filters}"
        ),
        f"- Total removed: {filter_summary.total_removed}",
        "",
        "### Settings",
        "",
    ]
    for key, value in filters_to_dict(filter_summary.settings).items():
        lines.append(f"- {key}: {_format_filter_value(value)}")
    return lines


def _format_filter_value(value: object) -> str:
    if value is None:
        return "not set"
    if isinstance(value, list):
        if not value:
            return "not set"
        return ", ".join(str(item) for item in value)
    return str(value)
