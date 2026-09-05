from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


@pytest.mark.asyncio
async def test_vocabulary_item_get_returns_none_when_missing(db_session: AsyncSession):
    repo = VocabularyItemRepository(db_session)
    assert await repo.get(VocabularyId(str(uuid4()))) is None


@pytest.mark.asyncio
async def test_vocabulary_item_save_and_get(
    db_session: AsyncSession, make_vocabulary_item: Callable[..., VocabularyItem]
):
    repo = VocabularyItemRepository(db_session)
    item = make_vocabulary_item(
        text="学习", pinyin="xuéxí", meaning="to study / to learn"
    )

    await repo.save(item)
    await db_session.commit()

    loaded = await repo.get(item.id)
    assert loaded is not None
    assert loaded.id == item.id
    assert loaded.text == "学习"
    assert loaded.pinyin == "xuéxí"
    assert loaded.meaning == "to study / to learn"


@pytest.mark.asyncio
async def test_vocabulary_item_save_updates_existing(
    db_session: AsyncSession, make_vocabulary_item: Callable[..., VocabularyItem]
):
    repo = VocabularyItemRepository(db_session)
    item = make_vocabulary_item(meaning="old meaning")
    await repo.save(item)
    await db_session.commit()

    updated = make_vocabulary_item(
        id=str(item.id),
        text=item.text,
        pinyin=item.pinyin,
        meaning="new meaning",
    )
    await repo.save(updated)
    await db_session.commit()

    loaded = await repo.get(item.id)
    assert loaded is not None
    assert loaded.meaning == "new meaning"


@pytest.mark.asyncio
async def test_vocabulary_item_get_by_text(
    db_session: AsyncSession, make_vocabulary_item: Callable[..., VocabularyItem]
):
    repo = VocabularyItemRepository(db_session)
    item = make_vocabulary_item(text="中文")
    await repo.save(item)
    await db_session.commit()

    loaded = await repo.get_by_text("中文")
    assert len(loaded) == 1
    assert loaded[0].id == item.id

    assert await repo.get_by_text("不存在") == []


@pytest.mark.asyncio
async def test_vocabulary_item_save_many_and_get_many(
    db_session: AsyncSession, make_vocabulary_item: Callable[..., VocabularyItem]
):
    repo = VocabularyItemRepository(db_session)
    items = [
        make_vocabulary_item(text="一"),
        make_vocabulary_item(text="二"),
        make_vocabulary_item(text="三"),
    ]
    await repo.save_many(items)
    await db_session.commit()

    results = await repo.get_many([i.id for i in items] + [VocabularyId(str(uuid4()))])
    assert len(results) == 3
    texts = {r.text for r in results}
    assert texts == {"一", "二", "三"}


@pytest.mark.asyncio
async def test_vocabulary_item_exists(
    db_session: AsyncSession, make_vocabulary_item: Callable[..., VocabularyItem]
):
    repo = VocabularyItemRepository(db_session)
    item = make_vocabulary_item()
    await repo.save(item)
    await db_session.commit()

    assert await repo.exists(item.id) is True
    assert await repo.exists(VocabularyId(str(uuid4()))) is False
