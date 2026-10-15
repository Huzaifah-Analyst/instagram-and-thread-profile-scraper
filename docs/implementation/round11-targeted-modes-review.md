# Round 11 (Claude) - independent review of Codex's targeted check modes

14 October 2026. Reviewing branch `feature/targeted-check-modes`, commit
`e04d08c`, against its parent `f07fc72`. Codex reported honestly that it ran
no live benchmark, so the live measurement below is this review's own work.

## Headline: Smart Combined works, and it is the breakthrough

Same 95 accounts, same 5 workers, same machine.

| Run | Mode | Elapsed | Mean row |
| --- | --- | ---: | ---: |
| GUI, 14 Oct 00:07 | `combined` | 596.3s | 24.39s |
| CLI, 14 Oct midday | `combined` (20-target control) | 148.4s / 20 | 26.01s |
| **CLI, 14 Oct midday** | **`combined_smart`, 95 targets** | **225.2s** | **5.50s** |
| **CLI, 14 Oct midday** | **`ig_status_only`, 95 targets** | **62.4s** | **2.76s** |

Smart Combined is **2.65x faster** than the Combined run of the same list,
and 225.2s is **inside the original 300s NFR-1 target**, not merely inside
the client's accepted 6 to 7 minutes.

A tighter back-to-back control on 20 identical targets, run minutes apart so
conditions could not drift: **`combined` 148.4s, `combined_smart` 50.2s**.

## Accuracy: nothing was traded away

Smart Combined's 95 rows compared field by field against the 596.3s Combined
baseline for the same usernames:

| Check | Result |
| --- | --- |
| Usernames matched | 95 / 95 |
| `ig_country` differs | **0 accounts** |
| `ig_date_joined` differs | **0 accounts** |
| `ig_status` differs | **0 accounts** |
| Country coverage, either platform | baseline **85/95**, smart **85/95** |
| Accounts that lost a country entirely | **0** |
| Wrongly skipped (skipped without a real IG country) | **0** |

83 of 95 targets skipped Threads; the 12 that did not were exactly the ones
Instagram did not give a country for, and they fell through to Threads as
designed. This is the P78 prediction confirmed by measurement rather than
by arithmetic.

## Defects found

### D1: a deliberately skipped row is labelled `Partial`

On the 95-target smart run, `data_quality` was **Partial 89, Not available 6,
Complete 0**. The same accounts in Combined mode produce Complete rows. An
operator asked for IG country plus IG joined, received exactly that for 85
accounts, and the app reports not a single Complete row.

The cause is in `src/core/result_records.py`: a skipped platform still has a
non-None `status`, so it stays in `checked`, and `complete` then requires
country and date from a platform that was deliberately never visited.

My own instruction is partly responsible: I specified only that such a row
must not be `Failed`, and Codex's test asserts exactly that. The spec was too
weak, not the implementation careless.

### D2: every skipped row carries error text

Smart run: **89 of 95 rows have `error_message` populated**, against 3 of 20
in the Combined control. The text is "Threads skipped: Instagram already
returned a country", which is a status, not an error. It reaches the GUI's
Error column and every export, so a clean run looks like a failed one. The
same applies in `ig_status_only`, where the mode notice is attached to all 95
rows.

**This one is my instruction's fault outright**: I wrote that exact sentence
as the example value for `error_message`. The table already renders
"Skipped (IG country)" in the Threads cells, so the reason is visible without
polluting the error channel.

### D3: an account with exactly one follower is classified Unknown

`ig_status_only` agreed with the logged-in baseline on 86 of 95. All 9
disagreements were `unknown`, never a wrong verdict, so the mode never
fabricates. But the cause of 7 of those 9 is a plain bug.

`_FOLLOWERS` in `src/core/anonymous_status.py` matches only the plural:

```python
classify_status("Log In Sign Up willie 1 follower 3 following")  -> "unknown"
classify_status("Log In Sign Up x 12 followers 3 following")     -> "active"
```

Instagram renders "1 follower" in the singular. Re-fetching the 9 unknown
profiles logged out confirmed 7 of them are live pages reading "1 follower".
This client's lists are largely new accounts with 0 or 1 followers, and 0
renders as the plural "0 followers", so **exactly 1 follower is the failing
case** and it will be common.

The remaining 2 unknowns (`pa.yne432`, `lukehodges43`) render
"Profile isn't available" correctly when fetched individually, so those are a
render-deadline miss under 5-way concurrency, not a classifier fault.

My prototype had the identical plural-only bug, which is what produced its
14 unknowns in Round 10. P79's 86/100 figure is explained by it.

### D4: a pre-existing flaky real-Tk test

My full-suite run gave **259 passed, 1 failed**, against Codex's reported 260
passed. The failure is `test_output_selection.py::test_corrupt_settings_default_and_visible_message`
with "tk wasn't installed properly". It is **not a regression**: the parent
commit `f07fc72` fails the same file on *different* parametrizations, and
passed cleanly earlier in the day. A second full-suite run on this same
branch then gave **260 passed**, which settles it as flakiness rather than a
regression: repeated real-Tk root creation in one session exhausts something.
Not caused by this branch, but it will surface during a handover demo.

## Verified correct

- The skip condition reuses `country_is_disclosed`; `None`, `""`, whitespace
  and any casing of "Not shared" all still take the Threads path, covered by
  a parametrized test and confirmed live by the 12 fall-through accounts.
- `combined` remains the default and still checks both platforms.
- `ig_status_only` opens no checker, reads no checker store (the GUI test
  makes `load()` raise and the run still succeeds), applies no pacing, and
  rejects `--login` flags.
- Bounded marker polling replaced the fixed sleep, with a real Chromium test
  serving a page that is blank at 1.2s and hydrates at 1.5s.
- Unresolvable pages stay `unknown` with a reason; nothing is guessed.
- No em dash or en dash in any changed file. All changed files under 500 lines.

Codex also fixed three things beyond the brief, all correct: a latent
whitespace hole in `country_is_disclosed`, exclusion of the new skip status
from `BanLinkEngine`'s composite verdict, and two-platform preflight for
smart mode because Threads may still be needed.

## What this changes about NFR-1

Measured, same list, same machine:

| Mode | 95 accounts | Within 300s? | Within the client's 6 to 7 min? |
| --- | ---: | --- | --- |
| `combined` | 596.3s | No | No |
| **`combined_smart`** | **225.2s** | **Yes** | **Yes** |
| **`ig_status_only`** | **62.4s** | **Yes** | **Yes** |

Pacing is now the largest single component of a smart run: 114s of roughly
225s. Whether it can safely be reduced remains a ban-risk decision and is
not changed here.

## Artifacts

- Back-to-back 20-target control and both 95-target runs (local only)
- Logged-out re-fetch of the 9 unknown profiles (local only)
