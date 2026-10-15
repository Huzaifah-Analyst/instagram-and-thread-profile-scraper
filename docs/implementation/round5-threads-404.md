# Round 5 continuation (Claude) - Threads' real 404 page was unrecognized

13 October 2026. Branch `fix/extraction-root-cause-isolation`. Continues
Codex's Round 5 work after it hit a usage limit mid-Task-3; this is evidence
review of Codex's own captured data, not a new live run.

## What the evidence showed

Codex's 50-account live Combined run (`debug/round5-t3-combined50.json`)
recorded `threads_stage == "identity"` for 24 of 50 records -- the single
largest failure bucket in that run. Each of those failures has a matching
debug capture at `debug/threads_<username>_identity_*.txt` (written by
`diagnostics.capture_page` right when `profile_matches()` returns `False`).

Sampling all 24 of those `.txt` files from the run's exact time window
(13:12-13:16) found the **same body text in every one**, for example
`debug/threads_lukehodges43_identity_20261013_131222_261285.txt`:

```
Not all who wander are lost, but this page is
The link's not working or the page is gone. Go back to keep exploring.
Back
© 2026
Threads Terms
Privacy Policy
Cookies Policy
```

This is Threads' own "this page doesn't exist" wording -- distinct from
Instagram's ("Sorry, this page isn't available") and from the Turkish
variants already in `NOT_FOUND_MARKERS` (`src/core/about_parser.py`). It was
not in the marker list, so `is_not_found_page()` returned `False`, the code
fell through to the identity-verification stage, and (correctly, since
there's no real profile to verify) `profile_matches()` failed. The result
was a generic "profile identity could not be verified" error -- which reads
like a bug in identity matching -- instead of the accurate `NOT_FOUND`
status, which is normal, expected FR-2 behaviour (not every Instagram
account has a Threads profile).

## What changed

Added `"the link's not working or the page is gone"` to `NOT_FOUND_MARKERS`.
It is distinctive enough (a full sentence fragment) that a false positive
against real profile content is implausible.

Added `tests/test_core_helpers.py::test_threads_not_found_wording_is_recognized`
using the exact captured text above as the fixture, so this specific wording
can never silently regress.

## Why this method, and what else was considered

- **Matching on the full distinctive phrase, not a shorter substring**: a
  shorter fragment like "page is gone" risks false-matching real post/bio
  text; the chosen phrase is long and specific enough not to.
- **Not re-deriving this from Instagram's marker list**: Instagram's and
  Threads' 404 copy are written independently by Meta and already diverge
  (confirmed by this exact evidence) -- treating them as a single shared
  list already existed as the design (`NOT_FOUND_MARKERS` serves both
  platforms) and this fix stays consistent with that, it just adds the
  missing Threads-specific entry rather than inventing a parallel list.
- **Not touching `profile_matches()` or the identity-verification logic
  itself**: the identity check behaved correctly given what it was handed
  (a 404 page correctly has no matching identity). The defect was upstream,
  in page classification, not in identity matching.
- **Rejected: guessing a fix without reading the raw evidence.** The error
  message alone ("profile identity could not be verified") does not
  distinguish "this account doesn't exist on Threads" from "the page loaded
  slowly" from "the identity selector is wrong" -- only the raw captured
  text settled which one this actually was, for all 24 samples, not a guess
  extrapolated from one.

## Verification

All 24 identity-stage `.txt` captures in the run's time window were read and
matched this exact text; none showed a different pattern. `tests/test_core_helpers.py`
regression passes. Full suite after this fix plus the related P58 fix (see
`round5-threads-country-absent.md`): **189 passed**, zero skips.

**Not verified**: a fresh live run confirming these 24 (or most of them) now
report `NOT_FOUND` instead of an identity error. This fix is evidence-backed
but unit-tested only at the time of this report; the next live batch should
confirm the Threads `NOT_FOUND` count rises and the identity-failure count
drops accordingly.
