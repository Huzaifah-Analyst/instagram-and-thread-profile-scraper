"""Independent persistent contexts and a shared target queue."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

from src.core.checker_health import verify_context
from src.core.checkers import Checker
from src.core.resource_blocker import attach_resource_blocker

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper

logger = logging.getLogger(__name__)


async def run_pool(scraper: MultiWorkerScraper, users: list[str]) -> list[dict]:
    """Preflight all selected contexts, then run one worker per checker."""
    contexts: list[BrowserContext] = []
    workers: list[tuple[Checker, Page]] = []
    records: dict[int, dict] = {}
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for item in enumerate(users):
        queue.put_nowait(item)
    async with async_playwright() as pw:
        try:
            for checker in scraper.checkers[:scraper.workers]:
                if scraper.is_stopped:
                    break
                checker.profile_dir.mkdir(parents=True, exist_ok=True)
                context = await pw.chromium.launch_persistent_context(
                    str(checker.profile_dir), channel="chromium", headless=scraper.headless,
                    viewport={"width": 1280, "height": 800},
                )
                contexts.append(context)
                health = await verify_context(context, scraper.mode, scraper.debug_dump)
                scraper.checker_health[checker.checker_id] = health
                failure = next((reason for reason in health.values() if reason), None)
                if failure:
                    scraper.stop(f"Checker session blocked: {checker.checker_id}: {failure}. Use Setup for this checker.")
                    break
                page = context.pages[0]
                scraper.blocker_stats.append(await attach_resource_blocker(page))
                workers.append((checker, page))
            if not scraper.is_stopped:
                tasks = [asyncio.create_task(
                    _consume(scraper, checker, page, queue, records)
                ) for checker, page in workers]
                try:
                    await asyncio.gather(*tasks)
                finally:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            for context in contexts:
                try:
                    await context.close()
                except PlaywrightError as exc:
                    logger.warning("Checker browser close failed: %s", exc)
    return [records[index] for index in sorted(records)]


async def _consume(
    scraper: MultiWorkerScraper, checker: Checker, page: Page,
    queue: asyncio.Queue[tuple[int, str]], records: dict[int, dict],
) -> None:
    """Claim each target once and pace independently; a challenge stops the pool."""
    import random

    while not scraper.is_stopped:
        await scraper._wait_while_paused()
        if scraper.is_stopped:
            return
        try:
            index, username = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        record = await scraper._check_account(page, username)
        record["checker_id"] = checker.checker_id
        records[index] = record
        scraper._done += 1
        scraper._emit(record)
        queue.task_done()
        if record["composite_status"] == "BLOCKED":
            scraper.checker_health[checker.checker_id] = {"error": record["error_message"]}
            scraper.stop(f"Checker session blocked: {checker.checker_id}: {record['error_message']}")
            return
        if not queue.empty():
            await scraper._interruptible_sleep(random.uniform(scraper.min_delay, scraper.max_delay))
