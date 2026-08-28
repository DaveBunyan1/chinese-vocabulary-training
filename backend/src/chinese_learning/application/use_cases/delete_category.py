"""Delete a user-managed category and its vocabulary assignments."""

from __future__ import annotations

from chinese_learning.domain.category.category import CategoryId, CategoryType
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)

_DELETABLE = frozenset({CategoryType.CUSTOM, CategoryType.TOPIC})


class DeleteCategory:
    def __init__(
        self,
        category_repo: CategoryRepository,
        assignment_repo: CategoryAssignmentRepository,
    ) -> None:
        self._category_repo = category_repo
        self._assignment_repo = assignment_repo

    async def execute(self, category_id: CategoryId) -> None:
        existing = await self._category_repo.get(category_id)
        if existing is None:
            raise LookupError(f"Category {category_id} not found")
        if existing.type not in _DELETABLE:
            raise ValueError(
                f"Cannot delete {existing.type.value} categories (only custom/topic)."
            )

        # Block delete if children still point at this category
        children = await self._category_repo.get_children(category_id)
        if children:
            raise ValueError(
                "Category has subcategories; delete or reassign them first."
            )

        assignments = await self._assignment_repo.get_by_category(category_id)
        for assignment in assignments:
            await self._assignment_repo.delete(assignment)

        await self._category_repo.delete(category_id)
