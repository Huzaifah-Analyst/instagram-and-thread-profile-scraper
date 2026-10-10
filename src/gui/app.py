"""Main MetaInspector Desktop window (TSK-201) wiring the panels to the engine."""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from src.core.scraper import MODE_COMBINED, MODE_IG_ONLY, MultiWorkerScraper, login_session
from src.core.session import SESSION_CONNECTED, check_session
from src.core.checkers import Checker, CheckerStore
from src.core.credentials import AccountCredential
from src.core.auto_login import login_accounts
from src.core.paths import DEFAULT_PROFILE_DIR
from src.gui import theme
from src.gui.bridge import ErrorEvent, FinishedEvent, ProgressEvent, RunState, ScraperBridge, ScraperFactory
from src.gui.components.data_table import DataTable
from src.gui.components.left_panel import LeftPanel
from src.gui.components.status_bar import StatusBar
from src.gui.components.checker_dialog import CheckerDialog

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 100
MODE_NAMES = {MODE_COMBINED: "Combined", MODE_IG_ONLY: "Instagram Only"}


class MetaInspectorApp(ctk.CTk):
    """Top-level window: header, left control panel, live table, status bar."""

    def __init__(self, profile_dir: Path = DEFAULT_PROFILE_DIR,
                 scraper_factory: Optional[ScraperFactory] = None) -> None:
        """Builds the window.

        Args:
            profile_dir: Chromium profile holding the checker login.
            scraper_factory: Override for tests; defaults to a headless
                ``MultiWorkerScraper`` on ``profile_dir``.
        """
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=theme.BG_DARK)
        self.title("MetaInspector Desktop")
        self.geometry("{}x{}".format(*theme.WINDOW_SIZE))
        self.minsize(*theme.WINDOW_MIN_SIZE)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.profile_dir = profile_dir
        self.checker_store = CheckerStore(profile_dir)
        self._session_invalid = False
        self._active_login: Optional[Checker] = None
        self._checker_dialog: Optional[CheckerDialog] = None
        self.bridge = ScraperBridge(scraper_factory or self._default_factory)
        self._login_thread: Optional[threading.Thread] = None
        self._login_error: Optional[str] = None
        self._login_updates: queue.Queue[str] = queue.Queue()
        self._login_cancel = threading.Event()
        self._login_summary: Optional[str] = None
        self._total = 0
        self._done = 0

        self._build_header()
        self.left_panel = LeftPanel(self, on_start=self._on_start, on_pause_toggle=self._on_pause_toggle,
                                    on_stop=self._on_stop)
        self.left_panel.grid(row=1, column=0, sticky="nsw")
        self.table = DataTable(self)
        self.table.grid(row=1, column=1, sticky="nsew", padx=14, pady=14)
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self._refresh_session()
        self._apply_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(POLL_INTERVAL_MS, self._poll)

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
        """Creates the production scraper for one run, using the panel's worker/timeout settings."""
        return MultiWorkerScraper(
            profile_dir=self.profile_dir, mode=mode, headless=True, workers=self.left_panel.workers,
            dialog_timeout_s=self.left_panel.dialog_timeout_s,
            menu_click_timeout_s=self.left_panel.menu_click_timeout_s,
            debug_dump=self.left_panel.debug_dump, progress_callback=callback,
            checkers=[slot for slot in self.checker_store.load() if slot.enabled],
            persist_results=True,
        )

    # ------------------------------------------------------------------ #
    # Controls
    # ------------------------------------------------------------------ #

    def _on_start(self) -> None:
        """Validates input and starts a run."""
        try:
            usernames = self.left_panel.usernames()
            self.left_panel.validate_timeouts()
        except ValueError as exc:
            self.status_bar.message(str(exc), "error")
            return
        if not usernames:
            self.status_bar.message("Paste at least one username first.", "warn")
            return
        self.table.clear()
        self._total, self._done = len(usernames), 0
        self.status_bar.set_progress(0, self._total)
        self.status_bar.set_timing(0, None)
        mode = self.left_panel.mode
        try:
            self.bridge.start(usernames, mode)
        except (OSError, ValueError) as exc:
            self.status_bar.message(str(exc), "error")
            return
        self.status_bar.message("Verifying selected checker logins, then checking targets...")
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

    def _on_setup(self) -> None:
        """Open the five-slot checker account manager."""
        if self.bridge.state is not RunState.IDLE or self._login_running:
            return
        if self._checker_dialog is not None and self._checker_dialog.winfo_exists():
            self._checker_dialog.lift()
            return
        try:
            self._checker_dialog = CheckerDialog(
                self, self.checker_store, self._start_login, self._refresh_session,
                on_import=self._start_import_login,
            )
        except (OSError, ValueError) as exc:
            self.status_bar.message(f"Checker settings: {exc}", "error")

    def _start_login(self, checker: Checker) -> None:
        """Open this slot's official login tabs in the background thread."""
        if self.bridge.state is not RunState.IDLE or self._login_running:
            return
        self._active_login = checker
        self._login_error = None
        self._login_summary = None
        self._login_thread = threading.Thread(target=self._login_worker, name="checker-login", daemon=True)
        self._login_thread.start()
        self.status_bar.message(f"{checker.checker_id}: log in to BOTH Instagram and Threads tabs, then close the browser.", "warn")
        self._apply_state()

    def _start_import_login(self, accounts: list[AccountCredential], checkers: list[Checker]) -> None:
        """Keep imported secrets only in the worker's argument lifetime."""
        if self.bridge.state is not RunState.IDLE or self._login_running:
            return
        self._login_error = self._login_summary = None
        self._login_cancel.clear()
        self._login_thread = threading.Thread(
            target=self._import_login_worker, args=(accounts, checkers),
            name="checker-import-login", daemon=True,
        )
        self._login_thread.start()
        self.status_bar.message("Setting up imported accounts. Follow any manual prompts in the browser.")
        self._apply_state()

    def _import_login_worker(self, accounts: list[AccountCredential], checkers: list[Checker]) -> None:
        """Forward only sanitized login progress to the Tk thread."""
        try:
            self._login_summary = asyncio.run(login_accounts(
                accounts, checkers, self._login_cancel, self._login_updates.put,
            ))
        except Exception:  # Secret-bearing browser exceptions must not reach logs.
            self._login_error = "Account login failed. Close the setup browser and retry."

    def _login_worker(self) -> None:
        """Background thread: runs the login browser until the user closes it."""
        try:
            profile = self._active_login.profile_dir if self._active_login else self.profile_dir
            asyncio.run(login_session(profile))
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
        while True:
            try:
                self.status_bar.message(self._login_updates.get_nowait(), "warn")
            except queue.Empty:
                break
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
                self._session_invalid = False
                self.status_bar.message(self._login_summary or "Login window closed. Start will verify both selected platforms live.")
            self._refresh_session()
            self._apply_state()

        self.after(POLL_INTERVAL_MS, self._poll)

    def _on_finished(self, event: FinishedEvent) -> None:
        """Shows the end-of-run summary."""
        self.status_bar.set_timing(event.elapsed, 0)
        checked = len(event.records)
        if event.stop_reason and "session blocked" in event.stop_reason.lower():
            self._session_invalid = True
            self.status_bar.message(
                f"Stopped after {checked}: {event.stop_reason}", "error")
            self._refresh_session()
        elif event.stop_reason:
            self.status_bar.message(f"{event.stop_reason}. {checked}/{self._total} accounts checked.", "warn")
        else:
            self.status_bar.message(
                f"Done: {checked} accounts in {theme.format_duration(event.elapsed)}.", "success")

    def _apply_state(self) -> None:
        """Syncs button states with the bridge and login status."""
        login = self._login_running
        self.left_panel.apply_state(self.bridge.state, start_allowed=not login)
        busy = login or self.bridge.state is not RunState.IDLE
        self.setup_button.configure(state="disabled" if busy else "normal")

    def _refresh_session(self) -> None:
        """Show saved-login presence honestly; only preflight verifies live health."""
        try:
            selected = [slot for slot in self.checker_store.load() if slot.enabled]
            saved = sum(check_session(slot.profile_dir)[0] == SESSION_CONNECTED for slot in selected)
            text = f"{saved}/{len(selected)} IG logins saved · live check on Start"
            color = theme.TEXT_MUTED
        except (OSError, ValueError) as exc:
            text, color = f"Checker settings: {exc}", theme.STATUS_WARN
        if self._session_invalid:
            text, color = "Checker login needs attention — open Setup", theme.STATUS_BANNED
        self._session_label.configure(text=text, text_color=color)

    def _on_close(self) -> None:
        """Stops any run before closing the window."""
        self._login_cancel.set()
        if self.bridge.state is not RunState.IDLE:
            self.bridge.stop()
            self.bridge.join(timeout=10)
        self.destroy()


def main() -> None:
    """Launches the desktop application."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = MetaInspectorApp()
    app.mainloop()
