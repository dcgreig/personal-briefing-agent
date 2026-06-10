from datetime import datetime, timezone
import unittest

from briefing_agent.briefing import (
    build_action_suggestions_report,
    build_briefing,
    build_markdown_briefing,
)
from briefing_agent.models import ActionSuggestion, Classification


class MarkdownBriefingTests(unittest.TestCase):
    def test_markdown_briefing_contains_required_sections_and_item_fields(self):
        classifications = [
            _classification(
                item_id="email-001",
                source_type="email",
                source_name="mock_email",
                title="Urgent email",
                category="urgent",
                reason="The email is urgent.",
            ),
            _classification(
                item_id="jira-001",
                source_type="jira",
                source_name="mock_jira",
                title="PBA-1: Follow up",
                category="waiting_on_me",
                reason="The task is assigned to you.",
            ),
            _classification(
                item_id="email-002",
                source_type="email",
                source_name="mock_email",
                title="FYI email",
                category="fyi",
                reason="The email is useful context.",
            ),
            _classification(
                item_id="jira-002",
                source_type="jira",
                source_name="mock_jira",
                title="PBA-2: Done task",
                category="ignore",
                reason="The task is already done.",
            ),
        ]
        generated_at = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)

        markdown = build_markdown_briefing(
            classifications,
            run_id="run-123",
            generated_at=generated_at,
            action_suggestions=[
                ActionSuggestion(
                    item_id="email-001",
                    action_type="reply",
                    title="Consider drafting a reply",
                    rationale="A response may be needed.",
                    requires_human_approval=True,
                )
            ],
        )

        self.assertIn("# Daily Briefing", markdown)
        self.assertIn("Run ID: run-123", markdown)
        self.assertIn("Generated: 2026-06-10T12:00:00+00:00", markdown)
        self.assertIn("## Summary Counts", markdown)
        self.assertIn("- Urgent: 1", markdown)
        self.assertIn("- Waiting On Me: 1", markdown)
        self.assertIn("- FYI: 1", markdown)
        self.assertIn("- Ignore: 1", markdown)
        self.assertIn("## Urgent Items", markdown)
        self.assertIn("## Waiting On Me Items", markdown)
        self.assertIn("## FYI Items", markdown)
        self.assertIn("## Ignored Items", markdown)
        self.assertIn("### Urgent email", markdown)
        self.assertIn("- Source: mock_email", markdown)
        self.assertIn("- Type: email", markdown)
        self.assertIn("- Classification: urgent", markdown)
        self.assertIn("- Reason: The email is urgent.", markdown)
        self.assertIn("- Suggested action: reply", markdown)
        self.assertIn("- Action title: Consider drafting a reply", markdown)
        self.assertIn("- Rationale: A response may be needed.", markdown)
        self.assertIn("- Requires human approval: true", markdown)
        self.assertIn("- Dry-run only: no action was executed.", markdown)

    def test_terminal_briefing_contains_run_id(self):
        generated_at = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)

        briefing = build_briefing(
            [_classification(
                item_id="email-001",
                source_type="email",
                source_name="mock_email",
                title="Urgent email",
                category="urgent",
                reason="The email is urgent.",
            )],
            run_id="run-123",
            generated_at=generated_at,
        )

        self.assertIn("Run ID: run-123", briefing)
        self.assertIn("Generated: 2026-06-10T12:00:00+00:00", briefing)

    def test_action_suggestions_report_is_explicitly_dry_run(self):
        classifications = [
            _classification(
                item_id="email-001",
                source_type="email",
                source_name="mock_email",
                title="Urgent email",
                category="urgent",
                reason="The email is urgent.",
            )
        ]
        suggestions = [
            ActionSuggestion(
                item_id="email-001",
                action_type="reply",
                title="Consider drafting a reply",
                rationale="A response may be needed.",
                requires_human_approval=True,
            )
        ]

        report = build_action_suggestions_report(classifications, suggestions)

        self.assertIn("Dry-Run Action Suggestions", report)
        self.assertIn("No external actions were executed.", report)
        self.assertIn("Suggested action: reply", report)
        self.assertIn("Requires human approval: true", report)


def _classification(
    item_id: str,
    source_type: str,
    source_name: str,
    title: str,
    category: str,
    reason: str,
) -> Classification:
    return Classification(
        item_id=item_id,
        source_type=source_type,
        source_name=source_name,
        title=title,
        category=category,
        summary="A short summary.",
        reason=reason,
    )


if __name__ == "__main__":
    unittest.main()
