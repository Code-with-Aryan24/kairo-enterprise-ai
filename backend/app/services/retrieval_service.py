import json
from pathlib import Path

import numpy as np

from app.services.embedding_service import embed_text


CHUNKS_DIR = Path("storage/chunks")


def cosine_similarity(vector_a, vector_b):
    vector_a = np.array(vector_a)
    vector_b = np.array(vector_b)

    return float(
        np.dot(vector_a, vector_b)
        / (
            np.linalg.norm(vector_a)
            * np.linalg.norm(vector_b)
        )
    )


def load_chunks():
    chunks = []

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        data = json.loads(
            chunk_file.read_text(encoding="utf-8")
        )

        for chunk in data.get("chunks", []):

            # Ignore chunks created before embeddings
            # were integrated into the pipeline.
            if "embedding" not in chunk:
                continue

            chunks.append(
                {
                    "document_id": data["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "embedding": chunk["embedding"],
                }
            )

    return chunks


def retrieve(query, top_k=3, min_score=0.35):
    query_embedding = embed_text(query)

    chunks = load_chunks()

    scored_chunks = []

    for chunk in chunks:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        scored_chunks.append(
            {
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "score": score,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    scored_chunks = [
    chunk
    for chunk in scored_chunks
    if chunk["score"] >= min_score
   ]

    return scored_chunks[:top_k]