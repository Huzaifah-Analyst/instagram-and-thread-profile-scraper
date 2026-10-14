"""Logged-out Instagram status checks with fresh contexts and bounded polling."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import TYPE_CHECKING

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, async_playwright

from src.core.modes import MODE_IG_STATUS_ONLY
from src.core.result_records import build_record

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper

logger = logging.getLogger(__name__)
_COUNT = r"\d[\d,.]*(?:\s?[kmb])?"
_FOLLOWERS = re.compile(
    rf"\b{_COUNT}\s+followers?\b|\bfollowers?\s*:?\s*{_COUNT}\b",
    re.IGNORECASE,
)


def classify_status(text: str) -> str:
    """Use explicit page-text markers only; ambiguous pages remain unknown."""
    normalized = " ".join(text.casefold().replace("\u2019", "'").split())
    if any(marker in normalized for marker in (
        "profile isn't available", "page isn't available", "user not found",
    )):
        return "not_found"
    if any(marker in normalized for marker in (
        "account suspended", "account is suspended", "account has been suspended",
        "account was suspended", "we suspended your account",
    )):
        return "suspended"
    if _FOLLOWERS.search(normalized):
        return "active"
    return "unknown"


async def check_status(page: Page, username: str, timeout_s: float) -> dict:
    """Navigate and poll for a decision marker within a single time budget."""
    started = time.monotonic()
    deadline = started + timeout_s
    status = "unknown"
    reason = "No decision marker appeared before the status deadline."
    source = f"https://www.instagram.com/{username}/"
    try:
        await page.goto(source, wait_until="domcontentloaded", timeout=timeout_s * 1000)
        while time.monotonic() < deadline:
            remaining_ms = max(1, (deadline - time.monotonic()) * 1000)
            text = await page.locator("body").inner_text(timeout=remaining_ms)
            status = classify_status(text)
            if status != "unknown":
                reason = ""
                break
            await asyncio.sleep(min(.25, max(0, deadline - time.monotonic())))
    except PlaywrightError as exc:
        logger.warning("Anonymous status read failed (%s)", type(exc).__name__)
        reason = f"Anonymous page could not be read ({type(exc).__name__}); status unknown."
    return status_record(username, status, reason, time.monotonic() - started, source)


def status_record(username: str, status: str, reason: str,
                  seconds: float, source: str | None = None) -> dict:
    """Keep unavailable metadata empty and distinguish scope from failure."""
    error = (reason or "Status could not be determined.") if status in ("unknown", "error") else None
    ig = {"status": status, "country": None, "date_joined": None,
          "stage": "status_only", "country_availability": "unavailable_in_mode",
          "source_url": source, "error": error}
    threads = {"status": None, "country": None, "date_joined": None,
               "stage": "skipped", "country_availability": "unavailable_in_mode"}
    record = build_record(username, ig, threads, seconds, MODE_IG_STATUS_ONLY)
    record["checker_id"] = None
    return record


async def run_anonymous(scraper: MultiWorkerScraper, users: list[str]) -> list[dict]:
    """Share a fresh anonymous context across worker pages, without pacing."""
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for item in enumerate(users):
        queue.put_nowait(item)
    records: dict[int, dict] = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="chromium", headless=scraper.headless)
        try:
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            try:
                pages = await scraper._open_pages(context, min(scraper.workers, len(users)))
                tasks = [asyncio.create_task(_consume(scraper, page, queue, records)) for page in pages]
                try:
                    await asyncio.gather(*tasks)
                finally:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                await context.close()
        finally:
            await browser.close()
    return [records[index] for index in sorted(records)]


async def _consume(scraper: MultiWorkerScraper, page: Page,
                   queue: asyncio.Queue[tuple[int, str]], records: dict[int, dict]) -> None:
    """Preserve pause, stop, ordering and per-target error reporting without login."""
    while not scraper.is_stopped:
        await scraper._wait_while_paused()
        if scraper.is_stopped:
            return
        try:
            index, username = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        started = time.monotonic()
        try:
            record = await check_status(page, username, scraper.page_ready_timeout_s)
        except Exception as exc:
            logger.error("Anonymous target failed (%s)", type(exc).__name__)
            record = status_record(
                username, "unknown", f"Status check failed ({type(exc).__name__}).",
                time.monotonic() - started,
            )
        records[index] = record
        scraper._done += 1
        scraper._emit(record)
        queue.task_done()
