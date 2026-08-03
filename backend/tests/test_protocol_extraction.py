import json

import pytest

from app.services.protocol_extraction import (
    ProtocolExtractionError,
    validate_extracted_criteria,
)


def test_validated_extraction_preserves_exact_source_clause():
    source = "Inclusion Criteria:\nAdults age 18 years or older."
    payload = json.dumps(
        {
            "criteria": [
                {
                    "criterion_type": "INCLUSION",
                    "source_clause": "Adults age 18 years or older.",
                    "clinical_concept": "age",
                    "review_notes": "Human review required.",
                }
            ]
        }
    )
    result = validate_extracted_criteria(payload, source)
    assert result[0].source_clause == "Adults age 18 years or older."


def test_extraction_rejects_invented_clause():
    payload = '[{"criterion_type":"INCLUSION","source_clause":"Invented criterion"}]'
    with pytest.raises(ProtocolExtractionError):
        validate_extracted_criteria(payload, "Adults age 18 years or older.")
