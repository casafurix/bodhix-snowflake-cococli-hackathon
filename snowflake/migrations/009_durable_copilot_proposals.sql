-- Durable human-approval proposals for ATLAS Copilot.
-- Proposals expire automatically and never contain PHI in this synthetic demo.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

CREATE TABLE IF NOT EXISTS AI.ACTION_PROPOSALS (
  proposal_id VARCHAR NOT NULL,
  task_key VARCHAR NOT NULL,
  action_type VARCHAR NOT NULL,
  reason VARCHAR NOT NULL,
  proposal_status VARCHAR NOT NULL,
  decision_request_id VARCHAR,
  created_at TIMESTAMP_TZ NOT NULL,
  expires_at TIMESTAMP_TZ NOT NULL,
  consumed_at TIMESTAMP_TZ,
  CONSTRAINT PK_ACTION_PROPOSALS PRIMARY KEY (proposal_id),
  CONSTRAINT CK_ACTION_PROPOSAL_STATUS
    CHECK (proposal_status IN ('PENDING', 'APPLIED', 'EXPIRED'))
) COMMENT = 'Durable, expiring ATLAS action proposals awaiting explicit coordinator approval';
