# CoCo patient-screening evidence

**Captured:** 2026-08-01 23:20 IST  
**CoCo:** Cortex Code v1.1.52  
**Connection:** `hackathon`  
**Guard:** server-side SQL read-only

CoCo automatically discovered and invoked the project skill at
`.cortex/skills/patient-screening/SKILL.md`, then independently queried the
governed Snowflake state.

## Result

- Latest run: `RUN-AB1DABE1`
- Cohort: 12/12 synthetic patients
- `POTENTIAL_MATCH`: 3
- `MISSING_INFORMATION`: 2
- `MANUAL_REVIEW`: 2
- `EXCLUDED`: 5
- `UNKNOWN` criterion results: 2
- `CONTRADICTORY` criterion results: 2

Representative two-sided citations returned by CoCo:

1. P009 / `INC-METFORMIN` — protocol `NCT00749190 · Participation criteria · Inclusion #2`; patient `MEDICATIONS.P009.METFORMIN`.
2. P003 / `INC-METFORMIN` — protocol `NCT00749190 · Participation criteria · Inclusion #2`; patient `MEDICATIONS.P003.METFORMIN`.

This proves CoCo is not used as a separate chatbot. It loads the repository's
domain workflow, queries the same persisted state as the application, and
returns governed evidence that can be reproduced from `docs/coco-runbook.md`.
