from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.character_knowledge import CharacterKnowledge
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.persistence.mappers.learner_mappers import (
    character_knowledge_to_domain,
    character_knowledge_to_model,
)
from chinese_learning.infrastructure.persistence.models import CharacterKnowledgeModel

from .repo_utils import logger, record_repo_metric


class CharacterKnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Single-item
    # ------------------------------------------------------------------
    async def get(
        self, learner_id: LearnerId, character: Character
    ) -> CharacterKnowledge | None:
        record_repo_metric("get", entity="character_knowledge")
        stmt = select(CharacterKnowledgeModel).where(
            CharacterKnowledgeModel.learner_id == str(learner_id),
            CharacterKnowledgeModel.character_literal == str(character),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return character_knowledge_to_domain(model) if model else None

    async def save(self, knowledge: CharacterKnowledge) -> None:
        record_repo_metric("save", entity="character_knowledge")
        await self.save_many([knowledge])

    # ------------------------------------------------------------------
    # Bulk
    # ------------------------------------------------------------------
    async def save_many(self, knowledges: Sequence[CharacterKnowledge]) -> None:
        if not knowledges:
            return

        record_repo_metric("save_many", entity="character_knowledge")
        models = [character_knowledge_to_model(k) for k in knowledges]

        values = [
            {
                "learner_id": m.learner_id,
                "character_literal": m.character_literal,
                "status": m.status,
                "successful_recognitions": m.successful_recognitions,
                "failed_recognitions": m.failed_recognitions,
                "correct_pinyin_count": m.correct_pinyin_count,
                "times_seen": m.times_seen,
                "first_seen_at": m.first_seen_at,
                "last_practised_at": m.last_practised_at,
                "last_seen_at": m.last_seen_at,
                "next_review_at": m.next_review_at,
            }
            for m in models
        ]

        stmt = pg_insert(CharacterKnowledgeModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["learner_id", "character_literal"],
            set_={
                "status": stmt.excluded.status,
                "successful_recognitions": stmt.excluded.successful_recognitions,
                "failed_recognitions": stmt.excluded.failed_recognitions,
                "correct_pinyin_count": stmt.excluded.correct_pinyin_count,
                "times_seen": stmt.excluded.times_seen,
                "first_seen_at": stmt.excluded.first_seen_at,
                "last_practised_at": stmt.excluded.last_practised_at,
                "last_seen_at": stmt.excluded.last_seen_at,
                "next_review_at": stmt.excluded.next_review_at,
            },
        )

        await self.session.execute(upsert_stmt)

        logger.info(
            "character_knowledge.saved_many",
            count=len(knowledges),
            learner_id=str(knowledges[0].learner_id),
        )

    async def get_many(
        self, learner_id: LearnerId, characters: Sequence[Character]
    ) -> list[CharacterKnowledge]:
        if not characters:
            return []
        literals = [str(c) for c in characters]
        stmt = select(CharacterKnowledgeModel).where(
            CharacterKnowledgeModel.learner_id == str(learner_id),
            CharacterKnowledgeModel.character_literal.in_(literals),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [character_knowledge_to_domain(m) for m in models]

    # ------------------------------------------------------------------
    # Queries needed by later phases
    # ------------------------------------------------------------------
    async def get_all_for_learner(
        self, learner_id: LearnerId
    ) -> list[CharacterKnowledge]:
        stmt = select(CharacterKnowledgeModel).where(
            CharacterKnowledgeModel.learner_id == str(learner_id)
        )
        result = await self.session.execute(stmt)
        return [character_knowledge_to_domain(m) for m in result.scalars().all()]

    async def get_by_status(
        self,
        learner_id: LearnerId,
        status: KnowledgeStatus,
    ) -> list[CharacterKnowledge]:
        stmt = select(CharacterKnowledgeModel).where(
            CharacterKnowledgeModel.learner_id == str(learner_id),
            CharacterKnowledgeModel.status == status,
        )
        result = await self.session.execute(stmt)
        return [character_knowledge_to_domain(m) for m in result.scalars().all()]

    async def get_due_for_review(
        self, learner_id: LearnerId, as_of: datetime
    ) -> list[CharacterKnowledge]:
        record_repo_metric("get_due", entity="character_knowledge")
        stmt = (
            select(CharacterKnowledgeModel)
            .where(
                CharacterKnowledgeModel.learner_id == str(learner_id),
                CharacterKnowledgeModel.next_review_at <= as_of,
            )
            .order_by(CharacterKnowledgeModel.next_review_at)
        )
        result = await self.session.execute(stmt)
        items = [character_knowledge_to_domain(m) for m in result.scalars().all()]
        logger.debug(
            "character_knowledge.due_for_review",
            extra={"learner_id": str(learner_id), "count": len(items)},
        )
        return items

    async def count_by_status(
        self, learner_id: LearnerId
    ) -> dict[KnowledgeStatus, int]:
        """Useful for dashboards and progress stats."""
        stmt = (
            select(
                CharacterKnowledgeModel.status,
                func.count().label("cnt"),
            )
            .where(CharacterKnowledgeModel.learner_id == str(learner_id))
            .group_by(CharacterKnowledgeModel.status)
        )
        result = await self.session.execute(stmt)
        return {row.status: row.cnt for row in result.all()}

    async def exists(self, learner_id: LearnerId, character: Character) -> bool:
        stmt = select(func.count(1)).where(
            CharacterKnowledgeModel.learner_id == str(learner_id),
            CharacterKnowledgeModel.character_literal == str(character.symbol),
        )
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0
