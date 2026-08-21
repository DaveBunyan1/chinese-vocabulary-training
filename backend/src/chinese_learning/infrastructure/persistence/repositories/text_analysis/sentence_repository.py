from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.infrastructure.persistence.mappers.text_analysis_mappers import (
    sentence_to_domain,
    sentence_to_model,
)
from chinese_learning.infrastructure.persistence.models import SentenceModel
from chinese_learning.infrastructure.persistence.repositories.repo_utils import (
    logger,
    record_repo_metric,
)


class SentenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, sentence_id: str) -> Sentence | None:
        record_repo_metric("get", entity="sentence")
        stmt = select(SentenceModel).where(SentenceModel.id == sentence_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return sentence_to_domain(model) if model else None

    async def save(self, sentence: Sentence, *, sentence_id: str | None = None) -> str:
        record_repo_metric("save", entity="sentence")
        sid = sentence_id or str(uuid4())
        model = sentence_to_model(sentence, sentence_id=sid)
        self.session.add(model)
        logger.info(
            "sentence.saved",
            sentence_id=sid,
            token_count=len(sentence.tokens),
        )
        return sid

    async def save_many(self, sentences: Sequence[Sentence]) -> list[str]:
        if not sentences:
            return []

        record_repo_metric("save_many", entity="sentence")
        ids: list[str] = []
        for sentence in sentences:
            sid = str(uuid4())
            model = sentence_to_model(sentence, sentence_id=sid)
            self.session.add(model)
            ids.append(sid)

        logger.info("sentence.saved_many", count=len(sentences))
        return ids

    async def get_by_raw_text(self, raw_text: str) -> list[Sentence]:
        """Useful when the same sentence text appears multiple times."""
        record_repo_metric("get_by_raw_text", entity="sentence")
        stmt = select(SentenceModel).where(SentenceModel.raw_text == raw_text)
        result = await self.session.execute(stmt)
        return [sentence_to_domain(m) for m in result.scalars().all()]

    async def exists(self, sentence_id: str) -> bool:
        record_repo_metric("exists", entity="sentence")
        stmt = select(func.count(1)).where(SentenceModel.id == sentence_id)
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
