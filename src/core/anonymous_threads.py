"""Read public Threads status without a checker session or About panel."""

from __future__ import annotations

import asyncio
import logging
import time
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from src.core.about_parser import is_not_found_page
from src.core.browser_helpers import profile_matches

logger = logging.getLogger(__name__)


def classify_threads_status(text: str, identity_verified: bool) -> str:
    """Require identity for Alive and explicit text for missing pages."""
    if identity_verified:
        lines = {line.strip().casefold() for line in text.splitlines()}
        private = {"this profile is private", "this account is private"}
        return "private" if lines & private else "active"
    if is_not_found_page(text):
        return "not_found"
    return "unknown"


async def check_threads_status(
    page: Page, username: str, timeout_s: float,
) -> dict:
    """Poll public identity or missing-page markers; never infer from login."""
    started = time.monotonic()
    deadline = started + timeout_s
    source = f"https://www.threads.com/@{username}"
    result = {
        "status": "unknown", "stage": "status_only",
        "country": None, "date_joined": None, "source_url": source,
        "error": "Threads: no decision marker before the status deadline.",
    }
    try:
        await page.goto(
            source, wait_until="commit", timeout=timeout_s * 1000,
        )
        while time.monotonic() < deadline:
            path = urlparse(page.url).path.rstrip("/")
            if path == "/login" or path.startswith("/accounts/login"):
                result.update(
                    stage="login_required",
                    error="Threads requires login to confirm this profile; "
                          "its public status is unknown.",
                )
                break
            remaining_ms = max(1, (deadline - time.monotonic()) * 1000)
            text = await page.locator("body").inner_text(timeout=remaining_ms)
            identity = await profile_matches(page, username, "threads")
            status = classify_threads_status(text, identity)
            if status != "unknown":
                result.update(status=status, error=None)
                break
            await asyncio.sleep(min(.25, max(0, deadline - time.monotonic())))
    except PlaywrightError as exc:
        logger.warning("Public Threads read failed (%s)", type(exc).__name__)
        result["error"] = (
            f"Threads public page unreadable ({type(exc).__name__}); "
            "status unknown."
        )
    result["source_url"] = page.url
    result["seconds"] = round(time.monotonic() - started, 2)
    return result
