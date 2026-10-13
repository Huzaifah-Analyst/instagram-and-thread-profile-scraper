# MetaInspector central problem log

Updated: 2026-10-13. Branch: `fix/resilience-and-root-cause`.
This is the single running inventory of problems. Confirmed observations,
reproduced code defects and unverified hypotheses are distinguished explicitly.
Test executions remain in [test_log.md](test_log.md).

## Current implementation status

**Round 3 supersedes the historical status bullets below.** Full suite:
**172 passed in 29.19s**, zero skips (latest follow-up). Partial checker health, independent platform
exceptions and claimed-target error retention are regression-tested. Live setup
attempted all five: **IG 1/5, Threads 0/5, both-platform 0/5**. Checker_2 has an
actual suspension notice; checker_4/5 Threads home returns an error screen after
onboarding redirects. No healthy Combined session exists, so the 100-target
benchmark remains unrun. See [Round 3 report](implementation/round3-report.md).

The user authorized categorized implementation and manual verification where
needed. The historical audit descriptions below are retained as evidence, with
updated states. Reports: [checker pool](implementation/isolated-checker-pool.md),
[extraction/session](implementation/transparency-and-session-hardening.md),
[results/storage](implementation/result-evidence-and-stable-storage.md).
[Run and verify](manual_verification.md).

- Five independent profile slots and a shared target queue are implemented.
  Five simulated sessions processed 21 targets exactly once. Five live account
  sessions have not yet been validated together.
- Threads' observed failure was an actual login wall, misreported as an About
  menu failure. New preflight identified it correctly before target assignment
  (23.2s Combined startup). The user later confirmed both official logins complete.
- After the user completed both logins, one Combined run succeeded in reading
  both About panels: 17.1s total / 8.36s row. IG raw text: China / October 2025;
  Threads raw text: October 2025 / 100M+ / Not shared. Both screenshots were
  inspected. This confirms transcription for this account, not the whole batch.
- Fixed a newly observed quality defect: Not shared is retained literally but
  no longer counts as a disclosed country or Complete data (P32).
- The next live recheck was unstable: 62.0s total / 43.41s row; IG menu absent,
  Threads screenshot still on the logo/loading screen. Both fields remain empty
  and the result is Failed. Post-fix successful live disclosure classification
  has not been observed; the exact captured structure passes its regression.
- Controlled 10-target batch launches were blocked twice by automatic
  permission-review timeouts; the batch did not execute. Five-account live
  operation and the 100-account performance requirement remain unverified.
- Account-file automatic setup is implemented; see [report](implementation/account-file-auto-login.md).
  This adds local authenticator codes and stable per-username sessions. Live
  acceptance is tracked separately; importing five rows does not prove five logins.
- First imported account passed live Instagram auto-login after a current-form
  selector fix (P35). Threads remained unverified after its authenticator step;
  setup stopped before the other four accounts (P36).
- The current authenticator screen's Code control now has label/ARIA/modern-name
  fallbacks and scoped submission (P37). A bounded IG-to-Threads return is also
  implemented; fresh live acceptance of this follow-up remains pending.
- **Latest full suite: 159 passed in 35.94s, zero skips**, outside the sandbox.
  This includes real Tk widgets and real local Chromium DOM tests. Earlier Tcl
  environment failures and approval timeouts remain in the running test log.

## Accuracy correction and scope

- User reported wrong country and date; runtime-path audit completed below.
- Latest supplied browser screenshot is for **brenna1074**, showing April 2016
  and no country field. The app screenshot is for **brenda_1074**, showing
  China / October 2025, Instagram Only, one account, 3.7s row time / 4s GUI time.
  These are different usernames. Country omission is not evidence of a specific
  different country, and this pair is not a same-account accuracy comparison.
- The screenshot's Instagram dialog title is **About this profile**, whereas
  current production IG menu text only accepts About this account / Turkish.
  A synthetic menu using that wording is not matched. A dialog title does NOT
  prove the menu uses the same wording on Meta; this is a compatibility risk,
  not a confirmed cause of this user's run failing.
- No claim that Meta deliberately serves fake dates is supported by current
  evidence. Repeated months alone do not establish wrong data.
- **Correction received during audit:** Huzaifah subsequently supplied the
  About dialog for the exact username **brenda_1074**. It shows **October 2025 /
  China**, matching the app screenshot. This specific alleged country/date
  discrepancy is resolved as a comparison of different usernames. It does not
  establish accuracy for every account or explain all repeated dates.

## How to read this log

