# ISSUE: 5-Worker Concurrent Runs Consistently Lose Transparency Data

## Document: `docs/ISSUE_concurrent_session_detection.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)
**Raised by:** Claude Code, Owner's session (Lead Architect/QA role, see `docs/team_roles_and_workflow.md`)
**For:** Partner Developer + Claude
**Date:** 2026-10-07, updated 2026-10-08, updated 2026-10-10
**Status:** Open, not fully isolated. Still must be resolved (and NFR-1 re-benchmarked) before treating Sprint 4 as done.
**2026-10-10 update:** item 3 below (dump the raw dialog text) is now implemented as `--debug-dump`/the GUI's "Save debug captures" checkbox, and the GUI no longer silently ignores widened timeouts the way it did for Test C's runs — see `docs/memory.md` §6 for the full write-up, including a new, more concerning finding (§6.2 point 4: a suspiciously identical "October 2025" join date parsed for dozens of unrelated accounts, not yet explained).
**Full raw evidence:** `docs/memory.md` §5-6 ("Live Testing Findings": Test A, Incident 5, Test B, Test C)

---

## 1. Summary

Three live tests have now been run against real Instagram with an actual disposable checker account. The pattern is consistent and reproducible: a solo single-account check extracts real data correctly every time. Every batch run using the default 5-worker concurrency model has extracted zero transparency data, for every account, across two separate batches (10 and 11 accounts).

This is not a crash and not a test failure. `pytest` is still green (86/86 as of Sprint 3). This is a live-behavior finding the test suite cannot catch on its own, since it only shows up against the real Meta site under concurrent load.

## 2. Evidence

**Test A, 2026-10-07, solo run, 1 account:**
`zaifi._.302` returned `ACTIVE`, IG country Pakistan, IG joined November 2019. Confirms the TSK-102 extractor genuinely works against the live site when run alone.

**Incident 5, 2026-10-07, batch run, 97 accounts queued, default 5 workers, Combined mode:**
- Run auto-stopped after 10 total accounts (across all 5 workers combined) with "Meta challenged the checker account."
- 2 of those 10 were explicitly `BLOCKED` (session-challenge text detected).
- The other 8 came back `ACTIVE` but with Country and Joined both `N/A`, including `zaifi._.302`, the same account that had returned real data in Test A minutes earlier.
- Duration per account: 19.8s to 57.1s, versus 21.2s solo.

**Test B, 2026-10-08, batch run, 11 accounts, re-authenticated session, default 5 workers, Combined mode:**
- Run completed with no stop reason. Session still showed `Connected` afterward, meaning Meta never challenged this run at all.
- All 11 accounts came back `ACTIVE` with Country and Joined both `N/A`. Zero successes, zero exceptions.
- Duration per account: 16.7s to 34.6s.

## 3. Why this matters

- NFR-1 ("100 accounts in 4 to 5 minutes") is unverified and in real doubt. The 5-worker model was meant to parallelize work safely. So far, every concurrent run has returned less usable data than a single solo check, not more throughput.
- Silent data loss: an `ACTIVE` row with `N/A`/`N/A` currently looks identical to "checked, nothing to report." The extractor does set an internal `error` field when this happens (for example "IG options (...) button not found"), but nothing in the live GUI table surfaces it. An operator cannot currently tell "no data because something failed" apart from "no data because there genuinely is none."

## 4. Working hypotheses (neither confirmed)

**Hypothesis 1, Meta-side detection.** Meta's abuse detection reacts to 5 simultaneous requests sharing one logged-in session, not just total volume, and may degrade served content before it ever shows an explicit checkpoint.

**Hypothesis 2, local timeout budget.** Test B weakens hypothesis 1 on its own: there was no challenge or block at all in that run, yet the failure rate was still 100 percent. Five Chromium pages loading Instagram at once on one machine may simply take longer to become interactive than a single page does. The extractor's polling budgets in `src/core/extractors.py`, `PAGE_READY_TIMEOUT_S = 8.0`, `DIALOG_TIMEOUT_S = 8.0`, and the 4.0s deadline inside `_click_menu_item`, were not sized against 5-way concurrent load. If every page is simply slower under load, every worker would time out at the same budget with no Meta involvement required, which is exactly what Test B shows.

These are not mutually exclusive. Meta detection could still explain Incident 5's 2 explicit blocks, while a tight timeout budget explains the other 8, and all 11 of Test B.

## 5. Requested investigation (suggested, not prescriptive)

1. **Cheapest first test: raise the timeout budgets.** Temporarily double `PAGE_READY_TIMEOUT_S`, `DIALOG_TIMEOUT_S`, and the 4.0s menu-click deadline in `src/core/extractors.py`, then re-run a 10 to 11 account batch with 5 workers. If real data comes back this time, the root cause is timing, not detection, and the fix is to raise these constants (or add a worker-count-aware budget) rather than touching the concurrency model at all.
2. **If raising timeouts does not help, isolate concurrency vs. account.** Re-run with `--workers 1` (CLI flag already exists in `src/core/scraper.py`), 5 to 10 accounts, Instagram-only mode, same checker account. A clean result points at concurrency itself as the trigger.
3. **Capture what the page actually looks like when extraction fails under load**, for example dump `page.content()` or a screenshot when `options is None` in `extract_instagram`, so there is direct evidence of whether the page is genuinely different under load versus solo, rather than just inferring it from timing.
4. **Surface `error_message` in the live GUI table and the clipboard copy, not only the CSV/Excel export.** This is a real gap independent of the root cause: an operator should be able to see why a row has no data, not just that it does.

## 6. Not yet done

- Root cause not isolated between hypothesis 1 and hypothesis 2 above.
- No code changes have been made in response to this. This is a report, not a fix.
- The checker account needed re-authentication once already (after Incident 5) and may need it again depending on further testing.
