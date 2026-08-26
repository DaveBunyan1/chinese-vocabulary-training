"""Schemas for the character dashboard API."""

from pydantic import BaseModel


class CharacterDashboardItemSchema(BaseModel):
    character: str
    pinyin: str
    meaning: str
    status: str
    successful_recognitions: int
    failed_recognitions: int
    correct_pinyin_count: int
    times_seen: int
    last_practised_at: str | None = None
    last_seen_at: str | None = None


class CharacterDashboardResponse(BaseModel):
    items: list[CharacterDashboardItemSchema]
    total: int
    status_counts: dict[str, int]
