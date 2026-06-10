"""Dry-run action suggestions for reviewed briefing items."""

from __future__ import annotations

from briefing_agent.models import ActionSuggestion, ReviewDecision


def suggest_actions(reviewed_items: list[ReviewDecision]) -> list[ActionSuggestion]:
    """Create one deterministic dry-run action suggestion per reviewed item."""
    return [suggest_action(reviewed_item) for reviewed_item in reviewed_items]


def suggest_action(reviewed_item: ReviewDecision) -> ActionSuggestion:
    """Create a safe suggestion without executing any external action."""
    classification = reviewed_item.final_category
    item = reviewed_item.original

    if classification == "ignore":
        return ActionSuggestion(
            item_id=item.item_id,
            action_type="no_action",
            title="No dry-run action suggested",
            rationale="The item is finalized as ignore, so no follow-up is needed.",
            requires_human_approval=False,
        )

    if classification == "fyi":
        return ActionSuggestion(
            item_id=item.item_id,
            action_type="review",
            title="Review for context",
            rationale="The item is informational, so reading it later is enough.",
            requires_human_approval=False,
        )

    if item.source_type == "email" and classification in {"urgent", "waiting_on_me"}:
        return ActionSuggestion(
            item_id=item.item_id,
            action_type="reply",
            title="Consider drafting a reply",
            rationale=(
                "The finalized classification suggests a response may be needed; "
                "this is only a local dry-run suggestion."
            ),
            requires_human_approval=True,
        )

    if item.source_type == "jira" and classification == "urgent":
        return ActionSuggestion(
            item_id=item.item_id,
            action_type="follow_up",
            title="Consider following up with the task owner",
            rationale=(
                "The task is urgent, so coordination may be useful; this agent "
                "does not contact anyone or update Jira."
            ),
            requires_human_approval=True,
        )

    if item.source_type == "jira" and classification == "waiting_on_me":
        return ActionSuggestion(
            item_id=item.item_id,
            action_type="update_task",
            title="Consider preparing a task update",
            rationale=(
                "The task is waiting on you; any real task update would require "
                "human approval outside this local agent."
            ),
            requires_human_approval=True,
        )

    return ActionSuggestion(
        item_id=item.item_id,
        action_type="review",
        title="Review manually",
        rationale="No more specific dry-run suggestion matched this item.",
        requires_human_approval=False,
    )
