"""Instagram and Threads profile extractors (TSK-102, TSK-103).

Each extractor opens a profile, classifies it (active / private / not found /
session blocked), then opens Meta's transparency dialog ("About this account"
or "About this profile") and reads the joined date and country.

The text parsing lives in small pure functions so it can be unit tested
without a browser.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.core.ban_engine import (
    STATUS_ACTIVE,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_PRIVATE,
    STATUS_SESSION_BLOCKED,
)

logger = logging.getLogger(__name__)

INSTAGRAM_URL = "https://www.instagram.com/{username}/"
THREADS_URL = "https://www.threads.com/@{username}"

NAVIGATION_TIMEOUT_MS = 30_000
PAGE_READY_TIMEOUT_S = 8.0
DIALOG_TIMEOUT_S = 8.0
POLL_INTERVAL_S = 0.25

# Label lines in the transparency dialogs (compared lower-cased, exact line).
DATE_KEYS = ("date joined", "joined", "date of creation", "katılma tarihi")
COUNTRY_KEYS = (
    "account based in", "based in", "account location", "location",
    "hesabın bulunduğu konum", "konum",
)

ABOUT_IG_TEXTS = ("About this account", "Bu hesap hakkında")
ABOUT_THREADS_TEXTS = ("About this profile", "Bu profil hakkında")

NOT_FOUND_MARKERS = (
    "sorry, this page isn't available",
    "this page isn't available",
    "profile isn't available",
    "the profile may have been removed",
    "üzgünüz, bu sayfaya ulaşılamıyor",
    "profil kullanılamıyor",
    "sayfa bulunamadı",
    "sayfa kullanılamıyor",
)
PRIVATE_MARKERS = ("this account is private", "bu hesap gizli")
CHALLENGE_PATH_PREFIXES = ("/accounts/login", "/login", "/challenge", "/checkpoint", "/auth_platform")
CHALLENGE_MARKERS = (
    "suspicious activity",
    "please wait a few minutes before you try again",
    "we restrict certain activity",
    "help us confirm it's you",
    "confirm you're a human",
    "hesabın geçici olarak kilitlendi",
    "olağan dışı hareket",
)

_BADGE_RE = re.compile(r"^(#\s?[\d.,]+|[\d.,]+\s?[KMB]\+?)$", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Pure parsing helpers
# --------------------------------------------------------------------------- #

def detect_session_challenge(url: str, body_text: str) -> Optional[str]:
    """Detects a login wall, checkpoint or rate-limit page on the checker session.

    Args:
        url: Current page URL.
        body_text: Visible body text of the page.

    Returns:
        A reason string if a challenge was detected, otherwise ``None``.
    """
    path = urlparse(url).path.lower().rstrip("/")
    # Match whole path segments so a username like "loginking" is not a login page.
    if any(path == p or path.startswith(p + "/") for p in CHALLENGE_PATH_PREFIXES):
        return f"Redirected to {url}"
    lowered = body_text.lower()
    for marker in CHALLENGE_MARKERS:
        if marker in lowered:
            return f"Challenge text detected: '{marker}'"
    return None


def is_not_found_page(body_text: str) -> bool:
    """Returns ``True`` if the body shows Meta's "page isn't available" error."""
    lowered = body_text.lower()
    return any(marker in lowered for marker in NOT_FOUND_MARKERS)


def is_private_profile(body_text: str) -> bool:
    """Returns ``True`` if the Instagram body shows the private-account notice."""
    lowered = body_text.lower()
    return any(marker in lowered for marker in PRIVATE_MARKERS)


def _value_after_label(lines: list[str], keys: tuple[str, ...]) -> Optional[str]:
    """Finds the first line equal to one of ``keys`` and returns the next line."""
    for idx, line in enumerate(lines[:-1]):
        if line.lower() in keys:
            return lines[idx + 1]
    return None