- **Observed:** visible in this session's saved evidence or supplied screenshots.
- **Reproduced locally:** exercised with assertions on pure code or actual
  Chromium synthetic DOM. These are not captures of the live Meta DOM.
- **Code-review risk:** present in the implementation; production impact still
  needs a targeted reproduction/live check.
- **Resolved comparison:** evidence corrected an earlier interpretation; no
  application patch was needed.

## Problems affecting results and confidence

| ID | Priority / state | Problem and evidence | Next action |
| --- | --- | --- | --- |
| P01 | Resolved comparison | `brenna1074` and `brenda_1074` were different targets. Corrected same-account screenshot matches **China / October 2025**. Parser-to-table transcription check also matches. | Keep exact username/URL with future comparisons; do not change this date. |
| P02 | High / unresolved across batch | Repeated October dates are not proven wrong. One exact account now matches the manually opened site; earlier 27-row screenshots had 11 October and 2 November dates. No production source October literal found. | Validate additional same-account raw dialogs before claiming a systematic bug or server decoy. |
| P03 | Implemented / live preflight verified; GUI regression passes | Header Connected reflects cookie metadata only, including after a challenge. Earlier saved live screenshot was logged out despite Connected. `session.py`, `app.py::_refresh_session`. | Header now says saved IG logins; live preflight and challenge invalidation implemented. Full GUI regressions pass in normal desktop environment. |
| P04 | Fixed / login heading regression passes | Public logged-out page with Log In / Sign Up returns no session challenge. `logged_out_public_page_not_detected`. | Exact observed Threads heading and IG login/signup lines now detected; retain captured evidence for other locales. |
| P05 | Fixed / actual Chromium synthetic DOM passes | `_poll_dialog` accepts text from a **hidden** dialog before the visible correct one. Synthetic hidden October/China beat visible April/Canada. `hidden_dialog_selected_before_visible_target`. | Visible-container filtering covered by competing hidden/visible Chromium fixture; live accuracy still needs fresh comparison. |
| P06 | Fixed / identity regression passes; one live identity-bound extraction verified | First parseable dialog wins; it is not bound to target identity. Wrong-user dialog wins in local two-dialog fixture. `first_dialog_not_bound_to_target_identity`. | Host/URL/header and dialog username now checked; no values from mismatched identities. |
| P07 | Fixed / adjacent-label regression passes | Missing date value followed by country label produces `date_joined = Account based in`. No date/value validation or adjacent-label guard. `missing_value_accepts_next_label_as_date`. | Adjacent labels no longer become values; original date/country label lists retained. |
| P08 | Fixed / late-field and missing-country regressions pass | Poll returns as soon as **either** field is present. Country added later is lost, and extractors only flag error when both fields are empty. `poll_returns_on_first_field_before_later_content`. | Waits for late fields and returns partial at deadline; no guessed country. |
| P09 | Fixed / generic-error page regression passes | An unclassified generic error page becomes ACTIVE with an Options error. No positive profile identity/existence requirement. `unclassified_error_page_returns_active`. | Requires positive profile identity before ACTIVE. |
| P10 | Implemented / quality semantics pass; GUI regression passes | Green ACTIVE rows coexist with failed/missing extraction; all 27 prior rows lacked Threads data. `ban_engine.py`, `theme.py`, `data_table.py`. | Data column now separates Complete/Partial/Failed; incomplete ACTIVE rows amber. |
| P11 | Named selector implemented / synthetic DOM passes; one authenticated live extraction verified | Threads chooses the rightmost SVG within coordinate bounds. A local fixture selects an unrelated control. Prior live runs repeatedly fail to find About afterward. | Use observed More title and button ancestor. Live authenticated Threads panel read successfully once; later loading failure remains open. |
| P12 | Fixed / visible duplicate regression passes | Menu lookup examines `.last` for each exact label: a hidden last duplicate masks a visible usable button. `last_hidden_duplicate_hides_visible_menu_candidate`. | Iterates visible exact matches instead of only .last. |
| P13 | Alias supported / synthetic menu regression passes | IG ignores a synthetic About this profile menu item. The user screenshot shows that wording as the **dialog title**, not the menu item; original prototype accepts it. | Both English About aliases accepted; not claimed as proven live root cause. |
| P14 | Open live IG failure / added stage evidence and late-auth checks | IG Options missing and dialog timeouts occur live. Header presence is treated as page-ready before menu availability; challenge checks occur before menu/dialog work. | One post-login run read both About panels; subsequent run showed IG menu absent and Threads loading splash. Intermittent readiness remains open; retain captures. |
| P15 | Implemented / five-context scheduler passes; five live logins pending | Five workers share one persistent checker context. Five separate checker accounts are not implemented. Challenge causation by concurrency is not isolated. | Set up distinct official logins in five slots, then verify small batch and checker IDs. No measured live speedup yet. |
| P16 | Fixed / queue-stop and cross-platform-stop regressions pass | Global stop is checked between accounts. In-flight accounts finish and another worker can proceed from IG into Threads after a global stop. Rows appeared after BLOCKED in user run. | Stop prevents next queued target/platform; already in-flight requests may finish. |
| P17 | Implemented / early-failure capture regression passes | Debug off in user runs; enabled debug only dumps text reached during polling. Early menu/login failures have no page snapshot or stage evidence. | Opt-in screenshots/text/stage/URL include early failures, menu transitions and final state. |
| P18 | Fixed / input normalization regression passes | Username cleanup accepts full URLs and whitespace-containing strings as usernames. It does not transform a valid Instagram URL into its handle or reject invalid input. | Supported URLs normalize to handle; invalid names rejected in UI/CLI. |
| P19 | Fixed / invalid timeout regression passes | Negative poll budgets are accepted. GUI numeric conversion also admits non-finite values such as infinity; invalid textual input silently defaults. | Finite positive budgets up to 120s; no silent numeric fallback. |
| P20 | Implemented / Threads preflight rejection verified live | The GUI can start when session is disconnected. Setup opens only IG; it does not establish/test Threads login separately. | Both login tabs and requested-platform preflight added; user confirmed login; one successful Combined extraction and a later loading failure are recorded. |
| P21 | Fixed / detached click deadline regression passes | `_safe_click` gives explicit limits to two click attempts but none to locator `evaluate`. Installed Playwright docs say locating for evaluate defaults to 30,000ms. Outer polling budgets can also overrun during locator operations. | All fallback stages and whole menu-click action now bounded. |
| P22 | Fixed / independent Threads lookup regression passes | Combined mode skips Threads whenever IG is NOT_FOUND. The existence of a same-handle Threads profile is assumed, not independently checked. | Combined checks Threads even when IG NOT_FOUND; same handle does not establish same owner. |
| P23 | Implemented / journal persistence passes; GUI selection/table regression passes | Error cell truncates at 200 characters and has no detailed-row viewer. GUI records exist in memory; this branch has no run-history/export implementation to retain them automatically. | Double-click full details; immediate JSONL row retention; history/export UI still not implemented. |

