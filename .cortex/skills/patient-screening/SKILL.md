---
name: patient-screening
description: Pre-screen a synthetic patient cohort against reviewed protocol criteria using deterministic structured rules plus grounded unstructured evidence, with criterion-level citations and safe uncertainty handling.
tools:
  - Read
  - Write
  - Grep
  - Bash
  - snowflake_sql_execute
  - snowflake_object_search
---

# Patient Screening

## When to use

Use this skill when constructing patient evidence, running or rerunning trial pre-screening, explaining a screening result, or testing eligibility rule behavior.

## Required behavior

1. Read `AGENTS.md` and use only human-reviewed protocol criteria.
2. Confirm the cohort is synthetic and the required patient, diagnosis, medication, lab, and note sources are available.
3. Normalize structured evidence, including units and observation timestamps, before comparison.
4. Use SQL or Snowpark for deterministic numeric, categorical, Boolean, and temporal evaluation.
5. Use Cortex Search only when unstructured evidence is required. Capture the exact note excerpt and source identifier.
6. Produce one of `MET`, `NOT_MET`, `UNKNOWN`, or `CONTRADICTORY` for every criterion.
7. Derive the overall pre-screen status using explicit rules:
   - `EXCLUDED`: a reviewed exclusion criterion is met or a required inclusion criterion is not met.
   - `MISSING_INFORMATION`: required evidence is unknown and no exclusion is established.
   - `MANUAL_REVIEW`: evidence is contradictory, stale, ambiguous, or a criterion is not machine-evaluable.
   - `POTENTIAL_MATCH`: all required machine-evaluable criteria pass and no exclusion is established.
8. Persist criterion-level results, evidence citations, run identifier, rule version, and overall status idempotently.
9. Never convert a confidence score into confirmed clinical eligibility.

## Guardrails

- Fail closed to `MANUAL_REVIEW` or `MISSING_INFORMATION`.
- Do not infer absent diagnoses, medications, pregnancy status, consent, or biomarkers.
- Do not use unsupported external facts to fill missing patient evidence.
- Explanations must agree with the stored deterministic result.

## Completion report

Return cohort size, status distribution, unknown/contradictory counts, validation failures, and representative protocol and patient citations.
