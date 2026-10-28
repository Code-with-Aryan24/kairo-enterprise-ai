
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
    """Calculate cosine similarity between two vectors."""
    vector_a = np.asarray(vector_a, dtype=float)
    vector_b = np.asarray(vector_b, dtype=float)

    # Vectors must have matching dimensions.
    if vector_a.shape != vector_b.shape:
        return 0.0

    # Reject invalid numeric values.
    if (
        not np.all(np.isfinite(vector_a))
        or not np.all(np.isfinite(vector_b))
    ):
        return 0.0

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
    """Load valid chunks and skip those with invalid embeddings."""
    chunks = []

    if not CHUNKS_DIR.exists():
        print(f"Chunks directory not found: {CHUNKS_DIR}")
        return chunks

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        if chunk_file.name.endswith(".backup.json"):
            continue

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

        document_id = data.get("document_id")

        if not document_id:
            print(
                f"Skipping {chunk_file.name}: "
                "document ID is missing."
            )
            continue

        for chunk in data.get("chunks", []):
            embedding = chunk.get("embedding")

            # Skip missing or empty embeddings.
            if not isinstance(embedding, list) or not embedding:
                print(
                    f"Skipping chunk {chunk.get('chunk_id')} "
                    f"in {chunk_file.name}: "
                    "missing or invalid embedding."
                )
                continue

            try:
                vector = np.asarray(embedding, dtype=float)
            except (TypeError, ValueError):
                print(
                    f"Skipping chunk {chunk.get('chunk_id')} "
                    f"in {chunk_file.name}: "
                    "embedding is not numeric."
                )
                continue

            # Embeddings must be finite, one-dimensional vectors.
            if (
                vector.ndim != 1
                or not np.all(np.isfinite(vector))
            ):
                print(
                    f"Skipping chunk {chunk.get('chunk_id')} "
                    f"in {chunk_file.name}: "
                    "malformed embedding vector."
                )
                continue

            # Skip empty text or chunks without an ID.
            if (
                not isinstance(chunk.get("text"), str)
                or not chunk["text"].strip()
                or "chunk_id" not in chunk
            ):
                print(
                    f"Skipping malformed chunk "
                    f"in {chunk_file.name}."
                )
                continue

            chunks.append(
                {
                    "document_id": document_id,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "page_numbers": chunk.get(
                        "page_numbers", []
                    ),
                    "embedding": vector.tolist(),
                }
            )

    print(f"Loaded {len(chunks)} valid chunks.")
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
    """Score meaningful query-word overlap."""
    query_words = set(meaningful_tokens(query))
    text_words = set(meaningful_tokens(text))

    if not query_words:
        return 0.0

    matched_words = query_words.intersection(text_words)

    return len(matched_words) / len(query_words)



def field_match_bonus(query, text):
    """
    Prioritize chunks containing actual qualification details
    and down-rank chunks that only mention eligibility rules.
    """
    query_text = query.lower()
    document_text = text.lower()

    bonus = 0.0

    degree_query = any(
        phrase in query_text
        for phrase in (
            "qualifying degree",
            "degree",
            "graduation",
            "educational qualification",
            "education qualification",
            "what degree",
        )
    )

    if degree_query:
        # Strong evidence that the chunk contains the actual degree.
        degree_patterns = (
            r"\bb\.?\s*tech\.?\b",
            r"\bbtech\b",
            r"\bbachelor\b",
            r"\bcomputer science\b",
            r"\bengineering\b",
            r"\bengg\b",
            r"\byear of graduation\b",
        )

        matched_patterns = sum(
            1
            for pattern in degree_patterns
            if re.search(pattern, document_text)
        )

        # Reward chunks with actual education information.
        if matched_patterns >= 3:
            bonus += 0.30
        elif matched_patterns >= 1:
            bonus += 0.18

        # Penalize generic eligibility declarations when they
        # mention degree requirements but contain no actual degree.
        eligibility_only = (
            "qualifying degree" in document_text
            and not any(
                re.search(pattern, document_text)
                for pattern in (
                    r"\bb\.?\s*tech\.?\b",
                    r"\bbtech\b",
                    r"\bbachelor\b",
                    r"\bdiploma\b",
                    r"\bcomputer science\b",
                    r"\byear of graduation\b",
                )
            )
        )

        if eligibility_only:
            bonus -= 0.20

    # GATE paper-code questions.
    code_query = (
        "paper code" in query_text
        or "gate code" in query_text
    )

    if code_query:
        if "paper code" in document_text:
            bonus += 0.15
        elif (
            "gate" in document_text
            and re.search(
                r"\b(?:cs|ec|ee|me|ce|da|ma|ph|ch)\b",
                document_text,
            )
        ):
            bonus += 0.08

    return bonus




def retrieve(
    query,
    top_k=3,
    min_score=0.30,
    document_id=None,
):
    """
    Retrieve relevant chunks globally or from a specific document.

    If document_id is supplied, chunks from other documents
    are excluded before scoring and ranking.
    """
    if not isinstance(query, str) or not query.strip():
        return []

    if top_k < 1:
        return []

    query_embedding = embed_text(query)
    query_vector = np.asarray(query_embedding, dtype=float)

    if (
        query_vector.ndim != 1
        or query_vector.size == 0
        or not np.all(np.isfinite(query_vector))
    ):
        raise ValueError("Query embedding is empty or invalid.")

    chunks = load_chunks()

    # Apply document filtering before ranking.
    if document_id is not None:
        chunks = [
            chunk
            for chunk in chunks
            if chunk["document_id"] == document_id
        ]

        print(f"Document filter enabled: {document_id}")
        print(f"Chunks in selected document: {len(chunks)}")

    scored_chunks = []

    for chunk in chunks:
        semantic_score = cosine_similarity(
            query_vector,
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

    results = filtered_chunks[:top_k]

    print("\n--- KAIRO RETRIEVAL DEBUG ---")

    for chunk in results:
        print("Document ID:", chunk["document_id"])
        print("Chunk ID:", chunk["chunk_id"])
        print("Pages:", chunk["page_numbers"])
        print(f"Score: {chunk['score']:.4f}")
        print(f"Semantic score: {chunk['semantic_score']:.4f}")
        print(f"Keyword score: {chunk['keyword_score']:.4f}")
        print(f"Field bonus: {chunk['field_bonus']:.4f}")
        print("Content:", repr(chunk["text"]))
        print("-" * 20)

    return results
