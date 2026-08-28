from chinese_learning.infrastructure.nlp.pinyin_normalize import (
    normalize_pinyin_for_match,
    to_tone_marks,
    to_tone_numbers,
)


def test_tone_numbers_and_marks_roundtrip_match():
    assert normalize_pinyin_for_match("nǐ hǎo") == normalize_pinyin_for_match(
        "ni3 hao3"
    )
    assert normalize_pinyin_for_match("nǐhǎo") == normalize_pinyin_for_match("ni3hao3")
    assert normalize_pinyin_for_match("xué") == normalize_pinyin_for_match("xue2")


def test_to_tone_marks_display():
    assert to_tone_marks("ni3 hao3") == "nǐ hǎo"
    assert to_tone_marks("xue2") == "xué"


def test_to_tone_numbers():
    assert to_tone_numbers("nǐ hǎo") == "ni3 hao3"
    assert "3" in to_tone_numbers("nǐhǎo")
