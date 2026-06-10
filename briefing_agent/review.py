"""Human review prompts for local classification decisions."""

from __future__ import annotations

from collections.abc import Callable

from briefing_agent.models import Category, Classification, ReviewDecision


VALID_CATEGORIES: tuple[Category, ...] = ("urgent", "waiting_on_me", "fyi", "ignore")
ACCEPT_INPUTS = {"", "a", "accept", "y", "yes"}


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
        output_func("")
        output_func(f"Item {index} of {len(classifications)}")
        output_func(f"[{classification.source_type}] {classification.title}")
        output_func(f"Summary: {classification.summary}")
        output_func(f"Suggested classification: {classification.category}")
        output_func(f"Reason: {classification.reason}")

        final_category = _ask_for_category(classification.category, input_func, output_func)
        decisions.append(
            ReviewDecision(
                original=classification,
                final_category=final_category,
                changed=final_category != classification.category,
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


def _ask_for_category(
    suggested_category: Category,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> Category:
    prompt = (
        "Press Enter to accept, or type urgent/waiting_on_me/fyi/ignore to override: "
    )

    while True:
        response = input_func(prompt).strip().lower()

        if response in ACCEPT_INPUTS:
            return suggested_category

        if response in VALID_CATEGORIES:
            return response

        output_func("Please enter one of: urgent, waiting_on_me, fyi, ignore.")
