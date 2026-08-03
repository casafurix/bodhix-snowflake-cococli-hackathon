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
