"""Schemas for the vocabulary dashboard API."""

from pydantic import BaseModel, Field


class CategorySummarySchema(BaseModel):
    id: str
    name: str
    type: str
    hsk_level: int | None = None


class VocabularyDashboardItemSchema(BaseModel):
    vocabulary_id: str
    text: str
    pinyin: str
    meaning: str
    status: str
    successful_recalls: int
    failed_recalls: int
    times_seen: int
    last_practised_at: str | None = None
    last_seen_at: str | None = None
    categories: list[CategorySummarySchema] = Field(default_factory=list)
    hsk_level: int | None = None
    characters: list[str] = Field(default_factory=list)


class VocabularyDashboardResponse(BaseModel):
    items: list[VocabularyDashboardItemSchema]
    total: int
    status_counts: dict[str, int]


class CategoryListItemSchema(BaseModel):
    id: str
    name: str
    type: str
    parent_id: str | None = None
    sort_order: int
    hsk_level: int | None = None


class CategoryListResponse(BaseModel):
    categories: list[CategoryListItemSchema]
