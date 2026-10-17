"""Public-first routing, parallel status reads and saved-login fallback."""

import asyncio
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.alive_fallback import AliveFallback
from src.core.checkers import Checker
from src.core.scraper import MultiWorkerScraper
from test_anonymous_pool import AnonymousPlaywright


def fake_browser(monkeypatch: pytest.MonkeyPatch) -> AnonymousPlaywright:
    """Give the pool a fresh context with anonymous pages."""
    browser = AnonymousPlaywright()
    browser.context.new_page = AsyncMock(side_effect=lambda: object())
    monkeypatch.setattr(
        "src.core.alive_pool.async_playwright", lambda: browser,
    )
    return browser


def test_public_alive_runs_platforms_in_parallel_without_checkers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """No configured login or account pacing is touched for decisive pages."""
    browser = fake_browser(monkeypatch)
    monkeypatch.setattr(
        "src.core.alive_fallback.CheckerStore.load",
        lambda *_: pytest.fail("Known public results must not load checkers"),
    )
    started: dict[str, set[str]] = {}
    pages: dict[str, set[int]] = {}

    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Require overlapping IG and Threads reads on distinct pages."""
        started.setdefault(username, set()).add(platform)
        pages.setdefault(username, set()).add(id(page))
        await asyncio.sleep(0)
        assert started[username] == {"ig", "threads"}
        assert len(pages[username]) == 2
        return {
            "status": "active", "error": None, "status_source": "anonymous",
        }

    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    scraper = MultiWorkerScraper(
        checks=("ig_alive", "threads_alive"), profile_dir=tmp_path / "unused",
        workers=2, resource_blocker_enabled=False,
    )
    pacing = AsyncMock(side_effect=AssertionError("Public work cannot pace"))
    monkeypatch.setattr(scraper, "_interruptible_sleep", pacing)
    records = scraper.run(["one", "two", "three"])
    assert len(records) == scraper._done == 3
    assert scraper.unstarted_usernames == []
    assert scraper.checkers == scraper.active_checker_ids == []
    assert all(row["error_message"] is None for row in records)
    assert browser.context.new_page.await_count == 4
    assert all(row["data_quality"] == "Status only" for row in records)
    pacing.assert_not_awaited()
    browser.browser.close.assert_awaited_once()


def test_login_wall_is_verified_only_on_affected_platform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing public Threads verdict never erases a known Instagram one."""
    fake_browser(monkeypatch)
    calls: Counter[str] = Counter()

    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Expose a public IG result and a Threads login gate."""
        calls[platform] += 1
        return {
            "status": "active" if platform == "ig" else "unknown",
            "stage": "status_only" if platform == "ig" else "login_required",
            "error": None if platform == "ig" else "Login required",
            "status_source": "anonymous",
        }

    async def verify(
        manager: AliveFallback, worker: int, username: str,
        platform: str, public: dict,
    ) -> dict:
        """Emulate an actual saved-login confirmation for the unclear side."""
        if public["status"] != "unknown":
            return public
        assert platform == "threads"
        manager.attempts += 1
        return {
            "status": "not_found", "error": None, "checker_id": "checker_1",
            "status_source": "saved_login",
        }

    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    monkeypatch.setattr(AliveFallback, "verify", verify)
    scraper = MultiWorkerScraper(
        checks=("ig_alive", "threads_alive"), resource_blocker_enabled=False,
    )
    rows = scraper.run(["target"])
    assert calls == Counter(ig=1, threads=1)
    assert rows[0]["ig_status"] == "active"
    assert rows[0]["threads_status"] == "not_found"
    assert rows[0]["threads_status_source"] == "saved_login"
    assert rows[0]["error_message"] is None
    assert scraper._done == 1


def test_missing_saved_login_keeps_unknown_and_does_not_repeat_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """A login redirect without usable credentials cannot become Not found."""
    fake_browser(monkeypatch)
    read = AsyncMock(return_value={
        "status": "unknown", "stage": "login_required", "error": "Login gate",
        "status_source": "anonymous",
    })
    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), profile_dir=tmp_path / "unused",
        resource_blocker_enabled=False,
    )
    row = scraper.run(["target"])[0]
    read.assert_awaited_once()
    assert row["threads_status"] == "unknown"
    assert row["ig_status"] == "skipped"
    assert "No healthy saved login" in row["error_message"]
    assert scraper._done == 1


def test_fallback_preserves_account_pacing_and_reads_no_about(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Logged-in fallback keeps per-worker cooldowns despite public speed."""
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), resource_blocker_enabled=False,
    )
    context = SimpleNamespace(new_page=AsyncMock(return_value=object()))
    slot = Checker("checker_1", tmp_path)
    manager = AliveFallback(scraper, object())
    monkeypatch.setattr(
        manager, "_context", AsyncMock(return_value=(slot, context)),
    )
    extract = AsyncMock(return_value={"status": "not_found", "error": None})
    monkeypatch.setattr("src.core.alive_fallback.extract_threads", extract)
    pacing = AsyncMock()
    monkeypatch.setattr(scraper, "_interruptible_sleep", pacing)
    public = {"status": "unknown", "stage": "login_required"}

    async def check() -> None:
        """Make two checks on the same saved-login worker page."""
        first = await manager.verify(0, "first", "threads", public)
        second = await manager.verify(0, "second", "threads", public)
        assert first["status"] == second["status"] == "not_found"
        assert manager.ready_at[("checker_1", 0)] > time.monotonic()
    asyncio.run(check())
    assert extract.await_count == 2
    assert extract.await_args.kwargs["requested_fields"] == ()
    pacing.assert_awaited_once()
    assert 3 < pacing.await_args.args[0] <= 8
    assert context.new_page.await_count == 1


