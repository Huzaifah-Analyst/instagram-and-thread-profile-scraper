"""Tests for the scraper-to-GUI bridge, pause/stop flags, session check and the GUI shell."""

import sqlite3
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

import pytest

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
    assert record_to_row(1, record) == ("01", "@elif", "ACTIVE", "Turkey", "Sep 2026", "N/A",
                                        "Sep 2026 · 100M+", "2.4s")


def test_eta_and_duration() -> None:
    assert theme.estimate_eta(60, 0, 100) is None
    assert theme.estimate_eta(60, 20, 100) == 240
    assert theme.format_duration(134) == "2m 14s"
    assert theme.format_duration(9.6) == "10s"


# ---- GUI smoke test ------------------------------------------------------- #

def test_app_runs_a_fake_check_end_to_end(tmp_path: Path) -> None:
    """Builds the real window, starts a run via the Start button and checks the table fills."""
    from src.gui.app import MetaInspectorApp

    try:
        app = MetaInspectorApp(profile_dir=tmp_path, scraper_factory=lambda mode, cb: FakeScraper(mode, cb))
    except tk.TclError as exc:
        pytest.skip(f"No display available: {exc}")
    try:
        app.withdraw()
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
    finally:
        app.destroy()
