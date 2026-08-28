from chinese_learning.domain.text_analysis.character import characters_from_text


def test_extracts_unique_cjk_in_order():
    chars = characters_from_text("你好你好")
    assert [str(c) for c in chars] == ["你", "好"]


def test_skips_non_cjk():
    chars = characters_from_text("A你1好!")
    assert [str(c) for c in chars] == ["你", "好"]


def test_empty():
    assert characters_from_text("") == ()
    assert characters_from_text("abc") == ()
