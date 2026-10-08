# MetaInspector Desktop (Instagram & Threads Checker)

A high-performance Windows desktop application to verify account alive/banned status and extract transparency data (Account Country, Joined Date, Threads Badge) for bulk Instagram and Threads accounts.

---

## Key Features
- **High Throughput:** 100 accounts in 4 to 5 minutes via 5-worker parallel browser concurrency.
- **Cross-Platform Ban Linking:** If either platform is flagged as banned/suspended, both are marked as BANNED.
- **Three Modes:** Instagram Only, Threads Only, or Combined Mode.
- **1-Click Google Sheets Export:** Copies clean TSV formatted data to clipboard for immediate `Ctrl + V` pasting.
- **Run History:** Embedded SQLite database logging all past execution runs.
- **1-Time Login:** Persistent browser session storage with zero plain-text password retention.

---

## Project Documentation (`docs/`)
All architectural and development specifications are documented in the `docs/` folder:
- [PRD.md](docs/PRD.md): Product Requirements Document
- [architecture.md](docs/architecture.md): System Architecture & Concurrency Specs
- [rules.md](docs/rules.md): Git Workflow & Engineering Rules
- [design.md](docs/design.md): UI/UX Theme, Colors & Component Layout
- [tasks.md](docs/tasks.md): 15-Day Milestone Breakdown & Granular Sprints
- [memory.md](docs/memory.md): Project Memory, Client Log & Issue History
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
