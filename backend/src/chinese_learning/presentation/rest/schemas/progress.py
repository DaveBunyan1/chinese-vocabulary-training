"""Schemas for progress stats API."""

from pydantic import BaseModel


class StatusBreakdownSchema(BaseModel):
    new: int
    learning: int
    known: int
    total: int


class VocabularyProgressSchema(BaseModel):
    by_status: StatusBreakdownSchema
    total_successful_recalls: int
    total_failed_recalls: int
    total_times_seen: int
    items_practised: int


class CharacterProgressSchema(BaseModel):
    by_status: StatusBreakdownSchema
    total_successful_recognitions: int
    total_failed_recognitions: int
    total_times_seen: int
    items_practised: int


class ProgressStatsResponse(BaseModel):
    vocabulary: VocabularyProgressSchema
    characters: CharacterProgressSchema
