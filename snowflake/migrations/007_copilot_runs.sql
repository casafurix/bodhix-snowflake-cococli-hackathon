-- Durable, non-PHI trace of ATLAS Coordinator Copilot requests.
-- Copilot responses remain decision support; this table is not a clinical record.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE TABLE IF NOT EXISTS AI.AGENT_RUNS (
  agent_run_id VARCHAR NOT NULL,
  request_id VARCHAR NOT NULL,
  agent_name VARCHAR NOT NULL,
  protocol_id VARCHAR,
  patient_id VARCHAR,
  source_run_id VARCHAR,
  query_text VARCHAR NOT NULL,
  intent VARCHAR NOT NULL,
  response_state VARCHAR NOT NULL,
  model VARCHAR NOT NULL,
  grounded BOOLEAN NOT NULL,
  citations VARIANT NOT NULL,
  retrieved_evidence VARIANT NOT NULL,
  proposed_action VARIANT,
  answer_text VARCHAR NOT NULL,
  persistence_status VARCHAR NOT NULL,
  created_at TIMESTAMP_TZ NOT NULL,
  CONSTRAINT PK_AGENT_RUNS PRIMARY KEY (agent_run_id),
  CONSTRAINT UQ_AGENT_RUNS_REQUEST UNIQUE (request_id)
) COMMENT = 'Append-only ATLAS copilot run trace over public protocol and synthetic evidence only';

