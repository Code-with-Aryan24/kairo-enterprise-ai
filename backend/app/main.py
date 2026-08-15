from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.routes import router
from app.api.health import router as health_router
from app.api.chat import router as chat_router

app = FastAPI(
    title="KAIRO Enterprise AI Platform",
    description="The Right Intelligence. At The Right Time.",
    version="0.1.0"
)

# Allow React frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)