import unittest

from briefing_agent.filters import (
    FilterSettings,
    apply_classification_filters,
    apply_pre_classification_filters,
    build_filter_report,
    build_filter_summary,
    filters_to_dict,
)
from briefing_agent.models import BriefingItem, Classification


class FilterTests(unittest.TestCase):
    def test_default_filters_keep_everything(self):
        items = [
            _item("email-001", "email", "mock_email"),
            _item("jira-001", "jira", "mock_jira"),
        ]

        result = apply_pre_classification_filters(items, FilterSettings())

        self.assertEqual(result.items, items)
        self.assertEqual(result.source_type_removed, 0)
        self.assertEqual(result.max_items_removed, 0)

    def test_pre_classification_filters_include_and_exclude_sources(self):
        items = [
            _item("email-001", "email", "mock_email"),
            _item("jira-001", "jira", "mock_jira"),
        ]

        result = apply_pre_classification_filters(
            items,
            FilterSettings(include_sources=("mock_email",)),
        )

        self.assertEqual([item.item_id for item in result.items], ["email-001"])
        self.assertEqual(result.source_type_removed, 1)

    def test_pre_classification_filters_item_types_and_max_items(self):
        items = [
            _item("email-001", "email", "mock_email"),
            _item("email-002", "email", "mock_email"),
            _item("jira-001", "jira", "mock_jira"),
        ]

        result = apply_pre_classification_filters(
            items,
            FilterSettings(include_item_types=("email",), max_items=1),
        )

        self.assertEqual([item.item_id for item in result.items], ["email-001"])
        self.assertEqual(result.source_type_removed, 1)
        self.assertEqual(result.max_items_removed, 1)

    def test_classification_filters_include_and_exclude_categories(self):
        classifications = [
            _classification("email-001", "urgent"),
            _classification("email-002", "fyi"),
            _classification("email-003", "ignore"),
        ]

        result = apply_classification_filters(
            classifications,
            FilterSettings(
                include_classifications=("urgent", "fyi"),
                exclude_classifications=("fyi",),
            ),
        )

        self.assertEqual(
            [classification.item_id for classification in result.classifications],
            ["email-001"],
        )
        self.assertEqual(result.classification_removed, 2)

    def test_filter_summary_and_report_count_removed_items(self):
        settings = FilterSettings(max_items=1, exclude_classifications=("ignore",))
        pre_result = apply_pre_classification_filters(
            [
                _item("email-001", "email", "mock_email"),
                _item("email-002", "email", "mock_email"),
            ],
            settings,
        )
        classification_result = apply_classification_filters(
            [_classification("email-001", "ignore")],
            settings,
        )

        summary = build_filter_summary(
            starting_count=2,
            pre_result=pre_result,
            classification_result=classification_result,
            settings=settings,
        )
        report = build_filter_report(summary)

        self.assertEqual(summary.total_removed, 2)
        self.assertIn("Removed by max_items: 1", report)
        self.assertIn("Removed by classification filters: 1", report)

    def test_filters_to_dict_is_json_friendly(self):
        settings = FilterSettings(
            include_sources=("mock_email",),
            exclude_classifications=("ignore",),
            max_items=5,
        )

        data = filters_to_dict(settings)

        self.assertEqual(data["include_sources"], ["mock_email"])
        self.assertEqual(data["exclude_classifications"], ["ignore"])
        self.assertEqual(data["max_items"], 5)


def _item(item_id: str, source_type: str, source_name: str) -> BriefingItem:
    return BriefingItem(
        item_id=item_id,
        source_type=source_type,
        source_name=source_name,
        title=f"{item_id} title",
        body="Body text.",
        metadata={},
    )


def _classification(item_id: str, category: str) -> Classification:
    return Classification(
        item_id=item_id,
        source_type="email",
        source_name="mock_email",
        title=f"{item_id} title",
        category=category,
        summary="A short summary.",
        reason="A short reason.",
    )


if __name__ == "__main__":
    unittest.main()
