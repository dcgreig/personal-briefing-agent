"""Local filters for briefing items and finalized classifications."""

from __future__ import annotations

from dataclasses import dataclass

from briefing_agent.models import BriefingItem, Category, Classification


@dataclass(frozen=True)
class FilterSettings:
    include_sources: tuple[str, ...] = ()
    exclude_sources: tuple[str, ...] = ()
    include_item_types: tuple[str, ...] = ()
    exclude_item_types: tuple[str, ...] = ()
    include_classifications: tuple[Category, ...] = ()
    exclude_classifications: tuple[Category, ...] = ()
    max_items: int | None = None


@dataclass(frozen=True)
class FilterSummary:
    starting_count: int
    after_source_type_filters: int
    after_max_items: int
    after_classification_filters: int
    source_type_removed: int
    max_items_removed: int
    classification_removed: int
    settings: FilterSettings

    @property
    def total_removed(self) -> int:
        return (
            self.source_type_removed
            + self.max_items_removed
            + self.classification_removed
        )


@dataclass(frozen=True)
class PreClassificationFilterResult:
    items: list[BriefingItem]
    source_type_removed: int
    max_items_removed: int


@dataclass(frozen=True)
class ClassificationFilterResult:
    classifications: list[Classification]
    classification_removed: int


def apply_pre_classification_filters(
    items: list[BriefingItem],
    settings: FilterSettings,
) -> PreClassificationFilterResult:
    """Apply local source, type, and max item filters before classification."""
    source_type_filtered = [
        item
        for item in items
        if _included(item.source_name, settings.include_sources)
        and not _excluded(item.source_name, settings.exclude_sources)
        and _included(item.source_type, settings.include_item_types)
        and not _excluded(item.source_type, settings.exclude_item_types)
    ]

    if settings.max_items is None:
        max_filtered = source_type_filtered
    else:
        max_filtered = source_type_filtered[: settings.max_items]

    return PreClassificationFilterResult(
        items=max_filtered,
        source_type_removed=len(items) - len(source_type_filtered),
        max_items_removed=len(source_type_filtered) - len(max_filtered),
    )


def apply_classification_filters(
    classifications: list[Classification],
    settings: FilterSettings,
) -> ClassificationFilterResult:
    """Apply local final-classification filters after human review."""
    filtered = [
        classification
        for classification in classifications
        if _included(classification.category, settings.include_classifications)
        and not _excluded(
            classification.category,
            settings.exclude_classifications,
        )
    ]
    return ClassificationFilterResult(
        classifications=filtered,
        classification_removed=len(classifications) - len(filtered),
    )


def build_filter_summary(
    starting_count: int,
    pre_result: PreClassificationFilterResult,
    classification_result: ClassificationFilterResult,
    settings: FilterSettings,
) -> FilterSummary:
    """Combine filter counts for terminal, Markdown, and history output."""
    return FilterSummary(
        starting_count=starting_count,
        after_source_type_filters=(
            starting_count - pre_result.source_type_removed
        ),
        after_max_items=len(pre_result.items),
        after_classification_filters=len(classification_result.classifications),
        source_type_removed=pre_result.source_type_removed,
        max_items_removed=pre_result.max_items_removed,
        classification_removed=classification_result.classification_removed,
        settings=settings,
    )


def build_filter_report(summary: FilterSummary) -> str:
    """Build a friendly terminal note about local filters."""
    lines = [
        "",
        "Filters Applied",
        "===============",
        f"Starting items: {summary.starting_count}",
        f"After source/type filters: {summary.after_source_type_filters}",
        f"After max_items: {summary.after_max_items}",
        f"After classification filters: {summary.after_classification_filters}",
        f"Total removed: {summary.total_removed}",
    ]

    if summary.total_removed == 0:
        lines.append("No items were removed by filters.")
    else:
        if summary.source_type_removed:
            lines.append(
                f"Removed by source/type filters: {summary.source_type_removed}"
            )
        if summary.max_items_removed:
            lines.append(f"Removed by max_items: {summary.max_items_removed}")
        if summary.classification_removed:
            lines.append(
                "Removed by classification filters: "
                f"{summary.classification_removed}"
            )

    return "\n".join(lines)


def filters_to_dict(settings: FilterSettings) -> dict[str, object]:
    """Convert filter settings to JSON-friendly values."""
    return {
        "include_sources": list(settings.include_sources),
        "exclude_sources": list(settings.exclude_sources),
        "include_item_types": list(settings.include_item_types),
        "exclude_item_types": list(settings.exclude_item_types),
        "include_classifications": list(settings.include_classifications),
        "exclude_classifications": list(settings.exclude_classifications),
        "max_items": settings.max_items,
    }


def _included(value: str, allowed_values: tuple[str, ...]) -> bool:
    return not allowed_values or value in allowed_values


def _excluded(value: str, blocked_values: tuple[str, ...]) -> bool:
    return value in blocked_values
