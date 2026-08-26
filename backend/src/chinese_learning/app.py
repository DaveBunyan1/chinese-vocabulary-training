from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chinese_learning.infrastructure.telemetry.config import settings
from chinese_learning.infrastructure.telemetry.logging import setup_logging
from chinese_learning.presentation.rest.routers import practice, text_import

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger.info("Application starting", environment=settings.ENVIRONMENT)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Chinese Learning Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local Vite dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(text_import.router, prefix="/api/v1")
app.include_router(practice.router, prefix="/api/v1")
