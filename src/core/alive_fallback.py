"""Lazy saved-login verification for inconclusive public Alive results."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING

from playwright.async_api import BrowserContext, BrowserType, Page

from src.core.checker_health import verify_context
from src.core.checkers import Checker, CheckerStore
from src.core.check_plan import USABLE_STATUSES
from src.core.extractors import extract_instagram, extract_threads
from src.core.resource_blocker import attach_resource_blocker

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper

logger = logging.getLogger(__name__)


class AliveFallback:
    """Open saved profiles only after a public result needs confirmation."""

    def __init__(
        self, scraper: MultiWorkerScraper, chromium: BrowserType,
    ) -> None:
        """Keep lazy startup, worker page locks and account pacing state."""
        self.scraper, self.chromium = scraper, chromium
        self.contexts: dict[str, BrowserContext] = {}
        self.pages: dict[tuple[str, int], Page] = {}
        self.page_locks: dict[tuple[str, int], asyncio.Lock] = {}
        self.ready_at: dict[tuple[str, int], float] = {}
        self.checked: dict[tuple[str, str], bool] = {}
        self.startup = asyncio.Lock()
        self.slots: list[Checker] | None = None
        self.attempts = 0
        self.unavailable_reason = "No healthy saved login for verification."

    async def _context(
        self, platform: str,
    ) -> tuple[Checker, BrowserContext] | None:
        """Cache session checks without logging in or reopening failures."""
        if self.slots is None:
            try:
                configured = CheckerStore(self.scraper.profile_dir).load()
                self.slots = [
                    slot for slot in configured
                    if slot.enabled and slot.profile_dir.exists()
                ]
            except (OSError, ValueError) as exc:
                self.slots = []
                self.unavailable_reason = (
                    "Saved checker settings unreadable "
                    f"({type(exc).__name__})."
                )
                logger.warning(self.unavailable_reason)
        for slot in self.slots:
            key = (slot.checker_id, platform)
            if self.scraper.is_stopped:
                return None
            if key in self.checked:
                if self.checked[key]:
                    return slot, self.contexts[slot.checker_id]
                continue
            self.checked[key] = False
            try:
                context = self.contexts.get(slot.checker_id)
                if context is None:
                    context = await self.chromium.launch_persistent_context(
                        str(slot.profile_dir), channel="chromium",
                        headless=self.scraper.headless,
                        viewport={"width": 1280, "height": 800},
                    )
                    self.contexts[slot.checker_id] = context
                health = await verify_context(
                    context, "ig_only" if platform == "ig" else "threads_only",
                    self.scraper.debug_dump, expected_username=slot.username,
                )
                self.scraper.checker_health.setdefault(
                    slot.checker_id, {},
                ).update(health)
                if not any(health.values()):
                    self.checked[key] = True
                    if slot.checker_id not in self.scraper.active_checker_ids:
                        self.scraper.active_checker_ids.append(slot.checker_id)
                    return slot, context
            except Exception as exc:
                reason = f"Saved-login startup failed ({type(exc).__name__})."
                self.scraper.checker_health.setdefault(
                    slot.checker_id, {},
                )[platform] = reason
                logger.warning(reason)
        return None

    async def verify(
        self, worker: int, username: str, platform: str, public: dict,
    ) -> dict:
        """Confirm unknown results using a serialized, paced worker page."""
        if public.get("status") != "unknown" or self.scraper.is_stopped:
            return public
        async with self.startup:
            selected = await self._context(platform)
            if selected is None:
                return {**public, "error": (
                    f"{public.get('error')} {self.unavailable_reason}"
                )}
            checker, context = selected
            key = (checker.checker_id, worker)
            if key not in self.pages:
                try:
                    page = await context.new_page()
                    if self.scraper.resource_blocker_enabled:
                        self.scraper.blocker_stats.append(
                            await attach_resource_blocker(page),
                        )
                    self.pages[key] = page
                    self.page_locks[key] = asyncio.Lock()
                except Exception as exc:
                    reason = (
                        f"Saved-login worker failed ({type(exc).__name__})."
                    )
                    logger.warning(reason)
                    return {**public, "error": reason}
        async with self.page_locks[key]:
            remaining = self.ready_at.get(key, 0) - time.monotonic()
            if remaining > 0:
                await self.scraper._interruptible_sleep(remaining)
            if self.scraper.is_stopped:
                return public
            self.attempts += 1
            extract = (
                extract_instagram if platform == "ig" else extract_threads
            )
            try:
                result = await extract(
                    self.pages[key], username, requested_fields=(),
                    page_ready_timeout_s=self.scraper.page_ready_timeout_s,
                    debug_dump=self.scraper.debug_dump,
                )
            except Exception as exc:
                reason = f"Saved-login read failed ({type(exc).__name__})."
                logger.warning(reason)
                result = {"status": "unknown", "error": reason}
            finally:
                self.ready_at[key] = time.monotonic() + random.uniform(
                    self.scraper.min_delay, self.scraper.max_delay,
                )
            if result.get("status") == "session_blocked":
                self.scraper.stop(
                    f"Saved checker challenged: {checker.checker_id}",
                )
            elif result.get("status") not in USABLE_STATUSES:
                result["status"] = "unknown"
            return {
                **result, "status_source": "saved_login",
                "checker_id": checker.checker_id,
            }

    async def close(self) -> None:
        """Close only contexts opened by this fallback manager."""
        for context in self.contexts.values():
            try:
                await context.close()
            except Exception as exc:
                logger.warning(
                    "Fallback close failed (%s)", type(exc).__name__,
                )
