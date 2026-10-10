# Transparency identity, dialog parsing and platform login

2026-10-10. Covers P03–P14, P18–P22, P28, and P30.

## Observed evidence

The original production Threads attempt returned ACTIVE / About option missing
after 19.53 seconds. Its captured page explicitly displayed **Log in or sign up
for Threads**. Instagram's saved login did not establish Threads authentication.
The selected real Threads menu icon carried `title="More"`; this supports a
named-action selector. It does not prove the old rightmost-icon selector caused
every previous failure.

The corrected preflight later returned **Threads login required** before
assigning any targets: Combined, one checker, 23.2 seconds total. IG passed
preflight in that run. An earlier readiness implementation failed against IG's
Content Security Policy; it was replaced by bounded locator text polling.

An IG-only live run reached the requested `brenda_1074` profile but did not open
a readable About dialog: 25.3 seconds total, 17.05 seconds row time, ACTIVE/Failed,
both transparency fields empty. The final capture shows the profile and no
dialog. Its underlying menu-action failure is **not yet pinpointed**. The code
now captures the open menu, the post-click page, and final state when debug is on.

The operator subsequently confirmed both logins complete. Agent-side post-login
launches were blocked by automatic permission-review timeouts; a user-operated
Combined verification was requested. Consult the running log for newer evidence.

## Changes and rationale

- Treat observed login headings, redirects and challenges as checker failures;
  verify each requested platform and its platform-scoped session cookie.
- Cookie metadata in the app header is described as saved login presence, never
  as live Connected. Batch startup checks the selected platform(s).
- Require the expected host, URL handle and visible profile identity before
  ACTIVE; require the requested username inside a visible transparency container.
- Ignore hidden and wrong-user dialogs. Wait for late fields; retain date-only
  data as Partial rather than guessing a missing country.
- Preserve exact labels/localized values. Reject a following field label as a
  value. Add the documented IG About-this-profile wording as a compatible alias.
- Search visible menu matches instead of a hidden `.last`. Threads prefers the
  observed named More action instead of an arbitrary rightmost SVG.
- Recheck late challenges after failures; bound click/JS fallback work; validate
  finite positive timeouts and supported profile URLs/usernames.
- Check same-handle Threads independently when Instagram is NOT_FOUND. Same
  handles are lookup targets, not proof the two profiles belong to one person.
- Split the oversized extractor into parser, browser, dialog and orchestration
  modules, with logged specific exceptions.

Rejected: changing October 2025 values, guessing country from account names,
loosening labels globally, or treating public profile visibility as successful
transparency extraction. The exact corrected user screenshot for `brenda_1074`
shows China / October 2025; it matches the old app output. No batch-wide fake-date
or server-decoy hypothesis has been established.

## Tests and limits

`test_accuracy_regressions.py` uses real local Chromium and synthetic HTML;
`test_health_and_validation.py` checks parsing, health boundaries and result
semantics. Synthetic captures are explicitly not live Meta evidence. One logged-in
Threads panel was subsequently verified below; live five-account accuracy still
needs verification.
See [test log](../test_log.md) and [central inventory](../problem_log.md).


## Subsequent live verification and final automated result

Once automatic approval recovered, a single-account Combined run after the
operator's login read both actual panels: 17.1s total, 8.36s row. Instagram raw
text and screenshot showed China / October 2025. Threads showed October 2025,
100M+ and country Not shared. This demonstrates that authenticated Threads
extraction works on this captured panel; it does not establish broad reliability.
The Not shared quality correction is documented [separately](threads-disclosure-quality.md).

A following live recheck returned Failed (62.0s total / 43.41s row): no IG About
menu appeared, and Threads' captured page was still its logo/loading splash with
no readable body. The exact source of that intermittent loading failure remains
unresolved. There is no evidence of incorrect field substitution in this attempt.

Final automated suite: **113 passed in 13.51s**, zero skips, including real Tk
widgets and local Chromium DOM. The earlier Tcl failures occurred in restricted
execution; the normal desktop run passes with a single Tk interpreter fixture.
Two controlled 10-target batch launch attempts did not execute because automatic
permission review timed out. That controlled batch, five live sessions, and the
100-account Combined benchmark remain pending.
