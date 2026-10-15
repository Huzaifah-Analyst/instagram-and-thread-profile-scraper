# Work Breakdown Structure (WBS) & Sprint Tasks

## Document: `docs/tasks.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)
**Total Timeline:** 15 Calendar Days
**Team Roles:** Partner Developer + Claude Code (implementation, both backend and frontend) | Claude Code - Owner's session (architecture, review, merge - role formerly held by Antigravity AI)

> Note: the "Dev 1 / Dev 2" assignee split below was the original two-person plan. In practice every task was implemented by the Partner Developer + Claude pairing; the column is kept only to show the intended backend/frontend split per task.

---

## 1. Project Goal & Milestone Overview

- **Primary Goal:** Deliver a standalone Windows `.exe` for account status and transparency data, with the client-accepted 6 to 7 minute country/date target (measured limits in PRD.md NFR-1), with cross-ban linking, 1-click Google Sheets export, and complete run history.
- **Sprint Cadence:** 5 Sprints across 15 Days.

---

## 2. Granular Task Breakdown

### Sprint 1: Backend Scraper Core & 5-Worker Concurrency (Days 1 to 4)
*Focus: Playwright automation engine, multi-worker contexts, and ban linking logic.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-101** | Implement resource blocker (abort images, media, fonts) in Playwright | Dev 1 | `[x]` | Verified network inspector shows zero image/video asset downloads; page load < 0.5s. |
| **TSK-102** | Refactor Instagram modal extractor with dynamic polling & fallback locators | Dev 1 | `[x]` | Test against 10 sample IG accounts; extract country and joined date accurately without crashes. |
| **TSK-103** | Refactor Threads extractor using bounding box SVG menu detection | Dev 1 | `[x]` | Test against 10 Threads profiles; extract country, joined date, and badge. |
| **TSK-104** | Develop `BanLinkEngine` module for cross-platform ban propagation | Dev 2 | `[x]` | Unit test: when IG=banned, Threads=banned and final status is BANNED. |
| **TSK-105** | Build 5-worker concurrent dispatcher with chunking logic | Dev 1 | `[x]` | Run 20 accounts concurrently across 5 workers; total execution finishes in under 60 seconds. |

---

