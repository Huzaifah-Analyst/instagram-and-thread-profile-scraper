"""Actual Chromium page allocation and persistent manual-window lifecycle."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import BrowserContext, BrowserType, Page, Route

from src.core import checker_health, checker_pool
from src.core.checkers import Checker
from src.core.scraper import MultiWorkerScraper


def test_one_real_context_has_five_concurrent_worker_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use real Chromium pages with fixture health and barrier-controlled targets."""
    monkeypatch.setattr(checker_pool, "verify_context", AsyncMock(
        return_value={"ig": None, "threads": None},
    ))
    scraper = MultiWorkerScraper(
        checkers=[Checker("only", tmp_path / "browser_profile", True)],
        workers=5, headless=True, min_delay=0, max_delay=0,
    )
    pages: set[Page] = set()
    contexts: set[BrowserContext] = set()

    async def scenario() -> list[dict]:
        """Require five simultaneous in-flight targets, not just five allocations."""
        ready = asyncio.Event()

        async def check(page: Page, username: str) -> dict:
            """Exercise separate DOMs while all workers share the saved context."""
            pages.add(page)
            contexts.add(page.context)
            await page.set_content(f"<p>{username}</p>")
            if len(pages) == 5:
                ready.set()
            await asyncio.wait_for(ready.wait(), 5)
            assert await page.locator("p").inner_text() == username
            return {"username": username, "composite_status": "ACTIVE"}

        monkeypatch.setattr(scraper, "_check_account", check)
        return await scraper.run_async([f"target{i}" for i in range(20)])

    rows = asyncio.run(scenario())
    assert len(pages) == 5 and len(contexts) == 1
    assert len(rows) == 20 and all(row["composite_status"] == "ACTIVE" for row in rows)
    assert len(scraper.blocker_stats) == 5
    assert scraper.active_checker_ids == ["only"]
    assert all(page.is_closed() for page in pages)


def test_sequential_real_windows_reuse_persisted_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close real headed windows in order; persistent cookies survive relaunch."""
    original = BrowserType.launch_persistent_context
    contexts: list[BrowserContext] = []
    closed: list[int] = []
    visits: list[str] = []
    closers: list[asyncio.Task] = []

    async def launch(
        browser: BrowserType, directory: str, **kwargs: object,
    ) -> BrowserContext:
        """Route fixture login pages without sending any traffic to Meta."""
        index = len(contexts)
        assert closed == list(range(index))
        assert directory == str(tmp_path / "browser_profile")
        assert kwargs["headless"] is (index == 2)
        if index < 2:
            assert kwargs["no_viewport"] is True
            assert "--start-maximized" in kwargs["args"]
        context = await original(browser, directory, **kwargs)
        if index < 2:
            assert context.pages[0].viewport_size is None
        contexts.append(context)
        context.on("close", lambda *_: closed.append(index))

        async def route(request: Route) -> None:
            """Provide local HTML for every request in these isolated profiles."""
            await request.fulfill(body="<html><body>Fixture login only</body></html>")

        await context.route("**/*", route)
        if index == 0:
            await context.add_cookies([{
                "name": "fixture_persistence", "value": "yes",
                "url": "https://www.instagram.com/", "expires": 2000000000,
            }])
        else:
            assert any(c["name"] == "fixture_persistence" for c in await context.cookies())
        if index < 2:
            async def close_loaded() -> None:
                """Simulate user closure only after the one expected tab loads."""
                page = context.pages[0]
                await page.wait_for_url(lambda url: "/login" in url, timeout=10000)
                visits.append(page.url)
                assert len(context.pages) == 1
                await context.close()

            closers.append(asyncio.create_task(close_loaded()))
        return context

    monkeypatch.setattr(BrowserType, "launch_persistent_context", launch)
    verify = AsyncMock(return_value={"ig": None, "threads": "Fixture: login missing"})
    monkeypatch.setattr(checker_health, "verify_context", verify)

    async def scenario() -> str:
        """Finish both closures and surface any asynchronous assertion failures."""
        try:
            summary = await asyncio.wait_for(checker_health.login_session(
                tmp_path / "browser_profile", expected_username="fixture",
            ), 40)
            await asyncio.gather(*closers)
            return summary
        finally:
            for context in contexts:
                await context.close()

    summary = asyncio.run(scenario())
    assert visits == ["https://www.instagram.com/accounts/login/", "https://www.threads.com/login"]
    assert closed == [0, 1, 2]
    assert "Threads: Fixture: login missing" in summary
    assert "Both logins verified" not in summary
    verify.assert_awaited_once_with(contexts[2], "combined", expected_username="fixture")
