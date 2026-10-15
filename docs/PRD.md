# Product Requirements Document (PRD)

## Project Name: MetaInspector Desktop (Instagram & Threads Checker)
**Target Platform:** Windows 10 / 11 Standalone Application (`.exe`)
**Development Timeline:** 15 Calendar Days
**Team:** Partner Developer + Claude Code (implementation) | Claude Code - Owner's session (architecture & review) - see `docs/team_roles_and_workflow.md`

---

## 1. Executive Summary & Problem Statement

### 1.1 The Problem
Operations teams, agencies, and social media managers frequently audit large batches of Instagram and Threads accounts to identify active status, registration age, and account origin country.
- **Meta Transparency Concealment:** Unlike basic alive/dead status, country location ("Account based in") and registration date ("Date joined") are strictly hidden behind Meta's dynamic transparency modals and require an authenticated session.
- **Rate-Limiting Bottleneck:** Scraping these transparency endpoints via direct HTTP requests triggers aggressive `HTTP 429 (Rate Limit)` blocks on single accounts.
- **Workflow Friction:** Manually clicking through hundreds of accounts in a browser takes hours, while typical CLI scrapers are complex for non-technical clients and lack seamless spreadsheet export.

### 1.2 The Solution
**MetaInspector Desktop** automates status verification and transparency data extraction across Instagram and Threads with parallel browser workers, cross-platform ban detection, spreadsheet export and local run history. Runtime depends on the selected mode and live site conditions; NFR-1 records measured results rather than a guaranteed throughput.

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
1. **Instagram Only:** authenticated IG status, country and joined date.
2. **Threads Only:** authenticated Threads status, country, joined date and badge.
3. **Combined (default):** both platforms, with existing cross-platform ban linking.
4. **Smart Combined:** Instagram first; skips Threads if IG discloses a real
   country. Skipped Threads status/country/date/badge are not collected. Missing
   or Not shared IG country falls through to the regular Threads check.
5. **IG Status Only:** fresh anonymous context, status from explicit page-text
   markers, Unknown on inconclusive reads. No checker login or account pacing.
   Country/date and all Threads metadata are unavailable: logged-out Instagram
   exposes no About control.

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
- Manual checker login and optional local account-file import with TOTP auto-login are supported. CAPTCHA, email/SMS verification and unresolved onboarding remain manual.
- Persist Chromium profile state in local app data. Chromium protects cookie values on Windows; the entire profile directory is not independently encrypted by this application.
- No plain-text passwords stored in source code or database.
- Session remains active across app restarts.

---

## 4. Non-Functional Requirements (NFR)

### NFR-1: Performance & Speed Benchmarks
- Original target: status 1 to 2 minutes, country/date 4 to 5 minutes per
  100 accounts. The client subsequently accepted 6 to 7 minutes for the
  country/date workflow. Neither range is a guaranteed runtime.
- Recorded Combined measurements: Round 7 afternoon **410.5s / 100 targets**;
  Round 11 near midnight **596.3s / 95 targets**. Combined does not meet the
  accepted range reliably. These historical runs used different target counts;
  they must not be described as a controlled same-list pair.
- The independent Round 11 review measured the **same 95-target list** in
  Combined **596.3s**, Smart Combined **225.2s**, and IG Status Only **62.4s**.
  Smart had zero differences in IG country/date/status and no lost country
  coverage in that comparison. The 225.2s value is one measured run, not a
  promise or a new measurement made during packaging.
- Smart skips Threads joined date and badge when IG supplies country. Status
  Only returns no country/date. These modes have different output scopes.
- Evidence: [Round 11](implementation/round11-targeted-modes-review.md),
  [Round 7](implementation/round7-benchmark100.md).

### NFR-2: Reliability & Anti-Detection
- Resource blocking (disable images, video streams, heavy stylesheets) to reduce page payload and load latency (<0.5s per navigation).
- Dynamic DOM event polling instead of fixed sleeps.
- Immediate fail-safe abort upon detecting security checkpoints or CAPTCHAs.

### NFR-3: Portability
- Single standalone PyInstaller executable with bundled Chromium.
- Known deviation from the original under-150-MB target: the 15 October 2026
  rebuild is **325,044,156 bytes** (325.0 MB decimal / 310.0 MiB).
  Installed Chromium alone is **452,900,525 bytes** (about 432 MiB, historically
  described as about 433 MB), before the Playwright driver and Python packages.
  The current full-browser bundle does not meet the 150 MB target.
- Shipping without Chromium and running `playwright install chromium` on the
  client machine would reduce the deliverable, but that alternative was rejected
  because the client needs a bare-Windows install with no Python/Playwright setup.
- Rebuilt-artifact verification: [BL-01](implementation/bl01-packaged-verification.md).
  Bare physical Windows acceptance remains pending under TSK-502.
- Compatible with Windows 10 (64-bit) and Windows 11.

---

## 5. Scope Boundaries

### In Scope
- Windows desktop GUI application.
- Multi-worker Playwright automation engine.
- Status, Country, Date Joined, and Badge extraction for Instagram and Threads.
- Cross-ban linking, TSV clipboard copying, and SQLite run history.
- Standalone `.exe` build with bundled Chromium.
- Local account-file import and authenticator TOTP auto-login.

### Out of Scope
- Mobile apps (iOS/Android) or web-hosted SaaS portal.
- Providing or supplying dummy Instagram accounts (client must supply their own checker account).
- Bypassing CAPTCHA, account suspensions or identity/security challenges. Local generation and submission of TOTP from operator-supplied authenticator secrets is implemented and in scope; email/SMS and other unsupported verification stay manual.
