"""Bounded, evidence-grounded Coordinator Assistant behavior.

The assistant routes only TrialOps/ATLAS operational intents. Deterministic
screening results remain authoritative; language generation is used only to
explain governed facts when the Snowflake repository provides Cortex AI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


SUPPORTED_INTENTS = {
    "PATIENT_EXPLANATION",
    "MISSING_INFORMATION",
    "SHORTLIST",
    "SITE_COMPARISON",
    "RECRUITMENT_SLOWDOWN",
    "COMPLIANCE_SUMMARY",
}

_PATIENT_PATTERN = re.compile(r"\bP\d{3}\b", re.IGNORECASE)
_PROPOSALS: dict[str, dict[str, str]] = {}
_PROPOSAL_LOCK = Lock()


@dataclass(frozen=True)
class CopilotProposal:
    proposal_id: str
    task_key: str
    action_type: str
    reason: str
    label: str


def _patient_id(query: str, context_patient_id: str | None) -> str | None:
    match = _PATIENT_PATTERN.search(query)
    return (match.group(0) if match else context_patient_id or "").upper() or None


def _classify(query: str, patient_id: str | None) -> tuple[str, str]:
    text = query.casefold()
    if any(word in text for word in ("enroll", "diagnose", "treat", "prescribe", "order a test", "medical advice")):
        return "UNSAFE", "ATLAS cannot provide treatment advice, confirm enrollment, or order clinical tests."
    if any(word in text for word in ("what should i do", "why is", "explain", "why did", "evidence")) and patient_id:
        return "PATIENT_EXPLANATION", "patient explanation"
    if any(word in text for word in ("missing", "blocked", "need evidence", "incomplete")):
        return "MISSING_INFORMATION", "missing-information review"
    if any(word in text for word in ("shortlist", "potential match", "candidates", "patients", "who can")):
        return "SHORTLIST", "candidate shortlist"
    if any(word in text for word in ("site", "sites", "workload", "compare")):
        return "SITE_COMPARISON", "site comparison"
    if any(word in text for word in ("slow", "recruitment", "enrollment", "enrolment", "forecast")):
        return "RECRUITMENT_SLOWDOWN", "recruitment operations"
    if any(word in text for word in ("compliance", "visit", "consent", "deviation", "report")):
        return "COMPLIANCE_SUMMARY", "compliance review"
    if not query.strip():
        return "CLARIFY", "Ask about a candidate, missing evidence, sites, recruitment, or compliance."
    return "CLARIFY", "I can answer questions about candidates, evidence, sites, recruitment, and compliance."


def _citation(source: str, label: str) -> dict[str, str]:
    return {"label": label, "source": source}


def _proposal(task: dict, reason: str) -> CopilotProposal:
    proposal = CopilotProposal(
        proposal_id=f"proposal-{uuid4().hex[:12]}",
        task_key=str(task["task_key"]),
        action_type=str(task["action_type"]),
        reason=reason,
        label="Approve coordinator action",
    )
    with _PROPOSAL_LOCK:
        _PROPOSALS[proposal.proposal_id] = {
            "task_key": proposal.task_key,
            "action_type": proposal.action_type,
            "reason": proposal.reason,
        }
    return proposal


def confirm_proposal(proposal_id: str) -> dict[str, str] | None:
    with _PROPOSAL_LOCK:
        return _PROPOSALS.pop(proposal_id, None)


def _cortex_answer(repository, question: str, draft: str, citations: list[dict[str, str]]) -> tuple[str, str]:
    """Ask Snowflake Cortex to polish a grounded draft when available.

    The deterministic draft is the fallback for local fixtures and for accounts
    where the selected model is not granted. Cortex never changes the status or
    creates an action; it only explains the supplied facts.
    """
    explain = getattr(repository, "cortex_explain", None)
    if explain is None:
        return draft, "governed-screening-context"
    generated = explain(question, draft, citations)
    return generated or draft, "claude-sonnet-4-6" if generated else "governed-screening-context"


def answer_query(repository, query: str, context_patient_id: str | None = None) -> dict:
    patient_id = _patient_id(query, context_patient_id)
    intent, intent_label = _classify(query, patient_id)
    base = {
        "query": query,
        "intent": intent,
        "intent_label": intent_label,
        "grounded": False,
        "model": "deterministic-router",
        "citations": [],
        "proposal": None,
    }
    if intent == "UNSAFE":
        return {**base, "state": "REFUSED", "answer": intent_label}
    if intent == "CLARIFY":
        return {**base, "state": "CLARIFICATION", "answer": intent_label}

    dashboard = repository.dashboard()
    if intent == "PATIENT_EXPLANATION":
        detail = repository.patient_detail(patient_id) if patient_id else None
        if detail is None:
            return {**base, "state": "CLARIFICATION", "answer": "I could not find that synthetic candidate. Use a candidate ID such as P004."}
        unresolved = [
            item for item in detail["criteria"]
            if item["status"] in {"UNKNOWN", "CONTRADICTORY"}
        ]
        answer = (
            f"{detail['patient_id']} is **{str(detail['status']).replace('_', ' ').title()}**. "
            f"The governed run has {len(unresolved)} unresolved criterion(s). "
        )
        if unresolved:
            answer += "The coordinator should verify: " + ", ".join(item["criterion_id"] for item in unresolved) + "."
        else:
            answer += "All reviewed machine-evaluable criteria have a recorded result; this remains pre-screening support, not enrollment confirmation."
        citations = [
            _citation(item["protocol_citation"], "Protocol clause")
            for item in detail["criteria"][:3]
        ]
        citations.extend(
            _citation(item["patient_citation"], "Patient evidence")
            for item in detail["criteria"][:3]
            if item["patient_citation"]
        )
        proposal = None
        task = next((item for item in repository.tasks() if item["patient_id"] == patient_id), None)
        if task and detail["status"] in {"MISSING_INFORMATION", "MANUAL_REVIEW", "POTENTIAL_MATCH"}:
            proposal = _proposal(task, f"Coordinator review for {patient_id}: {answer}")
        answer, model = _cortex_answer(repository, query, answer, citations)
        response = {**base, "state": "ANSWERED", "answer": answer, "citations": citations, "proposal": proposal.__dict__ if proposal else None, "grounded": True, "model": model}
        return response

    patients = dashboard["patients"]
    if intent == "SHORTLIST":
        matches = [item for item in patients if item["status"] == "POTENTIAL_MATCH"]
        answer = f"There are {len(matches)} potential match(es) in the latest governed run: " + ", ".join(item["patient_id"] for item in matches) + ". Each still requires coordinator verification against the remaining protocol clauses."
        citations = [_citation(dashboard["run"]["run_id"], "Screening run")]
        answer, model = _cortex_answer(repository, query, answer, citations)
        return {**base, "state": "ANSWERED", "answer": answer, "grounded": True, "model": model, "citations": citations}
    if intent == "MISSING_INFORMATION":
        missing = [item for item in patients if item["status"] == "MISSING_INFORMATION"]
        answer = f"{len(missing)} candidate(s) need evidence work: " + ", ".join(item["patient_id"] for item in missing) + ". ATLAS recommends locating existing records; it does not order tests or infer missing values."
        return {**base, "state": "ANSWERED", "answer": answer, "grounded": True, "model": "governed-screening-context", "citations": [_citation(dashboard["run"]["run_id"], "Screening run")]}
    if intent == "SITE_COMPARISON":
        operations = repository.operations()
        busiest = max(operations["sites"], key=lambda site: site["missing_information_count"] + site["manual_review_count"], default=None)
        if busiest is None:
            return {**base, "state": "ANSWERED", "answer": "No site workload is available in the current governed run.", "grounded": True}
        answer = f"{busiest['site_id']} has the highest evidence-review load in the current run, with {busiest['missing_information_count']} missing-information case(s) and {busiest['manual_review_count']} manual-review case(s)."
        return {**base, "state": "ANSWERED", "answer": answer, "grounded": True, "model": "governed-site-rollup", "citations": [_citation(operations["run_id"], "Operations rollup")]}
    if intent == "RECRUITMENT_SLOWDOWN":
        return {**base, "state": "ANSWERED", "answer": "The current ATLAS demo has candidate workload by site, but it does not yet contain historical enrollment velocity. I cannot produce a defensible recruitment forecast from this dataset. The next governed input would be historical screening, enrollment, dropout, and capacity observations.", "grounded": True, "model": "scope-guardrail", "citations": [_citation(dashboard["run"]["run_id"], "Current run scope")]}
    if intent == "COMPLIANCE_SUMMARY":
        return {**base, "state": "ANSWERED", "answer": "The current cohort contains screening evidence and coordinator tasks, but no visit/consent/report records are loaded into the deployed demo. ATLAS therefore cannot claim a compliance alert from this run.", "grounded": True, "model": "scope-guardrail", "citations": [_citation(dashboard["run"]["run_id"], "Current run scope")]}
    return {**base, "state": "CLARIFICATION", "answer": "Please rephrase that as a TrialOps question about a candidate, evidence, sites, recruitment, or compliance."}
