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


def test_protocol_contract_contains_reviewed_source_clauses():
    response = client.get("/api/protocol")
    assert response.status_code == 200
    payload = response.json()
    assert payload["protocol"]["protocol_id"] == "NCT00749190"
    assert len(payload["criteria"]) == 7
    assert all(item["source_clause"] for item in payload["criteria"])


def test_worklist_excludes_prescreen_exclusions():
    items = client.get("/api/tasks").json()["items"]
    assert len(items) == 7
    assert {item["source_status"] for item in items} == {
        "POTENTIAL_MATCH",
        "MISSING_INFORMATION",
        "MANUAL_REVIEW",
    }


def test_operations_rolls_up_all_three_sites():
    payload = client.get("/api/operations").json()
    assert len(payload["sites"]) == 3
    assert sum(site["candidate_count"] for site in payload["sites"]) == 12


def test_edit_decision_requires_an_edited_action():
    response = client.post(
        "/api/tasks/example-task/decision",
        json={"decision": "EDIT", "actor": "tester", "reason": "verified evidence"},
    )
    assert response.status_code == 422


def test_copilot_routes_answers_and_unsafe_requests():
    answered = client.post("/api/copilot/query", json={"query": "Why is P004 in manual review?"})
    refused = client.post("/api/copilot/query", json={"query": "Enroll P001 automatically"})

    assert answered.status_code == 200
    assert answered.json()["state"] == "ANSWERED"
    assert answered.json()["proposal"]["proposal_id"]
    assert refused.status_code == 200
    assert refused.json()["state"] == "REFUSED"
