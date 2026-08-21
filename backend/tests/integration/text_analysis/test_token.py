import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.infrastructure.persistence.repositories.text_analysis.token_repository import (
    TokenRepository,
)


@pytest.mark.asyncio
async def test_token_get_returns_none_when_missing(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    assert await repo.get("学习") is None


@pytest.mark.asyncio
async def test_token_save_and_get(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    token = Token("学习")

    await repo.save(token)
    await db_session.commit()

    loaded = await repo.get("学习")
    assert loaded is not None
    assert loaded.text == "学习"


@pytest.mark.asyncio
async def test_token_save_is_idempotent(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    token = Token("中文")

    await repo.save(token)
    await repo.save(token)
    await db_session.commit()

    assert await repo.exists("中文") is True


@pytest.mark.asyncio
async def test_token_save_many(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    tokens = [Token("我"), Token("喜欢"), Token("中文")]

    await repo.save_many(tokens)
    await db_session.commit()

    results = await repo.get_many(["我", "喜欢", "中文", "不存在"])
    assert len(results) == 3
    texts = {t.text for t in results}
    assert texts == {"我", "喜欢", "中文"}


@pytest.mark.asyncio
async def test_token_get_many_empty(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    assert await repo.get_many([]) == []


@pytest.mark.asyncio
async def test_token_exists(db_session: AsyncSession):
    repo = TokenRepository(db_session)
    await repo.save(Token("测试"))
    await db_session.commit()

    assert await repo.exists("测试") is True
    assert await repo.exists("不存在") is False
