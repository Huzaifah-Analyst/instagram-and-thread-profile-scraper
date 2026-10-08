"""Live results table with status colouring (TSK-203).

Uses a dark-styled ``ttk.Treeview`` (CustomTkinter has no table widget).
Treeview colours whole rows, so each row is tinted by its status badge colour.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from src.core.records import threads_joined
from src.gui import theme

COLUMNS = (
    ("idx", "#", 40, "center"),
    ("username", "Username", 130, "w"),
    ("status", "Status", 90, "center"),
    ("ig_country", "IG Country", 95, "w"),
    ("ig_joined", "IG Joined", 105, "w"),
    ("threads_country", "Threads Country", 110, "w"),
    ("threads_joined", "Threads Joined", 125, "w"),
    ("duration", "Duration", 65, "e"),
)
TREE_STYLE = "MetaInspector.Treeview"


def record_to_row(position: int, record: dict) -> tuple[str, ...]:
    """Converts a scraper record into table cell strings.

    Args:
        position: 1-based row number.
        record: Record from ``MultiWorkerScraper``.

    Returns:
        Cell values in ``COLUMNS`` order.
    """
    seconds = record.get("seconds")
    return (
        f"{position:02d}",
        f"@{record.get('username', '')}",
        theme.display_status(record),
        theme.cell(record.get("ig_country")),
        theme.cell(record.get("ig_date_joined")),
        theme.cell(record.get("threads_country")),
        threads_joined(record),
        "N/A" if seconds is None else f"{float(seconds):.1f}s",  # history runs store no timing
    )


class DataTable(ctk.CTkFrame):
    """Scrollable, colour-coded results grid."""

    def __init__(self, master: ctk.CTkBaseClass, title: str = "Live Results") -> None:
        """Builds the table inside a surface-coloured frame.

        Args:
            master: Parent widget.
            title: Heading shown above the table.
        """
        super().__init__(master, fg_color=theme.BG_SURFACE, corner_radius=8)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 8))
        ctk.CTkLabel(header, text=title, font=theme.FONT_SECTION,
                     text_color=theme.TEXT_PRIMARY).pack(side="left")
        self._summary = ctk.CTkLabel(header, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_MUTED)
        self._summary.pack(side="right")

        self._configure_style()
        self.tree = ttk.Treeview(self, columns=[c[0] for c in COLUMNS], show="headings",
                                 style=TREE_STYLE, selectmode="extended")
        for key, title, width, anchor in COLUMNS:
            self.tree.heading(key, text=title, anchor=anchor)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=key != "idx")
        for status, (fg, bg) in theme.STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=fg, background=bg)

        scrollbar = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(14, 0), pady=(0, 14))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(2, 8), pady=(0, 14))

        self._counts: dict[str, int] = {}
        self.records: list[dict] = []

    def clear(self) -> None:
        """Removes all rows."""
        self.tree.delete(*self.tree.get_children())
        self.records.clear()
        self._counts.clear()
        self._summary.configure(text="")

    def set_records(self, records: list[dict]) -> None:
        """Replaces the table contents (used by the history viewer)."""
        self.clear()
        for record in records:
            self.add_record(record)
        children = self.tree.get_children()
        if children:
            self.tree.see(children[0])

    def add_record(self, record: dict) -> None:
        """Appends one finished account and scrolls it into view."""
        self.records.append(record)
        values = record_to_row(len(self.records), record)
        status = values[2]
        item = self.tree.insert("", "end", values=values, tags=(status,))
        self.tree.see(item)
        self._counts[status] = self._counts.get(status, 0) + 1
        self._summary.configure(text="   ".join(f"{k}: {v}" for k, v in sorted(self._counts.items())))

    def _configure_style(self) -> None:
        """Applies the Cyber Dark palette to the ttk Treeview."""
        style = ttk.Style(self)
        style.theme_use("clam")  # the only built-in theme that honours custom colours
        style.configure(TREE_STYLE, background=theme.BG_ELEVATED, fieldbackground=theme.BG_ELEVATED,
                        foreground=theme.TEXT_PRIMARY, rowheight=30, borderwidth=0, font=theme.TTK_FONT_BODY)
        style.configure(f"{TREE_STYLE}.Heading", background=theme.BG_DARK, foreground=theme.TEXT_MUTED,
                        relief="flat", borderwidth=0, font=theme.TTK_FONT_HEADING)
        style.map(f"{TREE_STYLE}.Heading", background=[("active", theme.BORDER_COLOR)])
        style.map(TREE_STYLE, background=[("selected", theme.ACCENT_HOVER)],
                  foreground=[("selected", theme.TEXT_PRIMARY)])
        style.layout(TREE_STYLE, [("Treeview.treearea", {"sticky": tk.NSEW})])  # drop the light border
