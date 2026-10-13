# Round 8 task 3 — stable partial-dialog polling

13 October 2026. `_poll_dialog` now returns a populated target-matching panel
after four consecutive unchanged polling intervals (approximately one second).
It counts once per cycle, regardless of overlapping selectors, and resets
the stability counter when text changes or no matching populated panel is
seen. Complete date-plus-country panels still return immediately. Empty or
changing panels retain the existing deadline.

No page-ready, dialog, menu timeout, pacing constant or worker count changed.
The basis is the repeated identical live text documented in
[Round 5](round5-threads-country-absent.md). Increasing timeouts would make
that case slower; reducing pacing or raising concurrency was explicitly
excluded by the directive.

Real Chromium regressions use isolated local HTML: stable date-only content
returns in under four seconds with a ten-second budget; duplicate selectors
cannot prematurely advance the counter. A changing panel adds country after
1.6 seconds and the late value is retained. Existing delayed-country tests
remain intact. This is a stability heuristic: a panel that remains unchanged
for a full second and only later adds a field could still return early;
these tests do not prove all future platform hydration behavior.

## Paired live measurement

Only checker_5, five workers, default 4–8s pacing, debug captures enabled,
same twelve unique targets in the same order. Eleven were Round 7's
country-absent Threads cases; the twelfth was a comparison target. This is
an intentionally targeted sample, not a representative 100-target projection.
Runs were sequential and did not overlap browser tests.

| Measurement | Before | After |
| --- | ---: | ---: |
| Elapsed | 156.9s | 213.6s |
| Records / unique | 12 / 12 | 12 / 12 |
| IG complete stage | 9 | 3 |
| Threads complete stage | 9 | 6 |
| Data quality Failed | 3 | 6 |

**No live speed improvement established.** The after run was slower and had
more failures. Its saved records include nine identity-stage failures across
platforms and a Threads `ERR_TIMED_OUT` navigation error; logs also show
navigation timeouts. The before run already had three IG navigation failures
and three Threads dialog failures. The optimization cannot repair these
earlier navigation/identity failures. Their underlying cause was not isolated
in this round; network timing errors are evidence, not proof of one root cause.

Successful date-only panels used the new early exit, but this mixed-outcome
pair does not support claiming the projected 15-second full-batch saving.
Aggregate evidence: `evidence/round8-small-before.json` and
`evidence/round8-small-after.json`. Raw outputs and captures remain local in
`debug/round8-small-before.txt` and `debug/round8-small-after.txt`.