## Packaging, documentation and maintenance problems

| ID | State | Finding / next action |
| --- | --- | --- |
| P24 | Stable paths implemented / unit passes; packaged restart pending | Central paths use project root in source, LOCALAPPDATA in frozen mode. Release restart test remains required. |
| P25 | Code-review risk | Packaging selects the lexicographically last cached `chromium-*`, not the revision required by the installed Playwright driver. Dependencies use open-ended lower bounds. Resolve the required revision and pin a tested dependency set. |
| P26 | Documentation corrected / performance and absent features explicit | README now describes this branch; no validated NFR-1 claim, clipboard or SQLite-history claim. |
| P27 | Existing measured finding, still open | Prior packaging report measured 309.9 MB against the under-150 MB requirement; clean-machine delivery remains unverified. See memory section 5 / Sprint 5. No rebuild or size remeasurement in this audit. |
| P28 | Production split implemented / legacy scripts unchanged | Parser, browser helpers, dialogs, health/pool and diagnostics separated; validate source inventory before commit. |
| P29 | Observed workflow issue, mitigated once | Setup browser opened but was not visible to user; prior process/window check and foreground activation resolved that occurrence. No persistent foreground/focus handling was added to the app. |
| P30 | Expanded regression suite / 113 tests pass, zero skips; live stability remains open | New actual-browser DOM, pool, health, storage and GUI-widget regressions. Historical characterization script explicitly targets pre-fix commit. |

## Audit coverage and results

All **16 production Python files** (root main.py plus src/, including empty
package initializers) were reviewed/scanned across this investigation. All
**57 previously tracked Python files** were parsed for syntax, imports, date
literals, line counts and silent handlers: 16 production, 37 legacy checker
scripts, 4 test modules. The per-file inventory is in
[audit-reproductions.txt](implementation/evidence/audit-reproductions.txt).
Legacy scripts were statically scanned and relevant extraction/config paths
reviewed, not all independently executed. Their scripts can launch browsers
or call live endpoints, so they were not imported to perform this audit.

