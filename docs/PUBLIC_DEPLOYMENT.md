# Public ATLAS deployment — beginner guide

This document explains, in simple terms, how ATLAS was made publicly available,
why judges no longer need a Snowflake login, how to deploy an update, where the
credentials live, and how to monitor cost.

## Start here: what is deployed?

ATLAS has two deployed parts:

| Part | What it does | Where it runs | Who pays |
| --- | --- | --- | --- |
| Public gateway and frontend | Shows the React interface and safely forwards API requests | Cloudflare Worker | Free tier for normal demo traffic |
| Application and AI backend | Runs FastAPI, reads governed data, calls Cortex AI, and stores audit records | Snowflake | Hackathon Snowflake credits |

The link submitted to judges is:

<https://atlas-clinical-trial-copilot.snowflake-hackathon.workers.dev/>

The original Snowflake link still exists, but it asks users to sign in. Judges
do not need that link.

### A few useful terms

- **Worker:** a small program that runs on Cloudflare's edge network.
- **Wrangler:** Cloudflare's command-line tool for testing and deploying Workers.
- **PAT:** a Snowflake programmatic access token used by one service identity.
- **Secret:** an encrypted value stored by Cloudflare; it is not included in the
  browser code or repository.
- **Origin:** the private application behind the public gateway. Here, the origin
  is the Snowpark Container Services URL.

## How one request travels through the platform

ATLAS uses a free Cloudflare Worker as its anonymous public entry point while
Snowflake remains the governed application and AI data plane.

```text
Judge's browser
    -> Cloudflare Worker + Vite static assets
    -> authenticated /api/* proxy
    -> Snowpark Container Services (FastAPI)
    -> Snowflake tables, Cortex AI, and Cortex Search
```

For a normal page such as `/trials`, Cloudflare directly returns the compiled
React files. For an API call such as `/api/copilot/query`, the Worker adds the
Snowflake service credential on the server side and forwards the request to
FastAPI. The response then travels back through Cloudflare to the browser.

This is why the public URL does not display the Snowflake login page: the browser
is talking to Cloudflare, while Cloudflare authenticates to Snowflake privately.

The browser never receives a Snowflake password or token. Cloudflare adds a
role-restricted Snowflake programmatic access token (PAT) only while proxying an
API request. The PAT is an encrypted Cloudflare secret and is not stored in Git,
the frontend bundle, `wrangler.jsonc`, or a deployment log.

## Public-demo safeguards

- Only `GET`, `HEAD`, `POST`, and `OPTIONS` are accepted by the gateway.
- Requests are limited per client to 120 API calls, 20 mutations, and 8 Copilot
  questions per minute.
- Bodies larger than 512 KiB are rejected.
- Browser-supplied authorization and Snowflake identity headers are discarded.
- Redirects are not followed, preventing accidental credential forwarding.
- API responses use `Cache-Control: no-store`.
- The application remains decision support over synthetic patient data. It does
  not diagnose, confirm eligibility, enroll patients, or contain PHI.

Cloudflare rate-limit counters are eventually consistent and local to a
Cloudflare location. They are suitable for protecting a public hackathon demo,
not for billing or clinical security enforcement.

## What we configured, step by step

1. The existing Vite frontend was built into static HTML, CSS, and JavaScript.
2. A Worker was added in `cloudflare/worker.mjs`.
3. `wrangler.jsonc` was configured to serve the frontend and run the Worker for
   `/api/*` requests.
4. The existing Snowflake service URL was stored as a normal configuration
   value named `SNOWFLAKE_ORIGIN`.
5. A dedicated Snowflake PAT was restricted to `CTOPS_TEAM_ROLE`.
6. The PAT was uploaded as the encrypted Cloudflare secret `SNOWFLAKE_PAT`.
7. Rate limits and request-size checks were added to protect the public demo.
8. Wrangler deployed the Worker to the permanent `workers.dev` URL.
9. The public page, Snowflake health endpoint, and a grounded Cortex Copilot
   answer were tested after deployment.

No password, PAT, or private key was committed to Git.

## One-time setup

Authenticate Wrangler:

```bash
npx --yes wrangler@latest login
```

Create a dedicated Snowflake PAT using an administrator connection. Restrict it
to `CTOPS_TEAM_ROLE` and choose an expiry that covers the complete judging
window. The secret returned by Snowflake is shown only once.

The dedicated `CTOPS_CLI_PAT_POLICY` must permit that lifetime. The current
deployment uses a 45-day default and a 60-day maximum while retaining mandatory
role restriction for service-user PATs:

```sql
ALTER AUTHENTICATION POLICY CTOPS_HACKATHON.APP.CTOPS_CLI_PAT_POLICY
  SET PAT_POLICY = (
    DEFAULT_EXPIRY_IN_DAYS = 45
    MAX_EXPIRY_IN_DAYS = 60
    NETWORK_POLICY_EVALUATION = ENFORCED_NOT_REQUIRED
    REQUIRE_ROLE_RESTRICTION_FOR_SERVICE_USERS = TRUE
  );
```

```sql
ALTER USER CTOPS_CLI_SERVICE ADD PROGRAMMATIC ACCESS TOKEN ATLAS_PUBLIC_GATEWAY
  ROLE_RESTRICTION = 'CTOPS_TEAM_ROLE'
  DAYS_TO_EXPIRY = 45
  COMMENT = 'Cloudflare public ATLAS gateway; rotate after judging';
```

