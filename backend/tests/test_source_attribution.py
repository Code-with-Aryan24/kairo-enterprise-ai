
from app.services.source_attribution_service import validate_citations
from app.services.source_attribution_service import validate_claims

SAMPLE_CONTEXTS = [
    {
        "document_id": "doc-001",
        "chunk_id": 0,
        "page_numbers": [1, 2],
        "page_segments": [
            {
                "page_number": 1,
                "text": "Employee name: Aryan Pandey. Degree: B.Tech.",
            },
            {
                "page_number": 2,
                "text": "Specialization: Computer Science and Engineering.",
            },
        ],
    }
]


def test_valid_citation_is_accepted():
    citations = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_number": 1,
            "supporting_text": "Employee name: Aryan Pandey.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert len(result) == 1
    assert result[0]["page_number"] == 1


def test_unknown_document_is_rejected():
    citations = [
        {
            "document_id": "fake-doc",
            "chunk_id": 0,
            "page_number": 1,
            "supporting_text": "Employee name: Aryan Pandey.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert result == []


def test_unknown_chunk_is_rejected():
    citations = [
        {
            "document_id": "doc-001",
            "chunk_id": 99,
            "page_number": 1,
            "supporting_text": "Employee name: Aryan Pandey.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert result == []


def test_invalid_page_number_is_rejected():
    citations = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_number": 5,
            "supporting_text": "Employee name: Aryan Pandey.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert result == []


def test_evidence_not_present_on_cited_page_is_rejected():
    citations = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_number": 1,
            "supporting_text": "Specialization: Computer Science and Engineering.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert result == []


def test_evidence_from_correct_page_is_accepted():
    citations = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_number": 2,
            "supporting_text": "Specialization: Computer Science and Engineering.",
        }
    ]

    result = validate_citations(citations, SAMPLE_CONTEXTS)

    assert len(result) == 1
    assert result[0]["page_number"] == 2


def test_empty_citations_return_empty_list():
    result = validate_citations([], SAMPLE_CONTEXTS)

    assert result == []


def test_claim_with_valid_citation_is_accepted():
    claims = [
        {
            "text": "The qualification is B.Tech.",
            "citations": [
                {
                    "document_id": "doc-001",
                    "chunk_id": 0,
                    "page_number": 1,
                    "supporting_text": "Degree: B.Tech.",
                }
            ],
        }
    ]

    contexts = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_segments": [
                {
                    "page_number": 1,
                    "text": "Degree: B.Tech.",
                }
            ],
        }
    ]

    result = validate_claims(claims, contexts)

    assert len(result) == 1
    assert result[0]["text"] == "The qualification is B.Tech."


def test_claim_without_citations_is_rejected():
    claims = [
        {
            "text": "The candidate graduated in 2028.",
            "citations": [],
        }
    ]

    result = validate_claims(claims, SAMPLE_CONTEXTS)

    assert result == []


def test_claim_with_fabricated_evidence_is_rejected():
    claims = [
        {
            "text": "The candidate graduated in 2028.",
            "citations": [
                {
                    "document_id": "doc-001",
                    "chunk_id": 0,
                    "page_number": 1,
                    "supporting_text": "Graduated in 2028.",
                }
            ],
        }
    ]

    result = validate_claims(claims, SAMPLE_CONTEXTS)

    assert result == []


def test_invalid_claim_does_not_remove_valid_claim():
    claims = [
        {
            "text": "Unsupported claim.",
            "citations": [],
        },
        {
            "text": "The degree is B.Tech.",
            "citations": [
                {
                    "document_id": "doc-001",
                    "chunk_id": 0,
                    "page_number": 1,
                    "supporting_text": "Degree: B.Tech.",
                }
            ],
        },
    ]

    contexts = [
        {
            "document_id": "doc-001",
            "chunk_id": 0,
            "page_segments": [
                {
                    "page_number": 1,
                    "text": "Degree: B.Tech.",
                }
            ],
        }
    ]

    result = validate_claims(claims, contexts)

    assert len(result) == 1
    assert result[0]["text"] == "The degree is B.Tech."
