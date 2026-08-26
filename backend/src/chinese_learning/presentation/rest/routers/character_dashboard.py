"""REST endpoints for the learner character dashboard."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.list_character_dashboard import (
    ListCharacterDashboard,
)
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.character_knowledge_repository import (
    CharacterKnowledgeRepository,
)
from chinese_learning.presentation.rest.schemas.character_dashboard import (
    CharacterDashboardItemSchema,
    CharacterDashboardResponse,
)

router = APIRouter(prefix="/characters", tags=["Characters"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    return DEFAULT_LEARNER_ID


def get_cedict_dictionary() -> CedictDictionary:
    dict_path = (
        Path(__file__).resolve().parents[3]
        / "infrastructure"
        / "nlp"
        / "data"
        / "cedict.txt"
    )
    return CedictDictionary(dict_path)


def _parse_status(value: str | None) -> KnowledgeStatus | None:
    if value is None:
        return None
    try:
        return KnowledgeStatus(value.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {value}. Use new|learning|known.",
        ) from exc


@router.get(
    "",
    response_model=CharacterDashboardResponse,
    summary="List learner characters with optional filters",
)
async def list_characters(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by knowledge status: new | learning | known",
    ),
    search: str | None = Query(
        default=None,
        max_length=100,
        description="Search character / pinyin / meaning",
    ),
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
    dictionary: CedictDictionary = Depends(get_cedict_dictionary),
) -> CharacterDashboardResponse:
    knowledge_status = _parse_status(status_filter)

    use_case = ListCharacterDashboard(
        character_knowledge_repo=CharacterKnowledgeRepository(session),
        dictionary=dictionary,
    )

    result = await use_case.execute(
        learner_id,
        knowledge_status=knowledge_status,
        search=search,
    )

    return CharacterDashboardResponse(
        items=[
            CharacterDashboardItemSchema(
                character=row.character,
                pinyin=row.pinyin,
                meaning=row.meaning,
                status=row.status,
                successful_recognitions=row.successful_recognitions,
                failed_recognitions=row.failed_recognitions,
                correct_pinyin_count=row.correct_pinyin_count,
                times_seen=row.times_seen,
                last_practised_at=row.last_practised_at,
                last_seen_at=row.last_seen_at,
            )
            for row in result.items
        ],
        total=result.total,
        status_counts=result.status_counts,
    )
