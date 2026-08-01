"""Deterministic eligibility engine used by the Patient and Eligibility agents."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from numbers import Real
from typing import Any
from uuid import uuid4

from app.domain.models import (
    Criterion,
    CriterionResult,
    CriterionType,
    Evidence,
    EvidenceStatus,
    Operator,
    PatientSnapshot,
    ScreeningResult,
    ScreeningStatus,
)


def _compare(operator: Operator, actual: Any, expected: Any, upper: Any) -> bool:
    if operator == Operator.BETWEEN:
        return isinstance(actual, Real) and expected <= actual <= upper
    if operator == Operator.GTE:
        return actual >= expected
    if operator == Operator.LTE:
        return actual <= expected
    if operator == Operator.EQ:
        return actual == expected
    if operator == Operator.CONTAINS:
        values = actual if isinstance(actual, (list, tuple, set)) else [actual]
        return any(str(expected).casefold() in str(item).casefold() for item in values)
    if operator == Operator.NOT_CONTAINS:
        values = actual if isinstance(actual, (list, tuple, set)) else [actual]
        return not any(str(expected).casefold() in str(item).casefold() for item in values)
    if operator == Operator.EXISTS:
        return actual is not None and actual != ""
    if operator == Operator.DAYS_SINCE_LTE:
        if not isinstance(actual, date):
            return False
        return (datetime.now(UTC).date() - actual).days <= int(expected)
    raise ValueError(f"Unsupported operator: {operator}")


def evaluate_criterion(criterion: Criterion, evidence: Evidence | None) -> CriterionResult:
    protocol_citation = f"{criterion.protocol_id} · {criterion.source_location}"
    if criterion.review_status != "REVIEWED" or not criterion.machine_evaluable:
        return CriterionResult(
            criterion.criterion_id,
            EvidenceStatus.UNKNOWN,
            "Criterion requires coordinator interpretation before automated use.",
            protocol_citation,
            evidence.source_id if evidence else None,
        )
    if evidence is None or evidence.value is None:
        return CriterionResult(
            criterion.criterion_id,
            EvidenceStatus.UNKNOWN,
            f"No governed evidence is available for {criterion.field}.",
            protocol_citation,
            None,
        )
    if evidence.contradictory:
        return CriterionResult(
            criterion.criterion_id,
            EvidenceStatus.CONTRADICTORY,
            f"Sources disagree about {criterion.field}; coordinator review is required.",
            protocol_citation,
            evidence.source_id,
        )
    try:
        condition_holds = _compare(
            criterion.operator, evidence.value, criterion.value, criterion.upper_value
        )
    except (TypeError, ValueError):
        return CriterionResult(
            criterion.criterion_id,
            EvidenceStatus.UNKNOWN,
            f"Evidence for {criterion.field} could not be normalized safely.",
            protocol_citation,
            evidence.source_id,
        )

    status = EvidenceStatus.MET if condition_holds else EvidenceStatus.NOT_MET
    detail = evidence.excerpt or str(evidence.value)
    return CriterionResult(
        criterion.criterion_id,
        status,
        f"{criterion.field}: {detail}",
        protocol_citation,
        evidence.source_id,
    )


def derive_status(
    criteria: Iterable[Criterion], results: Iterable[CriterionResult]
) -> ScreeningStatus:
    pairs = list(zip(criteria, results, strict=True))
    if any(result.status == EvidenceStatus.CONTRADICTORY for _, result in pairs):
        return ScreeningStatus.MANUAL_REVIEW
    if any(
        (criterion.criterion_type == CriterionType.INCLUSION and result.status == EvidenceStatus.NOT_MET)
        or (criterion.criterion_type == CriterionType.EXCLUSION and result.status == EvidenceStatus.MET)
        for criterion, result in pairs
    ):
        return ScreeningStatus.EXCLUDED
    if any(not criterion.machine_evaluable for criterion, _ in pairs):
        return ScreeningStatus.MANUAL_REVIEW
    if any(result.status == EvidenceStatus.UNKNOWN for _, result in pairs):
        return ScreeningStatus.MISSING_INFORMATION
    return ScreeningStatus.POTENTIAL_MATCH


def screen_patient(
    protocol_id: str,
    patient: PatientSnapshot,
    criteria: Iterable[Criterion],
    *,
    run_id: str | None = None,
) -> ScreeningResult:
    applicable = tuple(c for c in criteria if c.protocol_id == protocol_id)
    results = tuple(evaluate_criterion(c, patient.fields.get(c.field)) for c in applicable)
    return ScreeningResult(
        run_id=run_id or str(uuid4()),
        protocol_id=protocol_id,
        patient_id=patient.patient_id,
        status=derive_status(applicable, results),
        criterion_results=results,
        computed_at=datetime.now(UTC),
    )
