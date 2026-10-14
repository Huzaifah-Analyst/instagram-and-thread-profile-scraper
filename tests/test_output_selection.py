"""Actual Tk selection, output parity and persistent history regressions."""

import csv
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from openpyxl import load_workbook

from src.core.checkers import CheckerStore
from src.core.history_db import HistoryDB, SCHEMA
from src.core.output_settings import DEFAULT_NAMES, OutputSettings
from src.gui.app import MetaInspectorApp
from src.gui.bridge import FinishedEvent
from src.gui.output_actions import OutputActions


@pytest.fixture(scope="session")
def gui_root(tmp_path_factory: pytest.TempPathFactory) -> Iterator[MetaInspectorApp]:
    """Share one interpreter, including repeated collection of this module."""
    app = MetaInspectorApp(profile_dir=tmp_path_factory.mktemp("output_gui") / "profile")
    yield app
    app.destroy()


def reload_output(app: MetaInspectorApp, directory: Path) -> None:
    """Rebuild actual output widgets/settings without recreating the Tk root."""
    for dialog in (app.output_actions.dialog, app.output_actions.history_dialog):
        if dialog is not None and dialog.winfo_exists():
            dialog.destroy()
    toast = getattr(app, "_active_toast", None)
    if toast is not None and toast.winfo_exists():
        toast.destroy()
    app.status_bar.destroy()
    app.profile_dir = directory / "profile"
    app.checker_store = CheckerStore(app.profile_dir)
    app.table.clear()
    app.left_panel.mode_var.set("combined")
    app.output_actions = OutputActions(app, app.table, directory)
    app.status_bar = app.output_actions.bar
    app.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
    app.update()


@pytest.fixture
def gui_app(gui_root: MetaInspectorApp, tmp_path: Path) -> MetaInspectorApp:
    """Isolate settings and records for each case while keeping the real root."""
    reload_output(gui_root, tmp_path)
    return gui_root


def assert_fresh_app_selection(directory: Path) -> None:
    """Verify saved selection in a new application process with its own Tk root."""
    source = """
import sys
from pathlib import Path
from src.gui.app import MetaInspectorApp
app = MetaInspectorApp(profile_dir=Path(sys.argv[1]) / 'profile')
try:
    assert app.output_actions.names == ('Username', 'Status')
finally:
    app.destroy()
"""
    subprocess.run(
        [sys.executable, "-c", source, str(directory)],
        cwd=Path(__file__).resolve().parents[1], check=True,
        capture_output=True, text=True, timeout=30,
    )


