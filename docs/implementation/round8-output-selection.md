# Round 8 task 2 — persistent output selector

13 October 2026. A bottom action bar offers Copy for Google Sheets, Export
CSV, Export Excel, View Run History and Select Output. Copy retains the
green toast and two-second Copied button label.

Select Output opens a modal, resizable, scrollable CTkToplevel (480x570,
minimum 400x400). It contains the requested twelve checkboxes plus IG Country
Availability and Threads Country Availability. Username is checked and
disabled. Select all, Reset to default, OK and Cancel are below the list.
The X and Cancel discard the draft. OK saves then applies; a write failure
leaves the prior selection intact and reports a status-bar error.

Default selection is the six existing Sheets columns. If every optional
column is cleared, Username and Status remain. Selection drives clipboard,
CSV, Excel and history re-export equally. The live table retains all its
columns. Checking mode still comes exclusively from the existing three
platform radios, independently of output selection.

**User clarification:** diagnostics are optional checkboxes. This supersedes
the directive's earlier requirement for mandatory diagnostic columns in
every file export. No unselected diagnostic columns are appended by the GUI.

Preferences live in `output_settings.json` beside `checkers.json`; default
location comes from `core.paths.data_root()` and the app uses its Checker's
directory (also isolating test/alternate profiles). Frozen builds therefore
use writable app data, not the bundle. JSON writes use atomic replacement.
Missing settings use defaults; corrupt/invalid/unreadable settings use
defaults with a visible status-bar warning. Preferences are git-ignored.

Rejected a second platform selector because it would conflict with the
existing radios. Rejected editing checkbox state directly in shared settings:
the popup maintains a private draft so Cancel works reliably.

Actual Tk tests operate the popup and application buttons, remove IG Country,
compare real clipboard TSV and actual CSV headers, check Excel headers,
clear optional columns, cancel a changed draft, select diagnostic columns,
reset defaults and reopen preferences in a new app instance. Corrupt settings
are tested both in the store and the visible app status message. A separate
real Tk test exercises all three existing radio modes and opens saved history.
See `tests/test_output_selection.py` and final task-4 test output.

This explicit widget description and real Tk assertions are the acceptance
evidence; no screenshot is claimed. No test opens a live checker browser.
