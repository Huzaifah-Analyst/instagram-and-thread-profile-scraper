# SP-01: Smart Combined

14 October 2026. Branch `feature/targeted-check-modes`, created from
`feature/output-selection-and-export` at `f07fc72`.

Added `combined_smart` to the CLI and the GUI radio list, labelled
"Smart Combined (skip Threads when IG gives country)". Existing `combined`
remains the default. The GUI forwards the selected value unchanged to the
production scraper. Smart mode verifies both checker platforms at preflight,
because some targets may still require Threads. It retains existing pacing,
worker limits and session-challenge handling.

Per target, the existing Instagram extractor runs first. The existing
`country_is_disclosed()` helper decides whether to skip Threads. Its empty
value check now also rejects whitespace-only strings. No duplicate country
definition was added. None, empty, whitespace and case-insensitive
"Not shared" all take the normal Threads path. An IG extractor exception
also leaves the Threads fallback available; a checker challenge still stops
the run as before.

A deliberate skip records `threads_status="skipped_ig_sufficient"`,
`threads_stage="skipped"`, and None for all Threads country/date/badge values.
After the [review fixes](round12-review-fixes.md), the skip reason stays in
the status, stage and table cells; it does not populate the error channel.
A skipped row with a real IG country and joined date is Complete unless
there is a genuine error. The table explains the skipped cells, and the offline
analyzer counts them as not checked. No IG value is copied into Threads.

Moved record construction to `core/result_records.py`, retaining its import
through `core.scraper` for existing callers. Shared mode identifiers live in
`core/modes.py`. This keeps files below the 500-line limit and avoids circular
imports with the independent anonymous runner.

Tests verify real-country skipping, all three missing/withheld cases,
case/whitespace handling, empty skipped fields, non-failure quality,
fallback after an IG exception, unchanged default Combined behavior,
two-platform preflight, CLI mode forwarding and actual Tk radio/Start/factory
forwarding. Existing tests were retained.

The Round 10 document estimates roughly 49 of 53 live Threads profiles
skippable and about 164 seconds removed from a saved 95-target run. Those
are **document-derived projections**, not measurements from this implementation.
No fresh live Smart Combined benchmark or full-list accuracy comparison was
run in this task. Neither that saving nor an under-five-minute result is
claimed. Threads joined date and badge are intentionally unavailable for
skipped targets.

Rejected changing Combined itself because that would silently reduce data
collection. Rejected copying IG metadata into Threads because it would
fabricate a platform-specific result.
