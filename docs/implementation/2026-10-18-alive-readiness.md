# Alive readiness follow-up and performance limits

Date: **18 October 2026**, Asia/Karachi. Continues the work started on
17 October. Branch: `feature/selectable-checks-and-exports`.

**The retained Alive flow returned 95 targets in 130.968 seconds with zero
error rows. The requested 120-second ceiling is not met. Later experiments
also had timeouts, so neither consistent two-minute completion nor universal
zero-error operation is claimed.**

## Retained changes

- Public-first IG/Threads status checks and selective saved-login verification
  remain as implemented in `dd81f9a`. Public requests do not use account pacing;
  saved verification retains its 4-8 second worker cooldown. Country and Age
  requests still use the existing logged-in metadata flow.
- Public Threads and logged-in Alive-only extraction can begin polling when
  a new document commits. A matching visible profile, explicit missing-page
  text or a checker challenge can settle the status without waiting for
  unrelated deferred scripts to finish. Missing evidence remains Unknown.
- Metadata/legacy Combined navigation still waits for DOMContentLoaded.
  The new option is passed only for `requested_fields=()`, never implicitly
  to country/date requests.
- A status-only navigation timeout is propagated as a read failure. It does
  not read a previous target's remaining DOM and reuse that target's 404 text.
  This final guard was added after the live comparisons and is covered by a
  regression. The 130.968-second run had no navigation timeout log entries;
  no fresh 95-target run after this guard is claimed.
- The later immediate-per-platform verification scheduler was not promoted.
  The retained scheduler is the independently queued public/saved-login
  implementation that produced the successful 130.968-second run.

