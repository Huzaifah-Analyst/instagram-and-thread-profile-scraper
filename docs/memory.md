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
| *Pending — reviewed 2026-10-07* | #2 | Andleeb Hassan (co-authored by Claude Opus 5.5) | `feature/sprint2-desktop-gui` | — | CustomTkinter interface (`src/gui/`), thread-safe bridge, checker-session detection (`src/core/session.py`), `pause()`/`resume()` on `MultiWorkerScraper`. 15 new tests (58 total, all passing on re-run). **Awaiting Huzaifah's merge decision — not yet merged.** |
| *Pending* | #3 | — | `feature/sheets-exporter` | — | TSV clipboard formatter and Google Sheets copy button. |
| *Pending* | #4 | — | `feature/history-db` | — | SQLite database and history viewer dialog. |

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
- **Docs found stale during this review and corrected:** `docs/architecture.md` §2 (described 5 isolated browser contexts; actual implementation uses 1 persistent context with 5 pages — a documented, deliberate deviation) and §4 (`BanLinkEngine` pseudocode was missing the session-blocked carve-out that the real `src/core/ban_engine.py` implements); `docs/tasks.md` Sprint 2 rows (still showed `[ ]`); `docs/rules.md` and `docs/PRD.md` "Team" lines (still said "2 Developers", not reflecting the actual AI-paired team structure).

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
- **Open question, not yet isolated:** Is this concurrency-triggered (5 simultaneous pages on one session) or account-triggered (this particular disposable account is new/weak and gets flagged quickly regardless)? Needs a controlled test: same account, 1 worker, 5–10 accounts, Instagram-only mode, to see if sequential single-page requests avoid the silent-degradation pattern.
- **Action needed:** Re-run "Setup Checker Account" (session was challenged and is now stale) before any further testing.
