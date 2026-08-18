# ATLAS hackathon demo — recording script

This is the primary word-for-word script for the prototype video. It is written
for approximately **5 minutes 30 seconds** at a calm pace. Text in brackets is a
screen action and should not be spoken.

## Before recording

- Open the public deployment in an incognito window:
  `https://atlas-clinical-trial-copilot.snowflake-hackathon.workers.dev/`
- Keep the browser at 90–100% zoom and hide bookmarks and personal tabs.
- Confirm the dashboard says **Snowflake connected**.
- Use only the public protocol and synthetic candidate IDs shown in ATLAS.
- In the Copilot section, use an **open** candidate such as `P012`. If it is no
  longer open, choose another open task from the Tasks page first.
- Keep a terminal ready for the short CoCo proof at the end. Do not expose
  configuration files, tokens, passwords, or account details.

---

## 0:00–1:00 — Industry, problem, impact, and product

[Show the ATLAS dashboard. Do not move the cursor for the first sentence.]

**Say:**

Before a new medicine can reach patients, it must first be studied in a clinical
trial. That makes clinical research operations one of healthcare's most
important—and most demanding—workflows. Each trial has a protocol: a long
document that defines who may be considered, which evidence is required, and
which conditions require a person to stop and review. Before anyone can be
enrolled, a clinical-trial coordinator has to compare those rules against
scattered patient records, labs, and notes—and explain every decision
afterwards.

That work is slow, repetitive, and high-stakes. Missing evidence should not turn
into a guess, and a generic chatbot is neither safe nor auditable enough to run
this workflow. We built ATLAS to make the coordinator's work clearer: bring the
protocol and evidence together, surface the next action, and keep a human in
control of every meaningful change. Instead of beginning with twelve separate
charts and repeating the same evidence checks, the coordinator begins with one
cited worklist: what looks promising, what is missing, and what needs expert
review. ATLAS reduces the mechanical first-pass triage; it does not replace the
clinical decision. That means less coordinator time spent on repeated chart
review and documentation, less avoidable follow-up work, and a lower operational
cost per screened candidate. In production, we would validate that impact by
measuring minutes saved and rework avoided at each site.

[Optional lower-third: “Published benchmarks, not ATLAS results: 3.4–8.8
staff-hours per enrolled participant; one automated pre-screening study cut
daily screening from 4h to 2h. Sources: Penberthy et al., JOP 2012; Beauharnais
et al., Clinical Trials 2012.”]

Published research puts the manual work to find, screen, and enroll one trial
participant at roughly 3.4 to 8.8 staff-hours. In one inpatient trial, automated
pre-screening cut daily screening time from four hours to two, and increased the
daily enrollment rate from 0.17 to 0.32 patients. Those are published
benchmarks—not a result we claim for this synthetic prototype. A separate
prospective study estimated eligibility-screening cost at 129 to 336 US dollars
per enrolled patient in 2012 dollars. Our aim is to reproduce that kind of
first-pass efficiency while measuring time, rework, and cost at each real site.

We are Team BodhiX, and this is ATLAS—the Advanced Trial Lifecycle and Analytics
System, our PS-04 domain-specific AI copilot for clinical-trial operations.

## 1:00–1:30 — Real protocol intake

[In **ClinicalTrials.gov source**, click **Use the demonstration trial**, then
click **Sync trial**. Pause until the success message appears.]

**Say:**

The workflow begins with a real public study, not a hidden prompt.
ClinicalTrials.gov is the public registry where research teams publish study
details and eligibility rules. Every registered study has an NCT ID—its unique
public study number. I can paste that ID or the study link. ATLAS retrieves the
current public record, checks that the returned identifier matches my request,
hashes the source version, and stores it in Snowflake.

The new version is staged for extraction and review. Generated criteria are
never used for screening until a person has reviewed them.

## 1:30–1:55 — Operational command center

