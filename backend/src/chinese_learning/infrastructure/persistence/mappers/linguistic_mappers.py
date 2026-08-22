from chinese_learning.domain.category.category import Category, CategoryId
from chinese_learning.domain.category.category_assignment import CategoryAssignment
from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)
from chinese_learning.infrastructure.persistence.models import (
    CategoryAssignmentModel,
    CategoryModel,
    VocabularyItemModel,
)

# ---------- VocabularyItem ----------


def vocabulary_item_to_domain(model: VocabularyItemModel) -> VocabularyItem:
    return VocabularyItem(
        id=VocabularyId(model.id),
        text=model.text,
        pinyin=model.pinyin,
        meaning=model.meaning,
    )


def vocabulary_item_to_model(domain: VocabularyItem) -> VocabularyItemModel:
    return VocabularyItemModel(
        id=str(domain.id),
        text=domain.text,
        pinyin=domain.pinyin,
        meaning=domain.meaning,
    )


# ---------- Category ----------


def category_to_domain(model: CategoryModel) -> Category:
    return Category(
        id=CategoryId(model.id),
        name=model.name,
        parent_id=CategoryId(model.parent_id) if model.parent_id else None,
        sort_order=model.sort_order,
    )


def category_to_model(domain: Category) -> CategoryModel:
    return CategoryModel(
        id=str(domain.id.value),
        name=domain.name,
        parent_id=str(domain.parent_id.value) if domain.parent_id else None,
        sort_order=domain.sort_order,
    )


# ---------- CategoryAssignment ----------


def category_assignment_to_domain(model: CategoryAssignmentModel) -> CategoryAssignment:
    return CategoryAssignment(
        category_id=CategoryId(model.category_id),
        vocabulary_id=VocabularyId(model.vocabulary_id),
    )


def category_assignment_to_model(domain: CategoryAssignment) -> CategoryAssignmentModel:
    return CategoryAssignmentModel(
        category_id=str(domain.category_id.value),
        vocabulary_id=str(domain.vocabulary_id.value),
    )
