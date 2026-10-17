> **Latest update, 17 October 2026:** Checking Mode presets removed; What to
> Check now controls matching Live Results columns, including separate IG
> Alive and Threads Alive. 449 tests pass. Saved 95-row replay verified 190
> status cells with zero mismatches. No fresh speed benchmark. See the
> [current report](2026-10-17-checks-and-live-columns.md). Older reports below
> retain their historical measurements.

> **Latest update, 17 October 2026:** individual What to Check cards, field
> export presets, Alive row filters and live snapshot exports implemented.
> Full suite: 427 passed. See the
> [shared dated report](2026-10-17-selectable-checks-and-exports.md).
> Older measurements below are historical, not a new benchmark.

> **Historical Round 8 update:** output selection, clipboard/CSV/Excel and history
> implemented; 222 tests pass. Fresh 100-target IG-only 584.6s and Threads-only
> 359.9s; both exceed 300s and have extraction failures. Historical Combined
> baseline is 410.5s. Checker 5 was usable for these runs; the older login
> snapshot below is historical. See [current report](round8-mode-benchmarks.md).

# MetaInspector progress report - 13 October 2026

**Round 4 code implement aur live test ho gaya. Checker 5 ke IG + Threads logins
verified hain aur ek account par 5 pages chal rahe hain. Lekin correct results
under 5 minutes ka main goal abhi achieve nahin hua.**

## Kya complete hua

- Single-account Setup: Instagram ki window khulti hai; band karne par Threads
  ki alag window; usay band karne par dono platform identities live verify hoti hain.
- Onboarding Continue tak pohanchne ka window-size issue: fixed viewport hata
  kar maximized, resizable windows ki gayi. Aap ne phir onboarding complete ki;
  app ne **Both logins verified** confirm kiya.
- Workers=5 ab ek healthy account par **5 concurrent pages** banata hai. Pehle
  ek healthy checker par sirf ek worker page banta tha. Live run mein bhi 1 context,
  5 pages aur 5 resource blockers observed hue.
- Round 3 ki failure isolation, error rows, shared queue aur challenge stop retained.
- **182 tests passed in 62.85 seconds**, zero skips. Real Chromium concurrency
  aur sequential-window tests included hain. Yeh test duration scraping speed nahin.

## Aapki 95-account list ka actual result

| Cheez | Result |
| --- | --- |
| Total time, unrounded | **1047.6569999999992 seconds** |
| Aasaan reading | Taqreeban 17 minutes 28 seconds |
| Returned rows | **95/95** |
| Complete Combined data | **0** |
| Partial data | **14** |
| Failed data extraction | **81** |
| Error-free rows | **0** |
| Unstarted / duplicate rows | **0 / 0** |
| Actual checker | Sirf Checker 5 |

ACTIVE status wali 53 rows ko successful data extraction na samjhein: ACTIVE
account ki existence ka status hai. Har returned row mein extraction error tha.
Aapke kehne par 95 targets use hue; 100-target acceptance abhi run nahin hui.

## Ab asal maslay kya hain

1. **Profile loading/readiness:** IG par 49 aur Threads par 60 checks identity
   stage par fail hue. Inspected IG screenshot mein profile ke bajaye loading
   logo tha. Har failure ko wrong-selector kehne ka evidence nahin.
2. **Threads menu loading:** 33 About-menu failures. Inspected screenshot mein
   sahi profile ka menu khula, lekin items ki jagah spinner tha.
3. **IG About data:** 18 checks About polling tak pohnche lekin required fields
   complete nahin mile. Inspected case mein About dialog visible nahin tha.
4. **Speed:** Average row time 47.24494736842105 seconds; slowest 84.86 seconds.
   Platform timings aur raw captures saved hain. Network/server/CPU ya rate-limit
   ko proven cause nahin kaha gaya; next investigation ko yeh distinguish karna hai.

Do Threads targets se date/country aaye. Ek raw screenshot mein date/country target identity ke saath app result se match karte hain. Is se poori
95-account list ki accuracy prove nahin hoti.

## Evidence aur delivery

- Branch: `fix/single-account-worker-concurrency`; merge nahin ki gayi.
- Checkers **1/2/3 ko is round mein login/open nahin kiya**. Checker 4 aur original
  profile fallback bhi use nahin hue. Manual login/onboarding aap ne ki;
  app verification aur benchmark agent ne chalaya.
- [Round 4 report](round4-report.md), [exact benchmark](TSK-401-nfr1-benchmark.md),
  [95 row results](../../debug/round4-benchmark95.json),
  [test output](evidence/round4-maximized.txt).
- [Problem log](../problem_log.md) mein P50-P54 aur
  [test log](../test_log.md) mein successful aur failed attempts recorded hain.
- [Purani Round 3 report](round3-report.md) historical login blockers aur pehle
  fixes preserve karti hai; woh latest live state nahin hai.

**Ab baqi kaam extraction readiness/menu failures ko diagnose aur fix karna,
phir usable results ke saath speed dobara measure karna hai.** Round 4 implementation
complete hone ka matlab main accuracy/speed goal complete hona nahin hai.
