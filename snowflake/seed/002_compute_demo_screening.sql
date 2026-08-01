-- Deterministic pre-screen. No final patient status is hard-coded.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

SET run_id = (
  SELECT 'RUN-' || UPPER(SUBSTR(SHA2('NCT00749190|SYNTHETIC-V1|RULES-V1', 256), 1, 8))
);

MERGE INTO CORE.SCREENING_RUNS target
USING (
  SELECT
    $run_id AS run_id,
    'NCT00749190' AS protocol_id,
    '22a7534399c8e69b3a2dc7534204f4b2a7792d6f36c3e0d3b661787c6290e4c1' AS document_hash,
    'SYNTHETIC-V1' AS cohort_version,
    'RULES-V1' AS rule_version,
    CURRENT_USER() AS requested_by,
    'RUNNING' AS run_status,
    (SELECT COUNT(*) FROM RAW.PATIENTS WHERE cohort_version = 'SYNTHETIC-V1') AS cohort_size,
    CURRENT_TIMESTAMP() AS computed_at
) source
ON target.run_id = source.run_id
WHEN MATCHED THEN UPDATE SET
  target.requested_by = source.requested_by,
  target.run_status = source.run_status,
  target.cohort_size = source.cohort_size,
  target.computed_at = source.computed_at
WHEN NOT MATCHED THEN INSERT ALL BY NAME;

MERGE INTO CORE.CRITERION_RESULTS target
USING (
  WITH evaluated AS (
    SELECT
      $run_id AS run_id,
      c.protocol_id,
      p.patient_id,
      c.criterion_id,
      e.evidence_id,
      e.source_id,
      e.source_excerpt,
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
      c.source_location,
      'RULES-V1' AS rule_version,
      CURRENT_TIMESTAMP() AS computed_at
    FROM RAW.PATIENTS p
    CROSS JOIN CORE.ELIGIBILITY_CRITERIA c
    LEFT JOIN RAW.PATIENT_EVIDENCE e
      ON e.patient_id = p.patient_id
     AND e.cohort_version = p.cohort_version
     AND e.evidence_field = c.evidence_field
    LEFT JOIN RAW.PATIENT_EVIDENCE mtd
      ON mtd.patient_id = p.patient_id
     AND mtd.cohort_version = p.cohort_version
     AND mtd.evidence_field = 'metformin_max_tolerated'
    WHERE p.cohort_version = 'SYNTHETIC-V1'
      AND c.protocol_id = 'NCT00749190'
      AND c.review_status = 'REVIEWED'
      AND c.machine_evaluable
  )
  SELECT
    run_id,
    protocol_id,
    patient_id,
    criterion_id,
    evidence_status,
    CASE evidence_status
      WHEN 'UNKNOWN' THEN 'No governed evidence is available for this reviewed criterion.'
      WHEN 'CONTRADICTORY' THEN 'Governed sources disagree; coordinator review is required.'
      ELSE source_excerpt
    END AS explanation,
    protocol_id || ' · ' || source_location AS protocol_citation,
    source_id AS patient_citation,
    evidence_id,
    rule_version,
    computed_at
  FROM evaluated
) source
ON target.run_id = source.run_id
 AND target.patient_id = source.patient_id
 AND target.criterion_id = source.criterion_id
WHEN MATCHED THEN UPDATE SET
  target.evidence_status = source.evidence_status,
  target.explanation = source.explanation,
  target.protocol_citation = source.protocol_citation,
  target.patient_citation = source.patient_citation,
  target.evidence_id = source.evidence_id,
  target.rule_version = source.rule_version,
  target.computed_at = source.computed_at
WHEN NOT MATCHED THEN INSERT ALL BY NAME;

MERGE INTO CORE.PATIENT_SCREENING_RESULTS target
USING (
  SELECT
    cr.run_id,
    cr.protocol_id,
    cr.patient_id,
    p.site_id,
    CASE
      WHEN COUNT_IF(cr.evidence_status = 'CONTRADICTORY') > 0 THEN 'MANUAL_REVIEW'
      WHEN COUNT_IF(
        (c.criterion_type = 'INCLUSION' AND cr.evidence_status = 'NOT_MET')
        OR (c.criterion_type = 'EXCLUSION' AND cr.evidence_status = 'MET')
      ) > 0 THEN 'EXCLUDED'
      WHEN COUNT_IF(cr.evidence_status = 'UNKNOWN') > 0 THEN 'MISSING_INFORMATION'
      ELSE 'POTENTIAL_MATCH'
    END AS overall_status,
    ROUND(100 * COUNT_IF(cr.evidence_status NOT IN ('UNKNOWN','CONTRADICTORY')) / COUNT(*), 2) AS evidence_completeness,
    COUNT_IF(cr.evidence_status = 'UNKNOWN') AS unknown_count,
    COUNT_IF(cr.evidence_status = 'CONTRADICTORY') AS contradictory_count,
    'RULES-V1' AS rule_version,
    CURRENT_TIMESTAMP() AS computed_at
  FROM CORE.CRITERION_RESULTS cr
  JOIN CORE.ELIGIBILITY_CRITERIA c
    ON c.criterion_id = cr.criterion_id AND c.protocol_id = cr.protocol_id
  JOIN RAW.PATIENTS p
    ON p.patient_id = cr.patient_id AND p.cohort_version = 'SYNTHETIC-V1'
  WHERE cr.run_id = $run_id
  GROUP BY cr.run_id, cr.protocol_id, cr.patient_id, p.site_id
) source
ON target.run_id = source.run_id AND target.patient_id = source.patient_id
WHEN MATCHED THEN UPDATE SET
  target.overall_status = source.overall_status,
  target.evidence_completeness = source.evidence_completeness,
  target.unknown_count = source.unknown_count,
  target.contradictory_count = source.contradictory_count,
  target.rule_version = source.rule_version,
  target.computed_at = source.computed_at
WHEN NOT MATCHED THEN INSERT ALL BY NAME;

UPDATE CORE.SCREENING_RUNS
SET run_status = 'COMPLETED', computed_at = CURRENT_TIMESTAMP()
WHERE run_id = $run_id;

SELECT run_id, overall_status, COUNT(*) AS patient_count
FROM CORE.PATIENT_SCREENING_RESULTS
WHERE run_id = $run_id
GROUP BY run_id, overall_status
ORDER BY overall_status;
