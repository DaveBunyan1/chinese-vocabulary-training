import pytest

from chinese_learning.domain.text_analysis.character import Character


def test_create_valid_single_chinese_character() -> None:
    char = Character(symbol="铁")

    assert char.symbol == "铁"


def test_reject_empty_string() -> None:
    with pytest.raises(ValueError):
        Character(symbol="")


def test_reject_multiple_characters() -> None:
    with pytest.raises(ValueError):
        Character(symbol="铁柱")


def test_reject_non_chinese_character() -> None:
    with pytest.raises(ValueError):
        Character(symbol="A")


def test_characters_with_same_symbol_are_equal() -> None:
    assert Character("铁") == Character("铁")


def test_character_is_immutable() -> None:
    char = Character("铁")

    with pytest.raises(AttributeError):
        char.symbol = "木"  # type: ignore[misc]
