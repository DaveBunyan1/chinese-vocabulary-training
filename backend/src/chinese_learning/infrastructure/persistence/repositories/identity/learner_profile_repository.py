from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.learner import LearnerId, LearnerProfile
from chinese_learning.domain.identity.user import UserId
from chinese_learning.infrastructure.persistence.mappers.identity_mappers import (
    learner_profile_to_domain,
)
from chinese_learning.infrastructure.persistence.models import LearnerProfileModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class LearnerProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, learner_id: LearnerId) -> LearnerProfile | None:
        record_repo_metric("get", entity="learner_profile")
        stmt = select(LearnerProfileModel).where(
            LearnerProfileModel.id == str(learner_id.value)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return learner_profile_to_domain(model) if model else None

    async def get_by_user(self, user_id: UserId) -> list[LearnerProfile]:
        record_repo_metric("get_by_user", entity="learner_profile")
        stmt = (
            select(LearnerProfileModel)
            .where(LearnerProfileModel.user_id == str(user_id.value))
            .order_by(LearnerProfileModel.created_at)
        )
        result = await self.session.execute(stmt)
        return [learner_profile_to_domain(m) for m in result.scalars().all()]

    async def save(self, profile: LearnerProfile) -> None:
        record_repo_metric("save", entity="learner_profile")
        await self.save_many([profile])

    async def save_many(self, profiles: Sequence[LearnerProfile]) -> None:
        if not profiles:
            return

        record_repo_metric("save_many", entity="learner_profile")
        values = [
            {
                "id": str(p.id.value),
                "user_id": str(p.user_id.value),
                "language": p.language,
                "display_name": p.display_name,
                "created_at": p.created_at,
            }
            for p in profiles
        ]

        stmt = pg_insert(LearnerProfileModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "user_id": stmt.excluded.user_id,
                "language": stmt.excluded.language,
                "display_name": stmt.excluded.display_name,
                # created_at is intentionally not updated
            },
        )
        await self.session.execute(upsert_stmt)

        logger.info("learner_profile.saved_many", count=len(profiles))

    async def exists(self, learner_id: LearnerId) -> bool:
        record_repo_metric("exists", entity="learner_profile")
        stmt = select(func.count(1)).where(
            LearnerProfileModel.id == str(learner_id.value)
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
