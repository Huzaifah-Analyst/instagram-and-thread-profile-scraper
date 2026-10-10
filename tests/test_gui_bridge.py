"""Tests for the scraper-to-GUI bridge, pause/stop flags, session check and the GUI shell."""

import sqlite3
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional, Iterator

import pytest

from src.gui.app import MetaInspectorApp
from src.core.checkers import CheckerStore

from src.core.scraper import MultiWorkerScraper
from src.core.session import SESSION_CONNECTED, SESSION_DISCONNECTED, _now_chrome_micros, check_session
from src.gui import theme
from src.gui.bridge import ErrorEvent, FinishedEvent, ProgressEvent, RunState, ScraperBridge
from src.gui.components.data_table import record_to_row


class FakeScraper:
    """Stands in for MultiWorkerScraper; ``gate`` lets a test hold the run open."""

    def __init__(self, mode: str, callback: Callable[[int, int, dict], None],
                 gate: Optional[threading.Event] = None, fail: bool = False) -> None:
        self.mode = mode
        self.callback = callback
        self.gate = gate
        self.fail = fail
        self.stop_reason: Optional[str] = None
        self.paused = False
        self.calls: list[str] = []

    def run(self, usernames: list[str]) -> list[dict]:
        if self.fail:
            raise RuntimeError("BrowserType.launch: Executable doesn't exist at C:\\chromium")
        records = []
        for i, name in enumerate(usernames, 1):
            if self.gate is not None:
                self.gate.wait(5)
            if self.stop_reason:
                break
            record = {"username": name, "composite_status": "ACTIVE", "ig_status": "active", "seconds": 0.1}
            records.append(record)
            self.callback(i, len(usernames), record)
        return records

    def pause(self) -> None:
        self.paused = True
        self.calls.append("pause")

    def resume(self) -> None:
        self.paused = False
        self.calls.append("resume")

    def stop(self, reason: str = "Stopped by user") -> None:
        self.stop_reason = reason
        self.calls.append("stop")


def drain(bridge: ScraperBridge, timeout: float = 5.0) -> list:
    """Polls until the run finishes, as the Tk timer would."""
    events: list = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        events += bridge.poll()
        if bridge.state is RunState.IDLE:
            return events
        time.sleep(0.01)
    raise AssertionError("bridge did not finish")


# ---- bridge --------------------------------------------------------------- #

def test_bridge_forwards_progress_then_finished() -> None:
    bridge = ScraperBridge(lambda mode, cb: FakeScraper(mode, cb))
    bridge.start(["a", "b", "c"], "combined")
    assert bridge.state is RunState.RUNNING

    events = drain(bridge)
    progress = [e for e in events if isinstance(e, ProgressEvent)]
    assert [(e.done, e.total, e.record["username"]) for e in progress] == [(1, 3, "a"), (2, 3, "b"), (3, 3, "c")]
    assert isinstance(events[-1], FinishedEvent)
    assert len(events[-1].records) == 3
    assert bridge.state is RunState.IDLE


def test_bridge_passes_mode_to_factory() -> None:
    created: list[FakeScraper] = []

    def factory(mode: str, cb: Callable) -> FakeScraper:
        created.append(FakeScraper(mode, cb))
        return created[-1]

    bridge = ScraperBridge(factory)
    bridge.start(["a"], "threads_only")
    drain(bridge)
    assert created[0].mode == "threads_only"


def test_pause_resume_stop_state_flags() -> None:
    gate = threading.Event()
    scraper: list[FakeScraper] = []
    bridge = ScraperBridge(lambda mode, cb: scraper.append(FakeScraper(mode, cb, gate)) or scraper[-1])
    bridge.start(["a", "b"], "combined")

    bridge.pause()
    assert bridge.state is RunState.PAUSED and scraper[0].paused
    bridge.pause()  # idempotent
    bridge.resume()
    assert bridge.state is RunState.RUNNING and not scraper[0].paused
    bridge.stop()
    assert bridge.state is RunState.STOPPING
    bridge.resume()  # ignored while stopping
    assert bridge.state is RunState.STOPPING

    gate.set()
    events = drain(bridge)
    assert scraper[0].calls == ["pause", "resume", "stop"]
    assert events[-1].stop_reason == "Stopped by user"


