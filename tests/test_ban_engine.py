"""Unit tests for the cross-platform ban linking engine (TSK-104)."""

import pytest

from src.core.ban_engine import BanLinkEngine


def test_ig_banned_threads_active_is_banned() -> None:
    """Instagram banned + Threads active -> both BANNED."""
    result = BanLinkEngine.evaluate("banned", "active")
    assert result == {"composite_status": "BANNED", "ig_status": "banned", "threads_status": "banned"}


def test_ig_active_threads_suspended_is_banned() -> None:
    """Instagram active + Threads suspended -> both BANNED."""
    result = BanLinkEngine.evaluate("active", "suspended")
    assert result == {"composite_status": "BANNED", "ig_status": "banned", "threads_status": "banned"}


def test_both_not_found_is_not_found() -> None:
    """Instagram not_found + Threads not_found -> NOT_FOUND."""
    result = BanLinkEngine.evaluate("not_found", "not_found")
    assert result["composite_status"] == "NOT_FOUND"


def test_both_active_is_active() -> None:
    """Both active -> ACTIVE with statuses preserved."""
    result = BanLinkEngine.evaluate("active", "active")
    assert result == {"composite_status": "ACTIVE", "ig_status": "active", "threads_status": "active"}


@pytest.mark.parametrize("state", ["banned", "suspended", "checkpoint", "deactivated", "BANNED", " Suspended "])
def test_every_ban_state_propagates(state: str) -> None:
    """Every ban-type state (any case/whitespace) on either side links the ban."""
    assert BanLinkEngine.evaluate(state, "active")["composite_status"] == "BANNED"
    assert BanLinkEngine.evaluate("active", state)["composite_status"] == "BANNED"


def test_private_ig_counts_as_existing() -> None:
    """A private IG account exists, so the composite is ACTIVE but IG stays private."""
    result = BanLinkEngine.evaluate("private", "active")
    assert result["composite_status"] == "ACTIVE"
    assert result["ig_status"] == "private"


def test_ig_active_without_threads_profile_is_active() -> None:
    """Many IG accounts never created a Threads profile; that is not a ban."""
    assert BanLinkEngine.evaluate("active", "not_found")["composite_status"] == "ACTIVE"


@pytest.mark.parametrize("ig, threads", [("not_found", None), (None, "not_found")])
def test_single_platform_not_found(ig: str, threads: str) -> None:
    """In single-platform modes the unchecked side is skipped."""
    assert BanLinkEngine.evaluate(ig, threads)["composite_status"] == "NOT_FOUND"


def test_ig_only_mode_marks_threads_skipped() -> None:
    """IG-only mode: Threads status None becomes 'skipped'."""
    result = BanLinkEngine.evaluate("active", None)
    assert result == {"composite_status": "ACTIVE", "ig_status": "active", "threads_status": "skipped"}


def test_session_block_is_never_reported_as_ban() -> None:
    """A challenge on the *checker* session says nothing about the target account."""
    result = BanLinkEngine.evaluate("session_blocked", None)
    assert result["composite_status"] == "BLOCKED"


def test_errors_only_give_error() -> None:
    """When nothing could be determined the composite is ERROR."""
    assert BanLinkEngine.evaluate("error", "error")["composite_status"] == "ERROR"
