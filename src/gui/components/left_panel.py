"""Left control panel: username input, .txt import, mode selector, run controls (TSK-202)."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from src.core.scraper import MODE_COMBINED, MODE_IG_ONLY, MODE_THREADS_ONLY, clean_usernames
from src.gui import theme
from src.gui.bridge import RunState

logger = logging.getLogger(__name__)

MODE_LABELS = (
    (MODE_COMBINED, "Combined (IG + Threads)"),
    (MODE_IG_ONLY, "Instagram Only"),
    (MODE_THREADS_ONLY, "Threads Only"),
)


class LeftPanel(ctk.CTkFrame):
    """Collects usernames and mode, and exposes Start / Pause / Stop."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_start: Callable[[], None],
        on_pause_toggle: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        """Builds the panel.

        Args:
            master: Parent widget.
            on_start: Called when Start is clicked.
            on_pause_toggle: Called when Pause/Resume is clicked.
            on_stop: Called when Stop is clicked.
        """
        super().__init__(master, width=theme.LEFT_PANEL_WIDTH, fg_color=theme.BG_SURFACE, corner_radius=0)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        ctk.CTkLabel(header, text="Input Usernames", font=theme.FONT_SECTION,
                     text_color=theme.TEXT_PRIMARY).pack(side="left")
        self._count_label = ctk.CTkLabel(header, text="0 accounts", font=theme.FONT_CAPTION,
                                         text_color=theme.TEXT_MUTED)
        self._count_label.pack(side="right")

        self.textbox = ctk.CTkTextbox(self, font=theme.FONT_BODY, fg_color=theme.BG_ELEVATED,
                                      border_color=theme.BORDER_COLOR, border_width=1,
                                      text_color=theme.TEXT_PRIMARY)
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=16)
        self.textbox.bind("<KeyRelease>", lambda _e: self._refresh_count())
        self.textbox.bind("<<Paste>>", lambda _e: self.after(10, self._refresh_count))

        self.import_button = ctk.CTkButton(self, text="📁  Load .txt File", command=self._import_file,
                                           fg_color=theme.BG_ELEVATED, hover_color=theme.BORDER_COLOR,
                                           border_color=theme.BORDER_COLOR, border_width=1, font=theme.FONT_BODY)
        self.import_button.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))

        ctk.CTkLabel(self, text="Checking Mode", font=theme.FONT_SECTION,
                     text_color=theme.TEXT_PRIMARY).grid(row=3, column=0, sticky="w", padx=16, pady=(0, 6))
        self.mode_var = ctk.StringVar(value=MODE_COMBINED)
        self._mode_buttons: list[ctk.CTkRadioButton] = []
        for row, (value, label) in enumerate(MODE_LABELS, start=4):
            button = ctk.CTkRadioButton(self, text=label, value=value, variable=self.mode_var,
                                        font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY,
                                        fg_color=theme.ACCENT_BLUE, hover_color=theme.ACCENT_HOVER)
            button.grid(row=row, column=0, sticky="w", padx=20, pady=3)
            self._mode_buttons.append(button)

        ctk.CTkLabel(self, text="Controls", font=theme.FONT_SECTION,
                     text_color=theme.TEXT_PRIMARY).grid(row=7, column=0, sticky="w", padx=16, pady=(16, 6))
        self.start_button = ctk.CTkButton(self, text="▶  Start Checking", command=on_start, height=38,
                                          fg_color=theme.ACCENT_BLUE, hover_color=theme.ACCENT_HOVER,
                                          font=theme.FONT_SECTION)
        self.start_button.grid(row=8, column=0, sticky="ew", padx=16)

        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.grid(row=9, column=0, sticky="ew", padx=16, pady=(8, 16))
        row_frame.grid_columnconfigure((0, 1), weight=1)
        self.pause_button = ctk.CTkButton(row_frame, text="❚❚  Pause", command=on_pause_toggle,
                                          fg_color=theme.BG_ELEVATED, hover_color=theme.BORDER_COLOR,
                                          font=theme.FONT_BODY)
        self.pause_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.stop_button = ctk.CTkButton(row_frame, text="■  Stop", command=on_stop,
                                         fg_color=theme.BG_ELEVATED, hover_color="#7F1D1D",
                                         font=theme.FONT_BODY)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.apply_state(RunState.IDLE)

    def usernames(self) -> list[str]:
        """Returns the cleaned, de-duplicated usernames from the textbox."""
        return clean_usernames(self.textbox.get("1.0", "end").splitlines())

    @property
    def mode(self) -> str:
        """Selected checking mode."""
        return self.mode_var.get()

    def apply_state(self, state: RunState, start_allowed: bool = True) -> None:
        """Enables/disables controls for the given run state.

        Args:
            state: Current bridge state.
            start_allowed: ``False`` while something else (e.g. login) owns the profile.
        """
        idle = state is RunState.IDLE
        self.start_button.configure(state="normal" if idle and start_allowed else "disabled")
        self.pause_button.configure(
            state="normal" if state in (RunState.RUNNING, RunState.PAUSED) else "disabled",
            text="▶  Resume" if state is RunState.PAUSED else "❚❚  Pause",
        )
        self.stop_button.configure(state="normal" if state in (RunState.RUNNING, RunState.PAUSED) else "disabled")
        input_state = "normal" if idle else "disabled"
        self.textbox.configure(state=input_state)
        self.import_button.configure(state=input_state)
        for button in self._mode_buttons:
            button.configure(state=input_state)

    def _import_file(self) -> None:
        """Loads a .txt file of usernames into the textbox."""
        path = filedialog.askopenfilename(title="Select usernames file",
                                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            logger.error("Could not read %s: %s", path, exc)
            self._count_label.configure(text="Could not read file", text_color=theme.STATUS_BANNED)
            return
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "\n".join(clean_usernames(text.splitlines())))
        self._refresh_count()

    def _refresh_count(self) -> None:
        """Updates the "N accounts" caption."""
        self._count_label.configure(text=f"{len(self.usernames())} accounts", text_color=theme.TEXT_MUTED)
