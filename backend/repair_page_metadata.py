
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.services.document_service import process_document

DOCUMENT_ID = "d9b3829e-2da9-4992-9f69-7a89514f8943"

SOURCE_FILE = Path(
    f"storage/documents/{DOCUMENT_ID}_Profile.pdf"
)
CHUNKS_FILE = Path(
    f"storage/chunks/{DOCUMENT_ID}.json"
)

def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source PDF not found: {SOURCE_FILE}")

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Chunk JSON not found: {CHUNKS_FILE}")

    with CHUNKS_FILE.open("r", encoding="utf-8") as file:
        old_data = json.load(file)

    old_chunks = old_data.get("chunks", [])

    # Reprocess the original PDF without changing stored files.
    result = process_document(SOURCE_FILE)
    new_chunks = result["chunks"]
    embeddings = result["embeddings"]

    # Validate everything before writing.
    if not new_chunks or len(new_chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match.")

    if len(new_chunks) != len(old_chunks):
        raise ValueError(
            f"Chunk count changed: stored={len(old_chunks)}, "
            f"regenerated={len(new_chunks)}. No files were changed."
        )

    for index, embedding in enumerate(embeddings):
        if len(embedding) != 384:
            raise ValueError(
                f"Chunk {index} has {len(embedding)} dimensions, not 384."
            )

    for index, chunk in enumerate(new_chunks):
        if not chunk.get("page_numbers"):
            raise ValueError(f"Chunk {index} has no page metadata.")

    print("Validation passed.")
    print(f"Pages: {len(result['pages'])}")
    print(f"Chunks: {len(new_chunks)}")

    for index, chunk in enumerate(new_chunks):
        print(f"Chunk {index}: pages={chunk['page_numbers']}")

    # Create a timestamped backup before replacing the stored data.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = CHUNKS_FILE.with_name(
        f"{CHUNKS_FILE.stem}_{timestamp}.backup.json"
    )
    shutil.copy2(CHUNKS_FILE, backup_file)

    repaired_data = {
        **old_data,
        "chunks": [
            {
                **old_chunks[index],
                "chunk_id": index,
                "text": chunk["text"],
                "page_numbers": chunk["page_numbers"],
                "embedding": embeddings[index],
            }
            for index, chunk in enumerate(new_chunks)
        ],
    }

    # Write to a temporary file, then replace the original.
    temp_file = CHUNKS_FILE.with_suffix(".tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(repaired_data, file, ensure_ascii=False, indent=2)
        temp_file.replace(CHUNKS_FILE)
    except Exception:
        if temp_file.exists():
            temp_file.unlink()
        raise

    print(f"Repair completed: {CHUNKS_FILE}")
    print(f"Backup created: {backup_file}")

if __name__ == "__main__":
    main()
