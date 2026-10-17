# MetaInspector Desktop: User Manual

What every button, column and value means. For installation and first-time
login, see the Quick Start guide.

---

## 1. What the app does

- Takes a list of Instagram usernames.
- For each one, reports whether the account is **active, not found, banned or
  private**.
- Where the platform discloses it, also reports the **country the account is
  based in** and the **month it joined**, for Instagram and for Threads.
- Shows results live in a table while the run is going.
- Lets you copy the results into Google Sheets, or save them as CSV or Excel.
- Keeps a local history of past runs.

**It never invents a value.** If something could not be read, the app says so
instead of filling the cell with a guess.

---

## 2. The five checking modes

Pick one on the left before pressing Start.

### Combined (IG + Threads)

- Checks **both** platforms for every account.
- Gives the most data: IG country and joined date, Threads country, joined
  date and badge.
- **Slowest.** Measured between about **7 and 10 minutes** for 95 accounts.
- This is the default.

### Instagram Only

- Checks Instagram only. Threads is not visited.
- Gives IG status, country and joined date.
- Measured between about **3.5 and 7 minutes** for 95 accounts.

### Threads Only

- Checks Threads only. Instagram is not visited.
- Gives Threads status, country, joined date and badge.

### Smart Combined (skip Threads when IG gives country)

- Checks Instagram first. **If Instagram already gave a country, Threads is
  skipped** for that account. If Instagram gave no country, Threads is checked
  as a fallback.
- **Recommended for most runs.** Measured at about **4 minutes** for 95
  accounts, against 10 minutes for Combined on the same list.
- **Accuracy is not reduced.** Where both platforms report a country they
  agreed 36 times out of 36 in testing, and the accounts Threads rescues are
  exactly the ones Instagram stayed silent on, which this mode still checks.
- **What you give up:** Threads Joined and Threads Badge for the skipped
  accounts. If you need those columns, use Combined.

### IG Status Only (no login, fastest)

- Checks **only whether the Instagram account exists**. Active, not found or
  suspended.
- **Needs no login at all.** No checker account, no setup step.
- Measured at about **1 to 1.5 minutes** for 95 accounts.
- **Cannot return country or joined date.** A logged-out Instagram page shows
  no profile menu, so the transparency panel does not exist to read.

---

## 3. The left panel

**What to Check** lets you combine individual fields, as in the supplied
reference picture. Use IG Alive, Threads Alive, IG Country, Threads Country,
IG Age (joined date), and Threads Age (joined date). **IG + Threads Alive** is
a shortcut controlling the two Alive boxes; it does not duplicate checks.

For example, untick everything except **IG Alive** and **IG Country** to read
IG status and country. Add **IG Age** to request its joined month/year too.
Age means the platform's reported joined date, not a calculated exact age.
At least one checkbox must remain selected before Start.

Clicking a checking-mode preset resets the checkboxes to that preset. Editing
a checkbox switches to a custom selection and shows its count. **Combined
remains the startup default.** Preset Smart Combined keeps its conditional
Threads behavior until you edit individual checks; custom selections visit
each explicitly selected platform without that conditional omission.

Only IG Alive by itself uses the anonymous no-login path. Other selections
use saved login sessions for the selected platforms. Status-only platform
checks stop after profile identity, without opening About. Country/date
choices read the shared About panel and keep only requested metadata. A
country/date check necessarily reads profile status as part of validation.
Excluded fields are shown as **Not checked**.

- **Input Usernames:** paste usernames, one per line. The count appears top
  right of the box.
- **Load .txt File:** import a plain text list instead of pasting.
- **Checking Mode:** the five modes above.
- **Parallel workers:** how many accounts are checked at the same time, 1 to
  5. Five is the normal setting. This is **not** the number of login accounts;
  one healthy login can drive all five.
- **Dialog (s), default 10:** how long to wait for the transparency panel to
  show its values before giving up on that account. Raise it if you see many
  timeouts.
