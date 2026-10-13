# Round 5 Task 2 - one versus five pages

13 October 2026. Same checker_5 and same ordered eight known-field targets as
Task 1; IG-only, blocker ON, fixed six-second pacing, same timeouts/headless/debug.
No other checker was opened and no concurrent browser test ran alongside these.

| Fresh comparison | Complete IG country/date | Failure stages | Elapsed seconds |
| --- | --- | --- | --- |
| 1 worker | 2/8 | About dialog 6 | 150.09299999999712 |
| 5 workers | 3/8 | About menu 2, About dialog 2, identity 1 | 42.89099999999962 |

Both passed expected checker identity preflight and returned all eight rows;
no active challenge or stop was observed. The original one-page blocker-ON Task 1
run was 8/8, so repeated one-page behavior itself changed during this session.
This evidence does not establish five-page concurrency as the sole cause, a
reliable maximum worker count with blocker ON, or a permanent account restriction.

A follow-up at **five workers with blocker OFF** returned **8/8 complete** in
**30.01599999999962 seconds**. Thus this machine/account can supply all eight
known IG fields at five pages in that condition. That success is not proof that
any 50-target Combined run will remain clean, nor does it distinguish route-hook
side effects from the particular assets being aborted.

Alternatives rejected: declare the account permanently unhealthy based on one
failed repeat; declare a machine limit below five when a five-page condition
succeeds; or weaken identity verification. Further control leaves routing attached
but continues all requests, separating routing effects from blocked resources.
Installed Playwright Page.route documentation explicitly notes that enabling
routing disables HTTP cache, making the on/off switch broader than asset filtering.

Raw local rows, timing and capture paths:
[one page](../../debug/round5-t2-one.json),
[five pages](../../debug/round5-t2-five.json),
[five pages OFF](../../debug/round5-t3-five-off.json).


## Confirmed usable worker count for the small IG set

After replacing wildcard routing with selective Chromium heavy-resource handling,
**five pages returned 8/8 complete in 28.1720000000023 seconds**, with blocking
still enabled. Five is therefore the highest configured count demonstrated clean
on this eight-target IG fixture set. Testing 2/3/4 was not necessary to find a
lower safe count: the corrected five-page condition itself passed. This is not
a claim that five pages are universally reliable or that the account was healthy
under all earlier routing modes. A single 50-target Combined check follows.

The repeated one-page failure and successful five-page OFF/corrected runs do not
justify labeling this permanently account-side or inherently unfixable in code.
The confirmed code defect is routing/cache behavior; server-state or machine-load
contributions to every earlier failure remain unquantified.
