from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from chinese_learning.application.use_cases.delete_category import DeleteCategory
from chinese_learning.application.use_cases.update_category import UpdateCategory
from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


def _custom(name: str = "Food") -> Category:
    return Category(
        id=CategoryId(str(uuid4())),
        name=name,
        type=CategoryType.CUSTOM,
    )


@pytest.mark.asyncio
async def test_update_renames_custom_category() -> None:
    cat = _custom("Old")
    repo = AsyncMock()
    repo.get.return_value = cat
    result = await UpdateCategory(repo).execute(cat.id, name="New")
    assert result.name == "New"
    repo.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_rejects_hsk() -> None:
    cat = Category(
        id=CategoryId(str(uuid4())),
        name="HSK 1",
        type=CategoryType.HSK,
        hsk_level=1,
    )
    repo = AsyncMock()
    repo.get.return_value = cat
    with pytest.raises(ValueError, match="custom/topic"):
        await UpdateCategory(repo).execute(cat.id, name="Nope")


@pytest.mark.asyncio
async def test_delete_removes_assignments_then_category() -> None:
    cat = _custom()
    cat_repo = AsyncMock()
    assign_repo = AsyncMock()
    cat_repo.get.return_value = cat
    cat_repo.get_children.return_value = []
    assign_repo.get_by_category.return_value = [
        CategoryAssignment(category_id=cat.id, vocabulary_id=VocabularyId("v1"))
    ]
    await DeleteCategory(cat_repo, assign_repo).execute(cat.id)
    assign_repo.delete.assert_awaited()
    cat_repo.delete.assert_awaited_once_with(cat.id)


@pytest.mark.asyncio
async def test_delete_rejects_system() -> None:
    cat = Category(
        id=CategoryId(str(uuid4())),
        name="Uncategorised",
        type=CategoryType.SYSTEM,
    )
    cat_repo = AsyncMock()
    assign_repo = AsyncMock()
    cat_repo.get.return_value = cat
    with pytest.raises(ValueError, match="custom/topic"):
        await DeleteCategory(cat_repo, assign_repo).execute(cat.id)
