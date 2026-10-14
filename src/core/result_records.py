"""Flat result records and mode-specific completeness semantics."""

from typing import Optional

from src.core.about_parser import country_is_disclosed
from src.core.ban_engine import BanLinkEngine, STATUS_NOT_FOUND
from src.core.modes import MODE_COMBINED, MODE_IG_STATUS_ONLY


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
    complete = all(
        country_is_disclosed(platform.get("country")) and platform.get("date_joined")
        for platform in checked
    )
    if mode == MODE_COMBINED and len(checked) != 2:
        complete = False
    any_data = any(
        country_is_disclosed(platform.get("country")) or platform.get("date_joined")
        for platform in checked
    )
    quality = "Complete" if complete and checked and not errors else ("Partial" if any_data else "Failed")
    if checked and all(platform["status"] == STATUS_NOT_FOUND for platform in checked):
        quality = "Not available"
    if mode == MODE_IG_STATUS_ONLY:
        status = ig["status"]
        verdict = {"ig_status": status, "threads_status": "skipped",
                   "composite_status": str(status).upper()}
        quality = "Unknown" if status in ("unknown", "error") else "Status only"
    if threads.get("status") == "skipped_ig_sufficient":
        verdict["threads_status"] = "skipped_ig_sufficient"
    return {
        "checking_mode": mode,
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
