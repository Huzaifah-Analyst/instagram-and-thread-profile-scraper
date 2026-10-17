"""Validated field selections and result grading for requested checks."""

from src.core.about_parser import country_is_disclosed
from src.core.modes import (
    MODE_COMBINED, MODE_IG_ONLY, MODE_IG_STATUS_ONLY, MODE_THREADS_ONLY,
)

CHECK_LABELS = (
    ("ig_alive", "IG Alive"),
    ("threads_alive", "Threads Alive"),
    ("ig_country", "IG Country"),
    ("threads_country", "Threads Country"),
    ("ig_age", "IG Age (joined date)"),
    ("threads_age", "Threads Age (joined date)"),
)
CHECK_NAMES = tuple(name for name, _ in CHECK_LABELS)
USABLE_STATUSES = {"active", "private", "not_found", "banned", "suspended"}
ALIVE_STATUSES = {"active", "private"}


def normalize_checks(checks: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Require a known nonempty selection and return its canonical order."""
    if not checks or any(name not in CHECK_NAMES for name in checks):
        raise ValueError("Select at least one supported check.")
    return tuple(name for name in CHECK_NAMES if name in checks)


def mode_for_checks(checks: tuple[str, ...]) -> str:
    """Choose the existing session strategy required by the selected fields."""
    chosen = normalize_checks(checks)
    if chosen == ("ig_alive",):
        return MODE_IG_STATUS_ONLY
    ig = any(name.startswith("ig_") for name in chosen)
    threads = any(name.startswith("threads_") for name in chosen)
    return MODE_COMBINED if ig and threads else (
        MODE_IG_ONLY if ig else MODE_THREADS_ONLY
    )


def checks_for_mode(mode: str) -> tuple[str, ...]:
    """Populate checkboxes from a legacy preset, preserving its scope."""
    if mode == MODE_IG_STATUS_ONLY:
        return ("ig_alive",)
    if mode in (MODE_IG_ONLY, MODE_THREADS_ONLY):
        prefix = "ig_" if mode == MODE_IG_ONLY else "threads_"
        return tuple(name for name in CHECK_NAMES if name.startswith(prefix))
    return CHECK_NAMES


def metadata_fields(checks: tuple[str, ...], platform: str) -> tuple[str, ...]:
    """List only the transparency fields needed for this platform."""
    fields = []
    if f"{platform}_country" in checks:
        fields.append("country")
    if f"{platform}_age" in checks:
        fields.append("date_joined")
    return tuple(fields)


def apply_check_selection(record: dict, checks: tuple[str, ...]) -> None:
    """Retain status evidence but mask unrequested metadata and grade scope."""
    record["requested_checks"] = list(checks)
    satisfied = []
    requested_statuses = []
    withheld = False
    for platform in ("ig", "threads"):
        status = record.get(f"{platform}_status")
        if any(name.startswith(f"{platform}_") for name in checks):
            requested_statuses.append(status)
        else:
            record[f"{platform}_status"] = "skipped"
            record[f"{platform}_stage"] = "skipped"
        if f"{platform}_alive" in checks:
            satisfied.append(status in USABLE_STATUSES)
        for suffix, field in (("country", "country"), ("age", "date_joined")):
            key = f"{platform}_{field}"
            if f"{platform}_{suffix}" in checks:
                value = record.get(key)
                satisfied.append(
                    country_is_disclosed(value) if suffix == "country"
                    else bool(value)
                )
            else:
                record[key] = None
                if suffix == "country":
                    key = f"{platform}_country_availability"
                    record[key] = "not_requested"
        withheld |= record.get(f"{platform}_country_availability") in {
            "not_disclosed", "not_shared",
        }
    if "threads_age" not in checks:
        record["threads_badge"] = None
    if record.get("checking_mode") == MODE_IG_STATUS_ONLY:
        return
    if all(satisfied) and not record.get("error_message"):
        record["data_quality"] = "Complete"
    elif requested_statuses and all(
        status == "not_found" for status in requested_statuses
    ):
        record["data_quality"] = "Not available"
    else:
        record["data_quality"] = (
            "Partial" if any(satisfied) or withheld else "Failed"
        )
