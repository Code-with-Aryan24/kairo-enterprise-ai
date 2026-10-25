
import json
import os
import tempfile
from pathlib import Path

from app.services.embedding_service import embed_chunks


DOCUMENT_ID = "287198bd-0cf6-4bf4-b447-9e249f4b60f6"
CHUNKS_DIR = Path("storage/chunks")
CHUNK_FILE = CHUNKS_DIR / f"{DOCUMENT_ID}.json"


def main():
    if not CHUNK_FILE.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {CHUNK_FILE}"
        )

    # Load the existing document without changing its text.
    data = json.loads(
        CHUNK_FILE.read_text(encoding="utf-8")
    )

    if data.get("document_id") != DOCUMENT_ID:
        raise ValueError(
            "Document ID in the chunk file does not match."
        )

    chunks = data.get("chunks", [])

    if not chunks:
        raise ValueError("No chunks found in the document.")

    # Repair only chunks with missing or empty embeddings.
    missing_indices = [
        index
        for index, chunk in enumerate(chunks)
        if not isinstance(chunk.get("embedding"), list)
        or not chunk["embedding"]
    ]

    if not missing_indices:
        print("No missing embeddings found. Nothing to repair.")
        return

    texts = [
        chunks[index]["text"]
        for index in missing_indices
    ]

    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunks to repair: {missing_indices}")

    # Reuse KAIRO's existing embedding model and implementation.
    new_embeddings = embed_chunks(texts)

    if len(new_embeddings) != len(missing_indices):
        raise RuntimeError(
            "Embedding count does not match the number of chunks."
        )

    # Validate all new embeddings before modifying the data.
    for embedding in new_embeddings:
        if not embedding:
            raise RuntimeError("Generated an empty embedding.")

        if not all(
            isinstance(value, (int, float))
            and __import__("math").isfinite(value)
            for value in embedding
        ):
            raise RuntimeError(
                "Generated an invalid or non-finite embedding."
            )

    expected_dimensions = data.get("embedding_dimensions")

    if expected_dimensions is not None:
        for embedding in new_embeddings:
            if len(embedding) != expected_dimensions:
                raise RuntimeError(
                    f"Expected {expected_dimensions} dimensions, "
                    f"received {len(embedding)}."
                )

    # Apply the new vectors only to the affected chunks.
    for index, embedding in zip(
        missing_indices,
        new_embeddings,
    ):
        chunks[index]["embedding"] = embedding

    data["chunks"] = chunks

    # Write to a temporary file first, then replace atomically.
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CHUNKS_DIR,
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(data, temp_file, indent=2)

        os.replace(temp_path, CHUNK_FILE)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()

    print("\nEmbedding repair completed successfully.")
    print(f"Updated file: {CHUNK_FILE}")

    for index in missing_indices:
        embedding = chunks[index]["embedding"]
        print(
            f"Chunk {chunks[index]['chunk_id']}: "
            f"{len(embedding)} dimensions"
        )


if __name__ == "__main__":
    main()
