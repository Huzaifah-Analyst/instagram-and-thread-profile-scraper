# Web SaaS Feasibility Study

Turning MetaInspector Desktop into a multi-tenant website where customers sign
up, pay, and run checks themselves.

20 October 2026. This study uses this project's own measured data, not
estimates. It replaces the optimistic sections of
[API_VS_BROWSER_SCALING_FEASIBILITY.md](API_VS_BROWSER_SCALING_FEASIBILITY.md),
which was written before the live account-suspension evidence existed.

---

## 1. The finding that decides everything

**In the desktop product, the customer supplies the Instagram account and
carries the ban risk. In a web SaaS, we supply the accounts and we carry the
ban risk.** That single change is the whole feasibility question. Everything
else (auth, payments, hosting) is ordinary work.

What this project measured, not guessed:

| Evidence | Source |
| --- | --- |
| **3 of 5 checker accounts suspended** during development-scale testing | P43 and the checker store |
| checker_2 suspended with an explicit account-integrity reason, 9 Oct 2026 | P43 |
| 4 to 8 second pacing per target is required; it is ~28% of run time | P65 |
| Raising workers from 5 to 8 is the exact variable implicated in earlier incidents | P65 |
| Country and joined date **require a logged-in session**; logged out, Instagram shows no profile menu at all | P79 |
| Concurrent runs on one account returned N/A for every row while a solo run kept its data | memory.md Incident 5 and the follow-up |

**Read that last row again.** Meta appears to degrade a session it suspects,
returning blank or possibly placeholder data rather than an error. A SaaS that
silently serves degraded data to paying customers is worse than one that fails
loudly.

### What this means commercially

- **Status checking (alive/dead) is safe to sell.** It needs no login, runs
  logged out, and measured **95 accounts in 44 to 91 seconds**. No account, no
  ban risk, trivial infrastructure.
- **Country and joined date are the risky product.** They need a pool of real
  Meta accounts that will keep getting suspended, each needing its own
  residential proxy so Meta cannot correlate them.

These are two different businesses with two different risk profiles. The study
below assumes we sell both, but **in separate tiers**.

---

## 2. What is genuinely hard, ranked

1. **Account pool economics.** Not the $0.50 per account the older document
   assumed. A usable account needs age, a warm-up period, its own residential
   IP, and replacement when it dies. Our own suspension rate was 60% at
   development volume.
2. **Third-party personal data.** The product's output is "which country does
   this person live in" about people who never consented. Under GDPR that is
   personal data and we would be the controller. A desktop tool the customer
   runs on their own machine keeps that exposure with the customer. A hosted
   service moves it to us.
3. **Platform and legal risk.** Automated collection breaches Meta's terms. A
   public branded website is far more visible than a desktop binary. Realistic
   outcomes range from IP blocks to a cease and desist. Payment processors also
   terminate merchants who attract complaints.
4. **Degraded-data detection.** We need to detect when Meta starts serving junk
   to a session and quarantine it, or we will bill customers for wrong answers.
5. Everything else: auth, billing, dashboards, queueing. Normal work.

**None of 1 to 4 are engineering problems. They are business decisions.** They
should be settled before writing code.

---

## 3. Recommended architecture

Reuses the existing Python extraction engine unchanged, which is the main
asset. Nothing here requires rewriting the scraper.

```
Customer browser
      |
   Next.js frontend  (Vercel)
      |
   FastAPI backend   (VPS)  ----  Postgres  (Supabase or managed)
      |                              |
   Job queue (Redis)                 |
      |                              |
   Worker fleet (separate VPS)  -----+
      |
   Playwright + Chromium containers
      |
   Residential proxy pool  ->  Instagram / Threads
```

- **Frontend: Next.js.** Already in your stack.
- **Backend: FastAPI.** Already in your stack, and the scraper is Python, so
  `src/core` ports across with little change.
- **Database: Postgres.** Supabase is the fastest route because it bundles auth,
  database and row-level security.