- **Menu (s), default 8:** how long to wait for the profile menu to appear and
  be clickable.
- **Save debug captures:** writes screenshots and page text for every step
  into a `debug` folder. Leave it **off** for normal use. Only turn it on when
  investigating a problem.
- **Start, Pause, Stop:** Pause suspends between accounts and resumes where it
  left off. Stop ends the run and keeps whatever has been collected.

---

## 4. The results table

| Column | What it means |
| --- | --- |
| **#** | Row number in the order results arrived. |
| **Username** | The account checked. |
| **Status** | The overall verdict. See section 5. |
| **Data** | How complete this row is. See section 6. |
| **Checker** | Which login account did the work. Empty in IG Status Only. |
| **IG Country** | The country Instagram says the account is based in. |
| **IG Joined** | The month and year the Instagram account was created. |
| **Threads Country** | The same, from Threads. |
| **Threads Joined** | Joined month from Threads, plus the follower badge. |
| **Duration** | Seconds spent on this account. |
| **Error** | The reason something is missing, when there is one. |

---

## 5. Status values

- **ACTIVE:** the account exists and is reachable.
- **NOT_FOUND:** the account does not exist, or was deleted or removed.
- **BANNED:** the account is suspended.
- **ERROR:** the check could not be completed. The account may well be fine.
  Re-run those rows. See section 8.
- **BLOCKED:** your own login account hit a security check. Stop and resolve
  the login before continuing.
- **UNKNOWN:** IG Status Only could not find a clear marker on the page. It
  means "not sure", not "does not exist".

---

## 6. The Data column

- **Complete:** everything the chosen mode asked for was collected.
- **Partial:** some of it was collected. Cell labels explain missing values;
  the Error column contains actual check failures, if any.
- **Not available:** the account does not exist, so there is nothing to
  collect. This is a correct result, not a failure.
- **Status only:** an IG Status Only row with a clear verdict.

---

## 7. What missing-value labels mean

The live table and reopened history explain missing country and joined-date
values in their own cells. These labels apply to both Instagram and Threads.

| Cell label | Meaning |
| --- | --- |
| **Not checked** | The field or platform was excluded by the selected checks or mode. |
| **Skipped (IG country)** | Smart Combined already obtained a real IG country, so Threads was skipped. |
| **Unavailable (status only)** | Logged-out IG Status Only cannot collect country or joined date. |
| **No account** | This platform returned not found, with no country-availability state. |
| **Not shown by platform** | The country row was absent from the platform's panel. This label describes country, not a missing date. |
| **Not shared** | The platform literally displayed these words. |
| **Page not loaded** | The check failed at the navigation stage. |
| **Identity unverified** | The intended profile could not be verified. |
| **Menu not found** | The check failed while opening the profile menu. |
| **About unavailable** | The check failed while finding or clicking the About menu item. |
| **Panel incomplete** | The About panel did not return this value. |
| **Check failed** | A failure was recorded without one of the stages above. |
| **N/A** | The stored fields do not explain the missing value. No cause is guessed. |

A country can be withheld while the date is available. A failed check can also
return some values, so blank country plus a populated date alone does not
prove why the country is missing. Read the cell label and full **Error** text.

These are **display labels only**. Clipboard, CSV and Excel retain the original
field values and existing empty-value representation; labels are not written
into missing country/date fields. For exported reasons, use **Select Output**
and tick **IG Status**, **Threads Status**, the relevant **Country Availability**
columns, and **Error**. Diagnostics are optional. A raw `not_disclosed` means
the country row was not shown, while `not_shared` means the platform printed
"Not shared".

---

## 8. Things that look like bugs but are not

- **An account was ACTIVE yesterday and is NOT_FOUND today.** These lists
  decay. In one measured day, **2 of 95 accounts were deleted.** Re-running
  will legitimately give different numbers.
- **A row says ERROR but the account opens fine in a browser.** Transient
  failures happen at a rate of roughly **2 in 95**. The app reports ERROR
  rather than guessing. Re-run those rows.
