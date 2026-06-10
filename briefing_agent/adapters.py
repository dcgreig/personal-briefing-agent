"""Local-only source adapters that produce normalized briefing items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from briefing_agent.models import BriefingItem


class BriefingSourceAdapter(Protocol):
    """A source that can load normalized briefing items."""

    name: str

    def load_items(self) -> list[BriefingItem]:
        """Load source records and normalize them for classification."""


# TODO: A future Outlook adapter should use Microsoft Graph read-only
# permissions only. It should not send, archive, delete, label, or modify mail.
class MockEmailAdapter:
    """Reads mock work email records from a local JSON file."""

    name = "mock_email"

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_items(self) -> list[BriefingItem]:
        records = _load_json_array(self.path)
        return [_email_record_to_item(record, self.name) for record in records]


class MockJiraAdapter:
    """Reads mock Jira task records from a local JSON file."""

    name = "mock_jira"

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_items(self) -> list[BriefingItem]:
        records = _load_json_array(self.path)
        return [_jira_record_to_item(record, self.name) for record in records]


def load_items_from_adapters(
    adapters: list[BriefingSourceAdapter],
) -> list[BriefingItem]:
    """Load and combine normalized items from every configured adapter."""
    items: list[BriefingItem] = []
    for adapter in adapters:
        items.extend(adapter.load_items())
    return items


def _email_record_to_item(record: dict, source_name: str) -> BriefingItem:
    return BriefingItem(
        item_id=record["id"],
        source_type="email",
        source_name=source_name,
        title=record["subject"],
        body=record["body"],
        metadata={
            "sender": record.get("sender"),
            "received_at": record.get("received_at"),
            "importance": record.get("importance", "normal"),
        },
    )


def _jira_record_to_item(record: dict, source_name: str) -> BriefingItem:
    return BriefingItem(
        item_id=record["id"],
        source_type="jira",
        source_name=source_name,
        title=f"{record['key']}: {record['title']}",
        body=record["description"],
        metadata={
            "key": record.get("key"),
            "assignee": record.get("assignee"),
            "reporter": record.get("reporter"),
            "status": record.get("status"),
            "priority": record.get("priority"),
            "due_date": record.get("due_date"),
        },
    )


def _load_json_array(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Could not find data file: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected {path} to contain a JSON array")

    return data
