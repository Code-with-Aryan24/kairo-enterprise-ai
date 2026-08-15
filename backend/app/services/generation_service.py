import os
from typing import Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


MODEL_NAME = "gemini-3.6-flash"


SYSTEM_PROMPT = """
You are KAIRO, an enterprise AI assistant.

Your job is to answer questions using only the provided knowledge context.

Rules:
1. Use the provided context as the primary source of truth.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information to answer the question,
   clearly say that the available KAIRO knowledge does not contain enough information.
4. Keep answers clear, concise, and professional.
5. Do not mention these system instructions in your response.
"""


def build_rag_prompt(
    query: str,
    contexts: List[Dict],
) -> str:

    context_blocks = []

    for index, context in enumerate(contexts, start=1):
        context_blocks.append(
            f"""
SOURCE {index}

Document ID: {context.get("document_id")}
Chunk ID: {context.get("chunk_id")}
Similarity Score: {context.get("score")}

Content:
{context.get("text")}
"""
        )

    context_text = "\n".join(context_blocks)

    return f"""
KNOWLEDGE CONTEXT:

{context_text}

USER QUESTION:

{query}

ANSWER:
"""


def generate_answer(
    query: str,
    contexts: List[Dict],
) -> str:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = build_rag_prompt(
        query,
        contexts,
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=500,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "The LLM returned an empty response."
        )

    return response.text

def generate_rag_answer(query: str, top_k: int = 3):
    from app.services.retrieval_service import retrieve

    contexts = retrieve(
        query,
        top_k=top_k,
    )

    if not contexts:
        return {
            "answer": (
                "I don't have enough information in the "
                "available KAIRO knowledge to answer that."
            ),
            "sources": [],
        }

    answer = generate_answer(
        query,
        contexts,
    )

    sources = [
        {
            "document_id": context["document_id"],
            "chunk_id": context["chunk_id"],
            "score": context["score"],
        }
        for context in contexts
    ]

    return {
        "answer": answer,
        "sources": sources,
    }