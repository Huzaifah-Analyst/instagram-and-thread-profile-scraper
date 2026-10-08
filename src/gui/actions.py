"""Copy / export actions shared by the main window and the history viewer."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from src.core.clipboard import format_tsv
from src.core.export import export_csv, export_xlsx
from src.gui.components.toast import show_toast

logger = logging.getLogger(__name__)

EXPORT_KINDS = {
    "csv": (".csv", "CSV file", export_csv),
    "xlsx": (".xlsx", "Excel workbook", export_xlsx),
}


def copy_to_clipboard(widget: ctk.CTkBaseClass, records: list[dict]) -> int:
    """Copies records as Google Sheets TSV and shows the green toast.

    Args:
        widget: Any widget of the window (owns the Tk clipboard).
        records: Records to copy.

    Returns:
        Number of accounts copied (0 = nothing done).
    """
    if not records:
        return 0
    widget.clipboard_clear()
    widget.clipboard_append(format_tsv(records))
    widget.update()  # Windows only publishes the clipboard once Tk processes events
    show_toast(widget, f"Copied {len(records)} accounts to clipboard! Press Ctrl+V in Google Sheets.")
    return len(records)


def export_records(widget: ctk.CTkBaseClass, records: list[dict], kind: str,
                   default_name: Optional[str] = None) -> Optional[Path]:
    """Asks for a destination and writes records as CSV or Excel.

    Args:
        widget: Parent for the save dialog and toast.
        records: Records to export.
        kind: ``csv`` or ``xlsx``.
        default_name: Suggested file name without extension.

    Returns:
        The written path, or ``None`` if cancelled, empty or failed (a red
        toast explains failures, e.g. the file is open in Excel).
    """
    if not records:
        return None
    extension, label, writer = EXPORT_KINDS[kind]
    stem = default_name or datetime.now().strftime("metainspector_%Y%m%d_%H%M%S")
    chosen = filedialog.asksaveasfilename(
        parent=widget.winfo_toplevel(), title=f"Export {label}", defaultextension=extension,
        initialfile=stem + extension, filetypes=[(label, f"*{extension}")],
    )
    if not chosen:
        return None
    try:
        path = writer(records, chosen)
    except OSError as exc:
        logger.error("Export to %s failed: %s", chosen, exc)
        reason = exc.strerror or str(exc)
        show_toast(widget, f"Could not save {Path(chosen).name}: {reason}. Is it open in Excel?", level="error")
        return None
    show_toast(widget, f"Exported {len(records)} accounts to {path.name}")
    return path
