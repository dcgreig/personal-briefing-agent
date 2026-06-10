"""Simple, inspectable classification rules for normalized briefing items."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from briefing_agent.models import BriefingItem, ClassifierMode, Classification


ME = "me"

URGENT_KEYWORDS = (
    "urgent",
    "asap",
    "today",
    "blocked",
    "blocker",
    "production",
    "outage",
    "deadline",
)

ACTION_KEYWORDS = (
    "can you",
    "please",
    "review",
    "approve",
    "approval",
    "respond",
    "reply",
    "send",
    "need your",
)

IGNORE_KEYWORDS = (
    "unsubscribe",
    "newsletter",
    "receipt",
    "sale",
    "promotion",
    "automated report",
)


class Classifier(Protocol):
    """Interface for briefing item classifiers."""

    def classify_item(
        self,
        item: BriefingItem,
        today: date | None = None,
    ) -> Classification:
        """Classify one normalized briefing item."""

    def classify_all(self, items: list[BriefingItem]) -> list[Classification]:
        """Classify every normalized briefing item."""


class RuleBasedClassifier:
    """Deterministic classifier using local rules only."""

    def classify_item(
        self,
        item: BriefingItem,
        today: date | None = None,
    ) -> Classification:
        if item.source_type == "email":
            return _classify_email_item(item)

        if item.source_type == "jira":
            return _classify_jira_item(item, today=today)

        raise ValueError(f"Unsupported source type: {item.source_type}")

    def classify_all(self, items: list[BriefingItem]) -> list[Classification]:
        return [self.classify_item(item) for item in items]


class LlmAssistedClassifier:
    """Placeholder for a future LLM-assisted classifier."""

    def classify_item(
        self,
        item: BriefingItem,
        today: date | None = None,
    ) -> Classification:
        raise NotImplementedError(LLM_ASSISTED_NOT_IMPLEMENTED_MESSAGE)

    def classify_all(self, items: list[BriefingItem]) -> list[Classification]:
        raise NotImplementedError(LLM_ASSISTED_NOT_IMPLEMENTED_MESSAGE)


LLM_ASSISTED_NOT_IMPLEMENTED_MESSAGE = (
    "LLM-assisted classification is scaffolded but not implemented. "
    "Use classifier_mode = \"rule_based\" to run the local deterministic classifier."
)


def build_classifier(mode: ClassifierMode) -> Classifier:
    """Build the configured classifier implementation."""
    if mode == "rule_based":
        return RuleBasedClassifier()

    if mode == "llm_assisted":
        return LlmAssistedClassifier()

    raise ValueError("classifier_mode must be one of: rule_based, llm_assisted")


def classify_item(item: BriefingItem, today: date | None = None) -> Classification:
    """Classify one item with the default local rule-based classifier."""
    return RuleBasedClassifier().classify_item(item, today=today)


def classify_all(items: list[BriefingItem]) -> list[Classification]:
    """Classify every item with the default local rule-based classifier."""
    return RuleBasedClassifier().classify_all(items)


def _classify_email_item(item: BriefingItem) -> Classification:
    text = _combined_text(item.title, item.body, item.metadata.get("sender"))
    importance = _metadata_value(item, "importance", default="normal").lower()
    sender = _metadata_value(item, "sender").lower()

    if importance == "high" or _contains_any(text, URGENT_KEYWORDS):
        return Classification(
            item_id=item.item_id,
            source_type="email",
            source_name=item.source_name,
            title=item.title,
            category="urgent",
            summary=_summarize(item.body),
            reason="The email is marked high importance or includes urgent language.",
        )

    if _contains_any(text, ACTION_KEYWORDS):
        return Classification(
            item_id=item.item_id,
            source_type="email",
            source_name=item.source_name,
            title=item.title,
            category="waiting_on_me",
            summary=_summarize(item.body),
            reason="The email appears to ask for your response, review, or approval.",
        )

    if _contains_any(text, IGNORE_KEYWORDS) or "no-reply" in sender:
        return Classification(
            item_id=item.item_id,
            source_type="email",
            source_name=item.source_name,
            title=item.title,
            category="ignore",
            summary=_summarize(item.body),
            reason="The email looks automated, promotional, or low-value.",
        )

    return Classification(
        item_id=item.item_id,
        source_type="email",
        source_name=item.source_name,
        title=item.title,
        category="fyi",
        summary=_summarize(item.body),
        reason="The email has useful context but no obvious action request.",
    )


def _classify_jira_item(item: BriefingItem, today: date | None = None) -> Classification:
    today = today or date.today()
    status = _metadata_value(item, "status").lower()
    priority = _metadata_value(item, "priority").lower()
    assignee = _metadata_value(item, "assignee").lower()
    due_date = _parse_date(item.metadata.get("due_date"))
    text = _combined_text(item.title, item.body, status, priority)

    if status in {"done", "closed", "canceled", "cancelled"}:
        return Classification(
            item_id=item.item_id,
            source_type="jira",
            source_name=item.source_name,
            title=item.title,
            category="ignore",
            summary=_summarize(item.body),
            reason="The Jira task is already complete or canceled.",
        )

    if (
        priority in {"highest", "high", "critical"}
        or "blocked" in text
        or (due_date is not None and due_date <= today)
    ):
        return Classification(
            item_id=item.item_id,
            source_type="jira",
            source_name=item.source_name,
            title=item.title,
            category="urgent",
            summary=_summarize(item.body),
            reason="The Jira task is high priority, blocked, or due now.",
        )

    if assignee == ME and status in {"to do", "todo", "in progress", "reopened"}:
        return Classification(
            item_id=item.item_id,
            source_type="jira",
            source_name=item.source_name,
            title=item.title,
            category="waiting_on_me",
            summary=_summarize(item.body),
            reason="The Jira task is assigned to you and still needs work.",
        )

    if assignee != ME:
        return Classification(
            item_id=item.item_id,
            source_type="jira",
            source_name=item.source_name,
            title=item.title,
            category="fyi",
            summary=_summarize(item.body),
            reason="The Jira task is owned by someone else but may be relevant context.",
        )

    return Classification(
        item_id=item.item_id,
        source_type="jira",
        source_name=item.source_name,
        title=item.title,
        category="fyi",
        summary=_summarize(item.body),
        reason="The Jira task does not need immediate action.",
    )


def _combined_text(*parts: str | None) -> str:
    return " ".join(part or "" for part in parts).lower()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _summarize(text: str, max_length: int = 120) -> str:
    """Return a short one-line summary from mock source text."""
    summary = " ".join(text.split())
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 3].rstrip() + "..."


def _metadata_value(
    item: BriefingItem,
    key: str,
    default: str = "",
) -> str:
    return item.metadata.get(key) or default
