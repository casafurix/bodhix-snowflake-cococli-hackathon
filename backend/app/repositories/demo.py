"""Deterministic in-memory repository for the first reviewable vertical slice.

The API contract stays unchanged when this repository is replaced by Snowflake.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, date, datetime
from threading import Lock
from uuid import uuid4

from app.domain.models import (
    Criterion,
    CriterionType,
    Evidence,
    Operator,
    PatientSnapshot,
    ScreeningResult,
    ScreeningStatus,
)
from app.services.eligibility import screen_patient
from app.services.operations import task_from_screening

PROTOCOL_ID = "NCT00749190"


def _criteria() -> tuple[Criterion, ...]:
    return (
        Criterion(
            "INC-DIAGNOSIS",
            PROTOCOL_ID,
            CriterionType.INCLUSION,
            "diagnoses",
            Operator.CONTAINS,
            "Diagnosis of type 2 diabetes mellitus.",
            "Participation criteria · Inclusion #1",
            "type 2 diabetes",
        ),
        Criterion(
            "INC-METFORMIN",
            PROTOCOL_ID,
            CriterionType.INCLUSION,
            "metformin_mg_day",
            Operator.GTE,
            "Stable metformin therapy of at least 1500 mg/day, or maximum tolerated dose.",
            "Participation criteria · Inclusion #2",
            1500,
            unit="mg/day",
        ),
        Criterion(
            "INC-HBA1C",
            PROTOCOL_ID,
            CriterionType.INCLUSION,
            "hba1c",
            Operator.BETWEEN,
            "HbA1c greater than 7.0% and up to 10.0% at the start of run-in.",
            "Participation criteria · Inclusion #4",
            7.0,
            10.0,
            "%",
        ),
        Criterion(
            "INC-AGE",
            PROTOCOL_ID,
            CriterionType.INCLUSION,
            "age",
            Operator.BETWEEN,
            "Age at least 18 and under 80 years.",
            "Participation criteria · Inclusion #5",
            18,
            79,
            "years",
        ),
        Criterion(
            "INC-BMI",
            PROTOCOL_ID,
            CriterionType.INCLUSION,
            "bmi",
            Operator.LTE,
            "Body mass index no greater than 40 kg/m².",
            "Participation criteria · Inclusion #6",
            40,
            unit="kg/m²",
        ),
        Criterion(
            "EX-CV-EVENT",
            PROTOCOL_ID,
            CriterionType.EXCLUSION,
            "recent_cv_event",
            Operator.EQ,
            "Myocardial infarction, stroke, or transient ischemic attack within six months.",
            "Participation criteria · Exclusion #1",
            True,
        ),
        Criterion(
            "EX-RENAL",
            PROTOCOL_ID,
            CriterionType.EXCLUSION,
            "renal_impairment",
            Operator.EQ,
            "Renal insufficiency or impaired renal function.",
            "Participation criteria · Exclusion #3",
            True,
        ),
    )


def _evidence(patient_id: str, key: str, value, *, contradictory: bool = False) -> Evidence:
    source = {
        "hba1c": f"LAB_RESULTS.{patient_id}.HBA1C",
        "bmi": f"VITALS.{patient_id}.SCREENING",
        "metformin_mg_day": f"MEDICATIONS.{patient_id}.METFORMIN",
        "diagnoses": f"PROBLEM_LIST.{patient_id}",
        "recent_cv_event": f"CLINICAL_NOTES.{patient_id}.HISTORY",
        "renal_impairment": f"CLINICAL_NOTES.{patient_id}.RENAL_REVIEW",
        "age": f"PATIENTS.{patient_id}",
    }[key]
    excerpt = f"Recorded {key.replace('_', ' ')}: {value}"
    return Evidence(value, source, date(2026, 7, 29), excerpt, contradictory)


def _patient(
    patient_id: str,
    site_id: str,
    *,
    age: int | None = 54,
    diagnosis: str | None = "Type 2 diabetes mellitus",
    metformin: int | float | None = 1800,
    hba1c: float | None = 8.2,
    bmi: float | None = 31.4,
    recent_cv_event: bool | None = False,
    renal_impairment: bool | None = False,
    contradictory_key: str | None = None,
) -> PatientSnapshot:
    values = {
        "age": age,
        "diagnoses": diagnosis,
        "metformin_mg_day": metformin,
        "hba1c": hba1c,
        "bmi": bmi,
        "recent_cv_event": recent_cv_event,
        "renal_impairment": renal_impairment,
    }
    fields = {
        key: _evidence(patient_id, key, value, contradictory=key == contradictory_key)
        for key, value in values.items()
        if value is not None
    }
    return PatientSnapshot(patient_id, site_id, f"Candidate {patient_id[1:]}", fields)


def _patients() -> tuple[PatientSnapshot, ...]:
    return (
        _patient("P001", "SITE-BLR", age=52, hba1c=8.4, bmi=29.8),
        _patient("P002", "SITE-BLR", hba1c=6.6),
        _patient("P003", "SITE-DEL", hba1c=None),
        _patient("P004", "SITE-MUM", hba1c=8.8, contradictory_key="hba1c"),
        _patient("P005", "SITE-DEL", recent_cv_event=True),
        _patient("P006", "SITE-MUM", age=67, metformin=2000, hba1c=9.1, bmi=35.2),
        _patient("P007", "SITE-BLR", bmi=42.1),
        _patient("P008", "SITE-DEL", renal_impairment=None),
        _patient("P009", "SITE-MUM", age=43, metformin=1500, hba1c=7.4, bmi=26.7),
        _patient("P010", "SITE-BLR", age=81),
        _patient("P011", "SITE-DEL", metformin=1000),
        _patient("P012", "SITE-MUM", contradictory_key="diagnoses"),
    )


class DemoRepository:
    """Thread-safe computed prototype state."""

    def __init__(self) -> None:
        self.criteria = _criteria()
        self.patients = _patients()
        self._lock = Lock()
        self.run_id = ""
        self.computed_at = datetime.now(UTC)
        self.results: dict[str, ScreeningResult] = {}
        self._task_states: dict[str, str] = {}
        self._audit: list[dict] = []
        self._synced_protocols: dict[str, dict] = {}
        self.run_screening()

    def run_screening(self) -> str:
        with self._lock:
            run_id = f"RUN-{uuid4().hex[:8].upper()}"
            self.results = {
                patient.patient_id: screen_patient(
                    PROTOCOL_ID, patient, self.criteria, run_id=run_id
                )
                for patient in self.patients
            }
            self.run_id = run_id
            self.computed_at = datetime.now(UTC)
            return run_id

    def _patient_summary(self, patient: PatientSnapshot) -> dict:
        result = self.results[patient.patient_id]
        known = sum(item.status not in {"UNKNOWN", "CONTRADICTORY"} for item in result.criterion_results)
        completeness = round(known / len(result.criterion_results) * 100)
        fields = patient.fields
        return {
            "patient_id": patient.patient_id,
            "display_name": patient.display_name,
            "site_id": patient.site_id,
            "status": result.status,
            "evidence_completeness": completeness,
            "age": fields.get("age").value if fields.get("age") else None,
            "hba1c": fields.get("hba1c").value if fields.get("hba1c") else None,
            "bmi": fields.get("bmi").value if fields.get("bmi") else None,
        }

    def dashboard(self) -> dict:
        order = {
            ScreeningStatus.POTENTIAL_MATCH: 0,
            ScreeningStatus.MISSING_INFORMATION: 1,
            ScreeningStatus.MANUAL_REVIEW: 2,
            ScreeningStatus.EXCLUDED: 3,
        }
        counts = {status.value: 0 for status in ScreeningStatus}
        for result in self.results.values():
            counts[result.status.value] += 1
        patients = sorted(
            (self._patient_summary(patient) for patient in self.patients),
            key=lambda row: (order[ScreeningStatus(row["status"])], -row["evidence_completeness"]),
        )
        return {
            "protocol": {
                "protocol_id": PROTOCOL_ID,
                "title": "BI 10773 add-on to Metformin in Patients With Type 2 Diabetes",
                "source": "ClinicalTrials.gov",
                "source_url": f"https://clinicaltrials.gov/study/{PROTOCOL_ID}",
                "criteria_count": len(self.criteria),
                "review_status": "REVIEWED",
            },
            "run": {
                "run_id": self.run_id,
                "computed_at": self.computed_at,
                "cohort_size": len(self.patients),
                "counts": counts,
            },
            "patients": patients,
        }

    def patient_detail(self, patient_id: str) -> dict | None:
        patient = next((p for p in self.patients if p.patient_id == patient_id), None)
        if patient is None:
            return None
        result = self.results[patient_id]
        criterion_map = {criterion.criterion_id: criterion for criterion in self.criteria}
        detail = []
        for item in result.criterion_results:
            criterion = criterion_map[item.criterion_id]
            detail.append(
                {
                    **asdict(item),
                    "criterion_type": criterion.criterion_type,
                    "source_clause": criterion.source_clause,
                }
            )
        return {
            **self._patient_summary(patient),
            "protocol_id": result.protocol_id,
            "run_id": result.run_id,
            "computed_at": result.computed_at,
            "criteria": detail,
            "disclaimer": "Pre-screening decision support only. A coordinator must verify every result.",
        }

    def tasks(self) -> list[dict]:
        items = []
        for result in self.results.values():
            task = task_from_screening(result)
            if task is not None:
                items.append(
                    {
                        **asdict(task),
                        "source_status": result.status,
                        "status": self._task_states.get(task.task_key, task.status),
                        "updated_at": task.created_at,
                    }
                )
        return items

    def protocol_detail(self) -> dict:
        criteria = []
        for ordinal, criterion in enumerate(self.criteria, start=1):
            criteria.append(
                {
                    "criterion_id": criterion.criterion_id,
                    "criterion_type": criterion.criterion_type,
                    "criterion_ordinal": ordinal,
                    "source_clause": criterion.source_clause,
                    "source_location": criterion.source_location,
                    "clinical_concept": criterion.field,
                    "operator": criterion.operator,
                    "threshold_value": criterion.value
                    if isinstance(criterion.value, (int, float))
                    and not isinstance(criterion.value, bool)
                    else None,
                    "threshold_upper": criterion.upper_value,
                    "threshold_unit": criterion.unit,
                    "temporal_window": None,
                    "required_evidence": criterion.field,
                    "machine_evaluable": criterion.machine_evaluable,
                    "review_status": criterion.review_status,
                    "review_notes": "Validated deterministic offline fixture.",
                }
            )
        return {
            "protocol": {
                **self.dashboard()["protocol"],
                "document_hash": "OFFLINE-FIXTURE-HASH",
                "overall_status": "COMPLETED",
                "retrieved_at": self.computed_at,
            },
            "processing": {
                "processing_run_id": "OFFLINE-FIXTURE",
                "extracted_count": len(self.criteria),
                "reviewed_count": len(self.criteria),
                "manual_review_count": 0,
                "rejected_count": 0,
                "processor": "deterministic offline fixture",
            },
            "criteria": criteria,
        }

    def list_trials(self) -> list[dict]:
        current = self.dashboard()["protocol"]
        items = [
            {
                "protocol_id": current["protocol_id"],
                "title": current["title"],
                "overall_status": "COMPLETED",
                "phase": "PHASE2",
                "conditions": ["Type 2 Diabetes Mellitus"],
                "site_count": 3,
                "enrollment": 12,
                "criteria_count": len(self.criteria),
                "reviewed_count": len(self.criteria),
                "processing_state": "READY_FOR_SCREENING",
                "updated_at": self.computed_at,
                "source_url": current["source_url"],
                "is_demo": True,
            }
        ]
        items.extend(self._synced_protocols.values())
        return items

    def ingest_protocol(self, trial: dict) -> dict:
        item = {
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
            "updated_at": datetime.now(UTC),
            "source_url": trial["source_url"],
            "document_hash": trial["document_hash"],
            "is_demo": False,
        }
        self._synced_protocols[trial["protocol_id"]] = item
        item["eligibility_text"] = trial["eligibility_text"]
        return {
            **item,
            "message": "Public record synced and versioned. Criterion extraction is the next governed step.",
        }

    def extract_protocol(self, protocol_id: str) -> dict:
        trial = self._synced_protocols.get(protocol_id)
        if trial is None:
            raise ValueError("Sync the public study before extracting its criteria.")
        text = str(trial.pop("eligibility_text", ""))
        count = sum(
            1
            for line in text.splitlines()
            if line.strip().lstrip("*- ").strip()
            and "criteria" not in line.strip().casefold()
        )
        trial["criteria_count"] = max(count, 1)
        trial["processing_state"] = "REVIEW_REQUIRED"
        trial["updated_at"] = datetime.now(UTC)
        return {
            "protocol_id": protocol_id,
            "processing_run_id": f"DEMO-EXTRACT-{uuid4().hex[:8].upper()}",
            "model": "offline-source-parser",
            "extracted_count": trial["criteria_count"],
            "reviewed_count": 0,
            "manual_review_count": trial["criteria_count"],
            "rejected_count": 0,
            "processing_state": "REVIEW_REQUIRED",
        }

    def import_synthetic_cohort(self, cohort_name: str, rows: list[dict]) -> dict:
        patients = []
        for row in rows:
            patients.append(
                _patient(
                    row["patient_id"],
                    row["site_id"],
                    age=row.get("age"),
                    diagnosis=row.get("diagnoses"),
                    metformin=row.get("metformin_mg_day"),
                    hba1c=row.get("hba1c"),
                    bmi=row.get("bmi"),
                    recent_cv_event=row.get("recent_cv_event"),
                    renal_impairment=row.get("renal_impairment"),
                    contradictory_key=row.get("contradictory_field"),
                )
            )
        self.patients = tuple(patients)
        run_id = self.run_screening()
        return {
            "cohort_version": f"DEMO-{cohort_name.upper().replace(' ', '-')}",
            "patient_count": len(patients),
            "run_id": run_id,
            "status": "SCREENED",
        }

    def audit_events(self) -> list[dict]:
        return list(reversed(self._audit))

    def apply_task_decision(
        self,
        task_key: str,
        decision: str,
        actor: str,
        reason: str,
        edited_action: str | None,
        request_id: str,
    ) -> dict:
        task = next((item for item in self.tasks() if item["task_key"] == task_key), None)
        if task is None:
            raise ValueError("Synthetic coordinator task was not found")
        next_status = {
            "APPROVE": "APPROVED",
            "EDIT": "OPEN",
            "REJECT": "REJECTED",
            "DISMISS": "DISMISSED",
        }[decision]
        self._task_states[task_key] = next_status
        event = {
            "event_id": f"DEMO-{uuid4().hex[:10].upper()}",
            "event_type": "COPILOT_TASK_DECISION" if request_id.startswith("copilot-") else "TASK_DECISION",
            "actor": actor,
            "entity_type": "COORDINATOR_TASK",
            "entity_id": task_key,
            "prior_state": {"status": task["status"]},
            "new_state": {"status": next_status, "action_type": edited_action or task["action_type"]},
            "reason": reason,
            "source_run_id": self.run_id,
            "occurred_at": datetime.now(UTC),
        }
        self._audit.append(event)
        return {"task_key": task_key, "status": next_status, "decision": decision}

    def operations(self) -> dict:
        rows = self.dashboard()["patients"]
        sites: dict[str, dict] = {}
        for patient in rows:
            site = sites.setdefault(
                patient["site_id"],
                {
                    "site_id": patient["site_id"],
                    "candidate_count": 0,
                    "potential_match_count": 0,
                    "missing_information_count": 0,
                    "manual_review_count": 0,
                    "excluded_count": 0,
                    "average_evidence_completeness": 0,
                },
            )
            site["candidate_count"] += 1
            key = {
                "POTENTIAL_MATCH": "potential_match_count",
                "MISSING_INFORMATION": "missing_information_count",
                "MANUAL_REVIEW": "manual_review_count",
                "EXCLUDED": "excluded_count",
            }[patient["status"]]
            site[key] += 1
            site["average_evidence_completeness"] += patient["evidence_completeness"]
        for site in sites.values():
            site["average_evidence_completeness"] = round(
                site["average_evidence_completeness"] / site["candidate_count"], 2
            )
        return {"run_id": self.run_id, "sites": sorted(sites.values(), key=lambda s: s["site_id"])}


repository = DemoRepository()