def headers(path: Path) -> list[str]:
    """Read the CSV's actual column headers."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def test_real_popup_drives_clipboard_csv_excel_and_persists(gui_app: MetaInspectorApp, tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """Click actual widgets, export actual files and reopen saved preferences."""
    app = gui_app
    destination = tmp_path / "results.csv"
    monkeypatch.setattr("src.gui.actions.filedialog.asksaveasfilename", lambda **kw: str(destination))
    app.update()
    app.table.add_record({"username": "target", "ig_country": "Canada",
                          "ig_date_joined": "April 2016", "data_quality": "Partial"})
    app.status_bar.set_results_available(True)
    app.status_bar.csv_button.invoke()
    before_csv = headers(destination)
    app.status_bar.copy_button.invoke()
    before_tsv = app.clipboard_get().splitlines()[0].split("\t")
    assert before_tsv == list(DEFAULT_NAMES)
    app.status_bar.output_button.invoke()
    app.update()
    popup = app.output_actions.dialog
    assert popup.checkboxes["Username"].cget("state") == "disabled"
    popup.checkboxes["IG Country"].toggle()
    popup.ok_button.invoke()
    app.status_bar.copy_button.invoke()
    assert app.clipboard_get().splitlines()[0].split("\t") == [
        name for name in before_tsv if name != "IG Country"]
    app.status_bar.csv_button.invoke()
    assert headers(destination) == [name for name in before_csv if name != "IG Country"]
    destination = tmp_path / "results.xlsx"
    app.status_bar.xlsx_button.invoke()
    assert [c.value for c in load_workbook(destination).active[1]] == headers(tmp_path / "results.csv")
    assert "IG Country" not in OutputSettings(tmp_path).load()
    assert app.status_bar.copy_button.cget("text").strip().endswith("Copied!")
    assert app._active_toast.winfo_exists()
    app.status_bar.output_button.invoke()
    popup = app.output_actions.dialog
    for name, checkbox in popup.checkboxes.items():
        if name != "Username":
            checkbox.deselect()
    popup.ok_button.invoke()
    app.status_bar.copy_button.invoke()
    assert app.clipboard_get().splitlines()[0] == "Username\tStatus"
    app.status_bar.output_button.invoke()
    app.output_actions.dialog.select_all()
    app.output_actions.dialog.destroy()  # X/Cancel must discard the draft.
    assert app.output_actions.names == ("Username", "Status")
    app.status_bar.output_button.invoke()
    popup = app.output_actions.dialog
    popup.select_all()
    popup.ok_button.invoke()
    app.status_bar.copy_button.invoke()
    selected = app.clipboard_get().splitlines()[0].split("\t")
    assert "IG Country Availability" in selected
    assert "Threads Country Availability" in selected
    assert "Data Quality" in selected
    destination = tmp_path / "selected.csv"
    app.status_bar.csv_button.invoke()
    assert headers(destination) == selected
    app.status_bar.output_button.invoke()
    popup = app.output_actions.dialog
    popup.reset()
    assert tuple(name for name, var in popup.variables.items() if var.get()) == DEFAULT_NAMES
    popup.destroy()
    app.output_actions.apply_selection(("Username", "Status"))
    assert_fresh_app_selection(tmp_path)


@pytest.mark.parametrize("raw", ['{broken', '{"columns":["invalid"]}',
                                      '{"columns":[{}]}', '[]', '\ufffd'])
def test_corrupt_settings_default_and_visible_message(
    gui_app: MetaInspectorApp, tmp_path: Path, raw: str,
) -> None:
    """Corrupt/invalid files never prevent startup and warn in the status bar."""
    (tmp_path / "output_settings.json").write_text(raw, encoding="utf-8")
    settings = OutputSettings(tmp_path)
    assert settings.load() == DEFAULT_NAMES
    assert settings.warning
    app = gui_app
    reload_output(app, tmp_path)
    assert "default columns restored" in app.status_bar._message.cget("text")


def test_history_migrates_and_retains_modern_record(tmp_path: Path) -> None:
    """Read a legacy row and round-trip current metadata through the same DB."""
    path = tmp_path / "history.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute("INSERT INTO run_items (run_id, username) VALUES ('old', 'legacy')")
    history = HistoryDB(path)
    assert history.get_run_items("old")[0]["username"] == "legacy"
    record = {"username": "new", "data_quality": "Partial", "ig_status": "private",
              "threads_country_availability": "not_disclosed", "seconds": 3.2,
              "checker_id": "checker_5"}
    run_id = history.save_run([record], "combined", 1, 4)
    assert history.get_run_items(run_id, full_record=True) == [record]


def test_real_history_and_platform_scope(gui_app: MetaInspectorApp, tmp_path: Path) -> None:
    """All existing radios reach the engine and finished results open in history."""
    app = gui_app
    for button in app.left_panel._mode_buttons:
        button.invoke()
        scraper = app._default_factory(app.left_panel.mode, lambda *args: None)
        assert scraper.mode == button.cget("value")
    record = {"username": "test", "composite_status": "ACTIVE", "data_quality": "Partial"}
    app._total = 1
    app.table.add_record(record)
    app._on_finished(FinishedEvent([record], None, 5.0))
    app.status_bar.history_button.invoke()
    viewer = app.output_actions.history_dialog
    assert viewer.records == [record]
    assert viewer.details.records == [record]
