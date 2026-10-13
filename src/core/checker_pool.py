"""Independent persistent contexts and a shared target queue."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from playwright.async_api import BrowserContext, Page, async_playwright

from src.core.checker_health import verify_context
from src.core.checkers import Checker
from src.core.resource_blocker import attach_resource_blocker

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper

logger = logging.getLogger(__name__)


async def run_pool(scraper: MultiWorkerScraper, users: list[str]) -> list[dict]:
    """Skip unhealthy contexts; only verified checkers consume the shared queue."""
    contexts: list[BrowserContext] = []
    healthy: list[tuple[Checker, BrowserContext]] = []
    workers: list[tuple[Checker, Page]] = []
    records: dict[int, dict] = {}
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for item in enumerate(users):
        queue.put_nowait(item)
    async with async_playwright() as pw:
        try:
            for checker in scraper.checkers:
                if scraper.is_stopped:
                    break
                if len(workers) >= scraper.workers:
                    break
                try:
                    checker.profile_dir.mkdir(parents=True, exist_ok=True)
                    context = await pw.chromium.launch_persistent_context(
                        str(checker.profile_dir), channel="chromium", headless=scraper.headless,
                        viewport={"width": 1280, "height": 800},
                    )
                    contexts.append(context)
                    health = await verify_context(
                        context, scraper.mode, scraper.debug_dump,
                        expected_username=checker.username,
                    )
                    scraper.checker_health[checker.checker_id] = health
                    if any(health.values()):
                        logger.warning("Skipping unhealthy %s: %s", checker.checker_id, health)
                        await context.close()
                        contexts.remove(context)
                        continue
                    page = context.pages[0]
                    if scraper.resource_blocker_enabled:
                        scraper.blocker_stats.append(await attach_resource_blocker(page))
                    workers.append((checker, page))
                    healthy.append((checker, context))
                except Exception as exc:
                    reason = f"Checker startup failed ({type(exc).__name__})"
                    scraper.checker_health[checker.checker_id] = {"error": reason}
                    logger.warning("Skipping %s: %s", checker.checker_id, reason)
            await _fill_worker_pages(scraper, healthy, workers)
            scraper.active_checker_ids = list(dict.fromkeys(
                checker.checker_id for checker, _ in workers
            ))
            if not workers and not scraper.is_stopped:
                scraper.stop("No healthy checker sessions. See checker health and use Setup.")
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
                except Exception as exc:
                    logger.warning("Checker browser close failed (%s)", type(exc).__name__)
    return [records[index] for index in sorted(records)]


async def _fill_worker_pages(
    scraper: MultiWorkerScraper,
    healthy: list[tuple[Checker, BrowserContext]],
    workers: list[tuple[Checker, Page]],
) -> None:
    """Distribute spare worker pages over verified contexts without new logins."""
    available = list(healthy)
    index = 0
    while available and len(workers) < scraper.workers and not scraper.is_stopped:
        index %= len(available)
        checker, context = available[index]
        page = None
        try:
            page = await context.new_page()
            if scraper.resource_blocker_enabled:
                stats = await attach_resource_blocker(page)
                scraper.blocker_stats.append(stats)
            workers.append((checker, page))
        except Exception as exc:
            reason = f"Additional worker page failed ({type(exc).__name__})"
            logger.warning("%s: %s", checker.checker_id, reason)
            scraper.checker_health[checker.checker_id]["worker_warning"] = reason
            available.pop(index)
            if page is not None:
                try:
                    await page.close()
                except Exception as close_error:
                    logger.warning("Worker page close failed (%s)", type(close_error).__name__)
        else:
            index += 1


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
        started = time.monotonic()
        try:
            record = await scraper._check_account(page, username)
            if not isinstance(record, dict) or "composite_status" not in record:
                raise ValueError("Target returned no result status")
        except Exception as exc:
            from src.core.scraper import build_record, empty_platform_result

            reason = f"Target processing failed ({type(exc).__name__})"
            logger.error("%s for @%s", reason, username)
            failed = {**empty_platform_result(), "status": "error",
                      "stage": "worker_error", "error": reason}
            skipped = empty_platform_result()
            record = build_record(
                username, failed if scraper.mode != "threads_only" else skipped,
                failed if scraper.mode != "ig_only" else skipped,
                time.monotonic() - started, scraper.mode,
            )
        record["checker_id"] = checker.checker_id
        records[index] = record
        scraper._done += 1
        scraper._emit(record)
        queue.task_done()
        if record["composite_status"] == "BLOCKED":
            scraper.checker_health[checker.checker_id] = {"error": record["error_message"]}
            reason = f"Checker session blocked: {checker.checker_id}: {record['error_message']}"
            if scraper.stop_reason and scraper.stop_reason.startswith("Checker session blocked while checking"):
                scraper.stop_reason = reason
            scraper.stop(reason)
            return
        if not queue.empty():
            await scraper._interruptible_sleep(random.uniform(scraper.min_delay, scraper.max_delay))
