# Submission readiness checklist

## Working and verified

- [x] PS-04 selected with one clear coordinator workflow.
- [x] Public ClinicalTrials.gov protocol and fully synthetic patient/site data.
- [x] Three discoverable CoCo project skills.
- [x] Reproducible read-only CoCo evidence over live Snowflake state.
- [x] Snowflake RBAC, warehouse resource monitor, governed schemas, and audit data.
- [x] Cortex Search service over protocol clauses and synthetic evidence.
- [x] Deterministic screening with all four safe branches and two-sided citations.
- [x] Idempotent screening/task procedures and append-only audit events.
- [x] React routes for command center, protocols, screening, worklist, operations,
  scenario lab, and audit history.
- [x] FastAPI/Snowflake API for protocol, patients, screening, tasks, decisions,
  audit history, and site workload.
- [x] One production Docker image with no embedded Snowflake credential.
- [x] Snowpark Container Services HTTPS deployment and authenticated smoke test.
- [x] Public Cloudflare gateway implemented with server-side Snowflake
  authentication and request limits.
- [x] Backend tests, frontend lint/build, and dependency audit pass.

## Human submission work still required

- [ ] Open the deployed link with both team accounts and confirm each has
  `CTOPS_TEAM_ROLE` selected/available.
- [ ] Record the 90-second product walkthrough and CoCo proof.
- [ ] Capture screenshots after the final human decision and audit event.
- [ ] Complete the supplied presentation template with verified claims only.
- [ ] Upload the video and deck, then verify their sharing permissions.
- [x] Verify the anonymous Cloudflare URL and live Cortex response outside a
  Snowflake session.
- [ ] Add the anonymous Cloudflare URL to the submission form.
- [ ] Verify the repository, deployment, video, and deck links in an incognito
  browser before the 6 August deadline.

## Current deployment

- Public URL: `https://atlas-clinical-trial-copilot.snowflake-hackathon.workers.dev/`
- Native Snowflake URL: `https://iaxsmo-pmwcgsc-yq79089.snowflakecomputing.app/`
- Service: `CTOPS_HACKATHON.APP.TRIALOPS_SERVICE`
- Compute pool: `CTOPS_COMPUTE_POOL` (`CPU_X64_XS`, one node)
- Public gateway PAT expires: `2026-09-18` and is restricted to `CTOPS_TEAM_ROLE`.
- Cost control during judging: keep the service available and monitor Snowflake
  credits; suspend it after the judging window.
