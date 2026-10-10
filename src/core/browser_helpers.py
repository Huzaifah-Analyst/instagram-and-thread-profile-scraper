"""Bounded browser actions and profile-identity verification."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.about_parser import detect_session_challenge, is_not_found_page

logger = logging.getLogger(__name__)
NAVIGATION_TIMEOUT_MS = 30_000
PAGE_READY_TIMEOUT_S = 10.0
DIALOG_TIMEOUT_S = 10.0
MENU_CLICK_TIMEOUT_S = 8.0
POLL_INTERVAL_S = 0.25
CLICK_ACTION_TIMEOUT_MS = 5_000


async def _body_text(page: Page) -> str:
    """Read visible page text with a short deadline."""
    try:
        return await page.inner_text("body", timeout=1500)
    except PlaywrightError as exc:
        logger.debug("Body not readable: %s", exc)
        return ""


async def _open_profile(
    page: Page, url: str, ready_selector: str,
    page_ready_timeout_s: float = PAGE_READY_TIMEOUT_S,
) -> str:
    """Navigate and wait for a visible profile header or a known failure."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        logger.warning("Navigation incomplete for %s: %s", url, exc)
    deadline = time.monotonic() + page_ready_timeout_s
    body = ""
    while time.monotonic() < deadline:
        body = await _body_text(page)
        if detect_session_challenge(page.url, body) or is_not_found_page(body):
            return body
        if await _first_visible([page.locator(ready_selector)]):
            return body
        await asyncio.sleep(POLL_INTERVAL_S)
    return body


async def _first_visible(candidates: list[Locator]) -> Optional[Locator]:
    """Examine every match, rather than only a possibly-hidden first/last one."""
    for group in candidates:
        for index in range(await group.count()):
            locator = group.nth(index)
            try:
                if await locator.is_visible():
                    return locator
            except PlaywrightError as exc:
                logger.debug("Candidate disappeared: %s", exc)
    return None


async def _safe_click(locator: Locator, timeout_ms: int = CLICK_ACTION_TIMEOUT_MS) -> None:
    """Bound all click fallbacks, including JS locator resolution/evaluation."""
    async def attempt() -> None:
        """Use normal, forced and JS click in that order, recording failures."""
        try:
            await locator.click(timeout=timeout_ms)
            return
        except PlaywrightError as exc:
            logger.debug("Plain click failed: %s", exc)
        try:
            await locator.click(timeout=timeout_ms, force=True)
            return
        except PlaywrightError as exc:
            logger.debug("Forced click failed: %s", exc)
        await locator.evaluate(
            "el => { const target = el.closest('button,[role=button]') || el; "
            "target.dispatchEvent(new MouseEvent('click', {bubbles:true})); }",
            timeout=timeout_ms,
        )

    try:
        await asyncio.wait_for(attempt(), timeout=3 * timeout_ms / 1000)
    except asyncio.TimeoutError as exc:
        raise PlaywrightTimeoutError("Click fallback deadline exceeded") from exc


async def _click_menu_item(
    page: Page, texts: tuple[str, ...], timeout_s: float = MENU_CLICK_TIMEOUT_S,
) -> bool:
    """Poll all visible exact menu-label matches within a whole-action budget."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        item = await _first_visible([page.get_by_text(text, exact=True) for text in texts])
        if item is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            try:
                await asyncio.wait_for(_safe_click(item), timeout=remaining)
                return True
            except asyncio.TimeoutError:
                logger.warning("Menu click exceeded %.2fs", timeout_s)
                return False
        await asyncio.sleep(min(POLL_INTERVAL_S, max(0, deadline - time.monotonic())))
    return False


async def profile_matches(page: Page, username: str, platform: str) -> bool:
    """Require the requested final URL and matching visible profile identity."""
    parsed_url = urlparse(page.url)
    allowed = {"instagram.com", "www.instagram.com"} if platform == "ig" else {
        "threads.com", "www.threads.com", "threads.net", "www.threads.net",
    }
    if parsed_url.hostname not in allowed:
        return False
    path = parsed_url.path.strip("/").lstrip("@")
    if path.casefold() != username.casefold():
        return False
    selector = "header h1, header h2" if platform == "ig" else (
        "div[aria-label='Column body'] h1, [role='main'] h1, header h1"
    )
    headers = page.locator(selector)
    for index in range(await headers.count()):
        header = headers.nth(index)
        if await header.is_visible():
            text = (await header.inner_text(timeout=1000)).strip().lstrip("@")
            if text.casefold() == username.casefold():
                return True
    # Threads headings may be display names; require the handle itself visible.
    if platform == "threads":
        return await _first_visible([page.get_by_text(username, exact=True)]) is not None
    return False


async def _dismiss(page: Page) -> None:
    """Close any open menu/dialog before reusing the page."""
    for _ in range(2):
        try:
            await page.keyboard.press("Escape")
        except PlaywrightError as exc:
            logger.debug("Dismiss failed: %s", exc)


def _short_error(prefix: str, exc: Exception) -> str:
    """Keep the row error concise while logs retain full details."""
    return f"{prefix}: {str(exc).splitlines()[0] if str(exc) else type(exc).__name__}"
