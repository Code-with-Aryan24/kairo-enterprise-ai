import pymupdf

from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_chunks


def extract_text_from_pdf(file_path):
    document = pymupdf.open(file_path)

    pages = []

    for page in document:
        pages.append(page.get_text())

    document.close()

    return "\n".join(pages)


def process_document(file_path):
    extracted_text = extract_text_from_pdf(file_path)

    chunks = chunk_text(extracted_text)

    embeddings = embed_chunks(chunks)

    return {
        "text": extracted_text,
        "chunks": chunks,
        "embeddings": embeddings,
    }