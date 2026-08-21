from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.infrastructure.persistence.mappers.text_analysis_mappers import (
    character_to_domain,
)
from chinese_learning.infrastructure.persistence.models import CharacterModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class CharacterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, symbol: str) -> Character | None:
        record_repo_metric("get", entity="character")
        stmt = select(CharacterModel).where(CharacterModel.symbol == symbol)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return character_to_domain(model) if model else None

    async def exists(self, symbol: str) -> bool:
        record_repo_metric("exists", entity="character")
        stmt = select(func.count(1)).where(CharacterModel.symbol == symbol)
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def save(self, character: Character) -> None:
        record_repo_metric("save", entity="character")
        await self.save_many([character])

    async def save_many(self, characters: Sequence[Character]) -> None:
        if not characters:
            return

        record_repo_metric("save_many", entity="character")
        values = [{"symbol": c.symbol} for c in characters]

        stmt = pg_insert(CharacterModel).values(values)
        # Characters are pure reference data – do nothing on conflict
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["symbol"])
        await self.session.execute(upsert_stmt)

        logger.info("character.saved_many", count=len(characters))

    async def get_many(self, symbols: Sequence[str]) -> list[Character]:
        if not symbols:
            return []
        record_repo_metric("get_many", entity="character")
        stmt = select(CharacterModel).where(CharacterModel.symbol.in_(symbols))
        result = await self.session.execute(stmt)
        return [character_to_domain(m) for m in result.scalars().all()]
