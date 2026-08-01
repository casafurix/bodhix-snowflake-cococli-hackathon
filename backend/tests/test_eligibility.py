from datetime import UTC, datetime

from app.domain.models import (
    Criterion,
    CriterionType,
    Evidence,
    Operator,
    PatientSnapshot,
    ScreeningStatus,
)
from app.services.eligibility import screen_patient


def criteria():
    return (
        Criterion("INC-AGE", "NCT00749190", CriterionType.INCLUSION, "age", Operator.BETWEEN, "Age >=18 and <80 years", "Eligibility #5", 18, 79),
        Criterion("INC-HBA1C", "NCT00749190", CriterionType.INCLUSION, "hba1c", Operator.BETWEEN, "HbA1c >7.0% to 10.0%", "Eligibility #4", 7.0, 10.0, "%"),
        Criterion("EX-MI", "NCT00749190", CriterionType.EXCLUSION, "recent_mi", Operator.EQ, "Myocardial infarction within 6 months", "Exclusion #1", True),
    )


def patient(**overrides):
    fields = {
        "age": Evidence(52, "PATIENTS.P001"),
        "hba1c": Evidence(8.2, "LAB_RESULTS.P001.HBA1C", datetime.now(UTC).date()),
        "recent_mi": Evidence(False, "DIAGNOSES.P001"),
    }
    fields.update(overrides)
    return PatientSnapshot("P001", "SITE-01", "Patient 001", fields)


def test_potential_match_when_all_inclusions_pass_and_exclusions_do_not():
    assert screen_patient("NCT00749190", patient(), criteria()).status == ScreeningStatus.POTENTIAL_MATCH


def test_excluded_when_inclusion_fails():
    result = screen_patient(
        "NCT00749190", patient(hba1c=Evidence(6.4, "LAB_RESULTS.P001.HBA1C")), criteria()
    )
    assert result.status == ScreeningStatus.EXCLUDED


def test_missing_information_fails_closed():
    missing = patient()
    del missing.fields["hba1c"]
    assert screen_patient("NCT00749190", missing, criteria()).status == ScreeningStatus.MISSING_INFORMATION


def test_contradictory_information_requires_manual_review():
    result = screen_patient(
        "NCT00749190",
        patient(hba1c=Evidence(8.1, "LAB_AND_NOTE", contradictory=True)),
        criteria(),
    )
    assert result.status == ScreeningStatus.MANUAL_REVIEW
