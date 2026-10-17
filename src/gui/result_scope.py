"""Visible result columns and labels for independent field selections."""

CHECK_COLUMNS = {
    "ig_alive": "ig_status",
    "threads_alive": "threads_status",
    "ig_country": "ig_country",
    "threads_country": "threads_country",
    "ig_age": "ig_joined",
    "threads_age": "threads_joined",
}
STATUS_LABELS = {
    "active": "ACTIVE",
    "private": "PRIVATE",
    "not_found": "NOT FOUND",
    "suspended": "SUSPENDED",
    "banned": "BANNED",
    "deactivated": "DEACTIVATED",
    "checkpoint": "CHECKPOINT",
    "session_blocked": "CHECKER BLOCKED",
    "error": "CHECK FAILED",
    "unknown": "UNKNOWN",
    "skipped": "Not checked",
    "skipped_ig_sufficient": "Skipped (IG country)",
}


def visible_columns(checks: tuple[str, ...]) -> tuple[str, ...]:
    """Put selected results before diagnostics without adding hidden work."""
    return (
        "idx", "username",
        *(column for check, column in CHECK_COLUMNS.items() if check in checks),
        "quality", "duration", "error",
    )


def platform_status_cell(record: dict, platform: str) -> str:
    """Display the actual platform status without borrowing the other one."""
    checks = record.get("requested_checks")
    if checks is not None and not any(
        check.startswith(f"{platform}_") for check in checks
    ):
        return "Not checked"
    status = str(record.get(f"{platform}_status") or "unknown").lower()
    return STATUS_LABELS.get(status, "UNKNOWN")
