from dataclasses import dataclass
from datetime import datetime

from chinese_learning.domain.identity.user import UserId


@dataclass(frozen=True, slots=True)
class LearnerId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class LearnerProfile:
    """
    Language-specific learning state belonging to a User.

    One User can have multiple LearnerProfiles (e.g. Chinese, Japanese, Korean...).
    All vocabulary knowledge, character knowledge, practice history, etc.
    live under a LearnerProfile, never directly under the User.
    """

    id: LearnerId
    user_id: UserId
    language: str  # e.g. "zh-CN", "zh-TW"
    display_name: str  # e.g. "My Chinese", "Mandarin 2026"
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.language.strip():
            raise ValueError("language cannot be empty")
        if not self.display_name.strip():
            raise ValueError("display_name cannot be empty")
