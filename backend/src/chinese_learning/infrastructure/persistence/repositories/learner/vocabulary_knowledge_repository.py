from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.learner.vocabulary_knowledge import VocabularyKnowledge
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.mappers.learner_mappers import (
    vocabulary_knowledge_to_domain,
    vocabulary_knowledge_to_model,
)
from chinese_learning.infrastructure.persistence.models import VocabularyKnowledgeModel

from ..repo_utils import logger, record_repo_metric


class VocabularyKnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self, learner_id: LearnerId, vocabulary_id: VocabularyId
    ) -> VocabularyKnowledge | None:
        record_repo_metric("get", entity="vocabulary_knowledge")
        stmt = select(VocabularyKnowledgeModel).where(
            VocabularyKnowledgeModel.learner_id == str(learner_id),
            VocabularyKnowledgeModel.vocabulary_id == str(vocabulary_id),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return vocabulary_knowledge_to_domain(model) if model else None

    async def save(self, knowledge: VocabularyKnowledge) -> None:
        record_repo_metric("save", entity="vocabulary_knowledge")
        await self.save_many([knowledge])

    async def save_many(self, knowledges: Sequence[VocabularyKnowledge]) -> None:
        if not knowledges:
            return

        record_repo_metric("save_many", entity="vocabulary_knowledge")
        models = [vocabulary_knowledge_to_model(k) for k in knowledges]

        values = [
            {
                "learner_id": m.learner_id,
                "vocabulary_id": m.vocabulary_id,
                "status": m.status,
                "successful_recalls": m.successful_recalls,
                "failed_recalls": m.failed_recalls,
                "times_seen": m.times_seen,
                "times_produced": m.times_produced,
                "first_seen_at": m.first_seen_at,
                "last_practised_at": m.last_practised_at,
                "last_seen_at": m.last_seen_at,
                "next_review_at": m.next_review_at,
                "ease_factor": m.ease_factor,
                "interval_days": m.interval_days,
            }
            for m in models
        ]

        stmt = pg_insert(VocabularyKnowledgeModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["learner_id", "vocabulary_id"],  # Composite primary key
            set_={
                "status": stmt.excluded.status,
                "successful_recalls": stmt.excluded.successful_recalls,
                "failed_recalls": stmt.excluded.failed_recalls,
                "times_seen": stmt.excluded.times_seen,
                "times_produced": stmt.excluded.times_produced,
                "first_seen_at": stmt.excluded.first_seen_at,
                "last_practised_at": stmt.excluded.last_practised_at,
                "last_seen_at": stmt.excluded.last_seen_at,
                "next_review_at": stmt.excluded.next_review_at,
                "ease_factor": stmt.excluded.ease_factor,
                "interval_days": stmt.excluded.interval_days,
            },
        )

        await self.session.execute(upsert_stmt)

        logger.info(
            "vocabulary_knowledge.saved_many",
            count=len(knowledges),
            learner_id=str(knowledges[0].learner_id),
        )

    async def get_many(
        self, learner_id: LearnerId, vocabulary_ids: Sequence[VocabularyId]
    ) -> list[VocabularyKnowledge]:
        if not vocabulary_ids:
            return []

        record_repo_metric("get_many", entity="vocabulary_knowledge")
        ids = [str(v) for v in vocabulary_ids]
        stmt = select(VocabularyKnowledgeModel).where(
            VocabularyKnowledgeModel.learner_id == str(learner_id),
            VocabularyKnowledgeModel.vocabulary_id.in_(ids),
        )
        result = await self.session.execute(stmt)
        return [vocabulary_knowledge_to_domain(m) for m in result.scalars().all()]

    async def get_all_for_learner(
        self, learner_id: LearnerId
    ) -> list[VocabularyKnowledge]:
        record_repo_metric("get_all", entity="vocabulary_knowledge")
        stmt = select(VocabularyKnowledgeModel).where(
            VocabularyKnowledgeModel.learner_id == str(learner_id)
        )
        result = await self.session.execute(stmt)
        return [vocabulary_knowledge_to_domain(m) for m in result.scalars().all()]

    async def get_by_status(
        self, learner_id: LearnerId, status: KnowledgeStatus
    ) -> list[VocabularyKnowledge]:
        record_repo_metric("get_by_status", entity="vocabulary_knowledge")
        stmt = select(VocabularyKnowledgeModel).where(
            VocabularyKnowledgeModel.learner_id == str(learner_id),
            VocabularyKnowledgeModel.status == status,
        )
        result = await self.session.execute(stmt)
        return [vocabulary_knowledge_to_domain(m) for m in result.scalars().all()]

    async def get_due_for_review(
        self, learner_id: LearnerId, as_of: datetime
    ) -> list[VocabularyKnowledge]:
        record_repo_metric("get_due", entity="vocabulary_knowledge")
        stmt = (
            select(VocabularyKnowledgeModel)
            .where(
                VocabularyKnowledgeModel.learner_id == str(learner_id),
                VocabularyKnowledgeModel.next_review_at <= as_of,
            )
            .order_by(VocabularyKnowledgeModel.next_review_at)
        )
        result = await self.session.execute(stmt)
        items = [vocabulary_knowledge_to_domain(m) for m in result.scalars().all()]

        logger.debug(
            "vocabulary_knowledge.due_for_review",
            learner_id=str(learner_id),
            count=len(items),
        )
        return items

    async def count_by_status(
        self, learner_id: LearnerId
    ) -> dict[KnowledgeStatus, int]:
        record_repo_metric("count_by_status", entity="vocabulary_knowledge")
        stmt = (
            select(
                VocabularyKnowledgeModel.status,
                func.count().label("cnt"),
            )
            .where(VocabularyKnowledgeModel.learner_id == str(learner_id))
            .group_by(VocabularyKnowledgeModel.status)
        )
        result = await self.session.execute(stmt)
        return {row.status: row.cnt for row in result.all()}

    async def exists(self, learner_id: LearnerId, vocabulary_id: VocabularyId) -> bool:
        record_repo_metric("exists", entity="vocabulary_knowledge")
        stmt = select(func.count(1)).where(
            VocabularyKnowledgeModel.learner_id == str(learner_id),
            VocabularyKnowledgeModel.vocabulary_id == str(vocabulary_id),
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
