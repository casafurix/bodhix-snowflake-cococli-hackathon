"""Snowflake-backed repository for the deployed ATLAS application."""

from __future__ import annotations

import os
from atexit import register
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4
import json
import hashlib

import snowflake.connector
from snowflake.connector import DictCursor, SnowflakeConnection
from snowflake.connector.errors import DatabaseError

from app.services.protocol_extraction import (
    ProtocolExtractionError,
    validate_extracted_criteria,
)


class SnowflakeRepository:
    """Read governed app views through a short-lived Snowflake connection."""

    backend_name = "snowflake"

    def __init__(self, connection_name: str | None = None) -> None:
        self.connection_name = connection_name or os.getenv(
            "SNOWFLAKE_CONNECTION_NAME", "hackathon"
        )
        self._connection_lock = RLock()
        self._cached_connection: SnowflakeConnection | None = None
        register(self.close)

    def _connect(self) -> SnowflakeConnection:
        last_error: DatabaseError | None = None
        for _attempt in range(3):
            connection: SnowflakeConnection | None = None
            try:
                token_path = Path("/snowflake/session/token")
                common = {
                    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CTOPS_WH"),
                    "database": os.getenv("SNOWFLAKE_DATABASE", "CTOPS_HACKATHON"),
                    "schema": os.getenv("SNOWFLAKE_SCHEMA", "APP"),
                    "session_parameters": {"QUERY_TAG": "atlas-fastapi"},
                }
                if token_path.exists():
                    connection = snowflake.connector.connect(
                        host=os.environ["SNOWFLAKE_HOST"],
                        account=os.environ["SNOWFLAKE_ACCOUNT"],
                        token=token_path.read_text(encoding="utf-8").strip(),
                        authenticator="oauth",
                        **common,
                    )
                else:
                    connection = snowflake.connector.connect(
                        connection_name=self.connection_name,
                        role=os.getenv("SNOWFLAKE_ROLE", "CTOPS_TEAM_ROLE"),
                        **common,
                    )
                # Local OAuth can occasionally return a stale cached session.
                # Validate it before exposing the connection to a request.
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                return connection
            except DatabaseError as exc:
                last_error = exc
                if connection is not None and not connection.is_closed():
                    connection.close()
        assert last_error is not None
        raise last_error

    @contextmanager
    def _connection(self) -> Iterator[SnowflakeConnection]:
        # The connector permits shared connections, but cursors must not execute
        # concurrently. A single locked session is ample for the hackathon demo
        # and avoids repeated Local OAuth browser/keychain prompts.
        with self._connection_lock:
            if self._cached_connection is None or self._cached_connection.is_closed():
                self._cached_connection = self._connect()
            yield self._cached_connection

    def close(self) -> None:
        with self._connection_lock:
            if self._cached_connection is not None and not self._cached_connection.is_closed():
                self._cached_connection.close()
            self._cached_connection = None

    @staticmethod
    def _value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, list):
            return [SnowflakeRepository._value(item) for item in value]
        if isinstance(value, dict):
            return {key: SnowflakeRepository._value(item) for key, item in value.items()}
        return value

    @staticmethod
    def _one(cursor: DictCursor) -> dict[str, Any]:
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Snowflake returned no current ATLAS record")
        return {
            key.lower(): SnowflakeRepository._value(value)
            for key, value in row.items()
        }

    @staticmethod
    def _all(cursor: DictCursor) -> list[dict[str, Any]]:
        return [
            {
                key.lower(): SnowflakeRepository._value(value)
                for key, value in row.items()
            }
            for row in cursor.fetchall()
        ]

    def health(self) -> dict[str, str]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                "SELECT CURRENT_ACCOUNT() AS account, CURRENT_ROLE() AS role, "
                "CURRENT_WAREHOUSE() AS warehouse"
            )
            context = self._one(cursor)
        return {
            "status": "ok",
            "backend": self.backend_name,
            "snowflake": "connected",
            "account": str(context["account"]),
            "role": str(context["role"]),
            "warehouse": str(context["warehouse"]),
        }

    def cortex_explain(
        self,
        question: str,
        draft: str,
        citations: list[dict[str, str]],
        *,
        protocol_id: str | None = None,
        patient_id: str | None = None,
    ) -> dict:
        """Grounded natural-language explanation using Snowflake Cortex.

        The model receives only the deterministic draft and source identifiers.
        If model access is unavailable, callers retain the safe deterministic
        explanation instead of failing the coordinator workflow. Retrieved
        evidence is returned separately so the UI can show what grounded the
        response.
        """
        model = os.getenv("ATLAS_CORTEX_MODEL", "claude-sonnet-4-6")
        retrieved: list[dict] = []
        try:
            # The user question alone can be underspecified (for example,
            # "Why is P004 in manual review?"). Include the already-governed
            # draft and citations to retrieve the precise evaluated concept,
            # never additional clinical facts.
            retrieval_query = f"{question}\n{draft}\n{json.dumps(citations)}"
            search_payload: dict[str, Any] = {
                "query": retrieval_query,
                "columns": ["document_type", "patient_id", "source_id", "title", "search_text"],
                "limit": 5,
            }
            filters: list[dict[str, Any]] = []
            if protocol_id:
                filters.append({"@eq": {"protocol_id": protocol_id}})
            if patient_id:
                # Candidate evidence is scoped to the requested patient, while
                # protocol clauses remain available as the shared source of truth.
                filters.append(
                    {
                        "@or": [
                            {"@eq": {"patient_id": patient_id}},
                            {"@eq": {"document_type": "PROTOCOL_CLAUSE"}},
                        ]
                    }
                )
            if len(filters) == 1:
                search_payload["filter"] = filters[0]
            elif filters:
                search_payload["filter"] = {"@and": filters}
            search_payload_json = json.dumps(search_payload)
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(%s, %s))['results']",
                    (os.getenv("ATLAS_CORTEX_SEARCH_SERVICE", "CTOPS_HACKATHON.AI.TRIALOPS_EVIDENCE_SEARCH"), search_payload_json),
                )
                row = cursor.fetchone()
            if row and row[0]:
                value = row[0]
                retrieved = json.loads(value) if isinstance(value, str) else value
        except DatabaseError:
            retrieved = []
        prompt = (
            "You are the ATLAS clinical-trial coordinator assistant. Rewrite the supplied draft "
            "in plain language using only the supplied facts. Do not change statuses, invent evidence, "
            "provide medical advice, confirm enrollment, order tests, or propose autonomous actions. "
            "Use plain text without Markdown, keep the answer under 120 words, and mention that a "
            "coordinator must verify it.\n\n"
            f"Question: {question}\nDraft: {draft}\nCitations: {json.dumps(citations)}\n"
            f"Retrieved evidence: {json.dumps(retrieved)}"
        )
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT AI_COMPLETE(%s, %s) AS answer", (model, prompt))
                row = cursor.fetchone()
            answer = row[0] if row and row[0] else None
            if isinstance(answer, str):
                try:
                    decoded = json.loads(answer)
                    answer = decoded if isinstance(decoded, str) else answer
                except json.JSONDecodeError:
                    pass
            return {"answer": answer, "retrieved_evidence": retrieved}
        except DatabaseError:
            return {"answer": None, "retrieved_evidence": retrieved}

    def record_copilot_run(
        self,
        *,
        agent_run_id: str,
        request_id: str,
        protocol_id: str | None,
        patient_id: str | None,
        source_run_id: str | None,
        response: dict,
    ) -> bool:
        """Persist a bounded copilot trace without changing clinical state."""
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO CTOPS_HACKATHON.AI.AGENT_RUNS (
                      agent_run_id, request_id, agent_name, protocol_id, patient_id,
                      source_run_id, query_text, intent, response_state, model,
                      grounded, citations, retrieved_evidence, proposed_action,
                      answer_text, persistence_status, created_at
                    )
                    SELECT %s, %s, 'COORDINATOR_ASSISTANT', %s, %s, %s, %s, %s, %s, %s,
                           %s, PARSE_JSON(%s), PARSE_JSON(%s), PARSE_JSON(%s), %s,
                           'PERSISTED', CURRENT_TIMESTAMP()
                    """,
                    (
                        agent_run_id,
                        request_id,
                        protocol_id,
                        patient_id,
                        source_run_id,
                        response["query"],
                        response["intent"],
                        response["state"],
                        response["model"],
                        response["grounded"],
                        json.dumps(response["citations"]),
                        json.dumps(response["retrieved_evidence"]),
                        json.dumps(response["proposal"]) if response["proposal"] else None,
                        response["answer"],
                    ),
                )
            return True
        except DatabaseError:
            return False

    def dashboard(self) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                    WITH latest_run AS (
                      SELECT protocol_id, document_hash
                      FROM CTOPS_HACKATHON.CORE.SCREENING_RUNS
                      WHERE run_status = 'COMPLETED'
                      QUALIFY ROW_NUMBER() OVER (ORDER BY computed_at DESC) = 1
                    )
                    SELECT d.protocol_id, d.brief_title AS title,
                           d.source_system AS source, d.source_url,
                           COUNT_IF(c.review_status = 'REVIEWED') AS criteria_count
                    FROM latest_run r
                    JOIN CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS d
                      ON d.protocol_id = r.protocol_id AND d.document_hash = r.document_hash
                    JOIN CTOPS_HACKATHON.CORE.ELIGIBILITY_CRITERIA c
                      ON c.protocol_id = d.protocol_id AND c.document_hash = d.document_hash
                    GROUP BY d.protocol_id, d.brief_title, d.source_system, d.source_url
                    """
            )
            protocol = self._one(cursor)
            protocol["review_status"] = "REVIEWED"

            cursor.execute(
                """
                    SELECT run_id, computed_at, cohort_size
                    FROM CTOPS_HACKATHON.CORE.SCREENING_RUNS
                    WHERE run_status = 'COMPLETED'
                    QUALIFY ROW_NUMBER() OVER (ORDER BY computed_at DESC) = 1
                    """
            )
            run = self._one(cursor)

            cursor.execute(
                """
                    SELECT overall_status, COUNT(*) AS patient_count
                    FROM CTOPS_HACKATHON.CORE.PATIENT_SCREENING_RESULTS
                    WHERE run_id = %s
                    GROUP BY overall_status
                    """,
                (run["run_id"],),
            )
            counts = {
                "POTENTIAL_MATCH": 0,
                "EXCLUDED": 0,
                "MISSING_INFORMATION": 0,
                "MANUAL_REVIEW": 0,
            }
            for row in self._all(cursor):
                counts[str(row["overall_status"])] = int(row["patient_count"])
            run["counts"] = counts

            cursor.execute(
                """
                    SELECT patient_id, display_name, site_id, overall_status AS status,
                           evidence_completeness, age, hba1c, bmi
                    FROM CTOPS_HACKATHON.APP.CURRENT_SCREENING_DASHBOARD
                    ORDER BY CASE overall_status
                               WHEN 'POTENTIAL_MATCH' THEN 1
                               WHEN 'MISSING_INFORMATION' THEN 2
                               WHEN 'MANUAL_REVIEW' THEN 3
                               ELSE 4
                             END,
                             evidence_completeness DESC,
                             patient_id
                    """
            )
            patients = self._all(cursor)
        return {"protocol": protocol, "run": run, "patients": patients}

    def patient_detail(self, patient_id: str) -> dict[str, Any] | None:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                    SELECT patient_id, display_name, site_id, overall_status AS status,
                           evidence_completeness, age, hba1c, bmi, run_id,
                           protocol_id, computed_at
                    FROM CTOPS_HACKATHON.APP.CURRENT_SCREENING_DASHBOARD
                    WHERE patient_id = %s
                    """,
                (patient_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            detail = {key.lower(): value for key, value in row.items()}

            cursor.execute(
                """
                    SELECT criterion_id, evidence_status AS status, explanation,
                           protocol_citation, patient_citation, criterion_type, source_clause
                    FROM CTOPS_HACKATHON.APP.PATIENT_EVIDENCE_RAIL
                    WHERE run_id = %s AND patient_id = %s
                    ORDER BY CASE criterion_type WHEN 'INCLUSION' THEN 1 ELSE 2 END,
                             criterion_id
                    """,
                (detail["run_id"], patient_id),
            )
            detail["criteria"] = self._all(cursor)
        detail["disclaimer"] = (
            "Pre-screening decision support only. A coordinator must verify every result."
        )
        return detail

    def run_screening(self) -> str:
        request_id = f"api-{uuid4()}"
        actor = os.getenv(
            "ATLAS_ACTOR", os.getenv("TRIALOPS_ACTOR", "API_SYNTHETIC_COORDINATOR")
        )
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "CALL CTOPS_HACKATHON.APP.RUN_SCREENING(%s, %s)",
                (request_id, actor),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Snowflake did not return a screening run identifier")
        return str(row[0])

    def tasks(self) -> list[dict[str, Any]]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                    SELECT t.task_key, t.patient_id, t.protocol_id,
                           t.effective_action_type AS action_type,
                           t.task_status AS status, t.reason, t.source_status,
                           t.created_at, t.updated_at
                    FROM CTOPS_HACKATHON.CORE.COORDINATOR_TASKS t
                    JOIN (
                      SELECT run_id FROM CTOPS_HACKATHON.CORE.SCREENING_RUNS
                      WHERE run_status = 'COMPLETED'
                      QUALIFY ROW_NUMBER() OVER (ORDER BY computed_at DESC) = 1
                    ) latest ON latest.run_id = t.run_id
                    ORDER BY CASE t.source_status
                               WHEN 'POTENTIAL_MATCH' THEN 1
                               WHEN 'MISSING_INFORMATION' THEN 2
                               ELSE 3
                             END,
                             t.patient_id
                    """
            )
            return self._all(cursor)

    def apply_task_decision(
        self,
        task_key: str,
        decision: str,
        actor: str,
        reason: str,
        edited_action: str | None,
        request_id: str,
    ) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                "CALL CTOPS_HACKATHON.APP.APPLY_TASK_DECISION(%s,%s,%s,%s,%s,%s)",
                (task_key, decision, actor, reason, edited_action, request_id),
            )
            result = self._one(cursor)
        payload = next(iter(result.values()))
        return dict(payload) if isinstance(payload, dict) else {"result": payload}

    def protocol_detail(self) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                WITH latest_run AS (
                  SELECT protocol_id, document_hash
                  FROM CTOPS_HACKATHON.CORE.SCREENING_RUNS
                  WHERE run_status = 'COMPLETED'
                  QUALIFY ROW_NUMBER() OVER (ORDER BY computed_at DESC) = 1
                )
                SELECT d.protocol_id, d.brief_title AS title, d.source_system AS source,
                       d.source_url, d.document_hash, d.overall_status, d.retrieved_at
                FROM latest_run r
                JOIN CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS d
                  ON d.protocol_id = r.protocol_id AND d.document_hash = r.document_hash
                """
            )
            protocol = self._one(cursor)

            cursor.execute(
                """
                SELECT processing_run_id, processor, model_or_function,
                       extracted_count, reviewed_count, manual_review_count,
                       rejected_count, warnings, processed_at
                FROM CTOPS_HACKATHON.CORE.PROTOCOL_PROCESSING_RUNS
                WHERE protocol_id = %s AND document_hash = %s
                QUALIFY ROW_NUMBER() OVER (ORDER BY processed_at DESC) = 1
                """,
                (protocol["protocol_id"], protocol["document_hash"]),
            )
            processing = self._one(cursor)

            cursor.execute(
                """
                SELECT criterion_id, criterion_type, criterion_ordinal,
                       source_clause, source_location, clinical_concept,
                       operator, threshold_value, threshold_upper, threshold_unit,
                       temporal_window, required_evidence, machine_evaluable,
                       review_status, review_notes
                FROM CTOPS_HACKATHON.CORE.ELIGIBILITY_CRITERIA
                WHERE protocol_id = %s AND document_hash = %s
                ORDER BY CASE criterion_type WHEN 'INCLUSION' THEN 1 ELSE 2 END,
                         criterion_ordinal
                """,
                (protocol["protocol_id"], protocol["document_hash"]),
            )
            criteria = self._all(cursor)
        return {"protocol": protocol, "processing": processing, "criteria": criteria}

    def list_trials(self) -> list[dict[str, Any]]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                WITH current_documents AS (
                  SELECT * FROM CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS
                  WHERE is_current
                  QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY protocol_id ORDER BY retrieved_at DESC
                  ) = 1
                ), criteria AS (
                  SELECT protocol_id, document_hash, COUNT(*) AS criteria_count,
                         COUNT_IF(review_status = 'REVIEWED') AS reviewed_count
                  FROM CTOPS_HACKATHON.CORE.ELIGIBILITY_CRITERIA
                  GROUP BY protocol_id, document_hash
                )
                SELECT d.protocol_id, d.brief_title AS title, d.overall_status,
                       COALESCE(c.criteria_count, 0) AS criteria_count,
                       COALESCE(c.reviewed_count, 0) AS reviewed_count,
                       CASE
                         WHEN COALESCE(c.reviewed_count, 0) > 0 THEN 'READY_FOR_SCREENING'
                         WHEN COALESCE(c.criteria_count, 0) > 0 THEN 'REVIEW_REQUIRED'
                         ELSE 'PENDING_EXTRACTION'
                       END AS processing_state,
                       d.retrieved_at AS updated_at, d.source_url,
                       d.document_hash, FALSE AS is_demo
                FROM current_documents d
                LEFT JOIN criteria c
                  ON c.protocol_id = d.protocol_id AND c.document_hash = d.document_hash
                ORDER BY d.retrieved_at DESC
                """
            )
            return self._all(cursor)

    def ingest_protocol(self, trial: dict) -> dict[str, Any]:
        """Version one public study; extraction stays human-gated."""
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS
                SET is_current = FALSE
                WHERE protocol_id = %s AND document_hash <> %s AND is_current
                """,
                (trial["protocol_id"], trial["document_hash"]),
            )
            cursor.execute(
                """
                MERGE INTO CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS target
                USING (SELECT %s AS protocol_id, %s AS document_hash) source
                  ON target.protocol_id = source.protocol_id
                 AND target.document_hash = source.document_hash
                WHEN MATCHED THEN UPDATE SET
                  target.retrieved_at = CURRENT_TIMESTAMP(), target.is_current = TRUE,
                  target.source_payload = PARSE_JSON(%s)
                WHEN NOT MATCHED THEN INSERT (
                  protocol_id, document_hash, source_system, source_url,
                  brief_title, official_title, overall_status, eligibility_text,
                  source_payload, retrieved_at, is_current
                ) VALUES (
                  %s, %s, 'ClinicalTrials.gov v2', %s, %s, %s, %s, %s,
                  PARSE_JSON(%s), CURRENT_TIMESTAMP(), TRUE
                )
                """,
                (
                    trial["protocol_id"],
                    trial["document_hash"],
                    json.dumps(trial["source_payload"]),
                    trial["protocol_id"],
                    trial["document_hash"],
                    trial["source_url"],
                    trial["title"],
                    trial["official_title"],
                    trial["overall_status"],
                    trial["eligibility_text"],
                    json.dumps(trial["source_payload"]),
                ),
            )
        return {
            "protocol_id": trial["protocol_id"],
            "title": trial["title"],
            "overall_status": trial["overall_status"],
            "phase": trial["phase"],
            "conditions": trial["conditions"],
            "site_count": trial["site_count"],
            "enrollment": trial["enrollment"],
            "criteria_count": 0,
            "reviewed_count": 0,
            "processing_state": "PENDING_EXTRACTION",
            "updated_at": trial["last_update"],
            "source_url": trial["source_url"],
            "document_hash": trial["document_hash"],
            "is_demo": False,
            "message": "Public record synced and versioned. Criterion extraction is the next governed step.",
        }

    def extract_protocol(self, protocol_id: str) -> dict[str, Any]:
        model = os.getenv("ATLAS_CORTEX_MODEL", 'SNOWFLAKE.MODELS."CLAUDE-SONNET-4-6"')
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT protocol_id, document_hash, eligibility_text
                FROM CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS
                WHERE protocol_id = %s AND is_current
                QUALIFY ROW_NUMBER() OVER (ORDER BY retrieved_at DESC) = 1
                """,
                (protocol_id,),
            )
            source = self._one(cursor)
        prompt = (
            "Extract every explicit inclusion and exclusion criterion from the supplied public "
            "ClinicalTrials.gov eligibility text. Return JSON only as an object with a criteria "
            "array. Each item must contain criterion_type (INCLUSION or EXCLUSION), source_clause "
            "copied exactly from the supplied text, clinical_concept, and review_notes. Do not "
            "paraphrase, merge clauses, infer medical facts, or create machine rules.\n\n"
            f"Eligibility text:\n{source['eligibility_text']}"
        )
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT AI_COMPLETE(%s, %s)", (model, prompt))
                row = cursor.fetchone()
            raw = str(row[0]) if row and row[0] else ""
            criteria = validate_extracted_criteria(raw, source["eligibility_text"])
        except (DatabaseError, ProtocolExtractionError) as exc:
            raise ValueError(f"Protocol extraction failed safely: {exc}") from exc

        processing_run_id = "PEX-" + hashlib.sha256(
            f"{protocol_id}|{source['document_hash']}|{model}".encode()
        ).hexdigest()[:12].upper()
        counts = {"INCLUSION": 0, "EXCLUSION": 0}
        with self._connection() as connection, connection.cursor() as cursor:
            for ordinal, criterion in enumerate(criteria, start=1):
                counts[criterion.criterion_type] += 1
                criterion_id = (
                    ("INC" if criterion.criterion_type == "INCLUSION" else "EX")
                    + f"-AI-{counts[criterion.criterion_type]:03d}"
                )
                cursor.execute(
                    """
                    MERGE INTO CTOPS_HACKATHON.CORE.ELIGIBILITY_CRITERIA target
                    USING (SELECT %s AS criterion_id, %s AS document_hash) source
                      ON target.criterion_id = source.criterion_id
                     AND target.document_hash = source.document_hash
                    WHEN MATCHED THEN UPDATE SET
                      target.source_clause = %s, target.clinical_concept = %s,
                      target.review_notes = %s
                    WHEN NOT MATCHED THEN INSERT (
                      criterion_id, protocol_id, document_hash, criterion_type,
                      criterion_ordinal, source_clause, source_location,
                      clinical_concept, evidence_field, operator, expected_text,
                      threshold_value, threshold_upper, expected_boolean,
                      threshold_unit, temporal_window, required_evidence,
                      machine_evaluable, review_status, review_notes
                    ) VALUES (
                      %s, %s, %s, %s, %s, %s,
                      'ClinicalTrials.gov eligibilityModule', %s,
                      NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                      FALSE, 'MANUAL_REVIEW', %s
                    )
                    """,
                    (
                        criterion_id,
                        source["document_hash"],
                        criterion.source_clause,
                        criterion.clinical_concept,
                        criterion.review_notes,
                        criterion_id,
                        protocol_id,
                        source["document_hash"],
                        criterion.criterion_type,
                        ordinal,
                        criterion.source_clause,
                        criterion.clinical_concept,
                        criterion.review_notes,
                    ),
                )
            cursor.execute(
                """
                MERGE INTO CTOPS_HACKATHON.CORE.PROTOCOL_PROCESSING_RUNS target
                USING (SELECT %s AS processing_run_id) source
                  ON target.processing_run_id = source.processing_run_id
                WHEN NOT MATCHED THEN INSERT (
                  processing_run_id, protocol_id, document_hash, processor,
                  model_or_function, extracted_count, reviewed_count,
                  manual_review_count, rejected_count, warnings, processed_at
                ) VALUES (
                  %s, %s, %s, 'ATLAS_PROTOCOL_INTELLIGENCE', %s,
                  %s, 0, %s, 0,
                  PARSE_JSON('["AI output validated; every clause requires human review."]'),
                  CURRENT_TIMESTAMP()
                )
                """,
                (
                    processing_run_id,
                    processing_run_id,
                    protocol_id,
                    source["document_hash"],
                    model,
                    len(criteria),
                    len(criteria),
                ),
            )
        return {
            "protocol_id": protocol_id,
            "processing_run_id": processing_run_id,
            "model": model,
            "extracted_count": len(criteria),
            "reviewed_count": 0,
            "manual_review_count": len(criteria),
            "rejected_count": 0,
            "processing_state": "REVIEW_REQUIRED",
        }

    def import_synthetic_cohort(self, cohort_name: str, rows: list[dict]) -> dict[str, Any]:
        """Load a normalized synthetic cohort and run the reviewed rule set."""
        canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        cohort_version = "COHORT-" + hashlib.sha256(
            f"{cohort_name}|{canonical}".encode()
        ).hexdigest()[:12].upper()
        evidence_fields = (
            "age",
            "diagnoses",
            "metformin_mg_day",
            "hba1c",
            "bmi",
            "recent_cv_event",
            "renal_impairment",
        )
        with self._connection() as connection, connection.cursor() as cursor:
            for row in rows:
                patient_id = row["patient_id"]
                cursor.execute(
                    """
                    MERGE INTO CTOPS_HACKATHON.RAW.PATIENTS target
                    USING (SELECT %s AS patient_id, %s AS cohort_version) source
                      ON target.patient_id = source.patient_id
                     AND target.cohort_version = source.cohort_version
                    WHEN NOT MATCHED THEN INSERT (
                      patient_id, cohort_version, site_id, display_name,
                      is_synthetic, loaded_at
                    ) VALUES (%s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP())
                    """,
                    (
                        patient_id,
                        cohort_version,
                        patient_id,
                        cohort_version,
                        row["site_id"],
                        f"Candidate {patient_id}",
                    ),
                )
                for field in evidence_fields:
                    value = row.get(field)
                    if value is None:
                        continue
                    evidence_id = f"{cohort_version}:{patient_id}:{field}"
                    source_id = f"SYNTHETIC_CSV.{cohort_version}.{patient_id}.{field}"
                    cursor.execute(
                        """
                        MERGE INTO CTOPS_HACKATHON.RAW.PATIENT_EVIDENCE target
                        USING (SELECT %s AS evidence_id) source
                          ON target.evidence_id = source.evidence_id
                        WHEN NOT MATCHED THEN INSERT (
                          evidence_id, patient_id, cohort_version, evidence_field,
                          evidence_value, unit, observed_at, source_id, source_excerpt,
                          contradictory, is_synthetic, loaded_at
                        ) VALUES (
                          %s, %s, %s, %s, PARSE_JSON(%s), NULL, CURRENT_TIMESTAMP(),
                          %s, %s, %s, TRUE, CURRENT_TIMESTAMP()
                        )
                        """,
                        (
                            evidence_id,
                            evidence_id,
                            patient_id,
                            cohort_version,
                            field,
                            json.dumps(value),
                            source_id,
                            f"Synthetic CSV recorded {field.replace('_', ' ')}: {value}",
                            row.get("contradictory_field") == field,
                        ),
                    )
        run_id = self.run_screening()
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    MERGE INTO CTOPS_HACKATHON.AI.SEARCH_CORPUS target
                    USING (
                      SELECT
                        'EVIDENCE:' || e.evidence_id AS corpus_id,
                        'PATIENT_EVIDENCE' AS document_type,
                        r.protocol_id,
                        e.patient_id,
                        e.source_id,
                        e.patient_id || ' · ' || e.evidence_field AS title,
                        e.source_excerpt AS search_text,
                        CURRENT_TIMESTAMP() AS updated_at
                      FROM CTOPS_HACKATHON.RAW.PATIENT_EVIDENCE e
                      JOIN CTOPS_HACKATHON.CORE.SCREENING_RUNS r
                        ON r.run_id = %s
                      WHERE e.cohort_version = %s AND e.is_synthetic
                    ) source
                    ON target.corpus_id = source.corpus_id
                    WHEN MATCHED THEN UPDATE SET
                      target.protocol_id = source.protocol_id,
                      target.patient_id = source.patient_id,
                      target.source_id = source.source_id,
                      target.title = source.title,
                      target.search_text = source.search_text,
                      target.updated_at = source.updated_at
                    WHEN NOT MATCHED THEN INSERT ALL BY NAME
                    """,
                    (run_id, cohort_version),
                )
        except DatabaseError:
            # Screening remains valid if the asynchronous retrieval index is
            # temporarily unavailable; direct criterion citations still work.
            pass
        return {
            "cohort_version": cohort_version,
            "patient_count": len(rows),
            "run_id": run_id,
            "status": "SCREENED",
        }

    def audit_events(self) -> list[dict[str, Any]]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT event_id, event_type, actor, entity_type, entity_id,
                       prior_state, new_state, reason, source_run_id,
                       citations, occurred_at
                FROM CTOPS_HACKATHON.CORE.AUDIT_EVENTS
                ORDER BY occurred_at DESC
                LIMIT 100
                """
            )
            return self._all(cursor)

    def operations(self) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                SELECT run_id, site_id,
                       COUNT(*) AS candidate_count,
                       COUNT_IF(overall_status = 'POTENTIAL_MATCH') AS potential_match_count,
                       COUNT_IF(overall_status = 'MISSING_INFORMATION') AS missing_information_count,
                       COUNT_IF(overall_status = 'MANUAL_REVIEW') AS manual_review_count,
                       COUNT_IF(overall_status = 'EXCLUDED') AS excluded_count,
                       ROUND(AVG(evidence_completeness), 2) AS average_evidence_completeness
                FROM CTOPS_HACKATHON.APP.CURRENT_SCREENING_DASHBOARD
                GROUP BY run_id, site_id
                ORDER BY site_id
                """
            )
            sites = self._all(cursor)
        return {"run_id": sites[0]["run_id"] if sites else None, "sites": sites}
