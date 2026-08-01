-- Idempotent screening execution, coordinator tasks, and append-only audit history.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE TABLE IF NOT EXISTS CORE.COORDINATOR_TASKS (
  task_key VARCHAR NOT NULL,
  run_id VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  patient_id VARCHAR NOT NULL,
  source_status VARCHAR NOT NULL,
  original_action_type VARCHAR NOT NULL,
  effective_action_type VARCHAR NOT NULL,
  task_status VARCHAR NOT NULL,
  reason VARCHAR NOT NULL,
  source_citations VARIANT NOT NULL,
  created_at TIMESTAMP_TZ NOT NULL,
  updated_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_COORDINATOR_TASKS PRIMARY KEY (task_key),
  CONSTRAINT CK_TASK_STATUS CHECK (task_status IN ('OPEN','APPROVED','REJECTED','DISMISSED'))
) COMMENT = 'Human-gated coordinator work generated idempotently from screening results';

CREATE TABLE IF NOT EXISTS CORE.SCREENING_QUEUE (
  queue_key VARCHAR NOT NULL,
  task_key VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  patient_id VARCHAR NOT NULL,
  queue_status VARCHAR NOT NULL,
  added_by VARCHAR NOT NULL,
  added_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_SCREENING_QUEUE PRIMARY KEY (queue_key)
) COMMENT = 'Human-approved review queue; this is not enrollment or patient outreach';

CREATE TABLE IF NOT EXISTS CORE.AUDIT_EVENTS (
  event_id VARCHAR NOT NULL,
  idempotency_key VARCHAR NOT NULL,
  event_type VARCHAR NOT NULL,
  actor VARCHAR NOT NULL,
  entity_type VARCHAR NOT NULL,
  entity_id VARCHAR NOT NULL,
  prior_state VARIANT NOT NULL,
  new_state VARIANT NOT NULL,
  reason VARCHAR NOT NULL,
  source_run_id VARCHAR NOT NULL,
  citations VARIANT NOT NULL,
  occurred_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_AUDIT_EVENTS PRIMARY KEY (event_id)
) COMMENT = 'Append-only workflow audit history; corrections are new events';

CREATE OR REPLACE VIEW APP.EVALUATED_CRITERIA_CURRENT AS
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
CROSS JOIN CORE.ELIGIBILITY_CRITERIA c
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

