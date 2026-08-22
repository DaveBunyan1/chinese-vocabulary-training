from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.category.category import Category, CategoryId
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
    category = make_category(name="Food")

    await repo.save(category)
    await db_session.commit()

    loaded = await repo.get(category.id)
    assert loaded is not None
    assert loaded.name == "Food"
    assert loaded.parent_id is None
    assert loaded.sort_order == 0


@pytest.mark.asyncio
async def test_category_save_with_parent(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    parent = make_category(name="Topics")
    child = make_category(name="Food", parent_id=parent.id, sort_order=1)

    await repo.save_many([parent, child])
    await db_session.commit()

    loaded = await repo.get(child.id)
    assert loaded is not None
    assert loaded.parent_id == parent.id
    assert loaded.sort_order == 1


@pytest.mark.asyncio
async def test_category_get_children_top_level(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    c1 = make_category(name="HSK 1", sort_order=1)
    c2 = make_category(name="HSK 2", sort_order=2)
    c3 = make_category(name="Child", parent_id=c1.id)

    await repo.save_many([c1, c2, c3])
    await db_session.commit()

    top_level = await repo.get_children(None)
    assert len(top_level) == 2
    names = [c.name for c in top_level]
    assert names == ["HSK 1", "HSK 2"]  # ordered by sort_order


@pytest.mark.asyncio
async def test_category_get_children_of_parent(
    db_session: AsyncSession, make_category: Callable[..., Category]
):
    repo = CategoryRepository(db_session)
    parent = make_category(name="Food")
    child1 = make_category(name="Fruits", parent_id=parent.id, sort_order=1)
    child2 = make_category(name="Vegetables", parent_id=parent.id, sort_order=2)

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
            make_category(name="A", sort_order=2),
            make_category(name="B", sort_order=1),
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
    category = make_category()
    await repo.save(category)
    await db_session.commit()

    assert await repo.exists(category.id) is True
    assert await repo.exists(CategoryId(str(uuid4()))) is False
