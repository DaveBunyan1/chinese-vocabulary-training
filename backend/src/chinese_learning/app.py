from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chinese_learning.infrastructure.telemetry.config import settings
from chinese_learning.infrastructure.telemetry.logging import setup_logging
from chinese_learning.presentation.rest.routers import (
    categories,
    character_dashboard,
    practice,
    progress,
    review_queue,
    text_import,
    vocabulary_dashboard,
)

logger = structlog.get_logger()


def _get_version() -> str:
    try:
        return version("chinese-learning")
    except PackageNotFoundError:
        return "0.1.0"


APP_VERSION = _get_version()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger.info(
        "Application starting",
        environment=settings.ENVIRONMENT,
        version=APP_VERSION,
    )
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Chinese Learning Platform API",
    description=(
        "Domain-driven API for Chinese vocabulary training: "
        "text import, knowledge tracking, practice, and dashboards."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Local Vite (port 3000 per vite.config) and common alternates
_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict[str, str]:
    """Liveness probe used by local checks and container orchestration."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": APP_VERSION,
    }


app.include_router(text_import.router, prefix="/api/v1")
app.include_router(practice.router, prefix="/api/v1")
app.include_router(vocabulary_dashboard.router, prefix="/api/v1")
app.include_router(character_dashboard.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(review_queue.router, prefix="/api/v1")
