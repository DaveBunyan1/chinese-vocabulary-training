from chinese_learning.application.services.hsk_lookup_service import HSKLookupService
from chinese_learning.domain.category.category import Category, CategoryId, CategoryType
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyItem
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)


class AssignHSKCategory:
    """
    Ensures every VocabularyItem has exactly one HSK or Uncategorised category.
    Does NOT touch topic/custom categories.
    """

    def __init__(
        self,
        hsk_lookup: HSKLookupService,
        category_repo: CategoryRepository,
        assignment_repo: CategoryAssignmentRepository,
    ) -> None:
        self._lookup = hsk_lookup
        self._category_repo = category_repo
        self._assignment_repo = assignment_repo

        # Cached after first call
        self._hsk_by_level: dict[int, Category] | None = None
        self._uncategorised: Category | None = None

    async def execute(self, items: list[VocabularyItem]) -> int:
        """
        Assign HSK / Uncategorised categories to the given items.
        Returns the number of new assignments created.
        """
        if not items:
            return 0

        hsk_by_level, uncategorised = await self._ensure_category_cache()

        to_create: list[CategoryAssignment] = []

        for item in items:
            existing = await self._assignment_repo.get_by_vocabulary(item.id)

            has_hsk_or_system = False
            for assignment in existing:
                # Skip if the item already has an HSK or SYSTEM category
                if await self._is_hsk_or_system(assignment.category_id):
                    has_hsk_or_system = True
                    break

            if has_hsk_or_system:
                continue

            level = self._lookup.get_level(item.text)

            if level is not None and level in hsk_by_level:
                category = hsk_by_level[level]
            else:
                category = uncategorised

            to_create.append(
                CategoryAssignment(
                    category_id=category.id,
                    vocabulary_id=item.id,
                )
            )

        if to_create:
            await self._assignment_repo.save_many(to_create)

        return len(to_create)

    async def _ensure_category_cache(self) -> tuple[dict[int, Category], Category]:
        """Loads categories into memory and returns non-None guarantees."""
        if self._hsk_by_level is None or self._uncategorised is None:
            hsk_cats = await self._category_repo.get_hsk_categories()
            self._hsk_by_level = {
                c.hsk_level: c for c in hsk_cats if c.hsk_level is not None
            }

            uncat = await self._category_repo.get_uncategorised()

            self._uncategorised = uncat

        return self._hsk_by_level, self._uncategorised

    async def _is_hsk_or_system(self, category_id: CategoryId) -> bool:
        cat = await self._category_repo.get(category_id)
        return cat is not None and cat.type in (CategoryType.HSK, CategoryType.SYSTEM)
