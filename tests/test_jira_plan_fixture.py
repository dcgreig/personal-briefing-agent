import json
import unittest
from pathlib import Path

from briefing_agent.models import BriefingItem


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class JiraPlanFixtureTests(unittest.TestCase):
    def test_sample_jira_fixture_parses_as_briefing_item(self):
        data = json.loads(
            (FIXTURES_DIR / "sample_jira_briefing_item.json").read_text(
                encoding="utf-8"
            )
        )

        item = BriefingItem(**data)

        self.assertEqual(item.item_id, "jira-issue-10001")
        self.assertEqual(item.source_type, "jira")
        self.assertEqual(item.source_name, "jira_tasks")
        self.assertEqual(item.title, "PBA-201: Review classifier copy")
        self.assertIn("classification reasons", item.body)
        self.assertEqual(item.metadata["key"], "PBA-201")
        self.assertEqual(item.metadata["assignee"], "me")
        self.assertEqual(item.metadata["status"], "To Do")

    def test_sample_jira_fixture_has_required_metadata_fields(self):
        data = json.loads(
            (FIXTURES_DIR / "sample_jira_briefing_item.json").read_text(
                encoding="utf-8"
            )
        )

        required_metadata = {
            "key",
            "assignee",
            "assignee_display_name",
            "reporter",
            "status",
            "priority",
            "due_date",
            "updated_at",
            "issue_type",
        }

        self.assertTrue(required_metadata.issubset(data["metadata"]))


if __name__ == "__main__":
    unittest.main()
