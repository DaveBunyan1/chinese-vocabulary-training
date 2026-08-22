from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.identity.user import User, UserId
from chinese_learning.infrastructure.persistence.mappers.identity_mappers import (
    user_to_domain,
)
from chinese_learning.infrastructure.persistence.models import UserModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UserId) -> User | None:
        record_repo_metric("get", entity="user")
        stmt = select(UserModel).where(UserModel.id == str(user_id.value))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        record_repo_metric("get_by_email", entity="user")
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_domain(model) if model else None

    async def save(self, user: User) -> None:
        record_repo_metric("save", entity="user")
        await self.save_many([user])

    async def save_many(self, users: Sequence[User]) -> None:
        if not users:
            return

        record_repo_metric("save_many", entity="user")
        values = [
            {
                "id": str(u.id.value),
                "email": u.email,
                "display_name": u.display_name,
                "created_at": u.created_at,
            }
            for u in users
        ]

        stmt = pg_insert(UserModel).values(values)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "email": stmt.excluded.email,
                "display_name": stmt.excluded.display_name,
                # created_at is intentionally not updated
            },
        )
        await self.session.execute(upsert_stmt)

        logger.info("user.saved_many", count=len(users))

    async def exists(self, user_id: UserId) -> bool:
        record_repo_metric("exists", entity="user")
        stmt = select(func.count(1)).where(UserModel.id == str(user_id.value))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def exists_by_email(self, email: str) -> bool:
        record_repo_metric("exists_by_email", entity="user")
        stmt = select(func.count(1)).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
