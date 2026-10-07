# Team Roles, Responsibilities & Collaboration Workflow

## Document: `docs/team_roles_and_workflow.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)  
**Status:** Active Production Workflow  

---

## 1. Executive Summary & Team Structure

> **2026-10-07 update:** Antigravity AI has been removed from this project. Claude Code (operating directly for Huzaifah) now performs the Lead Architect, QA & Code Reviewer role described below. See the changelog in `docs/memory.md` §3 for the handover record.

This project operates on a high-velocity, three-tier collaborative model combining human leadership, autonomous AI coding, and architectural code review. This ensures rapid development while maintaining strict enterprise quality, zero security leaks, and 100% test verification.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Huzaifah (Project Owner)                        │
│          Client Relations • Requirements • Final Sign-Off             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Directives & Feedback
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Claude Code — Owner's session (Lead Architect & Reviewer)  │
│   System Specs • Code Review • Test Verification • Sprint Roadmaps     │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ PRs & Code Delivery
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│       Partner Developer + Claude Code — Partner's session (Impl.)      │
│         Autonomous Coding • Local Testing • GitHub PR Branches         │
└────────────────────────────────────────────────────────────────────────┘
```

Note: "Claude Code" appears on both tiers but as two separate, independently-run sessions with different jobs — one runs in Huzaifah's environment and does architecture/review/merge, the other runs in the Partner Developer's environment and does implementation. They never share context directly; the Owner's session is the bridge between them, same as before.

---

## 2. Detailed Roles & Responsibilities

### Role 1: Huzaifah (Project Owner & Delivery Manager)
* **Primary Scope:** Project stewardship, commercial alignment, and delivery control.
* **Core Responsibilities:**
  1. **Client Interface:** Communicates directly with the client, clarifies requirements, sets timelines (15 days), and manages scope boundaries.
  2. **Repository Ownership:** Maintains the official GitHub repository (`Huzaifah-Analyst/instagram-and-thread-profile-scraper`), manages team access, and permissions.
  3. **Directive Bridge:** Relays task prompts from the Architect to the Partner Developer and reports progress back to the client.
  4. **Commercial & Support Warranty:** Oversees the 15–20 day post-delivery warranty support period.

---

### Role 2: Claude Code — Lead Architect, QA & Code Reviewer (formerly Antigravity AI)
* **Primary Scope:** System architecture, technical documentation, quality assurance, and code review — run directly inside Huzaifah's working directory.
* **Core Responsibilities:**
  1. **System & Feature Architecture:** Designs system specifications, database schemas, concurrency models, and research reports (e.g. `PRD.md`, `architecture.md`, `API_VS_BROWSER_SCALING_FEASIBILITY.md`).
  2. **Automated Code Review:** Fetches all remote branches pushed by the partner, inspects code quality, checks PEP 8 compliance, and audits security.
  3. **Verification & Testing:** Runs automated test suites (`pytest`), validates acceptance criteria, and verifies zero-crash resilience.
  4. **Git Integration & PR Merge:** Safely merges approved feature branches into `dev`, resolves any merge conflicts, and maintains documentation logs (`tasks.md` and `memory.md`).
  5. **Sprint Directive Generation:** Formulates detailed, copy-paste ready technical prompts for the next sprint tasks.
  6. **Documentation Audit:** Keeps every doc in `docs/` consistent with the actual code and with each other; flags and corrects drift (e.g. a spec doc describing a design that was later, deliberately, implemented differently).

---

### Role 3: Partner Developer + Claude (Implementation & Coding Lead)
* **Primary Scope:** Hands-on code development, unit testing, and GitHub pull requests.
* **Core Responsibilities:**
  1. **Autonomous Development:** Uses Claude agent tools to autonomously manage environment setup, Python packages, Playwright binaries, and file creation without manual intervention.
  2. **Feature Branching:** Checks out fresh branches from `dev` for each task (e.g., `feature/sprint1-core-engine`, `feature/sprint2-desktop-gui`).
  3. **Implementation Standards:** Implements code matching architectural specifications, including error handling, typing, and docstrings.
  4. **Pre-Push Unit Testing:** Writes and runs unit tests locally to ensure 100% pass rates prior to pushing.
  5. **PR Creation:** Pushes feature branches to GitHub with Conventional Commit messages (`feat:`, `fix:`, `refactor:`).

---

## 3. The End-to-End Operational Workflow Cycle

Every feature and sprint in this project follows a strict 6-stage lifecycle:

```
[Stage 1: Architect] ──> Generates Sprint Directive Prompt with exact task specs
         │
