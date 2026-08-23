from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)


@pytest.mark.asyncio
async def test_category_get_returns_none_when_missing(db_session: AsyncSession):
    repo = CategoryRepository(db_session)
    assert await repo.get(CategoryId(str(uuid4()))) is None


@pytest.mark.asyncio
async def test_category_save_and_get(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    category = make_category(
        name="Food",
        type=CategoryType.TOPIC,
        hsk_level=None,
    )

    await repo.save(category)
    await db_session.commit()

    loaded = await repo.get(category.id)
    assert loaded is not None
    assert loaded.name == "Food"
    assert loaded.type == CategoryType.TOPIC
    assert loaded.parent_id is None
    assert loaded.sort_order == 0
    assert loaded.hsk_level is None


@pytest.mark.asyncio
async def test_category_save_hsk(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    category = make_category(
        name="HSK 4",
        type=CategoryType.HSK,
        hsk_level=4,
        sort_order=4,
    )

    await repo.save(category)
    await db_session.commit()

    loaded = await repo.get(category.id)
    assert loaded is not None
    assert loaded.type == CategoryType.HSK
    assert loaded.hsk_level == 4


@pytest.mark.asyncio
async def test_category_save_with_parent(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    parent = make_category(
        name="Topics",
        type=CategoryType.TOPIC,
        hsk_level=None,
    )
    child = make_category(
        name="Food",
        type=CategoryType.TOPIC,
        parent_id=parent.id,
        sort_order=1,
        hsk_level=None,
    )

    await repo.save_many([parent, child])
    await db_session.commit()

    loaded = await repo.get(child.id)
    assert loaded is not None
    assert loaded.parent_id == parent.id
    assert loaded.sort_order == 1
    assert loaded.type == CategoryType.TOPIC


@pytest.mark.asyncio
async def test_category_get_children_top_level(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    c1 = make_category(name="HSK 1", type=CategoryType.HSK, hsk_level=1, sort_order=1)
    c2 = make_category(name="HSK 2", type=CategoryType.HSK, hsk_level=2, sort_order=2)
    c3 = make_category(
        name="Child",
        type=CategoryType.TOPIC,
        parent_id=c1.id,
        hsk_level=None,
    )

    await repo.save_many([c1, c2, c3])
    await db_session.commit()

    top_level = await repo.get_children(None)
    assert len(top_level) == 2
    assert [c.name for c in top_level] == ["HSK 1", "HSK 2"]


@pytest.mark.asyncio
async def test_category_get_children_of_parent(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    parent = make_category(name="Food", type=CategoryType.TOPIC, hsk_level=None)
    child1 = make_category(
        name="Fruits",
        type=CategoryType.TOPIC,
        parent_id=parent.id,
        sort_order=1,
        hsk_level=None,
    )
    child2 = make_category(
        name="Vegetables",
        type=CategoryType.TOPIC,
        parent_id=parent.id,
        sort_order=2,
        hsk_level=None,
    )

    await repo.save_many([parent, child1, child2])
    await db_session.commit()

    children = await repo.get_children(parent.id)
    assert len(children) == 2
    assert [c.name for c in children] == ["Fruits", "Vegetables"]


@pytest.mark.asyncio
async def test_category_get_all(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    await repo.save_many(
        [
            make_category(
                name="A", type=CategoryType.TOPIC, sort_order=2, hsk_level=None
            ),
            make_category(
                name="B", type=CategoryType.TOPIC, sort_order=1, hsk_level=None
            ),
        ]
    )
    await db_session.commit()

    all_cats = await repo.get_all()
    assert len(all_cats) == 2
    assert [c.name for c in all_cats] == ["B", "A"]


@pytest.mark.asyncio
async def test_category_exists(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    category = make_category(type=CategoryType.TOPIC, hsk_level=None)
    await repo.save(category)
    await db_session.commit()

    assert await repo.exists(category.id) is True
    assert await repo.exists(CategoryId(str(uuid4()))) is False


# ------------------------------------------------------------------
# New methods introduced with the HSK model
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_hsk_categories(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    hsk1 = make_category(name="HSK 1", type=CategoryType.HSK, hsk_level=1, sort_order=1)
    hsk3 = make_category(name="HSK 3", type=CategoryType.HSK, hsk_level=3, sort_order=3)
    topic = make_category(name="Food", type=CategoryType.TOPIC, hsk_level=None)

    await repo.save_many([hsk3, topic, hsk1])  # deliberately out of order
    await db_session.commit()

    hsk_cats = await repo.get_hsk_categories()
    assert len(hsk_cats) == 2
    assert [c.hsk_level for c in hsk_cats] == [1, 3]
    assert all(c.type == CategoryType.HSK for c in hsk_cats)


@pytest.mark.asyncio
async def test_get_uncategorised(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    uncategorised = make_category(
        name="Uncategorised",
        type=CategoryType.SYSTEM,
        hsk_level=None,
        sort_order=999,
    )
    await repo.save(uncategorised)
    await db_session.commit()

    loaded = await repo.get_uncategorised()
    assert loaded.id == uncategorised.id
    assert loaded.type == CategoryType.SYSTEM
    assert loaded.name == "Uncategorised"


@pytest.mark.asyncio
async def test_get_uncategorised_raises_when_missing(db_session: AsyncSession):
    repo = CategoryRepository(db_session)
    with pytest.raises(RuntimeError, match="Uncategorised"):
        await repo.get_uncategorised()


@pytest.mark.asyncio
async def test_list_by_type(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    await repo.save_many(
        [
            make_category(name="HSK 1", type=CategoryType.HSK, hsk_level=1),
            make_category(name="Food", type=CategoryType.TOPIC, hsk_level=None),
            make_category(name="Travel", type=CategoryType.TOPIC, hsk_level=None),
            make_category(
                name="Uncategorised", type=CategoryType.SYSTEM, hsk_level=None
            ),
        ]
    )
    await db_session.commit()

    topics = await repo.list_by_type(CategoryType.TOPIC)
    assert len(topics) == 2
    assert {c.name for c in topics} == {"Food", "Travel"}

    hsk = await repo.list_by_type(CategoryType.HSK)
    assert len(hsk) == 1
    assert hsk[0].hsk_level == 1


@pytest.mark.asyncio
async def test_delete(db_session: AsyncSession, make_category: Callable[..., Category]):
    repo = CategoryRepository(db_session)
    category = make_category(type=CategoryType.TOPIC, hsk_level=None)
    await repo.save(category)
    await db_session.commit()

    assert await repo.exists(category.id) is True

    await repo.delete(category.id)
    await db_session.commit()

    assert await repo.exists(category.id) is False
    assert await repo.get(category.id) is None