### Sprint 2: Desktop GUI Development & State Binding (Days 5 to 8)
*Focus: CustomTkinter visual interface, split-panel layout, and real-time event updates.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-201** | Create base window layout, Cyber Dark color scheme, and typography tokens | Dev 2 | `[x]` | Window launches with 1150x750 default dimensions; dark theme applied smoothly. Verified: `app.py`/`theme.py`, matches `design.md` tokens. |
| **TSK-202** | Build Left Panel: Username text box, file import button, mode radio selectors | Dev 2 | `[x]` | Text area accepts pastes; `.txt` import button populates usernames cleanly. Verified: `left_panel.py`. |
| **TSK-203** | Build Right Panel: Real-time data table with color-coded status badges | Dev 2 | `[x]` | Table renders test rows with green (Active) and red (Banned) cell highlights. Verified: `data_table.py` - rows (not individual badge cells) are tinted; see deviation #3 in the Sprint 1 & 2 progress report. |
| **TSK-204** | Implement worker-to-UI thread-safe queue for real-time row rendering | Dev 1 | `[x]` | GUI remains fully responsive during active scraping; zero frozen window warnings. Verified: `bridge.py`, event queue drained every 100ms via `root.after()`. |
| **TSK-205** | Implement one-time in-app setup browser launcher for checker login | Dev 1 | `[x]` | Setup button opens Chromium to IG/Threads; user logs in; session cookies persist on restart. Verified: `app.py`/`core/session.py` - shows Connected/Disconnected only, not username (see deviation #5). |

> **Status as of 2026-10-07:** All 5 tasks implemented, reviewed (58/58 tests, no defects found) and **merged into `dev`** (squash merge of PR #2). First live tests against real Instagram/Threads followed the merge - see `docs/memory.md` §5 for results, and `docs/ISSUE_concurrent_session_detection.md` for an open risk found during that testing (doesn't block Sprint 3, must be resolved before Sprint 4's TSK-401 benchmark).

---

### Sprint 3: Google Sheets Exporter & SQLite History (Days 9 to 11)
*Focus: 1-click clipboard integration, database logging, and history viewer tab.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-301** | Implement `ClipboardExporter` formatting tabular data to TSV | Dev 2 | `[x]` | Copy button copies TSV to clipboard; pressing `Ctrl + V` in Google Sheets populates separate columns cleanly. Verified: core/clipboard.py, GUI actions and actual export tests; see BL-01 report for packaged copy. |
| **TSK-302** | Add green toast confirmation feedback ("Copied to Clipboard!") | Dev 2 | `[x]` | Visual feedback banner displays for 2.5 seconds upon clicking copy button. Verified: components/toast.py, flash_copied and actual Tk feedback assertions. |
| **TSK-303** | Initialize SQLite `history.db` and implement schema migrations | Dev 1 | `[x]` | Database creates `runs` and `run_items` tables on first launch if not present. Verified: core/history_db.py and legacy migration/full-record round-trip tests. |
| **TSK-304** | Build History Viewer dialog/tab to view, filter, and re-copy past runs | Dev 2 | `[x]` | User can select a past run date and copy that batch's results directly to Google Sheets. Verified: components/history_dialog.py; saved run selection and copy/export controls. |
| **TSK-305** | Add CSV and Microsoft Excel (.xlsx) file export handlers | Dev 1 | `[x]` | Successfully exports `.csv` and `.xlsx` files with UTF-8 encoding. Verified: core/export.py, actual CSV/XLSX file assertions and packaged checks. |

---

### Sprint 4: 100-Account Speed Calibration & Stress Testing (Days 12 to 13)
*Focus: Rate-limit testing, edge cases, and 4 to 5-minute benchmark verification.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-401** | Execute 100-account benchmark test using 5 parallel workers | Dev 1 & Dev 2 | `[ ]` | Complete 100 accounts in under 5 minutes without triggering Meta rate limits. Remains open: 100-target under-300s acceptance is unproven; Round 11 Smart measured 95 targets. |
| **TSK-402** | Test edge cases: private accounts, non-existent users, no-Threads accounts | Dev 1 | `[x]` | App handles all edge cases gracefully without crashing or hanging. Verified: test_extractor_edge_cases.py, private-status helper tests and recorded genuine no-profile outcomes in Round 7. This does not close every live rendering failure. |
| **TSK-403** | Test fail-safe abort on security challenges and checkpoints | Dev 1 | `[x]` | Immediate alert and worker pause if Meta checkpoint or CAPTCHA is encountered. Verified: scraper global stop path, fail-safe tests and recorded live challenge stops in problem_log.md; implemented as fail-safe stop rather than a resumable pause. |
| **TSK-404** | Polish UI styling, hover animations, scrollbars, and button responsiveness | Dev 2 | `[ ]` | Clean, modern user experience verified across different Windows screen resolutions. Remains open for other physical display resolutions/scalings: current 1920x1080 EXE and minimum-size actual Tk tested; clipping fixed. |

> **Status as of 2026-10-10 (`feature/sprint4-speed-tuning`):** none of these can be checked off yet - their acceptance criteria require a real run against live Instagram/Threads, and no checker account/live access was available in this environment. What was actually done: added fail-safe-abort and extractor edge-case tests that exercise the real control flow with mocked browser interactions (not a live run), and fixed a genuine, verified bug for TSK-404 (the live table's 9 columns overflowed the 950px minimum window width with no horizontal scrollbar - fixed). See `docs/memory.md`'s Sprint 4 entry for exactly what was and wasn't verified.

---

### Sprint 5: Packaging & Client Delivery (Days 14 to 15)
*Focus: PyInstaller standalone build, clean documentation, and client handover.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-501** | Create PyInstaller `.spec` configuration bundling Playwright Chromium | Dev 1 | `[ ]` | Build single portable `.exe` package under 150 MB. Build implemented and rebuilt; remains open against the original under-150-MB criterion (known NFR-3 deviation). |
| **TSK-502** | Test standalone `.exe` on a clean Windows machine without Python | Dev 2 | `[ ]` | App runs smoothly on bare Windows machine without errors. Not run: needs a second physical Windows machine; see implementation/bl02-clean-machine-checklist.md. |
| **TSK-503** | Write Quick Start User Guide (PDF / Markdown) for client | Dev 2 | `[x]` | Illustrated guide explaining login setup, paste input, and Google Sheets copy. Current five-mode guide and real selector illustration updated; packaged observations and limits in BL-01 report. |
| **TSK-504** | Final client handover and 15-day free support warranty activation | Dev 1 & Dev 2 | `[ ]` | Client confirms receipt and approves delivery. |

> **Status as of 2026-10-10 (`feature/sprint5-exe-packaging`):** TSK-501 built and actually ran (confirmed it stays open 30s+ without crashing), but its own acceptance criterion ("under 150 MB") was not met - measured 309.9 MB, over double the target, because Chromium alone is 432 MB on disk. Not checking this off; see `docs/memory.md`'s Sprint 5 entry for the full breakdown and what would have to change to get closer to 150 MB. TSK-502 not done (no clean Windows machine without Python in this environment); manual steps for Huzaifah are in that same memory.md entry. TSK-503 done (`docs/QUICK_START.md`), but written against Sprint 3 features that are not yet merged into `dev` - re-verify against the shipped build before handover. TSK-504 intentionally skipped (handover is between Huzaifah and the client, not this session).

---

## Remaining Work Backlog (updated 15 October 2026)

Updated 15 October 2026 on `feature/targeted-check-modes`. Historical sprint
notes below retain their original dates. Current acceptance evidence is in
implementation/bl01-packaged-verification.md; no merge into dev is authorized.

### A. Blocks client handover

| ID | Task | Why it matters | Status |
| :--- | :--- | :--- | :---: |
| **BL-01** | Rebuild `dist/MetaInspectorDesktop.exe` | Rebuilt 15 October 2026, 325,044,156 bytes. Seven actual EXE checks passed on the development machine; see implementation/bl01-packaged-verification.md. | `[x]` |
| **BL-02** | TSK-502: run the exe on a clean Windows box with no Python | Never done. This is the client's actual environment. | `[ ]` |
| **BL-03** | Merge the feature branch into `dev` | Huzaifah merges; this session does not self-merge. | `[ ]` |
| **BL-04** | Move `docs/accounts.txt` out of the repo folder | Plaintext checker passwords and TOTP secrets. Gitignored and never committed, but the folder itself may be handed over. | `[ ]` |
| **BL-05** | Re-verify `docs/QUICK_START.md` against the shipped build | Five modes, real Setup versus Manage behavior, output selector illustration, exports and history updated from actual EXE checks; limits documented. | `[x]` |

### B. Speed and feature work

| ID | Task | Why it matters | Status |
| :--- | :--- | :--- | :---: |
| **SP-01** | Conditional Threads when Instagram provides a real country | Round 11 independently measured 225.2s for 95 targets; D1/D2 reporting fixes committed in 8e4b066. No timing guarantee. | `[x]` |
| **SP-02** | IG Status Only without login | Implemented; Round 11 independently measured 62.4s for 95 targets. Singular follower fix committed in 8e4b066; unknown deadline misses remain open. | `[x]` |
| **SP-03** | Rename worker control to Parallel workers | Label corrected; same workers variable and value. Real Tk coverage passes. | `[x]` |

### C. Documents that contradict the build

| ID | Task | Status |
| :--- | :--- | :---: |
| **DC-01** | PRD performance acceptance updated with client 6 to 7 minutes, historical target counts and attributed single-run measurements. | `[x]` |
| **DC-02** | PRD scope now includes local authenticator TOTP auto-login; CAPTCHA and unsupported verification stay manual. | `[x]` |
| **DC-03** | Task statuses reviewed against source, tests and recorded measurements. TSK-401/404/501/502 remain open against their unmet acceptance criteria. | `[x]` |
| **DC-04** | PRD records the 325,044,156-byte rebuild and bundled-browser size deviation, plus the rejected browser-install alternative. | `[x]` |

### D. Open, probably not code-fixable

| ID | Task | Status |
| :--- | :--- | :---: |
| **OP-01** | P64: `lyricnixon292`'s Threads profile is live but completely empty, and Threads renders no About control for it. 1 failure in 149 platform checks. | `[ ]` |
| **OP-02** | Three checker accounts are suspended; only `checker_5` is in use. Replacements needed before multi-checker concurrency is meaningful. | `[ ]` |


### Packaging follow-up (15 October 2026)

D1-D3 were committed in 8e4b066 and the 278-test suite was green before
packaging. Actual EXE inspection found a collapsed username input and clipped
Start controls at 150 percent scaling. The left panel now scrolls; minimum-size
real Tk regression and final 279-test suite pass. Rebuilt EXE checks and limits:
[BL-01 report](implementation/bl01-packaged-verification.md).

TSK-401 remains open because 95-target Smart timing does not prove 100-target
under-300s acceptance. TSK-404 remains open for a physical display matrix.
TSK-501 packaging exists but its original under-150-MB requirement is unmet.
TSK-502/BL-02 need the separate physical machine and remain unchecked. BL-03,
BL-04 and TSK-504 were not performed in this task.
