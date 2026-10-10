"""Bounded official-site login UI automation with sanitized outcomes."""

import asyncio
import re
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.async_api import Locator, Page

from src.core.credentials import AccountCredential
from src.core.authenticator_form import authenticator_field, authenticator_submit
from src.core.totp import totp_code

HOSTS = {
    "www.instagram.com", "instagram.com", "www.threads.com", "threads.com",
    "www.threads.net", "threads.net",
}
LOGIN_URLS = {
    "ig": "https://www.instagram.com/accounts/login/",
    "threads": "https://www.threads.com/login",
}


@dataclass(frozen=True)
class LoginOutcome:
    """Public status only: never include page text, passwords or OTPs."""

    platform: str
    ready: bool
    message: str


def official_url(url: str) -> bool:
    """Allow credential entry only on exact official HTTPS origins."""
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname in HOSTS
            and parsed.port in (None, 443) and parsed.username is None)


async def visible(locator: Locator) -> Locator | None:
    """Return the first visible match without waiting for absent controls."""
    for index in range(min(await locator.count(), 20)):
        item = locator.nth(index)
        if await item.is_visible():
            return item
    return None


async def click_named(page: Page, expression: str) -> bool:
    """Click an explicit visible button or link, never a signup fallback."""
    for role in ("button", "link"):
        item = await visible(page.get_by_role(role, name=re.compile(expression, re.I)))
        if item is not None:
            if not official_url(page.url):
                return False
            await item.click(timeout=3000)
            return True
    return False


async def identity_matches(page: Page, platform: str, username: str) -> bool:
    """Require a platform session cookie and its own visible profile link."""
    host = urlsplit(page.url).hostname or ""
    expected = "instagram.com" if platform == "ig" else "threads.com"
    if host not in ({expected, "www." + expected} if platform == "ig" else HOSTS - {
        "instagram.com", "www.instagram.com",
    }):
        return False
    if not any(c["name"] == "sessionid" for c in await page.context.cookies(page.url)):
        return False
    path = f"/{username}/" if platform == "ig" else f"/@{username}"
    for href in (path, path.rstrip("/"), f"https://{host}{path}"):
        links = page.locator(f'a[href="{href}"]')
        for index in range(await links.count()):
            item = links.nth(index)
            if not await item.is_visible():
                continue
            # A feed mention/link to the expected user is not the signed-in identity.
            label = (await item.inner_text()) + " " + (await item.get_attribute("aria-label") or "")
            labels = item.locator('svg title, img[alt], svg[aria-label]')
            for child_index in range(await labels.count()):
                child = labels.nth(child_index)
                label += " " + (await child.text_content() or "")
                label += " " + (await child.get_attribute("alt") or "")
                label += " " + (await child.get_attribute("aria-label") or "")
            if re.search(r"\b(profile|profil)\b", label, re.I):
                return True
    return False


async def login_platform(
    page: Page, platform: str, credential: AccountCredential,
    cancel: threading.Event, timeout_s: float = 75,
) -> LoginOutcome:
    """Submit credentials/TOTP once, stopping on challenges or unknown layouts.

    Exceptions from browser fill operations can contain their secret arguments;
    the boundary intentionally returns fixed messages without exception text.
    """
    try:
        return await _login_platform(page, platform, credential, cancel, timeout_s)
    except Exception:  # Browser errors must never expose fill arguments.
        return LoginOutcome(platform, False, "Browser login failed or was closed; retry from Setup.")


