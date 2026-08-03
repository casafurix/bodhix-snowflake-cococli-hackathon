# ATLAS — Product Explanation and Operator Guide

- **Product:** ATLAS (Advanced Trial Lifecycle & Analytics System)
- **Team:** BodhiX
- **Hackathon track:** PS-04 — Domain-Specific AI Copilot
- **Guide scope:** The application deployed as of 2 August 2026

## 1. The product in one sentence

ATLAS helps a clinical-trial coordinator compare public trial
eligibility rules with candidate evidence, identify the next safe review step,
and preserve the reason and source for every result.

The deployed Snowflake objects still use the original `TRIALOPS_*` names because
those are live infrastructure identifiers. They are implementation names, not
the product brand; the user-facing platform is ATLAS.

It is pre-screening decision support. It does not diagnose, recommend treatment,
confirm final eligibility, enroll a participant, order a test, contact a patient,
or replace clinical judgment.

## 2. Product and team identity

**BodhiX is the team name.** It is not the product name.

The product name displayed in the application is **ATLAS**. The
team name is **BodhiX**. In submission material, use
wording such as:

> Team BodhiX built ATLAS for the Snowflake CoCo CLI Hackathon.

Do not refer to the platform itself as BodhiX.

## 3. The problem in ordinary language

A clinical trial has rules describing who may or may not participate. Examples
include an age range, a laboratory threshold, a medication requirement, or the
absence of a recent medical event.

A coordinator normally has to read the study document, find the corresponding
information in candidate records, compare every value, investigate missing or
conflicting information, and document what happened. The work is repetitive,
but it is also sensitive: ambiguous medical language should not be converted
into an automatic decision.

ATLAS performs a controlled first pass:

1. Keep the original public criterion beside its structured interpretation.
2. Evaluate only criteria that have been marked reviewed and machine-evaluable.
3. Compare those criteria with governed candidate evidence.
4. Separate clear results from missing or contradictory evidence.
5. Generate safe coordinator tasks rather than autonomous clinical actions.
6. Require a human reason before a task changes state.
7. Append every system recommendation and human transition to an audit history.

The objective is not to remove the coordinator. It is to let the coordinator
spend less time assembling evidence and more time verifying it.

## 4. What the current demonstration contains

