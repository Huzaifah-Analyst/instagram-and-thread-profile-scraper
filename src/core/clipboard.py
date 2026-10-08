"""Google Sheets clipboard formatter (TSK-301).

Produces tab-separated text that Google Sheets splits into columns on a plain
Ctrl+V, with the header layout from ``docs/architecture.md`` §6.
"""

from __future__ import annotations

from src.core.records import SHEET_COLUMNS, to_rows


def format_tsv(records: list[dict], include_header: bool = True) -> str:
    """Formats records as TSV for pasting into Google Sheets.

    Args:
        records: Scraper records (``build_record()`` shape).
        include_header: Prepend the column header row.

    Returns:
        TSV text: one line per row, cells separated by tabs. Tabs and line
        breaks inside values are flattened so they cannot shift columns.
    """
    rows = to_rows(records, SHEET_COLUMNS)
    if not include_header:
        rows = rows[1:]
    return "\n".join("\t".join(row) for row in rows)
