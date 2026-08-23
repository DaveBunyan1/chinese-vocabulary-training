from uuid import uuid4

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)


class CreateCustomCategory:
    """Creates a new CUSTOM category owned by a specific learner or context."""

    def __init__(self, category_repo: CategoryRepository) -> None:
        self._category_repo = category_repo

    async def execute(self, name: str, parent_id: CategoryId | None = None) -> Category:
        new_category = Category(
            id=CategoryId(str(uuid4())),
            name=name,
            type=CategoryType.CUSTOM,
            parent_id=parent_id,
            hsk_level=None,
        )
        await self._category_repo.save(new_category)
        return new_category
