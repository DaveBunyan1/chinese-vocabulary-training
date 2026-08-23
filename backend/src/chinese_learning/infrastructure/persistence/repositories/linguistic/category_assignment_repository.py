from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.mappers.linguistic_mappers import (
    category_assignment_to_domain,
)
from chinese_learning.infrastructure.persistence.models import CategoryAssignmentModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class CategoryAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, assignment: CategoryAssignment) -> None:
        record_repo_metric("save", entity="category_assignment")
        await self.save_many([assignment])

    async def save_many(self, assignments: Sequence[CategoryAssignment]) -> None:
        if not assignments:
            return

        record_repo_metric("save_many", entity="category_assignment")
        values = [
            {
                "category_id": str(a.category_id.value),
                "vocabulary_id": str(a.vocabulary_id.value),
            }
            for a in assignments
        ]

        stmt = pg_insert(CategoryAssignmentModel).values(values)
        # Pure link table – ignore duplicates
        upsert_stmt = stmt.on_conflict_do_nothing(
            index_elements=["category_id", "vocabulary_id"]
        )
        await self.session.execute(upsert_stmt)

        logger.info("category_assignment.saved_many", count=len(assignments))

    async def get_by_vocabulary(
        self, vocabulary_id: VocabularyId
    ) -> list[CategoryAssignment]:
        record_repo_metric("get_by_vocabulary", entity="category_assignment")
        stmt = select(CategoryAssignmentModel).where(
            CategoryAssignmentModel.vocabulary_id == vocabulary_id.value
        )
        result = await self.session.execute(stmt)
        return [category_assignment_to_domain(m) for m in result.scalars().all()]

    async def get_by_category(
        self, category_id: CategoryId
    ) -> list[CategoryAssignment]:
        record_repo_metric("get_by_category", entity="category_assignment")
        stmt = select(CategoryAssignmentModel).where(
            CategoryAssignmentModel.category_id == category_id.value
        )
        result = await self.session.execute(stmt)
        return [category_assignment_to_domain(m) for m in result.scalars().all()]

    async def delete(self, assignment: CategoryAssignment) -> None:
        record_repo_metric("delete", entity="category_assignment")
        stmt = delete(CategoryAssignmentModel).where(
            CategoryAssignmentModel.category_id == assignment.category_id.value,
            CategoryAssignmentModel.vocabulary_id == assignment.vocabulary_id.value,
        )
        await self.session.execute(stmt)

    async def exists(self, assignment: CategoryAssignment) -> bool:
        record_repo_metric("exists", entity="category_assignment")
        stmt = select(func.count()).where(
            CategoryAssignmentModel.category_id == assignment.category_id.value,
            CategoryAssignmentModel.vocabulary_id == assignment.vocabulary_id.value,
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
