# MetaInspector central problem log

Updated: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.
This is the single running inventory of problems. Confirmed observations,
reproduced code defects and unverified hypotheses are distinguished explicitly.
Test executions remain in [test_log.md](test_log.md).

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
| P03 | High / observed | Header Connected reflects cookie metadata only, including after a challenge. Earlier saved live screenshot was logged out despite Connected. `session.py`, `app.py::_refresh_session`. | Separate saved-login presence from live IG/Threads health and invalidate health on challenge. |
| P04 | High / reproduced locally | Public logged-out page with Log In / Sign Up returns no session challenge. `logged_out_public_page_not_detected`. | Detect actual authenticated UI state, without confusing a target bio with a login wall. |
| P05 | High / reproduced locally | `_poll_dialog` accepts text from a **hidden** dialog before the visible correct one. Synthetic hidden October/China beat visible April/Canada. `hidden_dialog_selected_before_visible_target`. | Require visible intended transparency container. Verify on fresh live captures before claiming production repair. |
| P06 | High / reproduced locally | First parseable dialog wins; it is not bound to target identity. Wrong-user dialog wins in local two-dialog fixture. `first_dialog_not_bound_to_target_identity`. | Check navigated profile identity and appropriate dialog ownership; reject mismatches. |
| P07 | High / reproduced locally | Missing date value followed by country label produces `date_joined = Account based in`. No date/value validation or adjacent-label guard. `missing_value_accepts_next_label_as_date`. | Narrow label/value validation with real fixtures, retaining localized formats. |
| P08 | High / reproduced locally | Poll returns as soon as **either** field is present. Country added later is lost, and extractors only flag error when both fields are empty. `poll_returns_on_first_field_before_later_content`. | Distinguish settled/complete data from still-loading data; support legitimate country omission rather than requiring both unconditionally. |
| P09 | High / reproduced locally | An unclassified generic error page becomes ACTIVE with an Options error. No positive profile identity/existence requirement. `unclassified_error_page_returns_active`. | Use unknown/error until profile existence is established. |
| P10 | High / observed | Green ACTIVE rows coexist with failed/missing extraction; all 27 prior rows lacked Threads data. `ban_engine.py`, `theme.py`, `data_table.py`. | Keep account status and extraction completeness separate in UI/results. |
| P11 | High / reproduced locally; live cause unresolved | Threads chooses the rightmost SVG within coordinate bounds. A local fixture selects an unrelated control. Prior live runs repeatedly fail to find About afterward. | Inspect the actual failing menu and prefer semantic/verified action targets. |
| P12 | Medium / reproduced locally | Menu lookup examines `.last` for each exact label: a hidden last duplicate masks a visible usable button. `last_hidden_duplicate_hides_visible_menu_candidate`. | Search visible matching elements within the intended menu. |
| P13 | Medium / reproduced locally; live compatibility unresolved | IG ignores a synthetic About this profile menu item. The user screenshot shows that wording as the **dialog title**, not the menu item; original prototype accepts it. | Capture actual menu labels before deciding which aliases need production support. |
| P14 | High / observed failures, cause unresolved | IG Options missing and dialog timeouts occur live. Header presence is treated as page-ready before menu availability; challenge checks occur before menu/dialog work. | Capture failed page, stage, URL and timing; check late challenges before classifying a timeout. |
| P15 | High / design confirmed; causal hypothesis open | Five workers share one persistent checker context. Five separate checker accounts are not implemented. Challenge causation by concurrency is not isolated. | Establish working one-worker extraction, then evaluate isolated checker profiles and measured scaling. |
| P16 | Medium / code-review risk plus observed rows | Global stop is checked between accounts. In-flight accounts finish and another worker can proceed from IG into Threads after a global stop. Rows appeared after BLOCKED in user run. | Add a global-stop check between platform stages; define cancellation semantics and test concurrency. |
| P17 | High / observed and code-reviewed | Debug off in user runs; enabled debug only dumps text reached during polling. Early menu/login failures have no page snapshot or stage evidence. | Add opt-in failure capture and per-field provenance, with private data staying local. |
| P18 | Medium / reproduced locally | Username cleanup accepts full URLs and whitespace-containing strings as usernames. It does not transform a valid Instagram URL into its handle or reject invalid input. | Validate/normalize input explicitly; preserve exact target identity in results. |
| P19 | Medium / reproduced locally and code-reviewed | Negative poll budgets are accepted. GUI numeric conversion also admits non-finite values such as infinity; invalid textual input silently defaults. | Require finite, positive bounded budgets with a visible validation message. |
| P20 | Medium / code-review risk | The GUI can start when session is disconnected. Setup opens only IG; it does not establish/test Threads login separately. | Run a live preflight for each selected platform before the batch. |
| P21 | Medium / code-review risk | `_safe_click` gives explicit limits to two click attempts but none to locator `evaluate`. Installed Playwright docs say locating for evaluate defaults to 30,000ms. Outer polling budgets can also overrun during locator operations. | Enforce elapsed deadlines across operations; do not claim a guaranteed 10-second whole-click bound. |
| P22 | Medium / code-review risk | Combined mode skips Threads whenever IG is NOT_FOUND. The existence of a same-handle Threads profile is assumed, not independently checked. | Document the cross-platform identity contract or check platforms independently where required. |
| P23 | Medium / observed limitation | Error cell truncates at 200 characters and has no detailed-row viewer. GUI records exist in memory; this branch has no run-history/export implementation to retain them automatically. | Expose full error/details and persist diagnostic results. |

