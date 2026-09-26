def chunk_text(pages, chunk_size=1000, overlap=200):
    if not pages:
        return []

    chunks = []

    combined_text = ""

    page_ranges = []

    for page in pages:
        page_text = page["text"].strip()

        if not page_text:
            continue

        start_position = len(combined_text)

        combined_text += page_text + "\n"

        end_position = len(combined_text)

        page_ranges.append(
            {
                "page_number": page["page_number"],
                "start": start_position,
                "end": end_position,
            }
        )

    start = 0
    text_length = len(combined_text)

    while start < text_length:
        end = start + chunk_size

        chunk = combined_text[start:end].strip()

        if chunk:
            chunk_page_numbers = []

            for page_range in page_ranges:
                overlaps_page = (
                    start < page_range["end"]
                    and end > page_range["start"]
                )

                if overlaps_page:
                    chunk_page_numbers.append(
                        page_range["page_number"]
                    )

            chunks.append(
                {
                    "text": chunk,
                    "page_numbers": chunk_page_numbers,
                }
            )

        start += chunk_size - overlap

    return chunks