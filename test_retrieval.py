from app.services.retrieval_service import retrieve

results = retrieve(
    "What is the GATE paper code?",
    top_k=3,
    min_score=0.30,
)

for result in results:
    print(
        "--- CHUNK",
        result["chunk_id"],
        "| SCORE",
        f'{result["score"]:.3f}',
        "| PAGES",
        result["page_numbers"],
        "---",
    )

    print(result["text"])
    print()