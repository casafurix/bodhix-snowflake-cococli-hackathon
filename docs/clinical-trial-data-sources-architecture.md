# Clinical Trial Data Sources & Architecture

> Shared by Eirene (Google Doc) as the data-sourcing plan for the [Clinical Trial Operations Intelligence idea](idea-clinical-trial-operations.md). Saved here verbatim for reference — see [STRATEGY.md](STRATEGY.md) and [idea-clinical-trial-operations.md](idea-clinical-trial-operations.md) for how this feeds into the overall plan and rubric fit.

---

| Website | Data Available | Legal to Use? | Best For |
|---|---|---|---|
| ClinicalTrials.gov | Trial protocols, eligibility criteria, study design, recruitment status, interventions | ✅ Yes (public) | Clinical trial protocols |
| Clinical Trials Registry India (CTRI) | Indian clinical trial registrations, investigators, inclusion/exclusion criteria | ✅ Public search (respect terms of use) | Indian trials |
| PhysioNet (MIMIC-IV & MIMIC-IV-Note) | De-identified patient records, labs, medications, clinical notes | ✅ Yes (requires registration, training, and data use agreement) | Patient records |
| PubMed | Biomedical research papers and abstracts | ✅ Yes | Research evidence and citations |
| PubMed Central (PMC) | Full-text open access medical papers | ✅ Yes | RAG over research papers |
| OpenFDA | Drug labels, adverse events, recalls | ✅ Yes | Drug safety information |
| SNOMED CT Browser | Standard clinical terminology | ✅ Yes (browser access) | Disease normalization |
| ICD-10 Browser (WHO) | Disease classification codes | ✅ Yes | Diagnosis mapping |
| LOINC | Laboratory test codes | ✅ Yes | Standardizing lab results |
| RxNorm | Drug vocabulary | ✅ Yes | Medication normalization |
| OHDSI Atlas & OMOP CDM | Common healthcare data model | ✅ Open source | Data modeling |
| The Cancer Imaging Archive (TCIA) | CT, MRI, PET images | ✅ Yes | Imaging (optional) |
| SEER Program | Cancer incidence and survival statistics | ✅ Yes | Cancer analytics |
| National Cancer Institute Data Catalog | Cancer datasets | ✅ Yes | Oncology research |
| Kaggle Healthcare Datasets | Various curated datasets | ✅ Depends on dataset license | Prototyping |

## For your project specifically

You only need four primary sources.

### 1. ClinicalTrials.gov
Use for:
- Trial protocol
- Inclusion criteria
- Exclusion criteria
- Trial phase
- Disease
- Recruitment status

### 2. PhysioNet (MIMIC-IV)
Use for:
- Patients
- Admissions
- Lab values
- Medications
- Diagnoses
- Clinical notes

### 3. PubMed / PubMed Central
Use for:
- Supporting evidence
- Clinical guidelines
- Literature retrieval
- Explainable AI references

### 4. CTRI
Use if you want to show:
"This platform is designed for Indian clinical trials."

## Optional enrichment sources

You can enrich patient or trial information using:
- Drug information: OpenFDA
- Disease ontology: ICD-10
- Medical terminology: SNOMED CT
- Laboratory standardization: LOINC
- Medication standardization: RxNorm

These help normalize data from different hospitals.

## One source I highly recommend adding

If you want your project to feel like a real enterprise product, use FHIR (Fast Healthcare Interoperability Resources).

Official website:
- HL7 FHIR

FHIR isn't a dataset; it's the global standard for healthcare data exchange. Many hospital systems expose patient information in FHIR format. If your architecture states:

"The platform ingests FHIR resources from hospital EHR systems and stores them in Snowflake for AI-driven trial operations."

it immediately signals that your design is compatible with modern healthcare systems rather than being tied to a single dataset.

## My recommended stack

| Purpose | Source |
|---|---|
| Trial protocols | ClinicalTrials.gov + CTRI |
| Patient records | MIMIC-IV + MIMIC-IV-Note |
| Research evidence | PubMed + PubMed Central |
| Medical terminology | SNOMED CT + ICD-10 + LOINC + RxNorm |
| Future real-world integration | HL7 FHIR |

This combination is legal, well-established in research, and sufficient to build a convincing prototype while demonstrating that the architecture could integrate with real hospital systems in production.