def test_controls_are_noops_when_idle() -> None:
    bridge = ScraperBridge(lambda mode, cb: FakeScraper(mode, cb))
    bridge.pause()
    bridge.resume()
    bridge.stop()
    assert bridge.state is RunState.IDLE


def test_cannot_start_twice_or_with_no_usernames() -> None:
    gate = threading.Event()
    bridge = ScraperBridge(lambda mode, cb: FakeScraper(mode, cb, gate))
    with pytest.raises(ValueError):
        bridge.start([], "combined")
    bridge.start(["a"], "combined")
    with pytest.raises(RuntimeError):
        bridge.start(["b"], "combined")
    gate.set()
    drain(bridge)
    bridge.start(["c"], "combined")  # allowed again once idle
    drain(bridge)


def test_crash_becomes_friendly_error_event() -> None:
    bridge = ScraperBridge(lambda mode, cb: FakeScraper(mode, cb, fail=True))
    bridge.start(["a"], "combined")
    events = drain(bridge)
    assert isinstance(events[-1], ErrorEvent)
    assert "playwright install chromium" in events[-1].message
    assert bridge.state is RunState.IDLE


# ---- MultiWorkerScraper control flags ------------------------------------- #

def test_scraper_pause_resume_and_stop_flags(tmp_path: Path) -> None:
    scraper = MultiWorkerScraper(profile_dir=tmp_path)
    assert not scraper.is_paused
    scraper.pause()
    assert scraper.is_paused
    scraper.resume()
    assert not scraper.is_paused
    scraper.pause()
    scraper.stop()
    assert scraper.is_stopped and not scraper.is_paused  # stop releases paused workers
    scraper.pause()
    assert not scraper.is_paused  # cannot pause a stopped run


def test_stop_before_run_is_not_lost(tmp_path: Path) -> None:
    """A stop() that races ahead of run() must still stop the run."""
    scraper = MultiWorkerScraper(profile_dir=tmp_path)
    scraper.stop()
    assert scraper.run([]) == []
    assert scraper.is_stopped


# ---- session detection ---------------------------------------------------- #

