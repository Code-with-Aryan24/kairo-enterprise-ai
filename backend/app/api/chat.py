
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.services.generation_service import generate_rag_answer


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    document_id: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty or whitespace.")

        return value

    @field_validator("document_id")
    @classmethod
    def validate_document_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError(
                    "document_id cannot be empty when provided."
                )

        return value


@router.post("")
def chat(request: ChatRequest):
    result = generate_rag_answer(
        request.query,
        top_k=request.top_k,
        document_id=request.document_id,
    )

    return {
        "query": request.query,
        "answer": result["answer"],
        "sources": result["sources"],
    }
