"""Anonymous Threads identity, login-wall and bounded-read regressions."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page, Route

from src.core.anonymous_threads import (
    check_threads_status, classify_threads_status,
)
from test_accuracy_regressions import run_browser


@pytest.mark.parametrize("text,identity,expected", [
    ("target\n0 followers\nLog in", True, "active"),
    ("target\nThis profile is private", True, "private"),
    ("The link's not working or the page is gone", False, "not_found"),
    ("Log in with your Instagram account", False, "unknown"),
    ("Someone else\n100 followers", False, "unknown"),
    ("", False, "unknown"),
    ("target\nBio: this page isn't available", True, "active"),
])
def test_threads_classifier_requires_profile_evidence(
    text: str, identity: bool, expected: str,
) -> None:
    """Login prompts and unrelated follower counts cannot determine status."""
    assert classify_threads_status(text, identity) == expected


def test_threads_login_redirect_remains_unknown_without_waiting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A login redirect is not evidence that a target does not exist."""
    page = SimpleNamespace(
        goto=AsyncMock(), url="https://www.threads.com/login/?next=target",
    )
    identity = AsyncMock(side_effect=AssertionError("No profile on login"))
    monkeypatch.setattr("src.core.anonymous_threads.profile_matches", identity)
    result = asyncio.run(check_threads_status(page, "target", 30))
    assert result["status"] == "unknown"
    assert result["stage"] == "login_required"
    assert "requires login" in result["error"]
    assert result["seconds"] < 1
    assert result["country"] is result["date_joined"] is None
    identity.assert_not_awaited()


def test_real_threads_public_profile_waits_for_matching_identity() -> None:
    """A blank first render cannot become Unknown before the bounded poll."""
    async def check(page: Page) -> None:
        """Hydrate the public profile after the former fixed-wait threshold."""
        async def serve(route: Route) -> None:
            """Supply local fixture HTML, with no external site traffic."""
            await route.fulfill(content_type="text/html", body='''
                <body><script>setTimeout(() => document.body.innerHTML =
                '<div role="main"><h1>target</h1>0 followers</div>',
                1500)</script></body>''')
        await page.route("**/*", serve)
        result = await check_threads_status(page, "target", 4)
        assert result["status"] == "active"
        assert result["seconds"] >= 1.4
        assert result["error"] is None
    run_browser(check)


def test_real_threads_ambiguous_page_has_bounded_unknown() -> None:
    """A profile shell without target identity is never guessed Alive."""
    async def check(page: Page) -> None:
        """Serve an unrelated visible header and follower count."""
        await page.route("**/*", lambda route: route.fulfill(
            content_type="text/html",
            body='<div role="main"><h1>someone_else</h1>100 followers</div>',
        ))
        result = await check_threads_status(page, "target", .6)
        assert result["status"] == "unknown" and result["error"]
        assert .5 <= result["seconds"] < 2
    run_browser(check)
