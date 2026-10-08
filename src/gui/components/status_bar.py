"""Bottom action bar: progress, elapsed time, ETA, messages and result actions."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from src.gui import theme


COPY_LABEL = "📋  Copy for Google Sheets"
COPIED_LABEL = "✓  Copied!"
COPIED_FEEDBACK_MS = 2000


class StatusBar(ctk.CTkFrame):
    """Shows run progress, a status message and the copy/export/history actions."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_copy: Callable[[], None],
        on_export_csv: Callable[[], None],
        on_export_xlsx: Callable[[], None],
        on_history: Callable[[], None],
    ) -> None:
        """Builds the progress row, message line and action buttons.

        Args:
            master: Parent widget.
            on_copy: "Copy for Google Sheets" handler.
            on_export_csv: "Export CSV" handler.
            on_export_xlsx: "Export Excel" handler.
            on_history: "View Run History" handler.
        """
        super().__init__(master, fg_color=theme.BG_SURFACE, corner_radius=0, height=64)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Progress", font=theme.FONT_BODY,
                     text_color=theme.TEXT_MUTED).grid(row=0, column=0, padx=(16, 10), pady=(12, 2))
        self.progress = ctk.CTkProgressBar(self, height=10, progress_color=theme.ACCENT_BLUE,
                                           fg_color=theme.BG_ELEVATED)
        self.progress.grid(row=0, column=1, sticky="ew", pady=(12, 2))
        self.progress.set(0)
        self._counts = ctk.CTkLabel(self, text="0/0 (0%)", font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY)
        self._counts.grid(row=0, column=2, padx=12, pady=(12, 2))
        self._timing = ctk.CTkLabel(self, text="Elapsed: 0s | ETA: --", font=theme.FONT_CAPTION,
                                    text_color=theme.TEXT_MUTED)
        self._timing.grid(row=0, column=3, padx=(0, 16), pady=(12, 2))

        self._message = ctk.CTkLabel(self, text="Ready. Paste usernames and press Start.",
                                     font=theme.FONT_CAPTION, text_color=theme.TEXT_MUTED, anchor="w")
        self._message.grid(row=1, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 6))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 12))
        self.copy_button = ctk.CTkButton(actions, text=COPY_LABEL, command=on_copy, width=210,
                                         fg_color=theme.ACCENT_BLUE, hover_color=theme.ACCENT_HOVER,
                                         font=theme.FONT_BODY)
        self.copy_button.pack(side="left")
        secondary = {"fg_color": theme.BG_ELEVATED, "hover_color": theme.BORDER_COLOR, "font": theme.FONT_BODY}
        self.csv_button = ctk.CTkButton(actions, text="Export CSV", width=110, command=on_export_csv, **secondary)
        self.csv_button.pack(side="left", padx=(8, 0))
        self.xlsx_button = ctk.CTkButton(actions, text="Export Excel", width=110, command=on_export_xlsx,
                                         **secondary)
        self.xlsx_button.pack(side="left", padx=(8, 0))
        self.history_button = ctk.CTkButton(actions, text="📜  View Run History", width=160,
                                            command=on_history, **secondary)
        self.history_button.pack(side="left", padx=(8, 0))
        self.set_results_available(False)

    def set_results_available(self, available: bool) -> None:
        """Enables the copy/export buttons only when there are results to act on."""
        state = "normal" if available else "disabled"
        for button in (self.copy_button, self.csv_button, self.xlsx_button):
            button.configure(state=state)

    def flash_copied(self) -> None:
        """Shows "Copied!" on the copy button for 2 seconds (design.md §5)."""
        self.copy_button.configure(text=COPIED_LABEL)
        self.after(COPIED_FEEDBACK_MS, lambda: self.copy_button.configure(text=COPY_LABEL))

    def set_progress(self, done: int, total: int) -> None:
        """Updates the bar and the ``done/total (pct)`` label."""
        fraction = done / total if total else 0.0
        self.progress.set(fraction)
        self._counts.configure(text=f"{done}/{total} ({fraction:.0%})")

    def set_timing(self, elapsed: float, eta: Optional[float]) -> None:
        """Updates the elapsed / ETA caption."""
        eta_text = theme.format_duration(eta) if eta is not None else "--"
        self._timing.configure(text=f"Elapsed: {theme.format_duration(elapsed)} | ETA: {eta_text}")

    def message(self, text: str, level: str = "info") -> None:
        """Shows a status message; ``level`` is ``info``, ``success``, ``warn`` or ``error``."""
        colors = {"info": theme.TEXT_MUTED, "success": theme.STATUS_ACTIVE,
                  "warn": theme.STATUS_WARN, "error": theme.STATUS_BANNED}
        self._message.configure(text=text, text_color=colors.get(level, theme.TEXT_MUTED))
