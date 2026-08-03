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

import snowflake.connector
from snowflake.connector import DictCursor, SnowflakeConnection
from snowflake.connector.errors import DatabaseError


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
                    "session_parameters": {"QUERY_TAG": "trialops-fastapi"},
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

    def cortex_explain(self, question: str, draft: str, citations: list[dict[str, str]]) -> str | None:
        """Grounded natural-language explanation using Snowflake Cortex.

        The model receives only the deterministic draft and source identifiers.
        If model access is unavailable, callers retain the safe deterministic
        explanation instead of failing the coordinator workflow.
        """
        model = os.getenv("ATLAS_CORTEX_MODEL", "claude-sonnet-4-6")
        retrieved: list[dict] = []
        try:
            search_payload = json.dumps(
                {
                    "query": question,
                    "columns": ["document_type", "patient_id", "source_id", "title", "search_text"],
                    "limit": 5,
                }
            )
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(%s, %s))['results']",
                    (os.getenv("ATLAS_CORTEX_SEARCH_SERVICE", "CTOPS_HACKATHON.AI.TRIALOPS_EVIDENCE_SEARCH"), search_payload),
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
            "Keep the answer under 120 words and mention that a coordinator must verify it.\n\n"
            f"Question: {question}\nDraft: {draft}\nCitations: {json.dumps(citations)}\n"
            f"Retrieved evidence: {json.dumps(retrieved)}"
        )
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT AI_COMPLETE(%s, %s) AS answer", (model, prompt))
                row = cursor.fetchone()
            return str(row[0]) if row and row[0] else None
        except DatabaseError:
            return None

    def dashboard(self) -> dict[str, Any]:
        with self._connection() as connection, connection.cursor(DictCursor) as cursor:
            cursor.execute(
                """
                    SELECT protocol_id, title, source, source_url,
                           reviewed_criteria_count AS criteria_count
                    FROM CTOPS_HACKATHON.APP.CURRENT_PROTOCOL
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
        actor = os.getenv("TRIALOPS_ACTOR", "API_SYNTHETIC_COORDINATOR")
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
                SELECT protocol_id, brief_title AS title, source_system AS source,
                       source_url, document_hash, overall_status, retrieved_at
                FROM CTOPS_HACKATHON.RAW.PROTOCOL_DOCUMENTS
                WHERE is_current
                QUALIFY ROW_NUMBER() OVER (PARTITION BY protocol_id ORDER BY retrieved_at DESC) = 1
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
