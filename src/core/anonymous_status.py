"""Anonymous Instagram status checks with bounded polling and warm retries."""

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
ANONYMOUS_PAGE_READY_TIMEOUT_S = 30.0
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
        "account suspended", "account is suspended",
        "account has been suspended",
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
        await page.goto(
            source, wait_until="domcontentloaded", timeout=timeout_s * 1000,
        )
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
        reason = (
            f"Anonymous page could not be read ({type(exc).__name__}); "
            "status unknown."
        )
    return status_record(
        username, status, reason, time.monotonic() - started, source,
    )


def status_record(
    username: str, status: str, reason: str, seconds: float,
    source: str | None = None,
) -> dict:
    """Keep unavailable metadata empty and distinguish scope from failure."""
    error = None
    if status in ("unknown", "error"):
        error = reason or "Status could not be determined."
    ig = {
        "status": status, "country": None, "date_joined": None,
        "stage": "status_only", "country_availability": "unavailable_in_mode",
        "source_url": source, "error": error,
    }
    threads = {
        "status": None, "country": None, "date_joined": None,
        "stage": "skipped", "country_availability": "unavailable_in_mode",
    }
    record = build_record(
        username, ig, threads, seconds, MODE_IG_STATUS_ONLY,
    )
    record["checker_id"] = None
    return record


def anonymous_timeout_s(configured_s: float) -> float:
    """Allow cold startup without reducing a longer explicit budget."""
    return max(ANONYMOUS_PAGE_READY_TIMEOUT_S, configured_s)


async def run_anonymous(
    scraper: MultiWorkerScraper, users: list[str],
) -> list[dict]:
    """Run a fresh context, then retry Unknowns once with the warm cache."""
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for item in enumerate(users):
        queue.put_nowait(item)
    records: dict[int, dict] = {}
    emitted: set[int] = set()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            channel="chromium", headless=scraper.headless,
        )
        try:
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
            try:
                pages = await scraper._open_pages(
                    context, min(scraper.workers, len(users)),
                )
                await _run_pass(
                    scraper, pages, queue, records, emitted, retry=False,
                )
                pending = [
                    index for index, row in records.items()
                    if row["ig_status"] == "unknown"
                ]
                scraper._save_event({
                    "event": "anonymous_main_pass",
                    "unknown_count": len(pending),
                    "timeout_s": anonymous_timeout_s(
                        scraper.page_ready_timeout_s,
                    ),
                })
                attempts = 0
                if not scraper.is_stopped and pending:
                    for index in sorted(pending):
                        queue.put_nowait((index, users[index]))
                    attempts = await _run_pass(
                        scraper, pages, queue, records, emitted, retry=True,
                    )
                # A stop preserves attempted rows, including deferred Unknowns.
                for index, row in sorted(records.items()):
                    if index not in emitted:
                        _publish(scraper, index, row, emitted)
                scraper._save_event({
                    "event": "anonymous_retry_pass", "attempts": attempts,
                    "unknown_count": sum(
                        row["ig_status"] == "unknown"
                        for row in records.values()
                    ),
                })
            finally:
                await context.close()
        finally:
            await browser.close()
    return [records[index] for index in sorted(records)]


async def _run_pass(
    scraper: MultiWorkerScraper, pages: list[Page],
    queue: asyncio.Queue[tuple[int, str]], records: dict[int, dict],
    emitted: set[int], retry: bool,
) -> int:
    """Join main work before retrying and always cancel pending workers."""
    tasks = [asyncio.create_task(
        _consume(scraper, page, queue, records, emitted, retry),
    ) for page in pages]
    try:
        return sum(await asyncio.gather(*tasks))
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def _publish(
    scraper: MultiWorkerScraper, index: int, record: dict, emitted: set[int],
) -> None:
    """Emit exactly one final record and one progress increment per target."""
    emitted.add(index)
    scraper._done += 1
    scraper._emit(record)


async def _consume(
    scraper: MultiWorkerScraper, page: Page,
    queue: asyncio.Queue[tuple[int, str]], records: dict[int, dict],
    emitted: set[int], retry: bool,
) -> int:
    """Preserve pause/stop and finalize Unknown after one bounded retry."""
    attempts = 0
    while not scraper.is_stopped:
        await scraper._wait_while_paused()
        if scraper.is_stopped:
            break
        try:
            index, username = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        attempts += 1
        started = time.monotonic()
        try:
            record = await check_status(
                page, username,
                anonymous_timeout_s(scraper.page_ready_timeout_s),
            )
        except Exception as exc:
            logger.error("Anonymous target failed (%s)", type(exc).__name__)
            record = status_record(
                username, "unknown",
                f"Status check failed ({type(exc).__name__}).",
                time.monotonic() - started,
            )
        if retry:
            record["seconds"] = round(
                records[index]["seconds"] + record["seconds"], 2,
            )
        records[index] = record
        if retry or record["ig_status"] != "unknown":
            _publish(scraper, index, record, emitted)
        queue.task_done()
    return attempts
