"""Main MetaInspector Desktop window (TSK-201) wiring the panels to the engine and history."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from src.core.history_db import HistoryDB
from src.core.scraper import MODE_COMBINED, MultiWorkerScraper, login_session
from src.core.session import SESSION_CONNECTED, SESSION_UNKNOWN, check_session
from src.gui import theme
from src.gui.actions import copy_to_clipboard, export_records
from src.gui.bridge import ErrorEvent, FinishedEvent, ProgressEvent, RunState, ScraperBridge, ScraperFactory
from src.gui.components.data_table import DataTable
from src.gui.components.history_dialog import HistoryDialog
from src.gui.components.left_panel import LeftPanel
from src.gui.components.status_bar import StatusBar

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_DIR = PROJECT_ROOT / "browser_profile"
DEFAULT_HISTORY_PATH = PROJECT_ROOT / "history.db"
POLL_INTERVAL_MS = 100


class MetaInspectorApp(ctk.CTk):
    """Top-level window: header, left control panel, live table, status bar."""

    def __init__(self, profile_dir: Path = DEFAULT_PROFILE_DIR,
                 scraper_factory: Optional[ScraperFactory] = None,
                 history_path: Path = DEFAULT_HISTORY_PATH) -> None:
        """Builds the window.

        Args:
            profile_dir: Chromium profile holding the checker login.
            scraper_factory: Override for tests; defaults to a headless
                ``MultiWorkerScraper`` on ``profile_dir``.
            history_path: SQLite file for run history (created if missing).
        """
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=theme.BG_DARK)
        self.title("MetaInspector Desktop")
        self.geometry("{}x{}".format(*theme.WINDOW_SIZE))
        self.minsize(*theme.WINDOW_MIN_SIZE)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.profile_dir = profile_dir
        self.bridge = ScraperBridge(scraper_factory or self._default_factory)
        self._login_thread: Optional[threading.Thread] = None
        self._login_error: Optional[str] = None
        self._total = 0
        self._done = 0
        self._run_mode = MODE_COMBINED
        self._run_started = datetime.now()
        self._history_dialog: Optional[HistoryDialog] = None
        self._history_error: Optional[str] = None
        try:
            self.history: Optional[HistoryDB] = HistoryDB(history_path)
        except (sqlite3.Error, OSError) as exc:
            logger.error("History database unavailable at %s: %s", history_path, exc)
            self.history = None
            self._history_error = str(exc)

        self._build_header()
        self.left_panel = LeftPanel(self, on_start=self._on_start, on_pause_toggle=self._on_pause_toggle,
                                    on_stop=self._on_stop)
        self.left_panel.grid(row=1, column=0, sticky="nsw")
        self.table = DataTable(self)
        self.table.grid(row=1, column=1, sticky="nsew", padx=14, pady=14)
        self.status_bar = StatusBar(self, on_copy=self._on_copy, on_export_csv=lambda: self._on_export("csv"),
                                    on_export_xlsx=lambda: self._on_export("xlsx"), on_history=self._on_history)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        if self._history_error:
            self.status_bar.message(f"Run history unavailable: {self._history_error}", "error")

        self._refresh_session()
        self._apply_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_job = self.after(POLL_INTERVAL_MS, self._poll)

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #

    def _build_header(self) -> None:
        """Brand title, session indicator and Setup button."""
        header = ctk.CTkFrame(self, fg_color=theme.BG_SURFACE, corner_radius=0, height=56)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="◆  MetaInspector Desktop", font=theme.FONT_H1,
                     text_color=theme.TEXT_PRIMARY).grid(row=0, column=0, padx=16, pady=12, sticky="w")
        self._session_label = ctk.CTkLabel(header, text="", font=theme.FONT_BODY, text_color=theme.TEXT_MUTED)
        self._session_label.grid(row=0, column=1, sticky="e", padx=12)
        self.setup_button = ctk.CTkButton(header, text="⚙  Setup Checker Account", command=self._on_setup,
                                          fg_color=theme.BG_ELEVATED, hover_color=theme.BORDER_COLOR,
                                          border_color=theme.BORDER_COLOR, border_width=1, font=theme.FONT_BODY)
        self.setup_button.grid(row=0, column=2, padx=16, pady=12)

    def _default_factory(self, mode: str, callback: Callable[[int, int, dict], None]) -> MultiWorkerScraper:
        """Creates the production scraper for one run."""
        return MultiWorkerScraper(profile_dir=self.profile_dir, mode=mode, headless=True,
                                  progress_callback=callback)

    # ------------------------------------------------------------------ #
    # Controls
    # ------------------------------------------------------------------ #

    def _on_start(self) -> None:
        """Validates input and starts a run."""
        usernames = self.left_panel.usernames()
        if not usernames:
            self.status_bar.message("Paste at least one username first.", "warn")
            return
        self.table.clear()
        self._total, self._done = len(usernames), 0
        self.status_bar.set_progress(0, self._total)
        self.status_bar.set_timing(0, None)
        mode = self.left_panel.mode
        self._run_mode, self._run_started = mode, datetime.now()
        self.bridge.start(usernames, mode)
        self.status_bar.message(f"Checking {self._total} accounts ({theme.MODE_LABELS[mode]})...")
        self._apply_state()

    def _on_pause_toggle(self) -> None:
        """Pauses or resumes the active run."""
        if self.bridge.state is RunState.PAUSED:
            self.bridge.resume()
            self.status_bar.message("Resumed.")
        else:
            self.bridge.pause()
            self.status_bar.message("Paused. Workers finish their current account, then wait.", "warn")
        self._apply_state()

    def _on_stop(self) -> None:
        """Requests a stop of the active run."""
        self.bridge.stop()
        self.status_bar.message("Stopping after the current accounts finish...", "warn")
        self._apply_state()

    def _on_copy(self) -> None:
        """Copies the current results for Google Sheets (TSK-301/302)."""
        if copy_to_clipboard(self, self.table.records):
            self.status_bar.flash_copied()

    def _on_export(self, kind: str) -> None:
        """Exports the current results as CSV or Excel (TSK-305)."""
        export_records(self, self.table.records, kind)

    def _on_history(self) -> None:
        """Opens (or focuses) the Run History viewer (TSK-304)."""
        if self.history is None:
            self.status_bar.message(f"Run history unavailable: {self._history_error}", "error")
            return
        if self._history_dialog is not None and self._history_dialog.winfo_exists():
            self._history_dialog.refresh()
            self._history_dialog.focus()
            return
        self._history_dialog = HistoryDialog(self, self.history)

    def _on_setup(self) -> None:
        """Opens a visible browser for one-time checker login (TSK-205)."""
        if self.bridge.state is not RunState.IDLE or self._login_running:
            return
        self._login_error = None
        self._login_thread = threading.Thread(target=self._login_worker, name="checker-login", daemon=True)
        self._login_thread.start()
        self.status_bar.message("Log in with the checker account in the browser window, then close it.", "warn")
        self._apply_state()

    def _login_worker(self) -> None:
        """Background thread: runs the login browser until the user closes it."""
        try:
            asyncio.run(login_session(self.profile_dir))
        except Exception as exc:  # noqa: BLE001 - thread boundary: report to the UI
            logger.exception("Login browser failed")
            self._login_error = str(exc).splitlines()[0] if str(exc) else type(exc).__name__

    @property
    def _login_running(self) -> bool:
        """``True`` while the setup browser is open."""
        return self._login_thread is not None and self._login_thread.is_alive()

    # ------------------------------------------------------------------ #
    # Event loop
    # ------------------------------------------------------------------ #

    def _poll(self) -> None:
        """Drains bridge events and refreshes timers (runs every 100 ms)."""
        for event in self.bridge.poll():
            if isinstance(event, ProgressEvent):
                self._done = event.done
                self.table.add_record(event.record)
                self.status_bar.set_progress(event.done, event.total)
            elif isinstance(event, FinishedEvent):
                self._on_finished(event)
            elif isinstance(event, ErrorEvent):
                self.status_bar.message(event.message, "error")
            self._apply_state()

        if self.bridge.state is not RunState.IDLE:
            elapsed = self.bridge.elapsed
            self.status_bar.set_timing(elapsed, theme.estimate_eta(elapsed, self._done, self._total))

        if self._login_thread is not None and not self._login_thread.is_alive():
            self._login_thread = None
            if self._login_error:
                self.status_bar.message(f"Login browser failed: {self._login_error}", "error")
            else:
                self.status_bar.message("Login window closed.")
            self._refresh_session()
            self._apply_state()

        self._poll_job = self.after(POLL_INTERVAL_MS, self._poll)

    def _on_finished(self, event: FinishedEvent) -> None:
        """Saves the run to history (TSK-303) and shows the end-of-run summary."""
        self.status_bar.set_timing(event.elapsed, 0)
        checked = len(event.records)
        self._save_run(event)
        if event.stop_reason and "session blocked" in event.stop_reason.lower():
            self.status_bar.message(
                f"Stopped after {checked} accounts: Meta challenged the checker account. "
                "Use 'Setup Checker Account' to log in again.", "error")
            self._refresh_session()
        elif event.stop_reason:
            self.status_bar.message(f"{event.stop_reason}. {checked}/{self._total} accounts checked.", "warn")
        else:
            self.status_bar.message(
                f"Done: {checked} accounts in {theme.format_duration(event.elapsed)}.", "success")

    def _save_run(self, event: FinishedEvent) -> None:
        """Persists a finished (or stopped) run; failures are shown, never raised."""
        if self.history is None or not event.records:
            return
        try:
            run_id = self.history.save_run(event.records, self._run_mode, self._total, event.elapsed,
                                           created_at=self._run_started)
        except sqlite3.Error as exc:
            logger.error("Could not save run to history: %s", exc)
            self.status_bar.message(f"Run finished but could not be saved to history: {exc}", "error")
            return
        logger.info("Saved %s (%d accounts) to history", run_id, len(event.records))
        if self._history_dialog is not None and self._history_dialog.winfo_exists():
            self._history_dialog.refresh()

    def _apply_state(self) -> None:
        """Syncs button states with the bridge and login status."""
        login = self._login_running
        self.left_panel.apply_state(self.bridge.state, start_allowed=not login)
        busy = login or self.bridge.state is not RunState.IDLE
        self.setup_button.configure(state="disabled" if busy else "normal")
        self.status_bar.set_results_available(bool(self.table.records))

    def _refresh_session(self) -> None:
        """Updates the header session indicator."""
        state, detail = check_session(self.profile_dir)
        if state == SESSION_CONNECTED:
            text, color = "●  Connected", theme.STATUS_ACTIVE
        elif state == SESSION_UNKNOWN:
            text, color = f"●  {detail}", theme.STATUS_WARN
        else:
            text, color = f"●  Disconnected ({detail}) — click Setup", theme.STATUS_BANNED
        self._session_label.configure(text=text, text_color=color)

    def destroy(self) -> None:
        """Cancels the poll timer so no callback fires on a destroyed window."""
        self.after_cancel(self._poll_job)
        super().destroy()

    def _on_close(self) -> None:
        """Stops any run before closing the window."""
        if self.bridge.state is not RunState.IDLE:
            self.bridge.stop()
            self.bridge.join(timeout=10)
        self.destroy()


def main() -> None:
    """Launches the desktop application."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = MetaInspectorApp()
    app.mainloop()
