# Source audit and central problem log

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.

Created [docs/problem_log.md](../problem_log.md) as the requested single running
problem inventory. It consolidates old findings, new source-review risks,
local reproductions and the user's correction with stable P01–P30 IDs.

The initial browser comparison was for a different username. The subsequently
supplied exact-account screenshot matches the app's China / October 2025.
That correction is retained prominently; no unsupported claim of corrupted
country/date or a Meta decoy was turned into a parser change.

Added `audit_reproductions.py` to make findings reviewable. It statically
inventories all 57 previously tracked Python files without executing legacy
live scripts, checks pure parsing/record/display logic, and exercises actual
Chromium with synthetic local DOM. All 12 observation groups reproduced.
This characterizes existing behavior; it does not certify those behaviors as
correct. Runtime source was left unchanged because the user requested an audit
and problem log, and the exact-account discrepancy was resolved by evidence.

Alternatives rejected:

- Editing DATE_KEYS/COUNTRY_KEYS to remove repeated values: no same-account
  evidence supports that change; it would discard a confirmed matching value.
- Treating static review alone as proof of live causation: local DOM exercises
  establish capability, while the log preserves uncertainty about actual runs.
- Running all legacy scripts: they contain live browser/API actions and use a
  different profile path; an audit should not launch uncontrolled batches.
- Splitting findings across more issue documents: the user requested one
  running inventory, so problem_log.md owns issue status. This file records
  method/alternatives and test_log.md owns individual run evidence.

Validation: full suite `81 passed in 1.86s`, no skips; synthetic audit exited 0.
Outputs are in `docs/implementation/evidence/audit-*.txt`. No new Meta request
was made. Same-account live evidence was supplied by Huzaifah as screenshots.
