"""
Family Wellness App — FastAPI entry point.

IMPORTANT: observability.init_observability() is called FIRST so the
AnthropicInstrumentor wraps the Anthropic SDK before any client is created.
"""

from __future__ import annotations

import logging
import os

# ---------------------------------------------------------------------------
# 1. Observability MUST be initialized before importing agent or routes
#    so that AnthropicInstrumentor instruments the SDK on first import.
# ---------------------------------------------------------------------------
from observability import init_observability, is_phoenix_connected, shutdown_observability

phoenix_ok = init_observability()

# ---------------------------------------------------------------------------
# 2. Now safe to import the rest of the app
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from models import HealthCheck
from routes import chat, meal_plans, grocery, supplements, family

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    logger.info("Starting Family Wellness API...")
    try:
        client = database.get_client()
        if client:
            logger.info("Supabase client ready.")
        else:
            logger.warning("Database unavailable — running in memory-only mode.")
    except Exception as exc:
        logger.warning(f"Database init error: {exc}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    shutdown_observability()


app = FastAPI(
    title="Family Wellness API",
    description=(
        "AI-powered family meal planning, grocery lists, and supplement guidance "
        "backed by Anthropic Claude and Phoenix Arize observability."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
frontend_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(meal_plans.router, prefix="/api", tags=["Meal Plans"])
app.include_router(grocery.router, prefix="/api", tags=["Grocery"])
app.include_router(supplements.router, prefix="/api", tags=["Supplements"])
app.include_router(family.router, prefix="/api", tags=["Family"])
from routes.approvals import router as approvals_router
app.include_router(approvals_router, prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Return API health and Phoenix connection status."""
    phoenix_endpoint = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix:6006/v1/traces"
    )
    return HealthCheck(
        status="ok",
        phoenix_connected=is_phoenix_connected(),
        phoenix_endpoint=phoenix_endpoint,
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Family Wellness API is running.",
        "docs": "/docs",
        "health": "/health",
        "phoenix_ui": "http://localhost:6006",
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
