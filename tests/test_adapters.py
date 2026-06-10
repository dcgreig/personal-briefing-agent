import tempfile
import unittest
from pathlib import Path

from briefing_agent.adapters import (
    MockEmailAdapter,
    MockJiraAdapter,
    load_items_from_adapters,
)


class AdapterTests(unittest.TestCase):
    def test_mock_email_adapter_normalizes_email_records(self):
        adapter = MockEmailAdapter(Path("data/mock_emails.json"))

        items = adapter.load_items()

        self.assertGreater(len(items), 0)
        self.assertEqual(items[0].source_type, "email")
        self.assertEqual(items[0].source_name, "mock_email")
        self.assertEqual(items[0].item_id, "email-001")
        self.assertIn("production deploy", items[0].title)
        self.assertEqual(items[0].metadata["importance"], "high")

    def test_mock_jira_adapter_normalizes_jira_records(self):
        adapter = MockJiraAdapter(Path("data/mock_jira_tasks.json"))

        items = adapter.load_items()

        self.assertGreater(len(items), 0)
        self.assertEqual(items[0].source_type, "jira")
        self.assertEqual(items[0].source_name, "mock_jira")
        self.assertEqual(items[0].item_id, "jira-001")
        self.assertTrue(items[0].title.startswith("PBA-101:"))
        self.assertEqual(items[0].metadata["priority"], "High")

    def test_load_items_from_adapters_combines_sources(self):
        email_adapter = MockEmailAdapter(Path("data/mock_emails.json"))
        jira_adapter = MockJiraAdapter(Path("data/mock_jira_tasks.json"))

        items = load_items_from_adapters([email_adapter, jira_adapter])

        self.assertEqual(len(items), 8)
        self.assertEqual(items[0].source_type, "email")
        self.assertEqual(items[-1].source_type, "jira")

    def test_missing_mock_data_file_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = MockEmailAdapter(Path(temp_dir) / "missing.json")

            with self.assertRaises(FileNotFoundError):
                adapter.load_items()


if __name__ == "__main__":
    unittest.main()
