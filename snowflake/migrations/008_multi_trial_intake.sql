-- Select a reviewed protocol and the latest synthetic cohort for safe screening.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE OR REPLACE VIEW APP.EVALUATED_CRITERIA_CURRENT AS
WITH active_protocol AS (
  SELECT protocol_id, document_hash
  FROM CORE.ELIGIBILITY_CRITERIA
  WHERE review_status = 'REVIEWED' AND machine_evaluable
  GROUP BY protocol_id, document_hash
  QUALIFY ROW_NUMBER() OVER (
    ORDER BY COALESCE(MAX(reviewed_at), '1970-01-01'::TIMESTAMP_TZ) DESC,
             protocol_id
  ) = 1
), active_cohort AS (
  SELECT cohort_version
  FROM RAW.PATIENTS
  WHERE is_synthetic
  GROUP BY cohort_version
  QUALIFY ROW_NUMBER() OVER (ORDER BY MAX(loaded_at) DESC, cohort_version DESC) = 1
)
SELECT
  c.protocol_id,
  c.document_hash,
  p.cohort_version,
  p.patient_id,
  p.site_id,
  c.criterion_id,
  c.criterion_type,
  e.evidence_id,
  e.source_id AS patient_citation,
  c.protocol_id || ' · ' || c.source_location AS protocol_citation,
  CASE
    WHEN e.evidence_id IS NULL THEN 'UNKNOWN'
    WHEN e.contradictory THEN 'CONTRADICTORY'
    WHEN c.operator = 'CONTAINS'
      THEN IFF(CONTAINS(LOWER(e.evidence_value::VARCHAR), LOWER(c.expected_text)), 'MET', 'NOT_MET')
    WHEN c.operator = 'GTE_OR_MAX_TOLERATED'
      THEN IFF(
        TRY_TO_DOUBLE(e.evidence_value::VARCHAR) >= c.threshold_value
          OR COALESCE(TRY_TO_BOOLEAN(mtd.evidence_value::VARCHAR), FALSE),
        'MET', 'NOT_MET'
      )
    WHEN c.operator = 'BETWEEN_EXCLUSIVE_LOWER'
      THEN IFF(TRY_TO_DOUBLE(e.evidence_value::VARCHAR) > c.threshold_value
               AND TRY_TO_DOUBLE(e.evidence_value::VARCHAR) <= c.threshold_upper, 'MET', 'NOT_MET')
    WHEN c.operator = 'BETWEEN'
      THEN IFF(TRY_TO_DOUBLE(e.evidence_value::VARCHAR) >= c.threshold_value
               AND TRY_TO_DOUBLE(e.evidence_value::VARCHAR) <= c.threshold_upper, 'MET', 'NOT_MET')
    WHEN c.operator = 'LTE'
      THEN IFF(TRY_TO_DOUBLE(e.evidence_value::VARCHAR) <= c.threshold_value, 'MET', 'NOT_MET')
    WHEN c.operator = 'EQ'
      THEN IFF(TRY_TO_BOOLEAN(e.evidence_value::VARCHAR) = c.expected_boolean, 'MET', 'NOT_MET')
    ELSE 'UNKNOWN'
  END AS evidence_status,
  CASE
    WHEN e.evidence_id IS NULL THEN 'No governed evidence is available for this reviewed criterion.'
    WHEN e.contradictory THEN 'Governed sources disagree; coordinator review is required.'
    ELSE e.source_excerpt
  END AS explanation
FROM RAW.PATIENTS p
JOIN active_cohort ac ON ac.cohort_version = p.cohort_version
CROSS JOIN CORE.ELIGIBILITY_CRITERIA c
JOIN active_protocol ap
  ON ap.protocol_id = c.protocol_id AND ap.document_hash = c.document_hash
LEFT JOIN RAW.PATIENT_EVIDENCE e
  ON e.patient_id = p.patient_id
 AND e.cohort_version = p.cohort_version
 AND e.evidence_field = c.evidence_field
LEFT JOIN RAW.PATIENT_EVIDENCE mtd
  ON mtd.patient_id = p.patient_id
 AND mtd.cohort_version = p.cohort_version
 AND mtd.evidence_field = 'metformin_max_tolerated'
WHERE p.is_synthetic
  AND c.review_status = 'REVIEWED'
  AND c.machine_evaluable;
