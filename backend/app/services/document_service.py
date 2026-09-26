import pymupdf

from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_chunks


def extract_pages_from_pdf(file_path):
    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        pages.append(
            {
                "page_number": page_number,
                "text": page.get_text(),
            }
        )

    document.close()

    return pages


def extract_text_from_pdf(file_path):
    pages = extract_pages_from_pdf(file_path)

    return "\n".join(
        page["text"]
        for page in pages
    )


def process_document(file_path):
    pages = extract_pages_from_pdf(file_path)

    extracted_text = "\n".join(
        page["text"]
        for page in pages
    )

    chunks = chunk_text(extracted_text)

    embeddings = embed_chunks(chunks)

    return {
        "text": extracted_text,
        "pages": pages,
        "chunks": chunks,
        "embeddings": embeddings,
    }