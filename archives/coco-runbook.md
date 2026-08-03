# CoCo Runbook

## Purpose

This runbook provides the reproducible CoCo CLI path for the PS-04 Clinical Trial Operations Copilot. Run commands from the repository root.

## Local setup

The user-level Snowflake connection is named `hackathon`. Its configuration is stored under `~/.snowflake/` and must never be committed.

Verify the tools:

```bash
snow --help
cortex --version
snow connection test -c hackathon
```

Start CoCo in this workspace:

```bash
cortex -c hackathon --workdir "$PWD"
```

Inside CoCo, verify project skills:

```text
/skill list
```

## First planning prompt

```text
Read AGENTS.md and docs/Clinical_Trial_Operations_Intelligence_Platform_Architecture.md. Work in plan mode. Design the smallest deployed PS-04 golden path that invokes protocol-intelligence, patient-screening, and coordinator-action-orchestrator. Use synthetic patient data, a public protocol, Snowflake-native storage and AI, deterministic screening rules, citations, human approval, and an audit log. Do not implement forecasting, compliance monitoring, FHIR, MIMIC ingestion, or the digital twin yet.
```

## Workflow prompts

Protocol processing:

```text
Use the protocol-intelligence skill. Inspect the current Snowflake objects, propose the required schema, and process the selected public protocol into reviewed and cited eligibility criteria. Show the SQL and validation results before moving on.
```

Patient pre-screening:

```text
Use the patient-screening skill. Run the synthetic cohort against the reviewed criteria, compute every result rather than hard-coding outputs, and report the branch distribution with representative citations.
```

Coordinator actions:

```text
Use the coordinator-action-orchestrator skill. Create idempotent coordinator tasks from the latest screening run, preserve the human approval gate, and show the append-only audit events produced.
```

Application:

```text
Build the React coordinator workspace and FastAPI repository over the persisted Snowflake results and actions. The primary screen must be answer-first, show potential matches and missing-information tasks, provide protocol and patient evidence, and support approve/edit/reject with audit logging. Follow AGENTS.md safety language.
```

## Reproducible read-only evidence run

Headless CoCo requires tool approvals. Keep the server-side SQL read-only guard on
even when bypassing the interactive approval prompts:

```bash
cortex -c hackathon --workdir "$PWD" \
  --sql-read-only --bypass --no-mcp --max-turns 6 --effort low \
  -p "Use the patient-screening project skill. Read AGENTS.md and snowflake/verification/002_clinical_data.sql. Execute SELECT statements only against CTOPS_HACKATHON. Inspect the latest completed run by computed_at and report its id, confirm all patients are synthetic, the four overall status counts, UNKNOWN and CONTRADICTORY criterion counts for that run, and two exact protocol/patient citations. Do not edit files. Keep the final answer concise."
```

`--bypass` only skips non-interactive approval prompts here. `--sql-read-only`
still blocks database mutations. Do not omit the read-only flag for verification
runs.

## Demo evidence

Capture the following for the submission:

1. CoCo discovering all three project skills.
2. A skill executing real Snowflake SQL and AI functions.
3. Four decision branches generated from computed results.
4. React/FastAPI reflecting a new coordinator task.
5. A human approval producing a new screening-queue and audit event.
