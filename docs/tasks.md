# Work Breakdown Structure (WBS) & Sprint Tasks

## Document: `docs/tasks.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)  
**Total Timeline:** 15 Calendar Days  
**Team Roles:** Partner Developer + Claude Code (implementation, both backend and frontend) | Claude Code — Owner's session (architecture, review, merge — role formerly held by Antigravity AI)  

> Note: the "Dev 1 / Dev 2" assignee split below was the original two-person plan. In practice every task was implemented by the Partner Developer + Claude pairing; the column is kept only to show the intended backend/frontend split per task.

---

## 1. Project Goal & Milestone Overview

- **Primary Goal:** Deliver a production-ready, standalone Windows `.exe` capable of verifying account status and country transparency data for 100 accounts in 4 to 5 minutes, with cross-ban linking, 1-click Google Sheets export, and complete run history.
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
| **TSK-203** | Build Right Panel: Real-time data table with color-coded status badges | Dev 2 | `[x]` | Table renders test rows with green (Active) and red (Banned) cell highlights. Verified: `data_table.py` — rows (not individual badge cells) are tinted; see deviation #3 in the Sprint 1 & 2 progress report. |
| **TSK-204** | Implement worker-to-UI thread-safe queue for real-time row rendering | Dev 1 | `[x]` | GUI remains fully responsive during active scraping; zero frozen window warnings. Verified: `bridge.py`, event queue drained every 100ms via `root.after()`. |
| **TSK-205** | Implement one-time in-app setup browser launcher for checker login | Dev 1 | `[x]` | Setup button opens Chromium to IG/Threads; user logs in; session cookies persist on restart. Verified: `app.py`/`core/session.py` — shows Connected/Disconnected only, not username (see deviation #5). |

> **Status as of 2026-10-07:** All 5 tasks implemented, reviewed (58/58 tests, no defects found) and **merged into `dev`** (squash merge of PR #2). First live tests against real Instagram/Threads followed the merge — see `docs/memory.md` §5 for results, and `docs/ISSUE_concurrent_session_detection.md` for an open risk found during that testing (doesn't block Sprint 3, must be resolved before Sprint 4's TSK-401 benchmark).

---

### Sprint 3: Google Sheets Exporter & SQLite History (Days 9 to 11)
*Focus: 1-click clipboard integration, database logging, and history viewer tab.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-301** | Implement `ClipboardExporter` formatting tabular data to TSV | Dev 2 | `[ ]` | Copy button copies TSV to clipboard; pressing `Ctrl + V` in Google Sheets populates separate columns cleanly. |
| **TSK-302** | Add green toast confirmation feedback ("Copied to Clipboard!") | Dev 2 | `[ ]` | Visual feedback banner displays for 2.5 seconds upon clicking copy button. |
| **TSK-303** | Initialize SQLite `history.db` and implement schema migrations | Dev 1 | `[ ]` | Database creates `runs` and `run_items` tables on first launch if not present. |
| **TSK-304** | Build History Viewer dialog/tab to view, filter, and re-copy past runs | Dev 2 | `[ ]` | User can select a past run date and copy that batch's results directly to Google Sheets. |
| **TSK-305** | Add CSV and Microsoft Excel (.xlsx) file export handlers | Dev 1 | `[ ]` | Successfully exports `.csv` and `.xlsx` files with UTF-8 encoding. |

---

### Sprint 4: 100-Account Speed Calibration & Stress Testing (Days 12 to 13)
*Focus: Rate-limit testing, edge cases, and 4 to 5-minute benchmark verification.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-401** | Execute 100-account benchmark test using 5 parallel workers | Dev 1 & Dev 2 | `[ ]` | Complete 100 accounts in under 5 minutes without triggering Meta rate limits. |
| **TSK-402** | Test edge cases: private accounts, non-existent users, no-Threads accounts | Dev 1 | `[ ]` | App handles all edge cases gracefully without crashing or hanging. |
| **TSK-403** | Test fail-safe abort on security challenges and checkpoints | Dev 1 | `[ ]` | Immediate alert and worker pause if Meta checkpoint or CAPTCHA is encountered. |
| **TSK-404** | Polish UI styling, hover animations, scrollbars, and button responsiveness | Dev 2 | `[ ]` | Clean, modern user experience verified across different Windows screen resolutions. |

> **Status as of 2026-10-10 (`feature/sprint4-speed-tuning`):** none of these can be checked off yet — their acceptance criteria require a real run against live Instagram/Threads, and no checker account/live access was available in this environment. What was actually done: added fail-safe-abort and extractor edge-case tests that exercise the real control flow with mocked browser interactions (not a live run), and fixed a genuine, verified bug for TSK-404 (the live table's 9 columns overflowed the 950px minimum window width with no horizontal scrollbar — fixed). See `docs/memory.md`'s Sprint 4 entry for exactly what was and wasn't verified.

---

### Sprint 5: Packaging & Client Delivery (Days 14 to 15)
*Focus: PyInstaller standalone build, clean documentation, and client handover.*

| Task ID | Task Description | Assignee | Status | Acceptance / Test Criteria |
| :--- | :--- | :--- | :---: | :--- |
| **TSK-501** | Create PyInstaller `.spec` configuration bundling Playwright Chromium | Dev 1 | `[ ]` | Build single portable `.exe` package under 150 MB. |
| **TSK-502** | Test standalone `.exe` on a clean Windows machine without Python | Dev 2 | `[ ]` | App runs smoothly on bare Windows machine without errors. |
| **TSK-503** | Write Quick Start User Guide (PDF / Markdown) for client | Dev 2 | `[ ]` | Illustrated guide explaining login setup, paste input, and Google Sheets copy. |
| **TSK-504** | Final client handover and 15-day free support warranty activation | Dev 1 & Dev 2 | `[ ]` | Client confirms receipt and approves delivery. |

> **Status as of 2026-10-10 (`feature/sprint5-exe-packaging`):** TSK-501 built and actually ran (confirmed it stays open 30s+ without crashing), but its own acceptance criterion ("under 150 MB") was not met — measured 309.9 MB, over double the target, because Chromium alone is 432 MB on disk. Not checking this off; see `docs/memory.md`'s Sprint 5 entry for the full breakdown and what would have to change to get closer to 150 MB. TSK-502 not done (no clean Windows machine without Python in this environment); manual steps for Huzaifah are in that same memory.md entry. TSK-503 done (`docs/QUICK_START.md`), but written against Sprint 3 features that are not yet merged into `dev` — re-verify against the shipped build before handover. TSK-504 intentionally skipped (handover is between Huzaifah and the client, not this session).