Reviewed build spec, requirements, pytest configuration, gitignore, README,
current requirements/architecture/design/rules/workflow/task/memory docs and
existing implementation reports. Historical PDFs were not re-extracted;
their prior review notes are in memory. Browser databases, passwords, email
and 2FA material, binaries and generated build trees are not source-code
audit inputs and were not examined for contents.

No production import points to `checker_test`. The runtime path is GUI input
-> scraper -> extractor -> record merge -> event queue -> table. Local
transcription test confirms country/date pass through this path's merge and
display unchanged. The resource blocker aborts assets; no value-replacement
or date/country fallback mechanism was found in production source.

The [audit script](implementation/audit_reproductions.py) ran with exit 0:
**12 observation groups reproduced**, consisting of one positive
transcription/display check and 11 failure/risk characterizations. Browser
checks used actual Chromium with synthetic HTML, a fresh temporary context
and locally fulfilled navigation. They did not contact Meta or access the
saved checker profile. Reproduction success is not a product acceptance pass.

Historical audit suite (before this implementation): **81 passed in 1.86s**, exit 0. That audit changed no application behavior.
This audit establishes actionable risks; it does not establish that hidden
dialogs caused any actual October date. The same-account user screenshot
supports the opposite conclusion for brenda_1074: its displayed values match.

## Next sequence and update convention

1. Fix evidence/identity/health handling before making accuracy or speed claims.
2. Address reproduced dialog, completeness and menu-selection defects with
   regression tests; verify actual live failures with captures.
3. Verify independent Threads login/extraction; then measure controlled scaling.
4. Validate the implemented five-checker pool with live accounts after baseline extraction succeeds.

Append new problems with stable P-IDs. Update each entry's state and link the
fix report/test evidence when resolved; retain this correction history. Keep
individual test runs in test_log.md and task-method reports under implementation/.

## Additional finding during implementation

| ID | State | Evidence and action |
| --- | --- | --- |
| P31 | Fixed and live rechecked | Initial live preflight used wait_for_function; Instagram CSP rejected string evaluation. Replaced with bounded locator text polling. Next Combined preflight completed IG and correctly detected Threads login required (23.2s). |
| P32 | Fixed / exact live-text regression passes | Threads country explicitly says Not shared. Previously counted as Complete; source text is now preserved and classified as Partial when a joined date is available. Fresh post-fix live attempt failed earlier during loading, so live classification acceptance remains pending. See [report](implementation/threads-disclosure-quality.md). |
| P33 | Implemented / automated coverage passes | Account file could not previously set up checker logins. Added full-file validation, memory-only password/seed handling, local TOTP and official-page login for IG/Threads. Manual challenges stop setup. Five-account live acceptance remains separate. See [report](implementation/account-file-auto-login.md). |
| P34 | Preventive fix / automated coverage passes | Assigning imported sessions by slot number would mix accounts after a reordered import. Profile directories now follow stable username bindings; matching identity is required during setup and extraction preflight. Existing manual profiles are preserved. |
| P35 | Fixed / live IG login verified | First automatic attempt could not find the current IG username field: `name=email`, `autocomplete=username webauthn`. Read-only control inspection pinpointed the mismatch. Added email-name and autocomplete-token selectors; next live attempt verified the first account on IG. See [report](implementation/account-file-auto-login.md). |
| P36 | Open / live Threads authentication unverified | After IG succeeded, Threads submitted one authenticator code but no matching authenticated session was verified before timeout. Fresh read-only inspection still showed a login form and no Threads session cookie. It did not show an incorrect-code marker, so rejection, extra verification, or UI progression cannot yet be distinguished. Setup halted with 0/5 dual-platform accounts verified. Complete the first account manually in Setup and reimport; do not count the other four as tested. |
| P37 | Implemented / synthetic regressions pass; live acceptance pending | User screenshot shows an empty Code field on an explicit authentication-app screen. Prior selectors lacked label/ARIA/approvals_code fallbacks, and page-wide submit selection could choose an unrelated login button. Added explicit-app-prompt field recognition and form/dialog-scoped submission. Also return to Threads once after a verified IG handoff; P36 remains open until live confirmation. See [report](implementation/authenticator-code-form.md). |

## Round 3 findings, 12 October 2026