def _make_cookie_db(profile: Path, rows: list[tuple[str, str, int]]) -> None:
    db = profile / "Default" / "Network" / "Cookies"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE cookies (host_key TEXT, name TEXT, expires_utc INTEGER)")
    conn.executemany("INSERT INTO cookies VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()


def test_session_missing_profile(tmp_path: Path) -> None:
    assert check_session(tmp_path)[0] == SESSION_DISCONNECTED


def test_session_connected(tmp_path: Path) -> None:
    _make_cookie_db(tmp_path, [(".instagram.com", "sessionid", _now_chrome_micros() + 10**12)])
    assert check_session(tmp_path)[0] == SESSION_CONNECTED


def test_session_expired_or_absent(tmp_path: Path) -> None:
    _make_cookie_db(tmp_path, [(".instagram.com", "sessionid", _now_chrome_micros() - 10**9),
                               (".instagram.com", "csrftoken", _now_chrome_micros() + 10**12)])
    assert check_session(tmp_path) == (SESSION_DISCONNECTED, "Session expired")


# ---- display helpers ------------------------------------------------------ #

def test_display_status_shows_private() -> None:
    assert theme.display_status({"composite_status": "ACTIVE", "ig_status": "private"}) == "PRIVATE"
    assert theme.display_status({"composite_status": "BANNED", "ig_status": "banned"}) == "BANNED"
    assert theme.display_status({}) == "ERROR"


def test_record_to_row() -> None:
    record = {"username": "elif", "composite_status": "ACTIVE", "ig_status": "active", "ig_country": "Turkey",
              "ig_date_joined": "Sep 2026", "threads_date_joined": "Sep 2026", "threads_badge": "100M+",
              "seconds": 2.44}
    assert record_to_row(1, record) == ("01", "@elif", "ACTIVE", "Unknown", "", "Turkey", "Sep 2026", "N/A",
                                        "Sep 2026 · 100M+", "2.4s", "")


def test_record_to_row_surfaces_error_message() -> None:
    """An operator must be able to see *why* a row has no data (ISSUE_concurrent_session_detection.md)."""
    record = {"username": "elif", "composite_status": "ACTIVE", "ig_status": "active",
              "seconds": 8.1, "error_message": "IG about dialog did not load within timeout"}
    row = record_to_row(1, record)
    assert row[-1] == "IG about dialog did not load within timeout"


def test_record_to_row_collapses_a_multiline_error_to_one_line() -> None:
    """A raw multi-line Playwright exception (seen live, 2026-10-10) must not grow the row."""
    record = {"username": "elif", "composite_status": "ACTIVE", "ig_status": "active", "seconds": 34.7,
              "error_message": "Threads error: Locator.click: Timeout 5000ms exceeded.\nCall log:\n  - waiting"}
    row = record_to_row(1, record)
    assert "\n" not in row[-1]
    assert row[-1] == "Threads error: Locator.click: Timeout 5000ms exceeded. Call log: - waiting"


def test_record_to_row_truncates_a_very_long_error() -> None:
    from src.gui.components.data_table import _ERROR_CELL_MAX_CHARS

    record = {"username": "elif", "composite_status": "ACTIVE", "ig_status": "active",
              "seconds": 1.0, "error_message": "x" * 500}
    row = record_to_row(1, record)
    assert len(row[-1]) == _ERROR_CELL_MAX_CHARS
    assert row[-1].endswith("…")


def test_eta_and_duration() -> None:
    assert theme.estimate_eta(60, 0, 100) is None
    assert theme.estimate_eta(60, 20, 100) == 240
    assert theme.format_duration(134) == "2m 14s"
    assert theme.format_duration(9.6) == "10s"


# ---- GUI smoke tests: one real Tk interpreter, reset per test ------------ #

@pytest.fixture(scope="module")
def gui_root(tmp_path_factory: pytest.TempPathFactory) -> Iterator[MetaInspectorApp]:
    """Use one Tk root per process, matching the application's real lifetime."""
    app = MetaInspectorApp(profile_dir=tmp_path_factory.mktemp("gui") / "browser_profile")
    app.withdraw()
    yield app
    app.destroy()


@pytest.fixture
def gui_app(gui_root: MetaInspectorApp, tmp_path: Path) -> Iterator[MetaInspectorApp]:
    """Reset state and settings while preserving the single Tk interpreter."""
    app = gui_root
    app.profile_dir = tmp_path / "browser_profile"
    app.checker_store = CheckerStore(app.profile_dir)
    app.bridge = ScraperBridge(app._default_factory)
    app._checker_dialog = None
    app._session_invalid = False
    app.left_panel.workers_var.set("5")
    app.left_panel.dialog_timeout_var.set("10")
    app.left_panel.menu_timeout_var.set("8")
    app.left_panel.debug_dump_var.set(False)
    app.left_panel.textbox.delete("1.0", "end")
    app.table.clear()
    app._refresh_session()
    app._apply_state()
    yield app
    app.bridge.stop()
    app.bridge.join(timeout=5)
    app.update()
    if app._checker_dialog is not None and app._checker_dialog.winfo_exists():
        app._checker_dialog.destroy()


def test_gui_worker_count_is_not_hardcoded(gui_app: MetaInspectorApp) -> None:
    """The real option menu controls the number of active checkers."""
    assert gui_app.left_panel.workers == 5
    gui_app.left_panel.workers_var.set("1")
    scraper = gui_app._default_factory("combined", lambda *_: None)
    assert scraper.workers == 1


def test_gui_dialog_menu_timeout_and_debug_dump_are_not_hardcoded(gui_app: MetaInspectorApp) -> None:
    """Widget settings reach the engine; invalid input is visibly rejected."""
    from src.core.extractors import DIALOG_TIMEOUT_S, MENU_CLICK_TIMEOUT_S

    panel = gui_app.left_panel
    assert panel.dialog_timeout_s == DIALOG_TIMEOUT_S
    assert panel.menu_click_timeout_s == MENU_CLICK_TIMEOUT_S
    assert panel.debug_dump is False
    panel.dialog_timeout_var.set("20")
    panel.menu_timeout_var.set("15")
    panel.debug_dump_var.set(True)
    scraper = gui_app._default_factory("combined", lambda *_: None)
    assert (scraper.dialog_timeout_s, scraper.menu_click_timeout_s, scraper.debug_dump) == (20., 15., True)
    panel.dialog_timeout_var.set("not a number")
    with pytest.raises(ValueError):
        panel.validate_timeouts()
    gui_app.left_panel.textbox.insert("1.0", "target")
    gui_app.left_panel.start_button.invoke()
    assert gui_app.bridge.state is RunState.IDLE


def test_app_runs_a_fake_check_end_to_end(gui_app: MetaInspectorApp) -> None:
    """Start through real widgets, drain worker events, and verify table rows."""
    app = gui_app
    app.bridge = ScraperBridge(lambda mode, cb: FakeScraper(mode, cb))
    app.left_panel.textbox.insert("1.0", "@alice\nbob\nalice\n")
    app.left_panel.start_button.invoke()
    deadline = time.monotonic() + 5
    while app.bridge.state is not RunState.IDLE or len(app.table.records) < 2:
        app.update()
        if time.monotonic() > deadline:
            raise AssertionError("GUI run did not finish")
    rows = [app.table.tree.item(i, "values") for i in app.table.tree.get_children()]
    assert [r[1] for r in rows] == ["@alice", "@bob"]
    assert app.left_panel.start_button.cget("state") == "normal"


def test_checker_manager_selection_reaches_production_factory(
    gui_app: MetaInspectorApp, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Actual widgets persist selections and request the chosen login slot."""
    app = gui_app
    requested = []
    monkeypatch.setattr(app, "_start_login", requested.append)
    app._on_setup()
    dialog = app._checker_dialog
    assert len(dialog.variables) == 5
    for variable in dialog.variables:
        variable.set(True)
    dialog._save()
    scraper = app._default_factory("combined", lambda *_: None)
    assert len(scraper.checkers) == 5
    assert len({slot.profile_dir for slot in scraper.checkers}) == 5
    assert "live check on Start" in app._session_label.cget("text")
    app._on_setup()
    dialog = app._checker_dialog
    dialog._login(dialog.slots[3])
    assert requested[0].checker_id == "checker_4"


def test_checker_import_validates_then_launches_bound_accounts(
    gui_app: MetaInspectorApp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The actual import dialog rejects bad input before touching selections."""
    from src.gui.components import checker_dialog

    requested = []
    monkeypatch.setattr(gui_app, "_start_import_login", lambda *args: requested.append(args))
    source = tmp_path / "accounts.txt"
    source.write_text("invalid")
    monkeypatch.setattr(checker_dialog.filedialog, "askopenfilename", lambda **_: str(source))
    gui_app._on_setup()
    dialog = gui_app._checker_dialog
    dialog._import()
    assert dialog.winfo_exists() and not requested
    assert not gui_app.checker_store.path.exists()
    source.write_text("alice|synthetic-password|JBSWY3DPEHPK3PXP")
    dialog._import()
    assert len(requested) == 1
    accounts, checkers = requested[0]
    assert accounts[0].username == checkers[0].username == "alice"
    assert gui_app._default_factory("combined", lambda *_: None).checkers == checkers
    assert "synthetic-password" not in gui_app.checker_store.path.read_text()
