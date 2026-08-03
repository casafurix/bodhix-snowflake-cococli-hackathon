-- ATLAS — Advanced Trial Lifecycle & Analytics System: governed protocol, evidence, and screening model.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE TABLE IF NOT EXISTS RAW.PROTOCOL_DOCUMENTS (
  protocol_id VARCHAR NOT NULL,
  document_hash VARCHAR NOT NULL,
  source_system VARCHAR NOT NULL,
  source_url VARCHAR NOT NULL,
  brief_title VARCHAR NOT NULL,
  official_title VARCHAR,
  overall_status VARCHAR,
  eligibility_text VARCHAR NOT NULL,
  source_payload VARIANT NOT NULL,
  retrieved_at TIMESTAMP_TZ NOT NULL,
  is_current BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT PK_PROTOCOL_DOCUMENTS PRIMARY KEY (protocol_id, document_hash)
) COMMENT = 'Versioned public protocol documents; no patient data';

CREATE TABLE IF NOT EXISTS RAW.PATIENTS (
  patient_id VARCHAR NOT NULL,
  cohort_version VARCHAR NOT NULL,
  site_id VARCHAR NOT NULL,
  display_name VARCHAR NOT NULL,
  is_synthetic BOOLEAN NOT NULL,
  loaded_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_PATIENTS PRIMARY KEY (patient_id, cohort_version)
) COMMENT = 'Synthetic-only patient roster for the hackathon cohort';

CREATE TABLE IF NOT EXISTS RAW.PATIENT_EVIDENCE (
  evidence_id VARCHAR NOT NULL,
  patient_id VARCHAR NOT NULL,
  cohort_version VARCHAR NOT NULL,
  evidence_field VARCHAR NOT NULL,
  evidence_value VARIANT NOT NULL,
  unit VARCHAR,
  observed_at TIMESTAMP_TZ,
  source_id VARCHAR NOT NULL,
  source_excerpt VARCHAR NOT NULL,
  contradictory BOOLEAN NOT NULL DEFAULT FALSE,
  is_synthetic BOOLEAN NOT NULL,
  loaded_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_PATIENT_EVIDENCE PRIMARY KEY (evidence_id)
) COMMENT = 'Normalized synthetic patient evidence with exact source citations';

CREATE TABLE IF NOT EXISTS CORE.PROTOCOL_PROCESSING_RUNS (
  processing_run_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  document_hash VARCHAR NOT NULL,
  processor VARCHAR NOT NULL,
  model_or_function VARCHAR NOT NULL,
  extracted_count NUMBER NOT NULL,
  reviewed_count NUMBER NOT NULL,
  manual_review_count NUMBER NOT NULL,
  rejected_count NUMBER NOT NULL,
  warnings VARIANT,
  processed_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_PROTOCOL_PROCESSING_RUNS PRIMARY KEY (processing_run_id)
) COMMENT = 'Auditable protocol extraction and validation runs';

CREATE TABLE IF NOT EXISTS CORE.ELIGIBILITY_CRITERIA (
  criterion_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  document_hash VARCHAR NOT NULL,
  criterion_type VARCHAR NOT NULL,
  criterion_ordinal NUMBER NOT NULL,
  source_clause VARCHAR NOT NULL,
  source_location VARCHAR NOT NULL,
  clinical_concept VARCHAR,
  evidence_field VARCHAR,
  operator VARCHAR,
  expected_text VARCHAR,
  threshold_value FLOAT,
  threshold_upper FLOAT,
  expected_boolean BOOLEAN,
  threshold_unit VARCHAR,
  temporal_window VARCHAR,
  required_evidence VARCHAR,
  machine_evaluable BOOLEAN NOT NULL,
  review_status VARCHAR NOT NULL,
  review_notes VARCHAR,
  reviewed_by VARCHAR,
  reviewed_at TIMESTAMP_TZ,
  CONSTRAINT PK_ELIGIBILITY_CRITERIA PRIMARY KEY (criterion_id, document_hash),
  CONSTRAINT CK_CRITERION_TYPE CHECK (criterion_type IN ('INCLUSION', 'EXCLUSION')),
  CONSTRAINT CK_REVIEW_STATUS CHECK (review_status IN ('DRAFT', 'REVIEWED', 'MANUAL_REVIEW', 'REJECTED'))
) COMMENT = 'Cited eligibility clauses and validated machine-readable rule metadata';

CREATE TABLE IF NOT EXISTS CORE.SCREENING_RUNS (
  run_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  document_hash VARCHAR NOT NULL,
  cohort_version VARCHAR NOT NULL,
  rule_version VARCHAR NOT NULL,
  requested_by VARCHAR NOT NULL,
  run_status VARCHAR NOT NULL,
  cohort_size NUMBER NOT NULL,
  computed_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_SCREENING_RUNS PRIMARY KEY (run_id)
) COMMENT = 'Idempotent cohort pre-screen execution metadata';

