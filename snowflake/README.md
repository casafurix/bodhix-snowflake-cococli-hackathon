# Snowflake setup

This directory is the reproducible Snowflake setup for TrialOps Evidence Desk.
It does not contain account credentials. Local authentication stays in the
user-level Snowflake CLI connection named `hackathon`.

Run the migrations in numeric order:

```bash
snow sql -c hackathon -f snowflake/migrations/001_foundation.sql
snow sql -c hackathon -f snowflake/migrations/002_shared_workspace.sql
snow sql -c hackathon -f snowflake/migrations/003_clinical_data_model.sql
snow sql -c hackathon -f snowflake/seed/001_protocol_and_synthetic_cohort.sql
snow sql -c hackathon -f snowflake/seed/002_compute_demo_screening.sql
snow sql -c hackathon -f snowflake/migrations/004_cortex_search.sql
snow sql -c hackathon -f snowflake/migrations/005_workflow_and_screening_procedures.sql
snow sql -c hackathon -f snowflake/verification/001_foundation.sql
snow sql -c hackathon -f snowflake/verification/002_clinical_data.sql
snow sql -c hackathon -f snowflake/verification/003_cortex_search.sql
snow sql -c hackathon -f snowflake/verification/004_workflow.sql
```

The foundation creates:

- `CTOPS_TEAM_ROLE`: least-privilege shared development role.
- `CTOPS_WH`: extra-small, auto-suspending warehouse.
- `CTOPS_WH_MONITOR`: warehouse-specific 25-credit monthly guardrail.
- `CTOPS_HACKATHON`: shared database.
- `RAW`, `CORE`, `AI`, `APP`, and `COLLAB` schemas.
- `CTOPS_HACKATHON.COLLAB.TRIALOPS_SHARED`: shared Snowflake Workspace.

Both `AGNIBHA` and `SIMRAN.SAH` receive `CTOPS_TEAM_ROLE`. The role is also
granted to `SYSADMIN` so it remains inside Snowflake's standard role hierarchy.
The role receives `SNOWFLAKE.CORTEX_USER` and `USE AI FUNCTIONS`; individual
AI objects still use schema-level creation privileges.

The resource monitor is a safety ceiling, not a planned spend. It notifies at
50%, suspends at 80%, and suspends immediately at 90% of 25 credits. Change the
quota deliberately if the team later needs more capacity.
