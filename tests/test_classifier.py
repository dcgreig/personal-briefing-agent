from datetime import date
import unittest

from briefing_agent.classifier import (
    LLM_ASSISTED_NOT_IMPLEMENTED_MESSAGE,
    LlmAssistedClassifier,
    RuleBasedClassifier,
    build_classifier,
    classify_item,
)
from briefing_agent.models import BriefingItem


class ClassifierTests(unittest.TestCase):
    def test_build_rule_based_classifier_mode(self):
        classifier = build_classifier("rule_based")

        self.assertIsInstance(classifier, RuleBasedClassifier)

    def test_rule_based_classifier_classifies_items(self):
        classifier = RuleBasedClassifier()
        item = _email_item(
            item_id="email-test-rule-based",
            title="Review request",
            body="Can you review this before Friday?",
        )

        result = classifier.classify_item(item)

        self.assertEqual(result.category, "waiting_on_me")

    def test_llm_assisted_classifier_mode_fails_safely(self):
        classifier = build_classifier("llm_assisted")
        item = _email_item(
            item_id="email-test-llm",
            title="Review request",
            body="Can you review this before Friday?",
        )

        with self.assertRaisesRegex(
            NotImplementedError,
            "scaffolded but not implemented",
        ):
            classifier.classify_item(item)

        self.assertIsInstance(classifier, LlmAssistedClassifier)
        self.assertIn("rule_based", LLM_ASSISTED_NOT_IMPLEMENTED_MESSAGE)

    def test_high_importance_email_is_urgent(self):
        item = _email_item(
            item_id="email-test-1",
            title="Deploy help needed",
            body="The deploy is blocked today.",
            importance="high",
        )

        result = classify_item(item)

        self.assertEqual(result.category, "urgent")
        self.assertIn("urgent", result.reason.lower())
        self.assertIn("blocked", result.summary)

    def test_email_summary_is_shortened(self):
        long_body = " ".join(["This update contains detailed background."] * 10)
        item = _email_item(
            item_id="email-test-summary",
            title="Long context update",
            body=long_body,
        )

        result = classify_item(item)

        self.assertLessEqual(len(result.summary), 120)
        self.assertTrue(result.summary.endswith("..."))

    def test_action_request_email_is_waiting_on_me(self):
        item = _email_item(
            item_id="email-test-2",
            title="Review request",
            body="Can you review this before Friday?",
        )

        result = classify_item(item)

        self.assertEqual(result.category, "waiting_on_me")

    def test_newsletter_email_is_ignored(self):
        item = _email_item(
            item_id="email-test-3",
            title="Monthly newsletter",
            body="Product tips and unsubscribe link inside.",
            importance="low",
        )

        result = classify_item(item)

        self.assertEqual(result.category, "ignore")

    def test_jira_task_due_today_is_urgent(self):
        item = _jira_item(
            item_id="jira-test-1",
            key="PBA-200",
            title="Finish launch checklist",
            body="Final checks before release.",
            assignee="me",
            status="In Progress",
            priority="Medium",
            due_date="2026-06-09",
        )

        result = classify_item(item, today=date(2026, 6, 9))

        self.assertEqual(result.category, "urgent")

    def test_jira_task_assigned_to_me_is_waiting_on_me(self):
        item = _jira_item(
            item_id="jira-test-2",
            key="PBA-201",
            title="Write onboarding notes",
            body="Create first-pass docs.",
            assignee="me",
            status="To Do",
            priority="Low",
            due_date="2026-06-30",
        )

        result = classify_item(item, today=date(2026, 6, 9))

        self.assertEqual(result.category, "waiting_on_me")

    def test_done_jira_task_is_ignored(self):
        item = _jira_item(
            item_id="jira-test-3",
            key="PBA-202",
            title="Close old ticket",
            body="Completed work.",
            assignee="me",
            status="Done",
            priority="High",
            due_date="2026-06-09",
        )

        result = classify_item(item, today=date(2026, 6, 9))

        self.assertEqual(result.category, "ignore")


def _email_item(
    item_id: str,
    title: str,
    body: str,
    importance: str = "normal",
) -> BriefingItem:
    return BriefingItem(
        item_id=item_id,
        source_type="email",
        source_name="test_email",
        title=title,
        body=body,
        metadata={
            "sender": "teammate@example.com",
            "received_at": "2026-06-09T08:00:00-04:00",
            "importance": importance,
        },
    )


def _jira_item(
    item_id: str,
    key: str,
    title: str,
    body: str,
    assignee: str,
    status: str,
    priority: str,
    due_date: str | None,
) -> BriefingItem:
    return BriefingItem(
        item_id=item_id,
        source_type="jira",
        source_name="test_jira",
        title=f"{key}: {title}",
        body=body,
        metadata={
            "key": key,
            "assignee": assignee,
            "reporter": "teammate",
            "status": status,
            "priority": priority,
            "due_date": due_date,
        },
    )


if __name__ == "__main__":
    unittest.main()
