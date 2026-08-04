import pytest

from app.services.clinicaltrials import TrialSyncError, normalize_nct_id, normalize_public_trial


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("NCT00749190", "NCT00749190"),
        ("https://clinicaltrials.gov/study/NCT01234567", "NCT01234567"),
        ("nct07654321", "NCT07654321"),
    ],
)
def test_normalize_nct_id(source, expected):
    assert normalize_nct_id(source) == expected


def test_normalize_nct_id_rejects_non_registry_source():
    with pytest.raises(TrialSyncError):
        normalize_nct_id("https://example.com/protocol.pdf")


def test_normalize_public_trial_rejects_a_mismatched_record():
    payload = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT00000002",
                "briefTitle": "Different study",
            }
        }
    }

    with pytest.raises(TrialSyncError, match="does not match"):
        normalize_public_trial("NCT00000001", payload)