def test_warm_retry_only_rechecks_unknown_and_emits_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Cold public rendering gets one retry after the first pass."""
    fake_browser(monkeypatch)
    calls: Counter[tuple[str, str]] = Counter()
    published: list[dict] = []

    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Recover only the first target's delayed Threads profile."""
        calls[(username, platform)] += 1
        cold = username == "cold" and platform == "threads"
        if cold and calls[(username, platform)] == 2:
            assert calls[("ready", "threads")] == 1
        unknown = cold and calls[(username, platform)] == 1
        return {
            "status": "unknown" if unknown else "active",
            "stage": "status_only", "status_source": "anonymous",
            "error": "Rendering incomplete" if unknown else None,
        }
    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    scraper = MultiWorkerScraper(
        checks=("ig_alive", "threads_alive"), workers=1,
        profile_dir=tmp_path / "unused", resource_blocker_enabled=False,
        progress_callback=lambda done, total, row: published.append(row),
    )
    records = scraper.run(["cold", "ready"])
    assert calls[("cold", "threads")] == 2
    assert calls[("cold", "ig")] == 1
    assert len(published) == scraper._done == 2
    assert len({row["username"] for row in published}) == 2
    assert all(row["error_message"] is None for row in records)


def test_public_first_stop_preserves_attempted_and_unstarted_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user stop never loses an attempted result or invents pending rows."""
    fake_browser(monkeypatch)
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), workers=1, resource_blocker_enabled=False,
    )

    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Stop as the first complete public result arrives."""
        scraper.stop()
        return {"status": "active", "error": None}
    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    rows = scraper.run(["first", "unstarted"])
    assert len(rows) == scraper._done == 1
    assert rows[0]["username"] == "first"
    assert scraper.unstarted_usernames == ["unstarted"]


