-- Official public protocol metadata plus a fully synthetic demo cohort.

USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;

MERGE INTO RAW.PROTOCOL_DOCUMENTS target
USING (
  SELECT
    'NCT00749190' AS protocol_id,
    '22a7534399c8e69b3a2dc7534204f4b2a7792d6f36c3e0d3b661787c6290e4c1' AS document_hash,
    'ClinicalTrials.gov' AS source_system,
    'https://clinicaltrials.gov/study/NCT00749190' AS source_url,
    'BI 10773 add-on to Metformin in Patients With Type 2 Diabetes' AS brief_title,
    'A Phase II, Randomized, Parallel Group Safety, Efficacy, and Pharmacokinetics Study of BI 10773 Administered Orally Once Daily Over 12 Weeks in Type 2 Diabetic Patients With Insufficient Glycemic Control Despite Metformin Therapy' AS official_title,
    'COMPLETED' AS overall_status,
    $$Inclusion Criteria:
1. Male and female patients with a diagnosis of type 2 diabetes mellitus and previously treated with metformin alone or with metformin and one other oral antidiabetic drug
2. Stable metformin therapy of at least 1500 mg/day, or less if that is a maximum tolerated dose.
3. HbA1c at screening 6.5% to 9.0% for patients on metformin and one other antidiabetic drug, and HbA1c >7.0% to 10% for patients on metformin only
4. HbA1c >7.0% to 10.0% at Visit 2 (Start of Run-in)
5. Age >=18 and <80years
6. Body Mass Index (BMI) <=40 kg/m2
7. Signed and dated written informed consent prior to admission to the study in accordance with Good Clinical Practice (GCP) and local legislation

Exclusion Criteria:
1. Myocardial infarction, stroke or transient ischemic attack (TIA) within 6 months prior to informed consent
2. Impaired hepatic function
3. Renal insufficiency or impaired renal function
4. Diseases of the central nervous system or psychiatric disorders or clinically relevant neurological disorders that may interfere with participation in the trial
5. Chronic or clinically relevant acute infections
6. Current or chronic urogenital tract infection
7. History of clinically relevant allergy/hypersensitivity
8. Treatment with glitazones (e.g., rosiglitazone, pioglitazone), glucagon-like peptide (GLP-1) analogues, or insulin within 3 months prior to informed consent
9. Treatment with anti-obesity drugs within 3 months prior to informed consent
10. Treatment with systemic steroids or change in dosage of thyroid hormones within 6 weeks prior to informed consent
11. Alcohol abuse or drug abuse
12. Treatment with an investigational drug within 2 months prior to informed consent
13. Women of child-bearing potential who are nursing or pregnant, or who are not practicing an acceptable method of birth control, or do not plan to continue using this method throughout the study and do not agree to periodic pregnancy testing during participation in the trial$$ AS eligibility_text,
    PARSE_JSON($${"nctId":"NCT00749190","overallStatus":"COMPLETED","condition":"Diabetes Mellitus, Type 2","minimumAge":"18 Years","maximumAge":"79 Years","sex":"ALL","healthyVolunteers":false}$$) AS source_payload,
    TO_TIMESTAMP_TZ('2026-08-01 00:00:00 +00:00') AS retrieved_at,
    TRUE AS is_current
) source
ON target.protocol_id = source.protocol_id AND target.document_hash = source.document_hash
WHEN MATCHED THEN UPDATE SET
  target.source_url = source.source_url,
  target.brief_title = source.brief_title,
  target.official_title = source.official_title,
  target.overall_status = source.overall_status,
  target.eligibility_text = source.eligibility_text,
  target.source_payload = source.source_payload,
  target.is_current = TRUE
WHEN NOT MATCHED THEN INSERT (
  protocol_id, document_hash, source_system, source_url, brief_title, official_title,
  overall_status, eligibility_text, source_payload, retrieved_at, is_current
) VALUES (
  source.protocol_id, source.document_hash, source.source_system, source.source_url,
  source.brief_title, source.official_title, source.overall_status, source.eligibility_text,
  source.source_payload, source.retrieved_at, source.is_current
);

