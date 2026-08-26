"""REST endpoints for category management (create + assign)."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from chinese_learning.application.use_cases.assign_user_category import (
    AssignUserCategory,
)
from chinese_learning.application.use_cases.create_category import CreateCustomCategory
from chinese_learning.domain.category.category import (
    Category,
    CategoryId,
    CategoryType,
)
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId
from chinese_learning.infrastructure.persistence.database import get_db_session
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_assignment_repository import (
    CategoryAssignmentRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.category_repository import (
    CategoryRepository,
)
from chinese_learning.infrastructure.persistence.repositories.linguistic.vocabulary_item_repository import (
    VocabularyItemRepository,
)
from chinese_learning.presentation.rest.schemas.categories import (
    AssignCategoryRequest,
    AssignCategoryResponse,
    CategoryListResponse,
    CategorySchema,
    CategoryVocabularyItemSchema,
    CategoryVocabularyResponse,
    CreateCategoryRequest,
    CreateCategoryResponse,
    UnassignCategoryRequest,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


def _to_schema(c: Category) -> CategorySchema:
    return CategorySchema(
        id=str(c.id),
        name=c.name,
        type=c.type.value,
        parent_id=str(c.parent_id) if c.parent_id else None,
        sort_order=c.sort_order,
        hsk_level=c.hsk_level,
    )


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="List all categories",
)
async def list_categories(
    session: AsyncSession = Depends(get_db_session),
) -> CategoryListResponse:
    categories = await CategoryRepository(session).get_all()
    return CategoryListResponse(categories=[_to_schema(c) for c in categories])


@router.post(
    "",
    response_model=CreateCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom or topic category (optional parent)",
)
async def create_category(
    payload: CreateCategoryRequest,
    session: AsyncSession = Depends(get_db_session),
) -> CreateCategoryResponse:
    try:
        cat_type = CategoryType(payload.type.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid type: {payload.type}. Use custom|topic.",
        ) from exc

    if cat_type not in (CategoryType.CUSTOM, CategoryType.TOPIC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only custom or topic categories can be created here.",
        )

    parent_id = CategoryId(payload.parent_id) if payload.parent_id else None
    if parent_id is not None:
        parent = await CategoryRepository(session).get(parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category {payload.parent_id} not found.",
            )

    # CreateCustomCategory always uses CUSTOM; support TOPIC explicitly here
    if cat_type is CategoryType.CUSTOM:
        use_case = CreateCustomCategory(CategoryRepository(session))
        category = await use_case.execute(payload.name.strip(), parent_id=parent_id)
    else:
        category = Category(
            id=CategoryId(str(uuid4())),
            name=payload.name.strip(),
            type=CategoryType.TOPIC,
            parent_id=parent_id,
            hsk_level=None,
        )
        await CategoryRepository(session).save(category)

    await session.commit()
    return CreateCategoryResponse(category=_to_schema(category))


@router.post(
    "/assignments",
    response_model=AssignCategoryResponse,
    summary="Assign a vocabulary item to a topic/custom category",
)
async def assign_category(
    payload: AssignCategoryRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AssignCategoryResponse:
    use_case = AssignUserCategory(
        category_repo=CategoryRepository(session),
        assignment_repo=CategoryAssignmentRepository(session),
    )
    try:
        assigned = await use_case.add_category(
            VocabularyId(payload.vocabulary_id),
            CategoryId(payload.category_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await session.commit()
    return AssignCategoryResponse(
        assigned=assigned,
        vocabulary_id=payload.vocabulary_id,
        category_id=payload.category_id,
    )


@router.delete(
    "/assignments",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a vocabulary item from a topic/custom category",
)
async def unassign_category(
    payload: UnassignCategoryRequest,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    use_case = AssignUserCategory(
        category_repo=CategoryRepository(session),
        assignment_repo=CategoryAssignmentRepository(session),
    )
    try:
        await use_case.remove_category(
            VocabularyId(payload.vocabulary_id),
            CategoryId(payload.category_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await session.commit()


@router.get(
    "/{category_id}/vocabulary",
    response_model=CategoryVocabularyResponse,
    summary="List vocabulary items assigned to a category",
)
async def list_category_vocabulary(
    category_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> CategoryVocabularyResponse:
    cat_id = CategoryId(category_id)
    category = await CategoryRepository(session).get(cat_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found.",
        )

    assignments = await CategoryAssignmentRepository(session).get_by_category(cat_id)
    vids = [a.vocabulary_id for a in assignments]
    items = await VocabularyItemRepository(session).get_many(vids)
    items_sorted = sorted(items, key=lambda i: i.text)

    return CategoryVocabularyResponse(
        category_id=category_id,
        items=[
            CategoryVocabularyItemSchema(
                vocabulary_id=str(i.id),
                text=i.text,
                pinyin=i.pinyin,
                meaning=i.meaning,
            )
            for i in items_sorted
        ],
        total=len(items_sorted),
    )
