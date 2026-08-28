"""Update a user-managed (custom/topic) category."""

from __future__ import annotations

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)

_EDITABLE = frozenset({CategoryType.CUSTOM, CategoryType.TOPIC})


class UpdateCategory:
    def __init__(self, category_repo: CategoryRepository) -> None:
        self._category_repo = category_repo

    async def execute(
        self,
        category_id: CategoryId,
        *,
        name: str | None = None,
        parent_id: CategoryId | None = None,
        clear_parent: bool = False,
        sort_order: int | None = None,
    ) -> Category:
        existing = await self._category_repo.get(category_id)
        if existing is None:
            raise LookupError(f"Category {category_id} not found")
        if existing.type not in _EDITABLE:
            raise ValueError(
                f"Cannot edit {existing.type.value} categories (only custom/topic)."
            )

        new_name = name.strip() if name is not None else existing.name
        if not new_name:
            raise ValueError("Category name cannot be empty")

        if clear_parent:
            new_parent: CategoryId | None = None
        elif parent_id is not None:
            if str(parent_id) == str(category_id):
                raise ValueError("Category cannot be its own parent")
            parent = await self._category_repo.get(parent_id)
            if parent is None:
                raise LookupError(f"Parent category {parent_id} not found")
            new_parent = parent_id
        else:
            new_parent = existing.parent_id

        new_sort = existing.sort_order if sort_order is None else sort_order
        if new_sort < 0:
            raise ValueError("sort_order cannot be negative")

        updated = Category(
            id=existing.id,
            name=new_name,
            type=existing.type,
            parent_id=new_parent,
            sort_order=new_sort,
            hsk_level=None,
        )
        await self._category_repo.save(updated)
        return updated
