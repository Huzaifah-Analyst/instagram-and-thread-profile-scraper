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

from src.core.ban_engine import STATUS_ACTIVE, STATUS_NOT_FOUND
from src.core.extractors import extract_instagram, extract_threads


class FakeLocator:
    """Stands in for a Playwright ``Locator``; ``hits`` controls ``count()``."""

    def __init__(self, hits: int = 0) -> None:
        self.hits = hits
        self.clicked = False

    async def count(self) -> int:
        return self.hits

    async def is_visible(self) -> bool:
        return self.hits > 0

    async def click(self) -> None:
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
