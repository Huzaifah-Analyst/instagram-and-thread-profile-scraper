"""Real Chromium tests of populated-panel stability and delayed hydration."""

import time

from playwright.async_api import Page

from src.core.dialogs import _poll_dialog
from test_accuracy_regressions import run_browser


def test_stable_date_only_panel_returns_before_budget() -> None:
    """A stable matching date-only panel avoids the full ten-second budget."""
    async def check(page: Page) -> None:
        """Overlapping selectors must not count as distinct polling cycles."""
        await page.set_content('<div role="dialog" id="panel">target<br>Joined<br>October 2025</div>')
        start = time.monotonic()
        result = await _poll_dialog(page, ('[role="dialog"]', '#panel'),
                                    expected_username="target", dialog_timeout_s=10)
        elapsed = time.monotonic() - start
        assert 0.9 <= elapsed < 4
        assert result["date_joined"] == "October 2025"
        assert result["country"] is None
    run_browser(check)


def test_changing_panel_keeps_waiting_for_late_country() -> None:
    """Text changes reset stability so a later country remains readable."""
    async def check(page: Page) -> None:
        """Hydrate country after more than the stable panel's return time."""
        await page.set_content('''<div role="dialog">target<br>Joined<br>
          October 2025<br><span id="loading">Loading</span></div>
          <script>
          let n = 0;
          let timer = setInterval(() => {
            document.querySelector('#loading').textContent = 'Loading ' + (++n);
          }, 200);
          setTimeout(() => {
            clearInterval(timer);
            document.querySelector('#loading').remove();
            document.querySelector('[role=dialog]').innerHTML += '<br>Based in<br>Canada';
          }, 1600);
          </script>''')
        result = await _poll_dialog(page, ('[role="dialog"]',),
                                    expected_username="target", dialog_timeout_s=5)
        assert result["country"] == "Canada"
        assert result["date_joined"] == "October 2025"
    run_browser(check)
