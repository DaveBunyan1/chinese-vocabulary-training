"""Schemas for category management API."""

from uuid import UUID

from pydantic import BaseModel, Field

from chinese_learning.domain.category.category import CategoryType


class CategorySchema(BaseModel):
    id: UUID
    name: str
    type: CategoryType
    parent_id: UUID | None = None
    sort_order: int = 0
    hsk_level: int | None = None


class CategoryListResponse(BaseModel):
    categories: list[CategorySchema]


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: UUID | None = Field(
        default=None,
        description="Optional parent category id (for subcategories).",
    )
    type: CategoryType = Field(
        default=CategoryType.CUSTOM,
        description="custom | topic (HSK/SYSTEM cannot be created here)",
    )


class CreateCategoryResponse(BaseModel):
    category: CategorySchema


class AssignCategoryRequest(BaseModel):
    vocabulary_id: UUID
    category_id: UUID


class AssignCategoryResponse(BaseModel):
    assigned: bool  # False if already assigned
    vocabulary_id: UUID
    category_id: UUID


class UnassignCategoryRequest(BaseModel):
    vocabulary_id: UUID
    category_id: UUID


class CategoryVocabularyItemSchema(BaseModel):
    vocabulary_id: UUID
    text: str
    pinyin: str
    meaning: str


class CategoryVocabularyResponse(BaseModel):
    category_id: UUID
    items: list[CategoryVocabularyItemSchema]
    total: int


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: UUID | None = Field(
        default=None,
        description="Set a new parent. Omit to leave unchanged.",
    )
    clear_parent: bool = Field(
        default=False,
        description="If true, remove parent (root category).",
    )
    sort_order: int | None = Field(default=None, ge=0)


class UpdateCategoryResponse(BaseModel):
    category: CategorySchema
