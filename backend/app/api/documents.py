import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document_service import process_document


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)

STORAGE_DIR = Path("storage/documents")
PROCESSED_DIR = Path("storage/processed")
CHUNKS_DIR = Path("storage/chunks")
REGISTRY_FILE = Path("storage/registry.json")

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def load_registry():
    if not REGISTRY_FILE.exists():
        return []

    try:
        return json.loads(
            REGISTRY_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        return []


def save_registry(documents):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

    REGISTRY_FILE.write_text(
        json.dumps(documents, indent=2),
        encoding="utf-8",
    )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF documents are currently supported.",
        )

    document_id = str(uuid4())

    safe_filename = Path(file.filename).name
    stored_filename = f"{document_id}_{safe_filename}"

    file_path = STORAGE_DIR / stored_filename

    # Save original PDF
    contents = await file.read()
    file_path.write_bytes(contents)

    # Extract text, create chunks, and generate embeddings
    processed_data = process_document(file_path)

    extracted_text = processed_data["text"]
    chunks = processed_data["chunks"]
    embeddings = processed_data["embeddings"]

    # Save extracted text
    processed_filename = f"{document_id}.txt"
    processed_file = PROCESSED_DIR / processed_filename

    processed_file.write_text(
        extracted_text,
        encoding="utf-8",
    )

    # Save chunks and embeddings
    chunk_filename = f"{document_id}.json"
    chunk_file = CHUNKS_DIR / chunk_filename

    chunk_data = {
        "document_id": document_id,
        "chunk_size": 1000,
        "overlap": 200,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimensions": 384,
        "chunks": [
            {
                "chunk_id": index,
                "text": chunk,
                "embedding": embeddings[index],
            }
            for index, chunk in enumerate(chunks)
        ],
    }

    chunk_file.write_text(
        json.dumps(chunk_data, indent=2),
        encoding="utf-8",
    )

    # Save document metadata
    document = {
        "document_id": document_id,
        "filename": safe_filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "status": "processed",
        "stored_filename": stored_filename,
        "processed_filename": processed_filename,
        "text_length": len(extracted_text),
        "chunk_count": len(chunks),
        "chunk_filename": chunk_filename,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimensions": 384,
    }

    documents = load_registry()
    documents.append(document)
    save_registry(documents)

    return document


@router.get("")
def list_documents():
    documents = load_registry()

    return {
        "documents": documents,
        "total": len(documents),
    }