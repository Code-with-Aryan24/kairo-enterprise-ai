from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.health import router as health_router

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