from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.mappers.linguistic_mappers import (
    vocabulary_item_to_domain,
)
from chinese_learning.infrastructure.persistence.models import VocabularyItemModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class VocabularyItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, vocabulary_id: VocabularyId) -> VocabularyItem | None:
        record_repo_metric("get", entity="vocabulary_item")
        stmt = select(VocabularyItemModel).where(
            VocabularyItemModel.id == str(vocabulary_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return vocabulary_item_to_domain(model) if model else None

    async def get_by_text(self, text: str) -> VocabularyItem | None:
        record_repo_metric("get_by_text", entity="vocabulary_item")
        stmt = select(VocabularyItemModel).where(VocabularyItemModel.text == text)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return vocabulary_item_to_domain(model) if model else None

    async def save(self, item: VocabularyItem) -> None:
        record_repo_metric("save", entity="vocabulary_item")
        await self.save_many([item])

    async def save_many(self, items: Sequence[VocabularyItem]) -> None:
        if not items:
            return

        record_repo_metric("save_many", entity="vocabulary_item")
        values = [
            {
                "id": str(i.id),
                "text": i.text,
                "pinyin": i.pinyin,
                "meaning": i.meaning,
            }
            for i in items
        ]

        stmt = pg_insert(VocabularyItemModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "text": stmt.excluded.text,
                "pinyin": stmt.excluded.pinyin,
                "meaning": stmt.excluded.meaning,
            },
        )
        await self.session.execute(upsert_stmt)

        logger.info("vocabulary_item.saved_many", count=len(items))

    async def get_many(
        self, vocabulary_ids: Sequence[VocabularyId]
    ) -> list[VocabularyItem]:
        if not vocabulary_ids:
            return []
        record_repo_metric("get_many", entity="vocabulary_item")
        ids = [str(v) for v in vocabulary_ids]
        stmt = select(VocabularyItemModel).where(VocabularyItemModel.id.in_(ids))
        result = await self.session.execute(stmt)
        return [vocabulary_item_to_domain(m) for m in result.scalars().all()]

    async def exists(self, vocabulary_id: VocabularyId) -> bool:
        record_repo_metric("exists", entity="vocabulary_item")
        stmt = select(func.count(1)).where(VocabularyItemModel.id == str(vocabulary_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