def test_public_queue_continues_during_saved_login_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A paced verification cannot occupy the sole anonymous worker."""
    fake_browser(monkeypatch)
    later_read = asyncio.Event()

    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Read a later public target while the first fallback is pending."""
        if username == "later":
            later_read.set()
        return {
            "status": "unknown" if username == "gated" else "active",
            "stage": "login_required", "status_source": "anonymous",
            "error": "Login gate" if username == "gated" else None,
        }

    async def verify(
        manager: AliveFallback, worker: int, username: str,
        platform: str, public: dict,
    ) -> dict:
        """Fail if the anonymous worker remains blocked behind verification."""
        await asyncio.wait_for(later_read.wait(), timeout=1)
        return {
            "status": "not_found", "status_source": "saved_login",
            "error": None,
        }

    monkeypatch.setattr("src.core.alive_pool.read_public", read)
    monkeypatch.setattr(AliveFallback, "verify", verify)
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), workers=1, resource_blocker_enabled=False,
    )
    rows = scraper.run(["gated", "later"])
    assert [row["threads_status"] for row in rows] == ["not_found", "active"]
    assert scraper._done == 2
    assert all(row["error_message"] is None for row in rows)


def test_fallback_caches_failed_preflight_and_ignores_disabled_slots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Try enabled existing sessions without repeated startup."""
    slots = [Checker(name, tmp_path / name, enabled) for name, enabled in (
        ("disabled", False), ("bad", True), ("good", True),
    )]
    for slot in slots:
        slot.profile_dir.mkdir()
    contexts = [SimpleNamespace(
        new_page=AsyncMock(return_value=object()), close=AsyncMock(),
    ) for _ in range(2)]
    browser = SimpleNamespace(
        launch_persistent_context=AsyncMock(side_effect=contexts),
    )
    health = AsyncMock(side_effect=[{"threads": "Expired"}, {"threads": None}])
    monkeypatch.setattr(
        "src.core.alive_fallback.CheckerStore.load", lambda _: slots,
    )
    monkeypatch.setattr("src.core.alive_fallback.verify_context", health)
    monkeypatch.setattr("src.core.alive_fallback.extract_threads", AsyncMock(
        return_value={"status": "not_found", "error": None},
    ))
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), resource_blocker_enabled=False,
    )
    monkeypatch.setattr(scraper, "_interruptible_sleep", AsyncMock())
    manager = AliveFallback(scraper, browser)

    async def check() -> None:
        """Reuse the successful preflight and close both owned contexts."""
        for user in ("first", "second"):
            result = await manager.verify(
                0, user, "threads", {"status": "unknown"},
            )
            assert result["checker_id"] == "good"
        await manager.close()
    asyncio.run(check())
    assert health.await_count == 2
    assert browser.launch_persistent_context.await_count == 2
    assert scraper.active_checker_ids == ["good"]
    for context in contexts:
        context.close.assert_awaited_once()


@pytest.mark.parametrize("challenge", [True, False])
def test_fallback_keeps_failures_explicit_and_stops_on_challenge(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, challenge: bool,
) -> None:
    """A saved-login exception stays Unknown; a challenge prevents new work."""
    scraper = MultiWorkerScraper(
        checks=("threads_alive",), resource_blocker_enabled=False,
    )
    context = SimpleNamespace(new_page=AsyncMock(return_value=object()))
    manager = AliveFallback(scraper, object())
    monkeypatch.setattr(manager, "_context", AsyncMock(
        return_value=(Checker("checker_1", tmp_path), context),
    ))
    extract = AsyncMock(return_value={
        "status": "session_blocked", "error": "Verification required",
    }) if challenge else AsyncMock(side_effect=RuntimeError("Fixture failure"))
    monkeypatch.setattr("src.core.alive_fallback.extract_threads", extract)
    result = asyncio.run(manager.verify(
        0, "target", "threads", {"status": "unknown"},
    ))
    assert result["status"] == ("session_blocked" if challenge else "unknown")
    assert result["error"]
    assert scraper.is_stopped is challenge
    if challenge:
        asyncio.run(manager.verify(
            0, "later", "threads", {"status": "unknown"},
        ))
        extract.assert_awaited_once()
