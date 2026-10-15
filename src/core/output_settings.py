"""Validated output preferences stored beside checker settings."""

import json
import logging
from pathlib import Path

from src.core.paths import data_root
from src.core.records import Column, EXPORT_COLUMNS, SHEET_COLUMNS, text_or_missing

logger = logging.getLogger(__name__)
DEFAULT_NAMES = tuple(name for name, _ in SHEET_COLUMNS)
DIAGNOSTIC_NAMES = (
    "Data Quality", "IG Country Availability", "Threads Country Availability",
)
_COLUMN_MAP = dict(EXPORT_COLUMNS)
_COLUMN_MAP["Threads Badge"] = lambda r: text_or_missing(r.get("threads_badge"))
OUTPUT_NAMES = DEFAULT_NAMES + (
    "Threads Badge", "Data Quality", "IG Status", "Threads Status", "Seconds", "Error",
    "IG Country Availability", "Threads Country Availability",
)
OUTPUT_COLUMNS: tuple[Column, ...] = tuple((name, _COLUMN_MAP[name]) for name in OUTPUT_NAMES)


def normalize_selection(names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Keep canonical order, mandatory identity and an empty-selection fallback."""
    chosen = set(names) | {"Username"}
    if chosen == {"Username"}:
        chosen.add("Status")
    return tuple(name for name in OUTPUT_NAMES if name in chosen)


def selected_columns(names: tuple[str, ...]) -> tuple[Column, ...]:
    """Use the same selected columns for clipboard and both file formats."""
    return tuple(column for column in OUTPUT_COLUMNS
                 if column[0] in normalize_selection(names))


class OutputSettings:
    """Load preferences with a visible warning supplied to the GUI on failure."""

    def __init__(self, directory: Path | None = None) -> None:
        """Use the writable app-data root, or the caller's checker directory."""
        self.path = (directory if directory is not None else data_root()) / "output_settings.json"
        self.warning: str | None = None

    def load(self) -> tuple[str, ...]:
        """Return defaults for absent, corrupt or invalid configuration."""
        self.warning = None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            names = raw.get("columns") if isinstance(raw, dict) else None
            if (not isinstance(names, list)
                    or any(not isinstance(name, str) or name not in OUTPUT_NAMES for name in names)
                    or len(set(names)) != len(names)):
                raise ValueError("Invalid output column selection")
            return normalize_selection(names)
        except FileNotFoundError:
            return DEFAULT_NAMES
        except (OSError, UnicodeError, ValueError) as exc:
            logger.warning("Cannot load output settings: %s", exc)
            self.warning = "Output settings could not be read; default columns restored."
            return DEFAULT_NAMES

    def save(self, names: tuple[str, ...]) -> None:
        """Atomically save the normalized selection; let the GUI report failures."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"columns": normalize_selection(names)}), encoding="utf-8")
        temporary.replace(self.path)
