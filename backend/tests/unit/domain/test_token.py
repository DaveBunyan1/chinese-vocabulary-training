"""
Tests for the Token domain value object.

Token represents a meaningful semantic unit extracted from Chinese text.
"""

import pytest

from chinese_learning.domain.text_analysis.token import Token


def test_token_can_be_created_from_text() -> None:
    token = Token("学习")

    assert token.text == "学习"


def test_tokens_with_same_text_are_equal() -> None:
    first = Token("学习")
    second = Token("学习")

    assert first == second


def test_tokens_with_different_text_are_not_equal() -> None:
    first = Token("学习")
    second = Token("中文")

    assert first != second


def test_token_is_immutable() -> None:
    token = Token("学习")

    with pytest.raises(AttributeError):
        token.text = "中文"  # type: ignore[misc]


def test_token_cannot_be_empty() -> None:
    with pytest.raises(ValueError):
        Token("")


def test_token_cannot_contain_only_whitespace() -> None:
    with pytest.raises(ValueError):
        Token("   ")
