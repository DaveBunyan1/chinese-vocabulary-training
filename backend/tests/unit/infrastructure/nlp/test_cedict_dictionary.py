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
    item = cedict_dictionary.lookup("增田")
    assert "surname" in item.meaning.lower()

    xiahou = cedict_dictionary.lookup("夏侯")
    assert "surname" in xiahou.meaning.lower()
