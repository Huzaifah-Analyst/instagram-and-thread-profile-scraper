"""Real local Chromium login fixtures; all network requests are intercepted."""

import asyncio
import threading
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page, async_playwright

from src.core.credentials import AccountCredential
from src.core.login_flow import identity_matches, login_platform, official_url

ACCOUNT = AccountCredential("alice", "fake-password-only", "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ")


def browser_case(check: Callable[[Page], Awaitable[None]]) -> None:
    """Run entirely synthetic pages in a fresh context without Meta traffic."""
    async def run() -> None:
        """Own browser lifetime even on assertion failure."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            try:
                await check(await browser.new_page())
            finally:
                await browser.close()
    asyncio.run(run())


@pytest.mark.parametrize("url,allowed", [
    ("https://www.instagram.com/accounts/login/", True), ("https://www.threads.com/login", True),
    ("http://www.instagram.com/login", False), ("https://instagram.com.evil.test/", False),
    ("https://instagram.com@evil.test/", False), ("https://instagram.com:8443/", False),
])
def test_official_origins_only(url: str, allowed: bool) -> None:
    """Similar hostnames and insecure origins must never receive secrets."""
    assert official_url(url) is allowed


@pytest.mark.parametrize("username_control", [
    '<input name="username">',
    '<input name="email" autocomplete="username webauthn">',
    '<input name="unfamiliar" autocomplete="username webauthn">',
])
def test_password_then_authenticator_then_correct_identity(
    monkeypatch: pytest.MonkeyPatch, username_control: str,
) -> None:
    """Exercise filled values, one submission per form and cookie+identity success."""
    monkeypatch.setattr("src.core.login_flow.time.time", lambda: 1234567890)
    async def check(page: Page) -> None:
        """Serve a two-stage login page with actual browser form interactions."""
        html = username_control + '''<input type="password"><button onclick="login()">Log in</button>
        <script>window.submits=0;
        function login(){window.saved=[document.querySelector('input').value,
          document.querySelector('input[type=password]').value]; window.submits++;
          document.body.innerHTML='Authentication app<input name="verificationCode"><button onclick="finish()">Confirm</button>';}
        function finish(){window.otp=document.querySelector('input').value; document.cookie='sessionid=fake; path=/';
          document.body.innerHTML='<a href="/alice/">Profile</a>';}</script>'''
        await page.route("**/*", lambda route: route.fulfill(body=html, content_type="text/html; charset=utf-8"))
        result = await login_platform(page, "ig", ACCOUNT, threading.Event(), 4)
        assert result.ready
        assert await page.evaluate("window.saved") == ["alice", ACCOUNT.password]
        assert await page.evaluate("window.submits") == 1
        assert await page.evaluate("window.otp") == "005924"
    browser_case(check)


@pytest.mark.parametrize("html,reason", [
    ('Code sent to your email<input autocomplete="one-time-code">', "manual entry"),
    ('Confirm you are signing in. Text message<input name="verificationCode">', "manual entry"),
    ('Confirm you’re human<input name="username"><input type="password">', "manual attention"),
    ('Sorry, your password was incorrect<input name="username"><input type="password">', "rejected"),
])
def test_manual_steps_never_receive_secrets(html: str, reason: str) -> None:
    """Email/SMS, challenge and rejected login stop without another submission."""
    async def check(page: Page) -> None:
        """Inspect untouched form values after the safe stop."""
        await page.route("**/*", lambda route: route.fulfill(body=html, content_type="text/html; charset=utf-8"))
        result = await login_platform(page, "ig", ACCOUNT, threading.Event(), 2)
        assert not result.ready and reason in result.message
        assert await page.locator("input").evaluate_all("els => els.every(e => e.value === '')")
    browser_case(check)


def test_saved_cookie_alone_or_wrong_identity_never_passes() -> None:
    """A stale cookie or another user's profile is insufficient proof of login."""
    async def check(page: Page) -> None:
        """Require both platform cookie and the imported identity's visible link."""
        await page.route("**/*", lambda route: route.fulfill(body='<a href="/bob/">Profile</a>'))
        await page.goto("https://www.instagram.com/")
        await page.context.add_cookies([{"name": "sessionid", "value": "fake", "url": page.url}])
        assert not await identity_matches(page, "ig", "alice")
        await page.set_content('<a href="/alice/">alice</a> mentioned in a feed post')
        assert not await identity_matches(page, "ig", "alice")
        await page.set_content('<a href="/alice/">Profile</a>')
        assert await identity_matches(page, "ig", "alice")
        assert not await identity_matches(page, "threads", "alice")
        await page.context.clear_cookies()
        assert not await identity_matches(page, "ig", "alice")
    browser_case(check)


def test_browser_error_does_not_disclose_secret_arguments() -> None:
    """Exception messages can contain fill values; do not propagate them."""
    page = SimpleNamespace(goto=AsyncMock(side_effect=RuntimeError(ACCOUNT.password + ACCOUNT.totp_secret)))
    outcome = asyncio.run(login_platform(page, "ig", ACCOUNT, threading.Event()))
    assert not outcome.ready
    assert ACCOUNT.password not in outcome.message and ACCOUNT.totp_secret not in outcome.message


def test_password_is_submitted_only_once_when_page_does_not_advance() -> None:
    """Timeout must not retry a password repeatedly against the same form."""
    async def check(page: Page) -> None:
        """Leave the form unchanged while recording login clicks."""
        html = '''<input name="username"><input type="password">
        <button onclick="window.n=(window.n||0)+1">Log in</button>'''
        await page.route("**/*", lambda route: route.fulfill(body=html, content_type="text/html; charset=utf-8"))
        outcome = await login_platform(page, "ig", ACCOUNT, threading.Event(), 1)
        assert not outcome.ready
        assert await page.evaluate("window.n") == 1
    browser_case(check)


def test_redirect_away_from_official_origin_stops_before_fill(monkeypatch: pytest.MonkeyPatch) -> None:
    """A redirected phishing lookalike never receives imported credentials."""
    monkeypatch.setitem(__import__("src.core.login_flow", fromlist=["LOGIN_URLS"]).LOGIN_URLS,
                        "ig", "https://instagram.com.evil.test/login")
    async def check(page: Page) -> None:
        """Serve a convincing form on a disallowed origin, all locally."""
        await page.route("**/*", lambda route: route.fulfill(
            body='<input name="username"><input type="password"><button>Log in</button>',
            content_type="text/html",
        ))
        result = await login_platform(page, "ig", ACCOUNT, threading.Event(), 1)
        assert not result.ready and "Unexpected" in result.message
        assert await page.locator("input").evaluate_all("els => els.every(e => e.value === '')")
    browser_case(check)


def test_threads_continue_existing_account_without_signup() -> None:
    """Only existing-account continuation is used; signup controls stay untouched."""
    async def check(page: Page) -> None:
        """Emulate a saved Instagram login offered by Threads."""
        html = '''<button onclick="window.signup=true">Join Threads</button>
          <button onclick="document.cookie='sessionid=fake; path=/';
          document.body.innerHTML='<a href=&quot;/@alice&quot;>Profile</a>'">Continue as alice</button>'''
        await page.route("**/*", lambda route: route.fulfill(body=html, content_type="text/html"))
        result = await login_platform(page, "threads", ACCOUNT, threading.Event(), 2)
        assert result.ready
        assert await page.evaluate("window.signup === undefined")
    browser_case(check)
