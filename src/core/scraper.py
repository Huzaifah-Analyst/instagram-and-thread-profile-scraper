"""Multi-worker concurrent dispatcher (TSK-105).

Up to five independent persistent checker contexts consume a shared target
queue. Each checker handles one target at a time and is verified on the
requested platforms before work starts. Completed rows are streamed to the UI.

Usage from the command line::

    python -m src.core.scraper --login                 # one-time manual login
    python -m src.core.scraper user1 user2 --mode combined
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Union

from playwright.async_api import BrowserContext, Page
from playwright.async_api import Error as PlaywrightError

from src.core.ban_engine import (
    COMPOSITE_BLOCKED,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_SESSION_BLOCKED,
    BanLinkEngine,
)
from src.core.extractors import (
    DIALOG_TIMEOUT_S,
    MENU_CLICK_TIMEOUT_S,
    PAGE_READY_TIMEOUT_S,
    extract_instagram,
    extract_threads,
)
from src.core.resource_blocker import BlockerStats, attach_resource_blocker
from src.core.checkers import Checker
from src.core.checker_health import login_session
from src.core.diagnostics import RunJournal
from src.core.paths import DEFAULT_PROFILE_DIR
from src.core.validation import clean_usernames, positive_seconds
from src.core.about_parser import country_is_disclosed

logger = logging.getLogger(__name__)

MODE_IG_ONLY = "ig_only"
MODE_THREADS_ONLY = "threads_only"
MODE_COMBINED = "combined"
MODES = (MODE_IG_ONLY, MODE_THREADS_ONLY, MODE_COMBINED)


DEFAULT_WORKERS = 5
VIEWPORT = {"width": 1280, "height": 800}  # Threads menu detection assumes this width.

ProgressCallback = Callable[[int, int, dict], None]


def chunk_usernames(usernames: list[str], workers: int) -> list[list[str]]:
    """Splits usernames into at most ``workers`` balanced, contiguous chunks.

    Args:
        usernames: Usernames to split.
        workers: Desired number of chunks (must be >= 1).

    Returns:
        Non-empty chunks whose sizes differ by at most one.
    """
    if workers < 1:
        raise ValueError("workers must be >= 1")
    count = min(workers, len(usernames))
    if count == 0:
        return []
    size, extra = divmod(len(usernames), count)
    chunks: list[list[str]] = []
    start = 0
    for i in range(count):
        end = start + size + (1 if i < extra else 0)
        chunks.append(usernames[start:end])
        start = end
    return chunks


def empty_platform_result() -> dict:
    """Result placeholder for a platform that was not checked."""
    return {"status": None, "date_joined": None, "join_badge": None, "country": None, "error": None}


def build_record(
    username: str, ig: dict, threads: dict, seconds: float, mode: Optional[str] = None,
) -> dict:
    """Merges both platform results into one record (matches ``run_items`` schema).

    Args:
        username: Account username.
        ig: Instagram extractor result (or ``empty_platform_result()``).
        threads: Threads extractor result (or ``empty_platform_result()``).
        seconds: Total time spent on this account.

    Returns:
        Flat result record.
    """
    verdict = BanLinkEngine.evaluate(ig["status"], threads["status"])
    errors = [e for e in (ig.get("error"), threads.get("error")) if e]
    checked = [platform for platform in (ig, threads) if platform.get("status") is not None]
    complete = all(country_is_disclosed(platform.get("country")) and platform.get("date_joined") for platform in checked)
    if mode == MODE_COMBINED and len(checked) != 2:
        complete = False
    any_data = any(country_is_disclosed(platform.get("country")) or platform.get("date_joined") for platform in checked)
    quality = "Complete" if complete and checked and not errors else ("Partial" if any_data else "Failed")
    if checked and all(platform["status"] == STATUS_NOT_FOUND for platform in checked):
        quality = "Not available"
    return {
        "username": username,
        "composite_status": verdict["composite_status"],
        "ig_status": verdict["ig_status"],
        "ig_country": ig.get("country"),
        "ig_date_joined": ig.get("date_joined"),
        "threads_status": verdict["threads_status"],
        "threads_country": threads.get("country"),
        "threads_date_joined": threads.get("date_joined"),
        "threads_badge": threads.get("join_badge"),
        "seconds": round(seconds, 2),
        "error_message": "; ".join(errors) or None,
        "data_quality": quality,
        "ig_stage": ig.get("stage"),
        "threads_stage": threads.get("stage"),
        "ig_source_url": ig.get("source_url"),
        "threads_source_url": threads.get("source_url"),
        "ig_evidence": ig.get("evidence"),
        "threads_evidence": threads.get("evidence"),
        "ig_evidence_steps": ig.get("evidence_steps", []),
        "threads_evidence_steps": threads.get("evidence_steps", []),
        "ig_country_availability": ig.get("country_availability"),
        "threads_country_availability": threads.get("country_availability"),
    }


class MultiWorkerScraper:
    """Checks targets in parallel using one page per independent checker login."""

    def __init__(
        self,
        profile_dir: Union[str, Path] = DEFAULT_PROFILE_DIR,
        workers: int = DEFAULT_WORKERS,
        mode: str = MODE_COMBINED,
        headless: bool = True,
        min_delay: float = 4.0,
        max_delay: float = 8.0,
        page_ready_timeout_s: float = PAGE_READY_TIMEOUT_S,
        dialog_timeout_s: float = DIALOG_TIMEOUT_S,
        menu_click_timeout_s: float = MENU_CLICK_TIMEOUT_S,
        debug_dump: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
        checkers: Optional[list[Checker]] = None,
        persist_results: bool = False,
    ) -> None:
        """Configures the scraper.

        Args:
            profile_dir: Chromium user-data dir holding the checker login session.
            workers: Maximum number of active checker profiles (1 to 5).
            mode: ``ig_only``, ``threads_only`` or ``combined``.
            headless: Run Chromium without a visible window.
            min_delay: Minimum pause between accounts on one worker (seconds).
            max_delay: Maximum pause between accounts on one worker (seconds).
            page_ready_timeout_s: How long an extractor waits for a profile page
                to become classifiable. The default was sized against solo-page
                timing; widen it to test whether concurrent-worker load needs a
                larger budget (see `docs/ISSUE_concurrent_session_detection.md`).
            dialog_timeout_s: How long an extractor waits for the transparency
                dialog/panel to render parseable text.
            menu_click_timeout_s: How long an extractor waits for a menu item
                to appear before clicking it.
            debug_dump: If true, every dialog/panel text actually seen is
                written to ``debug/`` (git-ignored) for post-mortem review --
                e.g. to confirm a parsed join date is genuine, not a stale or
                decoy value. See `docs/memory.md`'s 2026-10-10 live test entry.
            progress_callback: Called as ``(done, total, record)`` after each account.
                It runs on the scraper's event-loop thread, so GUI code should
                hand the record to a queue rather than touch widgets directly.
        """
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
            raise ValueError("Delays must be nonnegative and min_delay <= max_delay")
        if not 1 <= workers <= 5:
            raise ValueError("Workers must be between 1 and 5.")
        for budget in (page_ready_timeout_s, dialog_timeout_s, menu_click_timeout_s):
            positive_seconds(budget)
        self.checkers = checkers if checkers is not None else [Checker("checker_1", Path(profile_dir), True)]
        if not self.checkers or len(self.checkers) > 5:
            raise ValueError("Select between 1 and 5 checkers.")
        paths = {str(checker.profile_dir.resolve()).casefold() for checker in self.checkers}
        if len(paths) != len(self.checkers):
            raise ValueError("Each checker must have a separate browser profile.")
        self.checker_health: dict[str, dict] = {}
        self.journal = RunJournal() if persist_results else None
        self.profile_dir = Path(profile_dir)
        self.workers = workers
        self.mode = mode
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.page_ready_timeout_s = page_ready_timeout_s
        self.dialog_timeout_s = dialog_timeout_s
        self.menu_click_timeout_s = menu_click_timeout_s
        self.debug_dump = debug_dump
        self.progress_callback = progress_callback
        self.blocker_stats: list[BlockerStats] = []
        self.stop_reason: Optional[str] = None
        self._stop = threading.Event()
        self._resume = threading.Event()  # cleared while paused
        self._resume.set()
        self._done = 0
        self._total = 0

    @property
    def is_paused(self) -> bool:
        """``True`` while workers are held by ``pause()``."""
        return not self._resume.is_set()

    @property
    def is_stopped(self) -> bool:
        """``True`` once ``stop()`` was called or the session got blocked."""
        return self._stop.is_set()

    def pause(self) -> None:
        """Holds every worker before its next account (thread-safe)."""
        if not self._stop.is_set():
            self._resume.clear()

    def resume(self) -> None:
        """Releases workers held by ``pause()`` (thread-safe)."""
        self._resume.set()

    def stop(self, reason: str = "Stopped by user") -> None:
        """Asks all workers to finish their current account and stop (thread-safe).

        A scraper is single-use: create a new instance for the next run, so a
        ``stop()`` that arrives just before ``run()`` starts is never lost.
        """
        if not self._stop.is_set():
            self.stop_reason = reason
            self._stop.set()
        self._resume.set()  # wake paused workers so they can exit

    def run(self, usernames: list[str]) -> list[dict]:
        """Blocking entry point; see ``run_async``."""
        return asyncio.run(self.run_async(usernames))

    async def run_async(self, usernames: list[str]) -> list[dict]:
        """Checks all usernames across the worker pages.

        Args:
            usernames: Usernames to check.

        Returns:
            Records for every account that was processed, in input order.
            Accounts skipped because of a stop are not included; see ``stop_reason``.
        """
        users = clean_usernames(usernames)
        chunks = chunk_usernames(users, self.workers)
        self._done, self._total = 0, len(users)
        if not chunks:
            return []

        from src.core.checker_pool import run_pool

        if self.is_stopped:
            return []
        if self.journal is not None:
            self.journal.append({
                "event": "started", "mode": self.mode, "target_count": len(users),
                "checkers": [c.checker_id for c in self.checkers[:self.workers]],
                "dialog_timeout_s": self.dialog_timeout_s,
                "menu_timeout_s": self.menu_click_timeout_s,
            })
        records = await run_pool(self, users)
        if self.journal is not None:
            self.journal.append({"event": "finished", "count": len(records),
                                 "stop_reason": self.stop_reason,
                                 "checker_health": self.checker_health})
        return records

    async def _open_pages(self, context: BrowserContext, count: int) -> list[Page]:
        """Creates ``count`` worker pages, each with its own resource blocker."""
        pages = list(context.pages[:count])
        while len(pages) < count:
            pages.append(await context.new_page())
        self.blocker_stats = [await attach_resource_blocker(page) for page in pages]
        return pages

    async def _worker(self, worker_id: int, page: Page, items: list[tuple[int, str]], results: dict[int, dict]) -> None:
        """Processes one chunk sequentially on one page."""
        # Stagger worker start so five pages don't hit Meta at the same instant.
        await self._interruptible_sleep(random.uniform(0, 2.0) * worker_id)
        for position, (index, username) in enumerate(items):
            await self._wait_while_paused()
            if self._stop.is_set():
                return
            record = await self._check_account(page, username)
            results[index] = record
            self._done += 1
            self._emit(record)
            logger.info("[worker %d] %d/%d @%s -> %s", worker_id, self._done, self._total,
                        username, record["composite_status"])

            if record["composite_status"] == COMPOSITE_BLOCKED:
                self.stop(f"Checker session blocked while checking @{username}: {record['error_message']}")
                return
            if position < len(items) - 1:
                await self._interruptible_sleep(random.uniform(self.min_delay, self.max_delay))

    async def _check_account(self, page: Page, username: str) -> dict:
        """Runs the extractors required by the current mode for one account."""
        t0 = time.monotonic()
        ig = empty_platform_result()
        threads = empty_platform_result()
        timeout_kwargs = {
            "page_ready_timeout_s": self.page_ready_timeout_s,
            "dialog_timeout_s": self.dialog_timeout_s,
            "menu_click_timeout_s": self.menu_click_timeout_s,
            "debug_dump": self.debug_dump,
        }
        try:
            if self.mode in (MODE_IG_ONLY, MODE_COMBINED):
                ig = await extract_instagram(page, username, **timeout_kwargs)
            # Check platforms independently; a global stop prevents the next stage.
            skip_threads = self.is_stopped or ig["status"] == STATUS_SESSION_BLOCKED
            if self.mode in (MODE_THREADS_ONLY, MODE_COMBINED) and not skip_threads:
                threads = await extract_threads(page, username, **timeout_kwargs)
        except PlaywrightError as exc:
            logger.error("Unexpected browser error for @%s: %s", username, exc)
            failed = {**empty_platform_result(), "status": STATUS_ERROR, "error": f"Browser error: {exc}"}
            if ig["status"] is None and self.mode != MODE_THREADS_ONLY:
                ig = failed
            else:
                threads = failed
        return build_record(username, ig, threads, time.monotonic() - t0, mode=self.mode)

    def _emit(self, record: dict) -> None:
        """Sends a record to the progress callback without letting it crash a worker."""
        if self.journal is not None:
            self.journal.append(record)
        if self.progress_callback is None:
            return
        try:
            self.progress_callback(self._done, self._total, record)
        except Exception:  # noqa: BLE001 - a broken UI callback must not kill the run
            logger.exception("Progress callback raised")

    async def _wait_while_paused(self) -> None:
        """Blocks this worker while paused; ``stop()`` also releases it."""
        while not self._resume.is_set():
            await asyncio.to_thread(self._resume.wait, 0.5)

    async def _interruptible_sleep(self, seconds: float) -> None:
        """Sleeps up to ``seconds`` but wakes immediately when ``stop()`` is called."""
        if seconds > 0:
            await asyncio.to_thread(self._stop.wait, seconds)



def main() -> None:
    """Command-line entry point for manual testing of the engine."""
    parser = argparse.ArgumentParser(description="MetaInspector core engine")
    parser.add_argument("usernames", nargs="*", help="Usernames to check")
    parser.add_argument("--file", type=Path, help="Text file with one username per line")
    parser.add_argument("--mode", choices=MODES, default=MODE_COMBINED)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--checkers", help="Comma-separated checker numbers, e.g. 1,2,3,4,5")
    parser.add_argument("--login-checker", type=int, choices=range(1, 6), help="Login a named checker slot")
    parser.add_argument("--headed", action="store_true", help="Show the browser windows")
    parser.add_argument("--login", action="store_true", help="Open a browser for one-time login")
    parser.add_argument("--page-ready-timeout", type=float, default=PAGE_READY_TIMEOUT_S,
                        help="Seconds to wait for a profile page to become classifiable "
                             "(widen this under concurrent-worker load; see "
                             "docs/ISSUE_concurrent_session_detection.md)")
    parser.add_argument("--dialog-timeout", type=float, default=DIALOG_TIMEOUT_S,
                        help="Seconds to wait for the transparency dialog/panel to render")
    parser.add_argument("--menu-click-timeout", type=float, default=MENU_CLICK_TIMEOUT_S,
                        help="Seconds to wait for a menu item to appear before clicking it")
    parser.add_argument("--debug-dump", action="store_true",
                        help="Write every dialog/panel text seen to debug/ (git-ignored), to "
                             "check whether a parsed value is genuine vs. stale/decoy data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Windows consoles default to cp1252, which cannot print Turkish country names.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.login or args.login_checker:
        from src.core.checkers import checker_slots

        slot = checker_slots(args.profile)[(args.login_checker or 1) - 1]
        asyncio.run(login_session(slot.profile_dir))
        return

    names = list(args.usernames)
    if args.file:
        names += args.file.read_text(encoding="utf-8").splitlines()
    if not names:
        parser.error("give usernames or --file")

    selected = None
    if args.checkers:
        from src.core.checkers import checker_slots

        numbers = args.checkers.split(",")
        if not numbers or any(n not in {"1", "2", "3", "4", "5"} for n in numbers) or len(set(numbers)) != len(numbers):
            parser.error("--checkers must list distinct slots from 1 to 5")
        slots = checker_slots(args.profile)
        selected = [slots[int(n) - 1] for n in numbers]
    scraper = MultiWorkerScraper(profile_dir=args.profile, workers=args.workers, mode=args.mode,
                                 checkers=selected, persist_results=True,
                                 headless=not args.headed, page_ready_timeout_s=args.page_ready_timeout,
                                 dialog_timeout_s=args.dialog_timeout, menu_click_timeout_s=args.menu_click_timeout,
                                 debug_dump=args.debug_dump)
    t0 = time.monotonic()
    records = scraper.run(names)
    elapsed = time.monotonic() - t0
    for record in records:
        print(json.dumps(record, ensure_ascii=False))
    blocked = sum(s.blocked for s in scraper.blocker_stats)
    print(f"\n{len(records)} accounts in {elapsed:.1f}s | assets blocked: {blocked}")
    if scraper.stop_reason:
        print(f"STOPPED: {scraper.stop_reason}")


if __name__ == "__main__":
    main()
