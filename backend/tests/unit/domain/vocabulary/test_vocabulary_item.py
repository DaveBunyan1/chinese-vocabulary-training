import pytest

from chinese_learning.domain.vocabulary.vocabulary_item import (
    VocabularyId,
    VocabularyItem,
)


def test_vocabulary_item_requires_text():

    with pytest.raises(ValueError):
        VocabularyItem(id=VocabularyId("id"), text="", pinyin="tiān", meaning="sky")


def test_vocabulary_item_requires_meaning():

    with pytest.raises(ValueError):
        VocabularyItem(
            id=VocabularyId("id"), text="天空", pinyin="tiān kōng", meaning=""
        )


def test_vocabulary_item_requires_pinyin():
    with pytest.raises(ValueError):
        VocabularyItem(id=VocabularyId("id"), text="天空", pinyin="", meaning="sky")