| ID | State | Evidence and action |
| --- | --- | --- |
| P38 | Fixed / regression passes | One failed preflight or browser launch stopped all selected checkers. Three healthy plus two unhealthy now process twelve targets through only the three healthy sessions. Worker cap counts healthy workers; later slots can replace failed startup slots. [Task 1](implementation/round3-partial-checker-resilience.md). |
| P39 | Fixed / regression and live orchestration verified | Failed setup returned early or waited indefinitely for manual closure. All five accounts now attempted, with ten platform outcomes and per-platform counts. A failed account_2 regression verifies accounts 3–5 are attempted. Actual live authentication remains blocked. |
| P40 | Fixed / regression passes | Unexpected error after queue claim could lose that target and cancel siblings. Twenty targets with one ValueError now return twenty ordered records, including the ERROR row. Unstarted targets tracked separately. [Task 4](implementation/round3-missing-targets.md). |
| P41 | Fixed / regression passes | A non-session IG exception prevented the requested Threads extraction. Independent platform boundaries retain Threads data while IG is error; genuine session block still stops globally. |
| P42 | Fixed / regression passes | Journal disk failure could stop processing before UI callback. Explicit storage warning now preserves in-memory/UI results and allows processing to continue. Persistence is not claimed when storage fails. |
| P43 | Confirmed external blocker; detection fixed | checker_2 displays actual suspension dated October 9, 2026, account-integrity reason. `/accounts/suspended/` previously timed out as unknown form and could escape health classification with a cookie. Now explicit manual-review outcome; no automation-causation claim. [Task 5](implementation/round3-checker-suspension.md). |
| P44 | Confirmed live blocker; diagnosis/classification implemented | checker_4/5 reached Threads `/onboarding/`, then broken-page home on read-only follow-up. Cookie exists but identity unverified. Report incomplete setup and reject observed broken-home page. Root server cause and successful setup remain unverified. [Task 3](implementation/round3-threads-root-cause.md). |
| P45 | Observed selector mismatch fixed / synthetic Chromium passes | Current Threads accessible button text `Continue with InstagramLog in` failed old anchored selector. Exact compound variant now accepted. Successful live login after this change is not claimed. |
| P46 | Fixed by source change; full suite passes | CLI constructed default numbered profile slots rather than loading imported username-bound paths. CLI now uses CheckerStore for selected and manual-login slots; no new live CLI authentication claim. |

P15/P36 follow-up: all five live setup attempts now have evidence. Historical
checker_1 dual-platform success does not imply current health; latest IG success
is checker_5 only. P37 follow-up: sibling/late Continue fallback passed its test
and one older live attempt submitted OTP but did not verify a session. It remains
distinct from the newly observed suspension/onboarding blockers. P02/P14 remain
open across the full batch; no repeated-date or hydration hypothesis was promoted
to a proven explanation.

### Actual GUI follow-up, 13 October 2026

| ID | State | Evidence and action |
| --- | --- | --- |
| P47 | Fixed / current-card and delayed-error Chromium regressions pass | Actual checker_5 Threads login displays `Join using your Meta Account` with its saved username. Production now matches this card within an exact username scope, independent of image-alt text in its accessible name. Agent selected the actual button in the app-created browser; its concatenated textContent must not be confused with its accessible name. |
| P48 | Private authorized / live completion blocked | That continuation leads to Threads `/onboarding/` with a real Privacy Public/Private selection. This explains the current incomplete setup more precisely than the earlier broken-home page. User chose Private; the next attempts did not complete that selection or verify Threads identity. See P49. [Actual GUI follow-up](implementation/round3-live-checker-logins.md). |
| P49 | Observed live sign-in blocker / explicit reporting implemented | Saved-account continuation returned a visible Threads alert Something went wrong at /login/. IG remained identity-verified. Exact ARIA/page evidence saved; underlying reason unknown. Production reports this alert without a redundant password fallback. Private setup, Combined sample and benchmark remain unverified. [Report](implementation/threads-saved-account-card.md). |

P44 remains historically accurate for the earlier home-error capture, but
an earlier app-driven path reached a usable onboarding control; the latest attempt returned the P49 login error. No assumption
that the account is permanently unusable or that the SVG selector caused this
login failure is justified.


### Round 4 - single-account concurrency, 13 October 2026

| ID | State | Evidence and action |
| --- | --- | --- |
| P50 | Fixed / real Chromium and scheduler regression verified | With one checker and workers=5, run_pool previously opened only one worker page. It now fills spare slots with pages on healthy existing contexts. A real Chromium test requires five simultaneous targets, separate DOMs and one context; 20 results returned. Mixed-health behavior and active-challenge stop remain. [Task 2](implementation/round4-worker-concurrency.md). |
| P51 | Fixed / synthetic and actual-app flow exercised | Setup previously opened IG and Threads tabs together and deferred live health to Start. Single-selected-checker Setup now opens IG alone, waits for closure, opens Threads on the same saved profile, waits, then checks both platforms and displays each result. Optional Manage checkers retains the older multi-account UI. [Task 1](implementation/round4-sequential-login.md). |
| P52 | Resolved for checker_5 after manual onboarding / historical first attempt | User reported both manual windows completed. Post-close preflight verified IG but returned Threads broken-link page; subsequent read-only headed check showed a public feed with Log in or sign up for Threads and no verified own identity. User later clarified onboarding was incomplete; after P53 window sizing correction and manual completion, both identities verified. The authorized 95-target run then completed; see P54. [Benchmark](implementation/TSK-401-nfr1-benchmark.md). |

