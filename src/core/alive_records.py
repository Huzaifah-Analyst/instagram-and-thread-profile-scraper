"""Shared public-first Alive result handling without fabricated metadata."""

from __future__ import annotations

import logging
import time

from playwright.async_api import Page

from src.core.anonymous_status import check_status
from src.core.anonymous_threads import check_threads_status
from src.core.check_plan import USABLE_STATUSES
from src.core.modes import MODE_THREADS_STATUS_ONLY
from src.core.result_records import build_record

logger = logging.getLogger(__name__)


def alive_platforms(mode: str) -> tuple[str, ...]:
    """Select platforms for the two public-first modes."""
    return ("threads",) if mode == MODE_THREADS_STATUS_ONLY else (
        "ig", "threads",
    )


async def read_public(
    page: Page, username: str, platform: str, timeout_s: float,
) -> dict:
    """Read one anonymous platform, preserving every unexpected failure."""
    started = time.monotonic()
    try:
        if platform == "threads":
            result = await check_threads_status(page, username, timeout_s)
        else:
            row = await check_status(page, username, timeout_s)
            result = {
                "status": row["ig_status"], "error": row["error_message"],
                "source_url": row["ig_source_url"], "stage": "status_only",
                "seconds": row["seconds"],
            }
    except Exception as exc:
        logger.error(
            "Public %s read failed (%s)", platform, type(exc).__name__,
        )
        result = {
            "status": "unknown", "stage": "status_only",
            "error": f"{platform} status read failed ({type(exc).__name__}).",
            "seconds": round(time.monotonic() - started, 2),
        }
    return {**result, "status_source": "anonymous"}


def alive_record(
    username: str, results: dict[str, dict], seconds: float, mode: str,
) -> dict:
    """Keep observations independent and grade only requested Alive checks."""
    record = build_record(
        username, results.get("ig", {"status": None}),
        results.get("threads", {"status": None}), seconds, mode,
    )
    record["requested_checks"] = [
        f"{platform}_alive" for platform in alive_platforms(mode)
    ]
    usable = [r.get("status") in USABLE_STATUSES for r in results.values()]
    for platform, result in results.items():
        record[f"{platform}_status"] = result["status"]
        record[f"{platform}_status_source"] = result.get("status_source")
        record[f"{platform}_country_availability"] = "unavailable_in_mode"
    if record["composite_status"] == "ERROR" and not any(usable):
        record["composite_status"] = "UNKNOWN"
    record["checker_id"] = next((
        r["checker_id"] for r in results.values() if r.get("checker_id")
    ), None)
    record["data_quality"] = (
        "Status only" if all(usable) and not record["error_message"]
        else "Partial" if any(usable) else "Unknown"
    )
    return record


async def check_public_target(
    page: Page, username: str, mode: str, timeout_s: float,
) -> dict:
    """Support single-page callers; the pool uses parallel platform pages."""
    started = time.monotonic()
    results = {
        platform: await read_public(page, username, platform, timeout_s)
        for platform in alive_platforms(mode)
    }
    return alive_record(username, results, time.monotonic() - started, mode)
