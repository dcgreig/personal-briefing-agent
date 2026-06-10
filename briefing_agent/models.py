"""Dataclasses shared by the briefing agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Category = Literal["urgent", "waiting_on_me", "fyi", "ignore"]
SourceType = Literal["email", "jira"]


@dataclass(frozen=True)
class BriefingItem:
    item_id: str
    source_type: SourceType
    source_name: str
    title: str
    body: str
    metadata: dict[str, str | None]


@dataclass(frozen=True)
class Classification:
    item_id: str
    source_type: SourceType
    title: str
    category: Category
    summary: str
    reason: str


@dataclass(frozen=True)
class ReviewDecision:
    original: Classification
    final_category: Category
    changed: bool
