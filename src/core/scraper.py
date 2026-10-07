"""Multi-worker concurrent dispatcher (TSK-105).

One persistent Chromium context (so every worker shares the logged-in checker
session) hosts N pages. The username list is split into N balanced chunks and
each page works through its chunk with human-like delays. Results are pushed
to a progress callback as soon as each account finishes.

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

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

from src.core.ban_engine import (
    COMPOSITE_BLOCKED,
    STATUS_ERROR,
    STATUS_NOT_FOUND,
    STATUS_SESSION_BLOCKED,
    BanLinkEngine,
)
from src.core.extractors import extract_instagram, extract_threads
from src.core.resource_blocker import BlockerStats, attach_resource_blocker

logger = logging.getLogger(__name__)

MODE_IG_ONLY = "ig_only"
MODE_THREADS_ONLY = "threads_only"
MODE_COMBINED = "combined"
MODES = (MODE_IG_ONLY, MODE_THREADS_ONLY, MODE_COMBINED)

DEFAULT_PROFILE_DIR = Path("browser_profile")
DEFAULT_WORKERS = 5
VIEWPORT = {"width": 1280, "height": 800}  # Threads menu detection assumes this width.

ProgressCallback = Callable[[int, int, dict], None]


def clean_usernames(raw: list[str]) -> list[str]:
    """Strips whitespace and leading ``@``, drops blanks and duplicates (order kept).

    Args:
        raw: Usernames as pasted or read from a file.

    Returns:
        Clean, de-duplicated usernames.
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    for name in raw:
        user = name.strip().lstrip("@").strip()
        if user and user.lower() not in seen:
            seen.add(user.lower())
            cleaned.append(user)
    return cleaned


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


def build_record(username: str, ig: dict, threads: dict, seconds: float) -> dict:
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
    }


class MultiWorkerScraper:
    """Checks many accounts in parallel using pages of one persistent context."""

    def __init__(
        self,
        profile_dir: Union[str, Path] = DEFAULT_PROFILE_DIR,
        workers: int = DEFAULT_WORKERS,
        mode: str = MODE_COMBINED,
        headless: bool = True,
        min_delay: float = 4.0,
        max_delay: float = 8.0,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        """Configures the scraper.

        Args:
            profile_dir: Chromium user-data dir holding the checker login session.
            workers: Number of concurrent pages.
            mode: ``ig_only``, ``threads_only`` or ``combined``.
            headless: Run Chromium without a visible window.
            min_delay: Minimum pause between accounts on one worker (seconds).
            max_delay: Maximum pause between accounts on one worker (seconds).
            progress_callback: Called as ``(done, total, record)`` after each account.
                It runs on the scraper's event-loop thread, so GUI code should
                hand the record to a queue rather than touch widgets directly.
        """
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if min_delay > max_delay:
            raise ValueError("min_delay must be <= max_delay")
        self.profile_dir = Path(profile_dir)
        self.workers = workers
        self.mode = mode
        self.headless = headless
        self.min_delay = min_delay
        self.max_delay = max_delay
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

        results: dict[int, dict] = {}
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as pw:
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir), headless=self.headless, viewport=VIEWPORT
            )
            try:
                pages = await self._open_pages(context, len(chunks))
                offset = 0
                jobs = []
                for worker_id, (page, chunk) in enumerate(zip(pages, chunks)):
                    indexed = list(enumerate(chunk, start=offset))
                    offset += len(chunk)
                    jobs.append(self._worker(worker_id, page, indexed, results))
                await asyncio.gather(*jobs)
            finally:
                await context.close()

        return [results[i] for i in sorted(results)]

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
        try:
            if self.mode in (MODE_IG_ONLY, MODE_COMBINED):
                ig = await extract_instagram(page, username)
            # Combined mode: a missing IG account has no Threads profile, and a
            # blocked session must not keep hitting Meta.
            skip_threads = self.mode == MODE_COMBINED and ig["status"] in (STATUS_NOT_FOUND, STATUS_SESSION_BLOCKED)
            if self.mode in (MODE_THREADS_ONLY, MODE_COMBINED) and not skip_threads:
                threads = await extract_threads(page, username)
        except PlaywrightError as exc:
            logger.error("Unexpected browser error for @%s: %s", username, exc)
            failed = {**empty_platform_result(), "status": STATUS_ERROR, "error": f"Browser error: {exc}"}
            if ig["status"] is None and self.mode != MODE_THREADS_ONLY:
                ig = failed
            else:
                threads = failed
        return build_record(username, ig, threads, time.monotonic() - t0)

    def _emit(self, record: dict) -> None:
        """Sends a record to the progress callback without letting it crash a worker."""
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


async def login_session(profile_dir: Path) -> None:
    """Opens a visible browser on the profile dir for one-time manual login."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir), headless=False, viewport=VIEWPORT
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")
        logger.info("Log in to Instagram (and Threads) with the checker account, then close the browser window.")
        closed = asyncio.Event()
        context.on("close", lambda _ctx: closed.set())
        await closed.wait()


def main() -> None:
    """Command-line entry point for manual testing of the engine."""
    parser = argparse.ArgumentParser(description="MetaInspector core engine")
    parser.add_argument("usernames", nargs="*", help="Usernames to check")
    parser.add_argument("--file", type=Path, help="Text file with one username per line")
    parser.add_argument("--mode", choices=MODES, default=MODE_COMBINED)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--headed", action="store_true", help="Show the browser windows")
    parser.add_argument("--login", action="store_true", help="Open a browser for one-time login")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Windows consoles default to cp1252, which cannot print Turkish country names.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.login:
        asyncio.run(login_session(args.profile))
        return

    names = list(args.usernames)
    if args.file:
        names += args.file.read_text(encoding="utf-8").splitlines()
    if not names:
        parser.error("give usernames or --file")

    scraper = MultiWorkerScraper(profile_dir=args.profile, workers=args.workers, mode=args.mode,
                                 headless=not args.headed)
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
