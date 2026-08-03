# ATLAS — demo script

## One-sentence pitch

ATLAS turns a clinical-trial protocol and fragmented patient evidence into a
cited coordinator worklist, while keeping eligibility decisions and workflow
changes human-controlled and auditable in Snowflake.

## 90-second product walkthrough

**0:00–0:12 — Pain.** A coordinator repeatedly compares long protocol clauses
against demographics, medication, labs, and notes. Missing or contradictory
evidence is easy to overlook, and the reasoning is difficult to audit later.

**0:12–0:25 — Protocol intelligence.** Open **Protocols**. Show the public
ClinicalTrials.gov source, its document hash, 20 preserved clauses, 7 reviewed
machine-evaluable criteria, and 13 clauses intentionally held for human
interpretation. Emphasize that compound or sensitive rules are not simplified.

**0:25–0:43 — Computed screening.** Open **Screening** and re-run the synthetic
cohort. Point to the four branches computed in Snowflake: 3 potential matches,
2 missing-information cases, 2 manual-review cases, and 5 cited exclusions.

**0:43–0:58 — Evidence rail.** Open Candidate 003 or Candidate 004. Walk one row
from the exact protocol clause to the exact synthetic source record and then to
`UNKNOWN` or `CONTRADICTORY`. Say: “The system fails closed; it does not invent
missing evidence or turn a confidence score into eligibility.”

**0:58–1:15 — Governed action.** Open **Worklist**, select one open task, choose
approve/edit/reject/dismiss, and enter a real verification reason. Show that the
original recommendation remains visible. Approving adds a case only to a
coordinator verification queue; it does not enroll or contact anyone.

**1:15–1:25 — Audit.** Open **Audit history** and show the new actor, reason,
prior/new state, source run, and timestamp. Corrections append events instead of
rewriting history.

**1:25–1:30 — Close.** “A generic chatbot can suggest. ATLAS creates a
reproducible, cited, human-gated workflow where the enterprise data already
lives.”

## CoCo proof after the product walkthrough

1. Run `cortex -c hackathon --workdir "$PWD"`.
2. Show `/skill list` discovering the three repository skills.
3. Invoke `patient-screening` with the read-only prompt in `docs/coco-runbook.md`.
4. Show that CoCo independently reads the latest Snowflake run, reports all four
   branches, verifies that all 12 patients are synthetic, and returns two-sided
   citations.
5. Explain the boundary: CoCo builds, operates, and verifies the workflow; the
   React/FastAPI application is the stable end-user runtime; both use the same
   governed Snowflake state.

## Safe demo choices

- Use only the public NCT00749190 protocol and visibly synthetic candidate IDs.
- Do not call a candidate “eligible”; say “potential match for coordinator review.”
- Make a human decision only while recording the demo, with an honest reason.
- Do not show `~/.snowflake`, Keychain, OAuth tokens, or account credentials.
- Suspend the Snowpark Container Services service after recording to control cost.
