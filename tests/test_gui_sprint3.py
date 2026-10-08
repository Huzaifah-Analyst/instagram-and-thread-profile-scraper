"""Real-window GUI tests for copy, toast, export and the history viewer (TSK-301 to TSK-305).

These touch the real Windows clipboard; the previous clipboard text is restored.
"""

import time
import tkinter as tk
from pathlib import Path
from typing import Iterator

import pytest

from src.core.clipboard import format_tsv
from src.gui import actions
from src.gui.bridge import RunState
from tests.test_gui_bridge import FakeScraper


@pytest.fixture
def app(tmp_path: Path) -> Iterator["MetaInspectorApp"]:  # noqa: F821
    """A hidden main window wired to a fake scraper and a temp history.db."""
    from src.gui.app import MetaInspectorApp

    try:
        window = MetaInspectorApp(profile_dir=tmp_path / "profile", history_path=tmp_path / "history.db",
                                  scraper_factory=lambda mode, cb: FakeScraper(mode, cb))
    except tk.TclError as exc:
        pytest.skip(f"No display available: {exc}")
    try:
        saved_clipboard = window.clipboard_get()
    except tk.TclError:
        saved_clipboard = None
    window.withdraw()
    yield window
    if saved_clipboard is not None:
        window.clipboard_clear()
        window.clipboard_append(saved_clipboard)
        window.update()
    window.destroy()


def pump(window: tk.Misc, seconds: float) -> None:
    """Runs the Tk event loop for ``seconds`` (lets after() timers fire)."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        window.update()
        time.sleep(0.02)


def run_fake_check(window: "MetaInspectorApp", names: str = "alice\nbob\ncarol") -> None:  # noqa: F821
    """Types usernames, clicks Start and waits for the fake run to finish."""
    window.left_panel.textbox.delete("1.0", "end")
    window.left_panel.textbox.insert("1.0", names)
    window.left_panel.start_button.invoke()
    deadline = time.monotonic() + 5
    while window.bridge.state is not RunState.IDLE or not window.table.records:
        window.update()
        assert time.monotonic() < deadline, "fake run did not finish"


def test_buttons_disabled_until_results(app) -> None:
    bar = app.status_bar
    assert bar.copy_button.cget("state") == "disabled"
    assert bar.history_button.cget("state") == "normal"
    run_fake_check(app)
    assert bar.copy_button.cget("state") == "normal"
    assert bar.csv_button.cget("state") == "normal"


def test_copy_puts_tsv_on_clipboard_and_toast_expires(app) -> None:
    run_fake_check(app)
    app.status_bar.copy_button.invoke()

    assert app.clipboard_get() == format_tsv(app.table.records)
    assert app.clipboard_get().splitlines()[0].split("\t")[0] == "Username"
    assert app.status_bar.copy_button.cget("text") == "✓  Copied!"
    toast = app._active_toast
    assert toast.winfo_exists()

    pump(app, 2.7)  # toast lives 2.5 s, button label 2.0 s
    assert not toast.winfo_exists()
    assert app.status_bar.copy_button.cget("text") == "📋  Copy for Google Sheets"


def test_finished_run_is_saved_to_history(app) -> None:
    run_fake_check(app, "alice\nbob")
    [run] = app.history.list_runs()
    assert run["mode"] == "combined"
    assert run["total_accounts"] == 2 and run["active_count"] == 2
    assert [i["username"] for i in app.history.get_run_items(run["run_id"])] == ["alice", "bob"]


@pytest.mark.parametrize("kind, suffix", [("csv", ".csv"), ("xlsx", ".xlsx")])
def test_export_buttons_write_files(app, tmp_path: Path, monkeypatch, kind: str, suffix: str) -> None:
    target = tmp_path / f"export{suffix}"
    monkeypatch.setattr(actions.filedialog, "asksaveasfilename", lambda **_kw: str(target))
    run_fake_check(app)
    (app.status_bar.csv_button if kind == "csv" else app.status_bar.xlsx_button).invoke()
    assert target.exists() and target.stat().st_size > 0


def test_export_cancel_writes_nothing(app, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(actions.filedialog, "asksaveasfilename", lambda **_kw: "")
    run_fake_check(app)
    assert actions.export_records(app, app.table.records, "csv") is None
    assert list(tmp_path.glob("*.csv")) == []


def test_history_dialog_lists_runs_and_recopies(app) -> None:
    run_fake_check(app, "alice")
    app.table.clear()
    run_fake_check(app, "bob\ncarol")
    app.status_bar.history_button.invoke()
    dialog = app._history_dialog
    dialog.withdraw()

    assert len(dialog.runs_tree.get_children()) == 2
    assert [r["username"] for r in dialog.records] == ["bob", "carol"]  # newest selected first

    older = dialog.runs_tree.get_children()[1]
    dialog.runs_tree.selection_set(older)
    dialog.update()
    assert [r["username"] for r in dialog.records] == ["alice"]

    dialog.copy_button.invoke()
    assert app.clipboard_get() == format_tsv([{"username": "alice", "composite_status": "ACTIVE"}])