## Packaging, documentation and maintenance problems

| ID | State | Finding / next action |
| --- | --- | --- |
| P24 | Code-review risk; packaged restart not tested | GUI profile root is derived from `__file__`. In a onefile build that can place browser state under `_MEIPASS` rather than a durable user-data directory. CLI profile/debug paths instead depend on current working directory. Verify packaged profile location across two launches, then centralize stable paths. |
| P25 | Code-review risk | Packaging selects the lexicographically last cached `chromium-*`, not the revision required by the installed Playwright driver. Dependencies use open-ended lower bounds. Resolve the required revision and pin a tested dependency set. |
| P26 | Observed documentary mismatch | README advertises 100 accounts in 4–5 minutes and clipboard/history features. This branch's app has no clipboard/history/export modules and no successful Combined benchmark. Quick Start partly warns about branch differences. Label capabilities and performance by verified build. |
| P27 | Existing measured finding, still open | Prior packaging report measured 309.9 MB against the under-150 MB requirement; clean-machine delivery remains unverified. See memory section 5 / Sprint 5. No rebuild or size remeasurement in this audit. |
| P28 | Reproduced static inventory | Production `extractors.py` has 572 lines, over the 500-line project rule, and two silent exception handlers. Several legacy scripts also contain silent handlers and broad selectors. Split production responsibilities during an authorized fix and retain diagnostic messages. |
| P29 | Observed workflow issue, mitigated once | Setup browser opened but was not visible to user; prior process/window check and foreground activation resolved that occurrence. No persistent foreground/focus handling was added to the app. |
| P30 | Test coverage gap, reproduced | Existing 81 tests pass while this audit reproduces 11 risk/failure cases. Current tests largely use fake browser pages and do not prove live authentication, target identity or current Meta selectors. Convert verified failure cases into regression tests alongside fixes. |

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

Full suite: **81 passed in 1.86s**, exit 0. No application behavior was changed.
This audit establishes actionable risks; it does not establish that hidden
dialogs caused any actual October date. The same-account user screenshot
supports the opposite conclusion for brenda_1074: its displayed values match.

## Next sequence and update convention

1. Fix evidence/identity/health handling before making accuracy or speed claims.
2. Address reproduced dialog, completeness and menu-selection defects with
   regression tests; verify actual live failures with captures.
3. Verify independent Threads login/extraction; then measure controlled scaling.
4. Evaluate the five-checker proposal only after baseline extraction works.

Append new problems with stable P-IDs. Update each entry's state and link the
fix report/test evidence when resolved; retain this correction history. Keep
individual test runs in test_log.md and task-method reports under implementation/.
