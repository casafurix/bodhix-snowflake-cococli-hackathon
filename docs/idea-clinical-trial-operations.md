# Idea: Clinical Trial Operations Intelligence Platform

> **Source:** proposed by Eirene. Enriched with quantified pain, golden-path scoping, Snowflake architecture, UX, and risk analysis.
> **Framing follows the North Star:** pain → experience → tool.

---

## 1. The Pain (lead here)

Clinical trial **patient recruitment is the single biggest bottleneck in drug development.** Trial coordinators manually review hundreds of patient records against trial protocols that can exceed **200 pages** — comparing inclusion/exclusion criteria, lab values, diagnoses, medications, biomarkers, and history for *every* patient. It's slow, repetitive, and error-prone.

**The numbers make it undeniable (great for Real-World Relevance, 30%):**

| Stat | Figure |
|------|--------|
| Trials delayed / missing original recruitment deadlines | **~86%** |
| Trials that fail to meet recruitment timelines | **~70–80%** |
| Trials terminated early due to poor recruitment | **>30%** |
| Trials that successfully recruit their target | **~25%** |
| Cost to a sponsor **per day** of delay | **$600K–$8M** (Phase III conduct alone ≈ $55.7K/day) |

*The person who feels it:* a **trial coordinator / clinical research associate** at a hospital site or CRO, drowning in chart-vs-protocol review, under enrollment-deadline pressure.

