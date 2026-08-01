-- Grounded retrieval over exact protocol clauses and synthetic evidence excerpts.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE TABLE IF NOT EXISTS AI.SEARCH_CORPUS (
  corpus_id VARCHAR NOT NULL,
  document_type VARCHAR NOT NULL,
  protocol_id VARCHAR NOT NULL,
  patient_id VARCHAR,
  source_id VARCHAR NOT NULL,
  title VARCHAR NOT NULL,
  search_text VARCHAR NOT NULL,
  updated_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_SEARCH_CORPUS PRIMARY KEY (corpus_id)
) COMMENT = 'Minimal non-PHI corpus for grounded protocol and synthetic evidence retrieval';

MERGE INTO AI.SEARCH_CORPUS target
USING (
  SELECT
    'PROTOCOL:' || criterion_id AS corpus_id,
    'PROTOCOL_CLAUSE' AS document_type,
    protocol_id,
    NULL::VARCHAR AS patient_id,
    source_location AS source_id,
    criterion_id || ' · ' || criterion_type AS title,
    source_clause AS search_text,
    CURRENT_TIMESTAMP() AS updated_at
  FROM CORE.ELIGIBILITY_CRITERIA
  UNION ALL
  SELECT
    'EVIDENCE:' || evidence_id AS corpus_id,
    'PATIENT_EVIDENCE' AS document_type,
    'NCT00749190' AS protocol_id,
    patient_id,
    source_id,
    patient_id || ' · ' || evidence_field AS title,
    source_excerpt AS search_text,
    CURRENT_TIMESTAMP() AS updated_at
  FROM RAW.PATIENT_EVIDENCE
  WHERE is_synthetic
) source
ON target.corpus_id = source.corpus_id
WHEN MATCHED THEN UPDATE SET
  target.document_type = source.document_type,
  target.protocol_id = source.protocol_id,
  target.patient_id = source.patient_id,
  target.source_id = source.source_id,
  target.title = source.title,
  target.search_text = source.search_text,
  target.updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT ALL BY NAME;

ALTER TABLE AI.SEARCH_CORPUS SET CHANGE_TRACKING = TRUE;

CREATE CORTEX SEARCH SERVICE IF NOT EXISTS AI.TRIALOPS_EVIDENCE_SEARCH
  ON search_text
  PRIMARY KEY (corpus_id)
  ATTRIBUTES document_type, protocol_id, patient_id, source_id
  WAREHOUSE = CTOPS_WH
  TARGET_LAG = '12 hours'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  REFRESH_MODE = INCREMENTAL
  INITIALIZE = ON_CREATE
  REQUEST_LOGGING = TRUE
  AUTO_SUSPEND = 1800
  COMMENT = 'Grounded retrieval for TrialOps protocol clauses and synthetic evidence'
AS
  SELECT
    corpus_id,
    document_type,
    protocol_id,
    patient_id,
    source_id,
    title,
    search_text,
    updated_at
  FROM AI.SEARCH_CORPUS;

SHOW CORTEX SEARCH SERVICES LIKE 'TRIALOPS_EVIDENCE_SEARCH' IN SCHEMA AI;
