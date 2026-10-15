# BL-02: physical clean-Windows acceptance checklist

Status: NOT RUN by the coding agent. Requires a second physical Windows 10/11
64-bit computer with no Python and no Playwright installed. TSK-502 stays
unchecked until Huzaifah reports the results. A virtual environment, renamed
Python folder or test on the development computer does not satisfy this check.

For every failure capture: the exact error text, a screenshot of the complete
app/browser/dialog, Windows version, time, and the corresponding BL-01 check
number below. Keep passwords, authenticator secrets and session cookies out
of screenshots shared with support. Record every step as Pass or Fail.

1. **Prepare the delivery (BL-01 #7).** Copy only the supplied
   `MetaInspectorDesktop.exe` and Quick Start/checklist documents to the second
   computer, for example `Downloads\MetaInspector`. Do not copy source,
   `accounts.txt`, browser profiles or development results. Right-click the
   executable, choose **Properties**, and compare **Size** in bytes with the
   packaged-build report. Use Size, not Size on disk. If it differs, capture
   Properties and stop until the correct file is supplied.
2. **First launch and SmartScreen (BL-01 #1).** Double-click the executable.
   If Windows says it protected your PC, confirm the file came from the trusted
   delivery. Click **More info**, then **Run anyway** if offered. Expected:
   the app opens after extraction, with no Python installation request. Do not
   disable security or bypass organization policy; capture a blocking screen
   and ask the administrator/delivery contact if Run anyway is unavailable.
3. **Observe the header (BL-01 #1).** Leave the app open at least 30 seconds.
   Expected: it remains responsive and shows no saved checker login on this
   new machine. Capture the full window if it exits or reports an error.
4. **Inspect all modes (BL-01 #3).** In Checking Mode, scroll the mode list if
   needed and select each radio: Combined, Instagram Only, Threads Only,
   Smart Combined, IG Status Only. Expected: all five labels appear and each
   selects. IG Status Only should say no login is needed and disable setup.
5. **Run anonymously before any login (BL-01 #4).** Select IG Status Only.
   Paste two agreed target usernames, one per line, and click Start Checking.
   Expected: rows return without setup or a checker account. Country/date cells
   say Unavailable (status only); Threads is not checked. Explicit page markers
   produce statuses; a deadline/network failure must remain Unknown with an
   error rather than inventing a verdict. Record elapsed time and row counts.
   Browser launch errors, missing rows or a login requirement fail this check.
6. **Test bundled setup (BL-01 #2).** Select Combined. Click Setup Checker
   Account, then Login IG + Threads beside the intended checker. Expected: a
   real Chromium window opens to Instagram without installing Playwright or
   any browser. Complete login and any verification yourself. Once the feed
   opens, close that window; finish the subsequent Threads login/onboarding
   and close it after its feed/profile appears. Record the app's verification
   result. Capture any executable-path error, with no secrets in the image.
7. **Run Smart Combined (BL-01 #5).** Select Smart Combined and use a small
   agreed list containing a target whose IG About panel shows a country.
   Click Start Checking. Expected: that row has the observed IG country/date,
   Threads cells say Skipped (IG country), and no error is created by the skip.
   Complete IG metadata without another error should report Complete. A target
   without an IG country should still be Threads-checked. Compare the same
   exact username's About panel when validating country/date.
8. **Select output and copy (BL-01 #6).** Click Select Output, untick IG Country,
   keep Username and Status, then OK. Click Copy for Google Sheets. Expected:
   Copied! feedback and a green message. Paste into a blank Google Sheet at A1.
   Expected: selected headers and rows in separate columns, with IG Country
   absent. Reopen Select Output and confirm the choice persisted.
9. **Export both formats (BL-01 #6).** Click Export CSV, save as
   `Downloads\MetaInspector\check.csv`. Repeat Export Excel as `check.xlsx`.
   Expected: both files exist, open in an available spreadsheet viewer and have
   the same selected headers and row count. Do not install Python to open them.
   Capture any save error or mismatch. An unavailable spreadsheet viewer is a
   separate unverified file-opening step, not a reason to claim it passed.
10. **History and restart (BL-01 #6 and #1).** Click View Run History, select
    the completed batch and check its rows. Copy/export from the viewer. Close
    the app, reopen the same executable, and inspect history and Select Output
    again. Expected: saved results and selected columns remain. The header
    should reflect the saved checker state; live preflight checks it again on
    the next logged-in run.
11. **Report back.** Send the executable byte size, Windows version, seven
    BL-01 Pass/Fail results, anonymous/Smart target counts and elapsed times,
    and any failed step's evidence. Confirm explicitly that this was a second
    physical computer with neither Python nor Playwright installed. Only after
    this report is reviewed may TSK-502 and BL-02 be marked complete.
