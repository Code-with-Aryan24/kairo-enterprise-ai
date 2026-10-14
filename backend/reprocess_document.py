
import json
from pathlib import Path

from app.services.document_service import process_document


CHUNKS_DIR = Path("storage/chunks")
PROCESSED_DIR = Path("storage/processed")
REGISTRY_FILE = Path("storage/registry.json")

# Existing document ID from your KAIRO logs.
DOCUMENT_ID = "9cfbbb17-2d22-4d25-93d0-a3fbba8422ca"


def main():
    registry = json.loads(
        REGISTRY_FILE.read_text(encoding="utf-8")
    )

    document = next(
        (
            item for item in registry
            if item["document_id"] == DOCUMENT_ID
        ),
        None,
    )

    if document is None:
        raise RuntimeError(
            "Document ID was not found in registry.json."
        )

    pdf_path = (
        Path("storage/documents")
        / document["stored_filename"]
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Original PDF not found: {pdf_path}"
        )

    # Re-extract text, create chunks, and regenerate embeddings.
    processed = process_document(pdf_path)

    chunk_path = CHUNKS_DIR / document["chunk_filename"]
    processed_path = (
        PROCESSED_DIR / document["processed_filename"]
    )

    # Preserve existing document ID and chunk-file identity.
    chunk_data = {
        "document_id": DOCUMENT_ID,
        "chunk_size": 1000,
        "overlap": 200,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimensions": 384,
        "chunks": [
            {
                "chunk_id": index,
                "text": chunk["text"],
                "page_numbers": chunk["page_numbers"],
                "embedding": processed["embeddings"][index],
            }
            for index, chunk in enumerate(processed["chunks"])
        ],
    }

    # Write the refreshed extracted text and chunk data.
    processed_path.write_text(
        processed["text"],
        encoding="utf-8",
    )

    chunk_path.write_text(
        json.dumps(chunk_data, indent=2),
        encoding="utf-8",
    )

    # Update the existing registry entry without adding a duplicate.
    document["text_length"] = len(processed["text"])
    document["chunk_count"] = len(processed["chunks"])
    document["status"] = "processed"

    REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8",
    )

    print("Reprocessing completed.")
    print("Document ID:", DOCUMENT_ID)
    print("Chunk count:", len(processed["chunks"]))
    print("Chunk file:", chunk_path)

    for index, chunk in enumerate(processed["chunks"]):
        if (
            "Qualification Details" in chunk["text"]
            or "Computer Science & Engg." in chunk["text"]
        ):
            print(f"\n--- QUALIFICATION CHUNK {index} ---")
            print(chunk["text"])
            print("Pages:", chunk["page_numbers"]) #enter the numbers


if __name__ == "__main__":
    main()
