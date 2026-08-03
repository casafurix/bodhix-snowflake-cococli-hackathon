from app.repositories.demo import repository
from app.services.copilot import answer_query, confirm_proposal


def test_copilot_answers_from_governed_candidate_context():
    result = answer_query(repository, "Why is P004 in manual review?")

    assert result["state"] == "ANSWERED"
    assert result["intent"] == "PATIENT_EXPLANATION"
    assert "P004" in result["answer"]
    assert result["grounded"] is True
    assert result["citations"]
    assert result["proposal"]
    assert result["copilot_run_id"].startswith("COPILOT-")
    assert result["run_record_status"] == "LOCAL_ONLY"
    assert [step["agent"] for step in result["agent_trace"]] == [
        "Protocol Intelligence",
        "Patient Screening",
        "Evidence Retrieval",
        "Coordinator Copilot",
        "Human Approval Gate",
    ]
    assert result["agent_trace"][-1]["status"] == "AWAITING_APPROVAL"


def test_copilot_clarifies_unknown_questions_and_refuses_unsafe_ones():
    clarification = answer_query(repository, "Tell me something unrelated")
    refusal = answer_query(repository, "Enroll P001 automatically")

    assert clarification["state"] == "CLARIFICATION"
    assert refusal["state"] == "REFUSED"


def test_copilot_proposal_is_single_use():
    result = answer_query(repository, "What should I do for P008?")
    proposal_id = result["proposal"]["proposal_id"]

    assert confirm_proposal(proposal_id)
    assert confirm_proposal(proposal_id) is None


def test_copilot_generates_a_grounded_coordinator_briefing():
    result = answer_query(repository, "Give me a daily coordinator briefing")

    assert result["state"] == "ANSWERED"
    assert result["intent"] == "COORDINATOR_SUMMARY"
    assert "Coordinator briefing" in result["answer"]
    assert len(result["citations"]) == 2
    assert result["agent_trace"][-1]["status"] == "NO_MUTATION"
