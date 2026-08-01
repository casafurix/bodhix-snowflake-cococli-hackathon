from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_every_safe_branch():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    counts = response.json()["run"]["counts"]
    assert all(counts[status] > 0 for status in counts)


def test_patient_detail_has_two_sided_citations():
    detail = client.get("/api/patients/P001").json()
    assert detail["status"] == "POTENTIAL_MATCH"
    assert all(item["protocol_citation"] for item in detail["criteria"])
    assert all(item["patient_citation"] for item in detail["criteria"])


def test_unknown_patient_returns_404():
    assert client.get("/api/patients/DOES_NOT_EXIST").status_code == 404

