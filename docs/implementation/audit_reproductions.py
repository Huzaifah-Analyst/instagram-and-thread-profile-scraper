"""Historical defect characterization for commit d94c255, before implementation.

Run from the repository root with:
    python -m docs.implementation.audit_reproductions

Do not use this script as a regression suite for the repaired implementation:
its assertions intentionally expect the old defects. The replacement checks
are tests/test_accuracy_regressions.py, test_health_and_validation.py and
test_checker_pool.py. Retained with its original evidence for audit history.
Browser fixtures below are synthetic, not captures.
"""

from __future__ import annotations

import ast
import asyncio
import json
import subprocess
from pathlib import Path

from playwright.async_api import Route, async_playwright

from src.core import extractors
from src.core.scraper import MultiWorkerScraper, build_record, clean_usernames
from src.gui.components.data_table import record_to_row


def report(case: str, observation: object) -> None:
    """Print one reproducible observation without claiming a product fix."""
    print(json.dumps({"case": case, "observed": observation}, ensure_ascii=True))


def inventory() -> None:
    """Scan every tracked Python file without importing legacy live scripts."""
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"], text=True, encoding="utf-8"
    ).split("\0")
    for name in tracked:
        if not name.endswith(".py"):
            continue
        source = Path(name).read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=name)
        imports = sorted({
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        })
        report("source_inventory", {
            "file": name,
            "lines": len(source.splitlines()),
            "imports": imports,
            "october_literal": "October 2025" in source,
            "silent_handlers": [
                node.lineno for node in ast.walk(tree)
                if isinstance(node, ast.ExceptHandler)
                and all(isinstance(item, (ast.Pass, ast.Continue))
                        for item in node.body)
            ],
        })


def pure_observations() -> None:
    """Check parsing, display and validation against explicit local fixtures."""
    # A transcription of the relevant labels from the corrected user image,
    # anonymized. This is not raw browser text captured by this agent.
    fields = extractors.parse_about_dialog(
        "About this profile\nexample_user\nDate joined\nOctober 2025\n"
        "Account based in\nChina"
    )
    assert fields["date_joined"] == "October 2025"
    assert fields["country"] == "China"
    row = record_to_row(1, build_record(
        "example_user", {"status": "active", **fields}, {"status": None}, 1.0
    ))
    assert row[3:5] == ("China", "October 2025")
    report("screenshot_transcription_and_display_match", row[3:5])

    malformed = extractors.parse_about_dialog(
        "Date joined\nAccount based in\nChina"
    )
    assert malformed["date_joined"] == "Account based in"
    report("missing_value_accepts_next_label_as_date", malformed)

    login = extractors.detect_session_challenge(
        "https://www.instagram.com/example_user/",
        "Log In\nSign Up\nexample_user\n0 followers",
    )
    assert login is None
    report("logged_out_public_page_not_detected", login)

    scraper = MultiWorkerScraper(dialog_timeout_s=-1, menu_click_timeout_s=-1)
    assert scraper.dialog_timeout_s == -1
    report("negative_poll_budgets_accepted", scraper.dialog_timeout_s)

    names = clean_usernames(["https://www.instagram.com/example_user/", "a b"])
    assert len(names) == 2
    report("urls_and_spaces_accepted_as_usernames", names)


async def browser_observations() -> None:
    """Exercise actual Chromium DOM behavior on local synthetic documents."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            await page.set_content(
                '<div role="dialog" style="display:none">'
                'Date joined\nOctober 2025\nAccount based in\nChina</div>'
                '<div role="dialog"><p>target_user</p><p>Date joined</p>'
                '<p>April 2016</p><p>Account based in</p><p>Canada</p></div>'
            )
            hidden = await extractors._poll_dialog(page, ("div[role='dialog']",))
            assert hidden["date_joined"] == "October 2025"
            assert hidden["country"] == "China"
            report("hidden_dialog_selected_before_visible_target", hidden)

            await page.set_content(
                '<div role="dialog"><p>other_user</p><p>Date joined</p>'
                '<p>October 2025</p><p>Account based in</p><p>China</p></div>'
                '<div role="dialog"><p>target_user</p><p>Date joined</p>'
                '<p>April 2016</p></div>'
            )
            wrong = await extractors._poll_dialog(page, ("div[role='dialog']",))
            assert wrong["date_joined"] == "October 2025"
            report("first_dialog_not_bound_to_target_identity", wrong)

            await page.set_content(
                '<div role="dialog" id="about"><p>Date joined</p>'
                '<p>April 2016</p></div>'
            )
            partial = await extractors._poll_dialog(page, ("div[role='dialog']",))
            assert partial["country"] is None
            await page.locator("#about").evaluate(
                "el => el.insertAdjacentHTML('beforeend', "
                "'<p>Account based in</p><p>Canada</p>')"
            )
            complete = extractors.parse_about_dialog(
                await page.locator("#about").inner_text()
            )
            assert complete["country"] == "Canada"
            report("poll_returns_on_first_field_before_later_content", {
                "returned": partial, "later_content": complete,
            })

            await page.set_content('<button>About this profile</button>')
            variant = await extractors._click_menu_item(
                page, extractors.ABOUT_IG_TEXTS, timeout_s=0.1
            )
            assert variant is False
            report("ig_about_profile_menu_variant_not_matched", variant)

            await page.set_content(
                '<button>About this account</button>'
                '<button style="display:none">About this account</button>'
            )
            duplicate = await extractors._click_menu_item(
                page, extractors.ABOUT_IG_TEXTS, timeout_s=0.1
            )
            assert duplicate is False
            report("last_hidden_duplicate_hides_visible_menu_candidate", duplicate)

            await page.set_content(
                '<div role="main">'
                '<div role="button" id="options" style="position:absolute;'
                'top:150px;left:700px"><svg width="20" height="20"></svg></div>'
                '<div role="button" id="unrelated" style="position:absolute;'
                'top:150px;left:900px"><svg width="20" height="20"></svg></div>'
                '</div>'
            )
            menu = await extractors._find_threads_menu_button(page)
            assert menu is not None
            selected = await menu.get_attribute("id")
            assert selected == "unrelated"
            report("threads_rightmost_svg_can_select_unrelated_control", selected)

            async def serve_error(route: Route) -> None:
                """Fulfil all navigations locally, never sending Meta a request."""
                await route.fulfill(
                    status=200, content_type="text/html",
                    body="<body>Something went wrong. Please reload.</body>",
                )

            await page.route("**/*", serve_error)
            result = await extractors.extract_instagram(
                page, "synthetic_error_page", page_ready_timeout_s=0.1
            )
            assert result["status"] == "active"
            assert result["error"] == "IG options (...) button not found"
            report("unclassified_error_page_returns_active", result)
        finally:
            await browser.close()


def main() -> None:
    """Run source inventory and twelve characterization groups, or fail."""
    inventory()
    pure_observations()
    asyncio.run(browser_observations())
    print("All 12 observation groups reproduced; this is NOT a product pass.")


if __name__ == "__main__":
    main()
