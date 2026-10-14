# SP-02: anonymous Instagram status only

14 October 2026. Added `ig_status_only`, labelled
"IG Status Only (no login, fastest)" in the GUI. "Fastest" is the requested
label, not a new measured performance claim.

This mode dispatches through `core/anonymous_status.py`, using
`chromium.launch()` and a fresh `browser.new_context()` with no storage state,
cookies or persistent profile. It does not load checker settings in the CLI
or GUI factory, run checker preflight, assign checker IDs, or sleep between
targets. Pause, stop, result ordering, progress callbacks, journaling and
per-target exception records are retained. Browser and context cleanup use
finally blocks. Explicit CLI login flags are rejected in this mode so they
cannot accidentally open a persistent setup browser.

Classification uses only body-text markers:

- Profile/page unavailable or user not found: `not_found`.
- Explicit account suspension wording: `suspended`.
- A numeric follower count: `active`.
- No decision marker: `unknown`, with an explicit reason.

Unavailable and suspension wording takes precedence over follower counts.
Unsupported wording, login walls and blank pages are not guessed to be
active or not found. Navigation plus marker polling has one bounded budget,
using the existing page-ready timeout (default ten seconds); the loop polls
every 0.25 seconds instead of using a fixed 1.2-second sleep. Browser read
errors produce Unknown with a reason, not a fabricated target verdict.

All country and joined-date fields, plus Threads badge, remain None. The
record states that country/dates are unavailable without login and Threads
was not checked. IG suspension remains an IG observation, with no fabricated
Threads ban. Recognized status results have `data_quality="Status only"`;
an inconclusive status has `data_quality="Unknown"`.

The GUI shows the mode limitation before Start, replaces the checker header
with "no login needed", and disables login setup controls while this mode is
selected. The table displays "Unavailable (status only)" for IG country/date
and "Not checked" for Threads. Underlying values remain None in saved records
and exports. History retains the mode and the complete record. The offline
analyzer distinguishes unavailable-in-mode metadata from extraction failure.

Tests include marker classification, unknown results, no fabricated metadata,
fresh-context launch boundaries, absent checker/profile access, no pacing,
exception-row completeness and stopped-batch tracking. Actual Chromium
fixtures verify a blank page that receives a follower count after 1.5 seconds
becomes Active, and a markerless login page remains Unknown at the deadline.
Actual Tk tests exercise the anonymous radio, Start, factory and availability
messages even when checker configuration access is prohibited.

The **119.4 seconds / 100 targets** and **14 blank pages at 1.2 seconds** are
from P79's earlier prototype, not measured in this implementation. No live
anonymous benchmark, language-coverage audit or public-profile accuracy run
was performed here. The deadline bounds waiting; it cannot guarantee Meta
will provide a marker within that deadline.

Rejected reusing the persistent checker pool because it would violate the
no-login contract. Rejected treating any nonempty page as active or simply
lengthening the fixed sleep, because both would preserve the guessing/timing
defect. Logged-out country/date extraction was deliberately not attempted.
