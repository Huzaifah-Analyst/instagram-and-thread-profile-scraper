# MetaInspector Desktop (Instagram & Threads Checker)

A high-performance Windows desktop application to verify account alive/banned status and extract transparency data (Account Country, Joined Date, Threads Badge) for bulk Instagram and Threads accounts.

---

## Current branch capabilities

- Instagram Only, Threads Only and Combined lookups.
- Five independent saved checker profiles, one active worker per profile, with
  per-platform login preflight and a shared target queue.
- Target identity checks, separate account status and extraction quality,
  checker attribution, full row details and opt-in local debug captures.
- Immediate JSONL result retention in `results/`; passwords/2FA are entered in
  official browser tabs, not stored in application configuration.

One authenticated Combined extraction has been verified against raw dialogs;
a later run failed during page/menu loading. Reliable five-account scaling and
the **100 accounts under five minutes** benchmark are not yet verified.
Current findings are tracked in [the problem log](docs/problem_log.md). Clipboard/Google
Sheets export and a SQLite history viewer are not implemented on this branch.

## Run and set up accounts

```powershell
python main.py
```

Restart an older running app to load these changes. Open **Setup Checker Account**,
log into both Instagram and Threads for each slot, close each login browser,
select the slots and save. The **Checker limit** caps concurrent slots.
See [step-by-step verification](docs/manual_verification.md) and the
[actual test outcomes](docs/test_log.md). The old packaged executable has not
been rebuilt with these changes.

---

## Project Documentation (`docs/`)
All architectural and development specifications are documented in the `docs/` folder:
- [PRD.md](docs/PRD.md): Product Requirements Document
- [architecture.md](docs/architecture.md): System Architecture & Concurrency Specs
- [rules.md](docs/rules.md): Git Workflow & Engineering Rules
- [design.md](docs/design.md): UI/UX Theme, Colors & Component Layout
- [tasks.md](docs/tasks.md): 15-Day Milestone Breakdown & Granular Sprints
- [memory.md](docs/memory.md): Project Memory, Client Log & Issue History
- [problem_log.md](docs/problem_log.md): Central problem inventory, evidence, corrections, and next actions
- [team_roles_and_workflow.md](docs/team_roles_and_workflow.md): Team Roles & Collaboration Workflow
- [ISSUE_concurrent_session_detection.md](docs/ISSUE_concurrent_session_detection.md): Open issue, live testing risk, read before Sprint 4

---

## Getting Started for Developers
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```
2. Read the collaboration rules in [docs/rules.md](docs/rules.md).
3. Check your assigned tasks in [docs/tasks.md](docs/tasks.md).
