"""Setup orchestration: isolated sessions, bounded failure and sanitized messages."""

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.auto_login import login_accounts
from src.core.checkers import CheckerStore
from src.core.credentials import AccountCredential
from src.core.login_flow import LoginOutcome


class BrowserFactory:
    """Record isolated profile launches without navigating real websites."""

    def __init__(self) -> None:
        """Expose a minimal Playwright-compatible browser launcher."""
        self.chromium = self
        self.profiles: list[str] = []
        self.contexts: list[SimpleNamespace] = []

    async def __aenter__(self) -> "BrowserFactory":
        """Enter the fake Playwright lifetime."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Leave context cleanup to production orchestration."""
        return None

    async def launch_persistent_context(self, profile: str, **kwargs: object) -> SimpleNamespace:
        """Record a distinct browser session and its close callback."""
        self.profiles.append(profile)
        context = SimpleNamespace(pages=[object()], close=AsyncMock(), on=lambda *_: None)
        self.contexts.append(context)
        return context


@pytest.mark.parametrize("fail_first", [True, False])
def test_five_setups_stop_on_first_failure_or_finish_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_first: bool,
) -> None:
    """A challenged account stops setup; it is not replaced to bypass restriction."""
    browser = BrowserFactory()
    monkeypatch.setattr("src.core.auto_login.async_playwright", lambda: browser)
    login = AsyncMock(side_effect=lambda page, platform, account, cancel: LoginOutcome(
        platform, not fail_first, "Manual verification required." if fail_first else "Verified.",
    ))
    monkeypatch.setattr("src.core.auto_login.login_platform", login)
    accounts = [AccountCredential(f"user{i}", "test-password", "JBSWY3DPEHPK3PXP") for i in range(5)]
    checkers = CheckerStore(tmp_path / "browser_profile").bind_accounts([a.username for a in accounts])
    updates: list[str] = []
    result = asyncio.run(login_accounts(accounts, checkers, threading.Event(), updates.append,
                                        headless=True, keep_manual_open=False))
    assert len(browser.profiles) == (1 if fail_first else 5)
    assert login.await_count == (1 if fail_first else 10)
    assert all(context.close.await_count == 1 for context in browser.contexts)
    assert len(set(browser.profiles)) == len(browser.profiles)
    assert "test-password" not in str(updates) + result
    assert ("0/5 verified" if fail_first else "All 5 accounts verified") in result


def test_bad_binding_never_launches_browser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a mismatched credential/profile pair before navigating anywhere."""
    factory = AsyncMock()
    monkeypatch.setattr("src.core.auto_login.async_playwright", factory)
    account = AccountCredential("alice", "test-password", "JBSWY3DPEHPK3PXP")
    checkers = CheckerStore(tmp_path / "browser_profile").bind_accounts(["bob"])
    result = asyncio.run(login_accounts([account], checkers, threading.Event(), lambda _: None))
    assert "bindings do not match" in result
    factory.assert_not_called()
