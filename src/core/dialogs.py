"""Target-bound transparency dialog reading with completeness tracking."""

import asyncio
import logging
import time
from typing import Callable, Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from src.core.about_parser import has_username, parse_about_dialog
from src.core.browser_helpers import DIALOG_TIMEOUT_S, POLL_INTERVAL_S

logger = logging.getLogger(__name__)


async def _poll_dialog(
    page: Page, container_selectors: tuple[str, ...], max_chars: int = 2000,
    dialog_timeout_s: float = DIALOG_TIMEOUT_S,
    debug_sink: Optional[Callable[[str], None]] = None,
    expected_username: Optional[str] = None,
) -> dict:
    """Read only visible matching dialogs; allow remaining fields to arrive.

    A date-only dialog is returned at the deadline as partial data; a missing
    country is never guessed or replaced with a prior account's value.
    """
    best = {"date_joined": None, "join_badge": None, "country": None}
    deadline = time.monotonic() + dialog_timeout_s
    while time.monotonic() < deadline:
        for selector in container_selectors:
            dialogs = page.locator(selector)
            # Fallback div selectors also match page-sized ancestors. Inspect
            # descendants first so an enclosing bio cannot supply field values.
            for index in reversed(range(await dialogs.count())):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return best
                dialog = dialogs.nth(index)
                try:
                    if not await dialog.is_visible():
                        continue
                    text = await dialog.inner_text(timeout=max(1, min(1000, remaining * 1000)))
                except PlaywrightError as exc:
                    logger.debug("Dialog not readable: %s", exc)
                    continue
                if len(text) > max_chars:
                    continue
                if debug_sink is not None:
                    debug_sink(text)
                if expected_username and not has_username(text, expected_username):
                    continue
                parsed = parse_about_dialog(text)
                score = sum(bool(parsed[key]) for key in ("date_joined", "country"))
                best_score = sum(bool(best[key]) for key in ("date_joined", "country"))
                if score and score >= best_score:
                    best = parsed
                if parsed["date_joined"] and parsed["country"]:
                    return parsed
        await asyncio.sleep(min(POLL_INTERVAL_S, max(0, deadline - time.monotonic())))
    return best