- **Queue: Redis plus RQ or Celery.** At MVP volume, a Postgres-backed queue is
  simpler and one less service to run.
- **Workers: separate machines from the API.** Chromium needs roughly 150MB to
  300MB per context. Never run workers on the box serving the website.
- **Secrets: the pool's Meta session cookies are the crown jewels.** Encrypt at
  rest with a managed KMS, never in application config, never in Git.

### Keep the desktop app

The desktop product stays sellable to customers who want to use their own
account and keep their own risk. It is also the honest fallback if the hosted
tier proves unviable.

---

## 4. Authentication and security

Do not build auth from scratch. Use **Supabase Auth**, **Clerk** or
**Auth.js**. Rolling your own session handling is the most common way small
SaaS products get breached.

**Minimum before taking a single payment:**

- Email verification on signup, and password reset that expires.
- Argon2id hashing if any password is ever stored by us.
- Per-account rate limiting on login and on job submission.
- Two-factor for admin accounts at minimum.
- Row-level security so one tenant can never read another's jobs or results.
- Audit log of who ran what and when.
- Encrypted backups, and a tested restore. An untested backup is not a backup.
- A documented deletion path for customer data.

**Specific to this product:**

- The pool's Meta session cookies must be encrypted and access-logged. A leak
  there is an account takeover of real Instagram accounts.
- Results contain third-party personal data. Set a retention window, for
  example 30 days, and delete automatically. Do not keep it forever by default.
- Publish what the service does and does not collect. If EU users or EU data
  subjects are in scope, a privacy policy and a lawful basis are required, not
  optional.

---

## 5. Payments

Two completely different answers depending on who the customers are. **This is
the first question to settle, because it changes the whole billing build.**

### If customers are in Pakistan

Local gateways, PKR, direct settlement to a Pakistani business account.

| Option | Why consider it |
| --- | --- |
| **Safepay** | Best fit for SaaS of the local options: supports recurring subscriptions, payment links and embedded checkout, and is developer-friendly |
| **PayFast** | The broadest general-purpose local gateway, well established |
| **PayPro** | Invoicing and B2B oriented |
| **JazzCash / Easypaisa** | Wallet coverage, which is how most Pakistani consumers actually pay |
| **Raast** | State Bank instant rails, low cost, increasingly expected |

Requirements to be aware of: a registered business (sole proprietorship with an
NTN at minimum), a business bank account, and merchant onboarding that takes
time. Verify current fees and onboarding directly with the provider; published
figures change.

### If customers are international

This is the likelier case, since the existing client is international.

- **Stripe is not available to Pakistani merchants.** Do not plan around it.
- Use a **merchant of record**, which also handles sales tax and VAT for you:
  - **Paddle:** pays out by wire or Payoneer, monthly, around a $100 minimum.
  - **Lemon Squeezy:** lists Pakistan for bank payouts; PayPal separately,
    around a $50 minimum. Payoneer is not listed.
  - **Dodo Payments, Polar, Creem:** newer, onboard individuals, Payoneer
    payouts in some cases.
- **Payoneer** is the common receiving route into a Pakistani bank account.

**A merchant of record is strongly recommended here.** Beyond tax handling, it
means you are not personally holding card data, and the compliance burden sits
with them.

One caution worth planning for: merchants of record review what you sell.
A tool that scrapes a platform in breach of its terms may be refused or
terminated later. Ask before building, not after launch.

---

## 6. Phasing

### Phase 0: Validate, do not build (2 weeks)

The cheapest phase and the one most often skipped.

- Put up a landing page describing the service and collect signups. No product.
- Confirm **who pays, how many, and how much**. The existing client is one
  data point, not a market.
- Resolve the account-pool question (section 1) with a real experiment: run 3
  accounts behind separate residential proxies at realistic volume for two
  weeks and **measure the suspension rate**. This is the single number the
  business model rests on.
- Get a written answer from the intended payment provider about the use case.

