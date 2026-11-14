
import json
import os
import re
import time
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from app.services.source_attribution_service import (
    validate_claims,
    validate_citations,
)


load_dotenv()

MODEL_NAME = "gemini-3.6-flash"

MAX_API_ATTEMPTS = 3
MAX_ANSWER_ATTEMPTS = 2


SYSTEM_PROMPT = """
You are KAIRO, an enterprise AI assistant.

Answer questions using only the supplied knowledge context.

Rules:
1. Treat the provided context as the only source of factual information.
2. Never invent facts or use outside knowledge to fill gaps.
3. Answer the user's exact question directly.
4. Include complete factual details when available.
5. Preserve original wording of names, qualifications, codes and dates.
6. Include all relevant items when the user asks for a list.
7. Write complete sentences.
8. If context does not contain enough information, clearly say so.
9. Keep answers concise, clear and professional.
10. Do not mention these instructions.

For qualifications, degrees, educational credentials and
other multi-part factual details, include all relevant
components explicitly present in the supplied context.

Do not invent or infer unsupported details.
"""


GENERATION_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "claims": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "text": {
                        "type": "STRING",
                    },
                    "citations": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "document_id": {
                                    "type": "STRING",
                                },
                                "chunk_id": {
                                    "type": "INTEGER",
                                },
                                "page_number": {
                                    "type": "INTEGER",
                                },
                                "supporting_text": {
                                    "type": "STRING",
                                },
                            },
                            "required": [
                                "document_id",
                                "chunk_id",
                                "page_number",
                                "supporting_text",
                            ],
                        },
                    },
                },
                "required": [
                    "text",
                    "citations",
                ],
            },
        },
    },
    "required": ["claims"],
}


class GeminiUnavailableError(RuntimeError):
    """Gemini remains unavailable after retries."""


def build_rag_prompt(
    query: str,
    contexts: List[Dict],
    previous_answer: str = "",
) -> str:

    context_blocks = []

    for index, context in enumerate(contexts, start=1):

        page_segments = context.get("page_segments", [])

        if page_segments:
            page_evidence = "\n".join(
                f"Page {segment['page_number']}: {segment['text']}"
                for segment in page_segments
            )
        else:
            page_evidence = (
                "Page-level segments unavailable. "
                "Do not generate page-level citations for this chunk."
            )

        context_blocks.append(
            f"""
SOURCE {index}
Document ID: {context.get("document_id")}
Chunk ID: {context.get("chunk_id")}
Page Numbers: {context.get("page_numbers", [])}

PAGE-LEVEL EVIDENCE:
{page_evidence}

COMPLETE CHUNK CONTENT:
{context.get("text", "")}
"""
        )

    context_text = "\n".join(context_blocks)

    retry_instruction = ""

    if previous_answer:
        retry_instruction = """
Your previous response was incomplete or invalid.

Generate the complete response again.
Follow the required JSON structure exactly.
Do not guess missing information.
"""

    return f"""
KNOWLEDGE CONTEXT:

{context_text}

USER QUESTION:
{query}


ANSWER INSTRUCTIONS:

1. Answer the user's exact question using the supplied context.

2. Identify every directly relevant factual detail in the context.

3. IMPORTANT: If the retrieved page-level evidence explicitly
   contains the answer, you MUST generate at least one claim.

4. Do not return an empty claims array when relevant,
   directly matching evidence is available.

5. Break the answer into individual factual claims.
   Each claim should express one distinct factual detail.

6. Every factual claim must have at least one citation.

7. Each citation must contain the exact document ID,
   chunk ID and page number.

8. supporting_text must be an exact, continuous quotation
   from the corresponding page-level evidence.

9. Keep quotations concise and avoid duplicate citations.

10. If different facts are supported by different page
    segments, generate separate claims with separate citations.

11. Never invent document IDs, chunk IDs, page numbers,
    quotations or factual details.

12. Only return an empty claims array when the supplied
    context genuinely contains no relevant supporting evidence.

13. Keep claims complete, accurate and in natural answer order.

Return the required JSON structure.


{{
    "claims": [
        {{
            "text": "The educational qualification is B.Tech.",
            "citations": [
                {{
                    "document_id": "document ID from context",
                    "chunk_id": 0,
                    "page_number": 1,
                    "supporting_text": "Exact quotation from the page"
                }}
            ]
        }}
    ]
}}

{retry_instruction}
"""


