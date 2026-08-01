USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

SELECT run_id, run_status, cohort_size, computed_at
FROM CORE.SCREENING_RUNS ORDER BY computed_at DESC;
SELECT run_id, source_status, original_action_type, task_status, COUNT(*) AS task_count
FROM CORE.COORDINATOR_TASKS GROUP BY ALL ORDER BY source_status;
SELECT event_type, COUNT(*) AS event_count
FROM CORE.AUDIT_EVENTS GROUP BY event_type ORDER BY event_type;

-- Repeating the same request must return the same run and create no duplicates.
CALL APP.RUN_SCREENING('bootstrap-governed-workflow-v1', CURRENT_USER());
SELECT COUNT(*) AS task_count FROM CORE.COORDINATOR_TASKS
WHERE run_id = 'RUN-' || UPPER(SUBSTR(SHA2('bootstrap-governed-workflow-v1', 256), 1, 8));
SELECT COUNT(*) AS audit_count FROM CORE.AUDIT_EVENTS
WHERE source_run_id = 'RUN-' || UPPER(SUBSTR(SHA2('bootstrap-governed-workflow-v1', 256), 1, 8));
