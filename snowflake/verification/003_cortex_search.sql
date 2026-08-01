USE ROLE CTOPS_TEAM_ROLE;
USE WAREHOUSE CTOPS_WH;
USE DATABASE CTOPS_HACKATHON;
USE SCHEMA AI;

SELECT document_type, COUNT(*) AS indexed_source_rows
FROM SEARCH_CORPUS GROUP BY document_type ORDER BY document_type;

SHOW CORTEX SEARCH SERVICES LIKE 'TRIALOPS_EVIDENCE_SEARCH' IN SCHEMA AI;
DESCRIBE CORTEX SEARCH SERVICE TRIALOPS_EVIDENCE_SEARCH;

SELECT PARSE_JSON(
  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'CTOPS_HACKATHON.AI.TRIALOPS_EVIDENCE_SEARCH',
    $${
      "query": "HbA1c range at start of run-in",
      "columns": ["corpus_id", "document_type", "source_id", "title", "search_text"],
      "filter": {"@eq": {"document_type": "PROTOCOL_CLAUSE"}},
      "limit": 3
    }$$
  )
)['results'] AS protocol_search_results;

SELECT PARSE_JSON(
  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'CTOPS_HACKATHON.AI.TRIALOPS_EVIDENCE_SEARCH',
    $${
      "query": "renal function review",
      "columns": ["corpus_id", "patient_id", "source_id", "search_text"],
      "filter": {"@and": [
        {"@eq": {"document_type": "PATIENT_EVIDENCE"}},
        {"@eq": {"patient_id": "P008"}}
      ]},
      "limit": 3
    }$$
  )
)['results'] AS patient_search_results;
