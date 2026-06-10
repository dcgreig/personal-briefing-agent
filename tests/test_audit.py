import json
import tempfile
import unittest
from pathlib import Path

from briefing_agent.audit import append_audit_log
from briefing_agent.models import Classification, ReviewDecision


class AuditLogTests(unittest.TestCase):
    def test_audit_log_writes_one_record_per_classification(self):
        reviewed_items = [
            ReviewDecision(
                original=Classification(
                    item_id="email-001",
                    source_type="email",
                    title="Urgent email",
                    category="urgent",
                    summary="A short email summary.",
                    reason="The email has urgent language.",
                ),
                final_category="urgent",
                changed=False,
            ),
            ReviewDecision(
                original=Classification(
                    item_id="jira-001",
                    source_type="jira",
                    title="PBA-1: Review task",
                    category="waiting_on_me",
                    summary="A short Jira summary.",
                    reason="The task is assigned to you.",
                ),
                final_category="fyi",
                changed=True,
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / "audit.jsonl"

            append_audit_log(reviewed_items, audit_path)

            records = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(records), len(reviewed_items))
        self.assertEqual(
            records[0]["original_classification"]["item_id"],
            "email-001",
        )
        self.assertEqual(records[0]["final_classification"]["category"], "urgent")
        self.assertFalse(records[0]["changed"])
        self.assertEqual(
            records[1]["original_classification"]["category"],
            "waiting_on_me",
        )
        self.assertEqual(records[1]["final_classification"]["category"], "fyi")
        self.assertTrue(records[1]["changed"])
        self.assertIn("timestamp", records[0])


if __name__ == "__main__":
    unittest.main()
