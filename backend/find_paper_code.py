import json
from pathlib import Path


for file in Path("storage/chunks").glob("*.json"):
    data = json.loads(
        file.read_text(encoding="utf-8")
    )

    for chunk in data.get("chunks", []):
        if "paper code" in chunk["text"].lower():
            print("DOCUMENT:", data["document_id"])
            print("CHUNK:", chunk["chunk_id"])
            print("PAGES:", chunk.get("page_numbers", []))
            print()
            print(chunk["text"])
            print()