> Sources: [WithPower — enrollment statistics](https://www.withpower.com/guides/enrollment-in-clinical-trials-statistics-and-patient-recruitment-strategies) · [DataAlly — enrollment benchmarks & costs](https://www.dataally.ai/blog/clinical-trial-enrollment-statistics) · [JAMA Network Open — completion & recruitment analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9857498/)

---

## 2. The Experience (what the coordinator actually sees)

*(Priority #2 — ease of use before engineering. The coordinator is not a data scientist.)*

**Answer-first, not chat-first.** The coordinator opens one screen and sees:

1. **A ranked shortlist of eligible patients** for a given trial — most-confident first.
2. Each candidate as an **explainable card**: ✅ criteria met / ❌ criteria failed / ⚠️ missing data (e.g., "needs EGFR biomarker test") — **every claim citing the exact protocol clause and the source record**.
3. **One-click actions**: shortlist for screening, flag missing test, dismiss.
4. A **natural-language box** for follow-ups ("show patients who'd qualify if we ran an HbA1c test").

The value proposition in one line: **"The 200-page-vs-hundreds-of-charts review already happened overnight — just verify the shortlist."**

**How we build the surface:** a **Streamlit-in-Snowflake** app over the CoCo agents, so the customer never touches the CLI. Clean candidate cards, confidence bars, plain-language evidence, satisfying approve/act flow. Polished UI beats backend-heavy-but-ugly every time.

---

## 3. The Solution (the tool that serves the pain)

An **AI-powered Clinical Trial Operations Intelligence Platform** that automates the operational side of trials:

- **Analyzes the trial protocol** → extracts eligibility criteria, required tests, visit schedules, timelines, safety requirements.
- **Analyzes patient data** → structured (demographics, diagnoses, medications, labs) + unstructured (physician notes, pathology/radiology reports, discharge summaries).
- **Determines eligibility with evidence** → explains *why* a patient qualifies or not, flags missing information, ranks candidates by confidence.
- **(Roadmap) Operations intelligence** → predicts whether recruitment targets will be met, flags underperforming sites, detects protocol deviations (missed visits, missing docs) before they become audit problems.

It becomes an **intelligent operations assistant, not a search tool.**

---

## 4. Scope Discipline — the Golden Path (critical for 9 days)

⚠️ The full vision has **five agents**; building all five in 9 days risks a broad-but-shallow demo. **Ruthlessly scope the demo to one razor-sharp flow; present the rest as roadmap.**

**The 90-second golden path (build this):**

> Upload a trial protocol → agent extracts eligibility criteria → screens the patient cohort → returns ranked eligible patients, each with an explainable "why qualify / why not / what's missing," citing the exact protocol clause.

This one flow is the "damn" moment: highly visual, shows structured+unstructured fusion, explainable AI, and the visceral pain. **Three core agents only.** Forecasting + compliance become "and the platform extends to…" (slide or mocked secondary screen).

| Agent | Role | Build for demo? |
|-------|------|-----------------|
| **Protocol Intelligence** | Extract structured eligibility rules from trial PDFs | ✅ Core |
| **Patient Intelligence** | Build patient profiles from structured + unstructured records | ✅ Core |
| **Eligibility Reasoning** | Match patients ↔ protocol; explainable, cited decisions | ✅ Core |
| **Recruitment Forecast** | Predict enrollment progress & bottlenecks | 🔶 Roadmap / mock |
| **Compliance** | Monitor adherence; flag missing visits/docs/safety | 🔶 Roadmap / mock |

---

## 5. How Snowflake Fits (the native moat)

- **Storage** — structured (demographics, labs, meds, appointments, recruitment metrics) + unstructured (protocol PDFs, notes, pathology reports, consent forms) in one governed place.
- **Cortex Search** — semantic/hybrid retrieval across medical documents (grounds every eligibility claim → anti-hallucination).
- **Cortex AISQL** (`AI_COMPLETE`, `AI_CLASSIFY`, `AI_EXTRACT`, `PARSE_DOCUMENT`) — reasoning, extraction, summarization over docs.
- **Snowpark** — preprocessing and data pipelines.
- **CoCo CLI** — orchestrates the multi-agent workflow (protocol → patient → eligibility).
- **Governance** — RBAC + audit trail on sensitive health data is a real requirement and a moat a generic agent can't credibly replicate.

---

## 5b. Data Sources (resolved — no longer an open risk)

Eirene sourced a concrete, credible data plan (shared as a team architecture doc). This is stronger than hand-waved synthetic data and signals real rigor to judges.

**Primary sources (4, all legitimate/legal to use):**

| Source | Provides |
|--------|----------|
| **[ClinicalTrials.gov](https://clinicaltrials.gov)** | Trial protocols, inclusion/exclusion criteria, phases, disease classifications, recruitment status |
| **PhysioNet — MIMIC-IV** | De-identified patient admissions, labs, medications, diagnoses, clinical notes (requires registration + data use agreement — respected, widely-published-on dataset, *not* toy synthetic data) |
| **PubMed / PubMed Central** | Biomedical literature & clinical guidelines — evidence for explainable-AI citations |
| **Clinical Trials Registry India (CTRI)** | Indian-specific trial registrations, investigators, criteria |

**Enrichment / normalization sources:** OpenFDA (drug safety/labeling) · ICD-10 (disease coding) · SNOMED CT (clinical terminology) · LOINC (lab test coding) · RxNorm (medication vocabulary).

**Production-path note:** the architecture doc points at **HL7 FHIR** as the standard for future real hospital EHR integration — good "this scales beyond the hackathon" talking point for the pitch, not something to build in 9 days.

> **Action:** MIMIC-IV requires a data-use agreement/registration (usually fast, but start it immediately — it's the one item on the critical path with external lead time).

---

## 6. Mapping to the Problem Statements & Rubric

- **PS-01 (Workflow Automation Agent)** — multi-agent orchestration, decision branches (eligible / ineligible / needs-more-data). *Submit under this — 40% Technical weight.*
- **PS-02 (Unstructured Data Intelligence)** — protocol PDFs + notes/pathology fused with structured labs. Core to the idea.
- **PS-04 (Domain-Specific Copilot)** — life-sciences/clinical domain, terminology, guardrails.
- **PS-03 (AI-Native App)** — the coordinator's NL app experience.

**Rubric fit:** Relevance (30%) — research-backed, quantified pain. Technical (40%) — multi-agent + grounded RAG + explainability. Completeness (30%) — protocol-in → verified shortlist-out, end-to-end.

---

## 7. Risks & Mitigations (be honest)

| Risk | Mitigation |
|------|------------|
| **Scope too large for 9 days** | Cut to the 3-agent eligibility golden path; forecast/compliance = roadmap |
| ~~Convincing synthetic data is hard (real data = PHI)~~ **RESOLVED** | MIMIC-IV (de-identified, real) + ClinicalTrials.gov protocols + PubMed — see §5b |
| **Needs domain expertise** to look credible | Confirm a teammate is comfortable with clinical/lab terminology; keep criteria logic transparent & cited |
| **Safety framing** ("patient qualifies" ≈ clinical claim) | Position as **decision-support for coordinators, human-verified, not auto-enrollment**; explainable + cited throughout |
| **Prior art** (NIH **TrialGPT**, **Deep6 AI**) | Differentiate on the *operations loop* + explainability + Snowflake-native governance, not just matching |
| **Demo crashes / live calls fail** | Pre-run agents, hardcode the golden-path dataset, record a backup video early |

---

## 8. Why This Stands Out

Most teams will build document chatbots or simple RAG healthcare assistants. This is an **enterprise operations platform** combining agentic AI, structured + unstructured healthcare data, workflow automation, explainable AI, and (roadmap) predictive analytics — solving a **well-documented, research-backed problem with real business value** ($600K–$8M/day of delay).

---

## 9. Open Decisions for the Team

1. **Does a teammate have healthcare/clinical-data comfort?** (Decides feasibility & credibility.)
2. **Commit to cutting scope** to the eligibility golden path for the demo? (Required.)
3. ~~Data source~~ **RESOLVED** — MIMIC-IV + ClinicalTrials.gov + PubMed (see §5b). Start the MIMIC-IV data-use-agreement request immediately; it's the one external-lead-time item.
4. **This vs. the denial-recovery idea** — clinical trials is *higher ceiling, higher risk*; denial-recovery is *safer, easier data*. With the data risk now resolved, clinical trials is the stronger pick *if* #1–2 hold. (See [STRATEGY.md](STRATEGY.md) for the comparison.)
5. ~~Finance / stock-market pivot~~ **DECIDED — stick with clinical trials.** See [STRATEGY.md § Domain Decision — Clinical Trials vs. Finance/Stock Market](STRATEGY.md#domain-decision--clinical-trials-vs-financestock-market).

## Target Customers
Pharmaceutical companies running trials, hospitals doing research, CROs, cancer centers, research institutions.
