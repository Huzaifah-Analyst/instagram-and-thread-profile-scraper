"""Execute only selected platforms and transparency fields."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from playwright.async_api import Page

from src.core.check_plan import apply_check_selection, metadata_fields
from src.core.extractors import extract_instagram, extract_threads
from src.core.result_records import build_record

if TYPE_CHECKING:
    from src.core.scraper import MultiWorkerScraper

logger = logging.getLogger(__name__)


async def run_selected(
    scraper: MultiWorkerScraper, page: Page, username: str,
) -> dict:
    """Skip excluded platforms and stop at identity for status-only checks."""
    started = time.monotonic()
    results = {name: {"status": None} for name in ("ig", "threads")}
    checks = scraper.checks
    assert checks is not None
    for platform, extract in (
        ("ig", extract_instagram), ("threads", extract_threads),
    ):
        if not any(name.startswith(f"{platform}_") for name in checks):
            continue
        if scraper.is_stopped:
            break
        try:
            result = await extract(
                page, username,
                page_ready_timeout_s=scraper.page_ready_timeout_s,
                dialog_timeout_s=scraper.dialog_timeout_s,
                menu_click_timeout_s=scraper.menu_click_timeout_s,
                debug_dump=scraper.debug_dump,
                requested_fields=metadata_fields(checks, platform),
            )
        except Exception as exc:
            reason = f"{platform} extraction failed ({type(exc).__name__})"
            logger.error("%s for @%s", reason, username)
            result = {
                "status": "error", "stage": "extractor_error", "error": reason,
            }
        results[platform] = result
        if result["status"] == "session_blocked":
            scraper.stop(
                f"Checker session blocked while checking @{username}: "
                f"{result.get('error')}",
            )
    record = build_record(
        username, results["ig"], results["threads"],
        time.monotonic() - started, mode=scraper.mode,
    )
    apply_check_selection(record, checks)
    return record
