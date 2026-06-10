import json
import unittest
from pathlib import Path

from briefing_agent.models import BriefingItem


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class OutlookPlanFixtureTests(unittest.TestCase):
    def test_sample_outlook_fixture_parses_as_briefing_item(self):
        data = json.loads(
            (FIXTURES_DIR / "sample_outlook_briefing_item.json").read_text(
                encoding="utf-8"
            )
        )

        item = BriefingItem(**data)

        self.assertEqual(item.item_id, "outlook-message-001")
        self.assertEqual(item.source_type, "email")
        self.assertEqual(item.source_name, "outlook_email")
        self.assertEqual(item.title, "Can you review the launch plan?")
        self.assertIn("review the launch plan", item.body)
        self.assertEqual(item.metadata["sender"], "teammate@example.com")
        self.assertEqual(item.metadata["folder"], "Inbox")
        self.assertEqual(item.metadata["is_read"], "false")

    def test_sample_outlook_fixture_has_required_metadata_fields(self):
        data = json.loads(
            (FIXTURES_DIR / "sample_outlook_briefing_item.json").read_text(
                encoding="utf-8"
            )
        )

        required_metadata = {
            "sender",
            "sender_name",
            "received_at",
            "importance",
            "is_read",
            "folder",
        }

        self.assertTrue(required_metadata.issubset(data["metadata"]))


if __name__ == "__main__":
    unittest.main()
