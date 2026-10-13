# Round 6 (Claude) - Threads menu/panel intermittent rendering, live-confirmed fixes

13 October 2026. Branch `fix/extraction-root-cause-isolation`. Following
Huzaifah's explicit process for this round: list errors -> find root cause ->
plan -> implement -> document, for a small live confirmation batch of P57/P58.

## Step 1: list the errors (12-target live Combined batch)

`python -m src.core.scraper --file debug/round6_confirm_targets.txt --mode combined --workers 5 --checkers 5 --debug-dump`,
checker_5 only, 63.1s total for 12 targets.

- 6 targets correctly returned `NOT_FOUND` for Threads (P57 working live).
- 4 targets (`charity_3810`, `ha.rdacre48`, `ke_nya6824`, `nolanesyg`):
  Threads `about_dialog` stage, error "not available/loaded: date_joined,
  country" -- **both** fields missing, not the country-only pattern P58
  already handles.
- 2 targets (`thomasrussell1017`, `brenda_1074`): Threads `about_menu` stage,
  error "About option not found".

## Step 2: find the root cause

For the 4 "both fields missing" targets: their `about_clicked` debug
capture (taken right after `_click_menu_item` reported success) shows the
plain profile page with **no About panel content at all** -- not a parsing
problem, the panel simply never appeared on screen for `_poll_dialog` to
read, despite `_click_menu_item` reporting that it successfully clicked
"About this profile".

For the 2 "option not found" targets: `_click_menu_item` times out because
the text was never found *within budget* -- but their **final-state**
capture (`capture_page(..., result["stage"])` in the `finally` block, taken
*after* the full `menu_click_timeout_s` had already elapsed, since
`result["stage"]` never advanced past `"about_menu"`) shows the full menu,
including "About this profile", fully rendered. The content arrived, just
too late for the poll window that was actively checking for it.

Both point to the same underlying thing: **Threads' menu and About panel
sometimes take longer to render than usual**, independent of which account
or which selector. This is not a selector bug -- the exact same code path
(`_options`, `_click_menu_item`, `_poll_dialog`) succeeded for 2 of these 6
exact accounts in Round 5's 50-account run, and for other accounts in this
same 12-account run. It is intermittent rendering latency, not a
deterministic defect.

## Step 3: plan

Raising the timeout budgets further was rejected: Round 5 already raised
them once based on evidence, and the failures here happened *within* an
8-second menu-click budget that had already found the target text was
eventually going to render (just not in time) -- a longer timeout helps,
but so does simply trying again, and a bounded retry costs nothing on the
common case (first attempt usually works) while giving a flaky render a
second chance, which better matches "intermittent" than "too short."

Rejected alternatives:
- **Just raise `menu_click_timeout_s`/`dialog_timeout_s` again**: would
  slow down every account, including the ones that already succeed
  instantly, to accommodate a minority that are flaky -- directly works
  against NFR-1's speed target for no benefit to the already-working
  majority.
- **Retry only Threads, not Instagram**: this round's evidence is
  Threads-only, but the retry only activates on a fully-empty result, which
  costs nothing extra when the first attempt already works (the overwhelming
  common case for IG in every round so far) -- scoping it to both platforms
  is simpler and has no observed downside.
- **Unlimited retries**: rejected as unbounded risk to total run time;
  exactly one retry was chosen as the minimum that could plausibly help an
  intermittent issue without materially risking NFR-1.

## Step 4: implement

`src/core/extractors.py`'s `_extract()`: the menu-open -> About-click ->
dialog-poll sequence is now a loop of up to 2 attempts. It retries (with an
`Escape` dismiss in between) when:
- the menu button itself isn't found, or
- `_click_menu_item` can't find/click the About option in time, or
- the dialog poll returns neither `date_joined` nor `country` at all.

It does **not** retry when country alone is missing (P58's already-correct
"complete, not disclosed" case) or when a definite negative is reached
(not-found page, session challenge, private account) -- only on a fully
empty, ambiguous outcome.

New test: `tests/test_accuracy_regressions.py::test_threads_retries_once_when_menu_renders_empty_first_try`,
a real-Chromium test where the first menu-button click opens an empty menu
and the second opens the real one with "About this profile" -- confirms the
retry actually recovers a result instead of failing after one flaky attempt.

Full suite after this change: **190 passed**, zero skips.

## Step 5: document (this file) and live-reconfirm

Re-ran the same 6 affected targets, Threads-only, workers=5, checker_5
(`debug/round6_retry_confirm_targets.txt`): **27.9s total for 6 targets**,
**all 6 succeeded on the first attempt** -- 5 with `country_availability=
"not_disclosed"` (P58 confirmed live, not just by unit test) and 1
(`brenda_1074`) with the literal `"Not shared"` value (the pre-existing
correct handling). No retry was actually exercised in this confirmation
run, since every first attempt worked.

**Honest open question**: this run was Threads-only, not Combined, and
used fewer targets than the failing run. It's plausible the earlier
failures were made more likely by 5-page concurrent Combined-mode load
(IG and Threads both running across 5 pages at once) rather than being a
pure, load-independent Threads flakiness rate -- but no controlled
Combined-vs-Threads-only A/B test was run to confirm this specifically, so
it remains a plausible explanation, not a proven one. The retry mechanism
itself has only been confirmed to work correctly via the synthetic
regression test, not by observing it actually fire and recover a real
live failure (because none of the 6 recheck targets needed it this time).

## What's still open

- The retry's real-world recovery rate (how often it actually fires and
  helps, versus the first attempt just usually working anyway) is unmeasured.
- Whether the earlier failures were concurrency-related or pure Threads-side
  flakiness is unconfirmed.
- The 100-account, 5-minute NFR-1 benchmark is still not attempted.
