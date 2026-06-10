import unittest

from briefing_agent.models import Classification
from briefing_agent.review import (
    accept_all_classifications,
    build_review_summary,
    confirm_review,
    review_classifications,
)


class ReviewTests(unittest.TestCase):
    def test_review_accepts_suggested_classification(self):
        classification = _classification(category="urgent")

        decisions = review_classifications(
            [classification],
            input_func=_input_from([""]),
            output_func=lambda message: None,
        )

        self.assertEqual(decisions[0].final_category, "urgent")
        self.assertFalse(decisions[0].changed)

    def test_review_allows_category_override(self):
        classification = _classification(category="urgent")

        decisions = review_classifications(
            [classification],
            input_func=_input_from(["fyi"]),
            output_func=lambda message: None,
        )

        self.assertEqual(decisions[0].final_category, "fyi")
        self.assertTrue(decisions[0].changed)

    def test_review_reprompts_for_invalid_category(self):
        classification = _classification(category="urgent")
        messages: list[str] = []

        decisions = review_classifications(
            [classification],
            input_func=_input_from(["later", "ignore"]),
            output_func=messages.append,
        )

        self.assertEqual(decisions[0].final_category, "ignore")
        self.assertTrue(decisions[0].changed)
        self.assertIn("Please choose", messages[-1])

    def test_review_allows_shortcut_override(self):
        classification = _classification(category="urgent")

        decisions = review_classifications(
            [classification],
            input_func=_input_from(["w"]),
            output_func=lambda message: None,
        )

        self.assertEqual(decisions[0].final_category, "waiting_on_me")
        self.assertTrue(decisions[0].changed)

    def test_review_allows_skipping_for_now(self):
        classification = _classification(category="urgent")

        decisions = review_classifications(
            [classification],
            input_func=_input_from(["s"]),
            output_func=lambda message: None,
        )

        self.assertEqual(decisions[0].final_category, "urgent")
        self.assertFalse(decisions[0].changed)
        self.assertTrue(decisions[0].skipped)

    def test_accept_all_classifications_skips_prompting(self):
        classification = _classification(category="waiting_on_me")

        decisions = accept_all_classifications([classification])

        self.assertEqual(decisions[0].final_category, "waiting_on_me")
        self.assertFalse(decisions[0].changed)
        self.assertFalse(decisions[0].skipped)

    def test_review_output_shows_action_suggestion_context(self):
        classification = _classification(category="waiting_on_me")
        messages: list[str] = []

        review_classifications(
            [classification],
            input_func=_input_from([""]),
            output_func=messages.append,
        )

        self.assertIn("Item 1 of 1", messages)
        self.assertIn("Source: mock_email", messages)
        self.assertIn("Type: email", messages)
        self.assertIn("Title: Example email", messages)
        self.assertIn("Classification: waiting_on_me", messages)
        self.assertIn("Reason: A short reason.", messages)
        self.assertIn("Suggested dry-run action: reply", messages)
        self.assertTrue(
            any(
                message.startswith("Suggested action rationale:")
                for message in messages
            )
        )

    def test_build_review_summary_counts_decisions(self):
        accepted = accept_all_classifications([_classification(category="urgent")])[0]
        changed = review_classifications(
            [_classification(category="waiting_on_me")],
            input_func=_input_from(["fyi"]),
            output_func=lambda message: None,
        )[0]
        skipped = review_classifications(
            [_classification(category="ignore")],
            input_func=_input_from(["skip"]),
            output_func=lambda message: None,
        )[0]

        summary = build_review_summary([accepted, changed, skipped])

        self.assertIn("Total items: 3", summary)
        self.assertIn("Accepted: 1", summary)
        self.assertIn("Changed: 1", summary)
        self.assertIn("Skipped for now: 1", summary)
        self.assertIn("- Urgent: 1", summary)
        self.assertIn("- FYI: 1", summary)
        self.assertIn("- Ignore: 1", summary)

    def test_confirm_review_accepts_yes(self):
        decisions = accept_all_classifications([_classification(category="urgent")])

        confirmed = confirm_review(
            decisions,
            input_func=_input_from(["yes"]),
            output_func=lambda message: None,
        )

        self.assertTrue(confirmed)

    def test_confirm_review_rejects_default_response(self):
        decisions = accept_all_classifications([_classification(category="urgent")])

        confirmed = confirm_review(
            decisions,
            input_func=_input_from([""]),
            output_func=lambda message: None,
        )

        self.assertFalse(confirmed)


def _classification(category: str) -> Classification:
    return Classification(
        item_id="email-001",
        source_type="email",
        source_name="mock_email",
        title="Example email",
        category=category,
        summary="A short summary.",
        reason="A short reason.",
    )


def _input_from(responses: list[str]):
    iterator = iter(responses)

    def input_func(prompt: str) -> str:
        return next(iterator)

    return input_func


if __name__ == "__main__":
    unittest.main()
