from collections.abc import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.category.category import Category
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)


@pytest.mark.asyncio
async def test_category_assignment_save_and_get_by_vocabulary(
    db_session: AsyncSession,
    make_vocabulary_item: Callable[..., VocabularyItem],
    make_category: Callable[..., Category],
):
    # First create the referenced entities
    vocab_repo = VocabularyItemRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    item = make_vocabulary_item()
    cat1 = make_category(name="HSK 3")
    cat2 = make_category(name="Education")

    await vocab_repo.save(item)
    await cat_repo.save_many([cat1, cat2])
    await db_session.commit()

    a1 = CategoryAssignment(category_id=cat1.id, vocabulary_id=item.id)
    a2 = CategoryAssignment(category_id=cat2.id, vocabulary_id=item.id)

    await assign_repo.save_many([a1, a2])
    await db_session.commit()

    results = await assign_repo.get_by_vocabulary(item.id)
    assert len(results) == 2
    cat_ids = {str(a.category_id.value) for a in results}
    assert cat_ids == {str(cat1.id.value), str(cat2.id.value)}


@pytest.mark.asyncio
async def test_category_assignment_get_by_category(
    db_session: AsyncSession,
    make_vocabulary_item: Callable[..., VocabularyItem],
    make_category: Callable[..., Category],
):
    vocab_repo = VocabularyItemRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    item1 = make_vocabulary_item(text="苹果")
    item2 = make_vocabulary_item(text="香蕉")
    category = make_category(name="Fruits")

    await vocab_repo.save_many([item1, item2])
    await cat_repo.save(category)
    await db_session.commit()

    await assign_repo.save_many(
        [
            CategoryAssignment(category_id=category.id, vocabulary_id=item1.id),
            CategoryAssignment(category_id=category.id, vocabulary_id=item2.id),
        ]
    )
    await db_session.commit()

    results = await assign_repo.get_by_category(category.id)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_category_assignment_is_idempotent(
    db_session: AsyncSession,
    make_vocabulary_item: Callable[..., VocabularyItem],
    make_category: Callable[..., Category],
):
    vocab_repo = VocabularyItemRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    item = make_vocabulary_item()
    category = make_category()
    await vocab_repo.save(item)
    await cat_repo.save(category)
    await db_session.commit()

    assignment = CategoryAssignment(category_id=category.id, vocabulary_id=item.id)

    await assign_repo.save(assignment)
    await assign_repo.save(assignment)  # second time should not raise
    await db_session.commit()

    results = await assign_repo.get_by_vocabulary(item.id)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_category_assignment_delete(
    db_session: AsyncSession,
    make_vocabulary_item: Callable[..., VocabularyItem],
    make_category: Callable[..., Category],
):
    vocab_repo = VocabularyItemRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    item = make_vocabulary_item()
    category = make_category()
    await vocab_repo.save(item)
    await cat_repo.save(category)
    await db_session.commit()

    assignment = CategoryAssignment(category_id=category.id, vocabulary_id=item.id)
    await assign_repo.save(assignment)
    await db_session.commit()

    assert await assign_repo.exists(assignment) is True

    await assign_repo.delete(assignment)
    await db_session.commit()

    assert await assign_repo.exists(assignment) is False


@pytest.mark.asyncio
async def test_category_assignment_exists(
    db_session: AsyncSession,
    make_category: Callable[..., Category],
    make_vocabulary_item: Callable[..., VocabularyItem],
):
    vocab_repo = VocabularyItemRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    assign_repo = CategoryAssignmentRepository(db_session)

    item = make_vocabulary_item()
    category = make_category()
    await vocab_repo.save(item)
    await cat_repo.save(category)
    await db_session.commit()

    assignment = CategoryAssignment(category_id=category.id, vocabulary_id=item.id)
    assert await assign_repo.exists(assignment) is False

    await assign_repo.save(assignment)
    await db_session.commit()

    assert await assign_repo.exists(assignment) is True
