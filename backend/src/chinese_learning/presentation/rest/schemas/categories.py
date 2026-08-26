"""Schemas for category management API."""

from pydantic import BaseModel, Field


class CategorySchema(BaseModel):
    id: str
    name: str
    type: str
    parent_id: str | None = None
    sort_order: int = 0
    hsk_level: int | None = None


class CategoryListResponse(BaseModel):
    categories: list[CategorySchema]


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: str | None = Field(
        default=None,
        description="Optional parent category id (for subcategories).",
    )
    type: str = Field(
        default="custom",
        description="custom | topic (HSK/SYSTEM cannot be created here)",
    )


class CreateCategoryResponse(BaseModel):
    category: CategorySchema


class AssignCategoryRequest(BaseModel):
    vocabulary_id: str
    category_id: str


class AssignCategoryResponse(BaseModel):
    assigned: bool  # False if already assigned
    vocabulary_id: str
    category_id: str


class UnassignCategoryRequest(BaseModel):
    vocabulary_id: str
    category_id: str


class CategoryVocabularyItemSchema(BaseModel):
    vocabulary_id: str
    text: str
    pinyin: str
    meaning: str


class CategoryVocabularyResponse(BaseModel):
    category_id: str
    items: list[CategoryVocabularyItemSchema]
    total: int
