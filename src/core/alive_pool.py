"""Parallel public Alive reads with selective, paced saved-login fallback."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from playwright.async_api import Page, async_playwright

from src.core.alive_fallback import AliveFallback
from src.core.alive_records import alive_platforms, alive_record, read_public
from src.core.anonymous_status import anonymous_timeout_s
from src.core.resource_blocker import attach_resource_blocker

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper


async def run_alive(
    scraper: MultiWorkerScraper, users: list[str],
) -> list[dict]:
    """Run up to five public targets and five paced verifications at once."""
    platforms = alive_platforms(scraper.mode)
    queue: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    for item in enumerate(users):
        queue.put_nowait(item)
    records: dict[int, dict] = {}
    results: dict[int, dict[str, dict]] = {}
    emitted: set[int] = set()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            channel="chromium", headless=scraper.headless,
        )
        fallback = AliveFallback(scraper, pw.chromium)
        try:
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
            pages: list[dict[str, Page]] = []
            for _ in range(min(scraper.workers, len(users))):
                group = {}
                for platform in platforms:
                    page = await context.new_page()
                    if scraper.resource_blocker_enabled:
                        scraper.blocker_stats.append(
                            await attach_resource_blocker(page),
                        )
                    group[platform] = page
                pages.append(group)

            started_at: dict[int, float] = {}
            prior_seconds: dict[int, float] = {}

            def settle(position: int, retry: bool) -> None:
                """Record elapsed work and publish a final target result."""
                record = alive_record(
                    users[position], results[position],
                    prior_seconds[position] + time.monotonic()
                    - started_at[position], scraper.mode,
                )
                records[position] = record
                if retry or not _retryable(results[position]):
                    _publish(scraper, position, record, emitted)

            async def worker(
                index: int, retry: bool,
                verification: asyncio.Queue[int | None],
            ) -> None:
                """Keep public reads moving during saved-login verification."""
                while not scraper.is_stopped:
                    await scraper._wait_while_paused()
                    if scraper.is_stopped:
                        return
                    try:
                        position, username = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    started_at[position] = time.monotonic()
                    prior_seconds[position] = records.get(
                        position, {},
                    ).get("seconds", 0)
                    values = results.setdefault(position, {})

                    async def platform_read(platform: str) -> None:
                        """Preserve known values and avoid repeating gates."""
                        previous = values.get(platform)
                        if previous and (
                            previous["status"] != "unknown"
                            or previous.get("stage") == "login_required"
                            or previous.get("status_source") == "saved_login"
                        ):
                            return
                        values[platform] = await read_public(
                            pages[index][platform], username, platform,
                            anonymous_timeout_s(scraper.page_ready_timeout_s),
                        )
                    await asyncio.gather(*(
                        platform_read(platform) for platform in platforms
                    ))
                    if any(r["status"] == "unknown" for r in values.values()):
                        verification.put_nowait(position)
                    else:
                        settle(position, retry)
                    queue.task_done()

            async def verifier(
                index: int, retry: bool,
                verification: asyncio.Queue[int | None],
            ) -> None:
                """Pace saved-login work independently of public navigation."""
                while True:
                    position = await verification.get()
                    if position is None:
                        verification.task_done()
                        return
                    await scraper._wait_while_paused()
                    values = results[position]
                    for platform, public in values.items():
                        if public["status"] == "unknown":
                            values[platform] = await fallback.verify(
                                index, users[position], platform, public,
                            )
                    settle(position, retry)
                    verification.task_done()

            async def run_pass(retry: bool) -> None:
                """Drain both bounded worker pools before any warm retry."""
                verification: asyncio.Queue[int | None] = asyncio.Queue()
                verifiers = [asyncio.create_task(
                    verifier(index, retry, verification),
                ) for index in range(len(pages))]
                tasks = [asyncio.create_task(
                    worker(index, retry, verification),
                ) for index in range(len(pages))]
                try:
                    await asyncio.gather(*tasks)
                    for _ in verifiers:
                        verification.put_nowait(None)
                    await asyncio.gather(*verifiers)
                finally:
                    for task in tasks + verifiers:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(
                        *tasks, *verifiers, return_exceptions=True,
                    )

            await run_pass(False)
            pending = [
                i for i, values in results.items() if _retryable(values)
            ]
            if not scraper.is_stopped and pending:
                for index in sorted(pending):
                    queue.put_nowait((index, users[index]))
                await run_pass(True)
            for index, record in sorted(records.items()):
                if index not in emitted:
                    _publish(scraper, index, record, emitted)
            scraper._save_event({
                "event": "alive_public_first", "targets": len(records),
                "public_pages": len(pages) * len(platforms),
                "fallback_attempts": fallback.attempts,
                "warm_retry_targets": len(pending),
                "unknown_platforms": sum(
                    r["status"] == "unknown"
                    for values in results.values() for r in values.values()
                ),
            })
        finally:
            await fallback.close()
            await browser.close()
    return [records[index] for index in sorted(records)]


def _retryable(values: dict[str, dict]) -> bool:
    """Retry transient public Unknowns once, not explicit login gates."""
    return any(
        r.get("status") == "unknown"
        and r.get("stage") != "login_required"
        and r.get("status_source") != "saved_login"
        for r in values.values()
    )


def _publish(
    scraper: MultiWorkerScraper, index: int, record: dict, emitted: set[int],
) -> None:
    """Publish one final row and one progress increment per target."""
    emitted.add(index)
    scraper._done += 1
    scraper._emit(record)