Pipe the returned value directly to Wrangler or enter it interactively. Never
place it in `.env`, `wrangler.jsonc`, a shell history entry, or Git:

```bash
npx --yes wrangler@latest secret put SNOWFLAKE_PAT
```

Cloudflare stores the value as an encrypted Worker secret. Confirm that the
expiry covers the judging window:

```sql
SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER CTOPS_CLI_SERVICE;
```

## Deploying an update

You normally do not repeat the one-time account and PAT setup. For a frontend or
Cloudflare gateway change, follow these steps from the repository root.

### 1. Confirm Cloudflare login

```bash
npx --yes wrangler@latest whoami
```

### 2. Test and build

```bash
node --test cloudflare/worker.test.mjs
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run build
```

### 3. Validate without publishing

```bash
npx --yes wrangler@latest deploy --dry-run
```

### 4. Publish

```bash
npx --yes wrangler@latest deploy
```

Wrangler prints the public `workers.dev` URL. The Worker serves the built React
application and sends only `/api/*` to Snowflake.

Current public URL:

<https://atlas-clinical-trial-copilot.snowflake-hackathon.workers.dev/>

Wrangler prints a version ID after every successful deploy. Keep the previous
version available so the Worker can be rolled back if a new release fails.

## Verification

Test the printed URL in an incognito window that has no Snowflake session:

1. Confirm the Dashboard renders without a login redirect.
2. Open Trials, Patients, Tasks, Analytics, and Notifications.
3. Open the floating ATLAS Copilot and ask `Explain patient P001 with cited protocol and patient evidence.`.
4. Confirm evidence citations and safe decision language are shown.
5. Open `<public-url>/api/health` and confirm the response reports the Snowflake backend.
6. Confirm the native Snowflake URL still requires Snowflake authentication.

## Month-long operation

The Cloudflare Worker does not idle-sleep. The Snowflake service must remain
running for live API and Cortex responses. During the judging window:

- keep `CTOPS_HACKATHON.APP.TRIALOPS_SERVICE` running;
- check the PAT expiry and service health daily;
- monitor the `CTOPS_COMPUTE_POOL`, warehouse, and Cortex credit usage;
- do not use a cron-based keepalive; and
- rotate or remove the public PAT after judging.

To revoke the public gateway without changing the application, remove or disable
its PAT in Snowflake. To stop compute spend after judging, suspend the Snowflake
service and compute pool.

## Checking cost and remaining credits

There are two separate places to check.

### Cloudflare

Open the Cloudflare dashboard, then select **Workers & Pages →
atlas-clinical-trial-copilot → Metrics**. This shows requests, errors, and CPU
time. Under normal hackathon traffic the Worker stays within the free plan; the
dashboard is the source of truth for current usage.

### Snowflake

Open Snowsight, switch to `ACCOUNTADMIN`, and select **Admin → Cost management →
Account Overview**. This is the easiest view of incurred cost and credit usage.
For trial-style accounts, `ACCOUNTADMIN` can also see a remaining-balance tile in
the left navigation. Snowflake cost data is delayed, so the most recent hours may
not yet be visible.

To see daily billed credits by product, run:

```sql
SELECT
  usage_date,
  service_type,
  ROUND(credits_billed, 6) AS credits_billed
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
WHERE usage_date >= DATEADD('day', -30, CURRENT_DATE())
  AND credits_billed <> 0
ORDER BY usage_date DESC, credits_billed DESC;
```

To isolate the ATLAS container pool:

```sql
SELECT
  DATE_TRUNC('day', start_time)::DATE AS usage_date,
  compute_pool_name,
  ROUND(SUM(credits_used), 6) AS credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.SNOWPARK_CONTAINER_SERVICES_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
  AND compute_pool_name = 'CTOPS_COMPUTE_POOL'
GROUP BY 1, 2
ORDER BY 1 DESC;
```

To see Cortex model usage:

```sql
SELECT
  DATE_TRUNC('day', start_time)::DATE AS usage_date,
  function_name,
  model_name,
  ROUND(SUM(credits), 6) AS credits,
  COUNT(DISTINCT query_id) AS query_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 4 DESC;
```

### Verified snapshot on 5 August 2026

From 1 August through the latest available metering data:

| Category | Billed credits |
| --- | ---: |
| Snowpark Container Services | 4.407183 |
| Warehouses | 2.542655 |
| CoCo CLI | 1.526661 |
| CoCo in Snowsight | 0.126203 |
| Cortex AI Functions | 0.100317 |
| Other measured services | about 0.001 |
| **Total** | **about 8.704** |

The container pool is currently the largest ATLAS deployment cost. Cortex model
calls are comparatively small. Credits are not the same as US dollars: use the
Snowsight promotional-balance view for the actual remaining dollar balance.

## Updating the deployment

Frontend or gateway-only changes need another frontend build and Wrangler
deploy. Backend changes must first be built and deployed to Snowpark Container
Services, then the unchanged public gateway will begin using the upgraded API.

Do not commit generated `frontend/dist`, `.wrangler`, `.dev.vars`, or any PAT.
