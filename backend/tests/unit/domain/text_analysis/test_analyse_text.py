import pytest

from chinese_learning.domain.text_analysis.analyse_text import AnalyseText
from chinese_learning.domain.text_analysis.character import Character
from chinese_learning.domain.text_analysis.token import Token


@pytest.fixture
def analyser() -> AnalyseText:
    return AnalyseText()


def test_simple_sentence(analyser: AnalyseText):
    result = analyser.execute("我喜欢学习中文")

    assert result.sentence.raw_text == "我喜欢学习中文"
    assert [t.text for t in result.sentence.tokens] == ["我", "喜欢", "学习", "中文"]
    assert [c.symbol for c in result.characters] == [
        "我",
        "喜",
        "欢",
        "学",
        "习",
        "中",
        "文",
    ]


def test_punctuation_is_dropped_from_tokens_but_kept_in_raw_text(analyser: AnalyseText):
    result = analyser.execute("我喜欢学习中文！你呢？")

    assert result.sentence.raw_text == "我喜欢学习中文！你呢？"
    assert [t.text for t in result.sentence.tokens] == [
        "我",
        "喜欢",
        "学习",
        "中文",
        "你",
        "呢",
    ]
    # no punctuation tokens
    assert all(
        not any(p in t.text for p in "！？。，、；：") for t in result.sentence.tokens
    )


def test_characters_are_unique_and_ordered_by_first_appearance(analyser: AnalyseText):
    result = analyser.execute("学习学习中文")

    symbols = [c.symbol for c in result.characters]
    assert symbols == ["学", "习", "中", "文"]
    assert len(symbols) == len(set(symbols))  # unique


def test_empty_string_raises(analyser: AnalyseText):
    with pytest.raises(ValueError, match="raw_text cannot be empty"):
        analyser.execute("")

    with pytest.raises(ValueError, match="raw_text cannot be empty"):
        analyser.execute("   ")


def test_only_punctuation_raises(analyser: AnalyseText):
    with pytest.raises(ValueError, match="No valid tokens found"):
        analyser.execute("！！！？？？")


def test_mixed_chinese_and_english(analyser: AnalyseText):
    result = analyser.execute("我爱Python和中文")

    token_texts = [t.text for t in result.sentence.tokens]
    assert "我" in token_texts
    assert "爱" in token_texts
    assert "中文" in token_texts

    assert result.sentence.raw_text == "我爱Python和中文"


def test_characters_skip_non_cjk(analyser: AnalyseText):
    result = analyser.execute("我有3个苹果")

    symbols = [c.symbol for c in result.characters]
    assert "3" not in symbols  # digit skipped
    assert "我" in symbols
    assert "个" in symbols
    assert "苹" in symbols
    assert "果" in symbols


def test_whitespace_is_stripped_from_raw_text(analyser: AnalyseText):
    result = analyser.execute("  我喜欢中文  ")

    assert result.sentence.raw_text == "我喜欢中文"
    assert len(result.sentence.tokens) > 0


def test_result_is_immutable(analyser: AnalyseText):
    result = analyser.execute("测试")

    assert isinstance(result.sentence.tokens, tuple)
    assert isinstance(result.characters, tuple)
    assert all(isinstance(t, Token) for t in result.sentence.tokens)
    assert all(isinstance(c, Character) for c in result.characters)
