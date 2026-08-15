from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.generation_service import generate_rag_answer


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@router.post("")
def chat(request: ChatRequest):
    result = generate_rag_answer(
        request.query,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "answer": result["answer"],
        "sources": result["sources"],
    }