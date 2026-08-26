"""REST endpoints for the learner vocabulary dashboard."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.list_vocabulary_dashboard import (
    ListVocabularyDashboard,
)
from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.identity.learner import LearnerId
from chinese_learning.domain.learner.knowledge_status import KnowledgeStatus
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.learner.vocabulary_knowledge_repository import (
    VocabularyKnowledgeRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.schemas.vocabulary_dashboard import (
    CategoryListItemSchema,
    CategoryListResponse,
    CategorySummarySchema,
    VocabularyDashboardItemSchema,
    VocabularyDashboardResponse,
)

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])

DEFAULT_LEARNER_ID = LearnerId(value="00000000-0000-0000-0000-000000000001")


def get_current_learner_id() -> LearnerId:
    return DEFAULT_LEARNER_ID


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
    response_model=VocabularyDashboardResponse,
    summary="List learner vocabulary with optional filters",
)
async def list_vocabulary(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by knowledge status: new | learning | known",
    ),
    category_id: str | None = Query(
        default=None,
        description="Filter by category id",
    ),
    hsk_level: int | None = Query(
        default=None,
        ge=1,
        le=7,
        description="Filter by HSK level 1–7",
    ),
    search: str | None = Query(
        default=None,
        max_length=100,
        description="Search text / pinyin / meaning",
    ),
    learner_id: LearnerId = Depends(get_current_learner_id),
    session: AsyncSession = Depends(get_db_session),
) -> VocabularyDashboardResponse:
    knowledge_status = _parse_status(status_filter)
    cat_id = CategoryId(category_id) if category_id else None

    use_case = ListVocabularyDashboard(
        vocabulary_knowledge_repo=VocabularyKnowledgeRepository(session),
        vocabulary_item_repo=VocabularyItemRepository(session),
        category_repo=CategoryRepository(session),
        category_assignment_repo=CategoryAssignmentRepository(session),
    )

    result = await use_case.execute(
        learner_id,
        knowledge_status=knowledge_status,
        category_id=cat_id,
        hsk_level=hsk_level,
        search=search,
    )

    return VocabularyDashboardResponse(
        items=[
            VocabularyDashboardItemSchema(
                vocabulary_id=row.vocabulary_id,
                text=row.text,
                pinyin=row.pinyin,
                meaning=row.meaning,
                status=row.status,
                successful_recalls=row.successful_recalls,
                failed_recalls=row.failed_recalls,
                times_seen=row.times_seen,
                last_practised_at=row.last_practised_at,
                last_seen_at=row.last_seen_at,
                categories=[
                    CategorySummarySchema(
                        id=c.id,
                        name=c.name,
                        type=c.type,
                        hsk_level=c.hsk_level,
                    )
                    for c in row.categories
                ],
                hsk_level=row.hsk_level,
            )
            for row in result.items
        ],
        total=result.total,
        status_counts=result.status_counts,
    )


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="List all categories (for dashboard filters)",
)
async def list_categories(
    session: AsyncSession = Depends(get_db_session),
) -> CategoryListResponse:
    repo = CategoryRepository(session)
    categories = await repo.get_all()
    return CategoryListResponse(
        categories=[
            CategoryListItemSchema(
                id=str(c.id),
                name=c.name,
                type=c.type.value,
                parent_id=str(c.parent_id) if c.parent_id else None,
                sort_order=c.sort_order,
                hsk_level=c.hsk_level,
            )
            for c in categories
        ]
    )
