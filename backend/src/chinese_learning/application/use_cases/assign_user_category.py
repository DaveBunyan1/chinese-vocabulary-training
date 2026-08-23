from chinese_learning.domain.category.category import CategoryId, CategoryType
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)


class AssignUserCategory:
    """
    Manually assigns or removes TOPIC / CUSTOM categories for a vocabulary item.
    Guards against attempting to manually reassign system/HSK categories here.
    """

    def __init__(
        self,
        category_repo: CategoryRepository,
        assignment_repo: CategoryAssignmentRepository,
    ) -> None:
        self._category_repo = category_repo
        self._assignment_repo = assignment_repo

    async def add_category(
        self, vocabulary_id: VocabularyId, category_id: CategoryId
    ) -> bool:
        """Assigns a topic or custom category to a vocabulary item."""
        category = await self._category_repo.get(category_id)
        if category is None:
            raise ValueError(f"Category {category_id} does not exist.")

        # Guard: Ensure this endpoint is not used to override HSK/SYSTEM logic
        if category.type in (CategoryType.HSK, CategoryType.SYSTEM):
            raise ValueError("Cannot manually assign HSK or SYSTEM categories.")

        # Check if already assigned
        existing = await self._assignment_repo.get_by_vocabulary(vocabulary_id)
        if any(a.category_id == category_id for a in existing):
            return False  # Already assigned

        assignment = CategoryAssignment(
            category_id=category_id,
            vocabulary_id=vocabulary_id,
        )
        await self._assignment_repo.save(assignment)
        return True

    async def remove_category(
        self, vocabulary_id: VocabularyId, category_id: CategoryId
    ) -> None:
        """Removes a topic or custom category assignment."""
        category = await self._category_repo.get(category_id)
        if category and category.type in (CategoryType.HSK, CategoryType.SYSTEM):
            raise ValueError("Cannot manually remove HSK or SYSTEM categories.")

        return await self._assignment_repo.delete(
            CategoryAssignment(category_id, vocabulary_id)
        )
