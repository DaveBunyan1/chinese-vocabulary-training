import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.repo_utils import logger
from chinese_learning.infrastructure.persistence.seed.categories import BASIC_CATEGORIES
from chinese_learning.infrastructure.telemetry.config import settings


async def seed_categories(session: AsyncSession) -> None:
    repo = CategoryRepository(session)
    await repo.save_many(BASIC_CATEGORIES)
    await session.commit()
    logger.info("Seeded %d basic categories", len(BASIC_CATEGORIES))


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await seed_categories(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
