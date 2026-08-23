import pytest

from chinese_learning.domain.category.category import Category, CategoryId, CategoryType


def test_empty_string_raise() -> None:
    with pytest.raises(ValueError):
        Category(id=CategoryId("cat-1"), name="", type=CategoryType.HSK)


def test_negative_sort_raises() -> None:
    with pytest.raises(ValueError):
        Category(
            id=CategoryId("cat-1"),
            name="HSK 1",
            type=CategoryType.HSK,
            sort_order=-1,
        )
