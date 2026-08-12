from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def embed_text(text):
    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()


def embed_chunks(chunks):
    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
    )

    return embeddings.tolist()