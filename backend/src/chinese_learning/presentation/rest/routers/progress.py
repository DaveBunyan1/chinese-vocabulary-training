"""REST endpoint for basic progress statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.get_progress_stats import GetProgressStats
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.presentation.rest.schemas.progress import (
    CharacterProgressSchema,
    ProgressStatsResponse,
    StatusBreakdownSchema,
    VocabularyProgressSchema,
)

router = APIRouter(prefix="/progress", tags=["Progress"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    return DEFAULT_LEARNER_ID


@router.get(
    "",
    response_model=ProgressStatsResponse,
    summary="Basic progress stats derived from knowledge records",
)
async def get_progress(
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
) -> ProgressStatsResponse:
    use_case = GetProgressStats(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        character_knowledge_repo=CharacterKnowledgeRepository(session),
    )
    result = await use_case.execute(learner_id)

    v = result.vocabulary
    c = result.characters

    return ProgressStatsResponse(
        vocabulary=VocabularyProgressSchema(
            by_status=StatusBreakdownSchema(
                new=v.by_status.new,
                learning=v.by_status.learning,
                known=v.by_status.known,
                total=v.by_status.total,
            ),
            total_successful_recalls=v.total_successful_recalls,
            total_failed_recalls=v.total_failed_recalls,
            total_times_seen=v.total_times_seen,
            items_practised=v.items_practised,
        ),
        characters=CharacterProgressSchema(
            by_status=StatusBreakdownSchema(
                new=c.by_status.new,
                learning=c.by_status.learning,
                known=c.by_status.known,
                total=c.by_status.total,
            ),
            total_successful_recognitions=c.total_successful_recognitions,
            total_failed_recognitions=c.total_failed_recognitions,
            total_times_seen=c.total_times_seen,
            items_practised=c.items_practised,
        ),
    )