[Stage 2: Owner]     ──> Huzaifah forwards Directive to Partner / Claude
         │
[Stage 3: Partner]   ──> Claude develops feature branch & runs local unit tests
         │
[Stage 4: GitHub]    ──> Partner pushes feature branch (`feature/*`) to remote repo
         │
[Stage 5: Architect] ──> Claude Code (Owner's session) pulls branch, runs automated QA & security audit
         │
[Stage 6: Integration]──> PR merged into `dev`, docs updated, next sprint begins!
```

### Stage 1: Sprint Directive Formulation
The Lead Architect drafts a detailed technical prompt specifying:
- Files to create/modify under `src/` and `tests/`.
- Functional and non-functional requirements.
- Acceptance criteria and automated test expectations.

### Stage 2: Prompt Dispatch
Huzaifah copies the directive and provides it to the Partner Developer's Claude agent.

### Stage 3: Autonomous Implementation & Testing
The Partner Developer's Claude executes the tasks autonomously:
- Sets up virtual environment / dependencies (`playwright`, `customtkinter`, etc.).
- Writes modular code adhering to `docs/rules.md`.
- Writes unit tests and executes `pytest` locally.

### Stage 4: Remote Push
The Partner Developer pushes the feature branch to GitHub:
```bash
git push -u origin feature/<sprint-name>
```

### Stage 5: Independent Verification & Review
The Lead Architect pulls the branch locally, executes verification:
- Runs full test suite: `pytest -v`.
- Verifies DOM locators and error handling against Meta's live behaviors.
- Audits `.gitignore` compliance (ensuring zero leaked tokens, cookies, or profile folders).

### Stage 6: Merge & Living Documentation Sync
Upon passing all checks:
- The Lead Architect merges the branch into `dev`.
- Updates `docs/tasks.md` (marks tasks as `[x]`).
- Records the merge in `docs/memory.md`.
- Generates the next Sprint Directive Prompt.

---

## 4. Git Branching & Protection Hierarchy

```
main (Production Releases - Standalone .exe builds)
  ▲
  │ (Protected Merge after full release testing)
  │
dev (Active Development & Integration)
  ▲
  │ (Squash & Merge after Architect Code Review)
  │
feature/sprint1-core-engine    [MERGED ✅]
feature/sprint2-desktop-gui    [IN PROGRESS 🔄]
feature/sprint3-sheets-export  [QUEUED ⏳]
feature/sprint4-speed-tuning   [QUEUED ⏳]
feature/sprint5-exe-packaging  [QUEUED ⏳]
```

* **`main`:** Contains only verified, production-grade code. Never committed to directly.
* **`dev`:** Shared integration branch where approved features land.
* **`feature/*`:** Isolated task branches created by the partner for specific modules.

---

## 5. Security & Credential Rules

1. **Zero Password Policy:** Passwords are never requested, stored, or committed to code.
2. **Persistent Profiles Isolated:** The `browser_profile/` folder is strictly ignored by `.gitignore`.
3. **No Target Leaks:** Client username lists (`usernames.txt`) and output data (`results/`) remain strictly local.

---

## 6. Sprint Roadmap & Current Status

| Sprint | Description | Lead | Status |
| :--- | :--- | :---: | :---: |
| **Sprint 1** | Backend Core Engine, Resource Blocker, Ban Linking, 5-Worker Scraper | Partner + Claude | **COMPLETED & MERGED ✅** (43/43 tests passed) |
| **Sprint 2** | CustomTkinter Desktop GUI, Left Panel, Live Data Table, Thread-Safe Bridge | Partner + Claude | **COMPLETED & MERGED ✅** (58/58 tests passed; squash-merged into `dev` 2026-10-07) |
| **Sprint 3** | Google Sheets TSV Clipboard Exporter & SQLite Run History Database | Partner + Claude | **DISPATCHED 📤** (directive sent 2026-10-07) |
| **Sprint 4** | 100-Account Speed Calibration (4–5 min benchmark) & Rate-Limit Stress Tests | All Team | Queued ⏳ |
| **Sprint 5** | Standalone Windows `.exe` Packaging (PyInstaller) & Client Handover | All Team | Queued ⏳ |
