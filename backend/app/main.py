from fastapi import FastAPI

from app.api.routes import router
from app.api.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="KAIRO Enterprise AI Platform",
    description="The Right Intelligence. At The Right Time.",
    version="0.1.0"
)

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