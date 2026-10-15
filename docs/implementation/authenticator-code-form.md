# Automatic entry on the current authenticator screen

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.

## Evidence and correction

The operator supplied an Instagram two-step-verification screenshot with the
heading **Go to your authentication app**, an empty **Code** field and a checked
Trust this device control. The operator wants the app to complete this step
using the already supplied permanent authenticator secret. This is within the
automatic setup scope; a routine authenticator prompt does not inherently
require the user to type the code.

The previous detector only recognized three named inputs and an exact
one-time-code autocomplete attribute. It did not recognize a field solely by
its Code label or a modern approvals_code input. The screenshot establishes the
visible label, not the real DOM attributes: those alternatives were reproduced
with local browser fixtures, not asserted as captured live HTML.

## Changes and rationale

- Added `authenticator_form.py` to recognize legacy fields, approvals_code,
  autocomplete tokens, labelled Code textboxes and a narrow six-digit numeric
  fallback. Label/numeric fallback requires explicit authentication-app wording;
  email/SMS wording disqualifies it. Ambiguous multiple fields do not receive codes.
- The existing local TOTP generator supplies the code. The submit control is
  selected within the field's closest form/dialog, preferring Continue/Confirm
  over Log in. A login button behind the dialog cannot steal the submission.
  Playwright scrolls controls into view during fill/click, including below-fold
  controls like those in the supplied screenshot. Trust-device selection is left
  as displayed; the app does not change it.
- Record the code as submitted only after its button click succeeds. Fixed
  sanitized errors remain in place; no code, password or secret is logged.
- Added one bounded return to Threads when its IG authentication handoff finishes
  on the correct Instagram account. Instagram cookies/profile alone never count
  as successful Threads login: Threads must still pass its own identity check.

Matching every numeric field or clicking the first page-wide login button would
be ambiguous. Generating repeated codes until accepted could repeat a rejected
login, so the existing one-submit limit and explicit manual-stop behavior remain.
An unrelated checkpoint/CAPTCHA/email/SMS step still requires its own completion.

## Validation and remaining limits

- Targeted real local Chromium suite: **24 passed in 33.52s**.
- Complete automated suite: **159 passed in 35.94s**, zero skips.
- New cases cover Code labels/ARIA labels/approvals_code/numeric controls,
  a Continue button below the fold, an unrelated outer Log in button, an email
  prompt mentioning an authenticator alternative, and an IG-to-Threads handoff.
- All browser fixture requests were intercepted locally. No real credentials
  were used in tests. Live acceptance on the operator's exact open page is still
  pending: browser-close confirmation was requested, and an attempted read-only
  Windows process-state query was denied. No duplicate login was started.

See [test log](../test_log.md) and P36/P37 in [problem log](../problem_log.md).

## Operator verification

Close the old setup browser and app, restart `python main.py`, and choose
**Setup Checker Account -> Import accounts & auto-login** with the same local
account file. This import flow supplies credentials and TOTP automatically;
the separate **Login IG + Threads** button remains the manual-login method.
On an authentication-app Code prompt, the imported account's code should be
entered and submitted without opening a separate authenticator app. A complete
two-platform setup is confirmed only by the app's verified-account message.
