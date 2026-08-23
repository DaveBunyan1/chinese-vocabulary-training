"""
Domain model for hierarchical categories.

Categories organise vocabulary and learning material (HSK levels, topics,
user-created groups, etc.). Hierarchy is expressed via parent_id.
"""

from dataclasses import dataclass
from enum import StrEnum


class CategoryType(StrEnum):
    HSK = "hsk"
    TOPIC = "topic"  # user topics (Food, Travel…)
    SYSTEM = "system"  # Uncategorised / Extra / etc.
    CUSTOM = "custom"  # free-form user categories


@dataclass(frozen=True, slots=True)
class CategoryId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("CategoryId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Category:
    id: CategoryId
    name: str
    type: CategoryType
    parent_id: CategoryId | None = None
    sort_order: int = 0

    # Only meaningful for HSK categories
    hsk_level: int | None = None  # 1–6 or 7 (for the 7-9 band)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Category name cannot be empty")
        if self.sort_order < 0:
            raise ValueError("sort_order cannot be negative")

        if self.type is CategoryType.HSK:
            if self.hsk_level is None or not (1 <= self.hsk_level <= 7):
                raise ValueError("HSK categories must have hsk_level 1–7")
        else:
            if self.hsk_level is not None:
                raise ValueError("Only HSK categories may have hsk_level")
