---
name: protocol-intelligence
description: Parse a clinical-trial protocol, extract cited and machine-readable eligibility criteria, validate them, and persist them to Snowflake for coordinator-reviewed patient pre-screening.
tools:
  - Read
  - Write
  - Grep
  - Bash
  - snowflake_sql_execute
  - snowflake_object_search
---

# Protocol Intelligence

## When to use

Use this skill when ingesting or reprocessing a trial protocol, extracting inclusion or exclusion criteria, or preparing criteria for patient pre-screening.

## Required behavior

1. Read `AGENTS.md` and the selected protocol metadata before acting.
2. Confirm the Snowflake connection and required stage/tables exist. Create missing project objects only after showing the plan.
3. Store the source document with a stable protocol identifier and content hash.
4. Parse the protocol using Snowflake document processing. Preserve page, section, and exact clause text.
5. Extract each criterion into a validated schema containing at least:
   - `criterion_id`
   - `protocol_id`
   - `criterion_type` (`INCLUSION` or `EXCLUSION`)
   - `source_clause`
   - `source_location`
   - `clinical_concept`
   - `operator`
   - `threshold_value`
   - `threshold_unit`
   - `temporal_window`
   - `required_evidence`
   - `machine_evaluable`
   - `review_status`
6. Reject malformed model output. Route nested, ambiguous, or unsupported logic to `MANUAL_REVIEW` instead of guessing.
7. Use idempotent `MERGE` behavior keyed by protocol, document hash, and criterion identifier.
8. Write a processing record containing model/function used, timestamps, warnings, and counts.

## Guardrails

- Extraction does not make patient-specific decisions.
- Never silently simplify AND/OR logic, negation, temporal constraints, units, or exceptions.
- Do not use external medical knowledge to rewrite the protocol requirement.
- Criteria are drafts until a human marks them reviewed.

## Completion report

Return the protocol identifier, extracted/rejected/manual-review counts, Snowflake objects changed, and sample clause citations.
