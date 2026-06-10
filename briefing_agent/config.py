"""Local settings loader for the briefing agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - used only on Python 3.10
    tomllib = None


@dataclass(frozen=True)
class Settings:
    enabled_sources: tuple[str, ...]
    require_human_review: bool
    audit_log_path: Path
    run_history_path: Path
    briefing_output_path: Path | None
    lookback_hours: int


DEFAULT_SETTINGS = Settings(
    enabled_sources=("mock_email", "mock_jira"),
    require_human_review=True,
    audit_log_path=Path("logs/audit.jsonl"),
    run_history_path=Path("logs/run_history.jsonl"),
    briefing_output_path=Path("logs/daily_briefing.md"),
    lookback_hours=24,
)


def load_settings(path: Path = Path("config/settings.toml")) -> Settings:
    """Load settings from TOML, falling back to sensible defaults."""
    if not path.exists():
        return DEFAULT_SETTINGS

    data = _load_toml(path)
    return Settings(
        enabled_sources=_read_enabled_sources(data),
        require_human_review=_read_bool(data, "require_human_review"),
        audit_log_path=_read_path(data, "audit_log_path"),
        run_history_path=_read_path(data, "run_history_path"),
        briefing_output_path=_read_optional_path(data, "briefing_output_path"),
        lookback_hours=_read_positive_int(data, "lookback_hours"),
    )


def _load_toml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(text)
    return _parse_simple_toml(text)


def _read_enabled_sources(data: dict[str, Any]) -> tuple[str, ...]:
    value = data.get("enabled_sources", DEFAULT_SETTINGS.enabled_sources)
    if not isinstance(value, list | tuple) or not all(
        isinstance(source, str) for source in value
    ):
        raise ValueError("enabled_sources must be a list of source names")
    return tuple(value)


def _read_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key, getattr(DEFAULT_SETTINGS, key))
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")
    return value


def _read_path(data: dict[str, Any], key: str) -> Path:
    value = data.get(key, getattr(DEFAULT_SETTINGS, key))
    if isinstance(value, Path):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty path string")
    return Path(value)


def _read_optional_path(data: dict[str, Any], key: str) -> Path | None:
    value = data.get(key, getattr(DEFAULT_SETTINGS, key))
    if value is None:
        return None
    if isinstance(value, Path):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a path string")
    if not value.strip():
        return None
    return Path(value)


def _read_positive_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key, getattr(DEFAULT_SETTINGS, key))
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return value


def _parse_simple_toml(text: str) -> dict[str, Any]:
    """Parse the tiny TOML subset used by config/settings.toml."""
    data: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, raw_value = line.partition("=")
        if not separator:
            raise ValueError(f"Invalid settings line: {raw_line}")
        data[key.strip()] = _parse_simple_value(raw_value.strip())
    return data


def _parse_simple_value(raw_value: str) -> Any:
    if raw_value in {"true", "false"}:
        return raw_value == "true"

    if raw_value.startswith("[") and raw_value.endswith("]"):
        inner = raw_value[1:-1].strip()
        if not inner:
            return []
        return [_parse_simple_value(part.strip()) for part in inner.split(",")]

    if raw_value.startswith('"') and raw_value.endswith('"'):
        return raw_value[1:-1]

    try:
        return int(raw_value)
    except ValueError:
        return raw_value