| P53 | Fixed / user completion and live identity verified | User clarified that Threads remained on onboarding: Continue could not be reached and scrolling did not work. Manual setup used a fixed 1280x800 viewport. It now uses no fixed viewport and starts maximized, permitting native window resizing. Tests assert these settings; user completed onboarding in the reopened checker_5 setup and live preflight verified both platforms. This changes login windows, not extraction viewport. |

| P54 | Open / measured live extraction and speed failure | 95-target Combined run returned all 95 rows in 1047.6569999999992 seconds using one verified checker context and five pages. Complete 0, Partial 14, Failed 81; all rows carry errors. Identity failures IG49/Threads60, Threads About-menu33, IG About-dialog18. Inspected captures include loading splash and menu spinner. Underlying readiness/network/server cause unproven; no five-minute acceptance. [Benchmark](implementation/TSK-401-nfr1-benchmark.md). |


### Round 5 - root-cause isolation, 13 October 2026

| ID | State | Evidence and action |
| --- | --- | --- |
| P55 | Reproduced mechanism defect / repaired / 8-target live check passed | Wildcard Playwright routing disables HTTP cache and intercepts critical requests. Five-page pass-through control failed 5/8 despite aborting zero assets, while OFF and selective blocker each completed 8/8. New real Chromium fixture proves cached script requested once, old implementation twice. Selective CDP heavy-resource interception retains default blocking without routing critical requests. This does not prove every historical failure had this single cause. [Task 1](implementation/round5-resource-blocker.md). |
| P56 | Implemented / diagnostic switch covered | Constructor resource_blocker_enabled and CLI --no-resource-blocker affect initial and additional worker pages; default remains ON. No other checker slots were opened. [Task 2](implementation/round5-concurrency.md). |


### Round 5 continuation (Claude, not Codex), 13 October 2026

Codex hit its usage limit mid-Task-3, while editing `tests/test_blocker_cache.py`,
after completing and committing nothing beyond the Task 1/2 work above (left
uncommitted on `fix/extraction-root-cause-isolation`). Huzaifah asked Claude to
continue the implementation directly until Codex's limit resets. This
continuation reviewed the actual repo state (not just the narrated log),
ran the full suite (187 passed, confirming the uncommitted work was sound),
then inspected the raw evidence from Codex's own 50-account Combined run
(`debug/round5-t3-combined50.json` plus the per-target `debug/threads_*`
captures) to find and fix two concrete causes behind the 24 Threads
"identity"-stage and 6 Threads "about_dialog"-stage records in that run.

| ID | State | Evidence and action |
| --- | --- | --- |
| P57 | Fixed / regression test passes | Threads' real "page not found" wording ("Not all who wander are lost, but this page is... The link's not working or the page is gone") was absent from NOT_FOUND_MARKERS. Sampled all 24 Threads identity-stage failures from the 50-account run (`debug/threads_*_identity_*.txt`, timestamps 13:12-13:16) — every single one showed this exact text, meaning a genuine "no Threads account" case was being misclassified as "profile identity could not be verified" instead of NOT_FOUND. Added the marker; `tests/test_core_helpers.py::test_threads_not_found_wording_is_recognized` uses the exact captured text. [Report](implementation/round5-threads-404.md). |
| P58 | Fixed / real-Chromium regression test passes | The Threads About panel sometimes renders with no "Based in" row at all (distinct from an explicit "Not shared" value) — confirmed via `debug/threads_charity_3810_*`, where the raw dialog text was captured ~30 times across the full `dialog_timeout_s` poll window with identical content each time (date_joined present, no country line), proving this is the panel's final, stable state, not a late-hydration timing issue. Previously classified as a stuck/failed `about_dialog` stage. Added a `missing == ["country"]` branch in `_extract` (`src/core/extractors.py`) that sets `country_availability="not_disclosed"` and `stage="complete"`, matching the existing "Not shared" handling. Does not change `data_quality` grading (`build_record`'s `country_is_disclosed()` already correctly scored a missing country as Partial, not Complete, before and after this fix) — this only corrects the misleading stage-level diagnostic. [Report](implementation/round5-threads-country-absent.md). |
| P59 | Open / single occurrence, not root-caused | One record (`de.ja5945`) failed with "Threads About option not found" even though the `profile_menu_open` debug capture's body text shows the menu was open and "About this profile" was visibly present in the text dump at that exact moment. `_click_menu_item` uses `get_by_text(..., exact=True)` plus a visible-candidate count that returns `None` on ambiguity — a transient multi-match or a reflow between the capture and the click is plausible but unconfirmed. One occurrence out of 50 is not enough evidence to fix without risking a wrong guess; needs another sample to investigate. |

