"""Wire ported result actions and persistent preferences into the desktop."""

import logging
import sqlite3
from pathlib import Path

import customtkinter as ctk

from src.core.history_db import HistoryDB
from src.core.output_settings import OutputSettings, selected_columns
from src.gui.actions import copy_to_clipboard, export_records
from src.gui.components.data_table import DataTable
from src.gui.components.history_dialog import HistoryDialog
from src.gui.components.output_dialog import OutputDialog
from src.gui.components.status_bar import StatusBar

logger = logging.getLogger(__name__)


class OutputActions:
    """Own output preferences, export callbacks and the local run history."""

    def __init__(self, master: ctk.CTkBaseClass, table: DataTable, directory: Path) -> None:
        """Prepare settings and callbacks without opening browser sessions."""
        self.master, self.table = master, table
        self.settings = OutputSettings(directory)
        self.names = self.settings.load()
        self.history_path = directory / "history.db"
        self.dialog: OutputDialog | None = None
        self.history_dialog: HistoryDialog | None = None
        self.bar = StatusBar(master, self.copy, lambda: self.export("csv"),
                             lambda: self.export("xlsx"), self.show_history, self.select_output)
        if self.settings.warning:
            self.bar.message(self.settings.warning, "warn")

    def copy(self) -> None:
        """Copy selected result columns and retain sprint3's success feedback."""
        if copy_to_clipboard(self.master, self.table.records, selected_columns(self.names)):
            self.bar.flash_copied()

    def export(self, kind: str) -> None:
        """Save exactly the selected columns, including any selected diagnostics."""
        export_records(self.master, self.table.records, kind,
                       columns=selected_columns(self.names))

    def select_output(self) -> None:
        """Open one modal draft selector at a time."""
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        self.dialog = OutputDialog(self.master, self.names, self.apply_selection)

    def apply_selection(self, names: tuple[str, ...]) -> bool:
        """Save before applying, keeping the previous selection on I/O failure."""
        try:
            self.settings.save(names)
        except OSError as exc:
            logger.error("Could not save output settings: %s", exc)
            self.bar.message("Could not save output settings; selection unchanged.", "error")
            return False
        self.names = names
        self.bar.message("Output columns saved.", "success")
        return True

    def save_run(self, records: list[dict], mode: str, total: int, elapsed: float) -> None:
        """Save final or stopped runs, without hiding persistence failures."""
        try:
            HistoryDB(self.history_path).save_run(records, mode, total, elapsed)
        except (OSError, sqlite3.Error) as exc:
            logger.error("Could not save run history: %s", exc)
            self.bar.message("Results ready, but run history could not be saved.", "warn")

    def show_history(self) -> None:
        """Open the ported history viewer with current output preferences."""
        if self.history_dialog is not None and self.history_dialog.winfo_exists():
            self.history_dialog.refresh()
            self.history_dialog.lift()
            return
        try:
            self.history_dialog = HistoryDialog(
                self.master, HistoryDB(self.history_path), lambda: self.names,
            )
        except (OSError, sqlite3.Error) as exc:
            logger.error("Could not open history: %s", exc)
            self.bar.message("Could not open run history.", "error")