CREATE TABLE IF NOT EXISTS CORE.CRITERION_RESULTS (
  run_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  patient_id VARCHAR NOT NULL,
  criterion_id VARCHAR NOT NULL,
  evidence_status VARCHAR NOT NULL,
  explanation VARCHAR NOT NULL,
  protocol_citation VARCHAR NOT NULL,
  patient_citation VARCHAR,
  evidence_id VARCHAR,
  rule_version VARCHAR NOT NULL,
  computed_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_CRITERION_RESULTS PRIMARY KEY (run_id, patient_id, criterion_id),
  CONSTRAINT CK_EVIDENCE_STATUS CHECK (evidence_status IN ('MET', 'NOT_MET', 'UNKNOWN', 'CONTRADICTORY'))
) COMMENT = 'One deterministic, cited outcome per reviewed criterion and patient';

CREATE TABLE IF NOT EXISTS CORE.PATIENT_SCREENING_RESULTS (
  run_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  patient_id VARCHAR NOT NULL,
  site_id VARCHAR NOT NULL,
  overall_status VARCHAR NOT NULL,
  evidence_completeness NUMBER(5,2) NOT NULL,
  unknown_count NUMBER NOT NULL,
  contradictory_count NUMBER NOT NULL,
  rule_version VARCHAR NOT NULL,
  computed_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_PATIENT_SCREENING_RESULTS PRIMARY KEY (run_id, patient_id),
  CONSTRAINT CK_SCREENING_STATUS CHECK (overall_status IN ('POTENTIAL_MATCH', 'EXCLUDED', 'MISSING_INFORMATION', 'MANUAL_REVIEW'))
) COMMENT = 'Safe overall pre-screen branch derived only from criterion results';

CREATE OR REPLACE VIEW APP.CURRENT_PROTOCOL AS
SELECT
  p.protocol_id,
  p.brief_title AS title,
  p.source_system AS source,
  p.source_url,
  p.document_hash,
  COUNT_IF(c.review_status = 'REVIEWED') AS reviewed_criteria_count,
  COUNT(*) AS extracted_criteria_count
FROM RAW.PROTOCOL_DOCUMENTS p
JOIN CORE.ELIGIBILITY_CRITERIA c
  ON c.protocol_id = p.protocol_id AND c.document_hash = p.document_hash
WHERE p.is_current
GROUP BY ALL;

CREATE OR REPLACE VIEW APP.CURRENT_SCREENING_DASHBOARD AS
WITH latest_run AS (
  SELECT * FROM CORE.SCREENING_RUNS
  WHERE run_status = 'COMPLETED'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY protocol_id ORDER BY computed_at DESC) = 1
), evidence_pivot AS (
  SELECT
    patient_id,
    cohort_version,
    MAX(IFF(evidence_field = 'age', TRY_TO_DOUBLE(evidence_value::VARCHAR), NULL)) AS age,
    MAX(IFF(evidence_field = 'hba1c', TRY_TO_DOUBLE(evidence_value::VARCHAR), NULL)) AS hba1c,
    MAX(IFF(evidence_field = 'bmi', TRY_TO_DOUBLE(evidence_value::VARCHAR), NULL)) AS bmi
  FROM RAW.PATIENT_EVIDENCE
  GROUP BY patient_id, cohort_version
)
SELECT
  r.run_id,
  r.protocol_id,
  r.computed_at,
  r.cohort_size,
  p.patient_id,
  p.display_name,
  p.site_id,
  s.overall_status,
  s.evidence_completeness,
  s.unknown_count,
  s.contradictory_count,
  e.age,
  e.hba1c,
  e.bmi
FROM latest_run r
JOIN CORE.PATIENT_SCREENING_RESULTS s ON s.run_id = r.run_id
JOIN RAW.PATIENTS p
  ON p.patient_id = s.patient_id AND p.cohort_version = r.cohort_version
LEFT JOIN evidence_pivot e
  ON e.patient_id = p.patient_id AND e.cohort_version = p.cohort_version;

CREATE OR REPLACE VIEW APP.PATIENT_EVIDENCE_RAIL AS
SELECT
  cr.run_id,
  cr.protocol_id,
  cr.patient_id,
  cr.criterion_id,
  c.criterion_type,
  cr.evidence_status,
  c.source_clause,
  c.source_location,
  cr.explanation,
  cr.protocol_citation,
  cr.patient_citation,
  e.source_excerpt AS patient_evidence_excerpt,
  cr.computed_at
FROM CORE.CRITERION_RESULTS cr
JOIN CORE.ELIGIBILITY_CRITERIA c
  ON c.criterion_id = cr.criterion_id AND c.protocol_id = cr.protocol_id
LEFT JOIN RAW.PATIENT_EVIDENCE e ON e.evidence_id = cr.evidence_id;