Fresh full suite after both fixes: **189 passed**, zero skips. Checkers 1/2/3/4
were not opened; only checker_5 was used, and no new live run was started in
this continuation beyond reading already-captured evidence from Codex's run.


### Round 6 (Claude), 13 October 2026 - live confirmation batch and a new fix

Huzaifah asked for a small controlled live batch to confirm P57/P58, with an
explicit process: list errors, find root cause, plan, implement, document.

**Confirmation batch 1** (12 targets, Combined, workers=5, checker_5,
`debug/round6_confirm_targets.txt`): **63.1s total (~5.3s/target)**.

| ID | State | Evidence and action |
| --- | --- | --- |
| P60 | Confirmed live | All 6 targets known from Round 5 to have Threads' real 404 text now correctly returned `NOT_FOUND` instead of a false identity error (lukehodges43, pa.yne432, ashly.92067, squirrel.708791, ne.wman5286, mo.rrison1007). P57 confirmed working live, not just by unit test. |
| P61 | New failure pattern found / fixed, pending re-confirmation | 4 targets (charity_3810, ha.rdacre48, ke_nya6824, nolanesyg) returned Threads `about_dialog` with **both** date_joined and country missing this time (not country-only, so P58's fix correctly did not apply) -- raw evidence shows the About panel never rendered at all (`capture_page` "about_clicked" snapshot shows the plain profile page, no panel content). 2 more targets (thomasrussell1017, brenda_1074) failed with "About option not found" -- their *final-state* capture (taken after the full menu_click_timeout_s budget, since `result["stage"]` never advanced) shows the full menu **did** eventually render with "About this profile" visible, meaning the content arrived too late or the exact-text click raced it. Root cause: intermittent Threads menu/panel rendering latency, not a selector or parsing bug -- the identical selectors worked on other accounts in the same run and on these same accounts in Round 5's earlier run. Fix: one bounded retry of the whole menu-open -> About-click -> dialog-poll sequence in `_extract()` (`src/core/extractors.py`) when the first attempt returns neither date_joined nor country. New real-Chromium regression test: `test_threads_retries_once_when_menu_renders_empty_first_try`. [Report](implementation/round6-menu-retry.md). |

**Confirmation batch 2** (the same 6 P61 accounts, Threads-only, workers=5,
`debug/round6_retry_confirm_targets.txt`, run after the retry fix): **27.9s
total (~4.65s/target)**. **All 6 succeeded on the first attempt** (no retry
was even needed this time) -- 5 with `country_availability="not_disclosed"`
(P58 confirmed live), 1 (`brenda_1074`) with the literal `"Not shared"` text
(the pre-existing, already-correct handling). This suggests the earlier
failures may be more related to 5-page concurrent Combined-mode load (IG and
Threads running together across 5 pages) than to Threads alone under lighter
load -- plausible, not proven; no controlled Combined-vs-Threads-only A/B
test was run to confirm this specifically.

Full suite after the retry fix: **190 passed**, zero skips. Checkers
1/2/3/4 not opened in either confirmation batch.


### Round 7 (Claude), 13 October 2026 - the 100-account benchmark

Full report: [round7-benchmark100.md](implementation/round7-benchmark100.md).
100 unique real targets (95 supplied + 5 from the project's own existing
lists; none invented or duplicated), Combined, workers=5, checker_5 only.

| ID | State | Evidence and action |
| --- | --- | --- |
| P62 | Confirmed live at scale | P57's Threads-404 fix: all 44 Threads `NOT_FOUND` rows in the 100-target run were re-checked against their own saved page captures -- 44/44 contain Threads' real 404 text, zero misclassifications. All 7 Instagram `NOT_FOUND` rows likewise verified 7/7. In Round 5 these same pages were reported as identity-verification failures. |
| P63 | Confirmed live | P61's menu/dialog retry fired on exactly 2 targets (`damaris_9759`, `me_redith6621`, identified by their `*_2_*` captures) and **both recovered full data** (October 2025 / China). First live evidence of the retry rescuing a result, not just passing a synthetic test. Cost when it does not help: `lyricnixon292` spent 32.0s searching the menu twice -- the accepted trade-off. |
| P64 | Open / likely not code-fixable | `lyricnixon292` is the **single genuine extraction failure in the entire 100-target run** (1 of 149 platform checks against existing accounts; 99.3% success). Threads account is real and active but renders no profile "More" control across both attempts; its capture shows an empty profile (0 followers, "No threads yet"). This matches the pre-existing documented quirk in `docs/memory.md` section 4 item 1 (inactive Threads profiles often have no About control). The produced output -- active, no transparency data, reason stated -- is the honest result if the control genuinely does not exist. |
| P65 | Open / measured, decision needed from Huzaifah | **NFR-1 not met: 410.5s vs the 300s target.** A validated model explains it: work per worker 271.3s + deliberate 4-8s inter-target pacing 114.0s = 385.3s predicted vs 410.5s measured. Pacing is ~28% of wall time and exists to avoid the rate-limiting behind this project's earlier incidents (this run: **zero** blocks). Projections: 2-4s pacing ~328s (still over); 8 workers ~238s (under, but concurrent-page count is the exact variable implicated in Incident 5 and the account suspensions). Not changed silently -- this is a risk/throughput trade-off for Huzaifah to decide. |
| P66 | Hypothesis tested and **disproved**, recorded | Debug captures were expected to be a meaningful cost (499 files written during the benchmark). Measured on 15 identical full-path targets: **87.9s with captures ON vs 119.9s with captures OFF** -- captures-off was slower, so live-site run-to-run variance (±36% on this sample) dominates any capture overhead. Turning captures off is **not** a route to 300s, and ~15-target single runs cannot measure effects smaller than roughly 40%. |

**Data quality across the 100 targets: Complete 36, Partial 58, Not
available 6, Failed 0.** The 58 Partial is dominated by the 44 targets that
genuinely have no Threads profile at all (Combined mode requires both
platforms for `Complete`), not by extraction failure -- 0 rows failed.


## Round 8 ? output selection, exports and measurements (13 October 2026)

| ID | State | Evidence and action |
| --- | --- | --- |
| P67 | Implemented / ported tests pass | Current branch lacked existing sprint3 clipboard, CSV/Excel and history features. Ported file by file, retained formula protection, added current quality/availability columns and complete modern record storage via an additive history table. Original ported test files remain byte-identical. [Report](implementation/round8-export-port.md). |
| P68 | Implemented / real Tk verification | Output selection was fixed. Added persistent modal column selection; Username mandatory; all-optional-off retains Status. User clarified quality/availability diagnostics must also be optional. Clipboard, CSV, Excel and history use the same selection. Corrupt settings fall back with a status-bar warning. [Report](implementation/round8-output-selection.md). |
| P69 | Implemented / synthetic timing passes / live saving NOT established | Stable populated dialogs now return after four unchanged poll intervals; changing content resets the counter. No timeout/pacing/worker changes. Same 12 targets measured 156.9s before vs 213.6s after, with more navigation/identity/dialog failures after. No projected saving claimed. [Report](implementation/round8-stable-dialog.md). |
| P70 | Analysis corrected / regression added | Round7 analyzer counted literal Not shared as a present country and could attribute missing date/badge to a country disclosure flag. Extended existing analyzer: withheld applies only to country, not unrelated fields. Recomputed historical Combined country totals: IG 86 present / 7 absent-account / 7 withheld; Threads 40 present / 44 absent-account / 15 withheld / 1 failed. Timing remains 410.5s. |
| P71 | Open / reproduced in fresh live runs | Round8 small runs and IG-only benchmark show substantially worse live rendering/navigation than Round7. IG-only: 100 rows in 584.6s, 41 target extraction failures; stages complete 52, navigate 17 (including 7 real not-found), identity 20, dialog 11. Logs include ERR_NETWORK_CHANGED and navigation timeouts. Underlying cause not isolated; neither stable polling nor live variance alone proven responsible. Do not claim zero errors or NFR-1 acceptance. |

Round8 P65/P71 follow-up: Threads-only measured **359.9s** with 9 extraction
failures (7 about_dialog, 2 about_menu); no 300s acceptance. Both per-mode
runs returned exactly 100 targets with no duplicates/unstarted or session
blocks. Final suite **222 passed**; live rendering failures remain open.
[All mode measurements and limits](implementation/round8-mode-benchmarks.md).
