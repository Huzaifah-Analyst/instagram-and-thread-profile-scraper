# Targeted modes review fixes (D1-D4)

14 October 2026. Branch `feature/targeted-check-modes`, parent `665f2bf`.
Read the Round 11 independent review and P81-P84 before implementation.

## Changes

- D1 / P82: Smart Combined excludes deliberately skipped Threads from required
  metadata. Real IG country plus joined date now yields Complete when there
  is no real error. A fallback with no Threads data remains incomplete.
  Combined retains its prior completeness rules and remains the default.
- D2 / P82: intentional skips and recognized anonymous statuses leave
  `error_message` None. Existing status, stage and table cells retain the
  explanation. Missing markers and browser read failures still report errors.
  Country/date/badge fields remain None when not collected. Saved historical
  records are not rewritten; these changes apply to newly produced records.
- D3 / P83: the follower marker accepts singular and plural, case-insensitively.
  Tests include 1 follower, 1 Follower, 0 followers, the supplied full page-text
  example, and 1 following. Bare labels and following counts remain Unknown.
  No deadline, concurrency, pacing or retry changes were made. The two reported
  live deadline misses remain unresolved and must not be guessed away.
- D4 / P84: output-selection tests share a session-scoped real Tk root, with
  fresh settings and widgets per case. The genuine application restart check
  runs in a separate process. Original export, clipboard, persistence, corrupt
  settings warning, cancellation, diagnostic selection and history assertions
  are retained. No test was deleted or skipped.

## Verification measured in this task

| Check | Result | Evidence |
| --- | --- | --- |
| Baseline suite | 260 passed in 77.73s | [baseline](evidence/review-fixes-before.txt) |
| Focused regressions | 58 passed in 11.76s | [focused](evidence/review-fixes-targeted.txt) |
| Initial Tk stress, module-scoped root | 17 passed, 7 setup errors in 14.52s | [part 1](evidence/review-fixes-tk-repeat.txt), [part 2](evidence/review-fixes-tk-repeat-part2.txt) |
| Final Tk stress, session-scoped root | 24 passed in 18.60s | [final stress](evidence/review-fixes-tk-repeat-final.txt) |
| Complete final suite | 278 passed in 73.10s, zero skips | [full suite](evidence/review-fixes-full.txt) |
| Combined record parity against parent | 5,184 synthetic input pairs, zero differing records | [comparison](evidence/review-fixes-combined-parity.json) |

The stress command collected `tests/test_output_selection.py` three times in
one pytest session with `--keep-duplicates`. Module-scoped reuse still created
a new interpreter for each collection; the third collection reproduced the
reported Tk initialization failure. Session-scoped reuse passed all three
collections. This establishes the tested mitigation, not the underlying Tcl
resource failure or a guarantee against every possible GUI environment fault.

New coverage checks Smart skips and fallback completeness, real error
preservation, clean GUI/CSV Error cells, singular follower matching and an
actual Playwright exception path. Existing real Chromium polling fixtures and
actual Tk export/selection tests pass in the full suite.

The parity check compared complete record dictionaries with the parent builder
across all pairs of six statuses, three country values, two joined-date values
and two error states. It made no network requests. Its synthetic scope does
not establish live extraction accuracy.

Source audit: 43 production files, largest 432 lines; no supplied credential
matches in candidate files. Changed Python files have annotations and
docstrings; added content contains no forbidden dash characters. This was
a targeted audit, not a comprehensive security review.

## Limits and delivery

No live IG/Threads navigation, login, extraction or benchmark ran in this task.
The 225.2s Smart and 596.3s Combined figures are from the independent
[Round 11 review](round11-targeted-modes-review.md), not measurements made here.
No new speed saving, all-account accuracy, fix for the two render-deadline
misses, or packaged EXE acceptance is claimed.

Changes remain on the requested feature branch. No merge into dev and no
branch deletion. Commit and remote verification are reported at delivery.