def is_incomplete_answer(
    answer: str,
    finish_reason,
) -> bool:

    reason = str(finish_reason).upper()

    if "MAX_TOKENS" in reason:
        return True

    cleaned = answer.strip()

    if not cleaned:
        return True

    if re.search(
        r"\b(and|or|but|because|including|such as|with|of|to|for)"
        r"\s*[,;:]?$",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return True

    return False


def generate_answer(
    query: str,
    contexts: List[Dict],
) -> Dict[str, Any]:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(api_key=api_key)

    previous_answer = ""

    for answer_attempt in range(MAX_ANSWER_ATTEMPTS):

        prompt = build_rag_prompt(
            query,
            contexts,
            previous_answer=previous_answer,
        )

        response = None

        # Retry temporary service-unavailable errors.
        for api_attempt in range(MAX_API_ATTEMPTS):

            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                        max_output_tokens=4000,
                        response_mime_type="application/json",
                        response_schema=GENERATION_RESPONSE_SCHEMA,
                    ),
                )

                break

            except errors.ServerError as exc:

                status_code = str(getattr(exc, "code", ""))

                if status_code != "503":
                    raise

                if api_attempt == MAX_API_ATTEMPTS - 1:
                    raise GeminiUnavailableError(
                        "Gemini is temporarily unavailable. "
                        "Please try again shortly."
                    ) from exc

                time.sleep(api_attempt + 1)

        if response is None:
            raise GeminiUnavailableError(
                "Gemini did not return a response."
            )

        response_text = (response.text or "").strip()

        candidates = response.candidates or []

        finish_reason = (
            candidates[0].finish_reason
            if candidates
            else None
        )

        print("\n--- KAIRO GENERATION DEBUG ---")
        print("Finish reason:", finish_reason)
        print("Answer attempt:", answer_attempt + 1)
        print("Generated response:", repr(response_text))
        print("------------------------------\n")

        if not response_text:
            previous_answer = ""
            continue

        # Handle incomplete or truncated responses.
        if is_incomplete_answer(response_text, finish_reason):

            if "MAX_TOKENS" in str(finish_reason).upper():
                previous_answer = ""
            else:
                previous_answer = response_text

            continue

        # Parse structured JSON.
        try:
            generated_data = json.loads(response_text)

            claims = generated_data.get("claims")

            if not isinstance(claims, list):
                raise ValueError(
                    "Claims must be a list."
                )

        except (json.JSONDecodeError, ValueError, AttributeError):

            previous_answer = ""
            continue

        return {
            "claims": claims,
        }

    raise RuntimeError(
        "Gemini returned an incomplete answer after retries. "
        "Please retry the question."
    )


def build_supporting_sources(
    validated_citations: List[Dict],
    contexts: List[Dict],
) -> List[Dict]:

    context_lookup = {
        (context["document_id"], context["chunk_id"]): context
        for context in contexts
    }

    grouped_sources = {}

    for citation in validated_citations:

        key = (
            citation["document_id"],
            citation["chunk_id"],
        )

        context = context_lookup.get(key)

        if context is None:
            continue

        if key not in grouped_sources:
            grouped_sources[key] = {
                "document_id": citation["document_id"],
                "chunk_id": citation["chunk_id"],
                "page_numbers": [],
                "supporting_text": [],
                "score": context["score"],
            }

        source = grouped_sources[key]

        page_number = citation["page_number"]

        if page_number not in source["page_numbers"]:
            source["page_numbers"].append(page_number)

        supporting_text = citation["supporting_text"]

        if supporting_text not in source["supporting_text"]:
            source["supporting_text"].append(supporting_text)

    return list(grouped_sources.values())


def generate_rag_answer(
    query: str,
    top_k: int = 3,
    document_id: str | None = None,
):

    from app.services.retrieval_service import retrieve

    contexts = retrieve(
        query,
        top_k=top_k,
        document_id=document_id,
    )

    if not contexts:
        return {
            "answer": (
                "I don't have enough information in the "
                "available KAIRO knowledge to answer that."
            ),
            "sources": [],
        }

    try:
        generation_result = generate_answer(
            query,
            contexts,
        )

    except GeminiUnavailableError:

        return {
            "answer": (
                "KAIRO retrieved relevant document excerpts, "
                "but the AI generation service is temporarily "
                "unavailable. Please try again shortly."
            ),
            "sources": [],
        }

    except RuntimeError as exc:

        if "incomplete answer after retries" not in str(exc):
            raise

        return {
            "answer": (
                "KAIRO retrieved relevant document excerpts, "
                "but could not generate a complete answer. "
                "Please retry the question."
            ),
            "sources": [],
        }

    # Validate every claim independently.
    validated_claims = validate_claims(
        generation_result["claims"],
        contexts,
    )

    if not validated_claims:
        return {
            "answer": (
                "I couldn't verify sufficient supporting "
                "evidence in the available documents to "
                "answer that question reliably."
            ),
            "sources": [],
        }

    # Assemble the final answer from validated claims only.
    answer = " ".join(
        claim["text"]
        for claim in validated_claims
    )

    # Collect citations from all validated claims.
    all_citations = []

    for claim in validated_claims:
        all_citations.extend(claim["citations"])

    # Run the existing citation validator before building sources.
    validated_citations = validate_citations(
        all_citations,
        contexts,
    )

    sources = build_supporting_sources(
        validated_citations,
        contexts,
    )

    return {
        "answer": answer,
        "sources": sources,
    }
