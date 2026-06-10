import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from json import dumps
from pathlib import Path
from unittest.mock import patch

from briefing_agent.cli import main
from briefing_agent.review import accept_all_classifications


class CliTests(unittest.TestCase):
    def test_llm_assisted_mode_exits_with_clear_message(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                "\n".join(
                    [
                        'enabled_sources = ["mock_email"]',
                        'classifier_mode = "llm_assisted"',
                        "require_human_review = false",
                        'audit_log_path = "logs/audit.jsonl"',
                        'run_history_path = "logs/run_history.jsonl"',
                        'briefing_output_path = ""',
                        "lookback_hours = 24",
                    ]
                ),
                encoding="utf-8",
            )

            with patch(
                "sys.argv",
                ["briefing-agent", "--config", str(settings_path)],
            ):
                with self.assertRaisesRegex(
                    SystemExit,
                    "LLM-assisted classification is scaffolded but not implemented",
                ):
                    main()

    def test_no_review_flag_accepts_all_and_writes_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audit_path = temp_path / "logs" / "audit.jsonl"
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            briefing_path = temp_path / "logs" / "daily_briefing.md"
            settings_path = _write_settings(
                temp_path,
                audit_path,
                run_history_path,
                briefing_path,
            )

            with patch(
                "sys.argv",
                ["briefing-agent", "--config", str(settings_path), "--no-review"],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            self.assertTrue(audit_path.exists())
            self.assertTrue(run_history_path.exists())
            self.assertTrue(briefing_path.exists())
            self.assertIn(
                "Human review skipped by config or --no-review.",
                output.getvalue(),
            )

    def test_run_subcommand_preserves_no_review_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audit_path = temp_path / "logs" / "audit.jsonl"
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            briefing_path = temp_path / "logs" / "daily_briefing.md"
            settings_path = _write_settings(
                temp_path,
                audit_path,
                run_history_path,
                briefing_path,
            )

            with patch(
                "sys.argv",
                [
                    "briefing-agent",
                    "run",
                    "--config",
                    str(settings_path),
                    "--no-review",
                ],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            self.assertTrue(audit_path.exists())
            self.assertTrue(run_history_path.exists())
            self.assertTrue(briefing_path.exists())
            self.assertIn("Daily Briefing", output.getvalue())

    def test_interactive_confirmation_can_cancel_before_writing_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audit_path = temp_path / "logs" / "audit.jsonl"
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            briefing_path = temp_path / "logs" / "daily_briefing.md"
            settings_path = _write_settings(
                temp_path,
                audit_path,
                run_history_path,
                briefing_path,
            )

            with patch(
                "sys.argv",
                ["briefing-agent", "--config", str(settings_path)],
            ):
                with patch(
                    "briefing_agent.cli.review_classifications",
                    side_effect=accept_all_classifications,
                ):
                    with patch("briefing_agent.cli.confirm_review", return_value=False):
                        with redirect_stdout(StringIO()) as output:
                            main()

            self.assertFalse(audit_path.exists())
            self.assertFalse(run_history_path.exists())
            self.assertFalse(briefing_path.exists())
            self.assertIn("Run cancelled before writing outputs.", output.getvalue())

    def test_history_subcommand_prints_recent_runs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            settings_path = _write_settings(
                temp_path,
                temp_path / "logs" / "audit.jsonl",
                run_history_path,
                temp_path / "logs" / "daily_briefing.md",
            )
            _write_history(run_history_path, ["run-1", "run-2"])

            with patch(
                "sys.argv",
                ["briefing-agent", "history", "--config", str(settings_path)],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            text = output.getvalue()
            self.assertIn("Briefing Run History", text)
            self.assertIn("Run ID: run-2", text)
            self.assertIn("Run ID: run-1", text)

    def test_history_subcommand_handles_missing_history_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings_path = _write_settings(
                temp_path,
                temp_path / "logs" / "audit.jsonl",
                temp_path / "logs" / "missing_history.jsonl",
                temp_path / "logs" / "daily_briefing.md",
            )

            with patch(
                "sys.argv",
                ["briefing-agent", "history", "--config", str(settings_path)],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            self.assertIn("No run history found yet", output.getvalue())

    def test_show_run_subcommand_prints_one_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            settings_path = _write_settings(
                temp_path,
                temp_path / "logs" / "audit.jsonl",
                run_history_path,
                temp_path / "logs" / "daily_briefing.md",
            )
            _write_history(run_history_path, ["run-1", "run-2"])

            with patch(
                "sys.argv",
                ["briefing-agent", "show-run", "run-1", "--config", str(settings_path)],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            text = output.getvalue()
            self.assertIn("Briefing Run", text)
            self.assertIn("Run ID: run-1", text)
            self.assertNotIn("Run ID: run-2", text)

    def test_show_run_subcommand_handles_missing_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            settings_path = _write_settings(
                temp_path,
                temp_path / "logs" / "audit.jsonl",
                run_history_path,
                temp_path / "logs" / "daily_briefing.md",
            )
            _write_history(run_history_path, ["run-1"])

            with patch(
                "sys.argv",
                [
                    "briefing-agent",
                    "show-run",
                    "missing-run",
                    "--config",
                    str(settings_path),
                ],
            ):
                with redirect_stdout(StringIO()) as output:
                    main()

            self.assertIn("No run found for run_id: missing-run", output.getvalue())


def _write_settings(
    temp_path: Path,
    audit_path: Path,
    run_history_path: Path,
    briefing_path: Path,
) -> Path:
    settings_path = temp_path / "settings.toml"
    settings_path.write_text(
        "\n".join(
            [
                'enabled_sources = ["mock_email"]',
                'classifier_mode = "rule_based"',
                "require_human_review = true",
                f'audit_log_path = "{_toml_path(audit_path)}"',
                f'run_history_path = "{_toml_path(run_history_path)}"',
                f'briefing_output_path = "{_toml_path(briefing_path)}"',
                "lookback_hours = 24",
            ]
        ),
        encoding="utf-8",
    )
    return settings_path


def _write_history(path: Path, run_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [_history_record(run_id) for run_id in run_ids]
    path.write_text(
        "\n".join(dumps(record, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def _history_record(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "generated_at": "2026-06-10T12:00:00+00:00",
        "enabled_sources": ["mock_email"],
        "total_item_count": 4,
        "counts_by_classification": {
            "urgent": 1,
            "waiting_on_me": 1,
            "fyi": 1,
            "ignore": 1,
        },
        "briefing_output_path": "logs/daily_briefing.md",
        "audit_log_path": "logs/audit.jsonl",
    }


def _toml_path(path: Path) -> str:
    return str(path).replace("\\", "/")


if __name__ == "__main__":
    unittest.main()
