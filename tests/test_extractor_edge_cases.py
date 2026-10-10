"""Edge-case coverage for the extractors against a fake Playwright page (TSK-402).

No live Instagram/Threads access is available in this environment, so these
tests cannot replace running the real edge cases from
`docs/tasks.md` TSK-402 (private account, non-existent username, no-Threads
account, inactive Threads profile) against the live site. What they do confirm
is that the extractor control flow handles each scenario's *shape* -- a
not-found page, a missing "..." menu, a missing "About" entry -- without
crashing or hanging, using a minimal fake `Page` that returns canned text and
locator results instead of a real browser.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.ban_engine import STATUS_ACTIVE, STATUS_NOT_FOUND
from src.core.extractors import _safe_click, extract_instagram, extract_threads


class FakeLocator:
    """Stands in for a Playwright ``Locator``; ``hits`` controls ``count()``.

    ``click_failures`` lets a test simulate Playwright's own click action
    hanging/failing N times before succeeding (or never), independent of
    ``count()``/``is_visible()`` -- this is what `_safe_click` falls back
    through, seen live as "Locator.click: Timeout ... Call log:" errors.
    """

    def __init__(self, hits: int = 0, click_failures: int = 0) -> None:
        self.hits = hits
        self.clicked = False
        self.evaluated = False
        self.click_failures = click_failures
        self.click_calls: list[tuple[Optional[int], bool]] = []

    async def count(self) -> int:
        return self.hits

    async def is_visible(self) -> bool:
        return self.hits > 0

    async def click(self, timeout: Optional[int] = None, force: bool = False) -> None:
        self.click_calls.append((timeout, force))
        if self.click_failures > 0:
            self.click_failures -= 1
            raise PlaywrightTimeoutError("Locator.click: Timeout 5000ms exceeded.\nCall log:\n  - waiting")
        self.clicked = True

    async def evaluate(self, _script: str) -> None:
        self.evaluated = True
        self.clicked = True

    async def bounding_box(self) -> Optional[dict]:
        return None

    @property
    def first(self) -> "FakeLocator":
        return self

    @property
    def last(self) -> "FakeLocator":
        return self

    def nth(self, _index: int) -> "FakeLocator":
        return self

    def locator(self, _selector: str) -> "FakeLocator":
        return FakeLocator(0)

    async def inner_text(self, timeout: int = 1_000) -> str:
        return ""


class FakeKeyboard:
    """No-op keyboard; extractors only use it to dismiss dialogs with Escape."""

    async def press(self, _key: str) -> None:
        return None


class FakePage:
    """Minimal fake of a worker ``Page``, driven entirely by canned selector hits.

    Args:
        body: Body text returned by ``inner_text("body")``.
        url: Current page URL.
        header_ready: Whether the profile header selector resolves (page loaded).
        menu_hits: ``count()`` for the IG "Options" / Threads card locators.
    """

    def __init__(self, body: str, url: str, header_ready: bool = True, menu_hits: int = 0) -> None:
        self.url = url
        self._body = body
        self._header_ready = header_ready
        self._menu_hits = menu_hits
        self.keyboard = FakeKeyboard()

    async def goto(self, _url: str, wait_until: str = "domcontentloaded", timeout: int = 0) -> None:
        return None

    async def inner_text(self, _selector: str, timeout: int = 2_000) -> str:
        return self._body

    _READY_SELECTORS = (
        "header h2, header h1",
        "div[aria-label='Column body'] h1, div[role='main'] h1",
    )

    def locator(self, selector: str) -> FakeLocator:
        if selector in self._READY_SELECTORS:
            return FakeLocator(1 if self._header_ready else 0)
        # Everything else (the IG "Options" button candidates, or the Threads
        # card/menu-svg lookups) is driven by menu_hits.
        return FakeLocator(self._menu_hits)

    def get_by_text(self, _text: str, exact: bool = True) -> FakeLocator:
        return FakeLocator(0)


# ---- Instagram: no "Options" menu (private/limited accounts can hide it) --- #

def test_extract_instagram_active_with_no_options_button_does_not_crash() -> None:
    """An active profile whose "..." button never resolves must stay ACTIVE with error set, not crash."""
    page = FakePage(body="someuser 42 posts", url="https://www.instagram.com/someuser/", menu_hits=0)
    result = asyncio.run(extract_instagram(page, "someuser"))
    assert result["status"] == STATUS_ACTIVE
    assert result["date_joined"] is None and result["country"] is None
    assert result["error"] == "IG options (...) button not found"


def test_extract_instagram_not_found_short_circuits_before_menu() -> None:
    """A non-existent username must classify as NOT_FOUND without ever touching the menu."""
    page = FakePage(
        body="Sorry, this page isn't available.", url="https://www.instagram.com/doesnotexist/",
        header_ready=False, menu_hits=0,
    )
    result = asyncio.run(extract_instagram(page, "doesnotexist"))
    assert result["status"] == STATUS_NOT_FOUND
    assert result["error"] is None


# ---- Threads: inactive profile with no "..." menu (memory.md quirk #1) ----- #

def test_extract_threads_inactive_profile_has_no_menu_and_does_not_crash() -> None:
    """Inactive Threads profiles often render with no action menu at all."""
    page = FakePage(
        body="someuser\n0 posts", url="https://www.threads.com/@someuser", menu_hits=0,
    )
    result = asyncio.run(extract_threads(page, "someuser"))
    assert result["status"] == STATUS_ACTIVE
    assert result["error"] == "Threads profile menu not found"
    assert result["date_joined"] is None and result["country"] is None


def test_extract_threads_not_found_for_account_with_no_threads_presence() -> None:
    """An Instagram account that never created a Threads profile must classify as NOT_FOUND."""
    page = FakePage(
        body="Sorry, this page isn't available.", url="https://www.threads.com/@someuser",
        header_ready=False, menu_hits=0,
    )
    result = asyncio.run(extract_threads(page, "someuser"))
    assert result["status"] == STATUS_NOT_FOUND
    assert result["error"] is None


# ---- _safe_click's 3-stage fallback (2026-10-10 live test findings) ------- #
#
# Live testing found Threads' options SVG sometimes hangs a plain .click()
# for Playwright's ~30s default actionability timeout, surfacing as a raw
# "Locator.click: Timeout ... Call log:" error dumped straight into the UI.
# _safe_click bounds each stage and falls back: plain click -> force click ->
# a raw JS click.

def test_safe_click_succeeds_on_first_try() -> None:
    locator = FakeLocator(click_failures=0)
    asyncio.run(_safe_click(locator))
    assert locator.clicked and not locator.evaluated
    assert locator.click_calls == [(5_000, False)]


def test_safe_click_falls_back_to_forced_click() -> None:
    """A plain click that times out once must be retried with force=True, not abandoned."""
    locator = FakeLocator(click_failures=1)
    asyncio.run(_safe_click(locator))
    assert locator.clicked and not locator.evaluated
    assert locator.click_calls == [(5_000, False), (5_000, True)]


def test_safe_click_falls_back_to_js_click_when_both_time_out() -> None:
    """If even a forced click hangs, a raw JS click must still complete the action."""
    locator = FakeLocator(click_failures=2)
    asyncio.run(_safe_click(locator))
    assert locator.clicked and locator.evaluated
    assert locator.click_calls == [(5_000, False), (5_000, True)]


def test_safe_click_never_takes_the_full_default_playwright_timeout() -> None:
    """Regression guard for the live-observed 34-40s hangs: each click attempt must be
    bounded well under Playwright's own ~30s default actionability timeout."""
    import src.core.extractors as extractors_module

    assert extractors_module.CLICK_ACTION_TIMEOUT_MS < 30_000


