"""
Links a VocabularyItem to a Category.

A VocabularyItem may belong to multiple categories
(e.g. HSK 3 + Food → Fruits).
"""

from dataclasses import dataclass

from chinese_learning.domain.category.category import CategoryId
from chinese_learning.domain.vocabulary.vocabulary_item import VocabularyId


@dataclass(frozen=True, slots=True)
class CategoryAssignment:
    category_id: CategoryId
    vocabulary_id: VocabularyId
