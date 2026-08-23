# Prefer an environment variable so CI / different machines can override it
import os
import subprocess
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chinese_learning.app import app
from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import User, UserId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.base import Base

# Import models so they register with Base.metadata
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.models import (
    CharacterKnowledgeModel,  # pyright: ignore[reportUnusedImport]
    VocabularyKnowledgeModel,  # pyright: ignore[reportUnusedImport]
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)


def _is_postgres_ready() -> bool:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.test.yml",
            "exec",
            "-T",
            "postgres-test",
            "pg_isready",
            "-U",
            "chinese",
            "-d",
            "chinese_learning_test",
        ],
        capture_output=True,
    )
    return result.returncode == 0


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    """Start the test Postgres container once per test session."""
    print("\n→ Starting test Postgres container...")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.test.yml", "up", "-d"],
        check=True,
    )

    # Wait until healthy
    for _ in range(30):
        if _is_postgres_ready():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Postgres test container failed to become ready")

    yield

    print("\n→ Stopping test Postgres container...")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.test.yml", "down", "-v"],
        check=True,
    )


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://chinese:chinese@localhost:5433/chinese_learning_test",
)


@pytest.fixture
def learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def other_learner_id() -> LearnerId:
    return LearnerId(str(uuid4()))


@pytest.fixture
def make_vocabulary_knowledge() -> Callable[..., VocabularyKnowledge]:
    def _factory(**overrides: Any) -> VocabularyKnowledge:
        defaults = {
            "learner_id": LearnerId("learner-1"),
            "vocabulary_id": VocabularyId("vocab-1"),
            "status": KnowledgeStatus.NEW,
            "successful_recalls": 0,
            "failed_recalls": 0,
            "times_seen": 0,
            "times_produced": 0,
            "first_seen_at": None,
            "last_practised_at": None,
            "last_seen_at": None,
            "next_review_at": None,
            "ease_factor": None,
            "interval_days": None,
        }
        defaults.update(overrides)
        return VocabularyKnowledge(**defaults)

    return _factory


@pytest.fixture
def make_character_knowledge() -> Callable[..., CharacterKnowledge]:
    def _factory(**overrides: Any) -> CharacterKnowledge:
        defaults = {
            "learner_id": LearnerId("learner-1"),
            "character": Character("学"),
            "status": KnowledgeStatus.NEW,
            "successful_recognitions": 0,
            "failed_recognitions": 0,
            "correct_pinyin_count": 0,
            "times_seen": 0,
            "first_seen_at": None,
            "last_practised_at": None,
            "last_seen_at": None,
            "next_review_at": None,
        }
        defaults.update(overrides)
        return CharacterKnowledge(**defaults)

    return _factory


@pytest.fixture
def make_vocabulary_item() -> Callable[..., VocabularyItem]:
    def _factory(**overrides: Any) -> VocabularyItem:
        defaults = {
            "id": VocabularyId(str(uuid4())),
            "text": "你好",
            "pinyin": "nǐhǎo",
            "meaning": "hello",
        }
        defaults.update(overrides)
        return VocabularyItem(**defaults)

    return _factory


@pytest.fixture
def make_category() -> Callable[..., Category]:
    def _factory(**overrides: Any) -> Category:
        defaults = {
            "name": "HSK 3",
            "parent_id": None,
            "type": CategoryType.HSK,
            "sort_order": 0,
            "id": CategoryId(str(uuid4())),
            "hsk_level": 3,
        }
        defaults.update(overrides)
        return Category(**defaults)

    return _factory


@pytest.fixture
def make_user() -> Callable[..., User]:
    def _factory(**overrides: Any) -> User:
        defaults = {
            "id": UserId(str(uuid4())),
            "email": "example@email.com",
            "display_name": "User Name",
            "created_at": datetime.now(UTC),
        }

        defaults.update(overrides)
        return User(**defaults)

    return _factory


@pytest.fixture
def make_learner_profile() -> Callable[..., LearnerProfile]:
    def _factory(**overrides: Any) -> LearnerProfile:
        defaults = {
            "id": LearnerId(str(uuid4())),
            "user_id": UserId("User-1"),
            "language": "zh-CN",
            "display_name": "Chinese Learner",
            "created_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return LearnerProfile(**defaults)

    return _factory


@pytest_asyncio.fixture(scope="function")
async def db_session():

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

    # Drop all tables after the test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def cedict_dictionary() -> CedictDictionary:
    # Resolves to: chinese_learning/infrastructure/nlp/data/cedict.txt
    dict_path = (
        Path(__file__).resolve().parents[1]  # Go up to backend/
        / "src"
        / "chinese_learning"
        / "infrastructure"
        / "nlp"
        / "data"
        / "cedict.txt"
    )
    return CedictDictionary(dict_path)


@pytest_asyncio.fixture(scope="function")
async def db_session_populated():

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        cat_repo = CategoryRepository(session)

        uncategorised_cat = Category(
            id=CategoryId(value=str(uuid4())),
            name="Uncategorised",
            type=CategoryType.SYSTEM,
        )
        await cat_repo.save(uncategorised_cat)

        # 2. Seed HSK 1 through 7 Categories
        for level in range(1, 8):
            hsk_cat = Category(
                id=CategoryId(value=str(uuid4())),
                name=f"HSK {level}",
                type=CategoryType.HSK,
                hsk_level=level,
                sort_order=level,
            )
            await cat_repo.save(hsk_cat)

        await session.commit()

        yield session
        await session.rollback()

    # Drop all tables after the test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(
    db_session_populated: AsyncSession,
) -> AsyncGenerator[AsyncClient]:
    async def _get_test_db() -> AsyncIterator[AsyncSession]:
        yield db_session_populated

    app.dependency_overrides[get_db_session] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
