"""Validation for model-produced protocol clause extraction."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class ExtractedCriterion(BaseModel):
    criterion_type: Literal["INCLUSION", "EXCLUSION"]
    source_clause: str = Field(min_length=3, max_length=4000)
    clinical_concept: str | None = Field(default=None, max_length=200)
    review_notes: str = Field(default="AI-extracted draft; human review required.", max_length=500)


class ProtocolExtractionError(RuntimeError):
    """Cortex output did not satisfy the governed extraction contract."""


def validate_extracted_criteria(raw: str, eligibility_text: str) -> list[ExtractedCriterion]:
    try:
        decoded: object = raw
        for _ in range(3):
            if not isinstance(decoded, str):
                break
            value = decoded.strip()
            if value.startswith("```"):
                value = value.removeprefix("```json").removeprefix("```")
                value = value.removesuffix("```").strip()
            decoded = json.loads(value)
        items = decoded.get("criteria") if isinstance(decoded, dict) else decoded
        criteria = [ExtractedCriterion.model_validate(item) for item in items]
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        raise ProtocolExtractionError("Cortex returned malformed criterion JSON.") from exc
    if not criteria:
        raise ProtocolExtractionError("Cortex returned no eligibility criteria.")
    normalized_source = " ".join(eligibility_text.split())
    for criterion in criteria:
        if " ".join(criterion.source_clause.split()) not in normalized_source:
            raise ProtocolExtractionError(
                "An extracted clause was not an exact passage from the public source."
            )
    return criteria
