"""Actual Chromium DOM regressions for the independently reproduced defects."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest
from playwright.async_api import Page, Route, async_playwright

from src.core.browser_helpers import _click_menu_item, _safe_click
from src.core.dialogs import _poll_dialog
from src.core.extractors import _find_threads_menu_button, extract_instagram


def run_browser(check: Callable[[Page], Awaitable[None]]) -> None:
    """Run a browser assertion in an isolated session with no external traffic."""
    async def scenario() -> None:
        """Create and reliably close a fresh local Chromium page."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            try:
                await check(await browser.new_page())
            finally:
                await browser.close()

    asyncio.run(scenario())


def test_dialog_rejects_hidden_and_wrong_account() -> None:
    """Neither a hidden match nor visible other-user dialog may supply data."""
    async def check(page: Page) -> None:
        """Read the intended visible identity from three competing dialogs."""
        await page.set_content('''
          <div role="dialog" style="display:none">target<br>Date joined<br>
          October 2025<br>Account based in<br>China</div>
          <div role="dialog">other<br>Date joined<br>November 2025<br>
          Account based in<br>Brazil</div>
          <div role="dialog">target<br>Date joined<br>April 2016<br>
          Account based in<br>Canada</div>''')
        result = await _poll_dialog(
            page, ('[role="dialog"]',), expected_username="target",
            dialog_timeout_s=1,
        )
        assert result["date_joined"] == "April 2016"
        assert result["country"] == "Canada"

    run_browser(check)


def test_dialog_waits_for_country_and_preserves_legitimate_missing_country() -> None:
    """Late hydration is retained; a genuinely absent field stays empty."""
    async def check(page: Page) -> None:
        """Exercise both a delayed second field and a stable date-only dialog."""
        await page.set_content('''<div role="dialog" id="about">target<br>
          Date joined<br>October 2025</div>
          <script>setTimeout(() => document.querySelector('#about')
          .innerHTML += '<br>Account based in<br>China', 150)</script>''')
        result = await _poll_dialog(
            page, ('[role="dialog"]',), expected_username="target",
            dialog_timeout_s=1,
        )
        assert result["country"] == "China"
        assert result["date_joined"] == "October 2025"
        await page.set_content('''<div role="dialog">target<br>
          Date joined<br>April 2016</div>''')
        result = await _poll_dialog(
            page, ('[role="dialog"]',), expected_username="target",
            dialog_timeout_s=.3,
        )
        assert result["date_joined"] == "April 2016"
        assert result["country"] is None

    run_browser(check)


def test_visible_menu_alias_survives_hidden_duplicate() -> None:
    """About this profile is supported even with a hidden last duplicate."""
    async def check(page: Page) -> None:
        """Click the visible alias and inspect its DOM side effect."""
        await page.set_content('''<button onclick="window.clicked=true">
          About this profile</button><button hidden>About this profile</button>''')
        assert await _click_menu_item(page, ("About this profile",), .5)
        assert await page.evaluate("window.clicked") is True

    run_browser(check)


def test_threads_fallback_prefers_dialog_over_enclosing_profile_bio() -> None:
    """A short page's bio must not override the actual nested About panel."""
    async def check(page: Page) -> None:
        """Use the observed Name/Joined/Based-in panel without a dialog role."""
        await page.set_content('''<div><h1>target</h1>
          <p>Date joined<br>January 1990<br>Account based in<br>Wrong</p>
          <div>Name<br>Example (@target)<br>Joined<br>October 2025<br>
          Based in<br>Not shared</div></div>''')
        result = await _poll_dialog(
            page, ("div:has-text('Based in')",), expected_username="target",
            dialog_timeout_s=.5,
        )
        assert result["date_joined"] == "October 2025"
        assert result["country"] == "Not shared"

    run_browser(check)


def test_threads_menu_uses_named_action_not_rightmost_icon() -> None:
    """The named live-observed More icon beats an unrelated rightmost SVG."""
    async def check(page: Page) -> None:
        """Place both controls in the profile band, then click the chosen one."""
        await page.set_content('''<div role="main" style="padding-top:120px">
          <div role="button" onclick="window.action='more'">
          <svg title="More" width="24" height="24"><title>More</title></svg>
          </div><button style="position:absolute;left:1000px;top:120px"
          onclick="window.action='wrong'"><svg width="24" height="24">
          </svg></button></div>''')
        menu = await _find_threads_menu_button(page)
        assert menu is not None
        await _safe_click(menu)
        assert await page.evaluate("window.action") == "more"

    run_browser(check)


def test_unknown_page_is_error_and_early_failure_has_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generic error content must not become ACTIVE; capture works before menus."""
    import src.core.diagnostics as diagnostics

    monkeypatch.setattr(diagnostics, "DEBUG_DIR", tmp_path)

    async def check(page: Page) -> None:
        """Fulfil all requests locally, then verify status and evidence files."""
        async def fulfill(route: Route) -> None:
            """Supply an unclassified error, never contacting Meta."""
            await route.fulfill(body="<p>Something went wrong</p>", content_type="text/html")

        await page.route("**/*", fulfill)
        result = await extract_instagram(
            page, "target", page_ready_timeout_s=.1, debug_dump=True,
        )
        assert result["status"] == "error"
        assert result["stage"] == "identity"
        assert result["country"] is None
        assert Path(result["evidence"]).exists()
        assert len(list(tmp_path.glob("*.png"))) == 1

    run_browser(check)


def test_detached_click_respects_total_deadline() -> None:
    """JS fallback must not inherit Playwright's 30-second lookup timeout."""
    from playwright.async_api import TimeoutError as BrowserTimeout

    async def check(page: Page) -> None:
        """A locator that never exists must fail within the configured budget."""
        started = time.monotonic()
        try:
            await _safe_click(page.locator("#absent"), timeout_ms=80)
        except BrowserTimeout as exc:
            assert str(exc)
        else:
            raise AssertionError("A missing locator unexpectedly clicked")
        assert time.monotonic() - started < 1.5

    run_browser(check)