CREATE OR REPLACE PROCEDURE APP.RUN_SCREENING(P_REQUEST_ID VARCHAR, P_REQUESTED_BY VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  V_RUN_ID VARCHAR DEFAULT 'RUN-' || UPPER(SUBSTR(SHA2(P_REQUEST_ID, 256), 1, 8));
BEGIN
  MERGE INTO CORE.SCREENING_RUNS target
  USING (
    SELECT
      :V_RUN_ID AS run_id,
      protocol_id,
      document_hash,
      cohort_version,
      'RULES-V1' AS rule_version,
      :P_REQUESTED_BY AS requested_by,
      'RUNNING' AS run_status,
      COUNT(DISTINCT patient_id) AS cohort_size,
      CURRENT_TIMESTAMP() AS computed_at
    FROM APP.EVALUATED_CRITERIA_CURRENT
    GROUP BY protocol_id, document_hash, cohort_version
  ) source
  ON target.run_id = source.run_id
  WHEN MATCHED THEN UPDATE SET
    target.requested_by = source.requested_by,
    target.run_status = source.run_status,
    target.computed_at = source.computed_at
  WHEN NOT MATCHED THEN INSERT ALL BY NAME;

  MERGE INTO CORE.CRITERION_RESULTS target
  USING (
    SELECT
      :V_RUN_ID AS run_id,
      protocol_id,
      patient_id,
      criterion_id,
      evidence_status,
      explanation,
      protocol_citation,
      patient_citation,
      evidence_id,
      'RULES-V1' AS rule_version,
      CURRENT_TIMESTAMP() AS computed_at
    FROM APP.EVALUATED_CRITERIA_CURRENT
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
    target.computed_at = source.computed_at
  WHEN NOT MATCHED THEN INSERT ALL BY NAME;

  MERGE INTO CORE.PATIENT_SCREENING_RESULTS target
  USING (
    SELECT
      :V_RUN_ID AS run_id,
      protocol_id,
      patient_id,
      site_id,
      CASE
        WHEN COUNT_IF(evidence_status = 'CONTRADICTORY') > 0 THEN 'MANUAL_REVIEW'
        WHEN COUNT_IF(
          (criterion_type = 'INCLUSION' AND evidence_status = 'NOT_MET')
          OR (criterion_type = 'EXCLUSION' AND evidence_status = 'MET')
        ) > 0 THEN 'EXCLUDED'
        WHEN COUNT_IF(evidence_status = 'UNKNOWN') > 0 THEN 'MISSING_INFORMATION'
        ELSE 'POTENTIAL_MATCH'
      END AS overall_status,
      ROUND(100 * COUNT_IF(evidence_status NOT IN ('UNKNOWN','CONTRADICTORY')) / COUNT(*), 2)
        AS evidence_completeness,
      COUNT_IF(evidence_status = 'UNKNOWN') AS unknown_count,
      COUNT_IF(evidence_status = 'CONTRADICTORY') AS contradictory_count,
      'RULES-V1' AS rule_version,
      CURRENT_TIMESTAMP() AS computed_at
    FROM APP.EVALUATED_CRITERIA_CURRENT
    GROUP BY protocol_id, patient_id, site_id
  ) source
  ON target.run_id = source.run_id AND target.patient_id = source.patient_id
  WHEN MATCHED THEN UPDATE SET
    target.overall_status = source.overall_status,
    target.evidence_completeness = source.evidence_completeness,
    target.unknown_count = source.unknown_count,
    target.contradictory_count = source.contradictory_count,
    target.computed_at = source.computed_at
  WHEN NOT MATCHED THEN INSERT ALL BY NAME;

  MERGE INTO CORE.COORDINATOR_TASKS target
  USING (
    WITH unresolved AS (
      SELECT
        patient_id,
        LISTAGG(criterion_id, ', ') WITHIN GROUP (ORDER BY criterion_id) AS criteria,
        ARRAY_AGG(OBJECT_CONSTRUCT(
          'criterion_id', criterion_id,
          'protocol_citation', protocol_citation,
          'patient_citation', patient_citation
        )) AS citations
      FROM CORE.CRITERION_RESULTS
      WHERE run_id = :V_RUN_ID AND evidence_status IN ('UNKNOWN','CONTRADICTORY')
      GROUP BY patient_id
    )
    SELECT
      :V_RUN_ID || ':' || r.patient_id || ':' ||
        CASE r.overall_status
          WHEN 'POTENTIAL_MATCH' THEN 'REVIEW_FOR_SCREENING'
          WHEN 'MISSING_INFORMATION' THEN 'REQUEST_MISSING_INFORMATION'
          ELSE 'CLINICAL_REVIEW_REQUIRED'
        END AS task_key,
      :V_RUN_ID AS run_id,
      r.protocol_id,
      r.patient_id,
      r.overall_status AS source_status,
      CASE r.overall_status
        WHEN 'POTENTIAL_MATCH' THEN 'REVIEW_FOR_SCREENING'
        WHEN 'MISSING_INFORMATION' THEN 'REQUEST_MISSING_INFORMATION'
        ELSE 'CLINICAL_REVIEW_REQUIRED'
      END AS original_action_type,
      CASE r.overall_status
        WHEN 'POTENTIAL_MATCH' THEN 'REVIEW_FOR_SCREENING'
        WHEN 'MISSING_INFORMATION' THEN 'REQUEST_MISSING_INFORMATION'
        ELSE 'CLINICAL_REVIEW_REQUIRED'
      END AS effective_action_type,
      'OPEN' AS task_status,
      'Review computed ' || r.overall_status ||
        IFF(u.criteria IS NULL, '', '; unresolved criteria: ' || u.criteria) AS reason,
      COALESCE(u.citations, ARRAY_CONSTRUCT()) AS source_citations,
      CURRENT_TIMESTAMP() AS created_at,
      CURRENT_TIMESTAMP() AS updated_at
    FROM CORE.PATIENT_SCREENING_RESULTS r
    LEFT JOIN unresolved u ON u.patient_id = r.patient_id
    WHERE r.run_id = :V_RUN_ID AND r.overall_status <> 'EXCLUDED'
  ) source
  ON target.task_key = source.task_key
  WHEN MATCHED THEN UPDATE SET target.updated_at = source.updated_at
  WHEN NOT MATCHED THEN INSERT ALL BY NAME;

  MERGE INTO CORE.AUDIT_EVENTS target
  USING (
    SELECT
      'AUD-' || UPPER(SUBSTR(SHA2(task_key || '|TASK_CREATED', 256), 1, 16)) AS event_id,
      task_key || '|TASK_CREATED' AS idempotency_key,
      'TASK_CREATED' AS event_type,
      :P_REQUESTED_BY AS actor,
      'COORDINATOR_TASK' AS entity_type,
      task_key AS entity_id,
      OBJECT_CONSTRUCT() AS prior_state,
      OBJECT_CONSTRUCT('status', task_status, 'action_type', effective_action_type) AS new_state,
      reason,
      run_id AS source_run_id,
      source_citations AS citations,
      CURRENT_TIMESTAMP() AS occurred_at
    FROM CORE.COORDINATOR_TASKS WHERE run_id = :V_RUN_ID
    UNION ALL
    SELECT
      'AUD-' || UPPER(SUBSTR(SHA2(:V_RUN_ID || '|' || patient_id || '|EXCLUDED', 256), 1, 16)),
      :V_RUN_ID || '|' || patient_id || '|EXCLUDED',
      'PRESCREEN_EXCLUSION_RECORDED',
      :P_REQUESTED_BY,
      'PATIENT_SCREENING_RESULT',
      :V_RUN_ID || ':' || patient_id,
      OBJECT_CONSTRUCT(),
      OBJECT_CONSTRUCT('status', overall_status),
      'No outreach task created for a cited pre-screen exclusion.',
      :V_RUN_ID,
      ARRAY_CONSTRUCT(),
      CURRENT_TIMESTAMP()
    FROM CORE.PATIENT_SCREENING_RESULTS
    WHERE run_id = :V_RUN_ID AND overall_status = 'EXCLUDED'
  ) source
  ON target.idempotency_key = source.idempotency_key
  WHEN NOT MATCHED THEN INSERT ALL BY NAME;

  UPDATE CORE.SCREENING_RUNS
  SET run_status = 'COMPLETED', computed_at = CURRENT_TIMESTAMP()
  WHERE run_id = :V_RUN_ID;

  RETURN V_RUN_ID;
END;
$$;

CREATE OR REPLACE PROCEDURE APP.APPLY_TASK_DECISION(
  P_TASK_KEY VARCHAR,
  P_DECISION VARCHAR,
  P_ACTOR VARCHAR,
  P_REASON VARCHAR,
  P_EDITED_ACTION VARCHAR,
  P_REQUEST_ID VARCHAR
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  V_CURRENT_STATUS VARCHAR;
  V_PRIOR_ACTION VARCHAR;
  V_NEW_STATUS VARCHAR;
  V_NEW_ACTION VARCHAR;
  V_RUN_ID VARCHAR;
  V_PROTOCOL_ID VARCHAR;
  V_PATIENT_ID VARCHAR;
  V_CITATIONS VARIANT;
  V_EXISTING_EVENT NUMBER;
  E_UNSUPPORTED EXCEPTION (-20001, 'Unsupported coordinator decision');
  E_TRANSITION EXCEPTION (-20002, 'Only OPEN coordinator tasks can transition');
  E_EDIT_ACTION EXCEPTION (-20003, 'EDIT requires an edited action');
BEGIN
  IF (P_DECISION NOT IN ('APPROVE','EDIT','REJECT','DISMISS')) THEN
    RAISE E_UNSUPPORTED;
  END IF;

  SELECT COUNT(*) INTO :V_EXISTING_EVENT
  FROM CORE.AUDIT_EVENTS WHERE idempotency_key = :P_REQUEST_ID;
  IF (V_EXISTING_EVENT > 0) THEN
    RETURN OBJECT_CONSTRUCT('status', 'ALREADY_APPLIED', 'task_key', P_TASK_KEY);
  END IF;

  SELECT task_status, effective_action_type, run_id, protocol_id, patient_id, source_citations
    INTO :V_CURRENT_STATUS, :V_PRIOR_ACTION, :V_RUN_ID, :V_PROTOCOL_ID, :V_PATIENT_ID, :V_CITATIONS
  FROM CORE.COORDINATOR_TASKS WHERE task_key = :P_TASK_KEY;

  IF (V_CURRENT_STATUS <> 'OPEN') THEN
    RAISE E_TRANSITION;
  END IF;

  V_NEW_STATUS := CASE P_DECISION
    WHEN 'APPROVE' THEN 'APPROVED'
    WHEN 'REJECT' THEN 'REJECTED'
    WHEN 'DISMISS' THEN 'DISMISSED'
    ELSE 'OPEN'
  END;
  V_NEW_ACTION := IFF(P_DECISION = 'EDIT', P_EDITED_ACTION, V_PRIOR_ACTION);

  IF (P_DECISION = 'EDIT' AND (P_EDITED_ACTION IS NULL OR P_EDITED_ACTION = '')) THEN
    RAISE E_EDIT_ACTION;
  END IF;

  UPDATE CORE.COORDINATOR_TASKS
  SET task_status = :V_NEW_STATUS,
      effective_action_type = :V_NEW_ACTION,
      updated_at = CURRENT_TIMESTAMP()
  WHERE task_key = :P_TASK_KEY;

  INSERT INTO CORE.AUDIT_EVENTS (
    event_id, idempotency_key, event_type, actor, entity_type, entity_id,
    prior_state, new_state, reason, source_run_id, citations, occurred_at
  ) SELECT
    'AUD-' || UPPER(SUBSTR(SHA2(:P_REQUEST_ID, 256), 1, 16)),
    :P_REQUEST_ID,
    'TASK_' || :P_DECISION,
    :P_ACTOR,
    'COORDINATOR_TASK',
    :P_TASK_KEY,
    OBJECT_CONSTRUCT('status', :V_CURRENT_STATUS, 'action_type', :V_PRIOR_ACTION),
    OBJECT_CONSTRUCT('status', :V_NEW_STATUS, 'action_type', :V_NEW_ACTION),
    :P_REASON,
    :V_RUN_ID,
    :V_CITATIONS,
    CURRENT_TIMESTAMP();

  IF (P_DECISION = 'APPROVE') THEN
    MERGE INTO CORE.SCREENING_QUEUE target
    USING (SELECT
      :P_TASK_KEY || '|SCREENING_QUEUE' AS queue_key,
      :P_TASK_KEY AS task_key,
      :V_PROTOCOL_ID AS protocol_id,
      :V_PATIENT_ID AS patient_id,
      'PENDING_COORDINATOR_VERIFICATION' AS queue_status,
      :P_ACTOR AS added_by,
      CURRENT_TIMESTAMP() AS added_at
    ) source
    ON target.queue_key = source.queue_key
    WHEN NOT MATCHED THEN INSERT ALL BY NAME;
  END IF;

  RETURN OBJECT_CONSTRUCT(
    'status', 'APPLIED',
    'task_key', P_TASK_KEY,
    'task_status', V_NEW_STATUS,
    'effective_action_type', V_NEW_ACTION
  );
END;
$$;

CALL APP.RUN_SCREENING('bootstrap-governed-workflow-v1', CURRENT_USER());
