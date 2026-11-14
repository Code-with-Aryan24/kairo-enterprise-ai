
from typing import Any


def validate_citations(
    citations: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate generated citations against the retrieved page segments.

    A citation is accepted only if:
    1. Its document and chunk exist in retrieved contexts.
    2. Its page number exists in that chunk.
    3. Its supporting text exists in that page segment.

    Returns only validated citations.
    """

    validated = []

    # Index retrieved contexts for efficient lookup.
    context_lookup = {
        (context["document_id"], context["chunk_id"]): context
        for context in contexts
    }

    for citation in citations:
        document_id = citation.get("document_id")
        chunk_id = citation.get("chunk_id")
        page_number = citation.get("page_number")
        supporting_text = citation.get("supporting_text")

        if not all([
            document_id,
            chunk_id is not None,
            page_number is not None,
            isinstance(supporting_text, str),
            supporting_text.strip(),
        ]):
            continue

        context = context_lookup.get((document_id, chunk_id))

        if context is None:
            continue

        page_segments = context.get("page_segments", [])

        matching_segment = next(
            (
                segment
                for segment in page_segments
                if segment.get("page_number") == page_number
            ),
            None,
        )

        if matching_segment is None:
            continue

        page_text = matching_segment.get("text", "")

        if supporting_text.strip() not in page_text:
            continue

        validated.append({
            "document_id": document_id,
            "chunk_id": chunk_id,
            "page_number": page_number,
            "supporting_text": supporting_text.strip(),
        })

    return validated

def validate_claims(
    claims: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate each factual claim independently.

    A claim is retained only when at least one of its
    citations passes the existing evidence validator.
    """

    validated_claims = []

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        claim_text = claim.get("text")
        citations = claim.get("citations")

        if not isinstance(claim_text, str):
            continue

        if not claim_text.strip():
            continue

        if not isinstance(citations, list) or not citations:
            continue

        validated_citations = validate_citations(
            citations,
            contexts,
        )

        if not validated_citations:
            continue

        validated_claims.append({
            "text": claim_text.strip(),
            "citations": validated_citations,
        })

    return validated_claims
