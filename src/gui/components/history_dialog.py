"""Run History viewer (TSK-304).

Lists past runs from ``history.db``; selecting one loads its records into a
results table that can be re-copied to Google Sheets or exported, without
re-running anything.
"""

from __future__ import annotations

import logging
import sqlite3
from tkinter import ttk
from typing import Optional

import customtkinter as ctk

from src.core.history_db import HistoryDB
from src.gui import theme
from src.gui.actions import copy_to_clipboard, export_records
from src.gui.components.data_table import TREE_STYLE, DataTable

logger = logging.getLogger(__name__)

RUN_COLUMNS = (
    ("created_at", "Date", 160, "w"),
    ("mode", "Mode", 140, "w"),
    ("total_accounts", "Total", 70, "e"),
    ("active_count", "Active", 70, "e"),
    ("banned_count", "Banned", 70, "e"),
    ("duration", "Duration", 90, "e"),
)


def run_to_row(run: dict) -> tuple[str, ...]:
    """Formats a ``runs`` row for the run list."""
    return (
        str(run["created_at"]),
        theme.MODE_LABELS.get(run["mode"], str(run["mode"])),
        str(run["total_accounts"]),
        str(run["active_count"]),
        str(run["banned_count"]),
        theme.format_duration(run["duration_seconds"] or 0),
    )


class HistoryDialog(ctk.CTkToplevel):
    """Window listing past runs and their results."""

    def __init__(self, master: ctk.CTkBaseClass, history: HistoryDB) -> None:
        """Builds the dialog and loads the run list.

        Args:
            master: Main window.
            history: Open history database.
        """
        super().__init__(master, fg_color=theme.BG_DARK)
        self.title("Run History")
        self.geometry("1000x640")
        self.minsize(800, 500)
        self.transient(master)
        self.history = history
        self.records: list[dict] = []
        self._run_ids: dict[str, str] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        ctk.CTkLabel(self, text="Past Runs", font=theme.FONT_SECTION, text_color=theme.TEXT_PRIMARY
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        # The details table configures the shared Treeview style, so build it first.
        self.details = DataTable(self, title="Run Details")
        self.runs_tree = ttk.Treeview(self, columns=[c[0] for c in RUN_COLUMNS], show="headings",
                                      style=TREE_STYLE, selectmode="browse", height=6)
        for key, title, width, anchor in RUN_COLUMNS:
            self.runs_tree.heading(key, text=title, anchor=anchor)
            self.runs_tree.column(key, width=width, anchor=anchor)
        self.runs_tree.grid(row=1, column=0, sticky="nsew", padx=16)
        self.runs_tree.bind("<<TreeviewSelect>>", lambda _e: self._load_selected())
        self.details.grid(row=2, column=0, sticky="nsew", padx=16, pady=(12, 0))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        self.copy_button = ctk.CTkButton(actions, text="📋  Copy for Google Sheets", command=self._copy,
                                         fg_color=theme.ACCENT_BLUE, hover_color=theme.ACCENT_HOVER,
                                         font=theme.FONT_BODY)
        self.copy_button.pack(side="left")
        for label, kind in (("Export CSV", "csv"), ("Export Excel", "xlsx")):
            ctk.CTkButton(actions, text=label, width=110, command=lambda k=kind: self._export(k),
                          fg_color=theme.BG_ELEVATED, hover_color=theme.BORDER_COLOR,
                          font=theme.FONT_BODY).pack(side="left", padx=(8, 0))
        self._status = ctk.CTkLabel(actions, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_MUTED)
        self._status.pack(side="right")

        self.refresh()
        self.after(50, self.lift)

    def refresh(self) -> None:
        """Reloads the run list and selects the newest run."""
        self.runs_tree.delete(*self.runs_tree.get_children())
        self._run_ids.clear()
        try:
            runs = self.history.list_runs()
        except sqlite3.Error as exc:
            logger.error("Could not read run history: %s", exc)
            self._status.configure(text=f"Could not read history: {exc}", text_color=theme.STATUS_BANNED)
            return
        for run in runs:
            item = self.runs_tree.insert("", "end", values=run_to_row(run))
            self._run_ids[item] = run["run_id"]
        if runs:
            first = self.runs_tree.get_children()[0]
            self.runs_tree.selection_set(first)
            self._load_selected()
        else:
            self._status.configure(text="No runs yet. Finished runs appear here automatically.")

    @property
    def selected_run_id(self) -> Optional[str]:
        """``run_id`` of the selected run, if any."""
        selection = self.runs_tree.selection()
        return self._run_ids.get(selection[0]) if selection else None

    def _load_selected(self) -> None:
        """Shows the selected run's records."""
        run_id = self.selected_run_id
        if run_id is None:
            return
        try:
            self.records = self.history.get_run_items(run_id)
        except sqlite3.Error as exc:
            logger.error("Could not load run %s: %s", run_id, exc)
            self._status.configure(text=f"Could not load run: {exc}", text_color=theme.STATUS_BANNED)
            return
        self.details.set_records(self.records)
        self._status.configure(text=f"{run_id} · {len(self.records)} accounts", text_color=theme.TEXT_MUTED)

    def _copy(self) -> None:
        """Copies the selected run to the clipboard."""
        if copy_to_clipboard(self, self.records):
            self.copy_button.configure(text="✓  Copied!")
            self.after(2000, lambda: self.copy_button.winfo_exists()
                       and self.copy_button.configure(text="📋  Copy for Google Sheets"))

    def _export(self, kind: str) -> None:
        """Exports the selected run, named after its run id."""
        export_records(self, self.records, kind, default_name=self.selected_run_id)
