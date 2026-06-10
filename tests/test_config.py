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
                        'classifier_mode = "llm_assisted"',
                        "require_human_review = false",
                        'audit_log_path = "tmp/audit.jsonl"',
                        'run_history_path = "tmp/run_history.jsonl"',
                        'briefing_output_path = "tmp/briefing.txt"',
                        "lookback_hours = 12",
                        'include_sources = ["mock_email"]',
                        'exclude_sources = ["mock_jira"]',
                        'include_item_types = ["email"]',
                        'exclude_item_types = ["jira"]',
                        'include_classifications = ["urgent", "fyi"]',
                        'exclude_classifications = ["ignore"]',
                        "max_items = 5",
                    ]
                ),
                encoding="utf-8",
            )

            settings = load_settings(settings_path)

        self.assertEqual(settings.enabled_sources, ("mock_email",))
        self.assertEqual(settings.classifier_mode, "llm_assisted")
        self.assertFalse(settings.require_human_review)
        self.assertEqual(settings.audit_log_path, Path("tmp/audit.jsonl"))
        self.assertEqual(settings.run_history_path, Path("tmp/run_history.jsonl"))
        self.assertEqual(settings.briefing_output_path, Path("tmp/briefing.txt"))
        self.assertEqual(settings.lookback_hours, 12)
        self.assertEqual(settings.filters.include_sources, ("mock_email",))
        self.assertEqual(settings.filters.exclude_sources, ("mock_jira",))
        self.assertEqual(settings.filters.include_item_types, ("email",))
        self.assertEqual(settings.filters.exclude_item_types, ("jira",))
        self.assertEqual(
            settings.filters.include_classifications,
            ("urgent", "fyi"),
        )
        self.assertEqual(settings.filters.exclude_classifications, ("ignore",))
        self.assertEqual(settings.filters.max_items, 5)

    def test_default_briefing_output_path_is_markdown(self):
        self.assertEqual(
            DEFAULT_SETTINGS.briefing_output_path,
            Path("logs/daily_briefing.md"),
        )

    def test_default_run_history_path_is_jsonl(self):
        self.assertEqual(
            DEFAULT_SETTINGS.run_history_path,
            Path("logs/run_history.jsonl"),
        )

    def test_default_classifier_mode_is_rule_based(self):
        self.assertEqual(DEFAULT_SETTINGS.classifier_mode, "rule_based")

    def test_default_filters_do_not_change_behavior(self):
        self.assertEqual(DEFAULT_SETTINGS.filters.include_sources, ())
        self.assertEqual(DEFAULT_SETTINGS.filters.exclude_sources, ())
        self.assertEqual(DEFAULT_SETTINGS.filters.include_item_types, ())
        self.assertEqual(DEFAULT_SETTINGS.filters.exclude_item_types, ())
        self.assertEqual(DEFAULT_SETTINGS.filters.include_classifications, ())
        self.assertEqual(DEFAULT_SETTINGS.filters.exclude_classifications, ())
        self.assertIsNone(DEFAULT_SETTINGS.filters.max_items)

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

    def test_invalid_classifier_mode_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                'classifier_mode = "mystery_classifier"',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "classifier_mode"):
                load_settings(settings_path)

    def test_zero_max_items_means_no_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text("max_items = 0", encoding="utf-8")

            settings = load_settings(settings_path)

        self.assertIsNone(settings.filters.max_items)

    def test_invalid_filter_classification_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                'include_classifications = ["later"]',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "include_classifications"):
                load_settings(settings_path)

    def test_invalid_filter_item_type_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.toml"
            settings_path.write_text(
                'include_item_types = ["calendar"]',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "include_item_types"):
                load_settings(settings_path)


if __name__ == "__main__":
    unittest.main()
