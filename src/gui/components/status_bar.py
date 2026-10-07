"""Bottom status bar: progress, elapsed time, ETA and messages."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from src.gui import theme


class StatusBar(ctk.CTkFrame):
    """Shows run progress and a single-line status message."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        """Builds the progress bar and labels."""
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
        self._message.grid(row=1, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 10))

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
