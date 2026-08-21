from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.token import Token
from chinese_learning.infrastructure.persistence.mappers.text_analysis_mappers import (
    token_to_domain,
)
from chinese_learning.infrastructure.persistence.models import TokenModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, text: str) -> Token | None:
        record_repo_metric("get", entity="token")
        stmt = select(TokenModel).where(TokenModel.text == text)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return token_to_domain(model) if model else None

    async def exists(self, text: str) -> bool:
        record_repo_metric("exists", entity="token")
        stmt = select(func.count(1)).where(TokenModel.text == text)
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def save(self, token: Token) -> None:
        record_repo_metric("save", entity="token")
        await self.save_many([token])

    async def save_many(self, tokens: Sequence[Token]) -> None:
        if not tokens:
            return

        record_repo_metric("save_many", entity="token")
        values = [{"text": t.text} for t in tokens]

        stmt = pg_insert(TokenModel).values(values)
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["text"])
        await self.session.execute(upsert_stmt)

        logger.info("token.saved_many", count=len(tokens))

    async def get_many(self, texts: Sequence[str]) -> list[Token]:
        if not texts:
            return []
        record_repo_metric("get_many", entity="token")
        stmt = select(TokenModel).where(TokenModel.text.in_(texts))
        result = await self.session.execute(stmt)
        return [token_to_domain(m) for m in result.scalars().all()]
