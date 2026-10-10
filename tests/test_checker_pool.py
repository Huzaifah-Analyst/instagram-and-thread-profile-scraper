"""Pool scheduling, isolation and failure semantics without live accounts."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.checker_pool import run_pool
from src.core.checkers import Checker, CheckerStore, checker_slots
from src.core.scraper import MultiWorkerScraper


class FakePlaywright:
    """Create independent fake contexts while recording launched directories."""

    def __init__(self) -> None:
        """Initialize observable contexts and browser launcher."""
        self.contexts: list[SimpleNamespace] = []
        self.directories: list[str] = []
        self.chromium = self

    async def __aenter__(self) -> "FakePlaywright":
        """Enter the fake Playwright lifetime."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Contexts are closed by the production pool's finally block."""
        return None

    async def launch_persistent_context(self, directory: str, **kwargs: object) -> SimpleNamespace:
        """Give each checker its own page and close callback."""
        self.directories.append(directory)
        context = SimpleNamespace(pages=[object()], close=AsyncMock())
        self.contexts.append(context)
        return context


def configure_pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[MultiWorkerScraper, FakePlaywright]:
    """Replace only browser/health boundaries, retaining the actual scheduler."""
    import src.core.checker_pool as pool

    browser = FakePlaywright()
    monkeypatch.setattr(pool, "async_playwright", lambda: browser)
    monkeypatch.setattr(pool, "verify_context", AsyncMock(return_value={"ig": None, "threads": None}))
    monkeypatch.setattr(pool, "attach_resource_blocker", AsyncMock(return_value=object()))
    scraper = MultiWorkerScraper(
        checkers=checker_slots(tmp_path / "browser_profile"),
        workers=5, min_delay=0, max_delay=0,
    )
    return scraper, browser


def test_five_profiles_process_each_target_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All five contexts participate, without shared pages or duplicate work."""
    scraper, browser = configure_pool(tmp_path, monkeypatch)
    seen: list[str] = []

    async def check(page: object, username: str) -> dict:
        """Yield so all five workers can claim independent queue entries."""
        seen.append(username)
        await asyncio.sleep(.01)
        return {"username": username, "composite_status": "ACTIVE"}

    monkeypatch.setattr(scraper, "_check_account", check)
    names = [f"target_{index}" for index in range(21)]
    records = asyncio.run(scraper.run_async(names))
    assert [row["username"] for row in records] == names
    assert sorted(seen) == sorted(names)
    assert len({row["checker_id"] for row in records}) == 5
    assert len(set(browser.directories)) == 5
    assert len({id(context.pages[0]) for context in browser.contexts}) == 5
    assert all(context.close.await_count == 1 for context in browser.contexts)


def test_preflight_failure_assigns_no_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Threads login wall is reported before any target rows are fabricated."""
    import src.core.checker_pool as pool

    scraper, browser = configure_pool(tmp_path, monkeypatch)
    monkeypatch.setattr(pool, "verify_context", AsyncMock(side_effect=[
        {"ig": None, "threads": None}, {"ig": None, "threads": "Threads login required"},
    ]))
    check = AsyncMock()
    monkeypatch.setattr(scraper, "_check_account", check)
    assert asyncio.run(scraper.run_async(["target"])) == []
    check.assert_not_awaited()
    assert "checker_2" in scraper.stop_reason
    assert "Threads login required" in scraper.stop_reason
    assert all(context.close.await_count == 1 for context in browser.contexts)


def test_challenge_stops_queue_without_reassigning_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """In-flight work may finish, but a challenge starts no replacement work."""
    scraper, browser = configure_pool(tmp_path, monkeypatch)
    seen: list[str] = []

    async def check(page: object, username: str) -> dict:
        """Make the first target fail before peers finish their current target."""
        seen.append(username)
        await asyncio.sleep(.01 if username == "t0" else .04)
        return {"username": username, "composite_status": "BLOCKED" if username == "t0" else "ACTIVE",
                "error_message": "Challenge" if username == "t0" else None}

    monkeypatch.setattr(scraper, "_check_account", check)
    records = asyncio.run(scraper.run_async([f"t{i}" for i in range(30)]))
    assert len(records) == 5
    assert len(seen) == len(set(seen)) == 5
    assert scraper.is_stopped
    assert all(context.close.await_count == 1 for context in browser.contexts)


def test_selection_persists_and_reuses_original_profile(tmp_path: Path) -> None:
    """Migration leaves checker 1's saved login in place and stores only IDs."""
    primary = tmp_path / "browser_profile"
    store = CheckerStore(primary)
    assert [slot.checker_id for slot in store.load() if slot.enabled] == ["checker_1"]
    store.save(["checker_1", "checker_3", "checker_5"])
    slots = store.load()
    assert slots[0].profile_dir == primary
    assert len({slot.profile_dir for slot in slots}) == 5
    assert [slot.checker_id for slot in slots if slot.enabled] == ["checker_1", "checker_3", "checker_5"]
    assert "password" not in store.path.read_text()


@pytest.mark.parametrize("raw", ['[]', '{"enabled":[]}', '{"enabled":[{}]}', '{"enabled":["checker_6"]}'])
def test_corrupt_selection_is_actionable(tmp_path: Path, raw: str) -> None:
    """Malformed user settings produce validation errors rather than crashes."""
    store = CheckerStore(tmp_path / "browser_profile")
    store.path.write_text(raw)
    with pytest.raises(ValueError, match="Invalid checkers"):
        store.load()


def test_duplicate_profile_cannot_be_used_concurrently(tmp_path: Path) -> None:
    """Two IDs must not silently reuse one persistent Chromium directory."""
    with pytest.raises(ValueError, match="separate browser profile"):
        MultiWorkerScraper(checkers=[Checker("one", tmp_path), Checker("two", tmp_path)])
