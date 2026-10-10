# Project Memory, Client Interaction Log & Technical Archive

## Document: `docs/memory.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)  
**Maintained By:** Developer 1 & Developer 2  
**Purpose:** Serves as the persistent project mind. Records client communications, architectural decisions, technical discoveries, problem-solving history, and pull request activity.

---

## 1. Client Profile & Interaction Archive

### 1.1 Project Agreement & Commercial Terms
- **Agreed Delivery Timeline:** 15 Calendar Days.
- **Support & Warranty Agreement:** 15 to 20 Days of complimentary bug-fixing warranty post-handover.
  - *Scope of Free Warranty:* Technical defects, bugs in desktop UI, or exporter errors.
  - *Out of Scope:* Major future structural overhauls or DOM re-architectures initiated by Meta/Instagram months after handover (classified as billable maintenance).
- **Target Machine Usage:** Client permitted to run the compiled standalone `.exe` across multiple office laptops without licensing friction.

### 1.2 Authentication Agreement
- **Zero Personal Account Risk:** Clarified to client that personal or client main accounts must never be used.
- **One-Time Dummy Session:** Client supplies a disposable checker/burner Instagram account. Login is performed once inside the tool's embedded browser window; cookies are saved locally; no password is ever stored in code.

---

## 2. Technical Discoveries & Past Incident Resolutions

### Incident 1: Direct API Call Rate Limiting (The Test D Discovery)
- **Problem:** Attempted to fetch user transparency data via direct HTTP requests to `https://www.instagram.com/api/v1/users/web_profile_info/` with short delays (1.5s–2.5s).
- **Outcome:** Instagram immediately returned **`HTTP 429 (Too Many Requests)`** across all subsequent requests.
- **Solution & Architectural Pivot:** Direct unauthorized API scraping on a single session is unsafe. Solved by implementing **Playwright 5-Worker Parallel Concurrency**. By distributing 100 accounts across 5 parallel browser contexts, each worker operates at a conservative, human-like 12s cadence, achieving 100 accounts in 4 minutes with zero rate-limit blocks.

### Incident 2: Threads Options Menu Selector Fragility
- **Problem:** On Threads profiles, the 3-dots options menu button has no unique CSS class name, ID, or accessible aria-label on desktop web.
- **Solution:** Engineered a coordinate-aware DOM locator targeting header action SVGs within specific bounding boxes:
  ```python
  action_svgs = [
      s for s in card.locator("svg").all()
      if s.bounding_box() and 100 < s.bounding_box()["y"] < 350 and s.bounding_box()["x"] > 600
  ]
  dots_svg = action_svgs[-1] # Rightmost element is reliably the 3-dots button
  ```

### Incident 3: Multi-Lingual Transparency Modal Labels
- **Problem:** Accounts in different locales return transparency modals in different languages (e.g., English "Date joined" / "Account based in" vs. Turkish "Katılma tarihi" / "Hesabın bulunduğu konum").
- **Solution:** Implemented a multi-language dictionary matcher:
  ```python
  DATE_KEYS = ["date joined", "katılma tarihi", "date of creation"]
  COUNTRY_KEYS = ["account based in", "hesabın bulunduğu konum", "account location", "based in"]
  ```

### Incident 4: Browser Session Persistence
- **Problem:** User having to re-authenticate on every script execution.
- **Solution:** Configured Playwright with `launch_persistent_context()` pointing to a designated local directory (`browser_profile/`). Cookies and storage state remain permanently stored on disk.

---

## 3. Collaborative Git & Merge Activity Log

Both developers must record every merged Pull Request in the table below to maintain a permanent audit trail:

| Date | PR # | Author | Branch Name | Merged By | Description & Key Files Modified |
| :--- | :---: | :--- | :--- | :--- | :--- |
| *2026-10-04* | - | Dev 1 & 2 | `main` | Team | Initial project documentation setup (`docs/` folder created with 6 standard specs). |
| *2026-10-06* | #1 | Andleeb Hassan | `feature/sprint1-core-engine` | Lead Architect | Merged Sprint 1 core engine: resource blocker, ban engine, extractors, 5-worker scraper, 43 unit tests passing. |
| *2026-10-07* | #2 | Andleeb Hassan (co-authored by Claude Opus 5.5) | `feature/sprint2-desktop-gui` | Claude Code (Owner's session) | CustomTkinter interface (`src/gui/`), thread-safe bridge, checker-session detection (`src/core/session.py`), `pause()`/`resume()` on `MultiWorkerScraper`. 15 new tests (58 total). Squash-merged into `dev` after independent review (58/58 re-run) and Huzaifah's go-ahead. Feature branch pending delete (blocked by local permission classifier on `git push --delete`; safe to delete manually on GitHub). |
| *Pending review 2026-10-08* | #3 | Andleeb Hassan (co-authored by Claude Opus 5.5) | `feature/sprint3-sheets-export` | — | TSV clipboard formatter (`src/core/clipboard.py`), toast banner, SQLite run history (`src/core/history_db.py`), History Viewer dialog, CSV/Excel export with formula-injection guard (`src/core/records.py`, `src/core/export.py`). 28 new tests (86 total, all passing on re-run). **Awaiting Huzaifah's merge decision.** |

### 3.1 Role Handover — Antigravity AI → Claude Code (2026-10-07)