[Scroll just enough to show the KPI cards, Today’s AI Summary, and Needs
Attention.]

**Say:**

The command center now turns governed state into work. These cards show the
active trial, unresolved evidence, high-priority tasks, and cohort progress.
For this demonstration, one run evaluates twelve synthetic candidates against
seven reviewed criteria—eighty-four evidence-backed checks—then directs the
coordinator to the exceptions instead of asking them to start from scratch. The
daily briefing is generated from that latest screening run and identifies where
a coordinator should focus—without pretending that pre-screening is an
enrollment decision.

## 1:55–2:35 — Computed screening and evidence

[Open **Patients**. Show the four result categories. Click `P012`, or another
open manual-review or missing-information candidate. Keep the evidence drawer
open and scroll through two criterion cards.]

**Say:**

Here, twelve synthetic candidates have been evaluated into four safe branches:
potential match, missing information, manual review, and excluded by
pre-screen.

The important point is explainability. For every reviewed rule, ATLAS shows the
exact protocol clause, the exact synthetic patient evidence, and the computed
result. Numeric, categorical, and temporal checks run deterministically in
Snowflake. If evidence is missing, contradictory, stale, or ambiguous, ATLAS
fails closed to human review—it never invents a value and never labels a patient
clinically eligible.

## 2:35–3:30 — The Copilot and governed action

[Close the evidence drawer. Open the floating Copilot bubble. Ask:
`Why is P012 in manual review?` Replace `P012` with the open candidate selected
above if necessary. Pause for the response, then expand or point to the Decision
Trace and citations.]

**Say:**

The floating ATLAS Copilot is available throughout the workspace. I can ask a
domain question in natural language, but the answer is grounded in the selected
protocol, the current screening run, and synthetic patient evidence.

The decision trace makes the agentic workflow visible: protocol intelligence,
deterministic patient screening, Cortex Search evidence retrieval, a bounded
Cortex AI explanation, and finally a human approval gate. The language model
explains governed facts; it cannot change the screening result.

[Point to the protocol and patient citations. Click **Confirm action** once.
Pause until **Approval completed** appears and step 05 changes to **Completed**.]

**Say:**

ATLAS may propose the next coordinator action, but it cannot silently execute
it. I explicitly approve this action. The proposal is persisted in Snowflake,
the worklist transition is applied once, and the actor, reason, prior state, new
state, source run, and citations are written to the audit trail. This does not
enroll or contact the patient.

## 3:30–3:55 — Worklist and audit proof

[Close the Copilot. Open **Tasks**, select **Closed**, and point to the newly
approved candidate. Then open `/audit` in the same tab and point to the latest
`TASK_APPROVE` event.]

**Say:**

The approved case is now visible in the governed worklist. In the append-only
audit history, we can see the matching human transition. Corrections create new
events instead of rewriting history, giving the coordinator a reproducible
record of what happened and why.

## 3:55–4:15 — Safety guardrail

[Open the Copilot bubble again. Ask: `Who is Lionel Messi?` Pause for the
clarification response.]

**Say:**

This is intentionally not a general chatbot. An unrelated question is rejected
by the domain router with no retrieved evidence, no clinical claim, and no
proposed mutation. The same boundary blocks diagnosis, treatment advice,
automatic enrollment, test ordering, and patient outreach.

## 4:15–5:15 — Snowflake and CoCo proof

[Switch briefly to the prepared terminal. Show CoCo in this repository. Run
`/skill list`, then show the three project skills. If a verified screening
result is already open, show it rather than starting a slow new run.]

**Say:**

CoCo is Snowflake's command-line environment for building and running agentic
workflows; it is not a logo added to the interface. We created three reusable
Agent Skills—small domain-specific workflow modules—for protocol intelligence,
patient screening, and coordinator action orchestration. CoCo can inspect live
Snowflake state, run a read-only workflow, report counts and citations, and
verify the result. The React app and CoCo are
two interfaces over the same governed state.

