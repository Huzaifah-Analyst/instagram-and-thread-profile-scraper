# Round 5 continuation (Claude) - Threads panels with no country row at all

13 October 2026. Branch `fix/extraction-root-cause-isolation`. Continues
Codex's Round 5 work after it hit a usage limit mid-Task-3; this is evidence
review of Codex's own captured data plus one fix and one new real-Chromium
regression test, not a new live run.

## What the evidence showed

Of the 50-account live Combined run, 6 records had `threads_stage ==
"about_dialog"` with `error_message` ending in `"not available/loaded:
country"` (date_joined present, country missing). One, `charity_3810`, has a
raw dialog-text dump at `debug/threads_charity_3810_20261013_181301_283019.txt`
written by `_write_debug_dump` -- this file contains every text `_poll_dialog`
read during the whole `dialog_timeout_s` poll loop (one entry per ~0.25s
cycle, roughly 30 entries for a 10s budget). **Every single entry is
identical**:

```
Name
Charity (@charity_3810)
Joined
October 2025 · 100M+
```

No "Based in" line ever appears, across the entire poll window. This is not
a late-hydration timing issue -- `_poll_dialog` (src/core/dialogs.py) already
keeps polling specifically to let late fields arrive, and the content here
never changed once at all. The panel is fully rendered and stable; Threads
simply did not include a country row for this account, which is a different
situation from the already-handled explicit `"Not shared"` text value (see
the Round 3 `threads-disclosure-quality.md` / P32 fix) -- here the row is
absent entirely, not present-but-withheld.

Before this fix, `src/core/extractors.py`'s `_extract()` only special-cased a
*truthy* but non-disclosed country value (`"Not shared"`); a `None` country
fell through to the generic `elif missing:` branch, which calls `_failure()`
and leaves `result["stage"]` at whatever it was before the dialog poll
(`"about_dialog"`) -- making a fully-successful-given-what-Threads-shows
extraction look, in the stage diagnostic, like the dialog step itself got
stuck or timed out.

## What changed

Added an `elif missing == ["country"]:` branch in `_extract()` that sets
`country_availability = "not_disclosed"`, an explanatory (not alarming)
`error` message, and `stage = "complete"` -- mirroring the existing `"Not
shared"` branch's shape.

**This does not change `data_quality` grading.** `build_record()` in
`src/core/scraper.py` computes `Complete`/`Partial`/`Failed` via
`country_is_disclosed(country)`, which already returns `False` for both
`None` and `"Not shared"` -- so a missing-country record was, and still is,
correctly graded `Partial` (date known, country not), consistent with the
Round 3 decision recorded in `threads-disclosure-quality.md` ("marks the row
Partial when a date is available but the country is not disclosed"). The fix
here is scoped to the `stage`/diagnostic-accuracy layer only, not the
operator-facing quality grade, which was already right.

Added `tests/test_accuracy_regressions.py::test_threads_about_with_no_country_row_is_complete_not_failed`,
a real-Chromium test (following this file's existing `page.route("**/*",
fulfill)` + synthetic-HTML pattern, not a mocked fake) that drives
`extract_threads()` through the full navigate -> identity -> menu -> About
flow against a synthetic panel with `Joined` but no `Based in` line, and
asserts `stage == "complete"`, `country_availability == "not_disclosed"`,
`country is None`.

## Why this method, and what else was considered

- **Reusing the existing `country_availability` field and "Not shared"
  pattern**, rather than inventing a new result shape, keeps the two
  "we resolved the country field, it's just not shown" cases (explicit
  "Not shared" text vs. no row at all) consistent and easy to tell apart
  later (`"not_shared"` vs `"not_disclosed"`), without conflating them into
  one label that would lose the distinction entirely.
- **Not changing `build_record`'s quality grading**: it was already correct
  for this case (`Partial`, not `Failed`). Changing it would have been
  fixing something that wasn't broken, based on a wrong initial assumption
  this report corrected after reading the actual code path.
- **Not assuming this applies identically to Instagram**: the live evidence
  is Threads-specific (`charity_3810`'s IG side was not examined for this
  pattern). The shared `_extract()` function naturally applies the same
  branch to both platforms, but no IG-specific evidence was gathered here,
  so no IG-only claim is made.
- **Rejected: lengthening the poll timeout for this case.** The evidence
  already shows the content was stable for the *entire* existing budget;
  polling longer would not produce a country value that Threads never
  sends, and would only slow down every account that genuinely has no
  country row.

## Verification

Real-Chromium regression test passes. Full suite after this fix plus the
related P57 fix (`round5-threads-404.md`): **189 passed**, zero skips.

Checked all 6 `about_dialog`-stage records from the run, not just
`charity_3810`: 5 of 6 (`charity_3810`, `ha.rdacre48`, `ke_nya6824`,
`nolanesyg`, `thomasrussell1017`) have a raw dump showing the identical
"Name / Joined / <date> · 100M+, no Based in line" pattern -- this fix
covers all 5. The 6th, `me_redith6621`, was missing **both** date_joined and
country (not country alone), so it correctly still falls through to the
generic failure branch unchanged -- that one is a genuine failure, not this
pattern, and was not touched.

One observation worth recording without over-claiming it: all 5 of these
accounts also show the same "October 2025" join date and "100M+" badge --
consistent with this round's test-username list (`pa.yne432`, `ha.rdacre48`,
etc. look like bulk-generated placeholder accounts) having actually been
created in bulk around the same real date, rather than the "October 2025"
pattern first flagged back in `docs/memory.md` section 6.1 being a parsing
or decoy-data problem. This is a plausible explanation, not a confirmed one
-- no evidence here establishes when these specific target accounts were
actually created outside of what Threads itself reports.

**Not verified**: a fresh live run confirming `threads_stage` now reports
`"complete"` rather than `"about_dialog"` for these accounts going forward.
