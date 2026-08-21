import pytest

from chinese_learning.domain.text_analysis.sentence import Sentence
from chinese_learning.domain.text_analysis.token import Token


def test_sentence_can_be_created_from_tokens() -> None:
    tokens = [
        Token("我"),
        Token("学习"),
        Token("中文"),
    ]

    raw_text = "我学习中文"
    sentence = Sentence(raw_text=raw_text, tokens=tokens)

    assert sentence.tokens == tuple(tokens)


def test_sentence_preserves_token_order() -> None:
    sentence = Sentence(
        raw_text="我喜欢猫",
        tokens=[
            Token("我"),
            Token("喜欢"),
            Token("猫"),
        ],
    )

    assert sentence.tokens[0].text == "我"
    assert sentence.tokens[1].text == "喜欢"
    assert sentence.tokens[2].text == "猫"


def test_sentence_cannot_be_empty() -> None:
    with pytest.raises(ValueError):
        Sentence(raw_text="", tokens=[])


def test_sentence_is_immutable() -> None:
    sentence = Sentence(raw_text="你好", tokens=[Token("你好")])

    with pytest.raises(AttributeError):
        sentence.tokens = ()  # type: ignore[misc]


def test_sentence_does_not_expose_mutable_token_collection() -> None:
    tokens = [Token("你好")]
    sentence = Sentence(raw_text="你好", tokens=tokens)

    tokens.append(Token("世界"))

    assert len(sentence.tokens) == 1


def test_token_collection_cannot_be_modified() -> None:
    sentence = Sentence(
        raw_text="我喜欢",
        tokens=[
            Token("我"),
            Token("喜欢"),
        ],
    )

    with pytest.raises(AttributeError):
        sentence.tokens += (Token("猫"),)  # type: ignore[misc]
