"""Schemas for the review queue API."""

from pydantic import BaseModel


class ReviewQueueItemSchema(BaseModel):
    kind: str  # vocabulary | character
    reason: str  # due | unscheduled
    vocabulary_id: str | None = None
    text: str | None = None
    pinyin: str | None = None
    meaning: str | None = None
    character: str | None = None
    status: str
    next_review_at: str | None = None
    successful_attempts: int
    failed_attempts: int


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItemSchema]
    due_vocabulary_count: int
    due_character_count: int
    unscheduled_vocabulary_count: int
    unscheduled_character_count: int
    total: int
    as_of: str