async def _login_platform(
    page: Page, platform: str, credential: AccountCredential,
    cancel: threading.Event, timeout_s: float,
) -> LoginOutcome:
    """Drive one login with a bounded deadline and explicit form recognition."""
    await page.goto(LOGIN_URLS[platform], wait_until="domcontentloaded", timeout=30_000)
    deadline = time.monotonic() + timeout_s
    password_sent = otp_sent = continue_sent = False
    returned_to_threads = False
    dismissed: set[str] = set()
    while time.monotonic() < deadline and not cancel.is_set():
        if not official_url(page.url):
            return LoginOutcome(platform, False, "Unexpected login destination; manual review needed.")
        body = (await page.locator("body").inner_text(timeout=3000)).lower()
        path = urlsplit(page.url).path.lower()
        app_prompt = any(word in body for word in (
            "authentication app", "authenticator app", "authentication code", "authenticator code",
        )) and not any(word in body for word in ("sent a code", "text message", "sent to your email"))
        otp_input = await authenticator_field(page, allow_label=app_prompt)
        authenticator = otp_input is not None and app_prompt
        if (any(part in path for part in ("/checkpoint", "/captcha"))
                or ("/challenge" in path and not authenticator)
                or any(word in body for word in (
                    "confirm you're human", "confirm you’re human", "suspicious login",
                    "try again later", "account has been suspended", "we restrict certain activity",
                ))):
            return LoginOutcome(platform, False, "Meta verification or restriction needs manual attention.")
        if any(word in body for word in (
            "password was incorrect", "incorrect password", "password is incorrect",
            "sorry, your password", "check your security code", "code is incorrect",
            "please check the code", "invalid code",
        )):
            return LoginOutcome(platform, False, "Login or 2FA was rejected; check account details and device time.")
        if await identity_matches(page, platform, credential.username):
            return LoginOutcome(platform, True, "Login verified for the imported account.")
        if (platform == "threads" and not returned_to_threads
                and await identity_matches(page, "ig", credential.username)):
            # An Instagram 2FA handoff may finish at Instagram's own feed.
            # Continue to Threads once; IG cookies alone never prove Threads login.
            returned_to_threads = True
            await page.goto(LOGIN_URLS["threads"], wait_until="domcontentloaded", timeout=30_000)
            continue
        if authenticator and not otp_sent:
            # Avoid submitting a code with only a few seconds of validity left.
            if time.time() % 30 > 25:
                await asyncio.sleep(.5)
                continue
            if not official_url(page.url):
                continue
            submit = await authenticator_submit(otp_input)
            if submit is None:
                return LoginOutcome(platform, False, "2FA submit control not recognized; finish in browser.")
            await otp_input.fill(totp_code(credential.totp_secret), timeout=3000)
            if not official_url(page.url) or cancel.is_set():
                continue
            await submit.click(timeout=3000)
            otp_sent = True
        elif otp_input is not None and not authenticator:
            return LoginOutcome(platform, False, "Email/SMS or unrecognized verification needs manual entry.")
        elif not password_sent:
            password = await visible(page.locator('input[type="password"]'))
            username = await visible(page.locator(
                'input[name="username"], input[name="email"], input[autocomplete~="username"], '
                'input[placeholder="Username, phone or email"]'
            ))
            if username is not None and password is not None:
                if not official_url(page.url):
                    continue
                await username.fill(credential.username, timeout=3000)
                if not official_url(page.url):
                    continue
                await password.fill(credential.password, timeout=3000)
                password_sent = True
                if not await click_named(page, r"^log\s*in$"):
                    return LoginOutcome(platform, False, "Login submit control not recognized; finish in browser.")
            elif platform == "threads" and not continue_sent:
                continue_sent = await click_named(page, (
                    r"^(continue with instagram|log in with instagram|continue as @?"
                    + re.escape(credential.username) + r")$"
                ))
        for label in ("Not now", "Decline optional cookies", "Only allow essential cookies"):
            if label not in dismissed and await click_named(page, "^" + label + "$"):
                dismissed.add(label)
        await asyncio.sleep(.4)
    if cancel.is_set():
        message = "Login cancelled."
    elif otp_sent:
        message = "Authenticator code submitted; account session not verified. Check the browser."
    elif password_sent:
        message = "Password submitted; account session not verified. Check the next browser step."
    elif continue_sent:
        message = "Existing-account continuation opened; session not verified. Finish in browser."
    else:
        message = "Login form or saved identity not recognized; no credentials submitted. Finish in browser."
    return LoginOutcome(platform, False, message)
