"""Live results table with status colouring (TSK-203).

Uses a dark-styled ``ttk.Treeview`` (CustomTkinter has no table widget).
Treeview colours whole rows, so each row is tinted by its status badge colour.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

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
    ("error", "Error", 160, "w"),
)
_STYLE = "MetaInspector.Treeview"


def record_to_row(position: int, record: dict) -> tuple[str, ...]:
    """Converts a scraper record into table cell strings.

    Args:
        position: 1-based row number.
        record: Record from ``MultiWorkerScraper``.

    Returns:
        Cell values in ``COLUMNS`` order.
    """
    joined = theme.cell(record.get("threads_date_joined"))
    if record.get("threads_badge"):
        joined = f"{joined} · {record['threads_badge']}"
    return (
        f"{position:02d}",
        f"@{record.get('username', '')}",
        theme.display_status(record),
        theme.cell(record.get("ig_country")),
        theme.cell(record.get("ig_date_joined")),
        theme.cell(record.get("threads_country")),
        joined,
        f"{float(record.get('seconds') or 0):.1f}s",
        record.get("error_message") or "",
    )


class DataTable(ctk.CTkFrame):
    """Scrollable, colour-coded results grid."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        """Builds the table inside a surface-coloured frame."""
        super().__init__(master, fg_color=theme.BG_SURFACE, corner_radius=8)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 8))
        ctk.CTkLabel(header, text="Live Results", font=theme.FONT_SECTION,
                     text_color=theme.TEXT_PRIMARY).pack(side="left")
        self._summary = ctk.CTkLabel(header, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_MUTED)
        self._summary.pack(side="right")

        self._configure_style()
        self.tree = ttk.Treeview(self, columns=[c[0] for c in COLUMNS], show="headings",
                                 style=_STYLE, selectmode="extended")
        for key, title, width, anchor in COLUMNS:
            self.tree.heading(key, text=title, anchor=anchor)
            self.tree.column(key, width=width, minwidth=40, anchor=anchor, stretch=key != "idx")
        for status, (fg, bg) in theme.STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=fg, background=bg)

        scrollbar = ctk.CTkScrollbar(self, command=self.tree.yview)
        # Columns total ~920px; at the 950px minimum window width (theme.WINDOW_MIN_SIZE)
        # the table area is well under that, so a horizontal scrollbar is required too.
        h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(14, 0), pady=(0, 0))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(2, 8), pady=(0, 0))
        h_scrollbar.grid(row=2, column=0, sticky="ew", padx=(14, 0), pady=(2, 14))

        self._counts: dict[str, int] = {}
        self.records: list[dict] = []

    def clear(self) -> None:
        """Removes all rows."""
        self.tree.delete(*self.tree.get_children())
        self.records.clear()
        self._counts.clear()
        self._summary.configure(text="")

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
        style.configure(_STYLE, background=theme.BG_ELEVATED, fieldbackground=theme.BG_ELEVATED,
                        foreground=theme.TEXT_PRIMARY, rowheight=30, borderwidth=0, font=theme.TTK_FONT_BODY)
        style.configure(f"{_STYLE}.Heading", background=theme.BG_DARK, foreground=theme.TEXT_MUTED,
                        relief="flat", borderwidth=0, font=theme.TTK_FONT_HEADING)
        style.map(f"{_STYLE}.Heading", background=[("active", theme.BORDER_COLOR)])
        style.map(_STYLE, background=[("selected", theme.ACCENT_HOVER)],
                  foreground=[("selected", theme.TEXT_PRIMARY)])
        style.layout(_STYLE, [("Treeview.treearea", {"sticky": tk.NSEW})])  # drop the light border