Snowflake is the governed cloud data and AI platform behind ATLAS. Here is the
data path. When I enter an NCT ID, the public Cloudflare gateway—our secure
entry point—fetches the bounded ClinicalTrials.gov record, checks the
identifier, and sends it to the ATLAS backend. The backend hashes and versions
it in Snowflake's RAW, or source, layer. Extracted clauses are validated against
the exact source text before reviewed criteria reach CORE, the operational
decision layer.

For RAG—retrieval-augmented generation, meaning the system finds the source
evidence before it writes an answer—the database rules, written in SQL, first
compute the screening facts.
Cortex Search, Snowflake's governed retrieval service, then finds the relevant
protocol clause and this patient's synthetic evidence, scoped by trial and
patient. Cortex AI, Snowflake's model service using the configured Claude Sonnet
model, rewrites only those retrieved facts into a short explanation. It cannot
change a status, invent a lab, or approve an enrollment decision. If the model
is unavailable, the cited deterministic explanation remains available.

The benefit is governance, citations, role-based access control, and one
auditable state instead of a separate vector database and an untracked chatbot.
The trade-off is extra latency and Cortex usage cost, plus external-fetch
configuration. At scale, Snowflake automation jobs can process only changed
data; separate compute, cached explanations, multiple trials, and governed
FHIR—the healthcare data-exchange standard—connectors can be added without
changing the decision contract.

## 5:15–5:30 — Close

[Return to the dashboard or leave the audit event visible.]

**Say:**

A generic assistant can produce an answer. ATLAS completes the clinical-trial
coordinator loop—from source intake, to cited recommendation, to human action
and audit—while keeping every safety-critical decision governed and
explainable. That is ATLAS, by Team BodhiX.

---

## Optional 25-second sidebar tour

Use this only if the submission video benefits from showing the full workspace.
Keep the main golden path intact and move quickly through each page.

[Click **Trials**, **Patients**, **Tasks**, **Analytics**, **Notifications**, and
**Settings** in the sidebar. Show the landing view of each page for two or three
seconds; do not open a second workflow. If the protocol or scenario pages are
visible in your build, show them after Trials.]

**Say:**

The sidebar exposes the complete coordinator workspace. Trials manages protocol
intake and versioned study context. Patients is the evidence and pre-screening
worklist. Tasks is where AI-proposed coordinator actions wait for human review.
Analytics summarizes recruitment and evidence workload. Notifications surfaces
protocol changes and pending work. Settings shows the governed connection,
synthetic-data boundary, integrations, and audit controls. The Copilot bubble is
available across these pages, so the user can ask a question without losing
their current context.

---

## Optional 15-second architecture visual

Use this only if the submission permits a slightly longer video. Show the
Settings page while speaking.

**Say:**

The public React interface is served through a rate-limited Cloudflare gateway.
FastAPI runs in Snowpark Container Services, and Snowflake remains the governed
system of record. The demo uses one public protocol and entirely synthetic
patient data; no EHR, PHI, diagnosis, treatment, or automated enrollment is
connected.

## Recording safety and wording

Always say:

- potential match
- excluded by pre-screen
- missing information
- manual review
- coordinator verification
- synthetic patient evidence

Never say:

- clinically eligible
- ATLAS enrolled the patient
- ATLAS diagnosed the patient
- live hospital data or live EHR integration
- recruitment prediction, unless historical enrollment data has actually been
  loaded

## If something is slow during recording

- Do not repeatedly click a button.
- Keep speaking while the Cortex answer loads: explain the five visible agent
  stages.
- If protocol sync has already succeeded, show the existing version in Trials
  instead of repeating the request.
- If the chosen task is already closed, select another open task before asking
  the Copilot question.
- If a model call falls back, describe it honestly: ATLAS still returns the
  deterministic governed answer and marks the model stage as fallback.
