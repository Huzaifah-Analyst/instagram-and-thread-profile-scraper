"""Real Tk forwarding and explicit status-only field availability."""

from pathlib import Path
from collections.abc import Iterator

import customtkinter as ctk
import pytest

from src.core.anonymous_status import status_record
from src.gui.app import MetaInspectorApp
from src.gui.components.data_table import COLUMNS, record_to_row


@pytest.fixture(scope="module")
def gui_root(tmp_path_factory: pytest.TempPathFactory) -> Iterator[MetaInspectorApp]:
    """Keep one actual Tk interpreter for this test module."""
    app = MetaInspectorApp(profile_dir=tmp_path_factory.mktemp("targeted_gui") / "profile")
    yield app
    app.destroy()


@pytest.mark.parametrize("mode", ["combined_smart", "ig_status_only"])
def test_gui_forwards_new_mode_unchanged(gui_root: MetaInspectorApp, monkeypatch: pytest.MonkeyPatch,
                                       mode: str) -> None:
    """Actual radios feed Start and the production factory without new defaults."""
    app = gui_root
    try:
        app.update()
        assert app.left_panel.mode == "combined"
        if mode == "ig_status_only":
            def reject_checker_load() -> None:
                """An anonymous mode must not require valid checker configuration."""
                raise AssertionError("Checker configuration accessed")
            monkeypatch.setattr(app.checker_store, "load", reject_checker_load)
        button = next(b for b in app.left_panel._mode_buttons if b.cget("value") == mode)
        button.invoke()
        assert app.left_panel.mode == mode
        engine = app._default_factory(mode, lambda *_: None)
        assert engine.mode == mode
        assert engine.workers == app.left_panel.workers
        seen: list[str] = []
        monkeypatch.setattr(app.bridge, "start", lambda users, selected: seen.append(selected))
        app.left_panel.textbox.insert("1.0", "fixture")
        app._on_start()
        assert seen == [mode]
        if mode == "ig_status_only":
            assert engine.checkers == []
            assert "unavailable without login" in app.status_bar._message.cget("text")
            assert "no login needed" in app._session_label.cget("text")
        captions = [widget.cget("text") for child in app.left_panel.winfo_children()
                    for widget in child.winfo_children() if isinstance(widget, ctk.CTkLabel)]
        assert "Parallel workers" in captions
        assert "Checker limit" not in captions
    finally:
        app.left_panel.mode_var.set("combined")
        app.left_panel.textbox.delete("1.0", "end")


def test_status_only_table_explains_absent_fields() -> None:
    """The table presents an intentional limitation instead of empty failed cells."""
    record = status_record("fixture", "active", "", .2)
    row = dict(zip((column[0] for column in COLUMNS), record_to_row(1, record)))
    assert row["quality"] == "Status only"
    assert row["ig_country"] == row["ig_joined"] == "Unavailable (status only)"
    assert row["threads_country"] == row["threads_joined"] == "Not checked"
    assert row["checker"] == ""


def test_small_window_keeps_input_and_controls_reachable(
    gui_root: MetaInspectorApp,
) -> None:
    """At minimum height, scrolling exposes controls without collapsing input."""
    app = gui_root
    app.geometry("950x600")
    app.update()
    panel = app.left_panel
    canvas = panel._parent_canvas
    canvas.yview_moveto(0)
    app.update()
    assert panel.textbox.winfo_height() >= 100
    assert panel.textbox.winfo_rooty() >= canvas.winfo_rooty()
    panel.textbox.insert("1.0", "fixture")
    assert panel.usernames() == ["fixture"]
    canvas.yview_moveto(1)
    app.update()
    top = canvas.winfo_rooty()
    bottom = top + canvas.winfo_height()
    for control in (panel.start_button, panel.pause_button, panel.stop_button):
        assert top <= control.winfo_rooty()
        assert control.winfo_rooty() + control.winfo_height() <= bottom
    panel.textbox.delete("1.0", "end")
    canvas.yview_moveto(0)
