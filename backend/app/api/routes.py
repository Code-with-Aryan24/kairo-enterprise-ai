from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "product": "KAIRO",
        "version": "0.1.0",
        "status": "Running",
        "message": "Welcome to KAIRO Enterprise AI Platform"
    }