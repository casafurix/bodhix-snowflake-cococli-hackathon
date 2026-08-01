---
name: coordinator-action-orchestrator
description: Convert persisted clinical-trial pre-screening results into safe, idempotent coordinator tasks and an append-only audit trail with human approval gates.
tools:
  - Read
  - Write
  - Grep
  - Bash
  - snowflake_sql_execute
  - snowflake_object_search
---

# Coordinator Action Orchestrator

## When to use

Use this skill after patient pre-screening, when creating the coordinator worklist, applying an approve/edit/reject decision, or auditing workflow actions.

## Decision branches

1. `POTENTIAL_MATCH` -> create `REVIEW_FOR_SCREENING`.
2. `MISSING_INFORMATION` -> create `REQUEST_MISSING_INFORMATION` describing the missing evidence without ordering a clinical test.
3. `MANUAL_REVIEW` -> create `CLINICAL_REVIEW_REQUIRED` with the ambiguity or contradiction.
4. `EXCLUDED` -> create no outreach task; record the cited exclusion in the audit trail.
5. Human `APPROVE` -> add the case to `SCREENING_QUEUE`.
6. Human `EDIT` -> preserve the original recommendation and record the edited action and reason.
7. Human `REJECT` -> close the task and record the rejection reason.

## Required behavior

1. Read `AGENTS.md` and operate only on persisted, versioned screening results.
2. Validate allowed status transitions before writing.
3. Prevent duplicate open tasks with an idempotency key based on protocol, patient, screening run, and action type.
4. Record who or what initiated the action, timestamps, prior state, new state, reason, source result, and citations.
5. Keep audit records append-only. Corrections create new events rather than rewriting history.
6. Return a clear summary of created, skipped, failed, and human-review actions.

## Guardrails

- The copilot never enrolls, contacts, diagnoses, treats, or orders tests for a patient.
- Any action affecting a screening queue requires a human decision.
- Do not expose synthetic patient details outside the governed application context.
- Stop and report an error if citations, result versions, or required audit fields are missing.
