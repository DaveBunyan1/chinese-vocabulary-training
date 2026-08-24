from chinese_learning.infrastructure.nlp.cedict_segment import max_match_segment


def test_max_match_zuozai():
    lex = {"坐", "在", "坐落", "在于"}
    assert max_match_segment("坐在", lex) == ["坐", "在"]


def test_does_not_need_full_compound_in_lexicon():
    lex = {"坐", "在"}
    assert max_match_segment("坐在", lex) == ["坐", "在"]


def test_prefers_longer_word():
    lex = {"中", "国", "中国"}
    assert max_match_segment("中国", lex) == ["中国"]


def test_unknown_char_emitted():
    lex = {"我"}
    assert max_match_segment("我喵", lex) == ["我", "喵"]
