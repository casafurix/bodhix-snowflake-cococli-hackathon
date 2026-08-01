USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

SELECT protocol_id, document_hash, brief_title, is_current FROM RAW.PROTOCOL_DOCUMENTS;
SELECT review_status, machine_evaluable, COUNT(*) AS criterion_count
FROM CORE.ELIGIBILITY_CRITERIA GROUP BY ALL ORDER BY review_status, machine_evaluable;
SELECT COUNT(*) AS synthetic_patients FROM RAW.PATIENTS WHERE is_synthetic;
SELECT COUNT(*) AS evidence_records, COUNT_IF(contradictory) AS contradiction_flags
FROM RAW.PATIENT_EVIDENCE WHERE is_synthetic;
SELECT run_id, overall_status, COUNT(*) AS patient_count
FROM CORE.PATIENT_SCREENING_RESULTS GROUP BY run_id, overall_status ORDER BY overall_status;
SELECT evidence_status, COUNT(*) AS criterion_result_count
FROM CORE.CRITERION_RESULTS GROUP BY evidence_status ORDER BY evidence_status;
SELECT patient_id, criterion_id, evidence_status, protocol_citation, patient_citation
FROM CORE.CRITERION_RESULTS
WHERE evidence_status IN ('UNKNOWN','CONTRADICTORY')
ORDER BY patient_id, criterion_id;
