from datetime import UTC, date, datetime, timedelta

from app.domain.models import SiteMetrics, VisitRecord
from app.services.operations import detect_compliance, forecast_site, run_scenario


def test_forecast_and_scenario_are_computed():
    site = SiteMetrics("S1", "North", 40, 12, (1, 2, 2, 3), 0.1, 2)
    baseline = forecast_site(site, as_of=date(2026, 8, 1))
    improved = run_scenario(site, added_weekly_capacity=2)
    assert baseline.weekly_velocity == 2.0
    assert improved.weeks_to_target < baseline.weeks_to_target


def test_compliance_detects_each_branch():
    today = datetime.now(UTC).date()
    alerts = detect_compliance(
        [
            VisitRecord("P1", "V1", today - timedelta(days=2), None, True, False),
            VisitRecord("P2", "V2", today, today, False, False),
        ],
        as_of=today,
    )
    assert {a.alert_type for a in alerts} == {"MISSED_VISIT", "MISSING_CONSENT", "MISSING_REPORT"}
