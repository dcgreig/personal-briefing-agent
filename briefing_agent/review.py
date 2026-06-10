"""Human review prompts for local classification decisions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from briefing_agent.actions import suggest_action
from briefing_agent.briefing import CATEGORY_LABELS, CATEGORY_ORDER, category_counts
from briefing_agent.models import ActionSuggestion, Category, Classification, ReviewDecision


ACCEPT_INPUTS = {"", "a", "accept", "y", "yes"}
SKIP_INPUTS = {"s", "skip"}
CONFIRM_INPUTS = {"y", "yes"}
OVERRIDE_INPUTS: dict[str, Category] = {
    "u": "urgent",
    "urgent": "urgent",
    "w": "waiting_on_me",
    "waiting_on_me": "waiting_on_me",
    "f": "fyi",
    "fyi": "fyi",
    "i": "ignore",
    "ignore": "ignore",
}


def review_classifications(
    classifications: list[Classification],
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> list[ReviewDecision]:
    """Ask a human to accept or override each classification."""
    decisions: list[ReviewDecision] = []

    output_func("")
    output_func("Human Review")
    output_func("============")

    for index, classification in enumerate(classifications, start=1):
        suggestion = _preview_suggestion(classification)
        _show_review_item(
            index,
            len(classifications),
            classification,
            suggestion,
            output_func,
        )

        final_category, skipped = _ask_for_review_choice(
            classification.category,
            input_func,
            output_func,
        )
        decisions.append(
            ReviewDecision(
                original=classification,
                final_category=final_category,
                changed=not skipped and final_category != classification.category,
                skipped=skipped,
            )
        )

    return decisions


def accept_all_classifications(
    classifications: list[Classification],
) -> list[ReviewDecision]:
    """Use the suggested classifications without prompting for review."""
    return [
        ReviewDecision(
            original=classification,
            final_category=classification.category,
            changed=False,
        )
        for classification in classifications
    ]


def finalized_classifications(
    reviewed_items: list[ReviewDecision],
) -> list[Classification]:
    """Return classifications after human review decisions are applied."""
    return [
        replace(reviewed_item.original, category=reviewed_item.final_category)
        for reviewed_item in reviewed_items
    ]


def confirm_review(
    reviewed_items: list[ReviewDecision],
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> bool:
    """Ask for final confirmation before writing local output files."""
    output_func("")
    output_func(build_review_summary(reviewed_items))
    response = input_func(
        "Write audit log, run history, and Markdown briefing? [y/N]: "
    ).strip().lower()
    return response in CONFIRM_INPUTS


def build_review_summary(reviewed_items: list[ReviewDecision]) -> str:
    """Build a short confirmation summary for reviewed classifications."""
    final_classifications = finalized_classifications(reviewed_items)
    counts = category_counts(final_classifications)
    changed_count = sum(1 for item in reviewed_items if item.changed)
    skipped_count = sum(1 for item in reviewed_items if item.skipped)
    accepted_count = len(reviewed_items) - changed_count - skipped_count

    lines = [
        "Review Summary",
        "==============",
        f"Total items: {len(reviewed_items)}",
        f"Accepted: {accepted_count}",
        f"Changed: {changed_count}",
        f"Skipped for now: {skipped_count}",
        "",
        "Final counts:",
    ]

    for category in CATEGORY_ORDER:
        lines.append(f"- {CATEGORY_LABELS[category]}: {counts[category]}")

    return "\n".join(lines)


def _show_review_item(
    index: int,
    total_count: int,
    classification: Classification,
    suggestion: ActionSuggestion,
    output_func: Callable[[str], None],
) -> None:
    output_func("")
    output_func(f"Item {index} of {total_count}")
    output_func(f"Source: {classification.source_name}")
    output_func(f"Type: {classification.source_type}")
    output_func(f"Title: {classification.title}")
    output_func(f"Classification: {classification.category}")
    output_func(f"Reason: {classification.reason}")
    output_func(f"Suggested dry-run action: {suggestion.action_type}")
    output_func(f"Suggested action rationale: {suggestion.rationale}")


def _preview_suggestion(classification: Classification) -> ActionSuggestion:
    return suggest_action(
        ReviewDecision(
            original=classification,
            final_category=classification.category,
            changed=False,
        )
    )


def _ask_for_review_choice(
    suggested_category: Category,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> tuple[Category, bool]:
    prompt = (
        "Choose [Enter/a] accept, [u] urgent, [w] waiting_on_me, "
        "[f] fyi, [i] ignore, [s] skip: "
    )

    while True:
        response = input_func(prompt).strip().lower()

        if response in ACCEPT_INPUTS:
            return suggested_category, False

        if response in SKIP_INPUTS:
            return suggested_category, True

        if response in OVERRIDE_INPUTS:
            return OVERRIDE_INPUTS[response], False

        output_func(
            "Please choose accept, urgent, waiting_on_me, fyi, ignore, or skip."
        )
