"""Live per-platform preflight and interactive IG/Threads session setup."""

import asyncio
import logging
import time
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

from src.core.about_parser import detect_session_challenge
from src.core.browser_helpers import _body_text
from src.core.diagnostics import capture_page
from src.core.login_flow import identity_matches

logger = logging.getLogger(__name__)
PLATFORM_URLS = {"ig": "https://www.instagram.com/", "threads": "https://www.threads.com/"}


async def verify_platform(page: Page, platform: str, debug_dump: bool = False) -> str | None:
    """Verify a loaded platform home page and its own session cookie together."""
    url = PLATFORM_URLS[platform]
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Hydration can initially render an empty shell. Wait for readable UI.
        deadline = time.monotonic() + 10
        body = ""
        while time.monotonic() < deadline:
            body = await _body_text(page)
            if len(body.strip()) > 40 or detect_session_challenge(page.url, body):
                break
            await asyncio.sleep(.25)
        if len(body.strip()) <= 40 and not detect_session_challenge(page.url, body):
            return f"{platform} session could not be verified: page did not load"
        reason = detect_session_challenge(page.url, body)
        if not reason:
            cookies = await page.context.cookies(url)
            if not any(cookie["name"] == "sessionid" for cookie in cookies):
                reason = f"{platform} login required: no platform session cookie"
        if reason and debug_dump:
            await capture_page(page, platform, "checker", "preflight")
        return reason
    except PlaywrightError as exc:
        logger.warning("%s live preflight failed: %s", platform, exc)
        if debug_dump:
            await capture_page(page, platform, "checker", "preflight_error")
        return f"{platform} session could not be verified: {str(exc).splitlines()[0]}"


async def verify_context(
    context: BrowserContext, mode: str, debug_dump: bool = False,
    expected_username: str | None = None,
) -> dict[str, str | None]:
    """Check every requested platform before assigning any targets to a checker."""
    page = context.pages[0] if context.pages else await context.new_page()
    platforms = ("ig", "threads") if mode == "combined" else (("ig",) if mode == "ig_only" else ("threads",))
    results: dict[str, str | None] = {}
    for platform in platforms:
        results[platform] = await verify_platform(page, platform, debug_dump)
        if not results[platform] and expected_username:
            deadline = time.monotonic() + 5
            while not await identity_matches(page, platform, expected_username):
                if time.monotonic() >= deadline:
                    results[platform] = f"{platform} imported checker identity could not be verified"
                    break
                await asyncio.sleep(.25)
        if results[platform]:
            break
    return results


async def login_session(profile_dir: Path) -> None:
    """Open both official login pages, bringing the first tab to the foreground."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            str(profile_dir), channel="chromium", headless=False,
            viewport={"width": 1280, "height": 800}
        )
        closed = asyncio.Event()
        context.on("close", lambda _context: closed.set())
        try:
            instagram = context.pages[0] if context.pages else await context.new_page()
            threads = await context.new_page()
            await instagram.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
            await threads.goto("https://www.threads.com/login", wait_until="domcontentloaded")
            await instagram.bring_to_front()
            logger.info("Complete Instagram AND Threads login in the two tabs, then close this browser.")
            await closed.wait()
        finally:
            await context.close()