The current build uses the public ClinicalTrials.gov study record
[NCT00749190](https://clinicaltrials.gov/study/NCT00749190), a completed Phase 2
study of BI 10773 in people with Type 2 diabetes receiving metformin.

The application currently contains:

- 20 public eligibility clauses: 7 inclusion and 13 exclusion clauses.
- 7 reviewed, machine-evaluable rules used in the deterministic pre-screen.
- 13 clauses held for coordinator interpretation.
- 12 synthetic candidates across 3 synthetic sites.
- 84 criterion results in the governed bootstrap run: 12 candidates multiplied
  by 7 evaluated rules.
- Four safe candidate branches: potential match, missing information, manual
  review, and excluded by pre-screen.
- Coordinator tasks for all non-excluded candidates.
- Audit events for task generation, exclusions, and human task decisions.
- Site-level evidence workload and a non-mutating staffing scenario.

The selected study is completed and is used as a stable public demonstration
source. The application does not claim that it is recruiting for this study.

## 5. What is real, derived, and synthetic

### Real public source

- The study identifier `NCT00749190`.
- The public study status, brief title, condition, age range, and eligibility
  wording obtained from ClinicalTrials.gov.
- The link from the application to the public study record.

The current build stores a curated snapshot of the public registry record. It
does not yet fetch the record dynamically at runtime, and it does not contain a
complete confidential sponsor protocol document.

### Derived by this project

- The structured concepts, operators, thresholds, and review notes created from
  the public eligibility wording.
- The choice of 7 rules considered safe for deterministic evaluation.
- The decision to hold the other 13 clauses for human interpretation.
- The safe result hierarchy and coordinator action types.

These are product logic, not facts asserted by ClinicalTrials.gov.

### Fully synthetic demonstration data

- Candidate identifiers `P001` through `P012` and their display names.
- Ages, HbA1c values, BMI values, medication data, diagnoses, history flags,
  missing values, and deliberately contradictory evidence.
- Evidence references such as `LAB_RESULTS.P001.HBA1C`.
- Sites `SITE-BLR`, `SITE-DEL`, and `SITE-MUM`.
- Site workload and scenario values.

There is no PHI and no real participant record in the repository or deployment.

### Real working platform behavior

- React pages call the FastAPI API rather than displaying static cards.
- The deployed FastAPI backend reads and writes Snowflake.
- Screening runs execute Snowflake SQL procedures.
- Final branch counts are calculated from criterion results; they are not
  hard-coded frontend totals.
- Task decisions change Snowflake state and create append-only audit events.
- Cortex Search is provisioned over protocol clauses and synthetic evidence.
- The application is packaged and running in Snowpark Container Services.

The most accurate description is:

> A real, deployed workflow applying real public eligibility wording to a fully
> synthetic, non-PHI candidate cohort.

## 6. How the pre-screen works

For each synthetic candidate, Snowflake evaluates the 7 reviewed rules. Each
criterion receives one of four evidence results:

- `MET`: the available evidence satisfies the rule.
- `NOT_MET`: the available evidence does not satisfy the rule.
- `UNKNOWN`: the required governed evidence is missing.
- `CONTRADICTORY`: governed evidence sources disagree.

Snowflake then assigns one overall pre-screen branch in this order:

1. If any evaluated evidence is contradictory, use **Manual review**.
2. Otherwise, if an inclusion rule is not met or an exclusion condition is met,
   use **Excluded by pre-screen**.
3. Otherwise, if evidence is unknown, use **Missing information**.
4. Otherwise, use **Potential match**.

This order is conservative. A contradiction is never hidden behind a more
confident-looking result, and an unknown is never treated as a pass.

### Meaning of the four branches

#### Potential match

The candidate passed all 7 currently evaluated rules. This means only that the
coordinator can continue verification. The other 13 criteria and all required
clinical procedures still need human review.

#### Missing information

At least one required item cannot be found in the synthetic evidence. The safe
next step is to locate existing information, not to invent a value or declare
the candidate eligible.

#### Manual review

Evidence is contradictory, or the workflow requires human interpretation. The
application routes the case to a coordinator instead of resolving ambiguity
with a confidence score.

#### Excluded by pre-screen

A reviewed deterministic rule clearly failed. The application records the
criterion and evidence but creates no outreach task. This is still a cited
pre-screen result, not an independent clinical determination.

## 7. Accessing the deployed application

**Deployment URL:**

<https://iaxsmo-pmwcgsc-yq79089.snowflakecomputing.app/>

1. Open the URL in a browser.
2. Sign in through Snowflake when prompted.
3. Use an account that has the `CTOPS_TEAM_ROLE` role grant.
4. If the service was suspended, the first request automatically starts it.
5. A cold start can briefly show `serviceStatus=PENDING`. Wait approximately a
   minute and refresh the page.

Browser authentication and local CLI authentication are separate. The local
`hackathon_pat` token prevents repeated CLI authentication; it does not remove
the Snowflake sign-in protecting the browser URL.

## 8. Frontend navigation and operation

The left navigation contains eight product routes: Dashboard, Trials, Patients,
Tasks, Analytics, AI Copilot, Notifications, and Settings. On a smaller display, open it with
the menu button in the top-left corner.

### 8.0 Start with your own demonstration inputs

The Dashboard no longer assumes that a protocol has already appeared. Paste a
ClinicalTrials.gov study URL or NCT identifier into **Sync trial**. ATLAS fetches
the live public v2 record, creates a stable content hash, and stores the source
version in Snowflake. A newly synced trial is shown as **Extraction pending**;
it cannot replace the active screened protocol until criteria have been
extracted and reviewed.

Select **Extract** on a pending trial to invoke the Protocol Intelligence agent.
The Cortex response must pass a structured schema and every returned clause
must be an exact passage from the stored public eligibility text. A malformed or
invented clause fails the run without a write. Successful clauses appear as
**Review required** and remain non-machine-evaluable until a human approves
their interpretation.

On Patients, **Import a synthetic cohort** accepts a constrained CSV containing
only aliases and the supported screening fields. Names, contact details,
medical-record identifiers, and PHI must not be uploaded. The cohort is
versioned, normalized, evaluated against reviewed criteria, and exposed through
the same evidence, task, and audit workflow as the built-in cohort.

### 8.1 Command center — `/`

This is the recommended starting page.

The top of the page shows:

- The active study identifier.
- The number of reviewed criteria.
- The number of synthetic candidates.
- The public study title.
- A **Re-run screening** button.

The four summary cards show the current number of potential matches, missing
information cases, manual reviews, and exclusions. The candidate table below
shows the individual branch, evidence completeness, site, and HbA1c value.

#### Filter and search

1. Use the status chips above the table to show one branch or all candidates.
2. Use **Search candidate or site** to search by candidate ID, display name, or
   site ID.
3. Select a candidate row to open the evidence panel.

#### Candidate evidence panel

The panel displays each evaluated criterion as a rail:

- Original criterion wording.
- `MET`, `NOT_MET`, `UNKNOWN`, or `CONTRADICTORY` result.
- Protocol citation.
- Synthetic patient-evidence citation.
- Plain-language explanation.

Use **Open governed worklist** to continue to the task workflow, or **Close
evidence** to return to the queue.

#### ATLAS Copilot

The right rail contains the bounded Coordinator Copilot. It is a focused
chat-style interaction, not unrestricted general chat: ask a question about a
candidate, evidence, sites, the current workload, recruitment, compliance, or
a daily coordinator briefing. The assistant classifies the request, retrieves
relevant protocol/evidence context when Cortex is available, uses the current
governed run, and returns an answer with source identifiers and a copilot-run
ID. Questions outside the clinical-trial operations scope are turned into a
clarification or a safety refusal rather than a guessed answer.

For a candidate explanation, the assistant may propose the existing coordinator
task. **Confirm action** is an explicit human approval: it changes the worklist
state and creates the corresponding audit event. The assistant never creates a
clinical decision, orders a test, or confirms enrollment.

#### Decision trace

Every answer includes an expandable **Decision trace**. It makes the agentic
path inspectable rather than presenting an opaque chatbot response:

1. **Protocol Intelligence** shows that reviewed protocol clauses and their
   citations were used.
2. **Patient Screening** shows that the current deterministic screening run was
   read. The LLM cannot alter this result.
3. **Evidence Retrieval** reports whether Cortex Search returned scoped protocol
   clauses and candidate evidence. It is marked `FALLBACK` when running offline.
4. **Coordinator Copilot** reports whether Snowflake Cortex generated the
   bounded explanation or the governed deterministic response was used instead.
5. **Human Approval Gate** shows whether an action is only proposed or whether
   the request is non-mutating.

The left sidebar can be collapsed from the desktop header or sidebar control;
route icons remain available with accessible labels.

### Local modes

The default local mode is intentionally offline and uses the synthetic fixture.
It proves the decision workflow but labels Cortex Search and Cortex generation
as fallbacks.

To exercise the real governed LLM flow, authenticate through the local
Snowflake connection outside the repository and run:

```bash
ATLAS_DATA_BACKEND=snowflake \
SNOWFLAKE_CONNECTION_NAME=hackathon_pat \
ATLAS_CORTEX_MODEL='SNOWFLAKE.MODELS."CLAUDE-SONNET-4-6"' \
uvicorn app.main:app --app-dir backend --port 8012
```

In this mode, the trace should show `COMPLETED` for Evidence Retrieval and
Coordinator Copilot, and each response is written to `AI.AGENT_RUNS`. The
Snowflake connection and token remain local; no credential is placed in this
repository.

### 8.2 Screening — `/screening`

The Screening route uses the same current Snowflake run and candidate evidence
queue as the Command center. It changes the page emphasis to criterion-level
cohort screening; it is not a separate dataset or second screening engine.

Use it when demonstrating how the overall status is supported by individual
criterion records.

### 8.3 Protocols — `/protocols`

This page is the source-to-rule register.

The header shows the study ID, document hash, public source link, and extraction
record. Summary cards show:

- Total extracted clauses.
- Clauses reviewed for deterministic screening.
- Clauses held for human interpretation.

#### Review the criterion register

1. Select **All**, **Reviewed**, or **Manual review**.
2. Search by criterion ID, wording, or clinical concept.
3. Read the public source clause in the middle column.
4. Inspect the operator or coordinator-interpretation label on the right.
5. Read the review note explaining why the clause is automated or held.
6. Use **Open public ClinicalTrials.gov record** to compare the snapshot with its
   public source.

Only clauses marked both reviewed and machine-evaluable participate in the
current pre-screen.

### 8.4 Worklist — `/worklist`

The Worklist is where a human changes workflow state.

Excluded candidates do not receive outreach tasks. Potential matches, missing
information cases, and manual-review cases receive safe coordinator tasks.

#### Review and decide a task

1. Start with the **Open** filter.
2. Select a task from the left side.
3. Keep the original recommendation and reason visible in the decision panel.
4. Choose **Approve**, **Edit**, **Reject**, or **Dismiss**.
5. For **Edit**, choose a replacement safe action.
6. Enter a decision reason of at least three characters. A useful reason should
   say what was checked and why the transition is appropriate.
7. Select **Record decision**.
8. Wait for **Decision recorded** before leaving the panel.

#### Exact decision behavior

- **Approve:** marks the task approved and adds the case to a pending coordinator
  verification queue. It does not enroll or contact the candidate.
- **Edit:** changes the proposed safe action, writes an audit event, and leaves
  the task open so it can receive a later final decision.
- **Reject:** closes the task as rejected and records the reason.
- **Dismiss:** closes the task as dismissed and records the reason.

Use **Closed** to inspect approved, rejected, and dismissed tasks. Use **All** to
see open and closed tasks together. Only an open task can transition.

On the deployed service, the backend prefers the Snowflake-authenticated username
forwarded by the ingress for audit attribution. In local development, the demo
actor is used when that identity header is absent.

### 8.5 Operations — `/operations`

This page groups the current screening results by synthetic site.

For every site it shows:

- Candidate count.
- Average evidence completeness.
- Potential, missing, manual-review, and excluded counts.
- Number of cases that need evidence resolution.

The page reports only the observed workload of the current synthetic cohort. It
does not currently forecast recruitment or claim historical site performance.

### 8.6 Scenario lab — `/scenarios`

This page explores staffing assumptions without modifying governed data.

1. Set **Additional coordinator capacity** from 0 to 4.
2. Set the percentage of cases resolved per available shift.
3. Read the estimated weeks needed to clear the present missing-information and
   manual-review backlog.
4. Check the displayed formula to understand the result.

The browser performs this calculation. Moving either slider does not change
patients, screening results, tasks, or audit history. It is an evidence-workload
scenario, not an enrollment forecast.

### 8.7 Audit history — `/audit`

The audit page lists the newest events first. Each record contains the event
type, actor, reason, entity, source screening run, and time.

The design is append-only: a correction creates a new event rather than silently
rewriting an earlier event. Use this page immediately after a Worklist decision
to demonstrate that the human action was persisted in Snowflake.

## 9. Re-running screening safely

The **Re-run screening** button starts a real Snowflake procedure. It:

1. Creates a new governed run identifier.
2. Re-evaluates every synthetic candidate against the 7 reviewed rules.
3. Writes criterion and overall results.
4. Generates tasks for non-excluded candidates.
5. Records task-generation and exclusion audit events.
6. Refreshes the dashboard, worklist, operations, and audit data.

The public criteria and synthetic cohort are stable, so the branch counts should
remain stable unless the underlying data or rules change. The new run becomes
the current worklist context. Earlier audit history is retained.

Do not press the button repeatedly during a presentation unless the intention is
to demonstrate run creation. One click is sufficient; wait for the spinner to
stop and the refreshed run ID to appear.

## 10. Recommended end-to-end demonstration

The following walkthrough fits the current build without claiming future scope:

1. **Command center:** establish the real public study, 12 synthetic candidates,
   and four safe branches.
2. **Protocols:** show one reviewed numeric rule and one clause held for human
   interpretation.
3. **Candidate P001:** show a potential match with complete cited evidence.
4. **Candidate P003:** show missing HbA1c evidence and the `UNKNOWN` result.
5. **Candidate P004:** show deliberately contradictory HbA1c evidence and the
   manual-review branch.
6. **Candidate P010:** show the age pre-screen exclusion.
7. **Worklist:** select one open task, enter a meaningful reason, and approve,
   edit, reject, or dismiss it.
8. **Audit history:** show the newly appended human decision.
9. **Operations:** show how the same governed run rolls up by synthetic site.
10. **Scenario lab:** change capacity and show that the calculation does not
    mutate the governed run.

## 11. Current technical architecture in plain language

```text
Browser
  -> React frontend
  -> same-origin FastAPI endpoints
  -> governed Snowflake tables, views, and procedures

Public study snapshot + synthetic evidence
  -> deterministic criterion evaluation
  -> safe candidate branch
  -> coordinator task
  -> human decision
  -> append-only audit event
```

- **React and TypeScript** render the user interface.
- **FastAPI** validates requests and provides a controlled API boundary.
- **Snowflake** stores the study snapshot, synthetic evidence, screening runs,
  tasks, and audit history.
- **Snowpark Container Services** hosts the production container.
- **Cortex Search** indexes protocol clauses and synthetic evidence for governed
  retrieval. ATLAS shows the retrieved evidence passages beside a grounded
  copilot answer when the Snowflake-backed Cortex path is available.
- **CoCo (Cortex Code)** was used as an engineering and Snowflake operations
  agent. It is not an invisible model making final candidate decisions.

The screening branch is deterministic and inspectable. AI assistance does not
silently override the stored rule or evidence result.

## 12. Operating the deployment from the CLI

Use the local non-interactive Snowflake connection:

```bash
snow connection test -c hackathon_pat
```

### Check service status

```bash
snow sql -c hackathon_pat -q \
  "SHOW SERVICES LIKE 'TRIALOPS_SERVICE' IN SCHEMA CTOPS_HACKATHON.APP"

snow sql -c hackathon_pat -q \
  "SELECT SYSTEM\$GET_SERVICE_STATUS('CTOPS_HACKATHON.APP.TRIALOPS_SERVICE')"
```

A healthy container reports `READY` and `Running`.

### Check application health

After signing in through the browser, open:

```text
https://iaxsmo-pmwcgsc-yq79089.snowflakecomputing.app/api/health
```

The deployed response should identify the `snowflake` backend and governed
account context.

### View recent container logs

```bash
snow spcs service logs TRIALOPS_SERVICE \
  -c hackathon_pat --role CTOPS_TEAM_ROLE \
  --database CTOPS_HACKATHON --schema APP \
  --container-name trialops --instance-id 0 --num-lines 100
```

### Resume explicitly

Normally, opening the URL resumes the service. It can also be resumed with:

```bash
snow sql -c hackathon_pat -q \
  "ALTER SERVICE CTOPS_HACKATHON.APP.TRIALOPS_SERVICE RESUME"
```

### Suspend after use

The public endpoint does not reliably signal ingress idleness for automatic
service suspension. Suspend the service after development or a demonstration:

```bash
snow sql -c hackathon_pat -q \
  "ALTER SERVICE CTOPS_HACKATHON.APP.TRIALOPS_SERVICE SUSPEND"
```

The service uses one `CPU_X64_XS` node while running. Suspending the service lets
the compute pool become idle and auto-suspend, protecting the hackathon balance.

## 13. Running the current application locally

The ignored root `.env` should contain the non-secret connection alias:

```dotenv
SNOWFLAKE_CONNECTION_NAME=hackathon_pat
```

The token itself remains outside the repository in the private Snowflake
credentials directory.

Start the backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open <http://127.0.0.1:5173>. The local API documentation is available at
<http://127.0.0.1:8000/docs>.

## 14. Troubleshooting

### The browser shows `serviceStatus=PENDING`

The suspended service is starting. Wait approximately one minute and refresh.
Use the status command above if it does not become ready.

### The page says ATLAS is offline

The frontend could not obtain `/api/dashboard`. For local development, confirm
FastAPI is running on port 8000. For production, check the service status and
container logs.

### A task decision fails

- Confirm that the task is still open.
- Confirm that the reason has at least three characters.
- For **Edit**, choose a replacement action.
- Refresh the Worklist before retrying if another user may have changed it.

### The command center and Screening page look similar

This is expected in the current build. Both expose the same current run and
candidate queue, with different explanatory headings.

### The CLI asks for browser authentication

Confirm the command uses `-c hackathon_pat`, not `-c hackathon`. The PAT is local
and private. Browser access to the deployed application still requires Snowflake
sign-in.

## 15. Current boundaries and honest submission claims

Implemented now:

- Public study snapshot and source-linked eligibility register.
- Reviewed deterministic rules and all four safe result branches.
- Criterion-level protocol and synthetic-evidence citations.
- Snowflake-computed runs, tasks, human decisions, and audit history.
- Site evidence workload and a transparent staffing scenario.
- React/FastAPI application deployed in Snowpark Container Services.
- Cortex Search, the bounded Coordinator Copilot, and reproducible CoCo project
  workflows.

Not implemented in the current frontend:

- A live ClinicalTrials.gov ingestion button or scheduled API sync.
- Real EHR, FHIR, EDC, or CTMS connectivity.
- Real patient data or real trial-site performance data.
- Final eligibility, enrollment, outreach, diagnosis, or treatment decisions.
- Historical recruitment or dropout forecasting.
- Visit, consent, protocol-deviation, or sponsor-portfolio modules.
- Arbitrary SQL generation or unrestricted general-purpose chat. The copilot is
  intentionally limited to governed TrialOps intents.

Do not present items in the second list as live capabilities. They are possible
future integrations or architecture targets.

## 16. Short explanation for a first-time viewer

> ATLAS is a clinical-trial coordinator workspace built by Team
> BodhiX. It takes real public trial eligibility wording and compares the reviewed
> rules with fictional candidate records. It shows possible matches, clear
> pre-screen exclusions, missing information, and contradictions. Every result
> includes its source, and a human must record a reason before workflow state
> changes. The system is deployed on Snowflake, but it contains no real patient
> information and makes no final clinical or enrollment decision.
