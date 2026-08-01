"""Typed contracts shared by agents, persistence adapters, and the API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class CriterionType(StrEnum):
    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"


class Operator(StrEnum):
    BETWEEN = "BETWEEN"
    GTE = "GTE"
    LTE = "LTE"
    EQ = "EQ"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    EXISTS = "EXISTS"
    DAYS_SINCE_LTE = "DAYS_SINCE_LTE"


class EvidenceStatus(StrEnum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    UNKNOWN = "UNKNOWN"
    CONTRADICTORY = "CONTRADICTORY"


class ScreeningStatus(StrEnum):
    POTENTIAL_MATCH = "POTENTIAL_MATCH"
    EXCLUDED = "EXCLUDED"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class Criterion:
    criterion_id: str
    protocol_id: str
    criterion_type: CriterionType
    field: str
    operator: Operator
    source_clause: str
    source_location: str
    value: Any = None
    upper_value: Any = None
    unit: str | None = None
    machine_evaluable: bool = True
    review_status: str = "REVIEWED"


@dataclass(frozen=True)
class Evidence:
    value: Any
    source_id: str
    observed_at: date | None = None
    excerpt: str | None = None
    contradictory: bool = False


@dataclass
class PatientSnapshot:
    patient_id: str
    site_id: str
    display_name: str
    fields: dict[str, Evidence] = field(default_factory=dict)


@dataclass(frozen=True)
class CriterionResult:
    criterion_id: str
    status: EvidenceStatus
    explanation: str
    protocol_citation: str
    patient_citation: str | None


@dataclass(frozen=True)
class ScreeningResult:
    run_id: str
    protocol_id: str
    patient_id: str
    status: ScreeningStatus
    criterion_results: tuple[CriterionResult, ...]
    computed_at: datetime


@dataclass(frozen=True)
class SiteMetrics:
    site_id: str
    site_name: str
    target_enrollment: int
    enrolled: int
    weekly_enrollment: tuple[int, ...]
    dropout_rate: float
    coordinator_capacity: int


@dataclass(frozen=True)
class ForecastResult:
    site_id: str
    weekly_velocity: float
    retained_target_remaining: float
    weeks_to_target: float | None
    projected_completion: date | None
    risk: str
    recommendation: str


@dataclass(frozen=True)
class VisitRecord:
    patient_id: str
    visit_id: str
    due_date: date
    completed_at: date | None
    consent_present: bool
    required_report_present: bool


@dataclass(frozen=True)
class ComplianceAlert:
    alert_key: str
    patient_id: str
    severity: str
    alert_type: str
    message: str
    due_date: date


@dataclass(frozen=True)
class CoordinatorTask:
    task_key: str
    patient_id: str
    protocol_id: str
    action_type: str
    status: str
    reason: str
    created_at: datetime
