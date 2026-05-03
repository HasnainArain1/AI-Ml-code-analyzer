"""
main.py — FastAPI application entry point
"""

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from app.database import engine, Base
from app.routers import review, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    print("✅ ML Model loaded")
    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered Python code quality analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler — always return JSON ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logging.error(f"Unhandled error on {request.method} {request.url}:\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# ── Routers ──
app.include_router(review.router)
app.include_router(history.router)

# ── Static files (frontend) ──
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def serve_frontend():
    """Serve the frontend index.html."""
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "AI Code Reviewer"}
