"""Instagram/Threads extraction with explicit identity, stage and evidence."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page

from src.core.about_parser import (
    ABOUT_IG_TEXTS, ABOUT_THREADS_TEXTS, COUNTRY_KEYS, DATE_KEYS,
    country_is_disclosed, detect_session_challenge, is_not_found_page, is_private_profile,
    parse_about_dialog, split_threads_joined,
)
from src.core.ban_engine import (
    STATUS_ACTIVE, STATUS_ERROR, STATUS_NOT_FOUND, STATUS_PRIVATE,
    STATUS_SESSION_BLOCKED,
)
from src.core.browser_helpers import (
    CLICK_ACTION_TIMEOUT_MS, DIALOG_TIMEOUT_S, MENU_CLICK_TIMEOUT_S,
    PAGE_READY_TIMEOUT_S, POLL_INTERVAL_S, _body_text, _click_menu_item,
    _dismiss, _first_visible, _open_profile, _safe_click, _short_error,
    profile_matches,
)
from src.core.diagnostics import capture_page
from src.core.dialogs import _poll_dialog
from src.core.paths import DEBUG_DIR
from src.core.validation import clean_usernames, positive_seconds

logger = logging.getLogger(__name__)
INSTAGRAM_URL = "https://www.instagram.com/{username}/"
THREADS_URL = "https://www.threads.com/@{username}"


def _write_debug_dump(platform: str, username: str, texts: list[str]) -> None:
    """Retain raw dialog text locally; evidence I/O must not crash a run."""
    if not texts:
        return
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        (DEBUG_DIR / f"{platform}_{username}_{stamp}.txt").write_text(
            "\n\n---\n\n".join(texts), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("Could not write dialog dump for %s/%s: %s", platform, username, exc)


def _result(**fields: object) -> dict:
    """Build a fresh result; no data is reused between target accounts."""
    result = {
        "status": STATUS_ERROR, "date_joined": None, "join_badge": None,
        "country": None, "seconds": 0.0, "error": None, "stage": "navigate",
        "source_url": None, "evidence": None,
        "evidence_steps": [],
    }
    result.update(fields)
    return result


async def _failure(page: Page, result: dict, message: str) -> None:
    """Re-check late login/challenge UI before reporting a menu/dialog failure."""
    challenge = detect_session_challenge(page.url, await _body_text(page))
    if challenge:
        result.update(status=STATUS_SESSION_BLOCKED, error=challenge)
    else:
        result["error"] = message


async def _find_threads_menu_button(page: Page) -> Optional[Locator]:
    """Find a named More/Options icon in the profile band, not any rightmost SVG."""
    card = page.locator("div[aria-label='Column body'], div[role='main']").first
    if not await card.count():
        return None
    icons = card.locator(
        "svg[title='More'], svg[aria-label='More'], svg[aria-label='Options'], "
        "svg:has(title:text-is('More')), svg[aria-label='Diğer']"
    )
    for index in range(await icons.count()):
        icon = icons.nth(index)
        try:
            if not await icon.is_visible():
                continue
            box = await icon.bounding_box(timeout=1000)
            if not box or not 80 < box["y"] < 350:
                continue
            button = icon.locator("xpath=ancestor::*[self::button or @role='button'][1]")
            if await button.count():
                return button
        except PlaywrightError as exc:
            logger.debug("Threads profile menu candidate failed: %s", exc)
    return None


async def _options(page: Page, platform: str, budget: float) -> Optional[Locator]:
    """Wait for a named profile control after the header becomes available."""
    deadline = time.monotonic() + budget
    while time.monotonic() < deadline:
        if platform == "threads":
            found = await _find_threads_menu_button(page)
        else:
            found = await _first_visible([
                page.locator("header svg[aria-label='Options']"),
                page.locator("header svg[aria-label='Seçenekler']"),
                page.locator("header [role='button'][aria-haspopup='dialog']"),
            ])
        if found is not None:
            return found
        await asyncio.sleep(POLL_INTERVAL_S)
    return None


async def _extract(
    page: Page, username: str, platform: str, page_ready_timeout_s: float,
    dialog_timeout_s: float, menu_click_timeout_s: float, debug_dump: bool,
) -> dict:
    """Execute a staged check with truthful partial/error results and captures."""
    username = clean_usernames([username])[0]
    for value in (page_ready_timeout_s, dialog_timeout_s, menu_click_timeout_s):
        positive_seconds(value)
    started = time.monotonic()
    result = _result()
    captured: list[str] = []
    label = "IG" if platform == "ig" else "Threads"
    url = (INSTAGRAM_URL if platform == "ig" else THREADS_URL).format(username=username)
    ready = "header h2, header h1" if platform == "ig" else (
        "div[aria-label='Column body'] h1, div[role='main'] h1"
    )
    try:
        body = await _open_profile(page, url, ready, page_ready_timeout_s)
        result["source_url"] = page.url
        challenge = detect_session_challenge(page.url, body)
        if challenge:
            result.update(status=STATUS_SESSION_BLOCKED, error=f"{label}: {challenge}")
            return result
        if is_not_found_page(body):
            result["status"] = STATUS_NOT_FOUND
            return result
        result["stage"] = "identity"
        if not await profile_matches(page, username, platform):
            await _failure(page, result, f"{label} profile identity could not be verified")
            return result
        result["status"] = STATUS_PRIVATE if is_private_profile(body) else STATUS_ACTIVE
        result["stage"] = "profile_menu"
        options = await _options(page, platform, page_ready_timeout_s)
        if options is None:
            await _failure(page, result, f"{label} profile menu not found")
            return result
        await _safe_click(options)
        result["stage"] = "about_menu"
        if debug_dump:
            result["evidence_steps"].append(
                await capture_page(page, platform, username, "profile_menu_open")
            )
        texts = ABOUT_IG_TEXTS if platform == "ig" else ABOUT_THREADS_TEXTS
        if not await _click_menu_item(page, texts, timeout_s=menu_click_timeout_s):
            await _failure(page, result, f"{label} About option not found")
            return result
        if debug_dump:
            result["evidence_steps"].append(
                await capture_page(page, platform, username, "about_clicked")
            )
        result["stage"] = "about_dialog"
        selectors = ("div[role='dialog']",)
        if platform == "threads":
            selectors += ("div:has-text('Based in')", "div:has-text('Konum')")
        parsed = await _poll_dialog(
            page, selectors, max_chars=2000, dialog_timeout_s=dialog_timeout_s,
            debug_sink=captured.append if debug_dump else None,
            expected_username=username,
        )
        result.update(parsed)
        missing = [name for name in ("date_joined", "country") if not parsed[name]]
        if parsed["country"] and not country_is_disclosed(parsed["country"]):
            result["country_availability"] = "not_shared"
            result["error"] = f"{label} About: country not shared by platform"
            if not missing:
                result["stage"] = "complete"
            else:
                result["error"] += f"; not available/loaded: {', '.join(missing)}"
        elif missing:
            await _failure(page, result, f"{label} About: not available/loaded: {', '.join(missing)}")
        else:
            result["stage"] = "complete"
    except PlaywrightError as exc:
        logger.warning("%s extraction failed at %s: %s", label, result["stage"], exc)
        await _failure(page, result, _short_error(f"{label} error", exc))
    finally:
        result["source_url"] = page.url
        if debug_dump:
            _write_debug_dump(platform, username, captured)
            result["evidence"] = await capture_page(page, platform, username, result["stage"])
        await _dismiss(page)
        result["seconds"] = round(time.monotonic() - started, 2)
    return result


async def extract_instagram(
    page: Page, username: str,
    page_ready_timeout_s: float = PAGE_READY_TIMEOUT_S,
    dialog_timeout_s: float = DIALOG_TIMEOUT_S,
    menu_click_timeout_s: float = MENU_CLICK_TIMEOUT_S,
    debug_dump: bool = False,
) -> dict:
    """Read Instagram transparency from a verified target profile/dialog."""
    return await _extract(page, username, "ig", page_ready_timeout_s,
                          dialog_timeout_s, menu_click_timeout_s, debug_dump)


async def extract_threads(
    page: Page, username: str,
    page_ready_timeout_s: float = PAGE_READY_TIMEOUT_S,
    dialog_timeout_s: float = DIALOG_TIMEOUT_S,
    menu_click_timeout_s: float = MENU_CLICK_TIMEOUT_S,
    debug_dump: bool = False,
) -> dict:
    """Read Threads transparency or report the login/menu failure stage."""
    return await _extract(page, username, "threads", page_ready_timeout_s,
                          dialog_timeout_s, menu_click_timeout_s, debug_dump)
