"""Cross-platform ban linking engine (TSK-104).

Merges the per-platform statuses produced by the extractors into a single
composite verdict. If either Instagram or Threads reports a ban-type state,
the account is treated as banned on both platforms.
"""

from __future__ import annotations

from typing import Optional

# Statuses an extractor may emit for a single platform.
STATUS_ACTIVE = "active"
STATUS_PRIVATE = "private"
STATUS_NOT_FOUND = "not_found"
STATUS_BANNED = "banned"
STATUS_SESSION_BLOCKED = "session_blocked"  # the *checker* session hit a login wall / challenge
STATUS_SKIPPED = "skipped"  # platform not checked in this mode
STATUS_ERROR = "error"

# Composite statuses shown in the UI / exports.
COMPOSITE_ACTIVE = "ACTIVE"
COMPOSITE_BANNED = "BANNED"
COMPOSITE_NOT_FOUND = "NOT_FOUND"
COMPOSITE_BLOCKED = "BLOCKED"
COMPOSITE_ERROR = "ERROR"


class BanLinkEngine:
    """Applies the FR-3 cross-platform ban linking rule."""

    BANNED_STATES = frozenset({"banned", "suspended", "checkpoint", "deactivated"})
    EXISTS_STATES = frozenset({STATUS_ACTIVE, STATUS_PRIVATE})

    @staticmethod
    def normalize(status: Optional[str]) -> str:
        """Lower-cases and trims a raw status; ``None``/empty becomes ``skipped``.

        Args:
            status: Raw status string from an extractor, or ``None``.

        Returns:
            The normalized status string.
        """
        if status is None:
            return STATUS_SKIPPED
        cleaned = str(status).strip().lower()
        return cleaned or STATUS_SKIPPED

    @classmethod
    def evaluate(cls, ig_status: Optional[str], threads_status: Optional[str]) -> dict:
        """Combines Instagram and Threads statuses into one verdict.

        Args:
            ig_status: Instagram status (``None`` when IG was not checked).
            threads_status: Threads status (``None`` when Threads was not checked).

        Returns:
            Dict with ``composite_status``, ``ig_status`` and ``threads_status``.
        """
        ig = cls.normalize(ig_status)
        threads = cls.normalize(threads_status)

        # A checker failure takes priority over any target verdict.
        if STATUS_SESSION_BLOCKED in (ig, threads):
            return {"composite_status": COMPOSITE_BLOCKED, "ig_status": ig, "threads_status": threads}

        # FR-3: a ban on either platform propagates to both.
        if ig in cls.BANNED_STATES or threads in cls.BANNED_STATES:
            return {
                "composite_status": COMPOSITE_BANNED,
                "ig_status": STATUS_BANNED,
                "threads_status": STATUS_BANNED,
            }

        checked = [s for s in (ig, threads) if s != STATUS_SKIPPED]

        if checked and all(s == STATUS_NOT_FOUND for s in checked):
            return {"composite_status": COMPOSITE_NOT_FOUND, "ig_status": ig, "threads_status": threads}

        if any(s in cls.EXISTS_STATES for s in checked):
            return {"composite_status": COMPOSITE_ACTIVE, "ig_status": ig, "threads_status": threads}

        return {"composite_status": COMPOSITE_ERROR, "ig_status": ig, "threads_status": threads}