- **Country is missing but joined date is filled.** Read the country cell's
  label. **Not shown by platform** and **Not shared** indicate disclosure
  limits; a stage failure label indicates a read failure. See section 7.
- **The same list takes 7 minutes once and 10 minutes another time.** Meta's
  own page speed varies by time of day. The transparency panel was measured
  running twice as slow near midnight as in the afternoon.
- **IG Status Only shows UNKNOWN.** It now allows at least 30 seconds per
  attempt and retries Unknown once after the main pass, using the same warm
  browser context. Persistent Unknown keeps its reason in Error, with no
  guessed verdict. On 15 October 2026, a 50-target CLI comparison returned
  **0 Unknown before and 0 after**, taking **37.1s and 125.7s** respectively.
  The client's earlier **26 Unknown out of 95 in the EXE** was not reproduced;
  no packaged cold-start resolution or speed improvement is established.
  If Unknown remains after its automatic retry, check connectivity and retry
  later. [Measurement and limits](implementation/status-clarity-and-cold-start.md).

---

## 9. Getting results out

- **Copy for Google Sheets:** copies the table to the clipboard. Paste into
  Sheets with Ctrl+V and it lands in separate columns using Select Output.
- **Export CSV / Export Excel:** saves a file with the same selected columns.
- **Select Output:** choose which of the **14 available columns** you want.
  The selection applies to clipboard, CSV and Excel alike, and is remembered
  after you close the app. Unticking everything still keeps Username and
  Status.
- **View Run History:** past runs are stored locally. Open one to see its date,
  mode and account count, and copy that batch again.

Available columns: Username, Status, IG Country, IG Joined, Threads Country,
Threads Joined, Threads Badge, Data Quality, IG Status, Threads Status,
Seconds, Error, IG Country Availability, Threads Country Availability.

**Select Output** also provides quick presets: **Full export**, **Alive/status
only**, **Country only**, **Age/joined only**, and **Checked fields**. Choose a
preset, adjust any individual columns, then press OK. Cancel discards the
draft. Full export includes every supported column for data already collected;
it does not run extra checks. Checked fields follows the results' stored check
selection, or the panel selection if no results exist yet.

**Copy/export rows** chooses All results, IG Alive only, Threads Alive only,
or Both Alive only. Alive includes active and private profiles with explicit
platform status; Unknown, errors, skipped platforms and Not found do not
qualify. A Smart-skipped Threads profile cannot qualify as Threads Alive.
History has the same row filters, defaulting to All results when opened.

**Live export:** once the first completed result appears, copy, CSV and Excel
remain available while checking continues. Each action takes a snapshot of
finished rows so far, applying the selected columns and row filter. It does
not stop the batch, and the file does not keep appending later arrivals.
Export again after more rows finish or use history for the final batch.

---

## 10. Limits you should know

- **Country and joined date always require a logged-in checker account.**
  Only the status check works logged out.
- **Smart Combined does not collect Threads Joined or Threads Badge** for
  accounts it skips.
- **A completely empty Threads profile** (no posts, no followers) sometimes
  shows no About control at all, so no data can be read from it. Measured at
  1 failure in 149 platform checks.
- **The pause between accounts is deliberate.** It exists to avoid rate limits
  and account suspensions. It accounts for a large share of the run time and
  should not be removed casually.
- **The app is not code-signed.** Windows SmartScreen will warn on first
  launch. This is expected for an unsigned program.

---

## 11. If something goes wrong

- **Many rows time out:** raise Dialog (s) to 15 and Menu (s) to 12, then
  re-run the failed rows.
- **Status says BLOCKED:** your checker login hit a security challenge. Open
  Setup Checker Account, log in again, clear the challenge, then re-run.
- **Header says no login saved:** run Setup Checker Account. Not needed for
  IG Status Only.
- **The whole run is slow:** check the time of day, and prefer Smart Combined.
- **Investigating a specific account:** turn on Save debug captures, run only
  that username, and send the resulting `debug` folder files.
