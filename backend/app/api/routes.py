from fastapi import APIRouter, HTTPException, status

from app.repositories.demo import repository

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": "demo", "snowflake": "not_connected"}


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

