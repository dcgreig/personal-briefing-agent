import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
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
            settings_path = temp_path / "settings.toml"
            audit_path = temp_path / "logs" / "audit.jsonl"
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            briefing_path = temp_path / "logs" / "daily_briefing.md"
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

    def test_interactive_confirmation_can_cancel_before_writing_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            settings_path = temp_path / "settings.toml"
            audit_path = temp_path / "logs" / "audit.jsonl"
            run_history_path = temp_path / "logs" / "run_history.jsonl"
            briefing_path = temp_path / "logs" / "daily_briefing.md"
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


def _toml_path(path: Path) -> str:
    return str(path).replace("\\", "/")


if __name__ == "__main__":
    unittest.main()
