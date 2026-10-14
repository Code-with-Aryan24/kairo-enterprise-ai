
import json
import re
from pathlib import Path

import numpy as np

from app.services.embedding_service import embed_text


CHUNKS_DIR = Path("storage/chunks")

# Common words that add little value to keyword matching.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "which", "who", "whom", "where", "when",
    "why", "how", "do", "does", "did", "for", "of",
    "in", "on", "at", "to", "from", "with", "and",
    "or", "my", "me", "i", "it", "this", "that",
    "be", "listed", "provided", "mentioned", "tell",
    "give", "please",
}


def cosine_similarity(vector_a, vector_b):
    vector_a = np.array(vector_a, dtype=float)
    vector_b = np.array(vector_b, dtype=float)

    denominator = (
        np.linalg.norm(vector_a)
        * np.linalg.norm(vector_b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b) / denominator
    )


def load_chunks():
    chunks = []

    if not CHUNKS_DIR.exists():
        return chunks

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        try:
            data = json.loads(
                chunk_file.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"Skipping unreadable chunk file "
                f"{chunk_file}: {exc}"
            )
            continue

        for chunk in data.get("chunks", []):
            # Ignore legacy chunks without embeddings.
            if "embedding" not in chunk:
                continue

            chunks.append(
                {
                    "document_id": data["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "page_numbers": chunk.get(
                        "page_numbers", []
                    ),
                    "embedding": chunk["embedding"],
                }
            )

    return chunks


def tokenize(text):
    """Normalize text and extract word tokens."""
    return re.findall(r"\b\w+\b", text.lower())


def meaningful_tokens(text):
    """Remove common words that add little search value."""
    return [
        token
        for token in tokenize(text)
        if token not in STOPWORDS
    ]


def keyword_score(query, text):
    """
    Score meaningful query-word overlap.

    Uses meaningful query tokens as the denominator so common
    words do not dilute the score.
    """
    query_words = set(meaningful_tokens(query))
    text_words = set(meaningful_tokens(text))

    if not query_words:
        return 0.0

    matched_words = query_words.intersection(text_words)

    return len(matched_words) / len(query_words)


def field_match_bonus(query, text):
    """
    Give a modest ranking boost to chunks likely to contain
    the requested document field.

    This improves ranking; it does not infer or invent values.
    """
    query_text = query.lower()
    document_text = text.lower()

    bonus = 0.0

    # Qualifying-degree / education questions.
    degree_query = any(
        phrase in query_text
        for phrase in (
            "qualifying degree",
            "degree",
            "graduation",
            "educational qualification",
        )
    )

    if degree_query:
        education_indicators = (
            "graduated",
            "year of graduation",
            "computer science",
            "engineering",
            "engg",
            "b.tech",
            "b. tech",
            "bachelor",
            "degree",
            "diploma",
            "qualification",
        )

        matched_indicators = sum(
            1
            for indicator in education_indicators
            if indicator in document_text
        )

        # Reward chunks with actual education details more
        # than chunks that only mention eligibility requirements.
        if matched_indicators >= 2:
            bonus += 0.15
        elif any(
            indicator in document_text
            for indicator in (
                "graduated",
                "year of graduation",
                "computer science",
                "bachelor",
                "b.tech",
                "b. tech",
            )
        ):
            bonus += 0.08

    # GATE paper-code questions.
    code_query = (
        "paper code" in query_text
        or "gate code" in query_text
    )

    if code_query:
        if "paper code" in document_text:
            bonus += 0.15
        elif "gate" in document_text and re.search(
            r"\b(?:cs|ec|ee|me|ce|da|ma|ph|ch)\b",
            document_text,
        ):
            bonus += 0.08

    return bonus


def retrieve(query, top_k=3, min_score=0.30):
    query_embedding = embed_text(query)
    chunks = load_chunks()

    scored_chunks = []

    for chunk in chunks:
        semantic_score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        lexical_score = keyword_score(
            query,
            chunk["text"],
        )

        field_bonus = field_match_bonus(
            query,
            chunk["text"],
        )

        combined_score = (
            0.7 * semantic_score
            + 0.3 * lexical_score
            + field_bonus
        )

        scored_chunks.append(
            {
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "page_numbers": chunk["page_numbers"],
                "score": combined_score,
                "semantic_score": semantic_score,
                "keyword_score": lexical_score,
                "field_bonus": field_bonus,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    filtered_chunks = [
        chunk
        for chunk in scored_chunks
        if chunk["score"] >= min_score
    ]

    return filtered_chunks[:top_k]