Playwright documents that navigation at `commit` returns when the new document
begins loading. It does not prove that a profile is ready, so the existing
bounded visible-evidence polling and identity checks remain necessary.
[Official navigation semantics](https://playwright.dev/python/docs/api/class-page#page-goto).

## Every additional live comparison

All rows below are actual 95-target runs performed during this continuation,
not projections or test-suite durations. Same target set, five workers and
default saved-login pacing. Browser tests and packaging did not run alongside
the benchmarks. These are sequential individual runs, not a controlled
average; the change alone cannot be assigned every timing difference.

| Configuration | Seconds | Error rows / Threads Unknown | Delivery decision |
| --- | ---: | ---: | --- |
| Prior independent queues | 137.969 | 0 / 0 | Earlier successful reference |
| Resource blocker disabled | 242.531 | 7 / 7 | Rejected; selective blocker stays on |
| Early decision on public Threads only | 178.641 | 2 / 2 | Intermediate; insufficient by itself |
| Early decision on public and saved Alive pages | **130.968** | **0 / 0** | Retained, with final timeout guard |
| Immediate per-platform verification experiment | 333.094 | 9 / 9 | Not promoted; previous scheduler restored |

The last experiment logged navigation timeouts while waiting for `commit`,
including requests that did not yield a new document within 30 seconds. That
is evidence of a navigation delay, not proof that selectors, the network,
Meta throttling or CPU load caused it. No root cause among those is claimed.
The rejected experiment and its failures remain in the evidence.

The retained-flow run had:

- 95 returned, 95 unique, exact target-set equality, no omitted targets or
  stop reason. IG: 85 Active / 10 Not found. Threads: 48 Active / 47 Not found.
- All IG statuses resolved publicly. Threads resolved 48 publicly and 47
  through the enabled saved `checker_1`. No new login or other checker opened.
- Zero status differences from the user's saved run across both platforms.
  This is comparison evidence, not independent manual inspection of all pages.
- All rows Status only, with no country/date values fabricated. The run took
  **10.968 seconds more than 120**. The prior user run's 300.060 seconds is
  historical, not a new baseline measured in this continuation.

Evidence: [retained flow](evidence/alive-public95-ready-summary.json),
[public-only early decision](evidence/alive-public95-early-status-summary.json),
[rejected scheduler](evidence/alive-public95-final-summary.json),
[rejected resource setting](evidence/alive-public95-unfiltered-summary.json).
The word `final` in the rejected experiment's filename is its original script
label, not its delivery disposition. Raw target rows remain local and ignored.

## Verification and delivery

Real Chromium tests hold a deferred script open while active, missing-account
and checker-challenge results are read. Both IG and Threads preserve those
distinctions. A separate timeout regression proves the previous page is never
read after failed status navigation. Existing selected-field tests assert
that only Alive calls select this earlier readiness path.

- Public decision tests: 21 passed in 5.15s.
- Retained readiness target set: 112 passed in 16.93s.
- Experimental scheduling target set: 113 passed in 13.98s; the experimental
  queue code/test remain local for review and are not part of delivery.
- Final full suite: **479 passed in 117.33s, zero skips**. This includes the
  final navigation-timeout guard. [Saved output](evidence/alive-ready-full.txt).
- Actual source GUI replay of the retained run verified 95 rows and 190
  platform-status cells with **zero mismatches**. The displayed totals were
  IG 85 Active / 10 Not found and Threads 48 Active / 47 Not found.
  Replay made no fresh network requests.
  [Replay checks](evidence/alive-ready-replay.json),
  [anonymized screenshot](images/alive-ready-2026-10-18.png).

The final EXE was rebuilt at `dist/alive-fast/MetaInspectorDesktop.exe`:
325,082,844 bytes, SHA256
`aa13b1953f217a140cb726db3b99e3e1bc3182d3b1b4e350a231611a681f6c62`.
PyInstaller reported successful completion at 180.581 seconds. This rebuild
started successfully with isolated app data and its actual GUI rendered the
six matching check/result columns. The earlier artifact's Windows Application
Control rejection was not reproduced; no policy change or workaround was used.
[Build/startup evidence](evidence/alive-ready-build.json),
[packaged window](images/alive-ready-exe-2026-10-18.png).

During the preview, two runs were initiated outside the verification harness.
Their local journals show one public-first 95-row run with IG 85 Active /
10 Not found and Threads 48 Active / 47 Unknown; it had no saved login in that
isolated folder. A metadata Combined attempt returned zero rows and explicitly
reported no healthy checker. These observations are recorded separately from
the timed benchmark: they are not an agent-controlled timing or successful
packaged fallback acceptance. The test window was left open because it was
being used. No existing session was copied, replaced or deleted.

Select only **IG Alive** and **Threads Alive** to use this path; untick Country
and Age. Live Results still has separate columns for each selected check.
Copy/CSV/Excel, output choices, row filters and history remain available.

The source entry point is `python main.py`. Source and packaged app sessions
use different data directories. The benchmark explicitly used the existing
packaged profile directory; it did not copy sessions or credentials.

Packaged startup is verified; a packaged 95-target run with saved-login
fallback and clean-machine acceptance remain unverified. Country/date accuracy,
metadata Combined speed and sustained two-minute Alive acceptance were not
verified by these status-only comparisons.

No merge into dev, branch deletion or remote push is part of this update.

## User's later metadata run: Alive versus About results

The user's screenshot was checked against the completed local journal
`run_20261018_073550_195000.jsonl`. This was the user's all-six-fields Combined
run, not the timed Alive-only benchmark above. It returned 95 records with
Threads 48 Active / 47 Not found. Among the 48 active Threads profiles:

| Observed result | Count | Meaning |
| --- | ---: | --- |
| Country value read | 22 | Country and joined date extracted |
| Literal Not shared | 4 | Panel supplied that literal value; date extracted |
| Not shown by platform | 9 | Date extracted, no country value parsed |
| About unavailable | 6 | About option not found within bounded attempts |
| Panel incomplete | 7 | Requested About fields not read within attempts |

The first 20 records match the screenshot: 10 active Threads profiles, of
which 5 failed at About-menu, 4 at About-dialog, and only 1 completed its
panel (literal Not shared plus a date). Being Active verifies the profile;
it does not prove its About data was extracted.

The 13 About failures are extraction failures, not confirmed nondisclosure.
The nine `not_disclosed` cases have a date but no parsed country, which is the
current code's condition for the display label. There are no raw browser
captures for this run, so this inspection cannot independently confirm that
all nine country rows were absent rather than delayed or unparsed. It also
cannot distinguish a spinner, missing menu item, selector issue or delayed
panel for the 13 failures. No root cause or repair is claimed from labels alone.

All six selected fields use logged-in metadata navigation, panel attempts and
saved-account pacing. The Alive-only timing does not apply to this scope.
The earlier readiness change is explicitly disabled for metadata requests.
[Aggregate journal review](evidence/metadata-user-run-2026-10-18.json).
