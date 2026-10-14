
import pymupdf

from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_chunks


def extract_pages_from_pdf(file_path):
    """Extract page text in a more consistent reading order."""
    pages = []

    with pymupdf.open(file_path) as document:
        for page_number, page in enumerate(document, start=1):
            pages.append(
                {
                    "page_number": page_number,
                    "text": page.get_text("text", sort=True),
                }
            )

    return pages


def extract_text_from_pdf(file_path):
    """Return extracted text from all pages."""
    pages = extract_pages_from_pdf(file_path)

    return "\n".join(
        page["text"]
        for page in pages
    )


def debug_pdf_extraction(file_path):
    """
    Compare default extraction with sorted extraction.
    Useful for investigating missing or misplaced form fields.
    """
    with pymupdf.open(file_path) as document:
        for page_number, page in enumerate(document, start=1):
            default_text = page.get_text("text")
            sorted_text = page.get_text("text", sort=True)

            print(f"\n--- PDF PAGE {page_number}: DEFAULT TEXT ---")
            print(repr(default_text))

            print(f"\n--- PDF PAGE {page_number}: SORTED TEXT ---")
            print(repr(sorted_text))


def process_document(file_path):
    """Extract, chunk, and embed a PDF document."""
    pages = extract_pages_from_pdf(file_path)

    extracted_text = "\n".join(
        page["text"]
        for page in pages
    )

    chunks = chunk_text(pages)

    chunk_texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embed_chunks(chunk_texts)

    return {
        "text": extracted_text,
        "pages": pages,
        "chunks": chunks,
        "embeddings": embeddings,
    }
