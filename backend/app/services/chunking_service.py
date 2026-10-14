
def chunk_text(pages, chunk_size=1000, overlap=200):
    """
    Create page-aware chunks while preferring line boundaries.

    Each returned chunk contains:
    - text
    - page_numbers

    Long lines are split only when they exceed chunk_size.
    Overlap is preserved where possible without exceeding
    the configured chunk size.
    """
    if not pages:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    # Keep each line associated with its original PDF page.
    lines = []

    for page in pages:
        page_number = page["page_number"]
        page_text = page.get("text", "")

        for raw_line in page_text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            # Split unusually long lines into manageable pieces.
            while len(line) > chunk_size:
                lines.append(
                    (line[:chunk_size], page_number)
                )
                line = line[chunk_size:]

            if line:
                lines.append((line, page_number))

    if not lines:
        return []

    chunks = []
    current_lines = []
    current_length = 0

    def emit_chunk(chunk_lines):
        if not chunk_lines:
            return

        text = "\n".join(
            line for line, _ in chunk_lines
        ).strip()

        if not text:
            return

        page_numbers = list(
            dict.fromkeys(
                page_number
                for _, page_number in chunk_lines
            )
        )

        chunks.append(
            {
                "text": text,
                "page_numbers": page_numbers,
            }
        )

    for line, page_number in lines:
        added_length = len(line) + (
            1 if current_lines else 0
        )

        # If the next line would exceed the chunk size,
        # emit the current chunk before adding that line.
        if (
            current_lines
            and current_length + added_length > chunk_size
        ):
            emit_chunk(current_lines)

            # Preserve a suffix of previous lines as overlap.
            overlap_lines = []
            overlap_length = 0

            for previous_line, previous_page in reversed(
                current_lines
            ):
                separator_length = (
                    1 if overlap_lines else 0
                )
                candidate_length = (
                    overlap_length
                    + separator_length
                    + len(previous_line)
                )

                # Reserve room for the next line.
                required_length = (
                    candidate_length
                    + 1
                    + len(line)
                )

                if (
                    candidate_length > overlap
                    or required_length > chunk_size
                ):
                    break

                overlap_lines.append(
                    (previous_line, previous_page)
                )
                overlap_length = candidate_length

            overlap_lines.reverse()
            current_lines = overlap_lines

            current_length = sum(
                len(previous_line)
                for previous_line, _ in current_lines
            ) + max(0, len(current_lines) - 1)

        separator_length = 1 if current_lines else 0

        current_lines.append((line, page_number))
        current_length += separator_length + len(line)

    # Emit the final chunk.
    emit_chunk(current_lines)

    return chunks
