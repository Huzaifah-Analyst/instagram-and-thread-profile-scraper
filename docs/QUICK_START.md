# MetaInspector Desktop — Quick Start Guide

This guide is for the person who will actually run checks day to day. No
Python, no terminal, no technical setup beyond the steps below.

> **Note on this guide's status (2026-10-10):** the Google Sheets copy,
> Excel/CSV export and Run History steps below describe features built on
> the `feature/sprint3-sheets-export` branch. They are implemented and
> tested, but **not yet merged into the main branch** at the time this guide
> was written — see `docs/memory.md` section 3.3. Re-check the button labels
> and screenshots against the actual shipped build before handing this to
> the client, in case anything changes between now and merge.

---

## 1. First-Time Setup

1. Double-click **MetaInspectorDesktop.exe**. No installation wizard, no
   admin rights needed — the window opens directly.
2. The header shows a session indicator (top-right). On a brand-new
   install it will say **Disconnected — click Setup**.

## 2. One-Time Checker Account Login

MetaInspector checks accounts through your own dummy/checker Instagram
account, never your personal or business account.

1. Click **⚙ Setup Checker Account** in the top-right corner.
2. A browser window opens to the Instagram login page. Log in with the
   checker account you created for this purpose (enter any 2FA code if
   asked, same as logging in anywhere else).
3. Once you see your checker account's home feed, simply **close that
   browser window**.
4. Back in MetaInspector, the session indicator turns green and shows
   **● Connected**.

You only need to do this once. The login is remembered between restarts.
If it ever shows **Disconnected** again (for example after Instagram asks
for a fresh login), just repeat these steps.

## 3. Paste Usernames and Choose a Mode

1. In the left panel, paste or type usernames into the text box — one per
   line, with or without the `@`. The count below the box updates live
   ("N accounts").
2. Alternatively, click **📁 Load .txt File** to import a plain text file
   with one username per line.
3. Choose a **Checking Mode**:
   - **Combined (IG + Threads)** — checks both platforms (slowest, most data).
   - **Instagram Only** — status + country + join date for Instagram only.
   - **Threads Only** — status + country + join date/badge for Threads only.
4. (If your build has it) set **Workers** to control how many accounts run
   at once — leave this at the default unless asked to change it for a test.

## 4. Start a Check

1. Click **▶ Start Checking**.
2. The right-hand table fills in live, one row per account, as each one
   finishes — you do not need to wait for the whole batch to watch progress.
3. The bottom bar shows **Progress**, **Elapsed** time and an **ETA**.
4. While running you can:
   - **❚❚ Pause** — finishes the account each worker is currently on, then
     holds. Click again (now labelled **▶ Resume**) to continue.
   - **■ Stop** — finishes current accounts, then ends the run early. You
     keep whatever was checked so far.
5. If the checker session gets challenged by Instagram mid-run, the app
   stops automatically and tells you to log in again via **Setup Checker
   Account** — this is a safety feature, not a bug.
6. If a row shows no country/join date, check the **Error** column next to
   it — it explains why (for example, the page didn't load in time), instead
   of just leaving the cell blank.

## 5. Copy Results to Google Sheets

1. Once a run finishes (or you've stopped it), click
   **📋 Copy for Google Sheets** at the bottom of the window.
2. The button briefly changes to **✓ Copied!** and a green banner confirms
   how many accounts were copied.
3. Open your Google Sheet, click the top-left cell of an empty area, and
   press **Ctrl+V**. Every column (Username, Status, IG Country, IG Joined,
   Threads Country, Threads Joined) lands in its own spreadsheet column —
   no import wizard, no manual delimiter choice.

## 6. Export Files

- Click **Export CSV** or **Export Excel** at the bottom of the window to
  save the current results as a `.csv` or `.xlsx` file.
- A save dialog lets you pick the folder and file name.
- Both formats are safe to open in Excel directly: text that looks like a
  formula (starting with `=`, `+`, `-` or `@`) is saved as plain text, not
  as a live formula.

## 7. View Run History

1. Click **📜 View Run History** to open the history viewer.
2. Every run (finished or stopped) is saved automatically — you never need
   to remember to save it yourself.
3. Pick a past run from the list to see its date, mode, account count and
   duration, then re-copy or re-export that run's results exactly as if it
   had just finished.

---

## Troubleshooting

| Symptom | What it means |
| :--- | :--- |
| "Chromium is not installed" | Should not happen in the packaged `.exe` (Chromium is bundled); if you see this, the install is broken — contact support rather than trying to fix it yourself. |
| "The browser profile is in use" | Close any open Setup/login window first, then try again. |
| Session shows Disconnected mid-run | Instagram challenged the checker account. Click Setup Checker Account and log in again. |
| A row has no Country/Joined and no Error text | The account may simply not have that information public; this is a normal, not-an-error N/A. |
