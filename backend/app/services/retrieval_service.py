
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

    if vector_a.shape != vector_b.shape:
        return 0.0

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

    return float(np.dot(vector_a, vector_b) / denominator)


def load_chunks():
    """Load valid chunks and skip those with invalid embeddings."""
    chunks = []

    if not CHUNKS_DIR.exists():
        print(f"Chunks directory not found: {CHUNKS_DIR}")
        return chunks

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        # Do not load backup files as active document data.
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
        "page_numbers": chunk.get("page_numbers") or [],
        "page_segments": chunk.get("page_segments") or [],
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

    degree_query = any(       #used for specific phrases
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

        if matched_patterns >= 3:
            bonus += 0.30
        elif matched_patterns >= 1:
            bonus += 0.18

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


# Month names used to recognize employment date ranges.
MONTH_PATTERN = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)

DATE_RANGE_PATTERN = re.compile(
    rf"\b(?:{MONTH_PATTERN})\s+\d{{4}}\s*[-–]\s*"
    rf"(?:(?:{MONTH_PATTERN})\s+\d{{4}}|Present|Current)\b",
    re.IGNORECASE,
)

EMPLOYMENT_TERMS = {
    "employment",
    "experience",
    "professional",
    "work",
    "job",
    "jobs",
    "role",
    "roles",
    "position",
    "positions",
    "internship",
    "internships",
    "career",
    "careers",
}

ROLE_EVIDENCE_PATTERN = re.compile(
    r"\b("
    r"intern|internship|manager|treasurer|"
    r"secretary|partner|analyst|engineer|"
    r"developer|consultant|associate|"
    r"coordinator|executive|director|"
    r"lead|assistant|videography|"
    r"content creation|"
    r")\b",
    re.IGNORECASE,
)




def is_employment_query(query):
    """Identify questions specifically about employment history."""

    tokens = set(tokenize(query))

    direct_employment_terms = {
        "employment",
        "job",
        "jobs",
        "role",
        "roles",
        "position",
        "positions",
        "internship",
        "internships",
        "career",
        "careers",
    }

    if tokens.intersection(direct_employment_terms):
        return True

    experience_terms = {
        "experience",
        "professional",
    }

    date_terms = {
        "date",
        "dates",
        "duration",
        "durations",
        "tenure",
        "timeline",
        "timelines",
    }

    return (
        bool(tokens.intersection(experience_terms))
        and bool(tokens.intersection(date_terms))
    )




def has_employment_evidence(text):
    """Check whether a chunk contains both a date range and role evidence."""
    has_dates = bool(DATE_RANGE_PATTERN.search(text))
    has_role = bool(ROLE_EVIDENCE_PATTERN.search(text))

    return has_dates and has_role




def retrieve(
    query,
    top_k=3,
    min_score=0.30,
    document_id=None,
):
    """
    Uses normal relevance filtering first. For employment-history
    questions, a conservative evidence-based fallback can recover
    chunks containing both employment date ranges and role evidence.
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
                "page_segments": chunk["page_segments"],
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

    # Normal retrieval remains the primary strategy.
    filtered_chunks = [
        chunk
        for chunk in scored_chunks
        if chunk["score"] >= min_score
    ]

    results = filtered_chunks[:top_k]

    fallback_used = False

    # Employment-specific fallback:
    # Only activate when normal retrieval returns insufficient results.
    if (
        is_employment_query(query)
        and len(results) < top_k
    ):
        existing_ids = {
            (chunk["document_id"], chunk["chunk_id"])
            for chunk in results
        }

        fallback_candidates = [
            chunk
            for chunk in scored_chunks
            if (
                (chunk["document_id"], chunk["chunk_id"])
                not in existing_ids
                and chunk["semantic_score"] >= 0.15
                and has_employment_evidence(chunk["text"])
            )
        ]

        fallback_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        if fallback_candidates:
            fallback_used = True
            results.extend(
                fallback_candidates[:top_k - len(results)]
            )

    print("\n--- KAIRO RETRIEVAL DEBUG ---")
    print("Query:", query)
    print("Minimum score:", min_score)
    print("Scored candidates:", len(scored_chunks))
    print("Candidates above threshold:", len(filtered_chunks))
    print("Employment fallback used:", fallback_used)
    print("Chunks returned:", len(results))

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
