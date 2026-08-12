from fastapi import APIRouter
from pydantic import BaseModel

from app.services.retrieval_service import retrieve


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


@router.post("")
def search(request: SearchRequest):
    results = retrieve(
        request.query,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "results": results,
    }