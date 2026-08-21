import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.persistence.repositories.text_analysis.character_repository import (
    CharacterRepository,
)


@pytest.mark.asyncio
async def test_character_get_returns_none_when_missing(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    assert await repo.get("学") is None


@pytest.mark.asyncio
async def test_character_save_and_get(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    char = Character("学")

    await repo.save(char)
    await db_session.commit()

    loaded = await repo.get("学")
    assert loaded is not None
    assert loaded.symbol == "学"
    assert str(loaded) == "学"


@pytest.mark.asyncio
async def test_character_save_is_idempotent(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    char = Character("好")

    await repo.save(char)
    await repo.save(char)  # second save should not raise
    await db_session.commit()

    assert await repo.exists("好") is True


@pytest.mark.asyncio
async def test_character_save_many(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    chars = [Character("一"), Character("二"), Character("三")]

    await repo.save_many(chars)
    await db_session.commit()

    results = await repo.get_many(["一", "二", "三", "不存在"])
    assert len(results) == 3
    symbols = {c.symbol for c in results}
    assert symbols == {"一", "二", "三"}


@pytest.mark.asyncio
async def test_character_get_many_empty(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    assert await repo.get_many([]) == []


@pytest.mark.asyncio
async def test_character_exists(db_session: AsyncSession):
    repo = CharacterRepository(db_session)
    await repo.save(Character("中"))
    await db_session.commit()

    assert await repo.exists("中") is True
    assert await repo.exists("国") is False