Antigravity AI is no longer part of this project. Huzaifah now runs **Claude Code directly** to perform the Lead Architect, QA & Code Reviewer responsibilities previously described for Antigravity AI in `docs/team_roles_and_workflow.md` (system architecture, code review, test verification, PR merges, documentation upkeep, sprint directive generation). No change to the Partner Developer + Claude implementation role, or to Huzaifah's role.

### 3.2 Sprint 2 Independent Review (Claude Code, 2026-10-07)

Performed in response to Huzaifah's request to take over QA after reading the "Sprint 1 & 2 Progress Report" PDF (`docs/MetaInspector Desktop — Sprint 1 & 2 Progress Report.pdf`).

- **Pulled** `feature/sprint2-desktop-gui` (was not yet fetched locally — `git fetch` found it on `origin`).
- **Installed** missing dependency (`customtkinter`, not previously installed in this environment) and **re-ran the full suite**: `pytest` → **58/58 passed** in 2.3s, matching the report's claim.
- **Smoke-tested** the GUI directly (`python main.py`) — launches cleanly, no startup errors.
- **Code-reviewed** every changed file (`app.py`, `bridge.py`, `theme.py`, `left_panel.py`, `data_table.py`, `status_bar.py`, `session.py`, `scraper.py` diff) against `docs/rules.md` and `docs/design.md`: type hints, docstrings, and the Cyber Dark colour tokens all match; no PEP 8 or security issues found (`session.py` correctly reads only cookie name/expiry, never the encrypted value).
- **Verified the 5 documented spec deviations** in the progress report against the actual code — all 5 check out exactly as described (session-block → `BLOCKED` carve-out in `ban_engine.py`'s `BanLinkEngine.evaluate`; 1 persistent context + 5 pages in `scraper.py`; whole-row tinting in `data_table.py`; background-thread login call in `app.py`; Connected/Disconnected-only in `session.py`).
- **Verdict:** Sprint 2 implementation is sound and ready to merge. Recommended merge is pending Huzaifah's explicit go-ahead (not performed automatically, since merging to `dev` and pushing affects the shared repo).
- **Docs found stale during this review and corrected:** `docs/architecture.md` §2 (described 5 isolated browser contexts; actual implementation uses 1 persistent context with 5 pages, a documented, deliberate deviation) and §4 (`BanLinkEngine` pseudocode was missing the session-blocked carve-out that the real `src/core/ban_engine.py` implements); `docs/tasks.md` Sprint 2 rows (still showed `[ ]`); `docs/rules.md` and `docs/PRD.md` "Team" lines (still said "2 Developers", not reflecting the actual AI-paired team structure).

### 3.3 Sprint 3 Independent Review (Claude Code, 2026-10-08)

Performed after Huzaifah saved the "Progress Report (Sprints 1 to 3)" PDF in `docs/`.

- **Pulled** `feature/sprint3-sheets-export` and **re-ran the full suite**: `pytest` gives **86/86 passed** in about 10s, matching the report's claim.
- **Code-reviewed** every new/changed file: `src/core/records.py`, `clipboard.py`, `export.py`, `history_db.py`, `src/gui/actions.py`, `components/toast.py`, `components/history_dialog.py`, and the diffs to `app.py`, `status_bar.py`, `data_table.py`, `theme.py`. No defects found; good practices noted: `export.py` uses UTF-8 with BOM for CSV (so Excel reads Turkish characters correctly) and stores every Excel cell as an explicit text type (so a value like `=HYPERLINK(...)` is shown as text, not run as a formula); `records.py` adds a shared `safe_cell()` formula-injection guard used everywhere; `history_db.py` matches the `architecture.md` §5 schema exactly and handles same-second run id collisions; a finished OR stopped run is both saved to history.
- **Good follow-through on the Sprint 2 review:** this submission independently fixed two things flagged in §3.2/the open issue report without being asked to: `theme.py`'s `MODE_LABELS` now covers all 3 modes (previously only 2 of 3 were mapped, see Sprint 2 review), and `display_status`/`cell` logic was de-duplicated into `src/core/records.py` and reused by `theme.py` instead of living in two places.
- **One gap still open:** the live results table (`data_table.py`, shown during an active run) still has no way to show *why* a row has `N/A` data, since `error_message` is not one of its columns. The new `EXPORT_COLUMNS` in `records.py` does add an `Error` column, but only for CSV/Excel export, not for the live table or the clipboard copy. Not a blocker; worth a small follow-up.
- **Not independently verified:** the two items the report itself flags as unverified (pasting into real Google Sheets with Ctrl+V, opening the exported files in real Excel). The unit tests check the TSV/CSV/XLSX content is correct, but nobody has pasted into an actual Google Sheet or opened a file in actual Excel yet.
- **Verdict:** Sprint 3 implementation is sound and ready to merge, same as Sprint 2. Merge pending Huzaifah's go-ahead.

---

## 4. Known Quirks & Operational Gotchas

1. **Threads Inactive Profiles:** Inactive Threads profiles with zero posts often do not display the "About this profile" button. The parser must detect this and gracefully set `threads_country = N/A` without timing out.
2. **Threads Badge Parsing:** The Threads join string typically contains both date and badge separated by a dot (e.g. `September 2026 · 100M+`). The parser splits this on `·` into `threads_date_joined` and `threads_join_badge`.
3. **Modal Dismissal:** Always send `Escape` keypress twice after modal reading to ensure the backdrop overlay is dismissed before navigating to the next profile.

---

## 5. Live Testing Findings (2026-10-07, Huzaifah + Claude Code)

First live tests against real Instagram/Threads with an actual checker account, run from the GUI (`feature/sprint2-desktop-gui`, Combined mode).

### Test A — 1 account, solo run
`zaifi._.302` → ACTIVE, IG country **Pakistan**, IG joined **November 2019**, Threads N/A. Confirms TSK-102 (Instagram transparency extraction) genuinely works end-to-end against the live site. 21.2s "check" time for this one account; total elapsed 30s (~9s of that is one-time Chromium/persistent-context startup, not per-account cost — don't divide 30s by 1 account).

### Incident 5: Concurrent workers degrade/block extraction far faster than expected
- **Setup:** Same checker account, 97 usernames queued, Combined mode, default 5 workers (one persistent context, 5 pages — per architecture.md §2.2).
- **Result:** Run auto-stopped after only **10 total accounts** (not per-worker — 10 across all 5 workers combined) with "Meta challenged the checker account." 2 of the 10 were explicitly `BLOCKED` (session challenge detected). The other 8 showed composite `ACTIVE`, but **all 10 rows — including the 8 non-blocked ones — came back with Country and Joined as `N/A`**, even `zaifi._.302` (row 5), which had returned real data (Pakistan / November 2019) in Test A just minutes earlier on the same account.
- **Interpretation:** Meta's abuse detection appears to react to **5 simultaneous requests sharing one login session**, not just total request volume. It looks like it starts degrading served page content (stripping/hiding the Options/About UI, so extraction silently fails with status still `ACTIVE`) *before* it serves an explicit checkpoint — only 2 of 10 hit the explicit challenge path. Per-account durations were also much higher and more variable under load (19.8s–57.1s) than the clean solo run (21.2s), the opposite of the speedup 5-worker concurrency was meant to buy.
- **Risk to NFR-1 (100 accounts in 4–5 min):** Unverified and now in doubt as currently configured — a single-session, 5-parallel-page model may simply not be viable against live Meta without triggering detection well before 100 accounts. TSK-401 (speed benchmark) should not be scheduled until this is isolated.
- **Open question, not yet isolated:** Is this concurrency-triggered (5 simultaneous pages on one session) or account-triggered (this particular disposable account is new/weak and gets flagged quickly regardless)? Needs a controlled test: same account, 1 worker, 5 to 10 accounts, Instagram-only mode, to see if sequential single-page requests avoid the silent-degradation pattern.
- **Action needed:** Re-run "Setup Checker Account" (session was challenged and is now stale) before any further testing.

### Test B (2026-10-08) — second 5-worker batch, re-authenticated session, Sprint 3 branch
- **Setup:** Same disposable checker account, re-authenticated after Incident 5. 11 usernames, Combined mode, default 5 workers.
- **Result:** Run completed cleanly, no stop reason, session still shows `Connected` afterward. All 11 accounts composite `ACTIVE`. **All 11 rows came back with Country and Joined as `N/A`, zero exceptions.** Not one explicit `BLOCKED` this time (compare Incident 5: 2 of 10 were `BLOCKED`). Durations: 16.7s to 34.6s.
- **Why this matters:** this is a cleaner data point than Incident 5. With zero challenge/block events at all, "Meta is actively detecting and degrading the session" is a weaker explanation than it looked after Incident 5 alone, because there was nothing here for Meta to detect and react to, yet the result was identical: 100% of concurrent-run accounts lost their data, 100% of the one solo account (Test A) kept it.
- **Revised working hypothesis:** this may be a **local resource/timeout problem, not only a Meta anti-bot problem**. Five Chromium pages loading Instagram at once on one machine may simply make each page slower to become interactive than when it is the only page running. `extract_instagram`'s polling budgets (`PAGE_READY_TIMEOUT_S = 8.0`, `DIALOG_TIMEOUT_S = 8.0`, the 4.0s menu-click deadline in `_click_menu_item`) were presumably sized against solo-page timing, not 5-way concurrent timing. If pages are simply rendering slower under load, every worker would time out at the same budget, with no Meta challenge required, exactly what was observed.
- **This does not rule out Meta detection too.** Both can be true at once (slower under load, AND more likely to get challenged under load). Incident 5's 2 explicit blocks still need explaining; Test B just shows the silent-failure part does not require a block to happen.
- **Suggested additional diagnostic (cheap, no extra live requests needed to design it):** temporarily double `PAGE_READY_TIMEOUT_S`, `DIALOG_TIMEOUT_S` and the 4.0s menu-click deadline in `src/core/extractors.py`, and re-run the same 10 to 11 account batch. If results come back with real data this time, the root cause is timeout budgets being too tight under concurrent load, a straightforward fix (raise the constants, or stagger workers more). If it still comes back all `N/A`, that points back toward Meta-side detection and the original 1-worker-vs-5-worker isolation test is still needed.

### Fix Attempt 1 (2026-10-10, `fix/concurrent-timeouts`): made the timeout budgets and GUI worker count configurable; not yet live-verified

**No live checker account or Instagram session was available in this environment**, so none of this was tested against the real site. Nothing below should be read as "the concurrent-run bug is fixed" — only as the groundwork so Huzaifah can run the two diagnostics `ISSUE_concurrent_session_detection.md` §5 already suggested, without a code change in between.

- **`src/core/extractors.py`:** `PAGE_READY_TIMEOUT_S`, `DIALOG_TIMEOUT_S` and the 4.0s menu-click deadline (now a named constant, `MENU_CLICK_TIMEOUT_S`) are unchanged as defaults, but `extract_instagram`, `extract_threads`, and their internal `_open_profile` / `_poll_dialog` / `_click_menu_item` helpers now accept them as parameters. `MultiWorkerScraper.__init__` takes the same three as `page_ready_timeout_s` / `dialog_timeout_s` / `menu_click_timeout_s` keyword args (same pattern as the existing `min_delay`/`max_delay`), and `scraper.py`'s CLI gained matching `--page-ready-timeout` / `--dialog-timeout` / `--menu-click-timeout` flags. This lets Huzaifah run, for example, `python -m src.core.scraper --workers 5 --page-ready-timeout 16 --dialog-timeout 16 --menu-click-timeout 8 <usernames>` to test the "double the budgets" diagnostic without touching code, and separately `--workers 1` to run the concurrency-vs-account isolation test from §5 item 2.
- **GUI worker count:** `MetaInspectorApp._default_factory` (`src/gui/app.py`) silently relied on `MultiWorkerScraper`'s `DEFAULT_WORKERS = 5` default; there was no way to run fewer workers from the GUI, only from the CLI's existing `--workers` flag. Added a "Workers" dropdown (1 to 5, default 5) to `LeftPanel` (`src/gui/components/left_panel.py`) so the 1-worker isolation test can also be run from the desktop app, not just the CLI.
- **Error visibility (independent of root cause, already flagged as a real gap in §3.3 above):** `data_table.py`'s live results table had no column for `error_message`, so an `ACTIVE` row with no country/joined data was visually identical to "nothing to report." Added an `Error` column to `DataTable.COLUMNS` / `record_to_row`, blank when there's no error. **Scope note:** the clipboard TSV copy and `SHEET_COLUMNS` mentioned in the original directive live in `src/core/records.py`, which only exists on `feature/sprint3-sheets-export` (not yet merged into `dev` as of this writing, per §3.3's "pending Huzaifah's go-ahead") — so that half of the ask isn't applicable yet on `dev`. It should be revisited once Sprint 3 merges.
- **Tests:** `tests/test_core_helpers.py` gained two tests asserting the new `MultiWorkerScraper` timeout kwargs default to the extractor constants and are actually stored when overridden. `tests/test_gui_bridge.py` gained a test that the Workers dropdown actually changes what `_default_factory` builds, plus a test that `record_to_row` surfaces `error_message`; the existing `test_record_to_row` was updated for the new 9th column. Full suite: 61 passed, 1 skipped (pre-existing, unrelated: a local Tcl/Tk install path issue that intermittently skips the real-window GUI smoke test on this machine, confirmed by re-running it repeatedly against the unmodified code).
- **Still open, needs live access to resolve:** which of Hypothesis 1 (Meta-side detection) or Hypothesis 2 (tight timeout budget under load) — or both — actually explains the data loss. That requires running the two diagnostics above against the real checker account, which this session could not do.

### Sprint 4 (2026-10-10, `feature/sprint4-speed-tuning`, branched from `fix/concurrent-timeouts`): implemented what does not require live access; TSK-401/402/403 still need Huzaifah's manual run

**Branching note:** per `team_roles_and_workflow.md` §4 the normal rule is "branch each sprint from latest `dev`." This branch is instead stacked on `fix/concurrent-timeouts` (not yet merged), because TSK-401's benchmark and TSK-403's fail-safe check are meaningless without the configurable timeouts/worker count that fix adds. Both branches need to land before `dev` is caught up; `fix/concurrent-timeouts` should be reviewed/merged first.

- **TSK-401 (100-account benchmark):** Not run. No live checker account in this environment. The CLI (`python -m src.core.scraper`) and GUI already print/display elapsed time and per-account duration, so no new code was needed to capture the benchmark; Huzaifah still needs to run it and record the real number against the 4-5 minute NFR-1 target.
- **TSK-402 (edge cases):** Added `tests/test_extractor_edge_cases.py` — a minimal fake Playwright `Page` driving `extract_instagram`/`extract_threads` through four shapes: IG active-but-no-"Options"-button, IG not-found, Threads inactive-profile-with-no-menu (the quirk already named in memory.md §4.1), and an IG account with no Threads presence. All four confirm the extractor returns a clean status with `error` set and does not raise or hang. **This is not the same as TSK-402's actual acceptance criteria**, which calls for running these against real private/non-existent/no-Threads accounts; a fake page can't reproduce Meta's actual DOM, only the control-flow shape the code is meant to handle.
- **TSK-403 (fail-safe abort under load):** Added `test_worker_stops_immediately_when_session_is_blocked` in `tests/test_core_helpers.py`, which monkeypatches `extract_instagram` to return `session_blocked` partway through a 3-account chunk and asserts `MultiWorkerScraper._worker` stops before the next account and `stop_reason` names the account. This confirms the abort wiring itself (no browser involved). It does not confirm the abort still fires reliably under a real 5-worker run against a real Meta challenge, which is what TSK-403 actually asks for.
- **TSK-404 (UI polish):** Found and fixed a real, verifiable bug while reviewing `data_table.py` for "responsiveness at minimum size": the table's columns sum to ~920px (920px exactly: 40+130+90+95+105+110+125+65+160, the last being the new Error column from the concurrent-timeouts fix), but `theme.WINDOW_MIN_SIZE` is `(950, 600)` and the table only gets the window width minus the 320px left panel, about 600px. There was no horizontal scrollbar, so several columns were simply unreachable at the minimum window size (and were already tight before the Error column, which made it worse). Added a horizontal `CTkScrollbar` bound to the Treeview's `xview`. **Not independently verified by eye** — this machine's Tk/Tcl install does not expose a way for this session to screenshot a live window (see the intermittent skip noted in the Phase 1 entry above), so the fix is confirmed by code review and the arithmetic above, not a screenshot. Hover colors were already present on every button/radio/option-menu before this sprint; no further changes made there without being able to see them rendered.

**Honest summary for this sprint:** of TSK-401 to TSK-404, only TSK-404 got an actual bug fixed and explained here. TSK-401, 402 and 403 got test/tooling groundwork so Huzaifah's manual pass is faster, but none of them can be marked `[x]` in `docs/tasks.md` yet — their acceptance criteria specifically require a real run against live Instagram/Threads, which this environment cannot do.

### Sprint 5 (2026-10-10, `feature/sprint5-exe-packaging`, branched from `feature/sprint4-speed-tuning`)

**TSK-501 (PyInstaller `.spec` under 150MB): built successfully, target missed by more than 2x — measured, not estimated.**

- `config/metainspector.spec` (new; `.gitignore`'s blanket `*.spec` rule was narrowed to `/*.spec` so this one can be tracked — it was silently ignoring the exact deliverable TSK-501 asks for) bundles Playwright's own driver (`playwright/driver`, 102MB) and its Chromium build (`chromium-1243` under `~/AppData/Local/ms-playwright`, 432MB) as onefile data, so the client's machine never needs `playwright install` run on it. `main.py` points `PLAYWRIGHT_BROWSERS_PATH` at the bundled copy, but only when `sys.frozen` is true, so `python main.py` during development is unaffected.
- **Actually built it:** `pyinstaller config/metainspector.spec --distpath dist --workpath build`. Succeeded on the first real attempt (PyInstaller's own `hook-playwright.async_api.py` and the `pyinstaller-hooks-contrib` `hook-customtkinter.py`/`hook-pandas.py` handled the rest without manual hidden-import hacking).
- **Actually ran it:** launched `dist/MetaInspectorDesktop.exe` directly on this machine (not a clean one — see TSK-502 below) and confirmed it stays running past 30s without crashing or printing a traceback (checked via a temporary `console=True` rebuild, then reverted to `console=False` for the real artifact). That is the most this environment can verify; no checker login or scrape was attempted through it.
- **Measured size: 309.9 MB** (`os.path.getsize` on the actual file, twice, across two separate builds). That is **more than double** the 150MB target in `docs/PRD.md` NFR-3. Breakdown: Chromium alone is 432MB on disk before any packing, the Playwright Node driver is another 102MB, and PyInstaller still has to fold in Python itself plus `customtkinter`, `pandas` (pulls in `numpy`/`pyarrow`), and `openpyxl`. `upx` is not installed in this environment, so no UPX compression was applied or measured; even with it, UPX mainly shrinks executable code sections, not Chromium's already-dense data files, so it would not plausibly close a ~160MB gap on its own.
- **What would actually need to change to approach 150MB**, in case Huzaifah wants to pursue it rather than revise the target: (1) swap `chromium-1243` for `chromium_headless_shell-1243` (270MB instead of 432MB) — but this app calls `pw.chromium.launch_persistent_context`, which needs full Chromium, not the headless-shell variant, so that would require a code change, not just a packaging change; (2) drop `pandas`/`openpyxl` as hard dependencies if CSV/Excel export can be done with the standard library instead (`csv` module + a lighter `.xlsx` writer) — not attempted here, out of scope for this sprint; (3) accept `onedir` instead of `onefile` and ship a folder — doesn't reduce total bytes, just changes how they're laid out, so it does not help NFR-3 as written. None of these were implemented; this is left for Huzaifah to decide since (1) and (2) are behavior/dependency changes, not packaging tweaks.
- **Recommendation:** revise NFR-3 in `docs/PRD.md`, or accept a much larger number, rather than treat 150MB as achievable while this app bundles its own Chromium. 150MB was likely written before anyone measured what Playwright's Chromium actually weighs.

**TSK-502 (test the .exe on a clean Windows machine without Python): not done, no such machine available in this environment.** Manual steps for Huzaifah to verify this himself:
1. Copy only `dist/MetaInspectorDesktop.exe` (309.9MB, single file) to a Windows 10/11 machine that has never had Python or Playwright installed — a spare laptop, a fresh VM, or a cloud Windows instance all work, as long as nothing in `pip` has ever touched it.
2. Double-click it (or `MetaInspectorDesktop.exe` from a `cmd` prompt to see any error dialog's text). It should open the same dark-themed window `python main.py` does in this dev environment.
3. Click "Setup Checker Account" and confirm the embedded Chromium window opens for login (this proves the bundled browser, not a system one, is what's launching — a clean machine has no other Chromium to fall back to, so if this fails the bundling is broken, not masked by a dev-machine fallback).
4. Paste 2-3 test usernames and run a check, same as any normal run.
5. Report back whether steps 2-4 worked, and if not, the exact error text/dialog — that's the fastest way to find a bundling gap this environment's launch-and-wait-30-seconds smoke test can't catch (e.g. a missing DLL that only matters on a machine without the Visual C++ redistributable Python's own installer normally pulls in).

**TSK-503 (Quick Start guide):** see `docs/QUICK_START.md` (new file), written for the non-technical client persona from `docs/PRD.md` §2. Covers first-time setup, the one-time checker login, pasting usernames, starting a check, copying to Google Sheets, exporting files, and viewing run history. The Google Sheets paste and history/export steps describe the Sprint 3 features (`feature/sprint3-sheets-export`), which are implemented and tested (86/86 per §3.3 above) but not yet merged into `dev`; the guide is written against where the product is headed once that merges, not against current `dev`, and should be re-checked against the shipped build before handover.

**TSK-504:** skipped, per the directive — final handover is between Huzaifah and the client.

---

## 6. Test C (2026-10-10, `fix/live-test-findings`): first live GUI runs with a saved checker session, and the fixes they led to

Huzaifah ran 5 live GUI sessions against `feature/sprint5-exe-packaging` (solo/1-account, 1-worker, 3-worker/95-account Combined, 5-worker/95-account IG-only, 5-worker/95-account Threads-only), using the `browser_profile/` session already saved on this machine from earlier testing. This session did not initiate any of these live requests itself (see the earlier back-and-forth in this log about not touching a live checker session without Huzaifah driving it); the screenshots were reviewed after the fact.

### 6.1 What the screenshots showed

- **Solo run (Workers=5 setting, 1 account), Combined:** `zaifi._.302` → ACTIVE, Country/Joined both N/A, error `IG about dialog did not load within timeout`, **48.9s** for one account.
- **1-worker run, same account, Combined:** IG succeeded this time — Country **Pakistan**, Joined **November 2019** (matches Test A from 2026-10-07) — but Threads failed with a raw `Threads error: Locator.click: Timeout 5000ms exceeded.\nCall log:\n...`. **49.9s** total.
- **3-worker, 95-account, Combined:** stopped itself after 30 accounts — `Stopped after 30 accounts: Meta challenged the checker account.` The blocked row (`@howard.8991`) showed composite `BLOCKED` with `Threads session blocked: Redirected to ...`. Of the other 29: the single most common error was `Threads 'About this profile' option not found` (roughly half the rows); a few showed the same raw `Locator.click: Timeout` as above, with much longer durations (37.8s, 40.5s); one showed `Threads profile menu not found` (the documented inactive-profile quirk); one IG row showed `IG about dialog did not load within timeout`. Nearly every row that did get an IG country also got IG Joined = **"October 2025"** — for dozens of unrelated accounts.
- **5-worker, 95-account, Instagram Only:** completed all 95 in 4m03s (within the 4-5 min NFR-1 target, though IG-only is the easier of the three modes). Same `IG about dialog did not load` errors on some rows; same suspicious "October 2025" clustering on most successful ones.
- **5-worker, 95-account, Threads Only:** `@howard.8991` got `BLOCKED` again, this time at list position 18 instead of 30 (worker count changes where a given username lands in the processing order, so this is not evidence the block is account-specific — see below). Virtually every other row before the block showed `Threads 'About this profile' option not found`.

### 6.2 Root-cause analysis (grounded in the code as of `fix/concurrent-timeouts`, before this round's fixes)

1. **`Threads 'About this profile' option not found` (by far the most common failure):** this error can only be reached after the "..." menu button was already found *and* clicked (`extractors.py` `extract_threads`, the line right before it). The failure is `_click_menu_item` not finding the "About this profile" text within `MENU_CLICK_TIMEOUT_S`. **That constant was 4.0s, and — this is the real gap — the GUI had no way to raise it.** `fix/concurrent-timeouts` added `--menu-click-timeout` to the CLI, but `MetaInspectorApp._default_factory` never passed it through, so every GUI run, including all 5 of these, used the hardcoded 4.0s default regardless of intent.
2. **Raw `Locator.click: Timeout ... Call log:` (34-40s durations):** a different failure mode from #1 — Playwright *located* the element but its own internal actionability timeout (~30s default) was hit trying to click it, most likely because `_find_threads_menu_button`'s fallback path clicks a raw `<svg>` element directly when no clickable ancestor `div[role=button]` exists, and SVGs are frequently not "stable"/unobscured enough for Playwright's default click to complete. This exception was also being dumped into the UI's Error column verbatim, including Playwright's multi-line "Call log:" trace, visibly breaking the row's height.
3. **`IG about dialog did not load within timeout`:** same shape as #1 but for IG's dialog render step (`DIALOG_TIMEOUT_S`, also 4-8s default, also not GUI-configurable before this fix).
4. **The "October 2025" clustering is the most concerning finding and is *not* explained by anything above.** This value is parsed from real dialog text (`parse_about_dialog` only returns a date when it actually matched a label line), so the dialog did open and did contain a line reading "October 2025" for dozens of unrelated accounts. Two explanations remain open, and this session could not distinguish between them without seeing the raw dialog text: (a) `DATE_KEYS` in `extractors.py` includes the bare word `"joined"` (needed for Threads' real label format, confirmed by existing tests) — if Instagram's current dialog has picked up some *other* line that is exactly "Joined" in a different context, the parser would confidently extract the wrong line; (b) Meta may be serving a plausible-but-wrong placeholder/decoy value to a session it already suspects is automated, rather than blank data (which is what Incident 5/Test B saw) — which would be *more* dangerous than blank N/A, because these rows have no error flag at all, so an operator has no way to know the value is fake. **This was not fixed, because guessing at a fix without evidence risks silently breaking Threads' currently-correct, tested parsing.** Instead, §6.3 below adds the instrumentation needed to actually answer this.
5. **Confirmed working as designed: the fail-safe abort (TSK-403).** Both the 3-worker and the 5-worker Threads-only runs stopped the *entire* run the moment `@howard.8991` came back session-blocked, matching `MultiWorkerScraper._worker`'s `COMPOSITE_BLOCKED` handling exactly. The same username triggered the block in both runs at a different *list position* (30th vs. 18th, because the worker count changes the chunking), which points at a request-count/time-based Meta threshold rather than that one account being specially flagged — consistent with Hypothesis 1 in `ISSUE_concurrent_session_detection.md`.
6. **Baseline is now much slower than historical:** both single-account runs took ~49s total, versus Test A's 21.2s on 2026-10-07 against the same account. This suggests the checker account/session itself may already be somewhat degraded from the earlier Incident 5/Test B testing, independent of concurrency — worth keeping in mind when interpreting any future timing numbers from this same session.

### 6.3 Fixes made in response (none of them re-verified live yet — see 6.4)

- **GUI now exposes Dialog/Menu-click timeouts and a debug-dump checkbox** (`src/gui/components/left_panel.py`, wired through `app.py`'s `_default_factory`). This was the single biggest gap: every number reported above used hardcoded defaults the GUI user had no way to change.
- **Raised the module defaults themselves**, not just the configurable ceiling: `MENU_CLICK_TIMEOUT_S` 4.0 → 8.0, `DIALOG_TIMEOUT_S` 8.0 → 10.0, `PAGE_READY_TIMEOUT_S` 8.0 → 10.0 (`src/core/extractors.py`). `docs/rules.md` §4 caps dynamic polling at "max 8-10s", so these stay within the project's own stated ceiling. **Trade-off to flag honestly:** if most Threads checks really were failing at the 4s menu-click step, doubling that budget could meaningfully slow down a run that hits this failure often, working against NFR-1's 4-5 minute target — this has not been measured.
- **Added `_safe_click`:** a 3-stage click (plain → `force=True` → raw JS `el.click()`), each capped at 5s, used everywhere the code clicks a menu/options element. This directly targets failure #2: worst case is now ~10s instead of Playwright's ~30s default, which is a net *improvement* for speed in the failure case even after the default timeout increases above.
- **Added `_short_error`:** exceptions caught by the broad `except PlaywrightError` blocks are now reduced to one line instead of the full multi-line `str(exc)`, so the UI's Error column (and `data_table.py`'s new `_error_cell`, a second line of defence that also collapses/truncates any stray multi-line or very long message) no longer shows a raw stack-trace-like dump.
- **Added `debug_dump`** (CLI `--debug-dump`, GUI checkbox "🐛 Save debug captures", off by default): when on, every dialog/panel text actually read is written to `debug/` (git-ignored). This is `ISSUE_concurrent_session_detection.md` §5 item 3, proposed on 2026-10-07 and never implemented until now. **This is the concrete next step for the "October 2025" question** — rerun a small batch with it checked, and the `debug/ig_<username>_<timestamp>.txt` files will show definitively whether the real dialog text says "October 2025" for each of those accounts (a Meta-side issue, nothing to fix here) or something else that the parser is misreading (a real bug in `DATE_KEYS`/`_value_after_label`).
- Tests: `tests/test_extractor_edge_cases.py` gained 9 new tests (`_safe_click`'s 3 stages, a regression guard that no click stage can take anywhere near Playwright's ~30s default, `_poll_dialog`'s `debug_sink` wiring, `_write_debug_dump`, `_short_error`). `tests/test_core_helpers.py` gained tests that `_check_account` actually forwards the configured timeouts and `debug_dump` to the extractors (not the module defaults). `tests/test_gui_bridge.py` gained a test that the new GUI fields change what `_default_factory` builds, including that invalid timeout input falls back safely instead of crashing. Full suite: **81 passed**, 0 skipped on this run (the pre-existing Tcl/Tk flake noted in earlier entries did not reproduce this time).

### 6.3b Follow-up fix (same day): packaged .exe's "Setup Checker Account" couldn't find its bundled Chromium

Huzaifah then tested the actual packaged `.exe` (not `python main.py`) and clicking "Setup Checker Account" failed: `Login browser failed: : Executable doesn't exist at C:\Users\...\_MEI00004b402\playwright\driver\package\.local-browsers\chromium-1243\chrome-win64\chrome.exe`.

**Root cause:** `main.py`'s `_point_playwright_at_bundled_browsers` (added in the Sprint 5 packaging work) checked `Path(sys.executable).resolve().parent / "ms-playwright"` to find the bundled Chromium. That is correct for a PyInstaller `--onedir` build, but `config/metainspector.spec` builds `--onefile` (the default `EXE(...)` call with no `exclude_binaries`), and a onefile build extracts its bundled data to a **temp directory at `sys._MEIPASS`** at runtime, not next to the `.exe` on disk. So the check always found nothing, the environment variable was never set, and Playwright fell back to its own internal default resolution -- which produced exactly the `.local-browsers` path in the error above, where nothing had ever been installed.

**Fix:** check `sys._MEIPASS` first (when set), falling back to the `sys.executable`-parent check in case this is ever built `--onedir` instead.

**Verified, not just implemented this time:** rebuilt the `.exe`, launched it, and while it was running, inspected its live `_MEI*` extraction directory under `%TEMP%` directly. `chrome.exe` genuinely exists at `<extraction dir>/ms-playwright/chromium-1243/chrome-win64/chrome.exe` -- the exact path the fixed code now points `PLAYWRIGHT_BROWSERS_PATH` at. This confirms the fix resolves the specific error Huzaifah hit, though the actual "Setup Checker Account" login flow (a visible Chromium window opening for manual login) still was not click-tested end-to-end, since this session has no way to drive the GUI's mouse/keyboard -- only to inspect files and processes.

### 6.4 What this session still could not do

- **None of the above was re-verified against the live site.** The defaults were raised based on live evidence (this is no longer purely speculative like the `fix/concurrent-timeouts` branch), but nobody has re-run the same batches with the new GUI timeout fields and confirmed the failure rate actually drops.
- **The "October 2025" question is open**, not resolved — `debug_dump` makes it answerable, but answering it needs one more live run with the checkbox on and someone reading the resulting files in `debug/`.
- **The `_safe_click` SVG-click-hang fix (#2) is untested against the real Threads DOM** — the unit tests confirm the 3-stage fallback logic itself works, not that it actually resolves the real click target Playwright was struggling with live.

### 6.5 Round 2 verification (2026-10-10, `fix/data-accuracy-and-nfr1-verification`): working-session gate failed

Pulled `fix/live-test-findings` (already up to date) and branched as directed. Cookie preflight reported connected, but the approved live 10-account Combined/1-worker CLI run returned no transparency fields for any account (`10 accounts in 193.8s`, 10 IG Options errors, nine Threads About-option errors and one Threads menu error). No raw dialogs were captured. A subsequent same-profile live screenshot and visible-text capture showed Log In / Sign Up, confirming the observed page was unauthenticated despite the cookie metadata. Stopped further live work: neither October 2025 hypothesis is resolved and the 100-account benchmark was not run. No application code changed. Full pytest retry outside the sandbox: `81 passed in 4.19s`; original sandbox failures are retained in the new [running test log](test_log.md). Dedicated reports cover [data accuracy and local evidence](implementation/TSK-402-data-accuracy.md), [the gated benchmark](implementation/TSK-401-nfr1-benchmark.md), and [verification methods and alternatives](implementation/round2-verification-process.md). Manual checker re-authentication is needed before resuming; no packaged-executable automation or Huzaifah-driven GUI run occurred in this round.

### 6.6 Setup window visibility follow-up (2026-10-10)

Huzaifah launched `python main.py` and clicked Setup, then reported no visible browser. Live process/window inspection found the app-owned Chromium window titled Instagram, handle 67942. Restored that existing window and checked that it became the foreground window (`ForegroundRequest=True`, `ForegroundMatches=True`). No source fix or profile reset was needed; authentication remains for the user to complete. See [the dedicated diagnostic](implementation/checker-login-window-visibility.md) and the new live-GUI observation row in [test_log.md](test_log.md).

### 6.7 User-run batch and five-checker assessment (2026-10-10)

Huzaifah supplied two screenshots of a 95-account Combined/5-worker run with debug off. The final screen shows 27 returned in displayed 3m 00s, 26 ACTIVE/1 BLOCKED, stopped on a checker challenge while the header still says Connected. Across both screenshots, 13 rows have IG country/date (11 October 2025 and two November 2025), 14 lack both, and all 27 lack Threads country/date. These are user-run screenshot observations, not independently measured benchmark results. [The dedicated assessment](implementation/current-failures-and-checker-pool.md) lists observed failures, code-review risks, the unresolved date hypotheses (including genuinely similar account creation dates), and a proposed five-profile checker design with alternatives. No application code or new live requests were made; a checker pool remains unimplemented and unverified.

### 6.8 Source audit and corrected same-account comparison (2026-10-10)

Huzaifah requested all source checked and problems kept in one file. Created [problem_log.md](problem_log.md) with stable P01–P30 entries and evidence states. The initial alleged country/date mismatch compared brenna1074 (April 2016, country absent) with brenda_1074 (China / October 2025); the corrected same-account browser screenshot explicitly matches the app's China / October 2025. No date-parser change was justified by that comparison. Reviewed the runtime path and statically inventoried all 57 existing Python files (16 production, 37 legacy, four tests); local synthetic Chromium and pure-code checks reproduced 12 observation groups, including hidden/unrelated-dialog acceptance, incomplete polling, malformed label-as-value, wrong menu targeting and false ACTIVE classification. These are proven local risks, not a claim they caused the actual matching October value. Full suite: `81 passed in 1.86s`. No application source or live checker state changed. [Audit method and alternatives](implementation/source-audit-and-problem-log.md), [reproduction output](implementation/evidence/audit-reproductions.txt) and [running test log](test_log.md) retain the evidence.