MERGE INTO CORE.ELIGIBILITY_CRITERIA target
USING (
  SELECT * FROM VALUES
    ('INC-DIAGNOSIS','INCLUSION',1,'Male and female patients with a diagnosis of type 2 diabetes mellitus and previously treated with metformin alone or with metformin and one other oral antidiabetic drug','Participation criteria · Inclusion #1','type 2 diabetes diagnosis','diagnoses','CONTAINS','type 2 diabetes',NULL,NULL,NULL,NULL,NULL,'Problem list diagnosis',TRUE,'REVIEWED','Reviewed atomic diagnosis component; medication requirements are evaluated separately.'),
    ('INC-METFORMIN','INCLUSION',2,'Stable metformin therapy of at least 1500 mg/day, or less if that is a maximum tolerated dose.','Participation criteria · Inclusion #2','stable metformin dose','metformin_mg_day','GTE_OR_MAX_TOLERATED',NULL,1500,NULL,NULL,'mg/day',NULL,'Medication dose and maximum-tolerated-dose flag',TRUE,'REVIEWED','The exception is preserved: a lower dose only passes when maximum tolerated dose is explicitly true.'),
    ('INC-HBA1C-SCREEN','INCLUSION',3,'HbA1c at screening 6.5% to 9.0% for patients on metformin and one other antidiabetic drug, and HbA1c >7.0% to 10% for patients on metformin only','Participation criteria · Inclusion #3','screening HbA1c conditional range',NULL,NULL,NULL,NULL,NULL,NULL,'%',NULL,'HbA1c and medication regimen branch',FALSE,'MANUAL_REVIEW','Compound medication-dependent branch is not simplified.'),
    ('INC-HBA1C','INCLUSION',4,'HbA1c >7.0% to 10.0% at Visit 2 (Start of Run-in)','Participation criteria · Inclusion #4','run-in HbA1c','hba1c','BETWEEN_EXCLUSIVE_LOWER',NULL,7.0,10.0,NULL,'%',NULL,'Visit 2 HbA1c lab result',TRUE,'REVIEWED','Strict lower bound and inclusive upper bound preserved.'),
    ('INC-AGE','INCLUSION',5,'Age >=18 and <80years','Participation criteria · Inclusion #5','age','age','BETWEEN',NULL,18,79,NULL,'years',NULL,'Synthetic demographics',TRUE,'REVIEWED',NULL),
    ('INC-BMI','INCLUSION',6,'Body Mass Index (BMI) <=40 kg/m2','Participation criteria · Inclusion #6','body mass index','bmi','LTE',NULL,40,NULL,NULL,'kg/m2',NULL,'Screening vital signs',TRUE,'REVIEWED',NULL),
    ('INC-CONSENT','INCLUSION',7,'Signed and dated written informed consent prior to admission to the study in accordance with Good Clinical Practice (GCP) and local legislation','Participation criteria · Inclusion #7','informed consent',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Human-verified consent record',FALSE,'MANUAL_REVIEW','Consent is always human verified and is never inferred by the copilot.'),
    ('EX-CV-EVENT','EXCLUSION',1,'Myocardial infarction, stroke or transient ischemic attack (TIA) within 6 months prior to informed consent','Participation criteria · Exclusion #1','recent cardiovascular event','recent_cv_event','EQ',NULL,NULL,NULL,TRUE,NULL,'Within 6 months prior to informed consent','Clinical history note',TRUE,'REVIEWED','Synthetic evidence explicitly represents the six-month window.'),
    ('EX-HEPATIC','EXCLUSION',2,'Impaired hepatic function','Participation criteria · Exclusion #2','impaired hepatic function',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Clinical review and hepatic labs',FALSE,'MANUAL_REVIEW','No protocol threshold is supplied; coordinator interpretation is required.'),
    ('EX-RENAL','EXCLUSION',3,'Renal insufficiency or impaired renal function','Participation criteria · Exclusion #3','renal impairment','renal_impairment','EQ',NULL,NULL,NULL,TRUE,NULL,NULL,'Clinical renal review',TRUE,'REVIEWED','Synthetic governed flag only; no external threshold invented.'),
    ('EX-CNS','EXCLUSION',4,'Diseases of the central nervous system or psychiatric disorders or clinically relevant neurological disorders that may interfere with participation in the trial','Participation criteria · Exclusion #4','CNS or psychiatric disorder',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Coordinator clinical review',FALSE,'MANUAL_REVIEW','Clinical relevance and interference require human interpretation.'),
    ('EX-INFECTION','EXCLUSION',5,'Chronic or clinically relevant acute infections','Participation criteria · Exclusion #5','clinically relevant infection',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Coordinator clinical review',FALSE,'MANUAL_REVIEW','Clinical relevance is not machine-defined in the source.'),
    ('EX-UROGENITAL','EXCLUSION',6,'Current or chronic urogenital tract infection','Participation criteria · Exclusion #6','urogenital infection',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Diagnosis and note review',FALSE,'MANUAL_REVIEW',NULL),
    ('EX-ALLERGY','EXCLUSION',7,'History of clinically relevant allergy/hypersensitivity','Participation criteria · Exclusion #7','clinically relevant hypersensitivity',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Allergy record and clinical review',FALSE,'MANUAL_REVIEW','Clinical relevance is not machine-defined in the source.'),
    ('EX-DIABETES-MEDS','EXCLUSION',8,'Treatment with glitazones (e.g., rosiglitazone, pioglitazone), glucagon-like peptide (GLP-1) analogues, or insulin within 3 months prior to informed consent','Participation criteria · Exclusion #8','prohibited diabetes medication','medications','TEMPORAL_NOT_CONTAINS',NULL,NULL,NULL,NULL,NULL,'Within 3 months prior to informed consent','Medication history',FALSE,'MANUAL_REVIEW','Multi-drug temporal logic awaits structured medication fixtures.'),
    ('EX-OBESITY-MEDS','EXCLUSION',9,'Treatment with anti-obesity drugs within 3 months prior to informed consent','Participation criteria · Exclusion #9','anti-obesity medication','medications','TEMPORAL_NOT_CONTAINS',NULL,NULL,NULL,NULL,NULL,'Within 3 months prior to informed consent','Medication history',FALSE,'MANUAL_REVIEW',NULL),
    ('EX-STEROID-THYROID','EXCLUSION',10,'Treatment with systemic steroids or change in dosage of thyroid hormones within 6 weeks prior to informed consent','Participation criteria · Exclusion #10','systemic steroid or thyroid dose change','medications','TEMPORAL_COMPOUND',NULL,NULL,NULL,NULL,NULL,'Within 6 weeks prior to informed consent','Medication history',FALSE,'MANUAL_REVIEW','Compound OR and dose-change history are preserved.'),
    ('EX-SUBSTANCE','EXCLUSION',11,'Alcohol abuse or drug abuse','Participation criteria · Exclusion #11','substance abuse',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Coordinator clinical review',FALSE,'MANUAL_REVIEW',NULL),
    ('EX-INVESTIGATIONAL','EXCLUSION',12,'Treatment with an investigational drug within 2 months prior to informed consent','Participation criteria · Exclusion #12','recent investigational drug','medications','TEMPORAL_NOT_CONTAINS',NULL,NULL,NULL,NULL,NULL,'Within 2 months prior to informed consent','Medication and study history',FALSE,'MANUAL_REVIEW',NULL),
    ('EX-PREGNANCY','EXCLUSION',13,'Women of child-bearing potential who are nursing or pregnant, or who are not practicing an acceptable method of birth control, or do not plan to continue using this method throughout the study and do not agree to periodic pregnancy testing during participation in the trial','Participation criteria · Exclusion #13','pregnancy and contraception requirements',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Human-verified pregnancy and contraception evidence',FALSE,'MANUAL_REVIEW','Sensitive compound criterion is never inferred.')
  AS criteria(criterion_id,criterion_type,criterion_ordinal,source_clause,source_location,clinical_concept,evidence_field,operator,expected_text,threshold_value,threshold_upper,expected_boolean,threshold_unit,temporal_window,required_evidence,machine_evaluable,review_status,review_notes)
) source
ON target.criterion_id = source.criterion_id
 AND target.document_hash = '22a7534399c8e69b3a2dc7534204f4b2a7792d6f36c3e0d3b661787c6290e4c1'
WHEN MATCHED THEN UPDATE SET
  target.source_clause = source.source_clause,
  target.source_location = source.source_location,
  target.clinical_concept = source.clinical_concept,
  target.evidence_field = source.evidence_field,
  target.operator = source.operator,
  target.expected_text = source.expected_text,
  target.threshold_value = source.threshold_value,
  target.threshold_upper = source.threshold_upper,
  target.expected_boolean = source.expected_boolean,
  target.threshold_unit = source.threshold_unit,
  target.temporal_window = source.temporal_window,
  target.required_evidence = source.required_evidence,
  target.machine_evaluable = source.machine_evaluable,
  target.review_status = source.review_status,
  target.review_notes = source.review_notes
WHEN NOT MATCHED THEN INSERT (
  criterion_id, protocol_id, document_hash, criterion_type, criterion_ordinal,
  source_clause, source_location, clinical_concept, evidence_field, operator,
  expected_text, threshold_value, threshold_upper, expected_boolean, threshold_unit,
  temporal_window, required_evidence, machine_evaluable, review_status, review_notes,
  reviewed_by, reviewed_at
) VALUES (
  source.criterion_id, 'NCT00749190', '22a7534399c8e69b3a2dc7534204f4b2a7792d6f36c3e0d3b661787c6290e4c1',
  source.criterion_type, source.criterion_ordinal, source.source_clause,
  source.source_location, source.clinical_concept, source.evidence_field,
  source.operator, source.expected_text, source.threshold_value, source.threshold_upper,
  source.expected_boolean, source.threshold_unit, source.temporal_window,
  source.required_evidence, source.machine_evaluable, source.review_status,
  source.review_notes, IFF(source.review_status = 'REVIEWED', 'HACKATHON_COORDINATOR', NULL),
  IFF(source.review_status = 'REVIEWED', TO_TIMESTAMP_TZ('2026-08-01 00:00:00 +00:00'), NULL)
);

MERGE INTO CORE.PROTOCOL_PROCESSING_RUNS target
USING (
  SELECT
    'EXTRACT-22A75343' AS processing_run_id,
    'NCT00749190' AS protocol_id,
    '22a7534399c8e69b3a2dc7534204f4b2a7792d6f36c3e0d3b661787c6290e4c1' AS document_hash,
    'protocol-intelligence' AS processor,
    'AI-assisted extraction validated against ClinicalTrials.gov source text' AS model_or_function,
    20 AS extracted_count,
    7 AS reviewed_count,
    13 AS manual_review_count,
    0 AS rejected_count,
    PARSE_JSON($${"warnings":["Compound and clinically ambiguous clauses remain MANUAL_REVIEW","No patient decision was made during extraction"]}$$) AS warnings,
    TO_TIMESTAMP_TZ('2026-08-01 00:00:00 +00:00') AS processed_at
) source
ON target.processing_run_id = source.processing_run_id
WHEN MATCHED THEN UPDATE SET
  target.extracted_count = source.extracted_count,
  target.reviewed_count = source.reviewed_count,
  target.manual_review_count = source.manual_review_count,
  target.rejected_count = source.rejected_count,
  target.warnings = source.warnings
WHEN NOT MATCHED THEN INSERT ALL BY NAME;

MERGE INTO RAW.PATIENTS target
USING (
  SELECT * FROM VALUES
    ('P001','SITE-BLR','Candidate 001'),('P002','SITE-BLR','Candidate 002'),
    ('P003','SITE-DEL','Candidate 003'),('P004','SITE-MUM','Candidate 004'),
    ('P005','SITE-DEL','Candidate 005'),('P006','SITE-MUM','Candidate 006'),
    ('P007','SITE-BLR','Candidate 007'),('P008','SITE-DEL','Candidate 008'),
    ('P009','SITE-MUM','Candidate 009'),('P010','SITE-BLR','Candidate 010'),
    ('P011','SITE-DEL','Candidate 011'),('P012','SITE-MUM','Candidate 012')
  AS patients(patient_id,site_id,display_name)
) source
ON target.patient_id = source.patient_id AND target.cohort_version = 'SYNTHETIC-V1'
WHEN MATCHED THEN UPDATE SET target.site_id = source.site_id, target.display_name = source.display_name
WHEN NOT MATCHED THEN INSERT (patient_id,cohort_version,site_id,display_name,is_synthetic,loaded_at)
VALUES (source.patient_id,'SYNTHETIC-V1',source.site_id,source.display_name,TRUE,CURRENT_TIMESTAMP());

MERGE INTO RAW.PATIENT_EVIDENCE target
USING (
  WITH patient_seed AS (
    SELECT * FROM VALUES
      ('P001',52,'Type 2 diabetes mellitus',1800,FALSE,8.4,29.8,FALSE,FALSE),
      ('P002',54,'Type 2 diabetes mellitus',1800,FALSE,6.6,31.4,FALSE,FALSE),
      ('P003',54,'Type 2 diabetes mellitus',1800,FALSE,NULL,31.4,FALSE,FALSE),
      ('P004',54,'Type 2 diabetes mellitus',1800,FALSE,8.8,31.4,FALSE,FALSE),
      ('P005',54,'Type 2 diabetes mellitus',1800,FALSE,8.2,31.4,TRUE,FALSE),
      ('P006',67,'Type 2 diabetes mellitus',2000,FALSE,9.1,35.2,FALSE,FALSE),
      ('P007',54,'Type 2 diabetes mellitus',1800,FALSE,8.2,42.1,FALSE,FALSE),
      ('P008',54,'Type 2 diabetes mellitus',1800,FALSE,8.2,31.4,FALSE,NULL),
      ('P009',43,'Type 2 diabetes mellitus',1500,FALSE,7.4,26.7,FALSE,FALSE),
      ('P010',81,'Type 2 diabetes mellitus',1800,FALSE,8.2,31.4,FALSE,FALSE),
      ('P011',54,'Type 2 diabetes mellitus',1000,FALSE,8.2,31.4,FALSE,FALSE),
      ('P012',54,'Type 2 diabetes mellitus',1800,FALSE,8.2,31.4,FALSE,FALSE)
    AS seed(patient_id,age,diagnoses,metformin_mg_day,metformin_max_tolerated,hba1c,bmi,recent_cv_event,renal_impairment)
  ), normalized AS (
    SELECT
      seed.patient_id,
      f.key::VARCHAR AS evidence_field,
      f.value AS evidence_value,
      CASE f.key::VARCHAR
        WHEN 'age' THEN 'years'
        WHEN 'metformin_mg_day' THEN 'mg/day'
        WHEN 'hba1c' THEN '%'
        WHEN 'bmi' THEN 'kg/m2'
        ELSE NULL
      END AS unit,
      CASE f.key::VARCHAR
        WHEN 'age' THEN 'PATIENTS.' || seed.patient_id
        WHEN 'diagnoses' THEN 'PROBLEM_LIST.' || seed.patient_id
        WHEN 'metformin_mg_day' THEN 'MEDICATIONS.' || seed.patient_id || '.METFORMIN'
        WHEN 'metformin_max_tolerated' THEN 'MEDICATIONS.' || seed.patient_id || '.MAX_TOLERATED'
        WHEN 'hba1c' THEN 'LAB_RESULTS.' || seed.patient_id || '.HBA1C'
        WHEN 'bmi' THEN 'VITALS.' || seed.patient_id || '.SCREENING'
        WHEN 'recent_cv_event' THEN 'CLINICAL_NOTES.' || seed.patient_id || '.HISTORY'
        WHEN 'renal_impairment' THEN 'CLINICAL_NOTES.' || seed.patient_id || '.RENAL_REVIEW'
      END AS source_id,
      (seed.patient_id = 'P004' AND f.key::VARCHAR = 'hba1c')
        OR (seed.patient_id = 'P012' AND f.key::VARCHAR = 'diagnoses') AS contradictory
    FROM patient_seed seed,
    LATERAL FLATTEN(INPUT => OBJECT_CONSTRUCT(
      'age', seed.age,
      'diagnoses', seed.diagnoses,
      'metformin_mg_day', seed.metformin_mg_day,
      'metformin_max_tolerated', seed.metformin_max_tolerated,
      'hba1c', seed.hba1c,
      'bmi', seed.bmi,
      'recent_cv_event', seed.recent_cv_event,
      'renal_impairment', seed.renal_impairment
    )) f
  )
  SELECT
    patient_id || ':' || evidence_field AS evidence_id,
    patient_id,
    'SYNTHETIC-V1' AS cohort_version,
    evidence_field,
    evidence_value,
    unit,
    TO_TIMESTAMP_TZ('2026-07-29 09:00:00 +00:00') AS observed_at,
    source_id,
    'Recorded ' || REPLACE(evidence_field, '_', ' ') || ': ' || evidence_value::VARCHAR AS source_excerpt,
    contradictory,
    TRUE AS is_synthetic,
    CURRENT_TIMESTAMP() AS loaded_at
  FROM normalized
) source
ON target.evidence_id = source.evidence_id
WHEN MATCHED THEN UPDATE SET
  target.evidence_value = source.evidence_value,
  target.unit = source.unit,
  target.observed_at = source.observed_at,
  target.source_id = source.source_id,
  target.source_excerpt = source.source_excerpt,
  target.contradictory = source.contradictory
WHEN NOT MATCHED THEN INSERT ALL BY NAME;
