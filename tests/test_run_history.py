import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from briefing_agent.models import Classification
from briefing_agent.run_history import (
    append_run_history,
    build_history_report,
    build_run_report,
    find_run,
    load_run_history,
)


class RunHistoryTests(unittest.TestCase):
    def test_run_history_writes_one_record_for_cli_run(self):
        classifications = [
            _classification("email-001", "email", "mock_email", "urgent"),
            _classification("jira-001", "jira", "mock_jira", "waiting_on_me"),
            _classification("email-002", "email", "mock_email", "fyi"),
            _classification("jira-002", "jira", "mock_jira", "ignore"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "nested" / "run_history.jsonl"

            append_run_history(
                path=history_path,
                run_id="run-123",
                generated_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
                enabled_sources=("mock_email", "mock_jira"),
                classifications=classifications,
                briefing_output_path=Path("logs/daily_briefing.md"),
                audit_log_path=Path("logs/audit.jsonl"),
            )

            records = [
                json.loads(line)
                for line in history_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["run_id"], "run-123")
        self.assertEqual(records[0]["generated_at"], "2026-06-10T12:00:00+00:00")
        self.assertEqual(records[0]["enabled_sources"], ["mock_email", "mock_jira"])
        self.assertEqual(records[0]["total_item_count"], 4)
        self.assertEqual(records[0]["counts_by_classification"]["urgent"], 1)
        self.assertEqual(records[0]["counts_by_classification"]["waiting_on_me"], 1)
        self.assertEqual(records[0]["counts_by_classification"]["fyi"], 1)
        self.assertEqual(records[0]["counts_by_classification"]["ignore"], 1)
        self.assertEqual(
            records[0]["briefing_output_path"],
            "logs\\daily_briefing.md",
        )
        self.assertEqual(records[0]["audit_log_path"], "logs\\audit.jsonl")

    def test_load_run_history_reads_jsonl_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "run_history.jsonl"
            history_path.write_text(
                "\n".join(
                    [
                        '{"run_id": "run-1", "total_item_count": 1}',
                        "",
                        '{"run_id": "run-2", "total_item_count": 2}',
                    ]
                ),
                encoding="utf-8",
            )

            records = load_run_history(history_path)

        self.assertEqual([record["run_id"] for record in records], ["run-1", "run-2"])

    def test_find_run_returns_matching_record(self):
        records = [{"run_id": "run-1"}, {"run_id": "run-2"}]

        record = find_run(records, "run-2")

        self.assertEqual(record, {"run_id": "run-2"})
        self.assertIsNone(find_run(records, "missing"))

    def test_build_history_report_shows_recent_runs(self):
        report = build_history_report(
            [
                _history_record("old-run"),
                _history_record("new-run"),
            ],
            limit=1,
        )

        self.assertIn("Briefing Run History", report)
        self.assertIn("Run ID: new-run", report)
        self.assertNotIn("Run ID: old-run", report)
        self.assertIn("Counts: urgent=1, waiting_on_me=2, fyi=3, ignore=4", report)

    def test_build_history_report_handles_empty_history(self):
        report = build_history_report([])

        self.assertIn("No briefing runs found yet.", report)

    def test_build_run_report_shows_single_run_details(self):
        report = build_run_report(_history_record("run-123"))

        self.assertIn("Briefing Run", report)
        self.assertIn("Run ID: run-123", report)
        self.assertIn("Audit log: logs/audit.jsonl", report)


def _classification(
    item_id: str,
    source_type: str,
    source_name: str,
    category: str,
) -> Classification:
    return Classification(
        item_id=item_id,
        source_type=source_type,
        source_name=source_name,
        title=f"{item_id} title",
        category=category,
        summary="A short summary.",
        reason="A short reason.",
    )


def _history_record(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "generated_at": "2026-06-10T12:00:00+00:00",
        "enabled_sources": ["mock_email", "mock_jira"],
        "total_item_count": 10,
        "counts_by_classification": {
            "urgent": 1,
            "waiting_on_me": 2,
            "fyi": 3,
            "ignore": 4,
        },
        "briefing_output_path": "logs/daily_briefing.md",
        "audit_log_path": "logs/audit.jsonl",
    }


if __name__ == "__main__":
    unittest.main()
