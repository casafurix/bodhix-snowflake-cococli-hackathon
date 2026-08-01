# Snowflake CoCo CLI Hackathon 2026

Team workspace for the **Snowflake CoCo (Cortex Code) CLI Hackathon 2026**.

## Docs
- [Problem Statements](docs/PROBLEM_STATEMENTS.md) — the four challenge tracks (build one).
- [Strategy](docs/STRATEGY.md) — event metadata, CoCo CLI primer, winning strategy, real-world pain research, and the 9-day plan.
- [Clinical Trial Architecture](docs/Clinical_Trial_Operations_Intelligence_Platform_Architecture.md) — the selected domain architecture.
- [Final Build Plan](docs/FINAL_BUILD_PLAN.md) — the authoritative product, data, CoCo, architecture, deployment, and five-day delivery contract.
- [CoCo Runbook](docs/coco-runbook.md) — reproducible CLI, skills, and demo workflow.

## Status
Selected track: **PS-04 — Domain-Specific AI Copilot**.

The deployed golden path is a clinical-trial coordinator copilot that extracts cited protocol criteria, pre-screens a synthetic patient cohort, creates safe coordinator tasks, and records human-reviewed actions in an audit trail. Project-specific CoCo skills live under `.cortex/skills/`.

## First vertical slice

The first reviewable slice is implemented as a separated React frontend and FastAPI backend. It computes all four safe pre-screening branches over deterministic synthetic evidence and exposes a cited patient-evidence panel.

Start the backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The backend API and interactive documentation are available at `http://127.0.0.1:8000/docs`.
