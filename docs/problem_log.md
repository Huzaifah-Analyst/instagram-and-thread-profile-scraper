# MetaInspector central problem log

Updated: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.
This is the single running inventory of problems. Confirmed observations,
reproduced code defects and unverified hypotheses are distinguished explicitly.
Test executions remain in [test_log.md](test_log.md).

## Current implementation status

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
