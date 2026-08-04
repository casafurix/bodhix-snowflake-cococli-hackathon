"""Public ClinicalTrials.gov intake with stable versioning and no patient data."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_NCT_PATTERN = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)


class TrialSyncError(RuntimeError):
    """A public study could not be resolved or validated."""


def normalize_nct_id(source: str) -> str:
    match = _NCT_PATTERN.search(source.strip())
    if match is None:
        raise TrialSyncError("Enter a ClinicalTrials.gov URL or an NCT ID such as NCT00749190.")
    return match.group(0).upper()


def fetch_public_trial(source: str) -> dict:
    """Fetch and normalize one public v2 study record."""
    nct_id = normalize_nct_id(source)
    api_url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    request = Request(api_url, headers={"Accept": "application/json", "User-Agent": "ATLAS-BodhiX/0.1"})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            raise TrialSyncError(f"ClinicalTrials.gov could not find {nct_id}.") from exc
        raise TrialSyncError(f"ClinicalTrials.gov returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise TrialSyncError("ClinicalTrials.gov is temporarily unavailable. Try again shortly.") from exc

    return normalize_public_trial(nct_id, payload)


def normalize_public_trial(source: str, payload: dict) -> dict:
    """Validate and normalize a public v2 record fetched by a trusted gateway."""
    nct_id = normalize_nct_id(source)

    protocol = payload.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    conditions = protocol.get("conditionsModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    eligibility_text = str(eligibility.get("eligibilityCriteria") or "").strip()
    payload_nct_id = str(identification.get("nctId") or "").upper()
    if payload_nct_id != nct_id:
        raise TrialSyncError("The public study record does not match the requested NCT ID.")
    if not identification.get("briefTitle"):
        raise TrialSyncError("The public study record is missing its identifier or title.")

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    phases = design.get("phases") or []
    locations = contacts.get("locations") or []
    enrollment = design.get("enrollmentInfo") or {}
    return {
        "protocol_id": nct_id,
        "title": identification["briefTitle"],
        "official_title": identification.get("officialTitle"),
        "overall_status": status.get("overallStatus", "UNKNOWN"),
        "phase": ", ".join(phases) if phases else "Not provided",
        "conditions": conditions.get("conditions") or [],
        "site_count": len(locations),
        "enrollment": enrollment.get("count"),
        "last_update": (status.get("studyFirstPostDateStruct") or {}).get("date"),
        "eligibility_text": eligibility_text or "Eligibility criteria not provided.",
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}",
        "source_api_url": f"https://clinicaltrials.gov/api/v2/studies/{nct_id}",
        "source_payload": payload,
        "document_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
        "processing_state": "PENDING_EXTRACTION",
    }
