"""Validation helpers for the future LLM classifier contract."""

from __future__ import annotations

from typing import Any

from briefing_agent.models import Category


ALLOWED_LLM_CLASSIFICATIONS: tuple[Category, ...] = (
    "urgent",
    "waiting_on_me",
    "fyi",
    "ignore",
)
ALLOWED_UNCERTAINTY_LEVELS = {"low", "medium", "high"}
REQUIRED_LLM_OUTPUT_FIELDS = {
    "item_id",
    "classification",
    "rationale",
    "confidence",
    "uncertainty",
}


def validate_llm_classifier_output(output: dict[str, Any]) -> None:
    """Validate one future LLM classifier output object.

    This function validates local JSON data only. It does not call a model or
    any external service.
    """
    missing_fields = REQUIRED_LLM_OUTPUT_FIELDS - set(output)
    if missing_fields:
        raise ValueError(
            "LLM classifier output is missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    _validate_non_empty_string(output["item_id"], "item_id")
    _validate_classification(output["classification"])
    _validate_non_empty_string(output["rationale"], "rationale")
    _validate_confidence(output["confidence"])
    _validate_uncertainty(output["uncertainty"])


def _validate_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_classification(value: Any) -> None:
    if value not in ALLOWED_LLM_CLASSIFICATIONS:
        raise ValueError(
            "classification must be one of: "
            + ", ".join(ALLOWED_LLM_CLASSIFICATIONS)
        )


def _validate_confidence(value: Any) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError("confidence must be a number from 0.0 to 1.0")

    if value < 0.0 or value > 1.0:
        raise ValueError("confidence must be a number from 0.0 to 1.0")


def _validate_uncertainty(value: Any) -> None:
    if value not in ALLOWED_UNCERTAINTY_LEVELS:
        raise ValueError("uncertainty must be one of: low, medium, high")
