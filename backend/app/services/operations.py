"""Missing-information, forecasting, compliance, actions, and scenario services."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from statistics import fmean

from app.domain.models import (
    ComplianceAlert,
    CoordinatorTask,
    ForecastResult,
    ScreeningResult,
    ScreeningStatus,
    SiteMetrics,
    VisitRecord,
)


def task_from_screening(result: ScreeningResult) -> CoordinatorTask | None:
    action_for = {
        ScreeningStatus.POTENTIAL_MATCH: "REVIEW_FOR_SCREENING",
        ScreeningStatus.MISSING_INFORMATION: "REQUEST_MISSING_INFORMATION",
        ScreeningStatus.MANUAL_REVIEW: "CLINICAL_REVIEW_REQUIRED",
    }
    action_type = action_for.get(result.status)
    if action_type is None:
        return None
    unresolved = [
        item.criterion_id
        for item in result.criterion_results
        if item.status in {"UNKNOWN", "CONTRADICTORY"}
    ]
    reason = (
        f"Review computed {result.status} result"
        + (f"; unresolved criteria: {', '.join(unresolved)}" if unresolved else "")
    )
    return CoordinatorTask(
        task_key=f"{result.run_id}:{result.patient_id}:{action_type}",
        patient_id=result.patient_id,
        protocol_id=result.protocol_id,
        action_type=action_type,
        status="OPEN",
        reason=reason,
        created_at=datetime.now(UTC),
    )


def forecast_site(site: SiteMetrics, *, as_of: date | None = None) -> ForecastResult:
    as_of = as_of or datetime.now(UTC).date()
    velocity = fmean(site.weekly_enrollment[-4:]) if site.weekly_enrollment else 0.0
    retained_target = site.target_enrollment / max(1.0 - site.dropout_rate, 0.01)
    remaining = max(retained_target - site.enrolled, 0.0)
    weeks = remaining / velocity if velocity > 0 else None
    completion = as_of + timedelta(weeks=weeks) if weeks is not None else None
    if velocity == 0:
        risk, recommendation = "CRITICAL", "Escalate the inactive site and review recruitment barriers."
    elif weeks and weeks > 16:
        risk, recommendation = "HIGH", "Add coordinator capacity or activate another site."
    elif weeks and weeks > 8:
        risk, recommendation = "WATCH", "Review weekly funnel conversion and referral sources."
    else:
        risk, recommendation = "ON_TRACK", "Maintain current recruitment cadence."
    return ForecastResult(
        site.site_id,
        round(velocity, 2),
        round(remaining, 1),
        round(weeks, 1) if weeks is not None else None,
        completion,
        risk,
        recommendation,
    )


def run_scenario(
    site: SiteMetrics, *, added_weekly_capacity: int = 0, dropout_delta: float = 0.0
) -> ForecastResult:
    adjusted = replace(
        site,
        weekly_enrollment=tuple(v + added_weekly_capacity for v in site.weekly_enrollment),
        dropout_rate=min(max(site.dropout_rate + dropout_delta, 0.0), 0.8),
    )
    return forecast_site(adjusted)


def detect_compliance(
    visits: Iterable[VisitRecord], *, as_of: date | None = None
) -> tuple[ComplianceAlert, ...]:
    as_of = as_of or datetime.now(UTC).date()
    alerts: list[ComplianceAlert] = []
    for visit in visits:
        if visit.completed_at is None and visit.due_date < as_of:
            alerts.append(
                ComplianceAlert(
                    f"{visit.visit_id}:MISSED_VISIT",
                    visit.patient_id,
                    "HIGH",
                    "MISSED_VISIT",
                    f"Visit {visit.visit_id} is overdue.",
                    visit.due_date,
                )
            )
        if not visit.consent_present:
            alerts.append(
                ComplianceAlert(
                    f"{visit.visit_id}:MISSING_CONSENT",
                    visit.patient_id,
                    "CRITICAL",
                    "MISSING_CONSENT",
                    "Required consent documentation is not recorded.",
                    visit.due_date,
                )
            )
        if visit.completed_at and not visit.required_report_present:
            alerts.append(
                ComplianceAlert(
                    f"{visit.visit_id}:MISSING_REPORT",
                    visit.patient_id,
                    "MEDIUM",
                    "MISSING_REPORT",
                    f"Visit {visit.visit_id} is complete but its report is missing.",
                    visit.due_date,
                )
            )
    return tuple(alerts)
