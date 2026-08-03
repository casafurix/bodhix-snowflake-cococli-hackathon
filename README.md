# Snowflake CoCo CLI Hackathon 2026

Team workspace for the **Snowflake CoCo (Cortex Code) CLI Hackathon 2026**.

## Docs
- [Problem Statements](docs/PROBLEM_STATEMENTS.md) — the four challenge tracks (build one).
- [Strategy](docs/STRATEGY.md) — event metadata, CoCo CLI primer, winning strategy, real-world pain research, and the 9-day plan.
- [Clinical Trial Architecture](docs/Clinical_Trial_Operations_Intelligence_Platform_Architecture.md) — the selected domain architecture.
- [Final Build Plan](docs/FINAL_BUILD_PLAN.md) — the authoritative product, data, CoCo, architecture, deployment, and five-day delivery contract.
- [ATLAS Product and Operator Guide](docs/ATLAS_PLATFORM_GUIDE.md) — plain-language explanation of the current build, frontend walkthrough, deployment operation, and honest demo boundaries.
- [CoCo Runbook](docs/coco-runbook.md) — reproducible CLI, skills, and demo workflow.

## Status
Selected track: **PS-04 — Domain-Specific AI Copilot**.

The deployed golden path is a clinical-trial coordinator copilot that extracts cited protocol criteria, pre-screens a synthetic patient cohort, creates safe coordinator tasks, and records human-reviewed actions in an audit trail. Project-specific CoCo skills live under `.cortex/skills/`.

**Live Snowflake deployment:** [ATLAS Trial Intelligence](https://iaxsmo-pmwcgsc-yq79089.snowflakecomputing.app/)

Snowflake sign-in is required. Use a team user with `CTOPS_TEAM_ROLE`; a suspended
service resumes on first access and may take a short time to become ready.

## First vertical slice

The first reviewable slice is implemented as a separated React frontend and FastAPI backend. Snowflake now stores the public protocol, 20 source criteria (7 reviewed for deterministic screening), a 12-patient synthetic cohort, 84 criterion results per run, 7 current coordinator tasks, append-only audit events, and a Cortex Search index. The offline fixture remains available only for tests and UI work without Snowflake.

Create the Snowflake foundation and governed demo state:

```bash
snow sql -c hackathon -f snowflake/migrations/001_foundation.sql
snow sql -c hackathon -f snowflake/migrations/002_shared_workspace.sql
snow sql -c hackathon -f snowflake/migrations/003_clinical_data_model.sql
snow sql -c hackathon -f snowflake/seed/001_protocol_and_synthetic_cohort.sql
snow sql -c hackathon -f snowflake/seed/002_compute_demo_screening.sql
snow sql -c hackathon -f snowflake/migrations/004_cortex_search.sql
snow sql -c hackathon -f snowflake/migrations/005_workflow_and_screening_procedures.sql
snow sql -c hackathon -f snowflake/migrations/007_copilot_runs.sql
snow sql -c hackathon -f snowflake/migrations/008_multi_trial_intake.sql
```

Start the backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Start on Dashboard, sync a public trial by
ClinicalTrials.gov URL or NCT ID, then open Patients to import a synthetic CSV
cohort or review the demonstration cohort. The backend API and interactive
documentation are available at `http://127.0.0.1:8000/docs`.

Production packaging and Snowpark Container Services commands are documented in
[snowflake/deployment/README.md](snowflake/deployment/README.md). The deployed
container authenticates with Snowflake's short-lived service workload identity;
there is no production database secret in this repository.

The ignored local `.env` contains only non-secret runtime names such as the
connection alias, role, warehouse, database, and schema. Authentication remains
in macOS Keychain and `~/.snowflake/connections.toml`; neither is committed.

## Verification

```bash
source backend/.venv/bin/activate
ruff check backend
pytest -q backend
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend audit --omit=dev
```

Current result: 13 backend tests pass, frontend lint/build pass, and the production
dependency audit reports zero vulnerabilities.
