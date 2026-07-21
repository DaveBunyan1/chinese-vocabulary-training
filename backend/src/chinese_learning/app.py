from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from chinese_learning.infrastructure.telemetry.config import settings
from chinese_learning.infrastructure.telemetry.logging import setup_logging

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


@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
