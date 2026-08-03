from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator

from app.repositories.runtime import repository
from app.services.clinicaltrials import TrialSyncError, fetch_public_trial
from app.services.copilot import answer_query, confirm_proposal

router = APIRouter(prefix="/api")


class TaskDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "EDIT", "REJECT", "DISMISS"]
    actor: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=3, max_length=500)
    edited_action: str | None = Field(default=None, max_length=100)
    request_id: str = Field(default_factory=lambda: f"api-{uuid4()}", min_length=8, max_length=100)

    @model_validator(mode="after")
    def validate_edit(self):
        if self.decision == "EDIT" and not self.edited_action:
            raise ValueError("EDIT requires edited_action")
        return self


class CopilotQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=600)
    context_patient_id: str | None = Field(default=None, pattern=r"^P\d{3}$")
    request_id: str = Field(default_factory=lambda: f"copilot-query-{uuid4()}", min_length=8, max_length=100)


class CopilotConfirmationRequest(BaseModel):
    proposal_id: str = Field(min_length=8, max_length=100)
    actor: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=3, max_length=500)
    request_id: str = Field(default_factory=lambda: f"copilot-{uuid4()}", min_length=8, max_length=100)


class TrialSyncRequest(BaseModel):
    source: str = Field(min_length=11, max_length=500)


class SyntheticPatientInput(BaseModel):
    patient_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,30}$")
    site_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,30}$")
    age: int | None = Field(default=None, ge=0, le=120)
    diagnoses: str | None = Field(default=None, max_length=300)
    metformin_mg_day: float | None = Field(default=None, ge=0, le=10000)
    hba1c: float | None = Field(default=None, ge=0, le=30)
    bmi: float | None = Field(default=None, ge=5, le=100)
    recent_cv_event: bool | None = None
    renal_impairment: bool | None = None
    contradictory_field: str | None = Field(default=None, max_length=50)


class CohortImportRequest(BaseModel):
    cohort_name: str = Field(min_length=3, max_length=80)
    synthetic_data_confirmed: Literal[True]
    patients: list[SyntheticPatientInput] = Field(min_length=1, max_length=500)


@router.get("/health")
def health() -> dict:
    if hasattr(repository, "health"):
        return repository.health()
    return {"status": "ok", "backend": "demo", "snowflake": "offline_fixture"}


@router.get("/dashboard")
def dashboard() -> dict:
    return repository.dashboard()


@router.post("/screening-runs", status_code=status.HTTP_201_CREATED)
def create_screening_run() -> dict:
    run_id = repository.run_screening()
    return {"run_id": run_id, "status": "COMPLETED"}


@router.get("/patients/{patient_id}")
def patient_detail(patient_id: str) -> dict:
    detail = repository.patient_detail(patient_id.upper())
    if detail is None:
        raise HTTPException(status_code=404, detail="Synthetic patient was not found")
    return detail


@router.get("/tasks")
def tasks() -> dict:
    return {"items": repository.tasks()}


@router.get("/protocol")
def protocol_detail() -> dict:
    return repository.protocol_detail()


@router.get("/trials")
def trials() -> dict:
    return {"items": repository.list_trials()}


@router.post("/trials/sync", status_code=status.HTTP_201_CREATED)
def sync_trial(body: TrialSyncRequest) -> dict:
    try:
        trial = fetch_public_trial(body.source)
    except TrialSyncError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return repository.ingest_protocol(trial)


@router.post("/trials/{protocol_id}/extract", status_code=status.HTTP_201_CREATED)
def extract_trial(protocol_id: str) -> dict:
    if not hasattr(repository, "extract_protocol"):
        raise HTTPException(status_code=503, detail="Protocol extraction is unavailable")
    try:
        return repository.extract_protocol(protocol_id.upper())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/cohorts/import", status_code=status.HTTP_201_CREATED)
def import_cohort(body: CohortImportRequest) -> dict:
    return repository.import_synthetic_cohort(
        body.cohort_name,
        [patient.model_dump() for patient in body.patients],
    )


@router.get("/audit-events")
def audit_events() -> dict:
    return {"items": repository.audit_events()}


@router.post("/copilot/query")
def copilot_query(body: CopilotQueryRequest) -> dict:
    return answer_query(repository, body.query, body.context_patient_id, body.request_id)


@router.post("/copilot/confirm")
def copilot_confirm(body: CopilotConfirmationRequest, request: Request) -> dict:
    proposal = confirm_proposal(body.proposal_id)
    if proposal is None:
        raise HTTPException(status_code=409, detail="This copilot proposal has expired or was already used")
    if not hasattr(repository, "apply_task_decision"):
        raise HTTPException(status_code=503, detail="Copilot actions require the governed Snowflake backend")
    actor = request.headers.get("Sf-Context-Current-User", body.actor)
    return repository.apply_task_decision(
        proposal["task_key"],
        "APPROVE",
        actor,
        body.reason,
        None,
        body.request_id,
    )


@router.get("/operations")
def operations() -> dict:
    return repository.operations()


@router.post("/tasks/{task_key}/decision")
def apply_task_decision(task_key: str, body: TaskDecisionRequest, request: Request) -> dict:
    if not hasattr(repository, "apply_task_decision"):
        raise HTTPException(
            status_code=503,
            detail="Task decisions require the governed Snowflake backend",
        )
    return repository.apply_task_decision(
        task_key,
        body.decision,
        request.headers.get("Sf-Context-Current-User", body.actor),
        body.reason,
        body.edited_action,
        body.request_id,
    )
