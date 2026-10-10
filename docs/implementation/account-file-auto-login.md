# Account-file import and isolated automatic login

Date: 2026-10-10. Branch: `fix/data-accuracy-and-nfr1-verification`.

## Problem and scope

The operator owns five checker accounts and requested automatic setup from the
local account file. Inspection exposed only row/column counts: five rows, each
`username|password|2FA secret`, without a separate email column. The operator
confirmed these are permanent authenticator seeds, not temporary codes.

## Implementation

- Setup has **Import accounts & auto-login**. UTF-8 input is validated completely
  before settings change: at most five distinct usernames, three pipe-separated
  fields, a nonempty password and a valid Base32 authenticator seed. Blank/comment
  lines and an optional `username|password|2fa` header are accepted. A password
  containing a pipe can be CSV-quoted. Password whitespace is preserved exactly.
- Passwords/seeds live in the setup worker's memory. They are excluded from
  credential repr, application settings, progress, diagnostics and exceptions.
  The original user-supplied file remains where it was; it is not copied or
  deleted. Its known path, browser sessions and local settings are gitignored.
- Each imported username maps to a stable hashed profile directory. Reordering
  the file changes slot order but not session identity. Existing manual profiles
  remain on disk. Only usernames and slot selections are saved in settings.
- TOTP is generated locally with the standard library: SHA-1, 30-second steps,
  six digits, following [RFC 6238](https://www.rfc-editor.org/rfc/rfc6238).
  There is no third-party OTP service. Codes are entered only into a recognized
  authenticator prompt. Email/SMS prompts require manual entry.
- Login uses visible official HTTPS pages. An exact origin allowlist is checked
  before secret entry. Password and authenticator forms are each submitted at
  most once per platform per attempt. No account creation is automated.
- Accounts are set up sequentially; saved sessions can later participate in the
  existing concurrent checker pool. A failed/challenged setup stops the batch.
  The GUI keeps that browser available for manual completion; close it and
  reimport to resume. Already-authenticated matching profiles are reused.
- Success requires both a platform session cookie and the expected account's
  visible profile link. Imported identities are checked again during extraction
  preflight, preventing accidental use of a different manually logged-in account.

## Alternatives and limitations

Slot-number-only storage would mix sessions when file order changes; username
bindings avoid that. Storing credentials in JSON or logs was unnecessary, so the
app rereads the selected file for each setup attempt. Five simultaneous login
windows would make manual security prompts difficult to attribute; sequential
setup retains later parallel extraction. Checkpoints, incorrect credentials,
email/SMS codes and unfamiliar login layouts stay explicit manual steps.

The browser requests English UI. Account-specific language/layout changes can
still require manual login. A recognized cookie without an identifiable profile
link does not pass automatically. Login success does not guarantee country/date
disclosure or fix the separately tracked intermittent Threads loading failures.

## Validation

- First targeted suite: `1 failed, 31 passed in 15.30s`; a synthetic page omitted
  its UTF-8 charset and mangled a curly apostrophe in a challenge message. Fixed
  the fixture's content type; the production challenge detector was unchanged.
- Full suite: **151 passed in 32.12s**, zero skips, including real Tk import
  widgets, local Chromium login forms, RFC SHA-1 vectors, error redaction,
  wrong-origin/wrong-identity rejection, email/SMS handling, one-submit behavior,
  Threads continuation and stopping five-account setup on its first failure.
- Live verification outcomes are recorded in [test_log.md](../test_log.md).
  Synthetic tests do not establish five-account live success.

## Live findings and resulting correction

The real file validated five rows. The first IG attempt submitted no credentials:
its username control uses `name=email` and `autocomplete=username webauthn`, which
the initial exact selector did not recognize. Read-only inspection pinpointed
this. Added an email-name fallback and HTML autocomplete-token matching; the
targeted suite passed **18 tests in 19.80s**. The next live attempt verified the
first account on Instagram.

Threads then submitted an authenticator code once, but a matching session did
not become verifiable before the deadline. The batch halted: **0/5 accounts
verified on both platforms**, with the remaining four unattempted. A read-only
follow-up still showed the Threads login form, no session cookie and no visible
incorrect/invalid marker on that fresh page. The reason for the prior failed
progression is unresolved (P36); no bypass or repeated-code attempts were made.
The scripted verification closed its browser on failure. In the shipped GUI,
that browser stays open for manual completion and reimport resumes verification.

Code review also tightened identity proof: the expected-user link must be a
visible Profile control, not merely a feed mention. Unsupported/localized
profile controls fail explicitly rather than claiming a successful account match.
Final full suite after these changes: **153 passed in 26.68s**, zero skips.
`git diff --check` passed. Local candidate-file scan found zero real password/seed
matches; production sources parse and remain below 500 lines per file.

See [manual steps](../manual_verification.md) and issues P33-P36 in
[problem_log.md](../problem_log.md).
