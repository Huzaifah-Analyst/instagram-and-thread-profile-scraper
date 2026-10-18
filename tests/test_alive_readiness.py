"""Alive extraction can decide before unrelated page scripts finish."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page, Route
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.browser_helpers import _open_profile
from src.core.extractors import extract_instagram, extract_threads
from test_accuracy_regressions import run_browser


@pytest.mark.parametrize("platform", ["ig", "threads"])
@pytest.mark.parametrize("status,content", [
    ("active", '<header><h1>target</h1></header>0 followers'),
    ("not_found", "Sorry, this page isn't available."),
    ("session_blocked", "Log in\nSign up"),
])
def test_alive_extractors_decide_before_deferred_scripts(
    platform: str, status: str, content: str,
) -> None:
    """Keep actual profile, missing-account and checker-gate distinctions."""
    async def check(page: Page) -> None:
        """Hold a script while the real extractor reads the profile DOM."""
        release_script = asyncio.Event()

        async def serve(route: Route) -> None:
            """Supply local HTML and an explicitly blocked deferred script."""
            if route.request.url.endswith("slow.js"):
                await release_script.wait()
                await route.fulfill(body="", content_type="text/javascript")
            else:
                await route.fulfill(content_type="text/html", body=(
                    '<script defer src="/slow.js"></script>'
                    f'<div role="main" style="white-space:pre-line">'
                    f'{content}</div>'
                ))

        await page.route("**/*", serve)
        extract = extract_instagram if platform == "ig" else extract_threads
        try:
            result = await asyncio.wait_for(extract(
                page, "target", requested_fields=(), page_ready_timeout_s=2,
            ), timeout=3)
            assert result["status"] == status
            assert result["country"] is result["date_joined"] is None
            assert bool(result["error"]) is (status == "session_blocked")
            assert not release_script.is_set()
        finally:
            release_script.set()
            await page.wait_for_load_state("domcontentloaded", timeout=2000)

    run_browser(check)


def test_alive_navigation_timeout_never_reads_previous_profile() -> None:
    """A request that never committed cannot reuse a prior page's 404 text."""
    body = AsyncMock(return_value="Sorry, this page isn't available.")
    page = SimpleNamespace(
        goto=AsyncMock(side_effect=PlaywrightTimeoutError("No document")),
        inner_text=body,
    )
    with pytest.raises(PlaywrightTimeoutError):
        asyncio.run(_open_profile(
            page, "https://www.threads.com/@target", "h1", .5,
            status_only=True,
        ))
    body.assert_not_awaited()
