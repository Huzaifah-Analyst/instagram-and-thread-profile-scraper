"""Sequential manual windows and post-close platform verification contracts."""

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core import checker_health as health


@pytest.mark.parametrize("threads_error", [None, "Threads login required"])
def test_manual_windows_close_before_next_launch_and_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, threads_error: str | None,
) -> None:
    """Gate each window closure and verify the same profile only after both close."""
    contexts = []
    events: list[str] = []

    async def launch(directory: str, **kwargs: object) -> SimpleNamespace:
        """Record non-overlapping windows and model user closure after navigation."""
        assert directory == str(tmp_path)
        if contexts:
            assert contexts[-1].closed
        index = len(contexts)
        assert kwargs["headless"] is (index == 2)
        if index < 2:
            assert kwargs["no_viewport"] is True
            assert "--start-maximized" in kwargs["args"]
        context = SimpleNamespace(closed=False, callback=None, pages=[])

        async def close() -> None:
            """Signal context closure to the production window waiter."""
            if not context.closed:
                events.append(f"close{index}")
                context.closed = True
                if context.callback:
                    context.callback(context)

        def on(name: str, callback: object) -> None:
            """Register the close callback."""
            context.callback = callback

        async def goto(url: str, **options: object) -> None:
            """Record which platform opens, then simulate the user closing it."""
            events.append(url)
            asyncio.get_running_loop().call_later(.01, lambda: asyncio.create_task(close()))

        context.on = on
        context.close = close
        context.pages = [SimpleNamespace(goto=goto)]
        contexts.append(context)
        return context

    class Manager:
        """Provide an async Playwright boundary without live credentials."""

        async def __aenter__(self) -> SimpleNamespace:
            """Return the observable launcher."""
            return SimpleNamespace(chromium=SimpleNamespace(launch_persistent_context=launch))

        async def __aexit__(self, *args: object) -> None:
            """Production closes every launched context."""
            return None

    verify = AsyncMock(return_value={"ig": None, "threads": threads_error})
    monkeypatch.setattr(health, "async_playwright", Manager)
    monkeypatch.setattr(health, "verify_context", verify)
    summary = asyncio.run(health.login_session(tmp_path, expected_username="alice"))
    assert events == [
        "https://www.instagram.com/accounts/login/", "close0",
        "https://www.threads.com/login", "close1", "close2",
    ]
    verify.assert_awaited_once_with(contexts[2], "combined", expected_username="alice")
    assert "Instagram: Logged in (live verified)" in summary
    assert ("Both logins verified." in summary) is (threads_error is None)
    if threads_error:
        assert threads_error in summary


def test_cancelled_setup_does_not_open_threads_or_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closing the application prevents a second surprise login window."""
    cancel = threading.Event()

    async def window(*args: object) -> bool:
        """Simulate cancellation while the first window is open."""
        cancel.set()
        return False

    manual = AsyncMock(side_effect=window)
    verify = AsyncMock()
    monkeypatch.setattr(health, "_manual_window", manual)
    monkeypatch.setattr(health, "verify_context", verify)
    assert "cancelled" in asyncio.run(health.login_session(tmp_path, cancel=cancel))
    assert manual.await_count == 1
    verify.assert_not_awaited()
