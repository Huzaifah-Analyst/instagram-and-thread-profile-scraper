# Round 8 task 1 — ported exports and history

13 October 2026. Base `bdb2e55`; branch `feature/output-selection-and-export`.

Ported file by file from `feature/sprint3-sheets-export`:

- `src/core/clipboard.py`, `export.py`, `records.py`, `history_db.py`.
- `src/gui/actions.py`, `components/toast.py`, `components/history_dialog.py`.
- `tests/test_exporters.py` and `tests/test_history_db.py`, unchanged.

Ported the action-bar implementation in `status_bar.py` and adapted the
current app through `output_actions.py`. Kept the current live table,
quality colouring, checker details and existing platform radios. Added only
the history table's title/set-records interfaces. Finished and stopped GUI
runs are saved to `history.db` beside checker settings; errors remain visible.

`EXPORT_COLUMNS` includes Data Quality and both Country Availability fields.
The six-column default Sheets formatter remains compatible. The user's
subsequent clarification makes diagnostics optional in the GUI selector:
GUI clipboard/CSV/Excel use exactly the selected columns. Direct exporter
callers without a selection retain the expanded diagnostic defaults.

Every output cell still passes through `safe_cell()`. CSV/TSV neutralize
formula prefixes; Excel retains sprint3's explicit string-cell type and
control-character filtering. No formula evaluation is enabled. Threads
Joined retains its existing date-plus-badge formatting; Threads Badge can
also be exported separately.

History retains the original `runs`/`run_items` schema and default API.
An additive `run_item_details` table stores the complete modern record in
the same transaction. The GUI requests `full_record=True` when reopening a
run, preserving platform statuses, seconds, quality and availability.
Old runs remain readable, with unavailable historic metadata left absent.
This avoids silently losing diagnostics on history re-export.

Rejected a branch merge because it would overwrite newer extraction/UI
work. Rejected changing the old history API/schema contract: the unchanged
ported tests exposed that incompatibility in the first test run. Retained
backward compatibility instead of weakening those tests.

Verification: the port has **11 exporter test functions / 16 collected cases**
(six parameterized formula-guard cases), plus **5 history tests**. The first
targeted run had 3 failures (two history compatibility assertions, one new
test using the wrong CTk checkbox method). Corrected implementation/test
driver; second targeted run **31 passed in 7.27s**. No old test assertion was
removed or weakened. Final suite evidence is recorded in the task-4 report.

No new packaged EXE or clean-machine installation was built in this round.
