# ISSUE: Concurrent Workers May Trigger Meta Detection Faster Than Expected

## Document: `docs/ISSUE_concurrent_session_detection.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)
**Raised by:** Claude Code — Owner's session (Lead Architect/QA role, see `docs/team_roles_and_workflow.md`)
**For:** Partner Developer + Claude
**Date:** 2026-10-07
**Status:** Open — unresolved, not yet isolated. Does not block Sprint 3, but **must be resolved before Sprint 4** (TSK-401 100-account benchmark).
**Full raw evidence:** `docs/memory.md` §5 ("Live Testing Findings", Test A + Incident 5)

---

## 1. Summary

The project owner ran the first two live tests against real Instagram/Threads using an actual (disposable) checker account. A single solo check worked correctly end-to-end. A 97-account batch using the default 5-worker concurrency model failed much faster, and much more broadly, than the architecture assumed.

This is not a crash and not a test failure — `pytest` is still 58/58. It's a live-behavior finding that the current test suite cannot catch, because it only shows up against the real Meta site under concurrent load.

## 2. Evidence

**Test A — solo run, 1 account, 1 worker (effectively):**
`zaifi._.302` → `ACTIVE`, IG country **Pakistan**, IG joined **November 2019**. Confirms the TSK-102 extractor genuinely works against the live site.

**Incident 5 — batch run, 97 accounts queued, default 5 workers, Combined mode:**
- Run auto-stopped after only **10 total accounts** (across all 5 workers combined) with `"Stopped after 10 accounts: Meta challenged the checker account."`
- Only 2 of those 10 were explicitly `BLOCKED` (session-challenge detected by `detect_session_challenge`).
- **The other 8 came back `ACTIVE` but with Country and Joined both `N/A` — including `zaifi._.302`, the exact same account that returned real data in Test A just minutes earlier.**
- Per-account duration was also much higher and more variable under load: 19.8s–57.1s, vs. a clean 21.2s in the solo run.

## 3. Why this matters

- **NFR-1 ("100 accounts in 4–5 minutes") is now unverified and in doubt.** The 5-worker model was designed to parallelize work safely; instead, concurrency appears to correlate with both slower *and* less reliable results.
- **Silent data loss:** an `ACTIVE` row with `N/A`/`N/A` currently looks like "we checked it, nothing to report" — it's visually indistinguishable from a legitimately private-but-active account in the current UI. The extractor does set `error` internally (e.g. `"IG options (...) button not found"`) when this happens, but `src/gui/components/data_table.py::record_to_row` never surfaces `error_message` anywhere in the table. Right now there is no way for an operator to tell "data unavailable" apart from "something went wrong" just by looking at the app.

## 4. Working hypothesis (not confirmed)

Meta's abuse detection may be reacting to **5 simultaneous page loads sharing one logged-in session** (not just total request volume over time) — and appears to start degrading served page content (so the Options/About UI silently isn't there to find) *before* it serves an explicit checkpoint/challenge page. Only 2 of 10 hit the explicit challenge path; the other 8 just quietly lost their data.

This is a hypothesis, not a confirmed root cause — it hasn't been isolated yet.

## 5. Requested investigation (suggested, not prescriptive)

1. **Isolate concurrency vs. account:** re-run with `--workers 1` (CLI) or a GUI override, 5–10 accounts, Instagram-only mode, same checker account. If it behaves cleanly, that points at concurrency as the trigger rather than this particular account being inherently weak/flagged.
2. **Capture what Meta actually served** when extraction silently fails under load — e.g. dump `page.content()` or a screenshot when `options is None` in `extract_instagram`, so we can see whether the page is genuinely different (degraded/stripped) under concurrent load vs. solo.
3. **Consider surfacing `error_message` in the UI** regardless of the concurrency outcome — this is a real gap independent of the root cause: an operator should be able to see *why* a row has no data, not just that it does.
4. If concurrency is confirmed as the trigger, options to discuss (no decision made yet): larger inter-request delays under concurrency, fewer simultaneous pages, or re-evaluating the "1 shared context, 5 pages" design in `docs/architecture.md` §2.2 (itself already a deviation from the original "5 isolated contexts" spec, made for a different reason — see `docs/memory.md` §3.2 deviation #2).

## 6. Not yet done

- Root cause not isolated (concurrency vs. account vs. something else).
- No code changes have been made in response to this — this is a report, not a fix.
- The checker account's session is currently stale/challenged again and needs "Setup Checker Account" re-run before any further live testing.
