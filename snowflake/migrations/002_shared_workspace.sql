-- TrialOps Evidence Desk: shared Snowflake Workspace
-- Kept separate because replacing a workspace can overwrite collaborative files.

USE ROLE CTOPS_TEAM_ROLE;
USE DATABASE CTOPS_HACKATHON;
USE SCHEMA COLLAB;

CREATE WORKSPACE IF NOT EXISTS CTOPS_HACKATHON.COLLAB.TRIALOPS_SHARED
  COMMENT = 'Shared CoCo and SQL collaboration workspace for TrialOps Evidence Desk';

-- Workspace ownership belongs to CTOPS_TEAM_ROLE, which both teammates inherit.
SHOW WORKSPACES LIKE 'TRIALOPS_SHARED' IN SCHEMA CTOPS_HACKATHON.COLLAB;
