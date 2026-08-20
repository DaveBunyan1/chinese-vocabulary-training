"""
Domain model for hierarchical categories.

Categories organise vocabulary and learning material (HSK levels, topics,
user-created groups, etc.). Hierarchy is expressed via parent_id.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CategoryId:
    value: str


@dataclass(frozen=True, slots=True)
class Category:
    id: CategoryId
    name: str
    parent_id: CategoryId | None = None  # None = top-level category
    sort_order: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Category name cannot be empty")
        if self.sort_order < 0:
            raise ValueError("sort_order cannot be negative")
