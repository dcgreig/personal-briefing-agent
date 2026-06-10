import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from briefing_agent.cli import main


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


if __name__ == "__main__":
    unittest.main()
