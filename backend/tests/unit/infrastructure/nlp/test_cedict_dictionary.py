from chinese_learning.infrastructure.nlp.cedict_dictionary import CedictDictionary


def test_prefers_non_surname_sense(cedict_dictionary: CedictDictionary):
    jiao = cedict_dictionary.lookup("教")
    assert "surname" not in jiao.meaning.lower()
    assert "teach" in jiao.meaning.lower()

    zuo = cedict_dictionary.lookup("坐")
    assert "surname" not in zuo.meaning.lower()
    assert "sit" in zuo.meaning.lower()


def test_single_surname_only_entry_still_returns_something(
    cedict_dictionary: CedictDictionary,
):
    xiahou = cedict_dictionary.lookup("夏侯")
    assert "surname" in xiahou.meaning.lower()


def test_missing_word_uses_soft_meaning(cedict_dictionary: CedictDictionary):
    item = cedict_dictionary.lookup("坐在")
    assert item.meaning == "—"
    assert "[not found" not in item.meaning.lower()
    assert item.pinyin  # still has pypinyin


def test_ta_definition_is_sanitized(cedict_dictionary: CedictDictionary):
    """他 should surface a short pronoun gloss, not bound-form notes."""
    item = cedict_dictionary.lookup("他")
    assert "bound form" not in item.meaning.lower()
    assert "third-person" not in item.meaning.lower()
    assert "he" in item.meaning.lower()
    # Keep it short for learners / answer matching
    assert len(item.meaning) < 40
