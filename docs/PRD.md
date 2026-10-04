# Product Requirements Document (PRD)

## Project Name: MetaInspector Desktop (Instagram & Threads Checker)
**Target Platform:** Windows 10 / 11 Standalone Application (`.exe`)  
**Development Timeline:** 15 Calendar Days  
**Team:** 2 Developers (Collaborative Git Workflow)  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Problem
Operations teams, agencies, and social media managers frequently audit large batches of Instagram and Threads accounts to identify active status, registration age, and account origin country. 
- **Meta Transparency Concealment:** Unlike basic alive/dead status, country location ("Account based in") and registration date ("Date joined") are strictly hidden behind Meta's dynamic transparency modals and require an authenticated session.
- **Rate-Limiting Bottleneck:** Scraping these transparency endpoints via direct HTTP requests triggers aggressive `HTTP 429 (Rate Limit)` blocks on single accounts.
- **Workflow Friction:** Manually clicking through hundreds of accounts in a browser takes hours, while typical CLI scrapers are complex for non-technical clients and lack seamless spreadsheet export.

### 1.2 The Solution
**MetaInspector Desktop** is a high-performance Windows desktop application that automates status verification and transparency data extraction across Instagram and Threads. It achieves **100 accounts in 4 to 5 minutes** via a safe 5-worker parallel browser concurrency model, enforces cross-platform ban detection, formats results for 1-click Google Sheets pasting, and maintains a complete local audit history.

---

## 2. User Personas & Use Cases

- **Persona:** Social Media Auditor / Client Operator.
- **Technical Literacy:** Non-technical. Needs a double-clickable Windows `.exe` with an intuitive graphical interface. No Python, terminal, or driver installation required.
- **Primary Use Case:** Pastes a list of 100 to 500 usernames, selects checking mode, hits "Start", views live progress, clicks "Copy for Google Sheets", and pastes directly into their spreadsheet.

---

## 3. Functional Requirements (FR)

### FR-1: Account Status Detection
- **Instagram Statuses:** `Active`, `Banned/Suspended`, `Private`, `Not Found`.
- **Threads Statuses:** `Active`, `Banned/Suspended`, `Not Found`.
- Detection must evaluate HTTP status codes, redirection to login/challenge checkpoints, and DOM error containers ("Sorry, this page isn't available", "Suspicious activity detected").

### FR-2: Transparency Data Extraction
- **Account Country:** Extract the registered country ("Account based in" / "Hesabın bulunduğu konum" / "Based in").
- **Date Joined:** Extract registration month and year (e.g., "September 2026").
- **Threads Badge:** Extract numeric signup badge sequence (e.g., "100M+").
- **Multi-Language Parsing:** Support English and Turkish interface labels dynamically.

### FR-3: Cross-Platform Ban Linking Rule
- If an account is flagged as `Banned`, `Suspended`, or `Checkpoint` on either Instagram or Threads:
  - Both platform statuses are marked as **BANNED** in the unified output.
  - The final composite status is set to **BANNED** with red UI highlighting.

### FR-4: Operational Modes
1. **Instagram Only Mode:** Scrapes only Instagram status and country data (~6–10s per account baseline).
2. **Threads Only Mode:** Scrapes only Threads status, country, and join badge.
3. **Combined Mode:** Scrapes Instagram first; if valid, checks Threads; applies cross-platform ban linking rule.

### FR-5: 1-Click Google Sheets Integration
- Provide a dedicated **"Copy for Google Sheets"** button.
- Format tabular data into **Tab-Separated Values (TSV)**:
  `Username\tStatus\tIG Country\tIG Joined\tThreads Country\tThreads Joined`
- Ensure direct `Ctrl + V` in Google Sheets populates individual columns without requiring import wizards or CSV delimiters.
- Provide secondary export to `.csv` and `.xlsx` (Excel).

### FR-6: Run History & Local Audit Log
- Automatically persist every batch run to an embedded SQLite database (`history.db`).
- Store metadata: Batch ID, Timestamp, Mode, Total Accounts, Banned Count, Duration, and full itemized results.
- Provide a **History Viewer Tab** to search past batches, review results, and re-copy to clipboard.

### FR-7: Secure 1-Time Session Authentication
- Provide an in-app setup button to launch an official Chromium window for Instagram and Threads.
- User logs in manually with their dummy/checker account (including 2FA support).
- Save cookies and session state in an encrypted local `browser_profile/` directory.
- No plain-text passwords stored in source code or database.
- Session remains active across app restarts.

---

## 4. Non-Functional Requirements (NFR)

### NFR-1: Performance & Speed Benchmarks
- **Alive / Dead Check:** **1 to 2 minutes** per 100 accounts.
- **Country & Date Joined Check:** **4 to 5 minutes** per 100 accounts (achieved via 5 parallel browser workers).

### NFR-2: Reliability & Anti-Detection
- Resource blocking (disable images, video streams, heavy stylesheets) to reduce page payload and load latency (<0.5s per navigation).
- Dynamic DOM event polling instead of fixed sleeps.
- Immediate fail-safe abort upon detecting security checkpoints or CAPTCHAs.

### NFR-3: Portability
- Packaged as a single standalone executable (`.exe`) under 150 MB via PyInstaller.
- Compatible with Windows 10 (64-bit) and Windows 11.

---

## 5. Scope Boundaries

### In Scope
- Windows desktop GUI application.
- Multi-worker Playwright automation engine.
- Status, Country, Date Joined, and Badge extraction for Instagram and Threads.
- Cross-ban linking, TSV clipboard copying, and SQLite run history.
- Standalone `.exe` build.

### Out of Scope
- Mobile apps (iOS/Android) or web-hosted SaaS portal.
- Providing or supplying dummy Instagram accounts (client must supply their own checker account).
- Bypassing 2FA/CAPTCHAs programmatically (user solves 2FA once in the setup browser window).
