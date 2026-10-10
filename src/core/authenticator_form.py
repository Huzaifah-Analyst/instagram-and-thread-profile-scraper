"""Recognize authenticator fields and their own submit controls without logging codes."""

import re

from playwright.async_api import Locator, Page


async def authenticator_field(page: Page, allow_label: bool) -> Locator | None:
    """Find legacy named fields or the current labelled Code control.

    Label/numeric fallbacks require an explicit authentication-app instruction;
    they must not interpret an email, SMS or arbitrary numeric field as TOTP.
    """
    candidates = [page.locator(
        'input[name="verificationCode"], input[name="verification_code"], '
        'input[name="security_code"], input[name="approvals_code"], '
        'input[autocomplete~="one-time-code"]'
    )]
    if allow_label:
        candidates += [
            page.get_by_label(re.compile(r"^(code|authentication code|security code)$", re.I)),
            page.get_by_role("textbox", name=re.compile(r"^(code|authentication code|security code)$", re.I)),
            page.locator('input[placeholder="Code"], input[inputmode="numeric"][maxlength="6"]'),
        ]
    for locator in candidates:
        eligible = []
        for index in range(min(await locator.count(), 20)):
            item = locator.nth(index)
            if await item.is_visible() and await item.is_editable():
                eligible.append(item)
        if len(eligible) == 1:
            return eligible[0]
        if len(eligible) > 1:
            return None
    return None


async def authenticator_submit(field: Locator) -> Locator | None:
    """Prefer the code's form/dialog over unrelated login buttons behind it."""
    container = field.locator('xpath=ancestor::*[self::form or @role="dialog"][1]')
    if not await container.count():
        container = field.locator("xpath=ancestor::body")
    for expression in (r"^(continue|confirm|verify|submit)$", r"^log\s*in$"):
        controls = container.get_by_role("button", name=re.compile(expression, re.I))
        visible = []
        for index in range(await controls.count()):
            control = controls.nth(index)
            if await control.is_visible():
                visible.append(control)
        if len(visible) == 1:
            return visible[0]
        if len(visible) > 1:
            return None
    return None
