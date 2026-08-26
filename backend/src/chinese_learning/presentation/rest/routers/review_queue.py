"""REST endpoint for the learner review queue."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.get_review_queue import GetReviewQueue
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.schemas.review_queue import (
    ReviewQueueItemSchema,
    ReviewQueueResponse,
)

router = APIRouter(prefix="/review-queue", tags=["Review"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    return DEFAULT_LEARNER_ID


@router.get(
    "",
    response_model=ReviewQueueResponse,
    summary="Get items due for review (plus unscheduled NEW/LEARNING)",
)
async def get_review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    include_vocabulary: bool = Query(default=True),
    include_characters: bool = Query(default=True),
    include_unscheduled: bool = Query(
        default=True,
        description="Include NEW/LEARNING items with no next_review_at",
    ),
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewQueueResponse:
    use_case = GetReviewQueue(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        character_knowledge_repo=CharacterKnowledgeRepository(session),
        vocabulary_item_repo=VocabularyItemRepository(session),
    )

    try:
        result = await use_case.execute(
            learner_id,
            limit=limit,
            include_vocabulary=include_vocabulary,
            include_characters=include_characters,
            include_unscheduled=include_unscheduled,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ReviewQueueResponse(
        items=[
            ReviewQueueItemSchema(
                kind=i.kind.value,
                reason=i.reason.value,
                vocabulary_id=i.vocabulary_id,
                text=i.text,
                pinyin=i.pinyin,
                meaning=i.meaning,
                character=i.character,
                status=i.status,
                next_review_at=i.next_review_at,
                successful_attempts=i.successful_attempts,
                failed_attempts=i.failed_attempts,
            )
            for i in result.items
        ],
        due_vocabulary_count=result.due_vocabulary_count,
        due_character_count=result.due_character_count,
        unscheduled_vocabulary_count=result.unscheduled_vocabulary_count,
        unscheduled_character_count=result.unscheduled_character_count,
        total=result.total,
        as_of=result.as_of,
    )
