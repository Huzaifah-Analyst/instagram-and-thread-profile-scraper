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
| *Pending* | #2 | Dev 2 | `feature/desktop-gui` | Dev 1 | CustomTkinter interface, live table, and mode selectors. |
| *Pending* | #3 | Dev 2 | `feature/sheets-exporter` | Dev 1 | TSV clipboard formatter and Google Sheets copy button. |
| *Pending* | #4 | Dev 1 | `feature/history-db` | Dev 2 | SQLite database and history viewer dialog. |

---

## 4. Known Quirks & Operational Gotchas

1. **Threads Inactive Profiles:** Inactive Threads profiles with zero posts often do not display the "About this profile" button. The parser must detect this and gracefully set `threads_country = N/A` without timing out.
2. **Threads Badge Parsing:** The Threads join string typically contains both date and badge separated by a dot (e.g. `September 2026 · 100M+`). The parser splits this on `·` into `threads_date_joined` and `threads_join_badge`.
3. **Modal Dismissal:** Always send `Escape` keypress twice after modal reading to ensure the backdrop overlay is dismissed before navigating to the next profile.
