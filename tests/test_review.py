import unittest

from briefing_agent.models import Classification
from briefing_agent.review import accept_all_classifications, review_classifications


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
        self.assertIn("Please enter one of", messages[-1])

    def test_accept_all_classifications_skips_prompting(self):
        classification = _classification(category="waiting_on_me")

        decisions = accept_all_classifications([classification])

        self.assertEqual(decisions[0].final_category, "waiting_on_me")
        self.assertFalse(decisions[0].changed)


def _classification(category: str) -> Classification:
    return Classification(
        item_id="email-001",
        source_type="email",
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
