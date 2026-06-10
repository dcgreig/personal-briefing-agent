import unittest

from briefing_agent.actions import suggest_action, suggest_actions
from briefing_agent.models import Classification, ReviewDecision


class ActionSuggestionTests(unittest.TestCase):
    def test_ignored_item_suggests_no_action(self):
        suggestion = suggest_action(_review_decision("email", "ignore"))

        self.assertEqual(suggestion.action_type, "no_action")
        self.assertFalse(suggestion.requires_human_approval)

    def test_fyi_item_suggests_review(self):
        suggestion = suggest_action(_review_decision("jira", "fyi"))

        self.assertEqual(suggestion.action_type, "review")
        self.assertFalse(suggestion.requires_human_approval)

    def test_email_waiting_on_me_suggests_reply(self):
        suggestion = suggest_action(_review_decision("email", "waiting_on_me"))

        self.assertEqual(suggestion.action_type, "reply")
        self.assertTrue(suggestion.requires_human_approval)

    def test_urgent_jira_item_suggests_follow_up(self):
        suggestion = suggest_action(_review_decision("jira", "urgent"))

        self.assertEqual(suggestion.action_type, "follow_up")
        self.assertTrue(suggestion.requires_human_approval)

    def test_waiting_on_me_jira_item_suggests_update_task(self):
        suggestion = suggest_action(_review_decision("jira", "waiting_on_me"))

        self.assertEqual(suggestion.action_type, "update_task")
        self.assertTrue(suggestion.requires_human_approval)

    def test_suggest_actions_returns_one_suggestion_per_reviewed_item(self):
        reviewed_items = [
            _review_decision("email", "urgent"),
            _review_decision("jira", "ignore"),
        ]

        suggestions = suggest_actions(reviewed_items)

        self.assertEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0].item_id, reviewed_items[0].original.item_id)
        self.assertEqual(suggestions[1].item_id, reviewed_items[1].original.item_id)


def _review_decision(source_type: str, final_category: str) -> ReviewDecision:
    return ReviewDecision(
        original=Classification(
            item_id=f"{source_type}-{final_category}",
            source_type=source_type,
            source_name=f"mock_{source_type}",
            title="Example item",
            category="fyi",
            summary="A short summary.",
            reason="A short reason.",
        ),
        final_category=final_category,
        changed=final_category != "fyi",
    )


if __name__ == "__main__":
    unittest.main()
