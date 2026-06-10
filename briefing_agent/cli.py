"""Command-line entry point for the personal briefing agent."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from briefing_agent.adapters import (
    MockEmailAdapter,
    MockJiraAdapter,
    load_items_from_adapters,
)
from briefing_agent.audit import append_audit_log
from briefing_agent.briefing import build_briefing, build_markdown_briefing
from briefing_agent.classifier import classify_all
from briefing_agent.config import Settings, load_settings
from briefing_agent.review import accept_all_classifications, review_classifications
from briefing_agent.run_history import append_run_history


SOURCE_ADAPTERS = {
    "mock_email": lambda data_dir: MockEmailAdapter(data_dir / "mock_emails.json"),
    "mock_jira": lambda data_dir: MockJiraAdapter(data_dir / "mock_jira_tasks.json"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local daily briefing.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing mock_emails.json and mock_jira_tasks.json.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/settings.toml"),
        help="Local TOML settings file.",
    )
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=None,
        help="Override the JSONL audit log path from settings.",
    )
    args = parser.parse_args()
    settings = load_settings(args.config)
    run_id = uuid4().hex
    generated_at = datetime.now(timezone.utc)
    audit_log_path = args.audit_log or settings.audit_log_path

    adapters = build_source_adapters(settings, args.data_dir)
    items = load_items_from_adapters(adapters)
    classifications = classify_all(items)
    briefing = build_briefing(classifications, run_id, generated_at)
    markdown_briefing = build_markdown_briefing(
        classifications,
        run_id,
        generated_at,
    )

    print(briefing)
    write_briefing_output(markdown_briefing, settings.briefing_output_path)

    if settings.require_human_review:
        reviewed_items = review_classifications(classifications)
    else:
        reviewed_items = accept_all_classifications(classifications)
        print("\nHuman review skipped by config.")

    append_audit_log(reviewed_items, audit_log_path, run_id, generated_at)
    append_run_history(
        settings.run_history_path,
        run_id,
        generated_at,
        settings.enabled_sources,
        classifications,
        settings.briefing_output_path,
        audit_log_path,
    )
    print(f"\nAudit log written to {audit_log_path}")
    print(f"Run history written to {settings.run_history_path}")
    if settings.briefing_output_path is not None:
        print(f"Briefing output written to {settings.briefing_output_path}")


def build_source_adapters(settings: Settings, data_dir: Path):
    adapters = []
    for source_name in settings.enabled_sources:
        if source_name not in SOURCE_ADAPTERS:
            raise ValueError(f"Unknown source in settings: {source_name}")
        adapters.append(SOURCE_ADAPTERS[source_name](data_dir))
    return adapters


def write_briefing_output(briefing: str, path: Path | None) -> None:
    if path is None:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(briefing + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