# ---- debug capture (ISSUE_concurrent_session_detection.md §5 item 3) ------ #

class _RecordingLocator:
    """Fake locator that always resolves to one fixed dialog text."""

    def __init__(self, text: str) -> None:
        self._text = text

    async def count(self) -> int:
        return 1

    def nth(self, _index: int) -> "_RecordingLocator":
        return self

    async def inner_text(self, timeout: int = 1_000) -> str:
        return self._text


class _RecordingDialogPage:
    """Fake page whose dialog selector always resolves to `_RecordingLocator`."""

    def __init__(self, text: str) -> None:
        self._text = text

    def locator(self, _selector: str) -> _RecordingLocator:
        return _RecordingLocator(self._text)


def test_poll_dialog_calls_debug_sink_with_every_text_seen() -> None:
    from src.core.extractors import _poll_dialog

    seen: list[str] = []
    page = _RecordingDialogPage("Date joined\nMarch 2015\nAccount based in\nTurkey")
    result = asyncio.run(
        _poll_dialog(page, ("div[role='dialog']",), dialog_timeout_s=1.0, debug_sink=seen.append)
    )
    assert result["date_joined"] == "March 2015" and result["country"] == "Turkey"
    assert seen == ["Date joined\nMarch 2015\nAccount based in\nTurkey"]


def test_write_debug_dump_writes_a_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.extractors as extractors_module

    monkeypatch.setattr(extractors_module, "DEBUG_DIR", tmp_path / "debug")
    extractors_module._write_debug_dump("ig", "someuser", ["Date joined\nMarch 2015"])
    files = list((tmp_path / "debug").glob("ig_someuser_*.txt"))
    assert len(files) == 1
    assert "March 2015" in files[0].read_text(encoding="utf-8")


def test_write_debug_dump_does_nothing_for_empty_texts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.extractors as extractors_module

    monkeypatch.setattr(extractors_module, "DEBUG_DIR", tmp_path / "debug")
    extractors_module._write_debug_dump("ig", "someuser", [])
    assert not (tmp_path / "debug").exists()


# ---- short, human-readable error messages (2026-10-10 live test findings) #
#
# A raw Playwright exception's str() is multi-line ("...Timeout ...\nCall
# log:\n  - waiting for ..."), which was showing up verbatim in the live
# table's Error column, wrapping rows across multiple lines. `_short_error`
# keeps only the first line.

def test_short_error_drops_playwrights_multiline_call_log() -> None:
    from src.core.extractors import _short_error

    exc = PlaywrightTimeoutError("Locator.click: Timeout 5000ms exceeded.\nCall log:\n  - waiting for element")
    assert _short_error("Threads error", exc) == "Threads error: Locator.click: Timeout 5000ms exceeded."


def test_short_error_handles_an_exception_with_no_message() -> None:
    from src.core.extractors import _short_error

    assert _short_error("IG error", PlaywrightTimeoutError("")) == "IG error: TimeoutError"
