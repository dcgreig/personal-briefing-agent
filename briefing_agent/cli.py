"""Command-line entry point for the personal briefing agent."""

from __future__ import annotations

import argparse
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from briefing_agent.adapters import (
    MockEmailAdapter,
    MockJiraAdapter,
    load_items_from_adapters,
)
from briefing_agent.actions import suggest_actions
from briefing_agent.audit import append_audit_log
from briefing_agent.briefing import (
    build_action_suggestions_report,
    build_briefing,
    build_markdown_briefing,
)
from briefing_agent.classifier import build_classifier
from briefing_agent.config import Settings, load_settings
from briefing_agent.filters import (
    apply_classification_filters,
    apply_pre_classification_filters,
    build_filter_report,
    build_filter_summary,
)
from briefing_agent.review import (
    accept_all_classifications,
    confirm_review,
    finalized_classifications,
    review_classifications,
)
from briefing_agent.run_history import (
    append_run_history,
    build_history_report,
    build_run_report,
    find_run,
    load_run_history,
)


SOURCE_ADAPTERS = {
    "mock_email": lambda data_dir: MockEmailAdapter(data_dir / "mock_emails.json"),
    "mock_jira": lambda data_dir: MockJiraAdapter(data_dir / "mock_jira_tasks.json"),
}


def main() -> None:
    args = build_parser().parse_args()
    command = args.command or "run"

    if command == "run":
        run_briefing(args)
        return

    if command == "history":
        show_history(args)
        return

    if command == "show-run":
        show_run(args)
        return

    raise SystemExit(f"Unknown command: {command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local daily briefing.")
    _add_run_options(parser)
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run the local briefing workflow.",
    )
    _add_run_options(run_parser)

    history_parser = subparsers.add_parser(
        "history",
        help="Show recent local briefing runs.",
    )
    _add_config_option(history_parser)

    show_run_parser = subparsers.add_parser(
        "show-run",
        help="Show details for one local briefing run.",
    )
    _add_config_option(show_run_parser)
    show_run_parser.add_argument("run_id", help="Run id to inspect.")

    return parser


def _add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing mock_emails.json and mock_jira_tasks.json.",
    )
    _add_config_option(parser)
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=None,
        help="Override the JSONL audit log path from settings.",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip interactive review and accept all classifications.",
    )


def _add_config_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/settings.toml"),
        help="Local TOML settings file.",
    )


def run_briefing(args: Namespace) -> None:
    settings = load_settings(args.config)
    run_id = uuid4().hex
    generated_at = datetime.now(timezone.utc)
    audit_log_path = args.audit_log or settings.audit_log_path

    adapters = build_source_adapters(settings, args.data_dir)
    items = load_items_from_adapters(adapters)
    pre_filter_result = apply_pre_classification_filters(items, settings.filters)
    if pre_filter_result.source_type_removed or pre_filter_result.max_items_removed:
        print(
            "Local filters removed "
            f"{pre_filter_result.source_type_removed + pre_filter_result.max_items_removed} "
            "item(s) before classification."
        )

    classifier = build_classifier(settings.classifier_mode)
    try:
        classifications = classifier.classify_all(pre_filter_result.items)
    except NotImplementedError as error:
        raise SystemExit(str(error)) from error
    briefing = build_briefing(classifications, run_id, generated_at)

    print(briefing)

    if settings.require_human_review and not args.no_review:
        reviewed_items = review_classifications(classifications)
    else:
        reviewed_items = accept_all_classifications(classifications)
        print("\nHuman review skipped by config or --no-review.")

    all_final_classifications = finalized_classifications(reviewed_items)
    classification_filter_result = apply_classification_filters(
        all_final_classifications,
        settings.filters,
    )
    final_classifications = classification_filter_result.classifications
    filter_summary = build_filter_summary(
        len(items),
        pre_filter_result,
        classification_filter_result,
        settings.filters,
    )
    if classification_filter_result.classification_removed:
        print(
            "\nLocal classification filters removed "
            f"{classification_filter_result.classification_removed} item(s)."
        )
    print(build_filter_report(filter_summary))

    all_action_suggestions = suggest_actions(reviewed_items)
    filtered_item_ids = {
        classification.item_id for classification in final_classifications
    }
    action_suggestions = [
        suggestion
        for suggestion in all_action_suggestions
        if suggestion.item_id in filtered_item_ids
    ]
    print(build_action_suggestions_report(final_classifications, action_suggestions))

    if settings.require_human_review and not args.no_review:
        if not confirm_review(reviewed_items):
            print("\nRun cancelled before writing outputs.")
            return

    markdown_briefing = build_markdown_briefing(
        final_classifications,
        run_id,
        generated_at,
        action_suggestions,
        filter_summary,
    )
    write_briefing_output(markdown_briefing, settings.briefing_output_path)

    append_audit_log(
        reviewed_items,
        all_action_suggestions,
        audit_log_path,
        run_id,
        generated_at,
    )
    append_run_history(
        settings.run_history_path,
        run_id,
        generated_at,
        settings.enabled_sources,
        final_classifications,
        settings.briefing_output_path,
        audit_log_path,
        settings.filters,
    )
    print(f"\nAudit log written to {audit_log_path}")
    print(f"Run history written to {settings.run_history_path}")
    if settings.briefing_output_path is not None:
        print(f"Briefing output written to {settings.briefing_output_path}")


def show_history(args: Namespace) -> None:
    settings = load_settings(args.config)
    history_path = settings.run_history_path
    if not history_path.exists():
        print(f"No run history found yet at {history_path}.")
        print("Run `python -m briefing_agent.cli run` to create one.")
        return

    records = load_run_history(history_path)
    print(build_history_report(records))


def show_run(args: Namespace) -> None:
    settings = load_settings(args.config)
    history_path = settings.run_history_path
    if not history_path.exists():
        print(f"No run history found yet at {history_path}.")
        print("Run `python -m briefing_agent.cli run` to create one.")
        return

    records = load_run_history(history_path)
    record = find_run(records, args.run_id)
    if record is None:
        print(f"No run found for run_id: {args.run_id}")
        return

    print(build_run_report(record))


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
