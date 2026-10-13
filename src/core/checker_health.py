"""Live per-platform preflight and interactive IG/Threads session setup."""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Callable

from playwright.async_api import BrowserContext, BrowserType, Page, async_playwright
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
            if debug_dump:
                await capture_page(page, platform, "checker", "preflight_loading")
            return f"{platform} session could not be verified: page did not load"
        reason = detect_session_challenge(page.url, body)
        if not reason and "Not all who wander are lost, but this page is" in body:
            reason = f"{platform} home page unavailable; platform returned its broken-link page"
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
        try:
            results[platform] = await verify_platform(page, platform, debug_dump)
            if not results[platform] and expected_username:
                deadline = time.monotonic() + 5
                while not await identity_matches(page, platform, expected_username):
                    if time.monotonic() >= deadline:
                        results[platform] = f"{platform} imported checker identity could not be verified"
                        break
                    await asyncio.sleep(.25)
        except Exception as exc:
            results[platform] = f"{platform} preflight failed ({type(exc).__name__})"
            logger.warning(results[platform])
    return results


async def _manual_window(
    browser: BrowserType, profile_dir: Path, url: str,
    cancel: threading.Event | None,
) -> bool:
    """Open one login tab until the user closes it; return false on cancellation."""
    context = await browser.launch_persistent_context(
        str(profile_dir), channel="chromium", headless=False,
        no_viewport=True, args=["--start-maximized"],
    )
    closed = asyncio.Event()
    context.on("close", lambda *_: closed.set())
    try:
        page = context.pages[0] if context.pages else await context.new_page()
        for extra in context.pages[1:]:
            await extra.close()
        try:
            await page.goto(url, wait_until="domcontentloaded")
        except PlaywrightError:
            if not closed.is_set():
                raise
            logger.info("User closed the login window during navigation")
        while not closed.is_set():
            if cancel is not None and cancel.is_set():
                return False
            await asyncio.sleep(.2)
        return cancel is None or not cancel.is_set()
    finally:
        await context.close()


async def login_session(
    profile_dir: Path, expected_username: str | None = None,
    progress: Callable[[str], None] | None = None,
    cancel: threading.Event | None = None,
) -> str:
    """Run manual IG then Threads windows on one saved profile and verify both."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    notify = progress or logger.info
    async with async_playwright() as pw:
        for name, url in (
            ("Instagram", "https://www.instagram.com/accounts/login/"),
            ("Threads", "https://www.threads.com/login"),
        ):
            if cancel is not None and cancel.is_set():
                return "Setup cancelled; logins were not verified."
            notify(f"Log in to {name}, then close that browser window to continue.")
            if not await _manual_window(pw.chromium, profile_dir, url, cancel):
                return "Setup cancelled; logins were not verified."
        notify("Checking Instagram and Threads logins live...")
        context = await pw.chromium.launch_persistent_context(
            str(profile_dir), channel="chromium", headless=True,
            viewport={"width": 1280, "height": 800},
        )
        try:
            health = await verify_context(
                context, "combined", expected_username=expected_username,
            )
        finally:
            await context.close()
    lines = ["Both logins verified." if not any(health.values())
             else "Setup needs attention; see platform results."]
    for platform, name in (("ig", "Instagram"), ("threads", "Threads")):
        lines.append(f"{name}: {health[platform] or 'Logged in (live verified)'}")
    return "\n".join(lines)
