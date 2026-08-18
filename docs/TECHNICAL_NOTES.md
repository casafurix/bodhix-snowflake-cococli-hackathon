# ATLAS technical notes

This is the short technical explanation to use when a judge asks how the
Snowflake and CoCo pieces work.

## What happens when a trial is synced?

1. The coordinator enters an NCT ID or ClinicalTrials.gov URL in the React UI.
2. The Cloudflare Worker validates the ID and fetches the bounded public
   ClinicalTrials.gov v2 JSON record. The browser never receives Snowflake
   credentials.
3. The Worker forwards the record through a private authenticated route to the
   FastAPI service. FastAPI checks that the payload's NCT ID matches the request,
   hashes the source, and stores a version in Snowflake `RAW`.
4. Protocol processing extracts eligibility clauses. Model-produced clauses are
   schema-validated and must match exact source text; malformed or ambiguous
   output is rejected or sent for human review.
5. Reviewed criteria are stored in `CORE` and become the only criteria that can
   drive screening.

The public gateway exists because this Snowflake trial account cannot make
arbitrary external calls directly. In a production account, an approved
external-access integration or a scheduled ingestion service could perform the
same step inside the governed environment.

## What kind of RAG is used?

ATLAS uses **bounded, citation-first RAG**:

1. SQL computes the candidate's criterion-level facts and produces a draft
   explanation with protocol and patient source IDs.
2. Cortex Search retrieves up to five relevant records from the governed
   evidence corpus: protocol clauses and the selected patient's synthetic notes,
   labs, diagnoses, or medications. Filters keep retrieval scoped to the trial
   and patient.
3. Cortex AI (`AI_COMPLETE`, configured as `claude-sonnet-4-6`) rewrites only
   that deterministic draft and retrieved evidence into plain language.
4. The response returns the retrieved evidence and citations to the UI. If
   Cortex is unavailable, ATLAS keeps the safe deterministic explanation.

This is not open-web RAG and it is not an LLM eligibility judge. SQL/Snowpark
owns numeric, categorical, Boolean, and temporal decisions. Unknown or
contradictory evidence fails closed to `MISSING_INFORMATION` or `MANUAL_REVIEW`.

## Why Snowflake and CoCo matter

- Snowflake keeps source data, criteria, evidence, results, tasks, and audit
  events under one RBAC-controlled system of record.
- Cortex Search provides governed retrieval without copying clinical evidence
  into a separate vector database.
- Cortex AI provides explanations close to the data, with model access and
  usage visible to Snowflake administrators.
- CoCo CLI supplies reusable domain skills: protocol intelligence, patient
  screening, and coordinator action orchestration. It can inspect, run, and
  verify the same Snowflake state used by the application.
- Human approval is persisted as a state transition and append-only audit event,
  rather than being an untracked chat response.

## Trade-offs in the prototype

**Benefits:** strong governance, reproducible decisions, source citations,
clear separation between deterministic rules and generative language, and one
shared state for the UI and CoCo.

**Costs:** Cortex Search indexing and AI calls add latency and credits; model
availability and permissions can vary by Snowflake account; external protocol
fetching needs a gateway or external-access integration; and the current demo
uses one public protocol plus synthetic patients rather than a production EHR.

## How this scales

- Add protocols by versioned ingestion; partition Search by protocol, site, and
  evidence type.
- Move extraction and screening into Snowpark tasks or streams so new protocol
  versions and patient evidence trigger incremental runs instead of full
  reprocessing.
- Use separate warehouses/resource monitors for ingestion, screening, and
  interactive copilot traffic.
- Add multiple trials and patient matching by reusing the same criterion and
  evidence schemas; add FHIR/EHR connectors only behind governed ingestion.
- Keep model calls asynchronous and cache explanations by run, question, and
  evidence hash. Scale the FastAPI service horizontally while Snowflake remains
  the source of truth.
- Add stronger role separation, retention policies, monitoring, and an approval
  queue before handling real PHI.

