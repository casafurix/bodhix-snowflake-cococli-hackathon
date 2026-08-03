# Clinical Trial Operations Intelligence Platform

> An AI-powered, Snowflake-native platform that automates clinical trial patient recruitment — turning a 200-page protocol and hundreds of patient charts into a ranked, explainable, citation-backed shortlist overnight.

**Built for:** Snowflake CoCo CLI Hackathon
**Problem Statement:** PS-02 — Unstructured Data Intelligence System *(secondary fit: PS-01 Workflow Automation, PS-04 Domain-Specific Copilot)*

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [The Solution](#2-the-solution)
3. [The Experience](#3-the-experience-what-the-coordinator-sees)
4. [Golden Path (Demo Scope)](#4-golden-path-demo-scope)
5. [System Architecture](#5-system-architecture)
6. [AI Agents](#6-ai-agents)
7. [Tech Stack](#7-tech-stack)
8. [Features](#8-features)
9. [Data Sources](#9-data-sources)
10. [Business Model](#10-business-model)
11. [Problem Statement Mapping & Rubric Fit](#11-problem-statement-mapping--rubric-fit)
12. [Risks & Mitigations](#12-risks--mitigations)
13. [Roadmap](#13-roadmap)
14. [Prior Art & Differentiation](#14-prior-art--differentiation)
15. [Getting Started](#15-getting-started)
16. [Project Structure](#16-project-structure)
17. [Team Requirements](#17-team-requirements)
18. [References](#18-references)

---

## 1. The Problem

Clinical trial **patient recruitment is the single biggest bottleneck in drug development.** Trial coordinators manually review hundreds of patient records against trial protocols that can exceed **200 pages** — comparing inclusion/exclusion criteria, lab values, diagnoses, medications, biomarkers, and history for every patient. It's slow, repetitive, and error-prone.

### The numbers

| Stat | Figure |
|---|---|
| Trials delayed / missing original recruitment deadlines | ~86% |
| Trials that fail to meet recruitment timelines | ~70–80% |
| Trials terminated early due to poor recruitment | >30% |
| Trials that successfully recruit their target | ~25% |
| Cost to a sponsor per day of delay | $600K–$8M (Phase III conduct alone ≈ $55.7K/day) |

**Who feels it:** a trial coordinator or clinical research associate (CRA) at a hospital site or CRO, drowning in chart-vs-protocol review under enrollment-deadline pressure.

Sources: [WithPower — enrollment statistics](https://www.withpower.com/guides/enrollment-in-clinical-trials-statistics-and-patient-recruitment-strategies) · [DataAlly — enrollment benchmarks & costs](https://www.dataally.ai/blog/clinical-trial-enrollment-statistics) · [JAMA Network Open — completion & recruitment analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9857498/)

---

## 2. The Solution

An AI-powered **Clinical Trial Operations Intelligence Platform** that automates the operational side of clinical trials:

- **Analyzes the trial protocol** → extracts eligibility criteria, required tests, visit schedules, timelines, safety requirements.
- **Analyzes patient data** → structured (demographics, diagnoses, medications, labs) + unstructured (physician notes, pathology/radiology reports, discharge summaries).
- **Determines eligibility with evidence** → explains *why* a patient qualifies or not, flags missing information, ranks candidates by confidence.
- **(Roadmap)** predicts recruitment target attainment, flags underperforming sites, detects protocol deviations before they become audit problems.

It is positioned as an **intelligent operations assistant, not a search tool** — and explicitly as **decision-support for coordinators, human-verified, not auto-enrollment.**

---

## 3. The Experience (what the coordinator sees)

Ease of use comes before engineering polish — the coordinator is not a data scientist. The interface (Streamlit-in-Snowflake, sitting over the CoCo agents) shows:

1. **A ranked shortlist of eligible patients** for a given trial — most-confident first.
2. Each candidate as an **explainable card**:
   - ✅ criteria met
   - ❌ criteria failed
   - ⚠️ missing data (e.g. "needs EGFR biomarker test")
   - **Every claim cites the exact protocol clause and the exact source record.**
3. **One-click actions**: shortlist for screening, flag missing test, dismiss.
4. A **natural-language follow-up box** (e.g. *"show patients who'd qualify if we ran an HbA1c test"*).

**Value proposition, one line:** *"The 200-page-vs-hundreds-of-charts review already happened overnight — just verify the shortlist."*

---

## 4. Golden Path (Demo Scope)

⚠️ The full vision has **five agents**. Building all five in a 9-day hackathon risks a broad-but-shallow demo. Scope is ruthlessly cut to **one razor-sharp, 90-second flow**:

> **Upload a trial protocol → agent extracts eligibility criteria → screens the patient cohort → returns a ranked list of eligible patients, each with an explainable "why qualify / why not / what's missing," citing the exact protocol clause.**

This single flow demonstrates: structured + unstructured data fusion, explainable/grounded AI, multi-agent orchestration, and the visceral pain point — in one demo.

| Agent | Role | Build for demo? |
|---|---|---|
| Protocol Intelligence | Extract structured eligibility rules from trial PDFs | ✅ Core |
| Patient Intelligence | Build patient profiles from structured + unstructured records | ✅ Core |
| Eligibility Reasoning | Match patients ↔ protocol; explainable, cited decisions | ✅ Core |
| Recruitment Forecast | Predict enrollment progress & bottlenecks | 🔶 Roadmap / mocked slide |
| Compliance | Monitor adherence; flag missing visits/docs/safety | 🔶 Roadmap / mocked slide |

---

## 5. System Architecture

```
                         ┌──────────────────────────┐
                         │   Trial Protocol (PDF)    │
                         │   ClinicalTrials.gov       │
                         └────────────┬──────────────┘
                                      │
                          PARSE_DOCUMENT / AI_EXTRACT
                                      │
                                      ▼
                     ┌───────────────────────────────┐
                     │   Agent 1: Protocol            │
                     │   Intelligence                 │
                     │   → structured eligibility      │
                     │     rules (inclusion/exclusion, │
                     │     tests, biomarkers, logic)   │
                     └───────────────┬─────────────────┘
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      │                              │                              │
      ▼                              ▼                              ▼
┌───────────────┐          ┌───────────────────┐          ┌──────────────────┐
│ Structured EHR │          │ Unstructured notes │          │  Cortex Search    │
│ (demographics,  │─────────▶ (physician notes,   │─────────▶  (semantic/hybrid │
│  labs, meds,     │  fuse   │  pathology reports, │  index   │  retrieval,       │
│  diagnoses)      │         │  discharge summaries)│         │  anti-hallucination│
└────────┬─────────┘          └─────────┬──────────┘          │  grounding)       │
         │                              │                     └─────────┬─────────┘
         └──────────────┬───────────────┘                               │
                         ▼                                              │
              ┌────────────────────────────┐                            │
              │  Agent 2: Patient           │◀───────────────────────────┘
              │  Intelligence                │
              │  → unified patient profile   │
              │    (structured + unstructured)│
              └──────────────┬────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │  Agent 3: Eligibility Reasoning   │
              │  → per-criterion match:            │
              │    ✅ met / ❌ failed / ⚠️ missing  │
              │  → cites exact protocol clause     │
              │    + exact source record           │
              │  → confidence ranking              │
              └──────────────┬───────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │  Streamlit-in-Snowflake UI         │
              │  → ranked shortlist, explainable    │
              │    cards, one-click actions,        │
              │    NL follow-up box                 │
              └─────────────────────────────────┘

              Orchestration across all agents: Snowflake CoCo CLI
              Preprocessing / pipelines: Snowpark
              Governance: RBAC + audit trail (all layers)
```

---

## 6. AI Agents

### Agent 1 — Protocol Intelligence
- **Input:** trial protocol PDF (up to 200+ pages)
- **Process:** `PARSE_DOCUMENT` → `AI_EXTRACT` / `AI_COMPLETE` to pull structured eligibility criteria (inclusion, exclusion, negation, logic relations, required tests, visit schedule, safety requirements)
- **Output:** structured, clause-referenced eligibility ruleset

### Agent 2 — Patient Intelligence
- **Input:** structured hospital data (demographics, diagnoses, medications, labs) + unstructured records (physician notes, pathology/radiology reports, discharge summaries)
- **Process:** fuses structured fields with Cortex Search retrieval over unstructured notes
- **Output:** a single unified patient profile per candidate

### Agent 3 — Eligibility Reasoning
- **Input:** structured eligibility ruleset (Agent 1) + patient profiles (Agent 2)
- **Process:** criterion-by-criterion matching with grounded citation
- **Output:** ✅/❌/⚠️ verdict per criterion, confidence-ranked shortlist, every claim cited to protocol clause + source record

### Agent 4 — Recruitment Forecast *(roadmap)*
- Predicts whether recruitment targets will be met; flags underperforming sites

### Agent 5 — Compliance *(roadmap)*
- Monitors protocol adherence; flags missed visits, missing documentation, safety issues before they become audit problems

---

## 7. Tech Stack

| Layer | Technology |
|---|---|
| Data platform | Snowflake AI Data Cloud |
| Structured + unstructured storage | Snowflake (single governed store) |
| Semantic/hybrid retrieval | Cortex Search |
| Reasoning / extraction / classification | Cortex AISQL (`AI_COMPLETE`, `AI_CLASSIFY`, `AI_EXTRACT`, `PARSE_DOCUMENT`) |
| Data pipelines / preprocessing | Snowpark |
| Agent orchestration | Snowflake CoCo CLI |
| UI | Streamlit-in-Snowflake |
| Governance | RBAC + audit trail on sensitive health data |
| Synthetic patient data | [Synthea](https://github.com/synthetichealth/synthea) |
| Synthetic clinical notes | [synthetichealth/chatty-notes](https://github.com/synthetichealth/chatty-notes) |
| Real protocol source | [ClinicalTrials.gov](https://clinicaltrials.gov) |

---

## 8. Features

**Core (golden path):**
- Protocol upload → automatic eligibility criteria extraction
- Patient cohort screening against extracted criteria
- Ranked, confidence-scored shortlist of eligible patients
- Explainable per-criterion verdicts (✅ / ❌ / ⚠️)
- Full citation of every claim to protocol clause + source patient record
- One-click coordinator actions: shortlist, flag missing test, dismiss
- Natural-language follow-up queries (e.g. "who'd qualify with an HbA1c test?")

**Roadmap (mocked/slide-only for demo):**
- Recruitment forecasting and bottleneck prediction
- Site underperformance detection
- Protocol deviation / compliance monitoring
- EDC/CTMS/EHR integrations (Medidata, Veeva, Oracle Clinical One, Epic, Cerner)
- Multi-language / international protocol support
- Mobile app for on-the-go shortlist review

---

## 9. Data Sources

| Source | Purpose | Why it's safe to use |
|---|---|---|
| [ClinicalTrials.gov](https://clinicaltrials.gov) | Real trial protocols (2–3 for demo, moderate complexity) | Public registry, no PHI |
| [Synthea](https://github.com/synthetichealth/synthea) | Synthetic patient cohort (~50–100 patients) — structured EHR (FHIR) | Fully synthetic, no privacy/legal restriction |
| [chatty-notes](https://github.com/synthetichealth/chatty-notes) | Generates unstructured clinical notes from Synthea FHIR bundles | Solves the "no realistic unstructured notes" gap without touching real PHI |

**Note on real patient data:** real EHR data is PHI and is deliberately avoided for the hackathon demo. Synthetic data is used throughout, and this is stated explicitly in the demo narrative.

---

## 10. Business Model

### Target Users
- **Trial coordinators / CRAs** — hospital sites and CROs; the primary day-to-day operator and the person who feels the pain most directly
- **Pharma sponsors** — clinical operations teams accountable for recruitment timelines and per-day delay costs
- **CROs & research institutions** — cancer centers, academic medical centers running multi-site trials

### Value Proposition
- **Solves a problem:** replaces manual 200-page-protocol-vs-hundreds-of-charts review, directly targeting the ~70–86% of trials that miss recruitment deadlines
- **Provides value:** ranked, explainable shortlist with protocol-clause citations instead of a black-box match; comparable published systems (TrialGPT) demonstrated ~40% reduction in screening time
- **Unique choice:** Snowflake-native governance (RBAC + audit trail on sensitive health data) combined with clause-level explainability — a packaged, auditable enterprise product that generic RAG tools or standalone matching engines don't offer

### Revenue Model
- **Subscription (SaaS)** — per-site or per-trial recurring license for hospitals/CROs running active trials
- **Usage-based fee** — per-patient-screened or per-protocol-processed pricing, scaling with sponsor trial volume
- **Enterprise licensing** — annual multi-site contracts with pharma sponsors; highest-value tier given the $600K–$8M/day cost of delay
- **Freemium/academic tier** — limited free usage for smaller academic research sites, funneling into paid enterprise contracts

### Major Costs
- **AI/API & cloud** — Cortex AISQL calls (`AI_EXTRACT`, `AI_COMPLETE`), Cortex Search indexing, compute for protocol/patient processing at scale
- **Development** — maintaining the multi-agent pipeline as protocol formats and EHR schemas vary across sponsors and sites
- **Compliance & security** — HIPAA-grade infrastructure, governance audits, RBAC — an ongoing cost, but also the core moat
- **Customer onboarding/support** — clinical domain training for coordinators, site-by-site integration; this is a high-touch enterprise sale, not self-serve

### Future Growth
- Activate the full agent suite (Recruitment Forecast, Compliance Monitoring) beyond the eligibility golden path
- EDC/CTMS/EHR integrations so the platform sits inside the existing trial-ops stack rather than beside it
- Global/multi-site expansion — international protocols, non-English clinical notes
- Coordinator mobile app for on-the-go review and approval

---

## 11. Problem Statement Mapping & Rubric Fit

**Submitting under: PS-02 — Unstructured Data Intelligence System**
(also credibly touches PS-01 Workflow Automation, PS-03 AI-Native App, and PS-04 Domain-Specific Copilot)

| Rubric Pillar | How this project addresses it |
|---|---|
| **Real-World Relevance (30%)** | Research-backed, quantified pain (86% delayed, 70–80% missed timelines, $600K–$8M/day cost); realistic operational context for coordinators, CROs, and sponsors |
| **Technical Execution (40%)** | Multi-agent orchestration via CoCo CLI, grounded RAG via Cortex Search (anti-hallucination), structured+unstructured fusion, explainable/cited decision-making |
| **Solution Completeness (30%)** | End-to-end: protocol-in → verified, cited shortlist-out; minimal manual intervention within the golden path |

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Scope too large for 9 days | Cut to the 3-agent eligibility golden path; Forecast/Compliance become roadmap slides only |
| Convincing synthetic data is hard (real data = PHI) | Synthea (structured) + chatty-notes (unstructured) + a real public protocol from ClinicalTrials.gov, pre-loaded and cached |
| Needs domain expertise to look credible | Confirm a teammate is comfortable with clinical/lab terminology before starting; keep all criteria logic transparent and cited |
| Safety framing ("patient qualifies" ≈ clinical claim) | Position explicitly as decision-support for coordinators, human-verified, not auto-enrollment — stated in UI and spoken in the demo, not just the deck |
| Eligibility-criteria parsing is a genuinely hard NLP problem (negation, nested logic, temporal constraints) | Test against edge cases early; don't assume LLM extraction is correct without manual verification on the demo protocols |
| Prior art (NIH TrialGPT, Deep6 AI, Criteria2Query) | Differentiate on the *operations loop* + explainability + Snowflake-native governance, not on matching accuracy alone; have the one-line differentiation ready before a judge asks |
| Demo crashes / live calls fail | Pre-run agents on the golden-path dataset, hardcode/cache that result, record a backup video early |

---

## 13. Roadmap

**Post-hackathon / production path:**
1. Build out Recruitment Forecast and Compliance agents (currently mocked)
2. Integrate with real EDC/CTMS/EHR systems (Medidata, Veeva, Oracle Clinical One, Epic, Cerner)
3. Expand protocol/language support beyond English, single-region trials
4. Formal clinical validation study (similar in spirit to TrialGPT's clinician user study)
5. Mobile companion app for coordinators
6. Enterprise pilot with a real CRO or hospital research department (under a data use agreement, replacing synthetic data)

---

## 14. Prior Art & Differentiation

| System | What it does | How this project differs |
|---|---|---|
| [NIH TrialGPT](https://github.com/ncbi-nlp/TrialGPT) | Zero-shot LLM patient-to-trial matching (retrieval + matching + ranking) | This project adds the *operations loop* (shortlisting, flagging, actions), Snowflake-native governance/audit trail, and a coordinator-first UI, not just a matching score |
| [Criteria2Query](https://github.com/OHDSI/Criteria2Query) (Columbia/OHDSI) | Parses free-text eligibility criteria into structured OMOP CDM queries | This project uses LLM extraction directly against live protocol + patient data with citation-level explainability, without requiring OMOP CDM mapping |
| Deep6 AI | Commercial patient-matching platform | Not open/inspectable; this project's differentiation is explainability (clause-level citation) and enterprise governance built on Snowflake's native stack |

**One-line differentiator:** *"Not just matching — an explainable, audited, governed operations loop for coordinators, built natively on Snowflake."*

---

## 15. Getting Started

> Fill in with actual CLI/setup commands once the environment is provisioned.

```bash
# 1. Clone the repo
git clone <repo-url>
cd clinical-trial-ops-intelligence

# 2. Set up Snowflake CoCo CLI
coco login
coco configure --account <snowflake-account>

# 3. Load synthetic data
#    - Generate Synthea patients
#    - Generate notes via chatty-notes
#    - Load structured + unstructured data into Snowflake stages

# 4. Index unstructured documents with Cortex Search

# 5. Run the agent pipeline
coco run protocol-intelligence --input <protocol.pdf>
coco run patient-intelligence --cohort <patient_ids>
coco run eligibility-reasoning --protocol <protocol_id> --cohort <patient_ids>

# 6. Launch the Streamlit-in-Snowflake UI
streamlit run app.py
```

---

## 16. Project Structure

```
clinical-trial-ops-intelligence/
├── README.md
├── data/
│   ├── protocols/              # ClinicalTrials.gov PDFs/XML
│   ├── synthea_patients/       # Synthetic structured EHR (FHIR)
│   └── synthetic_notes/        # chatty-notes generated clinical notes
├── agents/
│   ├── protocol_intelligence/
│   ├── patient_intelligence/
│   ├── eligibility_reasoning/
│   └── roadmap_mocks/          # Forecast & Compliance (mocked for demo)
├── snowflake/
│   ├── schemas/                # Structured table definitions
│   ├── cortex_search/          # Search service config
│   └── governance/             # RBAC + audit trail setup
├── app/
│   └── streamlit_app.py        # Coordinator-facing UI
└── docs/
    ├── golden_path_demo_script.md
    └── backup_demo_recording.mp4
```

---

## 17. Team Requirements

- **Clinical/domain comfort:** at least one teammate must be comfortable with clinical terminology, lab values, and eligibility logic — this is a hard requirement, not a nice-to-have, and should be confirmed before development starts.
- **Snowflake CoCo CLI familiarity:** for orchestration setup.
- **Frontend:** for the Streamlit-in-Snowflake coordinator UI.
- **Prompt engineering:** for the extraction and reasoning agents, especially around negation and nested eligibility logic.

---

## 18. References

**Papers**
- Jin, Q. et al. "Matching Patients to Clinical Trials with Large Language Models" (TrialGPT). *Nature Communications*, 2024.
- Yuan, C. et al. "Criteria2Query: a natural language interface to clinical databases for cohort definition." *JAMIA*, 2019.
- Park, J. et al. "Criteria2Query 3.0: Leveraging generative large language models for clinical trial eligibility query generation." 2024.
- TREC Clinical Trials Track (2021–2023) — patient-to-trial retrieval benchmark and proceedings.

**Repositories**
- [ncbi-nlp/TrialGPT](https://github.com/ncbi-nlp/TrialGPT)
- [OHDSI/Criteria2Query](https://github.com/OHDSI/Criteria2Query)
- [synthetichealth/synthea](https://github.com/synthetichealth/synthea)
- [synthetichealth/chatty-notes](https://github.com/synthetichealth/chatty-notes)
- [WengLab-InformaticsResearch/GIST](https://github.com/WengLab-InformaticsResearch/GIST)

**Data**
- [ClinicalTrials.gov](https://clinicaltrials.gov) — real trial protocols
- [WithPower — enrollment statistics](https://www.withpower.com/guides/enrollment-in-clinical-trials-statistics-and-patient-recruitment-strategies)
- [DataAlly — enrollment benchmarks & costs](https://www.dataally.ai/blog/clinical-trial-enrollment-statistics)
- [JAMA Network Open — completion & recruitment analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9857498/)

---

*Positioned as decision-support for clinical trial coordinators — human-verified, not auto-enrollment.*
