# Current extraction failures and five-checker feasibility

Date: 2026-10-10. Assessment only; no application changes or new live requests.

## New evidence supplied by Huzaifah

Two screenshots in this chat show a user-operated Combined run with 95 queued
accounts, 5 workers, dialog/menu budgets 10.0/8.0 seconds, and debug captures
unchecked. The final screenshot reports 27/95, elapsed 3m 00s, 26 ACTIVE and
1 BLOCKED, stopped because Meta challenged the checker account. The header
still says Connected. These are screenshot observations, not an agent-run
benchmark or independently timed measurement.

Together the screenshots show rows 1–27: 13 have IG country/date fields
(11 October 2025, 2 November 2025); 14 have neither IG field. All 27 show
Threads country/date N/A. Thus zero visible records have both platforms'
country/date. Displayed values have not been validated against raw dialogs.

## Problems, with limits on what is established

1. **Misleading Connected indicator.** `session.py` checks only the saved IG
   cookie's name/expiry; it does not verify live IG or Threads authentication.
   Earlier agent-run evidence also showed a logged-out page despite Connected.
2. **One shared checker across five workers.** `scraper.py` launches one
   persistent context and gives its pages to all workers. Five distinct checker
   accounts and isolated sessions are not implemented. Whether shared-session
   concurrency caused this challenge has not been isolated experimentally.
3. **Threads extraction fails before the About panel.** The screenshots show
   repeated About-option failures. A wrong menu target, UI change, timing or
   session issue remain possible; the truncated errors and absent raw evidence
   cannot distinguish them.
4. **IG Options/dialog failures.** Multiple rows show missing Options or dialog
   timeouts. The failure stages are observed; merely increasing timeouts has
   not been shown to resolve the underlying cause.
5. **ACTIVE does not mean data retrieval succeeded.** The verdict can be ACTIVE
   while transparency fields are empty and errors are present. The green row
   makes successful profile classification easy to confuse with complete data.
6. **Challenge detection and stopping have limits.** A BLOCKED row stopped this
   run. In-flight workers finish their current account, which can add records
   after the blocked row. Earlier logged-out public-page evidence was not
   detected as a challenge. No evidence establishes this particular target
   username as the cause of a checker challenge.
7. **Insufficient diagnostic evidence.** Debug was unchecked in this run. Even
   when enabled, current dumps only contain text read during dialog polling;
   early menu failures produce no dump. Failed-page screenshots/text would
   make selector, login and rendering problems easier to distinguish.
8. **Completeness and date validation gaps in code review.** `_poll_dialog`
   returns when either country or date is found, without waiting for both.
   `_value_after_label` takes the first exact label match and following line;
   it does not verify that the dialog belongs to the requested username.
   These are code-level risks, not proven causes of the repeated date.
9. **Throughput acceptance remains unmet by evidence.** This run stopped at 27
   of 95 and is not the required complete 100-account benchmark. There is no
   verified speed claim for Combined mode with usable data on both platforms.

## October 2025

No October/November 2025 literal was found in application source. The two
November rows also mean this screenshot does not show one universal fixed
date. Possibilities include a genuinely similar creation-date cohort, wrong
dialog/label selection, or repeated values served by the site. There is no
evidence establishing deliberate fake/decoy data from Meta.

After session recovery, compare a few target profiles' manually visible About
dialogs, fresh raw captures, and parsed output for the same username. A mismatch
supports a local extraction bug; matching output establishes what the site
served, not independently the true account creation date. Preserve parser
logic until evidence identifies a specific failure.

## Five separate checkers: feasible design, not implemented or benchmarked

The installed Playwright API documentation confirms that browser contexts can
isolate cookies, and persistent profiles store login state in separate user
data directories. It prohibits simultaneous browser instances sharing one
user-data directory. Online documentation access failed in this session; the
installed `Browser.new_context` and `BrowserType.launch_persistent_context`
docstrings were inspected directly.

Proposed design: five named, separate checker profiles; interactive login/2FA
per profile; independent live IG and Threads health checks; one worker per
healthy checker initially; a shared job queue; per-checker pacing; records with
checker ID and data-completeness status. Session cookies stay local and ignored.
Login/password/email/2FA secrets do not need to be embedded in application code.

A checker challenge should pause the run and identify the session needing
attention; automatic account switching must not be treated as a verified cure
for a challenge. Splitting ordinary work across authenticated checkers is
technically different from having five tabs on the same login, but it does not
repair selectors, prove date accuracy, or guarantee a fivefold speedup.

Shared cookies across five logins were rejected because they do not provide
independent checker sessions. Blindly reassigning challenged jobs was rejected
because it obscures the current failure and has no measured reliability here.
Increasing concurrency before fixing single-checker extraction was rejected
because the new screenshots already show zero complete Combined results.

Recommended order: live session validation and failure captures; narrow IG/
Threads extraction fixes supported by captures; data-completeness UI; then
isolated checker management and measured 1/2/5-checker comparisons. This document
records the proposal; it does not claim that the pool exists or works live.
