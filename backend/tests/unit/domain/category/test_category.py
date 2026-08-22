import pytest

from chinese_learning.domain.category.category import Category, CategoryId


def test_empty_string_raise() -> None:
    with pytest.raises(ValueError):
        Category(id=CategoryId("cat-1"), name="")


def test_negative_sort_raises() -> None:
    with pytest.raises(ValueError):
        Category(id=CategoryId("cat-1"), name="Category", sort_order=-1)
