import pytest

from chinese_learning.infrastructure.nlp.token_filters import is_studyable_chinese_token


@pytest.mark.parametrize(
    "text,expected",
    [
        ("我", True),
        ("坐在", True),
        ("的", True),
        ("2024", False),
        ("0505", False),
        ("HSK", False),
        ("iPhone", False),
        ("Hello", False),
        ("。", False),
        ("，", False),
        ("", False),
        ("  ", False),
        ("HSK五级", True),  # mixed: has Han — keep for now
    ],
)
def test_is_studyable_chinese_token(text: str, expected: bool):
    assert is_studyable_chinese_token(text) is expected
