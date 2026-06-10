import tempfile
import unittest
from pathlib import Path

from briefing_agent.config import DEFAULT_SETTINGS, load_settings


class ConfigTests(unittest.TestCase):
    def test_missing_settings_file_uses_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = load_settings(Path(temp_dir) / "missing.toml")

        self.assertEqual(settings, DEFAULT_SETTINGS)

    def test_settings_file_overrides_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                "\n".join(
                    [
                        'enabled_sources = ["mock_email"]',
                        "require_human_review = false",
                        'audit_log_path = "tmp/audit.jsonl"',
                        'briefing_output_path = "tmp/briefing.txt"',
                        "lookback_hours = 12",
                    ]
                ),
                encoding="utf-8",
            )

            settings = load_settings(settings_path)

        self.assertEqual(settings.enabled_sources, ("mock_email",))
        self.assertFalse(settings.require_human_review)
        self.assertEqual(settings.audit_log_path, Path("tmp/audit.jsonl"))
        self.assertEqual(settings.briefing_output_path, Path("tmp/briefing.txt"))
        self.assertEqual(settings.lookback_hours, 12)

    def test_empty_briefing_output_path_disables_file_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                "\n".join(
                    [
                        'enabled_sources = ["mock_email", "mock_jira"]',
                        "require_human_review = true",
                        'audit_log_path = "logs/audit.jsonl"',
                        'briefing_output_path = ""',
                        "lookback_hours = 24",
                    ]
                ),
                encoding="utf-8",
            )

            settings = load_settings(settings_path)

        self.assertIsNone(settings.briefing_output_path)

    def test_invalid_lookback_hours_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text("lookback_hours = 0", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_settings(settings_path)


if __name__ == "__main__":
    unittest.main()
