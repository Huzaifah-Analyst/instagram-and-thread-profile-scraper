"""Shared helpers for turning scraper records into table / sheet / file rows.

A *record* is the flat dict produced by ``build_record()`` in
``src/core/scraper.py``. The clipboard, CSV/Excel exporters, history
database and GUI all format records through this module so every output
agrees on status labels and missing-value text.
"""

from __future__ import annotations

from typing import Callable, Optional

MISSING = "N/A"

# Cells starting with these are run as formulas by Excel / Google Sheets.
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def display_status(record: dict) -> str:
    """Returns the user-facing status label for a record.

    The engine reports a private Instagram account as composite ``ACTIVE``
    with ``ig_status == "private"``; users see that as ``PRIVATE``.

    Args:
        record: Scraper record.

    Returns:
        ``ACTIVE``, ``PRIVATE``, ``BANNED``, ``NOT_FOUND``, ``BLOCKED`` or ``ERROR``.
    """
    status = record.get("composite_status") or "ERROR"
    if status == "ACTIVE" and record.get("ig_status") == "private":
        return "PRIVATE"
    return status


def text_or_missing(value: Optional[object]) -> str:
    """Formats an optional value; ``None`` / empty becomes ``N/A``."""
    if value is None or value == "":
        return MISSING
    return str(value)


def threads_joined(record: dict) -> str:
    """Threads joined date with its badge appended, e.g. ``Sep 2023 · 100M+``."""
    joined = text_or_missing(record.get("threads_date_joined"))
    badge = record.get("threads_badge")
    return f"{joined} · {badge}" if badge else joined


def safe_cell(value: str, formula_guard: bool = True) -> str:
    """Neutralises spreadsheet formula injection and in-cell line breaks.

    Values come from third-party pages, so a country or error text such as
    ``=HYPERLINK(...)`` must never execute when pasted or opened. A leading
    apostrophe makes Sheets/Excel treat the cell as plain text.

    Args:
        value: Cell text.
        formula_guard: Add the apostrophe. The Excel exporter turns this off
            because it stores every cell with an explicit text type instead.

    Returns:
        Text that is safe to paste into a sheet or write to CSV/Excel.
    """
    cleaned = " ".join(value.replace("\t", " ").splitlines()).strip()
    if formula_guard and cleaned.startswith(_FORMULA_PREFIXES):
        return "'" + cleaned
    return cleaned


def _seconds(record: dict) -> str:
    """Per-account duration, or ``N/A`` when unknown (e.g. runs loaded from history)."""
    seconds = record.get("seconds")
    return MISSING if seconds is None else f"{float(seconds):.1f}"


Column = tuple[str, Callable[[dict], str]]


def error_text(record: dict) -> str:
    """Why a row has no data (e.g. ``IG options (...) button not found``), or empty."""
    return str(record.get("error_message") or "")


# Google Sheets clipboard layout: docs/architecture.md §6 plus an Error column,
# so a row with N/A data can be told apart from one that failed.
SHEET_COLUMNS: tuple[Column, ...] = (
    ("Username", lambda r: str(r.get("username", ""))),
    ("Status", display_status),
    ("IG Country", lambda r: text_or_missing(r.get("ig_country"))),
    ("IG Joined", lambda r: text_or_missing(r.get("ig_date_joined"))),
    ("Threads Country", lambda r: text_or_missing(r.get("threads_country"))),
    ("Threads Joined", threads_joined),
    ("Error", error_text),
)

# CSV / Excel layout: the sheet columns plus per-platform status and timing.
EXPORT_COLUMNS: tuple[Column, ...] = SHEET_COLUMNS + (
    ("IG Status", lambda r: text_or_missing(r.get("ig_status"))),
    ("Threads Status", lambda r: text_or_missing(r.get("threads_status"))),
    ("Seconds", _seconds),
)


def to_rows(records: list[dict], columns: tuple[Column, ...], formula_guard: bool = True) -> list[list[str]]:
    """Builds a header row plus one sanitised row per record.

    Args:
        records: Scraper records.
        columns: ``SHEET_COLUMNS`` or ``EXPORT_COLUMNS``.
        formula_guard: Passed to ``safe_cell``.

    Returns:
        ``[header, row1, row2, ...]`` with every cell passed through ``safe_cell``.
    """
    rows = [[name for name, _ in columns]]
    for record in records:
        rows.append([safe_cell(fmt(record), formula_guard) for _, fmt in columns])
    return rows