def split_threads_joined(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Splits a Threads "Joined" value like ``September 2023 · 100M+``.

    Args:
        raw: Raw value text below the "Joined" label.

    Returns:
        Tuple of ``(date_joined, join_badge)``; either may be ``None``.
    """
    parts = [p.strip() for p in raw.split("·") if p.strip()]
    date_joined: Optional[str] = None
    badge: Optional[str] = None
    for part in parts:
        if badge is None and _BADGE_RE.match(part):
            badge = part
        elif date_joined is None:
            date_joined = part
    return date_joined, badge


def parse_about_dialog(text: str) -> dict:
    """Parses transparency dialog text into joined date, badge and country.

    Works for both the Instagram "About this account" dialog and the Threads
    "About this profile" panel, in English and Turkish.

    Args:
        text: ``inner_text`` of the dialog.

    Returns:
        Dict with ``date_joined``, ``join_badge`` and ``country`` (``None`` if missing).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    raw_date = _value_after_label(lines, DATE_KEYS)
    country = _value_after_label(lines, COUNTRY_KEYS)
    date_joined, badge = split_threads_joined(raw_date) if raw_date else (None, None)
    return {"date_joined": date_joined, "join_badge": badge, "country": country}


# --------------------------------------------------------------------------- #
# Browser helpers
# --------------------------------------------------------------------------- #

async def _body_text(page: Page) -> str:
    """Returns the page body text, or an empty string if it is not readable yet."""
    try:
        return await page.inner_text("body", timeout=2_000)
    except (PlaywrightTimeoutError, PlaywrightError) as exc:
        logger.debug("Body text not readable yet: %s", exc)
        return ""


async def _open_profile(page: Page, url: str, ready_selector: str) -> str:
    """Navigates to a profile and polls until it is classifiable.

    Args:
        page: Worker page.
        url: Profile URL.
        ready_selector: Selector that indicates the profile header has rendered.

    Returns:
        The body text at the moment the page became classifiable (or timed out).
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        logger.warning("Navigation timeout for %s, continuing with partial page", url)

    deadline = time.monotonic() + PAGE_READY_TIMEOUT_S
    body = ""
    while time.monotonic() < deadline:
        body = await _body_text(page)
        if (
            detect_session_challenge(page.url, body)
            or is_not_found_page(body)
            or await page.locator(ready_selector).count()
        ):
            return body
        await asyncio.sleep(POLL_INTERVAL_S)
    return body


async def _first_visible(candidates: list[Locator]) -> Optional[Locator]:
    """Returns the first candidate locator that is attached and visible."""
    for locator in candidates:
        try:
            if await locator.count() and await locator.is_visible():
                return locator
        except PlaywrightError as exc:
            logger.debug("Locator check failed: %s", exc)
    return None


async def _click_menu_item(page: Page, texts: tuple[str, ...]) -> bool:
    """Waits for a menu item with any of ``texts`` and clicks it.

    Returns:
        ``True`` if an item was clicked.
    """
    deadline = time.monotonic() + 4.0
    while time.monotonic() < deadline:
        candidates = [page.get_by_text(t, exact=True).last for t in texts]
        item = await _first_visible(candidates)
        if item is not None:
            await item.click()
            return True
        await asyncio.sleep(POLL_INTERVAL_S)
    return False


async def _poll_dialog(page: Page, container_selectors: tuple[str, ...], max_chars: int = 2_000) -> dict:
    """Polls the transparency dialog until a date or country is parsed.

    Args:
        page: Worker page.
        container_selectors: Selectors that may hold the dialog content.
        max_chars: Containers with longer text are skipped, so broad fallback
            selectors cannot match the whole page (and a bio line).

    Returns:
        Parsed dict from ``parse_about_dialog`` (all ``None`` on timeout).
    """
    empty = {"date_joined": None, "join_badge": None, "country": None}
    deadline = time.monotonic() + DIALOG_TIMEOUT_S
    while time.monotonic() < deadline:
        for selector in container_selectors:
            dialogs = page.locator(selector)
            for i in range(await dialogs.count()):
                try:
                    text = await dialogs.nth(i).inner_text(timeout=1_000)
                except (PlaywrightTimeoutError, PlaywrightError):
                    continue
                if len(text) > max_chars:
                    continue
                parsed = parse_about_dialog(text)
                if parsed["date_joined"] or parsed["country"]:
                    return parsed
        await asyncio.sleep(POLL_INTERVAL_S)
    return empty


async def _dismiss(page: Page) -> None:
    """Closes any open menu/dialog (Escape twice, per memory.md quirk #3)."""
    for _ in range(2):
        try:
            await page.keyboard.press("Escape")
        except PlaywrightError as exc:
            logger.debug("Escape press failed: %s", exc)


def _result(**fields: object) -> dict:
    """Builds an extractor result dict with all keys present."""
    base = {
        "status": STATUS_ERROR,
        "date_joined": None,
        "join_badge": None,
        "country": None,
        "seconds": 0.0,
        "error": None,
    }
    base.update(fields)
    return base


# --------------------------------------------------------------------------- #
# Instagram (TSK-102)
# --------------------------------------------------------------------------- #

async def extract_instagram(page: Page, username: str) -> dict:
    """Checks an Instagram profile and reads its transparency data.

    Args:
        page: Worker page from a logged-in persistent context.
        username: Instagram username without ``@``.

    Returns:
        Dict with ``status``, ``date_joined``, ``country``, ``seconds`` and ``error``.
    """
    t0 = time.monotonic()
    res = _result()
    try:
        # "header h2" is the profile username; a bare <header> also exists on error pages.
        body = await _open_profile(page, INSTAGRAM_URL.format(username=username), "header h2, header h1")

        challenge = detect_session_challenge(page.url, body)
        if challenge:
            res.update(status=STATUS_SESSION_BLOCKED, error=f"IG session blocked: {challenge}")
            return res
        if is_not_found_page(body):
            res["status"] = STATUS_NOT_FOUND
            return res

        res["status"] = STATUS_PRIVATE if is_private_profile(body) else STATUS_ACTIVE

        options = await _first_visible([
            page.locator("header svg[aria-label='Options']").first,
            page.locator("header svg[aria-label='Seçenekler']").first,
            page.locator("header [role='button']:has(svg[aria-label*='Options'])").first,
            page.locator("header div[aria-haspopup='dialog']").first,
        ])
        if options is None:
            res["error"] = "IG options (...) button not found"
            return res
        await options.click()

        if not await _click_menu_item(page, ABOUT_IG_TEXTS):
            res["error"] = "IG 'About this account' option not found"
            return res

        parsed = await _poll_dialog(page, ("div[role='dialog']",))
        res.update(date_joined=parsed["date_joined"], country=parsed["country"])
        if not (parsed["date_joined"] or parsed["country"]):
            res["error"] = "IG about dialog did not load within timeout"
    except PlaywrightError as exc:
        logger.warning("Instagram extraction failed for %s: %s", username, exc)
        res["error"] = f"IG error: {exc}"
    finally:
        await _dismiss(page)
        res["seconds"] = round(time.monotonic() - t0, 2)
    return res


# --------------------------------------------------------------------------- #
# Threads (TSK-103)
# --------------------------------------------------------------------------- #

async def _find_threads_menu_button(page: Page) -> Optional[Locator]:
    """Locates the Threads profile ``···`` button by SVG position.

    The button has no stable label, so we take the right-most SVG inside the
    profile header band (``100 < y < 350`` and ``x > 600`` at 1280px width).
    """
    card = page.locator("div[aria-label='Column body'], div[role='main']").first
    if not await card.count():
        return None
    candidates: list[tuple[float, Locator]] = []
    svgs = card.locator("svg")
    for i in range(await svgs.count()):
        svg = svgs.nth(i)
        try:
            box = await svg.bounding_box()
        except PlaywrightError:
            continue
        if box and 100 < box["y"] < 350 and box["x"] > 600:
            candidates.append((box["x"], svg))
    if not candidates:
        return None
    _, svg = max(candidates, key=lambda c: c[0])
    clickable = svg.locator("xpath=ancestor-or-self::div[@role='button' or @tabindex='0' or @aria-haspopup][1]")
    return clickable if await clickable.count() else svg


async def extract_threads(page: Page, username: str) -> dict:
    """Checks a Threads profile and reads its transparency data.

    Args:
        page: Worker page from a logged-in persistent context.
        username: Threads username without ``@``.

    Returns:
        Dict with ``status``, ``date_joined``, ``join_badge``, ``country``,
        ``seconds`` and ``error``.
    """
    t0 = time.monotonic()
    res = _result()
    try:
        body = await _open_profile(
            page, THREADS_URL.format(username=username), "div[aria-label='Column body'] h1, div[role='main'] h1"
        )

        challenge = detect_session_challenge(page.url, body)
        if challenge:
            res.update(status=STATUS_SESSION_BLOCKED, error=f"Threads session blocked: {challenge}")
            return res
        if is_not_found_page(body):
            res["status"] = STATUS_NOT_FOUND
            return res

        res["status"] = STATUS_ACTIVE

        menu = await _find_threads_menu_button(page)
        if menu is None:
            # Inactive profiles often have no menu (memory.md quirk #1).
            res["error"] = "Threads profile menu not found"
            return res
        await menu.click()

        if not await _click_menu_item(page, ABOUT_THREADS_TEXTS):
            res["error"] = "Threads 'About this profile' option not found"
            return res

        # Threads sometimes renders the panel without role=dialog; fall back to
        # the smallest container holding the "Based in" label.
        parsed = await _poll_dialog(page, ("div[role='dialog']", "div:has-text('Based in')"), max_chars=400)
        res.update(parsed)
        if not (parsed["date_joined"] or parsed["country"]):
            res["error"] = "Threads about panel did not load within timeout"
    except PlaywrightError as exc:
        logger.warning("Threads extraction failed for %s: %s", username, exc)
        res["error"] = f"Threads error: {exc}"
    finally:
        await _dismiss(page)
        res["seconds"] = round(time.monotonic() - t0, 2)
    return res