**Gate: if the suspension experiment shows accounts dying faster than they can
be economically replaced, stop here and keep selling the desktop app.** That is
a real possible outcome and finding it out now costs two weeks instead of three
months.

### Phase 1: MVP (4 to 6 weeks)

Narrow on purpose.

- Signup, login, email verification.
- Paste or upload usernames, maximum 100 per job.
- **Status-only checking first**, because it needs no account pool and carries
  no ban risk. This proves the entire web product end to end with the easy half.
- Job queue, live progress, results table, CSV export.
- One pricing tier, billed manually if necessary. Do not build metering yet.
- Deploy: frontend on Vercel, API and one worker on a single VPS.

**Gate: do customers return and run a second job?**

### Phase 2: the paid product (4 to 6 weeks)

- Add country and joined date behind the account pool.
- Pool health monitoring, automatic quarantine, and **degraded-data detection**
  so a suspected session is pulled before it serves junk.
- Real billing integration, subscriptions, usage limits.
- Residential proxy rotation, one IP per pool account.
- Retention policy and automatic deletion.

**Gate: unit economics positive after account churn and proxy cost.**

### Phase 3: scale and CI/CD

- Horizontal workers, autoscaling by queue depth.
- GitHub Actions: tests on every PR, staging deploy on merge, production on
  tag. The existing 339-test suite is the foundation and is already strong.
- Error tracking (Sentry), uptime monitoring, structured logs.
- Status page.

Continuous integration should start in Phase 1 in its simple form (tests on
every push). Full CD belongs in Phase 3.

---

## 7. Cost model

Monthly, small scale, roughly 10,000 checks per day.

| Item | Cost |
| --- | --- |
| Frontend hosting | $0 to $20 |
| API server | $10 to $20 |
| Worker servers (2) | $20 to $40 |
| Postgres and auth | $0 to $25 |
| **Residential proxies** | **$50 to $150** |
| **Account pool replacement** | **unknown, the key variable** |
| Monitoring and error tracking | $0 to $25 |
| Payment processing | 5% to 8% of revenue with a merchant of record |
| **Total known** | **roughly $80 to $280** |

The older document put infrastructure at $60 to $90 and claimed a margin above
90%. That ignored proxies, account churn, payment fees and support time.
**Treat the account-replacement line as the deciding cost, and Phase 0 exists
to measure it.**

---

## 8. Honest recommendation

**Feasible, with one condition.** Build it in the order above and let Phase 0
answer the account question before committing to the expensive half.

Specifically:

1. **Sell the status checker as a web service.** Low risk, cheap, no account
   pool, already measured at 95 accounts in under 90 seconds. This is a real
   product on its own.
2. **Treat country and joined date as a premium tier that may not survive.**
   Build it only after the suspension experiment. Price it to absorb account
   churn.
3. **Keep selling the desktop app** to customers who prefer to use their own
   account. It is finished, tested, and it moves the ban risk to the person who
   chose to take it.

**Do not promise the client a timeline before Phase 0 is done.** The honest
statement is that the status product is a 4 to 6 week build, and the
transparency product depends on a two-week experiment that has not run yet.

---

## 9. Open questions for Huzaifah

These change the plan materially and cannot be answered from the code:

1. **Who are the customers, Pakistani or international?** This decides the
   entire payment build.
2. **Whose Instagram accounts power the hosted tier?** Ours, the customer's
   (bring your own login), or a hybrid? Bring-your-own-login removes most of
   the risk in section 1 and is worth serious consideration.
3. **Is this one client asking, or a market?** A single client may be better
   served by a private deployment than a public SaaS.
4. **What is the budget and who carries the running cost** during the months
   before revenue?
5. **Is there an appetite for the legal exposure** in section 2, item 3?

Question 2 is the most important. **A "bring your own Instagram login" web app
is dramatically more feasible than a pooled one**, keeps the risk with the
customer exactly as the desktop app does, and still delivers the website the
client asked for.
